"""CP2 — Embeddings.

    python checkpoints/cp2_embeddings.py

Convierte los chunks en vectores y los guarda en Chroma. Antes, compara cuatro
frases sueltas para ver qué mide realmente la similitud coseno.

La primera corrida llama a la API. La segunda es instantánea: los vectores
quedan en cache/ con llave SHA-256.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.embeddings import (  # noqa: E402
    DIMENSION,
    MODELO_EMBEDDING,
    embed_pregunta,
    similitud_coseno,
)
from rag.indice import construir_indice  # noqa: E402

LINEA = "=" * 78

FRASES = [
    "El monto de la cuota de inscripción del periodo",
    "Cuánto hay que pagar para inscribirse al curso",
    "La tarjeta gráfica no es necesaria para el curso",
    "Receta de sopa de fideo con jitomate",
]

print(LINEA)
print(f"CP2 — EMBEDDINGS  ({MODELO_EMBEDDING}, {DIMENSION} dimensiones)")
print(LINEA)

# PASO 1 — Cuatro frases sueltas a vectores.
vectores = [embed_pregunta(f) for f in FRASES]

print(f"Cada frase es ahora una lista de {len(vectores[0])} números. Eso es todo.")
print(f"Los primeros 4 valores de la frase 1: "
      f"{[round(v, 5) for v in vectores[0][:4]]}")
print()

# PASO 2 — Compararlas. Similitud coseno: 1.0 = misma dirección.
for i, j in [(0, 1), (0, 2), (0, 3)]:
    similitud = similitud_coseno(vectores[i], vectores[j])
    print(f"  frase {i + 1} vs frase {j + 1}:  {similitud:.4f}  "
          f"{'█' * int(similitud * 40)}")
for i, frase in enumerate(FRASES, 1):
    print(f"    {i}. {frase}")
print()
print("Las frases 1 y 2 no comparten casi ninguna palabra y son las más")
print("parecidas. La 4 no llega a 0: estos modelos tienen un piso de similitud.")
print("El número absoluto no dice nada; lo que dice algo es el ORDEN.")
print()

# PASO 3 — El corpus completo.
#
# Los CHUNKS se embeben con task_type="RETRIEVAL_DOCUMENT" y las PREGUNTAS con
# "RETRIEVAL_QUERY". Es asimétrico a propósito: una pregunta y un documento no
# son el mismo tipo de texto aunque los procese el mismo modelo.
print(LINEA)
indice = construir_indice(cargar_corpus("corpus"), verboso=True)
print(LINEA)

# PASO 4 — Comprobar que los vectores están normalizados.
#
# gemini-embedding-001 auto-normaliza SOLO en 3072 dimensiones. Pedimos 768,
# así que lo hacemos a mano en rag/embeddings.py. Si se olvida, la similitud
# coseno sale mal y el retrieval se degrada sin avisar.
muestra = indice.coleccion.get(ids=[indice.chunks[0].id], include=["embeddings"])
vector = muestra["embeddings"][0]
norma = sum(v * v for v in vector) ** 0.5

print(f"  vectores en Chroma  : {indice.coleccion.count()}")
print(f"  dimensión           : {len(vector)}")
print(f"  norma del vector    : {norma:.6f}   (debe ser 1.0)")
print(f"  métrica             : coseno   (el default de Chroma es L2)")
print(f"  embedding_function  : {indice.coleccion._embedding_function}   "
      f"(en None: los vectores los calculamos nosotros)")
