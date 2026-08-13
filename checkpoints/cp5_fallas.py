"""CP5 — Las tres fallas.

    python checkpoints/cp5_fallas.py        # las tres
    python checkpoints/cp5_fallas.py 2      # solo la segunda

  1. Chunk size equivocado
  2. Elegir el recuperador sin medir
  3. El modelo rellenando huecos con su prior

Todos los números que imprime se calculan en el momento. No hay nada
hardcodeado: si cambias el corpus, cambian los números.

Lo que hay que decir en voz alta está en GUION.md, no aquí.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.generacion import ensamblar_prompt, formatear_contexto, generar  # noqa: E402
from rag.indice import (  # noqa: E402
    buscar,
    buscar_bm25,
    buscar_hibrido,
    construir_indice,
)

LINEA = "=" * 78

PREGUNTA_COSTO = "¿Cuál es el monto de la cuota de inscripción del Instituto Nébula?"
PREGUNTA_COLOQUIAL = "¿cuánto cuesta?"
PREGUNTA_SIGLA = "¿qué es el examen NBL-204-P1?"
PREGUNTA_SIN_RESPUESTA = "¿Cuál es la política de propiedad intelectual sobre el proyecto final?"

INSTRUCCION_DEBIL = (
    "Eres el asistente del Instituto Nébula. Responde la pregunta de la "
    "persona usuaria de forma útil y completa."
)


def responde_el_costo(chunk):
    """Un dato útil es un número JUNTO A SU CONCEPTO.

    No basta con que aparezca "4,850": ese número también sale suelto en una
    columna del tabulador, despegado de su etiqueta por la extracción del PDF.
    Un chunk así no responde nada.
    """
    return "4,850" in chunk.texto and "cuota de inscripción" in chunk.texto.lower()


def rango(resultados, predicado):
    """Posición del primer resultado que cumple el predicado, o None."""
    for posicion, resultado in enumerate(resultados, start=1):
        if predicado(resultado.chunk):
            return posicion
    return None


def falla_1(documentos):
    print(LINEA)
    print("FALLA 1 — CHUNK SIZE EQUIVOCADO")
    print(LINEA)

    # Mismo corpus, misma pregunta, dos segmentaciones distintas.
    tamanos_de_contexto = {}
    for tamano, traslape in [(2000, 0), (500, 80)]:
        indice = construir_indice(documentos, tamano, traslape, verboso=False)
        resultados = buscar(indice, PREGUNTA_COSTO, k=4)
        contexto = formatear_contexto(resultados)
        chunk = resultados[rango(resultados, responde_el_costo) - 1].chunk
        tamanos_de_contexto[tamano] = len(contexto)

        # Cuántos temas distintos van dentro del chunk que trae la respuesta.
        # En markdown, cada "##" es un tema. El chunk grande mete varios.
        temas = chunk.texto.count("## ")

        print(f"\n  chunk_size={tamano}, overlap={traslape}  "
              f"->  {len(indice.chunks)} chunks")
        print(f"    contexto que se manda al modelo : {len(contexto):,} caracteres")
        print(f"    el dato llega dentro de un chunk de {len(chunk.texto):,} caracteres, "
              f"que mete {temas} tema{'s' if temas != 1 else ''}")
        for i, r in enumerate(resultados, 1):
            print(f"      #{i}  {r.chunk.id:<32} {len(r.chunk.texto):>5} caracteres")

    proporcion = tamanos_de_contexto[2000] / tamanos_de_contexto[500]
    print(f"\n  El chunk grande SÍ contiene la respuesta, pero mete varios temas en")
    print(f"  un solo vector: su embedding es el promedio de todos ellos y no")
    print(f"  representa bien a ninguno. Y le mandas al modelo {proporcion:.1f} veces más")
    print(f"  texto para responder exactamente lo mismo.")


def falla_2(indice):
    print(LINEA)
    print("FALLA 2 — ELEGIR EL RECUPERADOR SIN MEDIR")
    print(LINEA)
    print("\n  Ningún documento dice 'cuánto' ni 'cuesta': dicen 'cuota de")
    print("  inscripción', 'monto de colegiatura'. Y NBL-204-P1 solo aparece")
    print("  literal en un chunk. Dos problemas opuestos.")
    print("\n  Posición dentro de los 4 chunks que le mandamos al modelo:\n")

    # Dos preguntas, dos objetivos distintos, los tres recuperadores.
    casos = [
        (PREGUNTA_COLOQUIAL, responde_el_costo),
        (PREGUNTA_SIGLA, lambda c: c.id == "temario_nbl204.md#004"),
    ]
    metodos = [
        ("densa (embeddings)", lambda p: buscar(indice, p, k=4)),
        ("léxica (BM25)", lambda p: buscar_bm25(indice, p, k=4)),
        ("híbrida (RRF k=60)", lambda p: buscar_hibrido(indice, p, k=4)),
    ]

    print(f"  {'':<22}{'¿cuánto cuesta?':>20}{'¿examen NBL-204-P1?':>24}")
    for nombre, buscar_con in metodos:
        posiciones = []
        for pregunta, objetivo in casos:
            posicion = rango(buscar_con(pregunta), objetivo)
            posiciones.append(f"posición {posicion}" if posicion else "NO LO ENCUENTRA")
        print(f"  {nombre:<22}{posiciones[0]:>20}{posiciones[1]:>24}")

    # BM25 no falla "un poco": no encuentra nada, porque busca palabras que no
    # existen en el corpus. Sus puntajes son literalmente cero.
    puntajes = [r.puntaje for r in buscar_bm25(indice, PREGUNTA_COLOQUIAL, k=4)]
    print(f"\n  Puntajes BM25 para 'cuánto cuesta': {[round(p, 2) for p in puntajes]}")

    print("\n  Los embeddings cruzan el puente de vocabulario solos: para eso son.")
    print("  BM25 solo falla completo. Y el híbrido EMPEORA la densa, porque RRF")
    print("  fusiona por posición y le dio rango de titular a un puntaje cero.")
    print("  Con la sigla se invierte todo: ahí la densa no alcanza a traer el")
    print("  chunk exacto y BM25 lo pone segundo.")
    print("\n  Híbrido no es 'mejor'. Cubre una debilidad distinta. Cuál tienes,")
    print("  solo se sabe midiendo, como acabamos de hacer.")


def falla_3(indice):
    print(LINEA)
    print("FALLA 3 — EL MODELO RELLENA CON SU PRIOR")
    print(LINEA)
    print(f"\n  {PREGUNTA_SIN_RESPUESTA}")
    print("  (esta respuesta no está en ningún archivo del corpus)\n")

    resultados = buscar(indice, PREGUNTA_SIN_RESPUESTA, k=4)
    contexto = formatear_contexto(resultados)

    # Mismo modelo, mismo contexto, mismos chunks. Lo único que cambia es la
    # instrucción de arriba del prompt.
    prompt_debil = (f"{INSTRUCCION_DEBIL}\n\n=== CONTEXTO ===\n{contexto}\n"
                    f"=== FIN ===\n\nPREGUNTA: {PREGUNTA_SIN_RESPUESTA}\n\nRESPUESTA:")
    respuesta_debil = generar(prompt_debil)
    respuesta_fuerte = generar(ensamblar_prompt(resultados, PREGUNTA_SIN_RESPUESTA))

    print(f"  SIN instrucción de restringirse al contexto "
          f"({len(respuesta_debil):,} caracteres):")
    print("-" * 78)
    print(respuesta_debil[:900])
    print("  [...]")
    print("-" * 78)
    print(f"\n  CON la instrucción ({len(respuesta_fuerte):,} caracteres):")
    print("-" * 78)
    print(respuesta_fuerte)
    print("-" * 78)

    print("\n  Busca 'suele', 'normalmente' o 'por lo general' en la primera.")
    print("  El Instituto Nébula no existe: no puede haber un 'normalmente'.")
    print("  Eso salió del promedio de academias que el modelo vio entrenando.")
    print("\n  Se arregló con una instrucción, y funcionó. Pero una instrucción no")
    print("  es una garantía: en el CP6 lo verificamos EN CÓDIGO.")


cuales = sys.argv[1:] or ["1", "2", "3"]
documentos = cargar_corpus("corpus")
indice = construir_indice(documentos, verboso=False)

if "1" in cuales:
    falla_1(documentos)
if "2" in cuales:
    falla_2(indice)
if "3" in cuales:
    falla_3(indice)

print()
print("  Ninguna de las tres es culpa del modelo. La 1 es de la segmentación,")
print("  la 2 de elegir sin medir, la 3 del prompt. En las tres, el modelo hizo")
print("  exactamente lo que se le pidió con lo que se le dio.")
