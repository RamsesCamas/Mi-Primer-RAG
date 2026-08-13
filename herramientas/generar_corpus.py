"""Genera los tres PDF del corpus del Instituto Nébula.

ESTE SCRIPT NO SE CORRE EN CLASE. Los PDF ya vienen commiteados en corpus/.
Solo se usa si hay que regenerarlos. Requiere requirements-dev.txt (reportlab).

    python herramientas/generar_corpus.py

Los tres PDF están diseñados a propósito para que la extracción con pypdf salga
de distinta calidad, porque esa diferencia es el material didáctico del CP0:

  1. reglamento_academico.pdf  -> dos columnas, se extrae INTERCALADO
  2. tabulador_precios.pdf     -> tabla + encabezado/pie repetidos, se DESTRUYE
  3. folleto_admisiones.pdf    -> flujo normal, se extrae BIEN

Nota de diseño: el contenido va como estructuras de datos de Python aquí abajo
y no como archivos .md aparte, porque en estos tres documentos lo que importa
no es la prosa sino la POSICIÓN de cada línea en la página. Un .md no puede
expresar "esta línea se dibuja antes que aquella aunque se vea a la derecha",
que es exactamente lo que rompe la extracción.
"""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as canvas_mod
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

CORPUS = Path(__file__).resolve().parent.parent / "corpus"

ANCHO, ALTO = LETTER


# ---------------------------------------------------------------------------
# 1. Reglamento académico a dos columnas
# ---------------------------------------------------------------------------
#
# Por qué se rompe: dibujamos línea por línea ALTERNANDO entre la columna
# izquierda y la derecha a la misma altura. El flujo interno del PDF queda
# "izq1, der1, izq2, der2, ...", que es como lo emiten muchas herramientas
# reales de maquetación. pypdf extrae en ese orden interno, no en el orden
# visual, así que las dos columnas salen entreveradas y las frases se parten.

REGLAMENTO_COL_IZQ = [
    # --- página 1, columna izquierda ---
    [
        "REGLAMENTO ACADÉMICO",
        "Instituto Nébula",
        "Vigente a partir del 1 de enero de 2026",
        "",
        "TÍTULO PRIMERO",
        "DE LAS PERSONAS PARTICIPANTES",
        "",
        "Artículo 1. Se considera persona",
        "participante quien haya formalizado su",
        "registro en alguno de los cursos del",
        "Programa de Especialización en",
        "Ingeniería de IA y se encuentre al",
        "corriente en sus obligaciones",
        "administrativas ante la Coordinación de",
        "Administración Escolar.",
        "",
        "Artículo 2. La calidad de persona",
        "participante se pierde por conclusión del",
        "periodo, por baja voluntaria presentada",
        "por escrito, o por suspensión derivada de",
        "adeudo mayor a treinta días naturales.",
        "",
        "Artículo 3. Son obligaciones de la",
        "persona participante asistir a las sesiones",
        "sincrónicas, entregar las prácticas en las",
        "fechas señaladas y observar las normas",
        "de convivencia del campus.",
        "",
        "TÍTULO SEGUNDO",
        "DE LA EVALUACIÓN",
    ],
    # --- página 2, columna izquierda ---
    [
        "Artículo 8. La revisión de una",
        "calificación se solicita dentro de los tres",
        "días hábiles siguientes a su publicación,",
        "mediante el formato disponible en el",
        "campus, y la resuelve la persona titular",
        "del curso en un plazo de cinco días",
        "hábiles.",
        "",
        "Artículo 9. El examen de recuperación se",
        "presenta por única vez y sustituye",
        "únicamente la calificación del examen",
        "parcial, nunca la de las prácticas ni la del",
        "proyecto final.",
        "",
        "TÍTULO CUARTO",
        "DE LAS SANCIONES",
        "",
        "Artículo 10. La entrega de trabajo ajeno",
        "como propio se sanciona con la",
        "anulación de la entrega en primera",
        "ocasión y con la baja del curso en caso de",
        "reincidencia, sin devolución de la cuota",
        "de inscripción ni del monto de",
        "colegiatura cubierto.",
        "",
        "Artículo 11. Las sanciones las impone la",
        "Coordinación Académica, oída la persona",
        "interesada, y son recurribles ante el",
        "comité de revisión dentro de los cinco",
        "días hábiles siguientes a su notificación.",
    ],
]

REGLAMENTO_COL_DER = [
    # --- página 1, columna derecha ---
    [
        "Artículo 4. La evaluación de cada curso",
        "se integra con las prácticas, el examen",
        "parcial y el proyecto final, en las",
        "proporciones que establezca el temario",
        "vigente del curso correspondiente.",
        "",
        "Artículo 5. La calificación mínima",
        "aprobatoria es de 7.0 en todos los cursos",
        "del tronco de Ingeniería de IA. Las",
        "calificaciones se expresan en escala de",
        "0 a 10 con un decimal.",
        "",
        "Artículo 6. Quien no alcance la",
        "calificación mínima aprobatoria podrá",
        "presentar examen de recuperación,",
        "previo pago de la cuota de recuperación",
        "señalada en el tabulador vigente del",
        "periodo.",
        "",
        "TÍTULO TERCERO",
        "DE LOS PROCEDIMIENTOS",
        "",
        "Artículo 7. Todo trámite se presenta a",
        "través del campus del Instituto Nébula,",
        "sección Trámites, y genera un acuse",
        "automático con folio de seguimiento que",
        "ampara la fecha de presentación para",
        "efectos de cómputo de plazos.",
        "",
        "",
    ],
    # --- página 2, columna derecha ---
    [
        "TÍTULO QUINTO",
        "DE LAS CONSTANCIAS",
        "",
        "Artículo 12. La constancia de",
        "participación se expide a quien haya",
        "aprobado el curso y se encuentre sin",
        "adeudo. La constancia indica la clave del",
        "curso, por ejemplo NBL-204, el periodo y",
        "el número de horas.",
        "",
        "Artículo 13. La expedición de",
        "constancias adicionales causa la cuota",
        "señalada en el tabulador vigente y no es",
        "reembolsable en ningún caso.",
        "",
        "TRANSITORIOS",
        "",
        "Primero. El presente reglamento entra en",
        "vigor el 1 de enero de 2026 y deja sin",
        "efecto el reglamento anterior.",
        "",
        "Segundo. Los asuntos iniciados antes de",
        "la entrada en vigor se resuelven conforme",
        "al reglamento anterior.",
        "",
        "Tercero. La Coordinación Académica",
        "resolverá lo no previsto en este",
        "reglamento.",
        "",
        "",
    ],
]


def generar_reglamento(destino: Path) -> None:
    c = canvas_mod.Canvas(str(destino), pagesize=LETTER)
    x_izq, x_der = 2.0 * cm, 11.2 * cm
    y_inicial = ALTO - 2.5 * cm
    interlinea = 0.62 * cm

    for pagina, (izq, der) in enumerate(zip(REGLAMENTO_COL_IZQ, REGLAMENTO_COL_DER)):
        c.setFont("Helvetica", 10)
        y = y_inicial
        # Aquí está el truco: alternamos izquierda/derecha renglón por renglón.
        for linea_izq, linea_der in zip(izq, der):
            if linea_izq:
                c.drawString(x_izq, y, linea_izq)
            if linea_der:
                c.drawString(x_der, y, linea_der)
            y -= interlinea
        c.setFont("Helvetica", 8)
        c.drawString(x_izq, 1.8 * cm, f"Reglamento Académico · página {pagina + 1} de 2")
        c.showPage()

    c.save()


# ---------------------------------------------------------------------------
# 2. Tabulador de cuotas: tabla, encabezado y pie repetidos en cada página
# ---------------------------------------------------------------------------
#
# Por qué se rompe: la tabla NO se dibuja con el objeto Table de reportlab sino
# celda por celda con drawString posicional, y además se dibuja POR COLUMNAS,
# no por filas: primero toda la columna "Clave" de arriba a abajo, luego toda la
# columna "Concepto", y así. Varias herramientas de exportación de hojas de
# cálculo emiten el texto agrupado por columna, no por fila.
#
# El resultado al extraer es demoledor y es justo el punto de la clase: pypdf no
# hace extracción de tablas, sigue el orden interno del documento, y entonces los
# montos quedan como un bloque de números sueltos, separados del concepto al que
# pertenecen. Con chunks de 500 caracteres, el concepto y su monto ni siquiera
# caen en el mismo chunk. Encima el encabezado y el pie se repiten en las tres
# páginas y terminan apareciendo en medio del contenido extraído.

PIE_REPETIDO = "Instituto Nébula · uso interno · pág."
ENCABEZADO_REPETIDO = "TABULADOR DE CUOTAS Y APORTACIONES 2026 — DOCUMENTO CONTROLADO"

TABULADOR_PAGINAS = [
    {
        "titulo": "Sección I. Cuotas ordinarias",
        "columnas": ["Clave", "Concepto", "Monto MXN", "Vigencia"],
        "filas": [
            ["C-001", "Cuota de inscripción por periodo", "4,850.00", "2026-B"],
            ["C-002", "Monto de colegiatura mensual", "3,200.00", "2026-B"],
            ["C-003", "Costo total del periodo", "11,250.00", "2026-B"],
            ["C-004", "Cuota de reactivación de registro", "1,150.00", "2026-B"],
            ["C-005", "Cuota de cambio de grupo", "620.00", "2026-B"],
            ["C-006", "Cuota de diferimiento de periodo", "1,900.00", "2026-B"],
            ["C-007", "Asesoría individual adicional", "540.00", "2026-B"],
            ["C-008", "Constancia adicional impresa", "310.00", "2026-B"],
            ["C-009", "Constancia adicional digital", "180.00", "2026-B"],
            ["C-010", "Reposición de credencial", "260.00", "2026-B"],
        ],
    },
    {
        "titulo": "Sección II. Cuotas de evaluación",
        "columnas": ["Clave", "Concepto", "Monto MXN", "Vigencia"],
        "filas": [
            ["E-001", "Cuota de recuperación NBL-101", "690.00", "2026-B"],
            ["E-002", "Cuota de recuperación NBL-118", "740.00", "2026-B"],
            ["E-003", "Cuota de recuperación NBL-204", "780.00", "2026-B"],
            ["E-004", "Cuota de recuperación NBL-231", "780.00", "2026-B"],
            ["E-005", "Cuota de recuperación NBL-240", "820.00", "2026-B"],
            ["E-006", "Examen de acreditación equivalente", "1,240.00", "2026-B"],
            ["E-007", "Revisión de calificación extemporánea", "430.00", "2026-B"],
            ["E-008", "Reposición de examen parcial NBL-204", "780.00", "2026-B"],
            ["E-009", "Dictamen académico especial", "1,050.00", "2026-B"],
            ["E-010", "Certificación de horas cursadas", "395.00", "2026-B"],
        ],
    },
    {
        "titulo": "Sección III. Recargos y notas",
        "columnas": ["Clave", "Concepto", "Monto MXN", "Vigencia"],
        "filas": [
            ["R-001", "Recargo por quincena de atraso", "5% del saldo", "2026-B"],
            ["R-002", "Recargo por reposición de examen NBL-204", "780.00", "2026-B"],
            ["R-003", "Recargo por pago rechazado", "180.00", "2026-B"],
            ["R-004", "Descuento egresado sobre inscripción", "-15%", "2026-B"],
            ["R-005", "Descuento pago anticipado del periodo", "-8%", "2026-B"],
            ["R-006", "Descuento grupal desde tres personas", "-10%", "2026-B"],
            ["R-007", "Los descuentos no son acumulables", "n/a", "2026-B"],
            ["R-008", "Montos expresados sin impuestos", "n/a", "2026-B"],
            ["R-009", "Vigencia sujeta a revisión trimestral", "n/a", "2026-B"],
            ["R-010", "Autoriza Administración Escolar", "n/a", "2026-B"],
        ],
    },
]


def generar_tabulador(destino: Path) -> None:
    c = canvas_mod.Canvas(str(destino), pagesize=LETTER)
    x_cols = [2.0 * cm, 4.2 * cm, 13.0 * cm, 16.5 * cm]

    for i, pagina in enumerate(TABULADOR_PAGINAS, start=1):
        # Encabezado repetido en las tres páginas.
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2.0 * cm, ALTO - 1.6 * cm, ENCABEZADO_REPETIDO)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.0 * cm, ALTO - 3.0 * cm, pagina["titulo"])

        y_encabezado = ALTO - 4.2 * cm
        y_primera_fila = y_encabezado - 0.75 * cm

        # Celda por celda y COLUMNA POR COLUMNA: aquí se destruye la estructura.
        # Recorremos j = columna en el bucle externo y la fila en el interno, de
        # modo que el orden interno del PDF queda "todas las claves, todos los
        # conceptos, todos los montos, todas las vigencias".
        for j, x in enumerate(x_cols):
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x, y_encabezado, pagina["columnas"][j])
            c.setFont("Helvetica", 9)
            y = y_primera_fila
            for fila in pagina["filas"]:
                c.drawString(x, y, fila[j])
                y -= 0.75 * cm

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(
            2.0 * cm,
            y - 0.8 * cm,
            "Los montos de esta sección se aplican conforme al reglamento académico vigente.",
        )

        # Pie repetido en las tres páginas.
        c.setFont("Helvetica", 8)
        c.drawString(2.0 * cm, 1.5 * cm, f"{PIE_REPETIDO} {i} de 3")
        c.showPage()

    c.save()


# ---------------------------------------------------------------------------
# 3. Folleto de admisiones: el PDF que sí se extrae bien
# ---------------------------------------------------------------------------

FOLLETO = [
    ("titulo", "Instituto Nébula"),
    ("subtitulo", "Programa de Especialización en Ingeniería de IA"),
    (
        "cuerpo",
        "El Instituto Nébula es una academia en línea dedicada a la formación "
        "práctica de personas que construyen sistemas de inteligencia artificial. "
        "El Programa de Especialización en Ingeniería de IA está integrado por "
        "cinco cursos que se cursan en periodos de ocho semanas.",
    ),
    (
        "cuerpo",
        "Todas las sesiones son sincrónicas y quedan grabadas en el campus dentro "
        "de las veinticuatro horas siguientes. Ningún curso del programa requiere "
        "tarjeta gráfica dedicada, porque los ejercicios están diseñados para "
        "correr en equipo de cómputo común o contra servicios de inferencia "
        "remota de nivel gratuito.",
    ),
    (
        "cuerpo",
        "La cohorte del periodo 2026-B inicia el 9 de septiembre de 2026. Las "
        "inscripciones se abren el 3 de agosto y cierran el 4 de septiembre de "
        "2026. El registro se formaliza cubriendo la cuota de inscripción "
        "correspondiente al periodo.",
    ),
    (
        "cuerpo",
        "El curso NBL-204, Sistemas de Recuperación Aumentada, es el tercero del "
        "tronco de ingeniería y requiere haber aprobado NBL-101 y NBL-118. Lo "
        "imparte Renata Solís, quien también es responsable de NBL-231.",
    ),
    (
        "cuerpo",
        "Para conocer los montos vigentes de cada concepto consulta el tabulador "
        "del periodo o escribe a la Coordinación de Administración Escolar, cuyo "
        "horario de atención es de lunes a viernes de nueve a diecisiete horas.",
    ),
]


def generar_folleto(destino: Path) -> None:
    hojas = getSampleStyleSheet()
    estilos = {
        "titulo": ParagraphStyle(
            "t", parent=hojas["Title"], fontName="Helvetica-Bold", fontSize=20
        ),
        "subtitulo": ParagraphStyle(
            "s", parent=hojas["Heading2"], fontName="Helvetica-Bold", fontSize=13
        ),
        "cuerpo": ParagraphStyle(
            "c", parent=hojas["BodyText"], fontName="Helvetica", fontSize=10, leading=15
        ),
    }

    doc = SimpleDocTemplate(
        str(destino),
        pagesize=LETTER,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )
    flujo = []
    for tipo, texto in FOLLETO:
        flujo.append(Paragraph(texto, estilos[tipo]))
        flujo.append(Spacer(1, 0.35 * cm))
    doc.build(flujo)


# ---------------------------------------------------------------------------

def main() -> None:
    CORPUS.mkdir(exist_ok=True)
    trabajos = [
        ("reglamento_academico.pdf", generar_reglamento),
        ("tabulador_precios.pdf", generar_tabulador),
        ("folleto_admisiones.pdf", generar_folleto),
    ]
    for nombre, funcion in trabajos:
        destino = CORPUS / nombre
        funcion(destino)
        print(f"Generado: {destino.relative_to(CORPUS.parent)} "
              f"({destino.stat().st_size:,} bytes)")

    print("\nListo. Verifica la extracción con: python checkpoints/cp0_corpus.py")


if __name__ == "__main__":
    main()
