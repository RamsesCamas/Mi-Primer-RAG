"""CP0 — Inspección del corpus crudo.

    python checkpoints/cp0_corpus.py
    
Imprime, por archivo: formato, tamaño y los primeros 300 caracteres del texto
EXTRAÍDO. En los PDF eso no es lo mismo que el archivo en disco.

Lo que hay que decir en voz alta está en GUION.md, no aquí.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.carga import cargar_corpus  # noqa: E402

LINEA = "=" * 78

# PASO 1 — Leer el corpus. cargar_corpus() despacha por extensión:
# .md y .txt se leen directo, .pdf pasa por pypdf. No se limpia nada.
documentos = cargar_corpus("corpus")

# PASO 2 — Cuánto texto aportó cada formato.
print(LINEA)
print(f"CP0 — CORPUS DEL INSTITUTO NÉBULA: {len(documentos)} archivos")
print(LINEA)

for formato in ("md", "txt", "pdf"):
    grupo = [d for d in documentos if d.formato == formato]
    caracteres = sum(len(d.texto) for d in grupo)
    print(f"  .{formato:<4} {len(grupo):>2} archivos   {caracteres:>7,} caracteres")

# PASO 3 — Archivo por archivo, con una muestra del texto extraído.
for documento in documentos:
    print()
    print(LINEA)
    print(f"{documento.fuente}   (.{documento.formato}, "
          f"{len(documento.texto):,} caracteres extraídos)")
    print("-" * 78)

    muestra = documento.texto[:300]
    if muestra.strip():
        print(muestra)
    else:
        print("  (la extracción no devolvió texto para este archivo)")

print()
print(LINEA)
print("El chunking no es el primer lugar donde se pierde información.")
print("La extracción lo es.")
print(LINEA)
