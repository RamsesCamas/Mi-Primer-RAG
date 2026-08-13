# Tu primer RAG

Repositorio de la clase en vivo de 2 horas. Construimos un sistema de
**recuperación aumentada** (RAG) de principio a fin, lo rompemos a propósito
tres veces, y le ponemos medición encima.

No necesitas saber nada de LLMs. Sí necesitas saber leer Python básico.

El corpus es la documentación de una academia ficticia, el **Instituto Nébula**.
Es ficticia a propósito: así ningún modelo puede saber las respuestas de
memoria, y todo lo que responda bien tiene que haberlo leído del corpus.

> **¿Vas a dar tú la clase?** Este README es para el alumnado. Lo que se dice en
> voz alta, con tiempos y pausas checkpoint por checkpoint, está en
> **[GUION.md](GUION.md)**. Los scripts no llevan esa narración adentro a
> propósito: en pantalla se lee código.

---

## Antes de la clase (haz esto hoy, no el día del vivo)

Son unos 10 minutos. Si lo dejas para el último momento, te vas a perder la
primera media hora de clase instalando cosas.

### 1. Python 3.10 o superior

```bash
python3 --version
```

Si el comando no existe o la versión es menor, instala Python primero.
En Windows usa `python` en lugar de `python3`.

### 2. Descarga el repositorio y crea el entorno virtual

```bash
cd tu-carpeta-de-trabajo
python3 -m venv .venv
```

Actívalo. En Linux y macOS:

```bash
source .venv/bin/activate
```

En Windows con PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Sabrás que funcionó porque aparece `(.venv)` al inicio de tu línea de terminal.
**Este paso se repite cada vez que abres una terminal nueva.**

> El entorno virtual no es opcional en esta clase. Varias de las bibliotecas que
> usamos tienen versiones viejas muy parecidas con otro nombre, y si las mezclas
> con las de tu sistema vas a pasar la clase depurando en vez de aprendiendo.

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

Tarda entre dos y cinco minutos.

### 4. Consigue las dos claves de acceso

Las dos son **gratuitas** y **no piden tarjeta**.

**Clave de Gemini** (para los embeddings):

1. Entra a <https://aistudio.google.com/apikey>
2. Inicia sesión con tu cuenta de Google
3. Botón **"Create API key"**
4. Copia la clave que aparece. Empieza con `AIza...`

**Clave de Groq** (para la generación):

1. Entra a <https://console.groq.com/keys>
2. Crea una cuenta o inicia sesión
3. Botón **"Create API Key"**, ponle cualquier nombre
4. Copia la clave. Empieza con `gsk_...`
5. **Cópiala ya**: Groq solo te la muestra una vez

### 5. Crea tu archivo `.env`

```bash
cp .env.example .env
```

Ábrelo con tu editor y pega cada clave después del signo igual, sin comillas
y sin espacios:

```
GEMINI_API_KEY=AIza...tu-clave-aqui
GROQ_API_KEY=gsk_...tu-clave-aqui
```

Guarda. El archivo `.env` ya está en `.gitignore`: nunca se sube a ningún
repositorio, y ningún script de esta clase lo imprime en pantalla.

### 6. Comprueba que todo quedó bien

```bash
python checkpoints/cp0_corpus.py
```

Si ves la lista de los 14 archivos del corpus con su formato y tamaño, ya estás.
Ese primer checkpoint ni siquiera usa las claves. Para probarlas:

```bash
python checkpoints/cp2_embeddings.py
```

La primera vez tarda unos segundos porque llama a la API. **La segunda es
instantánea**, porque los vectores quedan guardados en `cache/`.

---

## Los checkpoints

Cada uno corre **por sí solo**, sin depender de que hayas corrido el anterior.
Ninguno recibe argumentos (salvo el CP5, opcionalmente).

| Checkpoint | Qué hace | ¿Usa API? |
|---|---|---|
| `cp0_corpus.py` | Inspecciona el corpus crudo | No |
| `cp1_chunking.py` | Parte los documentos en chunks | No |
| `cp2_embeddings.py` | Convierte los chunks en vectores | Gemini |
| `cp3_retrieval.py` | Busca sin generar nada | Gemini |
| `cp4_generacion.py` | Arma el prompt y llama al modelo | Gemini + Groq |
| `cp5_fallas.py` | Rompe el sistema tres veces | Gemini + Groq |
| `cp6_produccion.py` | Monitoreo, guardrails, evaluación | Gemini + Groq |

### CP0 — ¿de qué está hecho el corpus?

Cada archivo con su formato, su tamaño y sus primeros 300 caracteres. Aquí se ve
que un PDF sale perfecto, otro con las columnas entreveradas y otro con la tabla
destruida. *El chunking no es el primer lugar donde se pierde información; la
extracción lo es.*

### CP1 — chunking

Parte los documentos en chunks de 500/80, muestra la distribución por formato y
cuatro chunks completos: uno limpio, uno que corta una frase a la mitad, uno del
PDF a dos columnas y uno con el pie de página a media tabla.

Los cuatro están fijados por id en el diccionario `EJEMPLOS`. Si editas el
corpus, corre `python checkpoints/cp1_chunking.py --verificar`.

### CP2 — embeddings

Compara cuatro frases sueltas para ver qué mide la similitud coseno, y después
embebe los 90 chunks y los guarda en Chroma. Fíjate en el `task_type`
asimétrico: los chunks van como `RETRIEVAL_DOCUMENT` y las preguntas como
`RETRIEVAL_QUERY`.

### CP3 — retrieval, sin generar

Una pregunta fija, los 4 chunks más cercanos, sus distancias, y una pregunta
impresa en pantalla: **¿está la respuesta en estos 4 chunks?** Si generas antes
de mirar esto, no vas a poder distinguir un fallo de recuperación de uno del
modelo.

### CP4 — generación

La misma pregunta sin RAG y con RAG, con el prompt completo impreso antes de
mandarlo. Un RAG es concatenar strings; aquí se ve.

### CP5 — las tres fallas

```bash
python checkpoints/cp5_fallas.py        # las tres
python checkpoints/cp5_fallas.py 2      # solo la segunda
```

1. **Chunk size equivocado**: 2000/0 contra 500/80, medido.
2. **Elegir el recuperador sin medir**: una tabla con lo que encuentran los
   embeddings, BM25 y la fusión híbrida (RRF) en dos preguntas opuestas.
3. **El modelo rellenando con su prior**: la misma pregunta con y sin
   instrucción de restringirse al contexto.

### CP6 — lo que falta para producción

Monitoreo por etapa, guardrails de entrada y salida, medición de apoyo en el
contexto, y 8 pruebas fijas en `checkpoints/golden.json`. Sin instalar nada
nuevo: todo con la biblioteca estándar.

---

## Pregúntale tú: `app.py`

Los checkpoints tienen preguntas fijas, porque son para explicar. Cuando quieras
preguntarle lo que se te ocurra, usa el programa principal:

```bash
python app.py
```

Arranca el índice una sola vez y te deja en un prompt:

```
pregunta> ¿Qué pasa si no alcanzo la calificación mínima?

  Chunks recuperados (top 4):
    #1  d=0.2838  reglamento_academico.pdf (.pdf)
    #2  d=0.2996  faq_mezclado.txt (.txt)
    ...
------------------------------------------------------------------------------
  Si no alcanzas la calificación mínima, puedes presentar el examen de
  recuperación y deberás cubrir la cuota correspondiente. [faq_mezclado.txt]
------------------------------------------------------------------------------
  [cita verificada: faq_mezclado.txt]  1.3s
```

También acepta una sola pregunta y se sale:

```bash
python app.py "¿Quién imparte el NBL-204?"
```

### Comandos dentro del programa

| Comando | Qué hace |
|---|---|
| `/chunks` | Muestra u oculta los chunks recuperados (por defecto visibles) |
| `/prompt` | Muestra u oculta el prompt completo que se le manda al modelo |
| `/ejemplos` | Preguntas que este corpus sí puede responder |
| `/ayuda` | La lista de comandos |
| `/salir` | Salir (o Ctrl+D) |

**Enciende `/prompt` al menos una vez.** Ver el texto exacto que sale hacia el
modelo, con el contexto pegado y todo, es la mejor forma de que se te quite la
idea de que un RAG es magia.

`app.py` no implementa nada nuevo: solo llama en orden a los cuatro módulos de
`rag/`. Toda la lógica está en la función `responder()`, que son unas 20 líneas
y trae los dos guardrails del CP6 puestos:

- **De entrada**: si la similitud del mejor chunk baja de 0.62, contesta que no
  tiene esa información **sin llamar al modelo**. Pruébalo con «¿cuál es la
  capital de Mongolia?».
- **De salida**: verifica en código que la respuesta cite un archivo que de
  verdad se recuperó. Si no, lo dice en pantalla.

### Ideas para experimentar

Abre `app.py` y cambia una cosa a la vez, luego vuelve a preguntar:

- `TOP_K = 4` → prueba con 1 y con 10. ¿A partir de cuántos chunks empeora?
- `UMBRAL_DOMINIO = 0.62` → súbelo a 0.75 y mira cuántas preguntas legítimas
  empieza a rechazar.
- En `rag/generacion.py`, edita `INSTRUCCION` y quítale la regla de citar.
- En `rag/indice.py`, cambia `CHUNK_SIZE` y `CHUNK_OVERLAP`.

Después de cada cambio corre `python checkpoints/cp6_produccion.py` y mira si
las 8 pruebas siguen pasando. Eso es exactamente lo que hace un equipo de
verdad: cambiar algo y tener una forma de saber si lo mejoró o lo empeoró.

---

## Estructura del repositorio

```
app.py           el programa principal: pregunta lo que quieras
GUION.md         el guion de la clase, con tiempos (para quien la imparte)
corpus/          14 documentos del Instituto Nébula (.md, .txt, .pdf)
rag/             el pipeline: carga, embeddings, índice, generación
checkpoints/     los siete scripts de la clase + golden.json
herramientas/    generador de los PDF (no se corre en clase)
cache/           vectores cacheados, se crea sola
```

### Sobre el corpus

Los 14 archivos ya vienen en el repositorio, **incluidos los PDF**. No tienes
que generarlos.

Es deliberadamente sucio y heterogéneo. Un corpus de markdowns limpios enseñaría
una mentira: en un sistema real la información llega en formatos distintos, con
calidades distintas, escrita por personas que no se pusieron de acuerdo. Hay
hasta una contradicción a propósito entre dos archivos (la política de
reembolsos en `.md` dice una cosa y las notas de junta en `.txt` dicen que se
actualizó). No la resolvemos en esta clase, pero conviene verla.

Si alguna vez quieres regenerar los PDF:

```bash
pip install -r requirements-dev.txt
python herramientas/generar_corpus.py
```

---

## Problemas frecuentes

### `ModuleNotFoundError: No module named 'google.genai'`

Instalaste el paquete equivocado. Son dos paquetes distintos con APIs
incompatibles:

```bash
pip uninstall google-generativeai      # el viejo
pip install google-genai               # el que usamos
```

El correcto se importa así: `from google import genai`. Si un tutorial dice
`import google.generativeai as genai`, ese tutorial es de 2024 o 2025 y no
aplica aquí.

### `model_decommissioned` o `model ... does not exist` de Groq

El modelo se dio de baja. Casi todos los tutoriales en línea usan
`llama-3.3-70b-versatile` o `llama-3.1-8b-instant`, y **Groq los apagó el 16 de
agosto de 2026**.

Este repositorio usa `openai/gpt-oss-120b`. Si también lo dan de baja algún día,
cambia la constante `MODELO_GROQ` en `rag/generacion.py` y revisa la lista
vigente en <https://console.groq.com/docs/deprecations>.

### `429 RESOURCE_EXHAUSTED` de Gemini

Se agotó la cuota gratuita del minuto o del día. El código ya reintenta solo,
con espera creciente. Si aun así falla:

- Espera unos minutos y vuelve a correr. **Lo que ya se embebió quedó en
  `cache/` y no se vuelve a pedir**, así que no pierdes el avance.
- Revisa tu consumo en <https://aistudio.google.com/>

### `429 rate_limit_exceeded` de Groq (tokens por minuto)

El tier gratuito de Groq limita **tokens por minuto**, no solo peticiones. El
CP6 hace once llamadas seguidas con contextos largos y lo alcanza sin problema.

El código ya reintenta solo con espera creciente, así que lo normal es que solo
veas una línea `[429] cuota de Groq alcanzada, reintento en 5s` y siga. Si
llegara a agotar los reintentos, espera un minuto completo y vuelve a correr:
los embeddings ya están en `cache/`, así que la corrida se reanuda rápido.

Si vas a correr varios checkpoints seguidos, déjales unos segundos entre uno y
otro.

### `InvalidArgumentError: Collection expecting embedding with dimension of 768`

Cambiaste `DIMENSION` en `rag/embeddings.py`. La dimensión de una colección de
Chroma la fija el primer vector que entra y ya no se puede cambiar.

Borra la caché y vuelve a correr:

```bash
rm -rf cache/
```

(En versiones anteriores de Chroma este error se llamaba
`InvalidDimensionException`. El código captura las dos.)

### Chroma intenta descargar un modelo o pide `onnxruntime`

No le pasaste `embedding_function=None` al crear la colección. Sin eso, Chroma
carga su función de embedding por defecto, que se trae `onnxruntime` y descarga
un modelo. En esta clase los vectores los calculamos nosotros con Gemini, así
que no hace falta ninguna de las dos cosas.

Revisa `rag/indice.py`: la colección se crea con `embedding_function=None` y con
`configuration={"hnsw": {"space": "cosine"}}`, porque el default de Chroma es
distancia L2 y toda la clase gira alrededor de la similitud coseno.

### `PyPDF2` en lugar de `pypdf`

`PyPDF2` está deprecado por su propio autor en favor de `pypdf`. Son paquetes
distintos con APIs distintas.

```bash
pip uninstall PyPDF2
pip install pypdf
```

### `page.extract_text()` devuelve `None` o cadena vacía

Es normal y no es un error: pasa en páginas que no tienen capa de texto, como
un escaneo. `rag/carga.py` ya lo maneja tratándolas como cero caracteres.

Si TODAS las páginas de un PDF salen vacías, ese PDF es una imagen y necesitas
OCR, que es un tema completamente distinto y no lo cubrimos aquí.

### La respuesta del modelo cambia entre corridas

Usamos `temperature=0`, pero eso no garantiza una salida idéntica byte a byte:
la infraestructura de inferencia introduce variación. Por eso las pruebas del
CP6 verifican **cadenas clave** (cifras, códigos, nombres) y nunca la respuesta
completa palabra por palabra.

---

## Notas técnicas

Las versiones y las firmas de este repositorio se verificaron contra la
documentación oficial el **12 de agosto de 2026**.

- **Embeddings**: `gemini-embedding-001` a 768 dimensiones. No usamos
  `gemini-embedding-2` porque devuelve un solo embedding agregado cuando le
  pasas una lista de textos, y porque no soporta `task_type`.
- **Normalización manual obligatoria**: con `gemini-embedding-001`, cualquier
  dimensión distinta de 3072 hay que normalizarla a mano. Si se olvida, la
  similitud coseno sale mal y el retrieval se degrada sin avisar.
- **Generación**: `openai/gpt-oss-120b` en Groq, `temperature=0`.
- **Vector store**: Chroma `EphemeralClient` (en memoria), espacio coseno,
  `embedding_function=None`.
