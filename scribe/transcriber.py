"""
Módulo de transcripción usando Whisper
"""

import whisper
from typing import Optional


def transcribe_audio(
    audio_path: str,
    model: str = "small",
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe un archivo de audio usando Whisper.

    Args:
        audio_path: Ruta al archivo de audio
        model: Nombre del modelo Whisper (tiny, base, small, medium, large)
        language: Código de idioma (es, en, etc.) o None para auto-detectar

    Returns:
        Diccionario con la transcripción y metadatos
    """
    # Cargar modelo
    whisper_model = whisper.load_model(model)

    # Transcribir
    options = {}
    if language:
        options["language"] = language

    result = whisper_model.transcribe(audio_path, **options)

    # Estructurar resultado
    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "confidence": seg.get("avg_logprob", 0),
            "no_speech_prob": seg.get("no_speech_prob", 0),
        })

    return {
        "audio": audio_path,
        "language": result.get("language", language),
        "duration": segments[-1]["end"] if segments else 0,
        "segments": segments,
    }
