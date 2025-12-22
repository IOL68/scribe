"""
Módulo para separar voces de un audio usando Demucs.
Los archivos generados son temporales y se eliminan después del proceso.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

import torch
import torchaudio


def separate_voices(
    audio_path: str,
    num_speakers: int = 2,
    output_dir: Optional[str] = None,
) -> List[str]:
    """
    Separa las voces de un archivo de audio.

    Args:
        audio_path: Ruta al archivo de audio
        num_speakers: Número de speakers a separar
        output_dir: Directorio temporal (se crea uno si no se especifica)

    Returns:
        Lista de rutas a los archivos de audio separados
    """
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    # Crear directorio temporal si no se especifica
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="scribe_separation_")

    # Cargar modelo de separación
    # htdemucs es el mejor para separar voces
    model = get_model("htdemucs")
    model.eval()

    # Usar GPU si está disponible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # Cargar audio
    waveform, sample_rate = torchaudio.load(audio_path)

    # Resamplear a la frecuencia del modelo si es necesario
    if sample_rate != model.samplerate:
        resampler = torchaudio.transforms.Resample(sample_rate, model.samplerate)
        waveform = resampler(waveform)
        sample_rate = model.samplerate

    # Convertir a mono si es necesario y luego a estéreo para el modelo
    if waveform.shape[0] == 1:
        waveform = waveform.repeat(2, 1)
    elif waveform.shape[0] > 2:
        waveform = waveform[:2, :]

    # Agregar dimensión de batch
    waveform = waveform.unsqueeze(0).to(device)

    # Aplicar modelo de separación
    with torch.no_grad():
        sources = apply_model(model, waveform, device=device)

    # sources tiene forma [batch, num_sources, channels, time]
    # Los sources de htdemucs son: drums, bass, other, vocals
    # Nos interesa "vocals" (índice 3)
    vocals_idx = model.sources.index("vocals") if "vocals" in model.sources else -1

    if vocals_idx == -1:
        # Si no hay track de vocals, usar el audio original
        separated_paths = [audio_path]
    else:
        # Extraer vocals
        vocals = sources[0, vocals_idx].cpu()

        # Guardar archivo temporal
        vocals_path = os.path.join(output_dir, "vocals.wav")
        torchaudio.save(vocals_path, vocals, sample_rate)
        separated_paths = [vocals_path]

    return separated_paths


def separate_by_diarization(
    audio_path: str,
    diarization_segments: List[dict],
    num_speakers: int = 2,
    output_dir: Optional[str] = None,
) -> List[str]:
    """
    Separa el audio basándose en los segmentos de diarización.
    Crea un archivo por cada speaker con solo sus partes.

    Args:
        audio_path: Ruta al archivo de audio
        diarization_segments: Segmentos con información de speaker y timestamps
        num_speakers: Número de speakers
        output_dir: Directorio temporal

    Returns:
        Lista de rutas: [speaker_1.wav, speaker_2.wav, ...]
    """
    from pydub import AudioSegment

    # Crear directorio temporal si no se especifica
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="scribe_separation_")

    # Cargar audio
    audio = AudioSegment.from_file(audio_path)

    # Crear un audio vacío para cada speaker
    speaker_audios = {}
    for i in range(1, num_speakers + 1):
        speaker_key = f"Speaker {i}"
        speaker_audios[speaker_key] = AudioSegment.silent(duration=len(audio))

    # Superponer cada segmento en el audio del speaker correspondiente
    for segment in diarization_segments:
        speaker = segment.get("speaker", "Unknown")
        if speaker == "Unknown" or speaker not in speaker_audios:
            continue

        start_ms = int(segment["start"] * 1000)
        end_ms = int(segment["end"] * 1000)

        # Extraer el segmento del audio original
        segment_audio = audio[start_ms:end_ms]

        # Colocar en la posición correcta del audio del speaker
        speaker_audios[speaker] = (
            speaker_audios[speaker][:start_ms] +
            segment_audio +
            speaker_audios[speaker][end_ms:]
        )

    # Guardar archivos
    separated_paths = []
    for speaker, speaker_audio in speaker_audios.items():
        speaker_num = speaker.split()[-1]
        output_path = os.path.join(output_dir, f"speaker_{speaker_num}.wav")
        speaker_audio.export(output_path, format="wav")
        separated_paths.append(output_path)

    return separated_paths


def cleanup_temp_files(paths: List[str]) -> None:
    """
    Elimina archivos temporales y sus directorios padre si están vacíos.

    Args:
        paths: Lista de rutas a eliminar
    """
    dirs_to_check = set()

    for path in paths:
        if os.path.exists(path):
            dirs_to_check.add(os.path.dirname(path))
            os.remove(path)

    # Eliminar directorios vacíos
    for dir_path in dirs_to_check:
        if dir_path and os.path.exists(dir_path) and not os.listdir(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
