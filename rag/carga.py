"""Carga del corpus: del disco al texto crudo.

Regla de oro de este módulo: NO SE LIMPIA NADA.

El corpus del Instituto Nébula es sucio a propósito. Trae markdown ordenado,
exports de chat, correos reenviados, un archivo con la codificación rota y tres
PDF de calidad de extracción muy distinta. Si aquí "arreglamos" el texto, la
clase pierde justo lo que tiene que ver: que la información se degrada mucho
antes de llegar al chunking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

# Extensiones que sabemos leer. Cualquier otra se ignora con aviso.
EXTENSIONES = {".md", ".txt", ".pdf"}


@dataclass
class Documento:
    """Un archivo del corpus ya leído.

    texto:   el contenido tal cual salió del disco o del extractor de PDF
    fuente:  el nombre del archivo (se usa como metadato en el índice)
    formato: "md", "txt" o "pdf" (sin el punto)
    """

    texto: str
    fuente: str
    formato: str


def _leer_texto_plano(ruta: Path) -> str:
    """Lee .md y .txt.

    errors="replace" es deliberado: corpus/faq_mezclado.txt trae la codificación
    rota a media página. Con errors="strict" el pipeline reventaría; con
    "replace" el archivo entra al corpus con su suciedad intacta, que es lo que
    queremos mostrar.
    """
    return ruta.read_text(encoding="utf-8", errors="replace")


def _leer_pdf(ruta: Path) -> str:
    """Lee un .pdf concatenando el texto extraído de cada página.

    Las páginas se pegan una tras otra sin meter ningún separador. Es la forma
    más común de hacerlo y también la que deja ver el problema: el encabezado y
    el pie que se repiten en cada página quedan incrustados en medio del texto,
    entre el final del contenido de una página y el principio de la siguiente.
    Hasta la manera de pegar las páginas es una decisión que afecta los chunks.

    extract_text() puede devolver None o cadena vacía en páginas sin capa de
    texto (por ejemplo un escaneo). No es un error: es información. La página
    aporta cero caracteres y así se refleja en el conteo del CP0.
    """
    lector = PdfReader(str(ruta))
    texto = ""
    for pagina in lector.pages:
        texto += pagina.extract_text() or ""
    return texto


def cargar_corpus(ruta: str | Path = "corpus") -> list[Documento]:
    """Recorre el directorio y despacha por extensión.

    Devuelve la lista ordenada por nombre de archivo. El orden importa: de él
    dependen los IDs de los chunks, y de los IDs depende que las demos de la
    clase salgan iguales en el ensayo y en vivo.
    """
    directorio = Path(ruta)
    if not directorio.is_dir():
        raise FileNotFoundError(
            f"No encuentro el directorio del corpus: {directorio.resolve()}\n"
            f"Corre los checkpoints desde la raíz del repositorio."
        )

    documentos: list[Documento] = []
    for archivo in sorted(directorio.iterdir()):
        if not archivo.is_file():
            continue
        extension = archivo.suffix.lower()
        if extension not in EXTENSIONES:
            print(f"  (ignorado, extensión desconocida: {archivo.name})")
            continue

        if extension == ".pdf":
            texto = _leer_pdf(archivo)
        else:
            texto = _leer_texto_plano(archivo)

        documentos.append(
            Documento(texto=texto, fuente=archivo.name, formato=extension.lstrip("."))
        )

    if not documentos:
        raise FileNotFoundError(
            f"El directorio {directorio.resolve()} no tiene archivos .md, .txt ni .pdf."
        )

    return documentos
