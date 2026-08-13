#!/usr/bin/env bash
# Renderiza los seis videos y los copia a la carpeta de Descargas.
#
#   bash videos/renderizar.sh
#
# Requiere Manim Community. Si no lo tienes, la vía sin sudo es conda-forge:
#
#   curl -sSL https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
#   export MAMBA_ROOT_PREFIX=$HOME/.micromamba
#   ./bin/micromamba create -y -n manim -c conda-forge python=3.12 manim
#
# La alternativa con apt necesita contraseña:
#   sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config && pip install manim

set -euo pipefail

DESTINO="${1:-/mnt/c/Users/ramse/Downloads/Explicacion RAG}"
MANIM="${MANIM:-$HOME/.micromamba/envs/manim/bin/manim}"
CALIDAD="${CALIDAD:--qh}"   # -ql borrador · -qm 720p30 · -qh 1080p60

ESCENAS=(Chunking Indexacion BaseVectorial Recuperacion Generacion Evaluacion)

# Manim guarda cada calidad en su propia carpeta. Hay que copiar de la que
# corresponde: si buscas el .mp4 por nombre a secas y ya renderaste en borrador
# alguna vez, te llevas el borrador sin enterarte.
case "$CALIDAD" in
    -ql) RESOLUCION="480p15"   ;;
    -qm) RESOLUCION="720p30"   ;;
    -qh) RESOLUCION="1080p60"  ;;
    -qk) RESOLUCION="2160p60"  ;;
    *)   echo "Calidad desconocida: $CALIDAD"; exit 1 ;;
esac

if [ ! -x "$MANIM" ]; then
    echo "No encuentro manim en: $MANIM"
    echo "Ajusta la variable MANIM o instálalo (ver arriba)."
    exit 1
fi

mkdir -p "$DESTINO/videos"

for i in "${!ESCENAS[@]}"; do
    escena="${ESCENAS[$i]}"
    echo "==> [$((i + 1))/6] $escena"
    "$MANIM" "$CALIDAD" --media_dir videos/media \
        videos/explicacion_rag.py "$escena"
done

echo
echo "==> Copiando a: $DESTINO/videos"
ORIGEN="videos/media/videos/explicacion_rag/$RESOLUCION"
n=1
for escena in "${ESCENAS[@]}"; do
    archivo="$ORIGEN/${escena}.mp4"
    if [ ! -f "$archivo" ]; then
        echo "No existe $archivo"; exit 1
    fi
    cp "$archivo" "$DESTINO/videos/${n}_${escena}.mp4"
    n=$((n + 1))
done

cp videos/explicacion_rag.py "$DESTINO/videos/"
ls -la "$DESTINO/videos/"
