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

    # Agregar Homebrew al PATH para esta sesión
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Instalar dependencias del sistema
echo "Instalando dependencias..."
brew install whisper-cpp ffmpeg python@3.11

# Instalar pipx si no existe
if ! command -v pipx &> /dev/null; then
    /opt/homebrew/bin/python3.11 -m pip install --user pipx
fi

# Instalar scribe con pipx usando Python 3.11
echo "Instalando Scribe..."
~/.local/bin/pipx install git+https://github.com/IOL68/scribe.git --python /opt/homebrew/bin/python3.11 --force

# Crear symlinks en /opt/homebrew/bin para acceso directo
ln -sf ~/.local/bin/scribe /opt/homebrew/bin/scribe 2>/dev/null || true
ln -sf ~/.local/bin/scribe-ui /opt/homebrew/bin/scribe-ui 2>/dev/null || true

echo ""
echo "==================================="
echo "   Instalacion completada!"
echo "==================================="
echo ""
echo "Uso:"
echo "  scribe audio.mp3 --format docx"
echo ""
