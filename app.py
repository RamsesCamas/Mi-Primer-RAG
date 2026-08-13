"""RAG del Instituto Nébula — programa principal.

    python app.py                          # modo interactivo, pregunta lo que quieras
    python app.py "¿Quién imparte NBL-204?" # una sola pregunta y se sale

Este archivo es el pegamento: no implementa nada nuevo, solo llama en orden a
los cuatro módulos de rag/ que construimos durante la clase.

    rag/carga.py        cargar_corpus()      del disco al texto
    rag/embeddings.py   embed_pregunta()     del texto a vectores
    rag/indice.py       construir_indice()   los vectores, consultables
                        buscar()             la búsqueda
    rag/generacion.py   ensamblar_prompt()   instrucción + contexto + pregunta
                        generar()            la llamada al modelo

Todo el pipeline cabe en la función responder(), unas 20 líneas más abajo.
Léela: eso es un RAG completo.
"""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.embeddings import DIMENSION, MODELO_EMBEDDING  # noqa: E402
from rag.generacion import (  # noqa: E402
    MODELO_GROQ,
    citas_validas,
    ensamblar_prompt,
    generar,
)
from rag.indice import CHUNK_OVERLAP, CHUNK_SIZE, buscar, construir_indice  # noqa: E402

ANCHO = 78

# Cuántos chunks se le pasan al modelo.
TOP_K = 4

# Por debajo de esta similitud consideramos que la pregunta no es del dominio y
# ni siquiera llamamos al modelo. Calibrado en el CP6 contra este corpus:
# preguntas de dominio dan 0.65 a 0.81, preguntas de fuera dan 0.52 a 0.60.
UMBRAL_DOMINIO = 0.62

# Qué tanto detalle se imprime. Se cambia en caliente con /chunks y /prompt.
mostrar_chunks = True
mostrar_prompt = False


def barra(caracter: str = "=") -> str:
    return caracter * ANCHO


# ---------------------------------------------------------------------------
# El pipeline completo
# ---------------------------------------------------------------------------

def responder(indice, pregunta: str) -> None:
    """Una pregunta, de principio a fin. Esto es todo el RAG."""
    inicio = time.perf_counter()

    # 1. Buscar. La pregunta se embebe con RETRIEVAL_QUERY dentro de buscar().
    resultados = buscar(indice, pregunta, k=TOP_K)
    similitud_mejor = 1 - resultados[0].distancia

    # 2. Guardrail de entrada: si ni el chunk más parecido se acerca, la
    #    pregunta no es de este corpus. Nos ahorramos la llamada al modelo.
    if similitud_mejor < UMBRAL_DOMINIO:
        print()
        print(f"  [guardrail de entrada] similitud del mejor chunk: "
              f"{similitud_mejor:.4f} < {UMBRAL_DOMINIO}")
        print()
        print("  No tengo esa información: esa pregunta no está en la")
        print("  documentación del Instituto Nébula.")
        print()
        print("  (Ni siquiera llamé al modelo. Cero tokens gastados.)")
        print()
        return

    if mostrar_chunks:
        print()
        print(f"  Chunks recuperados (top {TOP_K}):")
        for posicion, resultado in enumerate(resultados, start=1):
            vista = " ".join(resultado.chunk.texto[:90].split())
            print(f"    #{posicion}  d={resultado.distancia:.4f}  "
                  f"{resultado.chunk.fuente} (.{resultado.chunk.formato})")
            print(f"        «{vista}...»")

    # 3. Ensamblar el prompt: instrucción + contexto + pregunta.
    prompt = ensamblar_prompt(resultados, pregunta)

    if mostrar_prompt:
        print()
        print(barra("-"))
        print("  PROMPT COMPLETO")
        print(barra("-"))
        for linea in prompt.splitlines():
            print(f"  | {linea}")
        print(barra("-"))

    # 4. Generar.
    respuesta = generar(prompt)
    transcurrido = time.perf_counter() - inicio

    # 5. Guardrail de salida: ¿citó un archivo que realmente recuperamos?
    citas = citas_validas(respuesta, resultados)

    print()
    print(barra("-"))
    for linea in respuesta.splitlines():
        print(f"  {linea}")
    print(barra("-"))
    if citas:
        print(f"  [cita verificada: {', '.join(sorted(set(citas)))}]  "
              f"{transcurrido:.1f}s")
    else:
        print(f"  [SIN CITA VÁLIDA — el prompt la pedía y el modelo no la puso]  "
              f"{transcurrido:.1f}s")
    print()


# ---------------------------------------------------------------------------
# Modo interactivo
# ---------------------------------------------------------------------------

AYUDA = """
  Escribe una pregunta y presiona Enter. Comandos disponibles:

    /chunks    muestra u oculta los chunks recuperados   (ahora: {chunks})
    /prompt    muestra u oculta el prompt completo       (ahora: {prompt})
    /ejemplos  algunas preguntas que este corpus sí responde
    /ayuda     esto
    /salir     salir (o Ctrl+D)
"""

EJEMPLOS = [
    "¿Cuál es el monto de la cuota de inscripción?",
    "¿En qué fecha inicia la cohorte del periodo 2026-B?",
    "¿Se necesita tarjeta gráfica para los cursos?",
    "¿Quién imparte el NBL-204 y qué otro curso da?",
    "¿Qué pasa si no alcanzo la calificación mínima?",
    "¿Cuáles son los prerrequisitos del NBL-204?",
    "¿Qué formas de pago se aceptan?",
    "¿Cuál es la política de reembolsos?",
]


def imprimir_ayuda() -> None:
    print(AYUDA.format(
        chunks="visibles" if mostrar_chunks else "ocultos",
        prompt="visible" if mostrar_prompt else "oculto",
    ))


def imprimir_ejemplos() -> None:
    print()
    print("  Preguntas que este corpus sí puede responder:")
    for ejemplo in EJEMPLOS:
        print(f"    - {ejemplo}")
    print()
    print("  Y prueba también algo que NO esté en el corpus, como")
    print("  «¿cuál es la capital de Mongolia?», para ver el guardrail de entrada.")
    print()


def procesar_comando(entrada: str) -> bool:
    """Devuelve True si la entrada era un comando y ya se atendió."""
    global mostrar_chunks, mostrar_prompt

    comando = entrada.lower()
    if comando in ("/salir", "/exit", "/quit", "salir"):
        raise SystemExit(0)
    if comando == "/ayuda":
        imprimir_ayuda()
        return True
    if comando == "/ejemplos":
        imprimir_ejemplos()
        return True
    if comando == "/chunks":
        mostrar_chunks = not mostrar_chunks
        print(f"  Chunks recuperados: "
              f"{'visibles' if mostrar_chunks else 'ocultos'}\n")
        return True
    if comando == "/prompt":
        mostrar_prompt = not mostrar_prompt
        print(f"  Prompt completo: "
              f"{'visible' if mostrar_prompt else 'oculto'}\n")
        return True
    if comando.startswith("/"):
        print(f"  No conozco el comando «{entrada}». Escribe /ayuda.\n")
        return True
    return False


def interactivo(indice) -> None:
    print("Escribe /ayuda para ver los comandos, o /ejemplos si no sabes qué "
          "preguntar.")
    print()

    while True:
        try:
            entrada = input("pregunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nHasta luego.\n")
            return

        if not entrada:
            continue
        if procesar_comando(entrada):
            continue

        try:
            responder(indice, entrada)
        except RuntimeError as error:
            # Cuota agotada, modelo dado de baja, clave faltante... Mensaje
            # entendible en vez de un traceback de 30 líneas.
            print()
            for linea in str(error).splitlines():
                print(f"  {linea}")
            print()


# ---------------------------------------------------------------------------

def main() -> None:
    print(barra())
    print("RAG DEL INSTITUTO NÉBULA")
    print(barra())
    print()
    print("Preparando el índice...")

    documentos = cargar_corpus("corpus")
    indice = construir_indice(documentos, verboso=True)

    print()
    print(f"  documentos    : {len(documentos)}")
    print(f"  chunks        : {len(indice.chunks)} "
          f"(de {CHUNK_SIZE} caracteres, {CHUNK_OVERLAP} de traslape)")
    print(f"  embeddings    : {MODELO_EMBEDDING} a {DIMENSION} dimensiones")
    print(f"  generación    : {MODELO_GROQ} con temperature=0")
    print(f"  chunks por consulta: {TOP_K}")
    print()
    print(barra())
    print()

    argumento = " ".join(sys.argv[1:]).strip()
    if argumento:
        print(f"pregunta> {argumento}")
        responder(indice, argumento)
    else:
        interactivo(indice)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        # Falta una clave, se cayó la API, etc. Sin traceback.
        print()
        for linea in str(error).splitlines():
            print(f"  {linea}")
        print()
        sys.exit(1)
