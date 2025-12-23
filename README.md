# Scribe

CLI y UI para transcripción de audio con detección de speakers y timestamps.

100% local - tus audios nunca salen de tu computadora.

## Instalación (macOS)

```bash
bash -c "$(curl -sSL https://raw.githubusercontent.com/IOL68/scribe/main/install.sh)"
```

Esto instala automáticamente:
- whisper-cpp (transcripción)
- ffmpeg (procesamiento de audio)
- Python 3.11
- pipx y scribe

## Uso

### Interfaz gráfica (recomendado)

```bash
scribe-ui
```

Abre una ventana en tu navegador donde puedes:
- Arrastrar y soltar archivos de audio
- Seleccionar idioma, speakers y formato
- Descargar el archivo transcrito

### Línea de comandos

```bash
# Básico
scribe entrevista.mp3

# Con formato DOCX (estilo profesional LAI)
scribe entrevista.mp3 --format docx

# Especificar speakers e idioma
scribe entrevista.mp3 --speakers 2 --lang es --format docx
```

## Actualizar

```bash
scribe --update
```

## Opciones CLI

| Flag | Descripción | Default |
|------|-------------|---------|
| `--speakers`, `-s` | Número de speakers ('auto' o número) | auto |
| `--lang`, `-l` | Idioma (es, en, auto) | auto |
| `--model`, `-m` | Modelo Whisper (tiny, base, small, medium, large) | small |
| `--format`, `-f` | Formatos de salida (json,srt,txt,docx) | json |
| `--output`, `-o` | Nombre archivo de salida | mismo nombre del audio |
| `--update` | Actualizar a la última versión | - |
| `--version` | Ver versión instalada | - |

## Formatos de salida

- **DOCX** - Documento Word con formato profesional LAI
- **JSON** - Completo con metadata, ideal para programadores
- **SRT** - Subtítulos, compatible con reproductores de video
- **TXT** - Texto simple legible

## Instalación Linux (Ubuntu/Debian)

```bash
# 1. Dependencias
sudo apt update
sudo apt install -y ffmpeg build-essential cmake git python3-venv pipx

# 2. Compilar whisper.cpp
cd /tmp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp && make
sudo cp build/bin/whisper-cli /usr/local/bin/

# 3. Instalar Scribe
pipx ensurepath
pipx install git+https://github.com/IOL68/scribe.git
```

## Requisitos

- macOS (Apple Silicon o Intel) o Linux
- Python 3.11+
- Homebrew (macOS) o apt (Linux)

## Modelos

La primera vez que ejecutes scribe, descargará automáticamente:
- Modelo Whisper (~465MB para "small")
- Modelos de diarización (~80MB)

Después todo es 100% local.

## Licencia

MIT
