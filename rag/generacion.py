"""Generación con Groq: del contexto recuperado a una respuesta.

Aquí se ve la parte menos mágica del RAG: ensamblar el prompt es concatenar
strings. Nada más. Todo lo interesante ya pasó antes, en la recuperación.
"""

from __future__ import annotations

import os
import re
import time

from groq import APIError, Groq, RateLimitError

# Modelo de generación.
#
# NO uses llama-3.3-70b-versatile ni llama-3.1-8b-instant: Groq anunció su
# deprecación el 17 de junio de 2026 y los apagó el 16 de agosto de 2026. Casi
# todos los tutoriales que hay en línea usan uno de esos dos.
#
# openai/gpt-oss-120b es el reemplazo que Groq recomienda para el 70B.
# Alternativa más chica: openai/gpt-oss-20b.
#
# Antes de una clase, verifica en https://console.groq.com/docs/deprecations
MODELO_GROQ = "openai/gpt-oss-120b"

# temperature=0 para que las demos salgan igual en el ensayo y en vivo.
# Aun así, temperature=0 no garantiza salida idéntica byte a byte: la
# infraestructura de inferencia introduce variación. Por eso los golden tests
# del CP6 verifican subcadenas clave, nunca la respuesta completa.
TEMPERATURA = 0

# Reintentos ante 429 (cuota del tier gratuito).
MAX_REINTENTOS = 5
ESPERA_BASE_SEG = 5.0

_cliente: Groq | None = None


def _obtener_cliente() -> Groq:
    """Crea el cliente de Groq una sola vez, y solo cuando hace falta."""
    global _cliente
    if _cliente is None:
        clave = os.getenv("GROQ_API_KEY")
        if not clave:
            raise RuntimeError(
                "Falta GROQ_API_KEY.\n"
                "  1. Saca tu clave gratuita en https://console.groq.com/keys\n"
                "  2. Copia .env.example a .env\n"
                "  3. Pega la clave en la línea GROQ_API_KEY=\n"
                "La clave se lee del .env; nunca se escribe en el código."
            )
        _cliente = Groq(api_key=clave)
    return _cliente


INSTRUCCION = """Eres el asistente del Instituto Nébula.

Reglas:
1. Responde ÚNICAMENTE con información que aparezca en el CONTEXTO de abajo.
2. Si el contexto no contiene la respuesta, di exactamente: "No tengo esa información."
3. Cita SIEMPRE el archivo del que sacaste el dato, entre corchetes. Ejemplo: [costos_y_pagos.md]
4. No uses conocimiento propio. Si el contexto contradice lo que tú crees saber, gana el contexto.
"""


def formatear_contexto(resultados) -> str:
    """Convierte los chunks recuperados en el bloque de CONTEXTO del prompt.

    Cada fragmento va etiquetado con su archivo de origen. Sin esa etiqueta el
    modelo no puede citar, y sin cita no podemos verificar nada en el CP6.

    El orden de los fragmentos NO es cosmético: el modelo pesa más lo que está
    al principio y al final del contexto que lo que queda enterrado en medio.
    """
    partes = []
    for i, resultado in enumerate(resultados, start=1):
        partes.append(
            f"--- Fragmento {i} · fuente: [{resultado.chunk.fuente}] ---\n"
            f"{resultado.chunk.texto}"
        )
    return "\n\n".join(partes)


def ensamblar_prompt(resultados, pregunta: str, instruccion: str = INSTRUCCION) -> str:
    """Instrucción + contexto + pregunta. Esto es todo el "aumento" del RAG."""
    return (
        f"{instruccion}\n"
        f"=================== CONTEXTO ===================\n"
        f"{formatear_contexto(resultados)}\n"
        f"================================================\n\n"
        f"PREGUNTA: {pregunta}\n\n"
        f"RESPUESTA:"
    )


# Corchetes con los que el modelo puede envolver una cita. El ejemplo del prompt
# usa los normales, pero gpt-oss a veces responde con los de ancho completo
# 【archivo.md】. Si solo buscáramos [ ], daríamos por no citada una respuesta que
# sí citó: un guardrail que se equivoca es peor que no tenerlo.
_PATRON_CITAS = re.compile(r"[\[【]([^\]】]+)[\]】]")


def extraer_citas(respuesta: str) -> list[str]:
    """Todos los archivos citados en la respuesta, en orden de aparición."""
    return [c.strip() for c in _PATRON_CITAS.findall(respuesta)]


def citas_validas(respuesta: str, resultados) -> list[str]:
    """Solo las citas que apuntan a un archivo REALMENTE recuperado.

    Que el modelo escriba algo entre corchetes no basta: puede citar un archivo
    que no le pasamos, o inventarse el nombre. Un guardrail de salida verifica
    contra lo que de verdad estaba en el contexto.
    """
    fuentes = {r.chunk.fuente for r in resultados}
    return [c for c in extraer_citas(respuesta) if c in fuentes]


def generar(prompt: str, modelo: str = MODELO_GROQ) -> str:
    """Manda el prompt a Groq y devuelve el texto de la respuesta.

    Reintenta ante 429. El tier gratuito de Groq limita TOKENS POR MINUTO, no
    solo peticiones por minuto, así que un checkpoint que hace varias llamadas
    seguidas con contextos largos (el CP6 hace once) lo alcanza sin problema.
    No es un error de configuración: es la cuota gratuita haciendo su trabajo.
    """
    cliente = _obtener_cliente()

    for intento in range(MAX_REINTENTOS):
        try:
            respuesta = cliente.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURA,
            )
            return (respuesta.choices[0].message.content or "").strip()

        except RateLimitError as error:
            if intento == MAX_REINTENTOS - 1:
                raise RuntimeError(
                    "Groq sigue respondiendo 429 después de "
                    f"{MAX_REINTENTOS} intentos.\n"
                    "  Se agotó la cuota gratuita del minuto (tokens por minuto).\n"
                    "  Espera un minuto completo y vuelve a correr el checkpoint."
                ) from error
            espera = ESPERA_BASE_SEG * (2 ** intento)
            print(f"    [429] cuota de Groq alcanzada, reintento en {espera:.0f}s "
                  f"({intento + 1}/{MAX_REINTENTOS - 1})")
            time.sleep(espera)

        except APIError as error:
            mensaje = str(error)
            if "decommission" in mensaje or "does not exist" in mensaje:
                raise RuntimeError(
                    f"Groq no reconoce el modelo '{modelo}'.\n"
                    "  Lo más probable es que lo hayan deprecado.\n"
                    "  Revisa https://console.groq.com/docs/deprecations y actualiza\n"
                    "  MODELO_GROQ en rag/generacion.py"
                ) from error
            raise RuntimeError(f"Groq respondió con error: {mensaje}") from error

    raise RuntimeError("Inalcanzable: el bucle de reintentos siempre sale antes.")
