"""Embeddings con Gemini: del texto a vectores.

Tres cosas que hay que entender de este módulo, porque las tres se ven en clase:

1. TASK_TYPE ASIMÉTRICO. Un documento del corpus y una pregunta de una persona
   NO son el mismo tipo de texto, aunque los procese el mismo modelo. Por eso
   los chunks se embeben con RETRIEVAL_DOCUMENT y la pregunta con
   RETRIEVAL_QUERY. El modelo produce vectores pensados para encontrarse entre
   sí, no para parecerse.

2. NORMALIZACIÓN MANUAL. gemini-embedding-001 devuelve 3072 dimensiones por
   defecto y auto-normaliza SOLO en esa dimensión. Nosotros pedimos 768 por
   costo y velocidad, así que hay que normalizar a mano. Si se olvida, la
   similitud coseno sale mal y el retrieval se degrada de una forma
   dificilísima de diagnosticar: no truena nada, simplemente responde peor.

3. CACHÉ EN DISCO. Cada vector se guarda en cache/ con llave SHA-256. La
   segunda corrida es instantánea y no consume cuota. Es la diferencia entre
   poder ensayar la clase tres veces y quedarse sin cuota el día del vivo.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

# --- Configuración ---------------------------------------------------------

# gemini-embedding-001, NO gemini-embedding-2. El modelo nuevo devuelve UN SOLO
# embedding agregado cuando le pasas una lista de textos en contents (hay que
# envolver cada texto en un types.Content para obtener uno por texto) y además
# no soporta task_type. Para esta clase queremos el comportamiento predecible.
MODELO_EMBEDDING = "gemini-embedding-001"

# Recomendadas: 768, 1536, 3072. Usamos 768 por costo y velocidad.
# OJO: cambiar esto invalida la caché y obliga a recrear la colección de Chroma.
DIMENSION = 768

# Límite de entrada de gemini-embedding-001: 2,048 tokens por texto.
# Con chunks de 500 caracteres estamos muy holgados.

# Cuántos textos van por llamada. Si alguna vez sale un 400 quejándose del
# tamaño del lote, baja este número.
TAMANO_LOTE = 32

# Reintentos ante 429 RESOURCE_EXHAUSTED.
MAX_REINTENTOS = 5
ESPERA_BASE_SEG = 2.0

DIRECTORIO_CACHE = Path("cache")

_cliente: genai.Client | None = None


def _obtener_cliente() -> genai.Client:
    """Crea el cliente de Gemini una sola vez, y solo cuando hace falta.

    Es perezoso a propósito: así importar este módulo no falla si todavía no
    hay clave configurada, y el CP1 (que solo chunkea) corre sin claves.
    """
    global _cliente
    if _cliente is None:
        clave = os.getenv("GEMINI_API_KEY")
        if not clave:
            raise RuntimeError(
                "Falta GEMINI_API_KEY.\n"
                "  1. Saca tu clave gratuita en https://aistudio.google.com/apikey\n"
                "  2. Copia .env.example a .env\n"
                "  3. Pega la clave en la línea GEMINI_API_KEY=\n"
                "La clave se lee del .env; nunca se escribe en el código."
            )
        _cliente = genai.Client(api_key=clave)
    return _cliente


# --- Normalización ---------------------------------------------------------

def normalizar(valores: list[float]) -> list[float]:
    """Deja el vector con norma 1.

    Obligatorio con gemini-embedding-001 en cualquier dimensión distinta de
    3072. Con vectores normalizados, la similitud coseno es simplemente el
    producto punto, y la distancia coseno de Chroma se comporta como esperamos.
    """
    vector = np.array(valores, dtype=np.float32)
    norma = np.linalg.norm(vector)
    if norma == 0:
        # No debería pasar nunca, pero dividir entre cero sí arruinaría el día.
        return vector.tolist()
    return (vector / norma).tolist()


def similitud_coseno(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores. 1.0 = idénticos, 0.0 = sin relación."""
    va, vb = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denominador = np.linalg.norm(va) * np.linalg.norm(vb)
    if denominador == 0:
        return 0.0
    return float(np.dot(va, vb) / denominador)


# --- Caché en disco --------------------------------------------------------

def _llave_cache(texto: str, task_type: str) -> str:
    """SHA-256 de texto + modelo + dimensión + task_type.

    task_type va en la llave y esto no es un detalle: el MISMO texto embebido
    como RETRIEVAL_DOCUMENT y como RETRIEVAL_QUERY da vectores DISTINTOS. Si
    no lo incluyéramos, la caché devolvería el vector equivocado.
    """
    material = f"{MODELO_EMBEDDING}|{DIMENSION}|{task_type}|{texto}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _leer_de_cache(llave: str) -> list[float] | None:
    archivo = DIRECTORIO_CACHE / f"{llave}.json"
    if not archivo.exists():
        return None
    try:
        return json.loads(archivo.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Caché corrupta: la ignoramos y volvemos a pedir el embedding.
        return None


def _escribir_en_cache(llave: str, vector: list[float]) -> None:
    DIRECTORIO_CACHE.mkdir(exist_ok=True)
    archivo = DIRECTORIO_CACHE / f"{llave}.json"
    archivo.write_text(json.dumps(vector), encoding="utf-8")


# --- Llamada a la API con reintentos ---------------------------------------

def _embeber_lote(textos: list[str], task_type: str) -> list[list[float]]:
    """Pide un lote de embeddings a Gemini, con backoff exponencial ante 429.

    No hardcodeamos supuestos de peticiones por minuto: Google ya no publica
    esos números por modelo en su documentación y remiten a AI Studio. La
    estrategia correcta es manejar el 429 cuando llegue, no adivinarlo.
    """
    cliente = _obtener_cliente()

    for intento in range(MAX_REINTENTOS):
        try:
            respuesta = cliente.models.embed_content(
                model=MODELO_EMBEDDING,
                contents=textos,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=DIMENSION,
                ),
            )
            return [normalizar(e.values) for e in respuesta.embeddings]

        except genai_errors.APIError as error:
            recuperable = error.code in (429, 500, 503, 504)
            ultimo_intento = intento == MAX_REINTENTOS - 1

            if not recuperable:
                raise RuntimeError(
                    f"Gemini respondió con error {error.code}: {error.message}"
                ) from error

            if ultimo_intento:
                raise RuntimeError(
                    "Gemini sigue respondiendo 429 RESOURCE_EXHAUSTED después de "
                    f"{MAX_REINTENTOS} intentos.\n"
                    "Se agotó la cuota gratuita del día o del minuto.\n"
                    "  - Espera unos minutos y vuelve a correr: lo ya embebido "
                    "quedó en caché y no se vuelve a pedir.\n"
                    "  - Revisa tu cuota en https://aistudio.google.com/"
                ) from error

            espera = ESPERA_BASE_SEG * (2 ** intento)
            print(f"    [429] cuota alcanzada, reintento en {espera:.0f}s "
                  f"({intento + 1}/{MAX_REINTENTOS - 1})")
            time.sleep(espera)

    raise RuntimeError("Inalcanzable: el bucle de reintentos siempre sale antes.")


def _embeber_con_cache(textos: list[str], task_type: str, verboso: bool) -> list[list[float]]:
    """Resuelve por caché lo que se pueda y pide a la API solo lo que falte."""
    vectores: list[list[float] | None] = [None] * len(textos)
    pendientes: list[int] = []

    for i, texto in enumerate(textos):
        cacheado = _leer_de_cache(_llave_cache(texto, task_type))
        if cacheado is None:
            pendientes.append(i)
        else:
            vectores[i] = cacheado

    if verboso:
        print(f"  Caché: {len(textos) - len(pendientes)} de {len(textos)} ya estaban. "
              f"Faltan {len(pendientes)}.")

    for inicio in range(0, len(pendientes), TAMANO_LOTE):
        indices = pendientes[inicio:inicio + TAMANO_LOTE]
        lote = [textos[i] for i in indices]
        if verboso:
            print(f"  Pidiendo a Gemini: textos {inicio + 1} a "
                  f"{inicio + len(indices)} de {len(pendientes)}...")
        nuevos = _embeber_lote(lote, task_type)
        for indice, vector in zip(indices, nuevos):
            vectores[indice] = vector
            _escribir_en_cache(_llave_cache(textos[indice], task_type), vector)

    return [v for v in vectores if v is not None]


# --- API pública del módulo ------------------------------------------------

def embed_documentos(textos: list[str], verboso: bool = True) -> list[list[float]]:
    """Embebe chunks del corpus. Usa RETRIEVAL_DOCUMENT."""
    if not textos:
        return []
    return _embeber_con_cache(textos, "RETRIEVAL_DOCUMENT", verboso)


def embed_pregunta(pregunta: str, verboso: bool = False) -> list[float]:
    """Embebe la pregunta de la persona usuaria. Usa RETRIEVAL_QUERY.

    Esta es la otra mitad de la asimetría. Si embebemos la pregunta como si
    fuera un documento, el retrieval empeora sin avisar.
    """
    return _embeber_con_cache([pregunta], "RETRIEVAL_QUERY", verboso)[0]
