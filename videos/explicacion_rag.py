"""Seis videos de ~30 segundos que explican el pipeline de un RAG.

Requiere Manim Community:  https://docs.manim.community/en/stable/

Renderizar los seis y copiarlos a Descargas:

    bash videos/renderizar.sh

Uno solo, en borrador rápido:

    manim -ql videos/explicacion_rag.py Chunking

Todo el texto usa Text (Pango), no Tex: no hace falta LaTeX y los acentos del
español salen bien.

Nota de composición: el cuadro es de 8 unidades de alto (de -4 a +4). El título
ocupa arriba y los subtítulos abajo, así que TODO el contenido tiene que caber
entre ARRIBA y ABAJO. Si algo se sale, se encima con los subtítulos.
"""

from manim import *

# --- Paleta ----------------------------------------------------------------

FONDO = "#12141C"
TINTA = "#E9ECEF"
TENUE = "#868E96"
AZUL = "#4C6EF5"
VERDE = "#37B24D"
ROJO = "#F03E3E"
AMBAR = "#F59F00"
MORADO = "#AE3EC9"

# Zona útil para el contenido, entre el título y los subtítulos.
ARRIBA = 2.25
ABAJO = -1.95
CENTRO = (ARRIBA + ABAJO) / 2
ALTO_UTIL = ARRIBA - ABAJO
ANCHO_UTIL = 12.6

config.background_color = FONDO


class EscenaBase(Scene):
    """Título arriba, subtítulos abajo. Igual en los seis videos."""

    def setup(self):
        self.subtitulo_actual = None
        self.titulo_actual = None

    def poner_titulo(self, texto):
        titulo = Text(texto, font_size=30, color=TINTA, weight=BOLD)
        titulo.to_edge(UP, buff=0.45)
        linea = Line(LEFT * 6.6, RIGHT * 6.6, stroke_width=1.5, color=TENUE)
        linea.next_to(titulo, DOWN, buff=0.25)
        self.play(FadeIn(titulo, shift=DOWN * 0.2), Create(linea), run_time=0.7)
        self.titulo_actual = VGroup(titulo, linea)

    def acomodar(self, grupo):
        """Encoge y centra un grupo para que quepa en la zona útil."""
        factor = min(ALTO_UTIL / grupo.height, ANCHO_UTIL / grupo.width, 1.0)
        grupo.scale(factor)
        grupo.move_to(UP * CENTRO)
        return grupo

    def decir(self, texto, espera=2.6):
        """Cambia el subtítulo de abajo. El texto va ya cortado en líneas."""
        nuevo = Text(texto, font_size=25, color=TINTA, line_spacing=1.0)
        nuevo.to_edge(DOWN, buff=0.42)
        if self.subtitulo_actual is None:
            self.play(FadeIn(nuevo, shift=UP * 0.15), run_time=0.4)
        else:
            self.play(
                FadeOut(self.subtitulo_actual, shift=UP * 0.15),
                FadeIn(nuevo, shift=UP * 0.15),
                run_time=0.4,
            )
        self.subtitulo_actual = nuevo
        self.wait(espera)

    def cerrar(self, texto, espera=3.0):
        """Frase final, sola en el centro. El título se queda."""
        # titulo_actual es un VGroup, pero sus partes se agregaron sueltas a la
        # escena. Hay que comparar contra cada parte, no contra el grupo.
        conservar = list(self.titulo_actual) if self.titulo_actual else []
        sobran = [m for m in self.mobjects
                  if not any(m is c for c in conservar)]
        self.play(*[FadeOut(m) for m in sobran], run_time=0.6)

        self.subtitulo_actual = None
        frase = Text(texto, font_size=30, color=AMBAR, line_spacing=1.15, weight=BOLD)
        if frase.width > ANCHO_UTIL:
            frase.scale(ANCHO_UTIL / frase.width)
        frase.move_to(UP * CENTRO)
        self.play(FadeIn(frase, scale=1.05), run_time=0.9)
        self.wait(espera)


def hoja(lineas=14, ancho=2.6, color=TENUE):
    """Un documento: un rectángulo con renglones simulados adentro."""
    renglones = VGroup()
    for i in range(lineas):
        largo = ancho * (0.95 if i % 4 else 0.55)
        renglones.add(Line(ORIGIN, RIGHT * largo, stroke_width=2.5, color=color))
    renglones.arrange(DOWN, buff=0.13, aligned_edge=LEFT)
    marco = SurroundingRectangle(
        renglones, color=color, stroke_width=2, buff=0.22, corner_radius=0.08
    )
    return VGroup(marco, renglones)


def palomita(color=VERDE, tamano=0.3):
    """Una palomita dibujada con dos líneas.

    A propósito no usamos el carácter de palomita: si la fuente que elija Pango
    en la máquina donde se renderice no lo tiene, saldría un cuadrito. Dos
    líneas se ven igual en todos lados.
    """
    marca = VMobject(stroke_color=color, stroke_width=5)
    marca.set_points_as_corners([
        LEFT * 0.45 * tamano + UP * 0.05 * tamano,
        DOWN * 0.45 * tamano,
        RIGHT * 0.6 * tamano + UP * 0.75 * tamano,
    ])
    return marca


def caja(texto, ancho=4.2, alto=1.0, color=AZUL, tamano=20, relleno=0.12):
    """Una caja con texto centrado, que se encoge si el texto no cabe."""
    marco = RoundedRectangle(
        width=ancho, height=alto, corner_radius=0.12,
        color=color, fill_color=color, fill_opacity=relleno, stroke_width=2.5,
    )
    etiqueta = Text(texto, font_size=tamano, color=TINTA, line_spacing=0.9)
    if etiqueta.width > ancho - 0.35:
        etiqueta.scale((ancho - 0.35) / etiqueta.width)
    etiqueta.move_to(marco)
    return VGroup(marco, etiqueta)


# ===========================================================================
# 1. CHUNKING
# ===========================================================================

class Chunking(EscenaBase):
    def construct(self):
        self.poner_titulo("1 · CHUNKING — partir los documentos")

        documento = hoja(lineas=13, ancho=2.6)
        nombre = Text("politica_reembolsos.md", font_size=18, color=TENUE)
        nombre.next_to(documento, UP, buff=0.2)
        izquierda = VGroup(documento, nombre)

        pedazos = VGroup()
        for i in range(4):
            pedazo = RoundedRectangle(
                width=3.0, height=0.72, corner_radius=0.08,
                color=AZUL, fill_color=AZUL, fill_opacity=0.18, stroke_width=2,
            )
            texto = Text(f"chunk #{i:03d}", font_size=16, color=TINTA)
            texto.move_to(pedazo)
            pedazos.add(VGroup(pedazo, texto))
        pedazos.arrange(DOWN, buff=0.3)

        flecha = Arrow(LEFT * 0.7, RIGHT * 0.7, buff=0,
                       color=TENUE, stroke_width=3,
                       max_tip_length_to_length_ratio=0.22)

        escena = VGroup(izquierda, flecha, pedazos).arrange(RIGHT, buff=0.8)
        self.acomodar(escena)

        self.play(Create(documento), FadeIn(nombre), run_time=1.0)
        self.decir("Un modelo no puede leerse los 32,000 caracteres del corpus\n"
                   "cada vez que alguien hace una pregunta.", 3.0)

        self.play(GrowArrow(flecha), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.3) for p in pedazos],
                              lag_ratio=0.18), run_time=1.4)
        self.decir("Se parte en pedazos de 500 caracteres. A esos pedazos\n"
                   "les decimos chunks, y son la unidad que vamos a buscar.", 3.2)

        # El traslape entre chunks consecutivos.
        traslape = VGroup()
        for a, b in zip(pedazos[:-1], pedazos[1:]):
            banda = Rectangle(
                width=pedazos[0].width, height=0.24,
                color=AMBAR, fill_color=AMBAR, fill_opacity=0.6, stroke_width=0,
            )
            banda.move_to((a.get_bottom() + b.get_top()) / 2)
            traslape.add(banda)

        etiqueta = Text("80 caracteres\nde traslape", font_size=18, color=AMBAR,
                        line_spacing=0.9)
        etiqueta.next_to(pedazos, RIGHT, buff=0.4)

        self.play(LaggedStart(*[FadeIn(b) for b in traslape], lag_ratio=0.15),
                  FadeIn(etiqueta), run_time=1.0)
        self.decir("Y se solapan un poco a propósito: si una idea queda partida\n"
                   "por el corte, al menos un chunk la tiene completa.", 3.4)

        self.decir("Sin ese traslape, una frase cortada a la mitad se pierde\n"
                   "en las dos mitades, y no la encuentra ninguna búsqueda.", 3.2)

        contador = Text("14 documentos  ->  90 chunks", font_size=26, color=VERDE)
        contador.next_to(escena, DOWN, buff=0.35)
        self.play(FadeIn(contador, shift=UP * 0.2), run_time=0.6)
        self.decir("Así queda el corpus entero: 14 documentos convertidos\n"
                   "en 90 pedazos manejables.", 3.0)

        self.cerrar("El chunking no arregla lo que la extracción rompió.\nLo reparte.")


# ===========================================================================
# 2. INDEXACIÓN
# ===========================================================================

class Indexacion(EscenaBase):
    def construct(self):
        self.poner_titulo("2 · INDEXACIÓN — del texto a los números")

        chunk = caja("«La cuota de inscripción\nes de $4,850 MXN»",
                     ancho=4.0, alto=1.15, color=AZUL, tamano=19)
        modelo = caja("gemini-embedding-001", ancho=3.4, alto=0.8,
                      color=MORADO, tamano=18)
        vector = Text("[ 0.021, -0.114,\n  0.087, 0.003, ... ]",
                      font_size=20, color=VERDE, line_spacing=0.9)

        f1 = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, color=TENUE, stroke_width=3,
                   max_tip_length_to_length_ratio=0.28)
        f2 = Arrow(LEFT * 0.4, RIGHT * 0.4, buff=0, color=TENUE, stroke_width=3,
                   max_tip_length_to_length_ratio=0.28)

        fila = VGroup(chunk, f1, modelo, f2, vector).arrange(RIGHT, buff=0.45)
        fila.move_to(UP * 1.35)
        pie = Text("768 números", font_size=17, color=TENUE)
        pie.next_to(vector, DOWN, buff=0.2)

        self.play(FadeIn(chunk), run_time=0.6)
        self.decir("Para comparar textos hay que convertirlos primero\n"
                   "en algo que se pueda medir: números.", 3.0)

        self.play(GrowArrow(f1), FadeIn(modelo), run_time=0.7)
        self.play(GrowArrow(f2), Write(vector), FadeIn(pie), run_time=1.1)
        self.decir("Cada chunk se convierte en una lista de 768 números.\n"
                   "Eso es un embedding. No hay nada más.", 3.2)

        # El espacio vectorial.
        plano = Rectangle(width=8.6, height=2.5, color=TENUE, stroke_width=1.5)
        plano.move_to(DOWN * 0.85)

        etiquetas = [
            ("cuota de inscripción", LEFT * 3.4 + DOWN * 0.3, VERDE),
            ("cuánto hay que pagar", LEFT * 3.0 + DOWN * 0.95, VERDE),
            ("monto de colegiatura", LEFT * 3.8 + DOWN * 1.55, VERDE),
            ("requisitos de hardware", RIGHT * 0.6 + DOWN * 1.55, AZUL),
        ]
        grupo = VGroup()
        for texto, posicion, color in etiquetas:
            punto = Dot(posicion, radius=0.085, color=color)
            marca = Text(texto, font_size=15, color=color)
            marca.next_to(punto, RIGHT, buff=0.15)
            grupo.add(VGroup(punto, marca))

        self.play(Create(plano), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(g, scale=1.2) for g in grupo],
                              lag_ratio=0.2), run_time=1.5)
        self.decir("Y el truco está en que textos con significados parecidos\n"
                   "producen listas de números parecidas.", 3.0)

        cerca = DashedLine(etiquetas[0][1], etiquetas[1][1],
                           color=VERDE, stroke_width=2.5)
        medida = Text("0.81", font_size=17, color=VERDE)
        medida.next_to(cerca.get_center(), LEFT, buff=0.15)
        self.play(Create(cerca), FadeIn(medida), run_time=0.8)
        self.decir("«cuota de inscripción» y «cuánto hay que pagar» no comparten\n"
                   "ni una sola palabra, y aun así quedan pegados.", 3.4)

        self.decir("Eso es lo que una búsqueda por palabras clave\n"
                   "no puede hacer de ninguna manera.", 2.8)

        self.cerrar("Buscar ya no es comparar palabras.\nEs medir distancias entre vectores.")


# ===========================================================================
# 3. LA BASE DE DATOS VECTORIAL
# ===========================================================================

class BaseVectorial(EscenaBase):
    def construct(self):
        self.poner_titulo("3 · LA BASE DE DATOS VECTORIAL")

        entrada = VGroup(*[
            Dot(radius=0.075, color=VERDE) for _ in range(6)
        ]).arrange(DOWN, buff=0.32)
        entrada.move_to(LEFT * 5.2 + UP * 0.15)
        etiqueta_entrada = Text("90 vectores", font_size=18, color=TENUE)
        etiqueta_entrada.next_to(entrada, UP, buff=0.3)

        cilindro = VGroup(
            Ellipse(width=3.2, height=0.7, color=MORADO,
                    fill_color=MORADO, fill_opacity=0.35, stroke_width=2.5),
            Rectangle(width=3.2, height=1.8, color=MORADO,
                      fill_color=MORADO, fill_opacity=0.18, stroke_width=0),
            Ellipse(width=3.2, height=0.7, color=MORADO,
                    fill_color=MORADO, fill_opacity=0.5, stroke_width=2.5),
        )
        cilindro[0].move_to(UP * 0.9)
        cilindro[2].move_to(DOWN * 0.9)
        cilindro.move_to(LEFT * 2.4 + UP * 0.15)
        nombre = Text("Chroma", font_size=23, color=TINTA, weight=BOLD)
        nombre.move_to(cilindro)

        self.play(FadeIn(entrada), FadeIn(etiqueta_entrada), run_time=0.6)
        self.play(Create(cilindro), FadeIn(nombre), run_time=0.8)
        self.play(LaggedStart(*[
            d.animate.move_to(cilindro.get_center()).scale(0.2).set_opacity(0)
            for d in entrada
        ], lag_ratio=0.12), run_time=1.6)
        self.decir("Los 90 vectores se guardan en una base de datos vectorial.\n"
                   "Aquí usamos Chroma, viviendo en memoria.", 3.2)

        filas = VGroup(
            caja("id:  costos_y_pagos.md#000", ancho=5.4, alto=0.6, color=AZUL, tamano=16),
            caja("vector:  [0.021, -0.114, ... ]", ancho=5.4, alto=0.6, color=VERDE, tamano=16),
            caja("texto:  «La cuota de inscripción...»", ancho=5.4, alto=0.6, color=TENUE, tamano=16),
            caja("fuente: costos_y_pagos.md  ·  formato: md", ancho=5.4, alto=0.6, color=AMBAR, tamano=16),
        )
        filas.arrange(DOWN, buff=0.16).move_to(RIGHT * 3.4 + UP * 0.15)

        self.play(LaggedStart(*[FadeIn(f, shift=LEFT * 0.25) for f in filas],
                              lag_ratio=0.2), run_time=1.6)
        self.decir("De cada chunk se guarda su vector, pero también su id,\n"
                   "su texto original y de qué archivo salió.", 3.2)

        self.decir("Ese último dato es el que después nos deja citar la fuente\n"
                   "y verificar que la respuesta no se la inventó.", 3.2)

        metrica = Text("distancia: coseno", font_size=21, color=AMBAR)
        metrica.next_to(cilindro, DOWN, buff=0.4)
        self.play(FadeIn(metrica, shift=UP * 0.2), run_time=0.6)
        self.decir("Y le decimos explícitamente que mida por coseno, que es\n"
                   "como se comparan significados. No es lo que trae por defecto.", 3.4)

        self.cerrar("Ya tenemos un índice.\nTodavía nadie le ha preguntado nada.")


# ===========================================================================
# 4. RECUPERACIÓN
# ===========================================================================

class Recuperacion(EscenaBase):
    def construct(self):
        self.poner_titulo("4 · RECUPERACIÓN — buscar antes de responder")

        pregunta = caja("«¿Cuál es el monto de la\ncuota de inscripción?»",
                        ancho=4.0, alto=1.05, color=AMBAR, tamano=18)
        pregunta.move_to(LEFT * 4.6 + UP * 1.35)

        vector_pregunta = Text("[ 0.019, -0.098, ... ]", font_size=18, color=AMBAR)
        vector_pregunta.move_to(LEFT * 4.6 + UP * 0.15)
        flecha = Arrow(pregunta.get_bottom(), vector_pregunta.get_top(), buff=0.15,
                       color=TENUE, stroke_width=3, max_tip_length_to_length_ratio=0.3)

        self.play(FadeIn(pregunta), run_time=0.6)
        self.decir("La pregunta pasa por el mismo modelo de embeddings\n"
                   "que usamos con los chunks. Exactamente el mismo.", 3.0)

        self.play(GrowArrow(flecha), Write(vector_pregunta), run_time=0.9)

        plano = Rectangle(width=6.6, height=3.9, color=TENUE, stroke_width=1.5)
        plano.move_to(RIGHT * 3.0 + UP * 0.15)

        cercanos_datos = [
            (RIGHT * 2.3 + UP * 0.95, "d=0.19"),
            (RIGHT * 3.7 + UP * 0.45, "d=0.20"),
            (RIGHT * 2.0 + DOWN * 0.25, "d=0.22"),
            (RIGHT * 4.0 + DOWN * 0.65, "d=0.24"),
        ]
        lejanos_datos = [
            RIGHT * 5.2 + UP * 1.55, RIGHT * 1.2 + DOWN * 1.35,
            RIGHT * 4.9 + DOWN * 1.5, RIGHT * 1.4 + UP * 1.6,
        ]

        cercanos = VGroup(*[Dot(p, radius=0.085, color=AZUL) for p, _ in cercanos_datos])
        lejanos = VGroup(*[Dot(p, radius=0.075, color=TENUE) for p in lejanos_datos])

        self.play(Create(plano), FadeIn(lejanos), FadeIn(cercanos), run_time=0.9)
        self.decir("Los 90 chunks ya viven en este espacio desde que\n"
                   "construimos el índice.", 2.8)

        centro = RIGHT * 3.0 + UP * 0.2
        punto_pregunta = Dot(centro, radius=0.12, color=AMBAR)
        self.play(ReplacementTransform(vector_pregunta.copy(), punto_pregunta),
                  run_time=1.0)
        self.decir("La pregunta cae en ese mismo espacio.\n"
                   "A partir de aquí, buscar es pura geometría.", 3.0)

        radio = Circle(radius=0.2, color=AMBAR, stroke_width=2.5).move_to(centro)
        self.play(Create(radio), run_time=0.3)
        self.play(radio.animate.scale(6.5).set_stroke(opacity=0.55), run_time=1.3)

        marcas = VGroup()
        for i, (p, distancia) in enumerate(cercanos_datos):
            marca = Text(f"#{i + 1}  {distancia}", font_size=15, color=VERDE)
            marca.next_to(Dot(p), UP, buff=0.12)
            marcas.add(marca)
        self.play(cercanos.animate.set_color(VERDE),
                  LaggedStart(*[FadeIn(m) for m in marcas], lag_ratio=0.15),
                  run_time=1.3)
        self.decir("Nos quedamos con los 4 más cercanos. Esos, y solo esos,\n"
                   "van a llegar al modelo.", 3.2)

        self.cerrar("¿Está la respuesta en estos 4 chunks?\nMíralo ANTES de generar nada.")


# ===========================================================================
# 5. GENERACIÓN
# ===========================================================================

class Generacion(EscenaBase):
    def construct(self):
        self.poner_titulo("5 · GENERACIÓN — armar el prompt")

        instruccion = caja("INSTRUCCIÓN\nResponde solo con el contexto. Cita la fuente.",
                           ancho=5.6, alto=0.95, color=MORADO, tamano=16)
        contexto = caja("CONTEXTO\nlos 4 chunks que acabamos de recuperar",
                        ancho=5.6, alto=0.95, color=AZUL, tamano=16)
        consulta = caja("PREGUNTA\n¿Cuál es el monto de la cuota de inscripción?",
                        ancho=5.6, alto=0.95, color=AMBAR, tamano=16)

        partes = VGroup(instruccion, contexto, consulta)
        partes.arrange(DOWN, buff=0.25).move_to(LEFT * 3.6 + UP * 0.4)

        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.25) for p in partes],
                              lag_ratio=0.25), run_time=1.6)
        self.decir("El prompt son tres cosas: una instrucción, el contexto que\n"
                   "acabamos de recuperar, y la pregunta al final.", 3.2)

        # Las tres partes se funden en el prompt y desaparecen: ya están dentro.
        prompt = caja("PROMPT\n~620 tokens", ancho=2.7, alto=1.4,
                      color=VERDE, tamano=19)
        prompt.move_to(LEFT * 3.2 + UP * 0.55)
        copias = [p.copy() for p in partes]
        self.add(*copias)
        self.play(*[Transform(c, prompt) for c in copias],
                  *[FadeOut(p) for p in partes], run_time=1.4)
        self.play(FadeIn(prompt), *[FadeOut(c) for c in copias], run_time=0.4)
        self.decir("Se pegan en un solo texto. Literalmente sumar strings:\n"
                   "eso es todo el «aumento» de Retrieval Augmented Generation.", 3.4)

        modelo = caja("gpt-oss-120b\ntemperature = 0", ancho=2.9, alto=1.05,
                      color=MORADO, tamano=18)
        modelo.move_to(RIGHT * 0.6 + UP * 0.55)
        flecha = Arrow(prompt.get_right(), modelo.get_left(), buff=0.2,
                       color=TENUE, stroke_width=3, max_tip_length_to_length_ratio=0.25)
        self.play(GrowArrow(flecha), FadeIn(modelo), run_time=0.9)

        respuesta = caja("«La cuota de inscripción es de $4,850 MXN por periodo.»\n"
                         "[costos_y_pagos.md]",
                         ancho=9.4, alto=1.1, color=VERDE, tamano=18, relleno=0.2)
        respuesta.move_to(LEFT * 0.4 + DOWN * 1.35)
        self.play(FadeIn(respuesta, shift=UP * 0.2), run_time=0.9)
        self.decir("El modelo responde con el dato correcto y cita el archivo\n"
                   "del que lo sacó.", 3.0)

        self.decir("Ese dato no existe en internet ni en el entrenamiento de\n"
                   "ningún modelo. Solo está en nuestro corpus.", 3.2)

        self.cerrar("El modelo no se hizo más listo.\nLe pusimos enfrente lo que necesitaba leer.")


# ===========================================================================
# 6. EVALUACIÓN
# ===========================================================================

class Evaluacion(EscenaBase):
    def construct(self):
        self.poner_titulo("6 · EVALUACIÓN — ¿cómo sé que funciona?")

        casos = [
            ("cuota de inscripción", "4850"),
            ("inicio de la cohorte", "9 de septiembre"),
            ("colegiatura mensual", "3200"),
            ("costo total", "11250"),
            ("calificación mínima", "7.0"),
            ("quién imparte NBL-204", "renata solis"),
            ("¿pide tarjeta gráfica?", "no"),
        ]

        izquierdas = VGroup(*[Text(p, font_size=18, color=TINTA) for p, _ in casos])
        izquierdas.add(Text("¿capital de Mongolia?", font_size=18, color=AMBAR))
        derechas = VGroup(*[Text(f"debe contener «{e}»", font_size=16, color=TENUE)
                            for _, e in casos])
        derechas.add(Text("NO debe responder", font_size=16, color=AMBAR))

        izquierdas.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        for izq, der in zip(izquierdas, derechas):
            der.next_to(izq, RIGHT, buff=0.3)
            der.align_to(izquierdas, LEFT).shift(RIGHT * 3.3)

        tabla = VGroup(izquierdas, derechas)
        self.acomodar(tabla)
        tabla.shift(LEFT * 1.1)

        self.play(LaggedStart(*[FadeIn(VGroup(i, d), shift=RIGHT * 0.2)
                                for i, d in zip(izquierdas, derechas)],
                              lag_ratio=0.1), run_time=1.8)
        self.decir("Ocho preguntas fijas, con el dato que cada respuesta\n"
                   "tiene que traer.", 3.0)

        self.decir("No comparamos la respuesta completa: solo cadenas clave,\n"
                   "porque la redacción cambia y las cifras no.", 3.2)

        palomitas = VGroup()
        for izq in izquierdas[:-1]:
            marca = palomita(VERDE)
            marca.next_to(derechas, RIGHT, buff=0.55).align_to(izq, DOWN)
            palomitas.add(marca)
        self.play(LaggedStart(*[FadeIn(p, scale=1.3) for p in palomitas],
                              lag_ratio=0.18), run_time=1.7)
        self.decir("Siete preguntas cuya respuesta sí está en el corpus.\n"
                   "Las siete pasan.", 2.8)

        marca_final = palomita(AMBAR)
        marca_final.next_to(derechas, RIGHT, buff=0.55).align_to(izquierdas[-1], DOWN)
        nota = Text("pasa porque se abstuvo", font_size=16, color=AMBAR)
        nota.next_to(marca_final, RIGHT, buff=0.25)
        self.play(FadeIn(marca_final, scale=1.3), FadeIn(nota), run_time=0.8)
        self.decir("La octava es distinta: su respuesta no está en el corpus,\n"
                   "y la prueba pasa cuando el sistema NO responde.", 3.4)

        resultado = Text("8 / 8", font_size=42, color=VERDE, weight=BOLD)
        resultado.move_to(RIGHT * 5.4 + UP * 1.55)
        self.play(FadeIn(resultado, scale=1.2), run_time=0.7)
        self.wait(1.0)

        self.cerrar("Ahora sabes si un cambio mejoró o empeoró el sistema.\n"
                    "Antes solo tenías una opinión.")
