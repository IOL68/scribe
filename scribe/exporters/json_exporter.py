"""
Exportador a formato JSON
"""

import json
from pathlib import Path


def export_json(transcription: dict, output_path: Path) -> None:
    """
    Exporta la transcripción a formato JSON.

    Args:
        transcription: Datos de la transcripción
        output_path: Ruta del archivo de salida
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcription, f, ensure_ascii=False, indent=2)
