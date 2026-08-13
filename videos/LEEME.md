# Explicación RAG — corpus y videos

## `corpus/`

Los 14 documentos del Instituto Nébula, la academia ficticia que usamos en la
clase. Es ficticia a propósito: ningún modelo puede saber sus datos de memoria,
así que todo lo que el sistema responda bien tuvo que haberlo leído de aquí.

El corpus es deliberadamente sucio y heterogéneo:

- **6 archivos `.md`** — la documentación oficial, limpia y estructurada.
- **5 archivos `.txt`** — un export de chat de soporte, notas de junta con
  abreviaturas, un correo reenviado cuatro veces, un changelog y un archivo con
  la codificación rota a media página (busca los `Ã³`).
- **3 archivos `.pdf`** — uno se extrae perfecto, uno tiene dos columnas que
  salen entreveradas renglón por renglón, y uno tiene una tabla que al extraerla
  se destruye: los conceptos quedan en un bloque y los montos en otro.

Hay además una contradicción a propósito: `politica_reembolsos.md` dice que el
reembolso es a 7 días naturales, y `notas_junta_2026_07_02.txt` dice que se
cambió a 5 días hábiles.

## `videos/`

Seis videos de ~25-30 segundos, uno por etapa del pipeline, con subtítulos.

| # | Video | Qué muestra |
|---|---|---|
| 1 | `1_Chunking.mp4` | Cómo se parten los documentos en chunks y para qué sirve el traslape |
| 2 | `2_Indexacion.mp4` | Cómo el texto se convierte en vectores y por qué los significados parecidos quedan cerca |
| 3 | `3_BaseVectorial.mp4` | Qué se guarda en la base de datos vectorial además del vector |
| 4 | `4_Recuperacion.mp4` | Cómo la pregunta cae en el mismo espacio y se buscan los 4 chunks más cercanos |
| 5 | `5_Generacion.mp4` | Cómo se arma el prompt y qué responde el modelo |
| 6 | `6_Evaluacion.mp4` | Golden tests, y por qué una de las pruebas pasa cuando el sistema NO responde |

El orden importa: cada video asume el anterior.

### Regenerarlos

El código está en `explicacion_rag.py`, hecho con
[Manim Community](https://docs.manim.community/en/stable/).

```bash
manim -qh explicacion_rag.py Chunking
```

Escenas disponibles: `Chunking`, `Indexacion`, `BaseVectorial`, `Recuperacion`,
`Generacion`, `Evaluacion`.

Calidad: `-ql` borrador rápido · `-qm` 720p30 · `-qh` 1080p60.

Si no tienes Manim instalado y no quieres pelearte con las dependencias del
sistema, la vía sin permisos de administrador es conda-forge:

```bash
curl -sSL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
export MAMBA_ROOT_PREFIX=$HOME/.micromamba
./bin/micromamba create -y -n manim -c conda-forge python=3.12 manim
```
