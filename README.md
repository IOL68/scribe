# Scribe

CLI para transcripción de audio con detección de speakers y timestamps.

100% local - tus audios nunca salen de tu computadora.

## Instalación

```bash
curl -sSL https://raw.githubusercontent.com/ivanlandaverde/scribe/main/install.sh | bash
```

## Uso

```bash
# Básico
scribe entrevista.mp3

# Con formato DOCX (estilo profesional LAI)
scribe entrevista.mp3 --format docx

# Especificar speakers e idioma
scribe entrevista.mp3 --speakers 2 --lang es --format docx

# Múltiples formatos
scribe entrevista.mp3 --format json,srt,txt,docx
```

## Opciones

| Flag | Descripción | Default |
|------|-------------|---------|
| `--speakers`, `-s` | Número de speakers ('auto' o número) | auto |
| `--lang`, `-l` | Idioma (es, en, auto) | auto |
| `--model`, `-m` | Modelo Whisper (tiny, base, small, medium, large) | small |
| `--format`, `-f` | Formatos de salida (json,srt,txt,docx) | json |
| `--output`, `-o` | Nombre archivo de salida | mismo nombre del audio |

## Formatos de salida

- **JSON** - Completo con metadata, ideal para programadores
- **SRT** - Subtítulos, compatible con reproductores de video
- **TXT** - Texto simple legible
- **DOCX** - Documento Word con formato profesional LAI

## Modelos

| Modelo | Tamaño | Velocidad | Precisión |
|--------|--------|-----------|-----------|
| tiny | 39 MB | Muy rápido | Baja |
| base | 140 MB | Rápido | Media |
| small | 460 MB | Normal | Buena |
| medium | 1.5 GB | Lento | Alta |
| large | 3 GB | Muy lento | Máxima |

## Licencia

MIT
