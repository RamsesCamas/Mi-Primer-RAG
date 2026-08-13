# Guion de la clase

Lo que dices tú en voz alta, checkpoint por checkpoint, con tiempos. El código
no lleva esta narración adentro a propósito: en pantalla se lee código, y lo
demás lo dices tú.

**Total: 120 minutos.** Los tiempos incluyen las preguntas de la audiencia.

| Bloque | Min | Acumulado |
|---|---|---|
| Apertura | 10 | 0:10 |
| CP0 — el corpus | 5 | 0:15 |
| CP1 — chunking | 15 | 0:30 |
| CP2 — embeddings | 20 | 0:50 |
| CP3 — retrieval | 10 | 1:00 |
| CP4 — generación | 15 | 1:15 |
| CP5 — las tres fallas | 25 | 1:40 |
| CP6 — producción | 15 | 1:55 |
| Cierre | 5 | 2:00 |

### Antes de empezar

- Corre `python checkpoints/cp2_embeddings.py` una vez para llenar `cache/`.
  Así ningún checkpoint espera a la API durante la clase.
- Ten dos terminales: una para correr, otra con el editor abierto.
- Si editaste el corpus, corre `python checkpoints/cp1_chunking.py --verificar`.

---

## Apertura (10 min)

No corras nada todavía. Abre `app.py` en la terminal:

```bash
python app.py "¿Cuál es el monto de la cuota de inscripción del Instituto Nébula?"
```

> Esto que acaban de ver responde `$4,850 MXN`. El Instituto Nébula no existe:
> me lo inventé para esta clase. Ese dato no está en internet, no está en los
> datos de entrenamiento de ningún modelo, no existe en ningún lugar del mundo
> más que en una carpeta de este repositorio.
>
> En dos horas ustedes van a haber construido esto, lo van a romper tres veces
> a propósito, y le van a poner medición encima para saber cuándo está mintiendo.

Define el término una sola vez:

> RAG son las siglas de *Retrieval Augmented Generation*. En español: buscar
> primero, y después pedirle al modelo que responda con lo que encontraste.
> Todo lo interesante está en el "buscar primero".

**Pregunta a la audiencia:** ¿quién ha visto a un modelo inventarse algo con
mucha seguridad? Deja que contesten treinta segundos. Ese es el problema que
vamos a atacar.

---

## CP0 — ¿de qué está hecho el corpus? (5 min)

```bash
python checkpoints/cp0_corpus.py
```

Sube por la salida hasta `reglamento_academico.pdf`.

> Miren esto. Este PDF tiene dos columnas. Al extraerlo, las frases de la
> columna izquierda y las de la derecha salieron intercaladas renglón por
> renglón. Léanlo en voz alta: no dice nada.

Ahora `tabulador_precios.pdf`:

> Y este es peor. Era una tabla de conceptos y montos. Al extraerla, los
> conceptos quedaron todos juntos en un bloque y los montos todos juntos en
> otro. Para saber cuánto cuesta la reposición del examen NBL-204 habría que
> contar posiciones. Esa información, en la práctica, se perdió.

Contrasta con `folleto_admisiones.pdf`:

> Y este PDF salió perfecto. Entonces el problema no es "los PDF". Es la
> estructura de cada documento.

**La frase que sostiene el resto de la clase:**

> Todavía no hemos hecho nada de RAG y ya perdimos información. El chunking no
> es el primer lugar donde se pierde; la extracción lo es.

Menciona `faq_mezclado.txt` de pasada: los `Ã³` son un archivo con la
codificación rota, y así llegan los corpus reales.

---

## CP1 — chunking (15 min)

Antes de correrlo, explica el problema:

> Un modelo no puede leerse los 32,000 caracteres del corpus en cada pregunta.
> Hay que partirlo en pedazos y guardar los pedazos. A esos pedazos les decimos
> chunks. La pregunta es dónde cortas.

```bash
python checkpoints/cp1_chunking.py
```

**Sobre la tabla por formato** (2 min):

> Fíjense en la columna de chunks cortos. Los `.md` producen seis chunks de
> menos de 200 caracteres, los PDF ninguno. No es que los PDF sean mejores: es
> que el markdown tiene secciones cortas de verdad y los PDF son un chorro de
> texto continuo que se corta donde caiga.

**Sobre los cuatro chunks** (10 min). Uno por uno:

1. **El limpio.** Se sostiene solo. Si te lo dan fuera de contexto, entiendes
   de qué habla. Ese es el objetivo.
2. **La frase cortada.** Termina en "dentro" y ahí muere. El chunk siguiente
   empieza con "del periodo señalado". La idea quedó partida en dos y ninguna
   de las dos mitades está completa. Esto pasa **todo el tiempo**.
3. **Las dos columnas.** Léelo en voz alta, en serio. Es el momento más
   didáctico de la clase. Y luego di: *esto va a entrar al índice exactamente
   igual que el chunk limpio, y se va a poder recuperar exactamente igual*.
4. **El pie de página en medio.** Señala `pág. 2 de 3` a media tabla, y el
   encabezado repetido justo después. Al pegar las páginas del PDF, la basura
   estructural quedó incrustada entre los datos.

**Cierre del bloque:**

> El chunking no arregla lo que la extracción rompió: lo reparte. Y un chunk
> malo no avisa que es malo. Pesa lo mismo que uno bueno.

---

## CP2 — embeddings (20 min)

Este es el bloque conceptual pesado. No lo corras hasta haber explicado la idea.

**En pizarra o con las manos** (5 min):

> Necesitamos que la computadora sepa que "cuota de inscripción" y "cuánto hay
> que pagar" significan lo mismo, aunque no compartan ni una palabra. La forma
> de lograrlo es convertir cada texto en una lista de números, de manera que
> textos con significados parecidos den listas de números parecidas.
>
> Esa lista de números se llama embedding. No hay nada más. Es una lista de
> números.

```bash
python checkpoints/cp2_embeddings.py
```

**Sobre las tres barras** (5 min):

> Las frases 1 y 2 dicen lo mismo con palabras distintas: 0.81. La 1 y la 3
> son las dos del curso pero de temas distintos: 0.59. La 1 contra una receta
> de sopa: 0.48.

**Este es el punto que casi nadie explica y hay que decirlo:**

> Fíjense que la sopa de fideo no da cero. Da 0.48. Estos modelos tienen un
> piso de similitud: dos textos cualesquiera en español ya comparten idioma y
> estructura, y eso solo ya los acerca. El número absoluto no significa nada.
> Lo que significa algo es el orden: 0.81 es mayor que 0.59 es mayor que 0.48.
>
> Guarden esto, porque más adelante vamos a poner un umbral, y de aquí sale.

**Sobre el `task_type` asimétrico** (5 min). Abre `rag/embeddings.py`:

> Los chunks se embeben diciéndole al modelo "esto es un documento" y las
> preguntas diciéndole "esto es una pregunta". Distinto a propósito. Una
> pregunta y un documento no son el mismo tipo de texto, aunque los procese el
> mismo modelo. Le decimos qué papel juega cada uno para que produzca vectores
> pensados para encontrarse, no para parecerse.

**Sobre la normalización** (3 min). Señala la línea `norma del vector: 1.000000`:

> Pedimos 768 dimensiones en vez de las 3072 por defecto, por costo y
> velocidad. Este modelo normaliza solo cuando le pides 3072. En cualquier otra
> dimensión hay que normalizar a mano. Si se te olvida, no truena nada: el
> sistema simplemente responde peor, y te vuelves loco buscando por qué.

**Corre el script otra vez** delante de ellos (2 min):

> Un segundo. Los vectores quedaron en `cache/` con una llave SHA-256 del
> texto. Sin esto no podría ensayar esta clase sin quedarme sin cuota.

---

## CP3 — retrieval, sin generar (10 min)

**Antes de correr, di por qué este orden importa:**

> Vamos a hacer una pregunta y a mirar qué encuentra. Sin generar nada
> todavía. Este orden no es capricho.

```bash
python checkpoints/cp3_retrieval.py
```

Lee los cuatro chunks en pantalla, despacio.

**La pausa importante** (3 min). Señala la pregunta impresa al final y no
digas nada durante unos segundos. Deja que la lean.

> ¿Está la respuesta en estos cuatro chunks?
>
> Fíjense en algo: el chunk número 1, el más cercano, **no trae el monto**.
> Trae la lista de lo que cubre la inscripción. El monto está en el número 2.
>
> Si el dato no estuviera en ninguno de los cuatro, ningún modelo del mundo
> podría responder bien. No hay nada que leer. Y si el dato sí está y la
> respuesta sale mal, entonces el problema es del modelo o del prompt.
>
> Son dos problemas distintos, con arreglos distintos. Mirar el retrieval antes
> de generar es lo que te deja distinguirlos, y es gratis.

---

## CP4 — generación (15 min)

```bash
python checkpoints/cp4_generacion.py
```

**Parte 1, sin RAG** (3 min): el modelo dice que no tiene esa información.

> Perfecto. Es lo correcto. No la tiene.

**Parte 2, el prompt completo** (7 min). Este es el momento desmitificador de
la clase. Desplázate por el prompt entero, sin prisa.

> Esto es lo que le mandamos al modelo. Una instrucción, cuatro pedazos de
> texto que sacamos de la búsqueda, y la pregunta al final. Pegado. Con
> comillas triples.
>
> Eso es todo el "aumento" de Retrieval Augmented Generation. Concatenar
> strings.

**Parte 3, la respuesta** (5 min):

> El modelo es el mismo de hace un minuto. Lo único que cambió es el texto que
> le pusimos delante de la pregunta.
>
> Un RAG no hace más listo al modelo. Le pone enfrente lo que necesita leer.
> Toda la ingeniería está en decidir qué ponerle enfrente, que es exactamente
> lo que hicimos en el checkpoint anterior.

---

## CP5 — las tres fallas (25 min)

El bloque más importante de la clase. Ocho minutos cada una.

### Falla 1 — chunk size (8 min)

```bash
python checkpoints/cp5_fallas.py 1
```

> Muchos piensan: pongo chunks grandes y así no corto ninguna frase a la mitad.
> Vamos a probarlo.

Señala los dos números clave:

> Con chunks de 2000, el dato llega dentro de un pedazo que mete cinco temas
> distintos. Ese chunk tiene un solo vector, y ese vector es el promedio de los
> cinco temas: no representa bien a ninguno. Por eso la búsqueda pierde
> puntería.
>
> Y además le estamos mandando al modelo tres veces más texto para responder
> exactamente lo mismo. Eso son tokens que pagas y ruido que el modelo tiene
> que ignorar.
>
> No hay un número mágico. 500 con 80 funciona para este corpus. Para otro
> corpus se mide y se ajusta. No se copia de un tutorial.

### Falla 2 — elegir el recuperador sin medir (9 min)

```bash
python checkpoints/cp5_fallas.py 2
```

Deja la tabla en pantalla todo el bloque.

> Los documentos del Instituto Nébula están escritos en registro formal: dicen
> "cuota de inscripción". Nadie pregunta así. La gente pregunta "¿cuánto
> cuesta?".

Recorre la tabla renglón por renglón:

> **Los embeddings lo resuelven.** Posición 2. No comparten ni una palabra con
> el documento y aun así lo encontraron. Para eso sirven. Buena noticia.
>
> **BM25 falla completo.** Y fíjense en los puntajes: cero, cero, cero, cero.
> No falló un poco. Busca las palabras de la pregunta y esas palabras no
> existen en ningún archivo. Esto es lo que tiene hoy el buscador interno de
> casi cualquier empresa.
>
> **Y ahora la sorpresa.** El híbrido, que es lo que todo el mundo recomienda
> en internet, lo **empeora**: de la posición 2 a la 4. RRF fusiona por
> posición, no por calidad. Le dio rango de titular al primer lugar de BM25 sin
> enterarse de que ese primer lugar tenía puntaje cero. Metimos ruido.

Ahora la segunda columna:

> Pero miren la otra pregunta. `NBL-204-P1` es un código exacto. Ahí la densa
> es la que no encuentra el chunk correcto, porque para un modelo semántico
> "NBL-204-P1" y "NBL-204" significan casi lo mismo. BM25 sí lo ve, porque para
> BM25 son dos cadenas distintas y punto.
>
> Híbrido no es "mejor". Cubre una debilidad distinta. Cuál de los dos
> problemas tienes solo se sabe midiendo, como acabamos de hacer.

### Falla 3 — el prior (8 min)

```bash
python checkpoints/cp5_fallas.py 3
```

> Le voy a preguntar algo cuya respuesta no está en ningún archivo del corpus.

Deja que lean la primera respuesta.

> Busquen las palabras "suele", "normalmente", "por lo general".
>
> El Instituto Nébula no existe. No puede haber un "normalmente". Todo eso
> salió del promedio de las academias que este modelo vio en su entrenamiento,
> y se lo atribuyó a esta.
>
> Y fíjense en lo peligroso que es: no es un error obvio. Son tres mil
> caracteres bien redactados, con viñetas, con formato de documento oficial.
> Nadie los va a leer completos antes de creerles.

Muestra la segunda respuesta:

> Mismo modelo, mismo contexto, mismos chunks. Lo único que cambió es la
> instrucción. Ahora dice "No tengo esa información".
>
> Abstenerse es una respuesta correcta. Un sistema que nunca dice "no sé" no es
> un sistema seguro: es un sistema que no sabe cuándo no sabe.

**El puente al CP6:**

> Ojo con la conclusión fácil. Lo arreglamos con una instrucción y funcionó.
> Pero una instrucción no es una garantía. Ahora vamos a ver la diferencia.

---

## CP6 — lo que falta para producción (15 min)

Marca el tono antes de correrlo:

> Esto es superficial a propósito. No les estoy enseñando observabilidad ni
> evaluación: les estoy enseñando que existen y que no son magia. Cuatro cosas,
> todas con Python estándar, sin instalar nada nuevo.

```bash
python checkpoints/cp6_produccion.py
```

**1. Monitoreo** (3 min):

> La generación se lleva el 99% del tiempo. Y ahora la frase importante: cuando
> un RAG responde mal, casi nunca es culpa de esa etapa. La etapa más barata en
> tiempo es la que más determina la calidad. Sin medir por etapa no sabes dónde
> estás perdiendo.

**2. Guardrails** (5 min). Es el bloque que cierra la clase conceptualmente.

Sobre el de entrada:

> "Capital de Mongolia" da 0.52, por debajo del umbral. Ni siquiera llamamos al
> modelo. Cero tokens. Y ese umbral de 0.62 no me lo inventé: lo calibré
> midiendo preguntas de dentro y de fuera del dominio. ¿Se acuerdan del piso de
> similitud del CP2? De ahí sale.

Sobre el de salida, señala los tres renglones:

> El prompt dice "cita siempre el archivo". Con la regla puesta, cita. Le quito
> la regla y deja de citar, y la respuesta sigue saliendo bonita: nada te
> avisa, solo el código lo detecta. Y la tercera es la mejor: **sí citó**, pero
> citó un archivo que nunca estuvo en el contexto. Se lo inventó.
>
> Por eso el guardrail no pregunta "¿citó?". Pregunta "¿citó algo que de verdad
> le pasamos?".
>
> **"El prompt dice que lo haga" no es un guardrail.** Un guardrail es código
> que verifica y que puede decir que no.

Si te alcanza el tiempo, cuenta la anécdota del `【 】`: la primera versión de
ese guardrail solo buscaba corchetes normales y daba por no citadas respuestas
que sí citaban. Los guardrails también hay que probarlos.

**3. Groundedness** (3 min):

> Para cada oración medimos qué proporción de sus palabras aparece en el
> contexto. La respuesta buena sale toda en verde. La inventada, toda en rojo.
>
> Y ahora la limitación, que es parte de la lección: esto es solapamiento de
> palabras y nada más. Una paráfrasis fiel le sale mal calificada, y una mentira
> escrita con las palabras del contexto se le cuela. Por eso las herramientas
> serias usan otro modelo como juez.

**4. Golden tests** (4 min):

> Ocho preguntas fijas. No comparo la respuesta completa: comparo dos o tres
> cadenas clave, cifras y nombres, porque la redacción cambia y los datos no.
>
> Y fíjense en la última. Esa prueba **pasa cuando el sistema no responde**.
> Abstenerse a tiempo es una función del sistema, y como cualquier función hay
> que probarla.

---

## Cierre (5 min)

> Ahora tienen una forma de saber si un cambio de prompt, de chunk size o de
> modelo mejoró o empeoró el sistema.
>
> Antes de esto solo tenían una opinión.

Invítalos a jugar:

```bash
python app.py
```

> Pregúntenle lo que quieran. Enciendan `/prompt` al menos una vez para ver el
> texto exacto que sale hacia el modelo. Y en el README hay una lista de cosas
> para cambiar de una en una: el número de chunks, el umbral, la instrucción.
> Cambien una, corran el CP6, y miren si las ocho pruebas siguen pasando.
>
> Eso es exactamente lo que hace un equipo de verdad.

**Puente a la siguiente sesión:** los golden tests vuelven en serio cuando
hablemos de agentes.

---

## Si algo sale mal en vivo

| Síntoma | Qué haces |
|---|---|
| Un checkpoint se queda pensando | Es la API. Sigue hablando, tarda 1-2 segundos. |
| `429` de Gemini o de Groq | Reintenta solo. Verás una línea `[429]`. Espera. |
| La respuesta del modelo salió distinta | Normal, `temperature=0` no garantiza texto idéntico. Los datos sí son los mismos. |
| Un chunk del CP1 no es el que esperabas | Alguien editó el corpus. Corre `cp1_chunking.py --verificar`. |
| Se cayó la red | CP0 y CP1 corren sin conexión. Sigue con esos y regresa. |
