"""CP3 — Retrieval, todavía SIN generar.

    python checkpoints/cp3_retrieval.py

Miramos qué recupera el sistema antes de dejar que un modelo escriba nada. Si
generamos primero, cuando la respuesta salga mal no vamos a poder distinguir si
el modelo alucinó o si nunca le llegó la información.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.indice import buscar, construir_indice  # noqa: E402

LINEA = "=" * 78

# Query fija: la misma en el ensayo y en el vivo.
PREGUNTA = "¿Cuál es el monto de la cuota de inscripción del Instituto Nébula?"
TOP_K = 4

# PASO 1 — El índice.
indice = construir_indice(cargar_corpus("corpus"), verboso=True)

# PASO 2 — Buscar.
#
# Dentro de buscar(), la pregunta se embebe con task_type="RETRIEVAL_QUERY".
# Los chunks se embebieron con "RETRIEVAL_DOCUMENT". Distinto a propósito.
resultados = buscar(indice, PREGUNTA, k=TOP_K)

# PASO 3 — Mirar lo que trajo. Distancia coseno: 0.0 = idénticos.
print()
print(LINEA)
print(f"PREGUNTA: {PREGUNTA}")
print(LINEA)

for posicion, resultado in enumerate(resultados, start=1):
    vista = " ".join(resultado.chunk.texto[:150].split())
    print(f"  #{posicion}  distancia {resultado.distancia:.4f}   "
          f"{resultado.chunk.fuente} (.{resultado.chunk.formato})")
    print(f"      «{vista}...»")

print()
print(LINEA)
print("        ¿ESTÁ LA RESPUESTA EN ESTOS 4 CHUNKS?")
print(LINEA)
