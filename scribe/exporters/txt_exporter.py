"""
Exportador a formato TXT simple
"""

from pathlib import Path


def format_time(seconds: float) -> str:
    """Convierte segundos a formato MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def export_txt(transcription: dict, output_path: Path) -> None:
    """
    Exporta la transcripción a formato TXT legible.

    Args:
        transcription: Datos de la transcripción
        output_path: Ruta del archivo de salida
    """
    lines = []

    # Header
    lines.append(f"Transcripción: {transcription.get('audio', 'audio')}")
    lines.append(f"Idioma: {transcription.get('language', 'desconocido')}")
    lines.append(f"Speakers: {transcription.get('speakers', 'desconocido')}")
    lines.append(f"Duración: {format_time(transcription.get('duration', 0))}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    current_speaker = None

    for segment in transcription["segments"]:
        speaker = segment.get("speaker", "Unknown")
        timestamp = format_time(segment["start"])
        text = segment["text"]
        review_marker = " [?]" if segment.get("needs_review") else ""

        # Agrupar por speaker para mejor legibilidad
        if speaker != current_speaker:
            if current_speaker is not None:
                lines.append("")
            lines.append(f"[{timestamp}] {speaker}:")
            current_speaker = speaker

        lines.append(f"  {text}{review_marker}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
