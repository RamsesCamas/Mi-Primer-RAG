"""CP1 — Chunking.

    python checkpoints/cp1_chunking.py
    python checkpoints/cp1_chunking.py --verificar   # después de editar el corpus

Parte los 14 documentos en chunks de 500/80, muestra la distribución por
formato y cuatro chunks completos elegidos para la clase.

Lo que hay que decir en voz alta está en GUION.md, no aquí.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.carga import cargar_corpus  # noqa: E402
from rag.indice import CHUNK_OVERLAP, CHUNK_SIZE, chunkear  # noqa: E402

LINEA = "=" * 78

# Los cuatro chunks de la demo, fijados por id.
#
# Son ids estables: "archivo#posicion". Si editas un archivo del corpus, los
# ids de ESE archivo se recorren y alguno puede dejar de ilustrar lo que dice
# aquí. Para eso está el modo --verificar, que revisa los cuatro y avisa.
EJEMPLOS = {
    "1. LIMPIO — markdown bien portado": "guia_instalacion.md#004",
    "2. FRASE CORTADA A LA MITAD": "politica_reembolsos.md#004",
    "3. PDF A DOS COLUMNAS — texto intercalado": "reglamento_academico.pdf#000",
    "4. PIE DE PÁGINA EN MEDIO DE LA TABLA": "tabulador_precios.pdf#003",
}

# PASO 1 — Cargar y partir.
documentos = cargar_corpus("corpus")
chunks = chunkear(documentos, CHUNK_SIZE, CHUNK_OVERLAP)
por_id = {c.id: c for c in chunks}

print(LINEA)
print(f"CP1 — CHUNKING  (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
print(LINEA)
print(f"{len(documentos)} documentos  ->  {len(chunks)} chunks")
print()

# PASO 2 — Distribución de tamaños POR FORMATO. La calidad del chunk depende
# del formato del que vino, y eso se tiene que ver en números.
print(f"{'formato':<9}{'chunks':>7}{'mín':>7}{'mediana':>9}{'máx':>7}{'cortos(<200)':>14}")
for formato in ("md", "txt", "pdf"):
    tamanos = [len(c.texto) for c in chunks if c.formato == formato]
    print(f"{'.' + formato:<9}{len(tamanos):>7}{min(tamanos):>7}"
          f"{int(statistics.median(tamanos)):>9}{max(tamanos):>7}"
          f"{sum(1 for t in tamanos if t < 200):>14}")

# PASO 3 — Los cuatro chunks, completos.
for titulo, id_chunk in EJEMPLOS.items():
    chunk = por_id.get(id_chunk)
    print()
    print(LINEA)
    print(f"CHUNK {titulo}")
    print(f"  {id_chunk}   ({len(chunk.texto) if chunk else 0} caracteres)")
    print("-" * 78)
    print(chunk.texto if chunk else f"  !! Ya no existe el id {id_chunk}. Corre --verificar.")


# --- Modo verificación ------------------------------------------------------
# Solo se usa si editaste el corpus. Comprueba que cada id siga existiendo y
# siga ilustrando el defecto que promete su título.

def _verificar():
    fin_de_oracion = tuple(".!?:;\"')")
    pruebas = {
        "guia_instalacion.md#004": ("no trae codificación rota", lambda c: "Ã" not in c.texto),
        "politica_reembolsos.md#004": ("no cierra la frase", lambda c: not c.texto.rstrip().endswith(fin_de_oracion)),
        "reglamento_academico.pdf#000": ("líneas de dos columnas entreveradas", lambda c: c.texto.count("\n") > 10),
        "tabulador_precios.pdf#003": ("pie de página en medio", lambda c: 40 < c.texto.find("uso interno · pág.") < len(c.texto) - 80),
    }
    print()
    print(LINEA)
    print("VERIFICACIÓN DE LOS CUATRO EJEMPLOS")
    print(LINEA)
    for id_chunk, (descripcion, prueba) in pruebas.items():
        chunk = por_id.get(id_chunk)
        ok = chunk is not None and prueba(chunk)
        print(f"  [{'OK  ' if ok else 'ROTO'}]  {id_chunk:<32} {descripcion}")
    print()
    print("Si alguno salió ROTO, busca a mano el chunk que sí ilustre el caso")
    print("y actualiza el diccionario EJEMPLOS de este archivo. No improvises en vivo.")


if "--verificar" in sys.argv:
    _verificar()
