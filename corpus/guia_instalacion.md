# Guía de instalación del entorno

**Instituto Nébula** · Soporte Técnico
Aplica a NBL-204 — Sistemas de Recuperación Aumentada

## Antes de empezar

Verifica que tengas Python 3.10 o superior. Abre una terminal y ejecuta:

```
python3 --version
```

Si el comando no existe o la versión es menor, instala Python antes de continuar.
No sigas con los pasos siguientes hasta que ese comando responda correctamente.

## Paso 1: crear el entorno virtual

Desde la carpeta del proyecto:

```
python3 -m venv .venv
```

Esto crea una carpeta `.venv` con una instalación aislada de Python. Trabajar en
un entorno virtual evita que las bibliotecas del curso choquen con las que ya
tengas instaladas en el sistema.

## Paso 2: activar el entorno virtual

En Linux y macOS:

```
source .venv/bin/activate
```

En Windows con PowerShell:

```
.venv\Scripts\Activate.ps1
```

Sabrás que funcionó porque el nombre `.venv` aparece al inicio de la línea de tu
terminal. Este paso se repite cada vez que abres una terminal nueva.

## Paso 3: instalar las bibliotecas

```
pip install -r requirements.txt
```

La instalación tarda entre dos y cinco minutos según tu conexión. Hazla antes de
la sesión, nunca durante.

## Paso 4: configurar las claves de acceso

Copia el archivo de ejemplo y edítalo con tus propias claves:

```
cp .env.example .env
```

El archivo `.env` nunca se sube al repositorio. Ya está listado en `.gitignore`.

## Paso 5: verificar la instalación

```
python checkpoints/cp0_corpus.py
```

Si ves la lista de archivos del corpus con su formato y tamaño, el entorno quedó
listo. Si aparece un error, revisa la sección de problemas frecuentes del README
antes de escribir a Soporte Técnico.

## Problemas frecuentes

- **El comando `python3` no existe en Windows.** Usa `python` sin el 3.
- **`pip` instala en el Python del sistema.** No activaste el entorno virtual.
- **La activación falla en PowerShell.** Ejecuta primero
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- **La instalación se queda detenida.** Cancela con Ctrl+C y vuelve a intentar.

## Soporte

Escribe al canal de Soporte Técnico del campus. El horario de atención es de
lunes a viernes de 9:00 a 18:00.
