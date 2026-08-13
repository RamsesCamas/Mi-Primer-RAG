"""Piezas del RAG del Instituto Nébula.

Cada módulo corresponde a una etapa del pipeline:

    carga.py       ->  del disco al texto crudo
    embeddings.py  ->  del texto a vectores (con caché y normalización)
    indice.py      ->  de los vectores a un índice consultable (denso + léxico)
    generacion.py  ->  del contexto recuperado a una respuesta
"""
