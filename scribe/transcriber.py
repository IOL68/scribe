"""
Módulo de transcripción usando whisper.cpp (binario nativo)
Más rápido que la versión Python, especialmente en Mac con Metal.
"""

import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# Directorio de modelos
MODELS_DIR = Path.home() / ".cache" / "whisper-cpp"

# URLs de modelos
MODEL_URLS = {
    "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
    "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    "large": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
}


def get_model_path(model: str) -> Path:
    """Obtiene la ruta al modelo, descargándolo si no existe."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_file = MODELS_DIR / f"ggml-{model}.bin"
    if model == "large":
        model_file = MODELS_DIR / "ggml-large-v3.bin"

    if not model_file.exists():
        print(f"Descargando modelo {model}...")
        url = MODEL_URLS.get(model)
        if not url:
            raise ValueError(f"Modelo '{model}' no soportado. Usa: {list(MODEL_URLS.keys())}")

        # Descargar con curl
        subprocess.run(
            ["curl", "-L", url, "-o", str(model_file)],
            check=True,
        )

    return model_file


def find_whisper_cli() -> str:
    """Encuentra el binario whisper-cli."""
    # Buscar en PATH
    whisper_path = shutil.which("whisper-cli")
    if whisper_path:
        return whisper_path

    # Buscar en ubicaciones comunes de Homebrew
    common_paths = [
        "/opt/homebrew/bin/whisper-cli",
        "/usr/local/bin/whisper-cli",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "whisper-cli no encontrado. Instálalo con: brew install whisper-cpp"
    )


def transcribe_audio(
    audio_path: str,
    model: str = "small",
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe un archivo de audio usando whisper.cpp.

    Args:
        audio_path: Ruta al archivo de audio
        model: Nombre del modelo Whisper (tiny, base, small, medium, large)
        language: Código de idioma (es, en, etc.) o None para auto-detectar

    Returns:
        Diccionario con la transcripción y metadatos
    """
    # Encontrar binario y modelo
    whisper_cli = find_whisper_cli()
    model_path = get_model_path(model)

    # Crear archivo temporal para output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_base = tmp.name.replace(".json", "")

    try:
        # Construir comando
        cmd = [
            whisper_cli,
            "-m", str(model_path),
            "-f", audio_path,
            "-ojf",  # Output JSON Full (incluye confianza por token)
            "-of", output_base,
            "--no-prints",
        ]

        if language:
            cmd.extend(["-l", language])

        # Ejecutar whisper-cli
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"whisper-cli falló: {result.stderr}")

        # Leer resultado JSON
        output_file = f"{output_base}.json"
        with open(output_file, "r") as f:
            whisper_result = json.load(f)

        # Convertir formato whisper.cpp a nuestro formato
        segments = []
        for seg in whisper_result.get("transcription", []):
            # Convertir offsets de ms a segundos
            start_ms = seg["offsets"]["from"]
            end_ms = seg["offsets"]["to"]

            # Calcular confianza promedio desde tokens
            tokens = seg.get("tokens", [])
            if tokens:
                # Filtrar tokens especiales y puntuación
                word_tokens = [
                    t for t in tokens
                    if t.get("p", 0) > 0
                    and not t.get("text", "").startswith("[_")
                    and t.get("text", "").strip() not in ".,!?;:'-\""
                ]

                if word_tokens:
                    probs = [t["p"] for t in word_tokens]
                    avg_confidence = sum(probs) / len(probs)
                    min_confidence = min(probs)
                    # Encontrar la palabra con menor confianza
                    lowest_token = min(word_tokens, key=lambda t: t["p"])
                    lowest_word = lowest_token["text"].strip()
                else:
                    avg_confidence = 0
                    min_confidence = 0
                    lowest_word = ""
            else:
                avg_confidence = 0
                min_confidence = 0
                lowest_word = ""

            segment_data = {
                "start": start_ms / 1000.0,
                "end": end_ms / 1000.0,
                "text": seg["text"].strip(),
                "confidence": round(avg_confidence, 4),
                "min_confidence": round(min_confidence, 4),
                "no_speech_prob": 0,
            }

            # Agregar palabra dudosa si la confianza es baja
            if lowest_word and min_confidence < 0.7:
                segment_data["suspect_word"] = lowest_word

            segments.append(segment_data)

        detected_lang = whisper_result.get("result", {}).get("language", language or "auto")

        return {
            "audio": audio_path,
            "language": detected_lang,
            "duration": segments[-1]["end"] if segments else 0,
            "segments": segments,
        }

    finally:
        # Limpiar archivo temporal
        output_file = f"{output_base}.json"
        if os.path.exists(output_file):
            os.remove(output_file)
