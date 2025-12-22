# Scribe

CLI y UI para transcripción de audio con detección de speakers y timestamps.

100% local - tus audios nunca salen de tu computadora.

## Instalación (macOS)

```bash
curl -sSL https://raw.githubusercontent.com/IOL68/scribe/main/install.sh | bash
```

O manualmente:

```bash
brew install whisper-cpp ffmpeg python@3.11
python3.11 -m pip install git+https://github.com/IOL68/scribe.git
```

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

## Opciones CLI

| Flag | Descripción | Default |
|------|-------------|---------|
| `--speakers`, `-s` | Número de speakers ('auto' o número) | auto |
| `--lang`, `-l` | Idioma (es, en, auto) | auto |
| `--model`, `-m` | Modelo Whisper (tiny, base, small, medium, large) | small |
| `--format`, `-f` | Formatos de salida (json,srt,txt,docx) | json |
| `--output`, `-o` | Nombre archivo de salida | mismo nombre del audio |

## Formatos de salida

- **DOCX** - Documento Word con formato profesional LAI
- **JSON** - Completo con metadata, ideal para programadores
- **SRT** - Subtítulos, compatible con reproductores de video
- **TXT** - Texto simple legible

## Requisitos

- macOS (Apple Silicon o Intel)
- Python 3.11
- Homebrew

## Licencia

MIT
