"""CP4 — Generación.

    python checkpoints/cp4_generacion.py

La misma pregunta sin RAG y con RAG, e imprime el prompt completo antes de
mandarlo. Un RAG es concatenar strings; aquí se ve.

Lo que hay que decir en voz alta está en GUION.md, no aquí.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from rag.carga import cargar_corpus  # noqa: E402
from rag.generacion import MODELO_GROQ, ensamblar_prompt, generar  # noqa: E402
from rag.indice import buscar, construir_indice  # noqa: E402

LINEA = "=" * 78

# Dos datos que solo existen en el corpus del Instituto Nébula. Van en
# preguntas separadas porque viven en archivos distintos: preguntados juntos,
# el retrieval trae uno y no el otro, y el modelo se abstiene con razón.
PREGUNTA = "¿Cuál es el monto de la cuota de inscripción del Instituto Nébula?"
PREGUNTA_FECHA = "¿En qué fecha inicia la cohorte del periodo 2026-B?"

# PASO 1 — La pregunta pelada, sin contexto. El Instituto Nébula no existe:
# este dato no está en los datos de entrenamiento de ningún modelo.
print(LINEA)
print(f"SIN RAG  ({MODELO_GROQ})")
print(LINEA)
print(f"PREGUNTA: {PREGUNTA}\n")
print(generar(PREGUNTA))

# PASO 2 — Recuperar el contexto.
indice = construir_indice(cargar_corpus("corpus"), verboso=False)
resultados = buscar(indice, PREGUNTA, k=4)

# PASO 3 — Ensamblar: instrucción + contexto + pregunta. Esto es todo el
# "aumento" de Retrieval Augmented Generation.
prompt = ensamblar_prompt(resultados, PREGUNTA)

print()
print(LINEA)
print(f"EL PROMPT COMPLETO  ({len(prompt):,} caracteres, ~{len(prompt) // 4:,} tokens)")
print(LINEA)
print(prompt)

# PASO 4 — Generar con ese prompt.
print()
print(LINEA)
print("CON RAG")
print(LINEA)
print(generar(prompt))

# PASO 5 — Otra pregunta, mismo pipeline, sin volver a explicarlo.
resultados_fecha = buscar(indice, PREGUNTA_FECHA, k=4)
print()
print(LINEA)
print(f"OTRA PREGUNTA: {PREGUNTA_FECHA}")
print(LINEA)
print(generar(ensamblar_prompt(resultados_fecha, PREGUNTA_FECHA)))
