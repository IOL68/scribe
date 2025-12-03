# Scribe

CLI para transcripción de audio con detección de speakers y timestamps.

100% local - tus audios nunca salen de tu computadora.

## Instalación

```bash
pip install scribe-cli
```

## Uso

```bash
# Básico
scribe entrevista.mp3

# Con opciones
scribe entrevista.mp3 --speakers 2 --lang es --format json,srt,txt

# Ver modelos disponibles
scribe list-models

# Descargar modelo específico
scribe download small
```

## Opciones

| Flag | Descripción | Default |
|------|-------------|---------|
| `--speakers`, `-s` | Número de speakers ('auto' o número) | auto |
| `--lang`, `-l` | Idioma (es, en, auto) | auto |
| `--model`, `-m` | Modelo Whisper (tiny, base, small, medium, large) | small |
| `--format`, `-f` | Formatos de salida (json,srt,txt,docx) | json |
| `--output`, `-o` | Nombre archivo de salida | mismo nombre del audio |
| `--proofread`, `-p` | Marcar segmentos con baja confianza | false |

## Formatos de salida

- **JSON** - Completo con metadata, ideal para programadores
- **SRT** - Subtítulos, compatible con reproductores de video
- **TXT** - Texto simple legible
- **DOCX** - Documento Word editable para correcciones

## Modelos

| Modelo | Tamaño | Velocidad | Precisión |
|--------|--------|-----------|-----------|
| tiny | 39 MB | Muy rápido | Baja |
| base | 140 MB | Rápido | Media |
| small | 460 MB | Normal | Buena |
| medium | 1.5 GB | Lento | Alta |
| large | 3 GB | Muy lento | Máxima |

## Ejemplo de salida

```json
{
  "audio": "entrevista.mp3",
  "duration": 3600,
  "language": "es",
  "speakers": 2,
  "segments": [
    {
      "start": 0.0,
      "end": 4.5,
      "speaker": "Speaker 1",
      "text": "Bienvenidos, hoy tenemos un invitado especial.",
      "confidence_score": 0.97
    }
  ]
}
```

## Licencia

MIT
