#!/bin/bash
# Instalador de Scribe CLI
# Uso: curl -sSL https://raw.githubusercontent.com/IOL68/scribe/main/install.sh | bash

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
echo "Instalando dependencias..."
brew install whisper-cpp ffmpeg python@3.11

# Instalar scribe con Python 3.11
echo "Instalando Scribe..."
/opt/homebrew/bin/python3.11 -m pip install git+https://github.com/IOL68/scribe.git

echo ""
echo "==================================="
echo "   Instalacion completada!"
echo "==================================="
echo ""
echo "Uso:"
echo "  scribe audio.mp3 --format docx"
echo ""
