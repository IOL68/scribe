"""
Exportador a formato DOCX (Word)
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


def format_time(seconds: float) -> str:
    """Convierte segundos a formato MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def export_docx(transcription: dict, output_path: Path) -> None:
    """
    Exporta la transcripción a formato DOCX editable.

    Args:
        transcription: Datos de la transcripción
        output_path: Ruta del archivo de salida
    """
    doc = Document()

    # Título
    title = doc.add_heading("Transcripción", level=0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Metadata
    meta = doc.add_paragraph()
    meta.add_run(f"Archivo: ").bold = True
    meta.add_run(f"{transcription.get('audio', 'audio')}\n")
    meta.add_run(f"Idioma: ").bold = True
    meta.add_run(f"{transcription.get('language', 'desconocido')}\n")
    meta.add_run(f"Speakers: ").bold = True
    meta.add_run(f"{transcription.get('speakers', 'desconocido')}\n")
    meta.add_run(f"Duración: ").bold = True
    meta.add_run(f"{format_time(transcription.get('duration', 0))}")

    doc.add_paragraph()  # Espacio

    # Transcripción
    current_speaker = None

    for segment in transcription["segments"]:
        speaker = segment.get("speaker", "Unknown")
        timestamp = format_time(segment["start"])
        text = segment["text"]
        needs_review = segment.get("needs_review", False)

        # Nuevo speaker = nuevo párrafo con encabezado
        if speaker != current_speaker:
            doc.add_paragraph()  # Espacio entre speakers

            speaker_para = doc.add_paragraph()
            speaker_run = speaker_para.add_run(f"[{timestamp}] {speaker}")
            speaker_run.bold = True
            speaker_run.font.size = Pt(11)
            speaker_run.font.color.rgb = RGBColor(0, 102, 204)  # Azul

            current_speaker = speaker

        # Texto del segmento
        text_para = doc.add_paragraph()
        text_run = text_para.add_run(text)
        text_run.font.size = Pt(11)

        # Marcar si necesita revisión (amarillo)
        if needs_review:
            text_run.font.highlight_color = 7  # Amarillo
            review_run = text_para.add_run(" [REVISAR]")
            review_run.font.size = Pt(9)
            review_run.font.color.rgb = RGBColor(255, 0, 0)

    # Guardar
    doc.save(output_path)
