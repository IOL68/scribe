#!/bin/bash
# Instalador de Scribe CLI
# Uso: curl -sSL https://raw.githubusercontent.com/ivanlandaverde/scribe/main/install.sh | bash

set -e

echo "==================================="
echo "   Instalando Scribe CLI"
echo "==================================="

# Verificar Homebrew
if ! command -v brew &> /dev/null; then
    echo "Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Instalar dependencias del sistema
echo "Instalando whisper-cpp y ffmpeg..."
brew install whisper-cpp ffmpeg

# Instalar scribe
echo "Instalando Scribe..."
pip3 install scribe-cli

echo ""
echo "==================================="
echo "   Instalacion completada!"
echo "==================================="
echo ""
echo "Uso:"
echo "  scribe audio.mp3 --format docx"
echo ""
