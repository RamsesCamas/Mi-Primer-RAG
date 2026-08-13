"""CP6 — Lo que falta para producción.

    python checkpoints/cp6_produccion.py

Cuatro cosas que separan una demo de un sistema, con CERO dependencias nuevas:
todo con la biblioteca estándar sobre el pipeline que ya construimos.

  1. Monitoreo    — ¿dónde se va el tiempo?
  2. Guardrails   — qué entra y qué sale
  3. Groundedness — ¿esta respuesta se apoya en el contexto?
  4. Golden tests — ¿el cambio de ayer mejoró o empeoró el sistema?

Es superficial a propósito. Si lo implementamos a mano en pocas líneas, se
entiende qué hacen por dentro las herramientas de verdad.

Lo que hay que decir en voz alta está en GUION.md, no aquí.
"""

import json
import re
import sys
import time
import unicodedata
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.embeddings import embed_pregunta  # noqa: E402
from rag.generacion import (  # noqa: E402
    citas_validas,
    ensamblar_prompt,
    extraer_citas,
    formatear_contexto,
    generar,
)
from rag.indice import buscar, construir_indice, tokenizar  # noqa: E402

LINEA = "=" * 78

# Umbral de dominio, calibrado contra ESTE corpus (ver bloque 2):
# preguntas de dominio dan 0.65 a 0.81, preguntas de fuera dan 0.52 a 0.60.
UMBRAL_DOMINIO = 0.62

# Qué proporción de las palabras de una oración debe estar en el contexto.
UMBRAL_APOYO = 0.60

PREGUNTA_BUENA = "¿Cuál es el monto de la cuota de inscripción del Instituto Nébula?"
PREGUNTA_FUERA = "¿Cuál es la capital de Mongolia?"
PREGUNTA_SIN_CITA = "¿Cuál es la política de reembolsos?"
PREGUNTA_INVENTABLE = "¿Cuál es la política de propiedad intelectual sobre el proyecto final?"

indice = construir_indice(cargar_corpus("corpus"), verboso=False)


# ===========================================================================
# 1. MONITOREO — un decorador que cronometra cada etapa
# ===========================================================================

MEDICIONES = []


def medir(etapa):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            inicio = time.perf_counter()
            resultado = funcion(*args, **kwargs)
            MEDICIONES.append((etapa, (time.perf_counter() - inicio) * 1000))
            return resultado
        return envoltura
    return decorador


@medir("1. embeber pregunta")
def etapa_embeber(pregunta):
    return embed_pregunta(pregunta)


@medir("2. retrieval")
def etapa_buscar(pregunta):
    return buscar(indice, pregunta, k=4)


@medir("3. ensamblar prompt")
def etapa_ensamblar(resultados, pregunta):
    return ensamblar_prompt(resultados, pregunta)


@medir("4. generación")
def etapa_generar(prompt):
    return generar(prompt)


print(LINEA)
print("1. MONITOREO")
print(LINEA)

etapa_embeber(PREGUNTA_BUENA)
resultados = etapa_buscar(PREGUNTA_BUENA)
prompt = etapa_ensamblar(resultados, PREGUNTA_BUENA)
respuesta = etapa_generar(prompt)

total = sum(ms for _, ms in MEDICIONES)
for etapa, ms in MEDICIONES:
    print(f"  {etapa:<22}{ms:>10.1f} ms{ms / total * 100:>8.1f}%")
print(f"  {'TOTAL':<22}{total:>10.1f} ms{100.0:>8.1f}%")
print(f"\n  chunks recuperados: {len(resultados)}   "
      f"distancia del mejor: {resultados[0].distancia:.4f}   "
      f"tokens del prompt: ~{len(prompt) // 4:,}")
print("\n  La generación se lleva casi todo el tiempo. Y cuando un RAG responde")
print("  mal, casi nunca es culpa de esa etapa. Sin medir por etapa no sabes")
print("  dónde estás perdiendo ni tiempo ni calidad.")
print("\n  >> En serio: Phoenix / OpenTelemetry")


# ===========================================================================
# 2. GUARDRAILS — uno de entrada y uno de salida
# ===========================================================================

def guardrail_entrada(pregunta):
    """¿Se parece esta pregunta a algo que tengamos? Similitud del mejor chunk."""
    mejor = buscar(indice, pregunta, k=1)[0]
    return 1 - mejor.distancia


print()
print(LINEA)
print("2. GUARDRAILS")
print(LINEA)
print(f"DE ENTRADA: rechazar antes de gastar la llamada. Umbral: {UMBRAL_DOMINIO}\n")

for pregunta in (PREGUNTA_BUENA, PREGUNTA_FUERA):
    similitud = guardrail_entrada(pregunta)
    veredicto = "PASA" if similitud >= UMBRAL_DOMINIO else "RECHAZADA — 0 tokens gastados"
    print(f"  {similitud:.4f}  {veredicto:<32} «{pregunta}»")

print(f"\nDE SALIDA: el prompt pide citar. Verifiquemos EN CÓDIGO que citó.\n")

# La instrucción normal, pero sin la regla 3. Es un experimento controlado:
# quitamos a propósito la única cosa que le pedía citar.
INSTRUCCION_SIN_REGLA_3 = """Eres el asistente del Instituto Nébula.

Reglas:
1. Responde ÚNICAMENTE con información que aparezca en el CONTEXTO de abajo.
2. Si el contexto no contiene la respuesta, di exactamente: "No tengo esa información."
"""

resultados = buscar(indice, PREGUNTA_SIN_CITA, k=4)
fuentes = sorted({r.chunk.fuente for r in resultados})
print(f"  Pregunta: {PREGUNTA_SIN_CITA}")
print(f"  Archivos que le pasamos: {fuentes}\n")

# Caso A: el prompt completo. El modelo sí cita.
con_regla = generar(ensamblar_prompt(resultados, PREGUNTA_SIN_CITA))

# Caso B: mismo todo, pero sin la regla que pide citar.
sin_regla = generar(ensamblar_prompt(resultados, PREGUNTA_SIN_CITA,
                                     INSTRUCCION_SIN_REGLA_3))

# Caso C: una respuesta inventada por nosotros, que cita un archivo que NUNCA
# estuvo en el contexto. No cuesta ninguna llamada y siempre se comporta igual.
inventada = "La política se revisa cada año [manual_interno_secreto.md]."

for etiqueta, texto in [("prompt completo", con_regla),
                        ("sin la regla de citar", sin_regla),
                        ("cita un archivo que no le pasamos", inventada)]:
    citas = extraer_citas(texto)
    validas = citas_validas(texto, resultados)
    veredicto = "PASA" if validas else "RECHAZADA"
    print(f"  [{veredicto:<9}] {etiqueta:<36} citas={citas or '[]'}")

print("\n  Tres cosas que se ven aquí:")
print("   - Con la regla puesta, el modelo cita. Bien.")
print("   - Quítale la regla y deja de citar. Nada te avisa: la respuesta sigue")
print("     saliendo bonita y con formato. Solo el código lo detecta.")
print("   - Y citar no basta: la tercera CITÓ, pero un archivo que nunca vio.")
print("     Un guardrail compara contra lo que de verdad estaba en el contexto.")
print("\n  'El prompt dice que lo haga' NO ES UN GUARDRAIL.")
print("  Un guardrail es código que verifica y puede decir que no.")
print("\n  Detalle real de este repositorio: la primera versión de este guardrail")
print("  solo buscaba corchetes [ ]. El modelo cita con 【 】 y la daba por no")
print("  citada. Un guardrail mal escrito es peor que no tenerlo: los guardrails")
print("  también hay que probarlos.")
print("\n  >> En serio: Guardrails AI o NeMo Guardrails")


# ===========================================================================
# 3. GROUNDEDNESS — ¿cada oración se apoya en el contexto?
# ===========================================================================

VACIAS = {"para", "como", "esta", "este", "esto", "esa", "ese", "los", "las",
          "del", "que", "con", "por", "una", "uno", "sus", "sobre", "entre",
          "pero", "mas", "muy", "son", "ser", "hay", "sin", "segun", "cual",
          "todo", "toda", "todos", "todas", "puede", "pueden", "debe", "deben"}


def apoyo_lexico(oracion, contexto):
    """Proporción de palabras significativas de la oración que están en el contexto."""
    palabras = {t for t in tokenizar(oracion) if len(t) > 3 and t not in VACIAS}
    if not palabras:
        return 1.0
    return len(palabras & set(tokenizar(contexto))) / len(palabras)


def revisar(respuesta, contexto):
    oraciones = [o.strip() for o in re.split(r"(?<=[.!?])\s+|\n+",
                                             re.sub(r"[*#>|`-]", " ", respuesta))
                 if len(o.strip()) > 25]
    for oracion in oraciones:
        puntaje = apoyo_lexico(oracion, contexto)
        marca = "OK" if puntaje >= UMBRAL_APOYO else "!!"
        print(f"  [{marca}] {puntaje:.2f}  {' '.join(oracion.split())[:80]}")
    apoyadas = sum(apoyo_lexico(o, contexto) >= UMBRAL_APOYO for o in oraciones)
    print(f"  -> {apoyadas} de {len(oraciones)} oraciones apoyadas\n")


print()
print(LINEA)
print("3. GROUNDEDNESS")
print(LINEA)

for pregunta, instruccion in [
    (PREGUNTA_BUENA, None),
    (PREGUNTA_INVENTABLE, "Eres el asistente del Instituto Nébula. Responde de "
                          "forma útil y completa."),
]:
    resultados = buscar(indice, pregunta, k=4)
    contexto = formatear_contexto(resultados)
    if instruccion is None:
        texto = generar(ensamblar_prompt(resultados, pregunta))
    else:
        texto = generar(f"{instruccion}\n\n=== CONTEXTO ===\n{contexto}\n=== FIN ==="
                        f"\n\nPREGUNTA: {pregunta}\n\nRESPUESTA:")
    print(f"  {pregunta}")
    revisar(texto[:2500], contexto)

print("  Esto es solapamiento de palabras y nada más. Se equivoca con las")
print("  paráfrasis fieles y se le cuela una mentira escrita con las palabras")
print("  del contexto. Por eso las herramientas serias usan un LLM como juez.")
print("\n  >> En serio: RAGAS (métrica de faithfulness)")


# ===========================================================================
# 4. GOLDEN TESTS — 8 preguntas fijas, una de ellas con abstención
# ===========================================================================

def normalizar(texto):
    """Minúsculas, sin acentos y sin separadores de miles."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"(?<=\d),(?=\d)", "",
                  "".join(c for c in descompuesto if not unicodedata.combining(c)))


def responder(pregunta):
    """El pipeline con abstención: si la pregunta no es del dominio, no llamamos."""
    similitud = guardrail_entrada(pregunta)
    if similitud < UMBRAL_DOMINIO:
        return None, similitud
    resultados = buscar(indice, pregunta, k=4)
    return generar(ensamblar_prompt(resultados, pregunta)), similitud


print()
print(LINEA)
print("4. GOLDEN TESTS")
print(LINEA)

casos = json.loads((Path(__file__).parent / "golden.json").read_text("utf-8"))["casos"]
pasaron = 0

for caso in casos:
    respuesta, similitud = responder(caso["pregunta"])

    if caso["abstencion_esperada"]:
        # Esta prueba pasa cuando el sistema NO responde.
        ok = respuesta is None
        detalle = f"se abstuvo (similitud {similitud:.2f})" if ok else "RESPONDIÓ, y no debía"
    elif respuesta is None:
        ok, detalle = False, f"se abstuvo de más (similitud {similitud:.2f})"
    else:
        # No comparamos la respuesta completa: solo las cadenas clave.
        faltan = [c for c in caso["debe_contener"] if normalizar(c) not in normalizar(respuesta)]
        ok, detalle = not faltan, "ok" if not faltan else f"faltó: {faltan}"

    pasaron += ok
    print(f"  [{'PASA ' if ok else 'FALLA'}]  {caso['id']:<22} {detalle}")

print(f"\n  RESULTADO: {pasaron} de {len(casos)} pruebas pasaron")
print("\n  Ahora tienes una forma de saber si un cambio de prompt, de chunk size")
print("  o de modelo mejoró o empeoró el sistema. Antes solo tenías una opinión.")
print("\n  >> En serio: RAGAS / promptfoo")
