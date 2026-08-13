"""Índice: de los vectores a algo que se pueda consultar.

Contiene las dos formas de buscar que se comparan en la clase:

  - BÚSQUEDA DENSA (embeddings + Chroma): entiende el significado, se pierde
    con las siglas y los códigos raros.
  - BÚSQUEDA LÉXICA (BM25): no entiende nada, pero encuentra `NBL-204` exacto.

Y la forma de combinarlas: Reciprocal Rank Fusion.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import chromadb
from chromadb.errors import InvalidArgumentError, InvalidDimensionException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from rag.carga import Documento
from rag.embeddings import DIMENSION, embed_documentos, embed_pregunta

# Valores por defecto de la clase. El CP5 los cambia a propósito para romperlo.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# Cuántos índices llevamos construidos en este proceso. Solo sirve para que
# cada colección de Chroma tenga un nombre distinto (ver construir_indice).
_contador_indices = 0


@dataclass
class Chunk:
    """Un pedazo de documento, con su origen siempre a la vista.

    id: identificador estable, "archivo.md#007". Estable importa: de él depende
        que las demos salgan iguales en el ensayo y en vivo.
    """

    id: str
    texto: str
    fuente: str
    formato: str
    posicion: int


@dataclass
class Resultado:
    """Un chunk recuperado, con su distancia o su puntaje."""

    chunk: Chunk
    distancia: float | None = None
    puntaje: float | None = None


# --- Chunking --------------------------------------------------------------

def chunkear(
    documentos: list[Documento],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Parte cada documento en chunks, conservando de dónde vino cada uno.

    RecursiveCharacterTextSplitter intenta cortar primero en los separadores
    más "grandes" (dos saltos de línea, luego uno, luego espacio) y solo parte a
    la mitad de una palabra si no le queda otra. Eso funciona bien en texto con
    estructura y bastante peor en el texto que sacamos de los PDF, donde los
    saltos de línea ya no significan lo que parecen.
    """
    partidor = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[Chunk] = []
    for documento in documentos:
        pedazos = partidor.split_text(documento.texto)
        for posicion, texto in enumerate(pedazos):
            chunks.append(
                Chunk(
                    id=f"{documento.fuente}#{posicion:03d}",
                    texto=texto,
                    fuente=documento.fuente,
                    formato=documento.formato,
                    posicion=posicion,
                )
            )
    return chunks


# --- Tokenización para BM25 ------------------------------------------------

def tokenizar(texto: str) -> list[str]:
    """Minúsculas, sin acentos, partido en palabras y números.

    Quitar acentos importa en este corpus: los .md están bien escritos
    ("recuperación") y los .txt no ("recuperacion"). Sin normalizar, BM25 los
    trataría como palabras distintas.

    `NBL-204` queda como ["nbl", "204"], y la pregunta que trae `NBL-204`
    produce los mismos dos tokens. Eso es justo lo que hace que BM25 acierte
    donde los embeddings se diluyen.
    """
    sin_acentos = unicodedata.normalize("NFKD", texto.lower())
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", sin_acentos)


# --- El índice -------------------------------------------------------------

class Indice:
    """Chunks + colección de Chroma + índice BM25, todo junto."""

    def __init__(self, chunks: list[Chunk], coleccion, bm25: BM25Okapi):
        self.chunks = chunks
        self.coleccion = coleccion
        self.bm25 = bm25
        self._por_id = {c.id: c for c in chunks}

    def chunk_por_id(self, id_chunk: str) -> Chunk:
        return self._por_id[id_chunk]


def construir_indice(
    documentos: list[Documento],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    nombre_coleccion: str | None = None,
    verboso: bool = True,
) -> Indice:
    """Chunkea, embebe y mete todo en una colección de Chroma en memoria."""
    chunks = chunkear(documentos, chunk_size, chunk_overlap)
    if verboso:
        print(f"  {len(chunks)} chunks de {len(documentos)} documentos "
              f"(chunk_size={chunk_size}, overlap={chunk_overlap})")

    vectores = embed_documentos([c.texto for c in chunks], verboso=verboso)

    # EphemeralClient = todo en memoria. Cada corrida arranca limpia y no
    # arrastramos estado entre el ensayo y el vivo.
    global _contador_indices
    _contador_indices += 1
    cliente = chromadb.EphemeralClient()
    nombre = nombre_coleccion or f"nebula_{chunk_size}_{chunk_overlap}_{_contador_indices}"

    # Dos detalles que NO son opcionales:
    #   embedding_function=None -> los vectores los calculamos nosotros. Si no
    #     lo pasas, Chroma puede cargar su función por defecto, que arrastra
    #     onnxruntime y una descarga de modelo. Justo lo que no queremos en vivo.
    #   space="cosine" -> el default de Chroma es L2 y toda la explicación de la
    #     clase gira alrededor de la similitud coseno.
    # Detalle de Chroma que muerde: dentro de un mismo proceso, EphemeralClient()
    # devuelve SIEMPRE el mismo cliente, no uno nuevo. Si un script construye dos
    # índices (el CP5 lo hace: uno bueno y uno malo), el segundo choca con
    # "Collection already exists" si repite el nombre.
    #
    # Por eso el nombre automático lleva un contador: cada índice vive en su
    # propia colección y los dos siguen siendo consultables a la vez. Borrar la
    # anterior sería peor: dejaría colgado el índice que ya habíamos construido.
    if nombre in [c.name for c in cliente.list_collections()]:
        cliente.delete_collection(nombre)

    coleccion = cliente.create_collection(
        name=nombre,
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )

    try:
        coleccion.add(
            ids=[c.id for c in chunks],
            embeddings=vectores,
            documents=[c.texto for c in chunks],
            metadatas=[{"fuente": c.fuente, "formato": c.formato} for c in chunks],
        )
    except (InvalidArgumentError, InvalidDimensionException) as error:
        raise RuntimeError(
            "Chroma rechazó los embeddings por dimensión incorrecta.\n"
            f"  Estamos generando vectores de {DIMENSION} dimensiones.\n"
            "  La dimensión de una colección la fija el PRIMER embedding que "
            "entra, y ya no cambia.\n"
            "  Si cambiaste DIMENSION en rag/embeddings.py, borra el contenido "
            "de cache/ y vuelve a correr.\n"
            f"  Mensaje original de Chroma: {error}"
        ) from error

    bm25 = BM25Okapi([tokenizar(c.texto) for c in chunks])

    return Indice(chunks=chunks, coleccion=coleccion, bm25=bm25)


# --- Las tres formas de buscar ---------------------------------------------

def buscar(indice: Indice, pregunta: str, k: int = 4) -> list[Resultado]:
    """Búsqueda densa: embeddings + distancia coseno.

    La pregunta se embebe con RETRIEVAL_QUERY, no con RETRIEVAL_DOCUMENT.
    """
    vector_pregunta = embed_pregunta(pregunta)
    respuesta = indice.coleccion.query(query_embeddings=[vector_pregunta], n_results=k)

    resultados = []
    for id_chunk, distancia in zip(respuesta["ids"][0], respuesta["distances"][0]):
        resultados.append(
            Resultado(chunk=indice.chunk_por_id(id_chunk), distancia=float(distancia))
        )
    return resultados


def buscar_bm25(indice: Indice, pregunta: str, k: int = 4) -> list[Resultado]:
    """Búsqueda léxica: BM25 sobre los tokens, sin entender nada de significado."""
    puntajes = indice.bm25.get_scores(tokenizar(pregunta))
    mejores = sorted(range(len(puntajes)), key=lambda i: (-puntajes[i], i))[:k]
    return [
        Resultado(chunk=indice.chunks[i], puntaje=float(puntajes[i])) for i in mejores
    ]


def fusionar_rrf(
    listas: list[list[Resultado]], k: int = 4, constante: int = 60
) -> list[Resultado]:
    """Reciprocal Rank Fusion.

    Cada lista vota por sus resultados según la POSICIÓN en la que los puso, no
    según su puntaje. Un chunk que sale 1º en BM25 y 3º en densa suma
    1/(60+1) + 1/(60+3). La constante 60 es el valor del paper original; sirve
    para que la diferencia entre el 1º y el 2º no sea abismal.

    La gracia de RRF es que no hay que normalizar puntajes entre sistemas que
    miden cosas incomparables (una distancia coseno y un puntaje BM25 no viven
    en la misma escala). Solo se comparan posiciones.
    """
    puntajes: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}

    for lista in listas:
        for posicion, resultado in enumerate(lista, start=1):
            id_chunk = resultado.chunk.id
            puntajes[id_chunk] = puntajes.get(id_chunk, 0.0) + 1.0 / (constante + posicion)
            chunks[id_chunk] = resultado.chunk

    ordenados = sorted(puntajes.items(), key=lambda par: (-par[1], par[0]))
    return [
        Resultado(chunk=chunks[id_chunk], puntaje=puntaje)
        for id_chunk, puntaje in ordenados[:k]
    ]


def buscar_hibrido(indice: Indice, pregunta: str, k: int = 4, k_cada: int = 10) -> list[Resultado]:
    """Densa + léxica, fusionadas con RRF.

    Cada recuperador aporta k_cada candidatos y RRF se queda con los k mejores.
    Pedir más candidatos de los que devolvemos es intencional: si cada lista
    aportara solo 4, la fusión casi no tendría de dónde elegir.
    """
    densa = buscar(indice, pregunta, k=k_cada)
    lexica = buscar_bm25(indice, pregunta, k=k_cada)
    return fusionar_rrf([densa, lexica], k=k)
