"""
Exportador a formato SRT (subtítulos)
"""

from pathlib import Path


def format_timestamp(seconds: float) -> str:
    """Convierte segundos a formato SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_srt(transcription: dict, output_path: Path) -> None:
    """
    Exporta la transcripción a formato SRT.

    Args:
        transcription: Datos de la transcripción
        output_path: Ruta del archivo de salida
    """
    lines = []

    for i, segment in enumerate(transcription["segments"], start=1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        speaker = segment.get("speaker", "")
        text = segment["text"]

        # Marcar si necesita revisión
        review_marker = " [?]" if segment.get("needs_review") else ""

        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(f"[{speaker}] {text}{review_marker}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
