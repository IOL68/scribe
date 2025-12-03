"""
Módulo de diarización (detección de speakers)
"""

from typing import Optional
from simple_diarizer.diarizer import Diarizer


def diarize_audio(
    audio_path: str,
    transcription: dict,
    num_speakers: Optional[int] = None,
) -> dict:
    """
    Detecta quién habla en cada segmento del audio.

    Args:
        audio_path: Ruta al archivo de audio
        transcription: Resultado de la transcripción
        num_speakers: Número de speakers (None para auto-detectar)

    Returns:
        Transcripción actualizada con información de speakers
    """
    # Inicializar diarizer
    diar = Diarizer(embed_model="ecapa")

    # Ejecutar diarización
    diar_segments = diar.diarize(
        audio_path,
        num_speakers=num_speakers,
    )

    # Mapear speakers a segmentos de transcripción
    for trans_seg in transcription["segments"]:
        seg_start = trans_seg["start"]
        seg_end = trans_seg["end"]
        seg_mid = (seg_start + seg_end) / 2

        # Encontrar el speaker que habla en el punto medio del segmento
        speaker = "Unknown"
        for diar_seg in diar_segments:
            if diar_seg["start"] <= seg_mid <= diar_seg["end"]:
                speaker = f"Speaker {diar_seg['label'] + 1}"
                break

        trans_seg["speaker"] = speaker

    # Contar speakers únicos
    unique_speakers = set(seg.get("speaker", "Unknown") for seg in transcription["segments"])
    transcription["speakers"] = len(unique_speakers)

    return transcription
