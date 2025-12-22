"""
Módulo de diarización (detección de speakers)
100% local - carga modelos directamente sin internet.
"""

import os
import warnings
from pathlib import Path
from typing import Optional, List

import torch
import numpy as np

# Suprimir warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Ruta base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "pretrained_models"
ECAPA_MODEL_DIR = MODELS_DIR / "spkrec-ecapa-voxceleb"

# Cache del modelo para no recargarlo cada vez
_cached_embed_model = None
_cached_vad_model = None


def _check_model_exists() -> bool:
    """Verifica si el modelo ECAPA ya está descargado localmente."""
    required_files = [
        "embedding_model.ckpt",
        "hyperparams.yaml",
        "mean_var_norm_emb.ckpt",
    ]
    return all((ECAPA_MODEL_DIR / f).exists() for f in required_files)


def _download_models():
    """Descarga los modelos de diarización automáticamente."""
    from rich.console import Console
    console = Console()

    console.print("[yellow]Descargando modelos de diarización (primera vez)...[/yellow]")

    # Crear directorio
    ECAPA_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Descargar desde HuggingFace
    base_url = "https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb/resolve/main"
    files = [
        "embedding_model.ckpt",
        "hyperparams.yaml",
        "mean_var_norm_emb.ckpt",
    ]

    import urllib.request
    for filename in files:
        url = f"{base_url}/{filename}"
        dest = ECAPA_MODEL_DIR / filename
        if not dest.exists():
            console.print(f"  Descargando {filename}...")
            urllib.request.urlretrieve(url, dest)

    console.print("[green]Modelos descargados correctamente.[/green]")


def _load_embedding_model_local():
    """
    Carga el modelo ECAPA-TDNN directamente desde archivos locales.
    Sin usar from_hparams, sin internet.
    """
    global _cached_embed_model

    if _cached_embed_model is not None:
        return _cached_embed_model

    if not _check_model_exists():
        _download_models()

    from speechbrain.lobes.features import Fbank
    from speechbrain.processing.features import InputNormalization
    from speechbrain.lobes.models.ECAPA_TDNN import ECAPA_TDNN

    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # Crear modelo con la misma arquitectura del hyperparams.yaml
    compute_features = Fbank(n_mels=80)

    mean_var_norm = InputNormalization(norm_type="sentence", std_norm=False)

    embedding_model = ECAPA_TDNN(
        input_size=80,
        channels=[1024, 1024, 1024, 1024, 3072],
        kernel_sizes=[5, 3, 3, 3, 1],
        dilations=[1, 2, 3, 4, 1],
        attention_channels=128,
        lin_neurons=192,
    )

    mean_var_norm_emb = InputNormalization(norm_type="global", std_norm=False)

    # Cargar pesos del modelo de embeddings
    embedding_model.load_state_dict(
        torch.load(ECAPA_MODEL_DIR / "embedding_model.ckpt", map_location=device)
    )

    # Cargar estadísticas de normalización (formato especial de SpeechBrain)
    norm_ckpt = torch.load(ECAPA_MODEL_DIR / "mean_var_norm_emb.ckpt", map_location=device)
    mean_var_norm_emb.count = norm_ckpt.get("count", 0)
    mean_var_norm_emb.glob_mean = norm_ckpt.get("glob_mean", torch.zeros(192))
    mean_var_norm_emb.glob_std = norm_ckpt.get("glob_std", torch.ones(192))
    mean_var_norm_emb.spk_dict_mean = norm_ckpt.get("spk_dict_mean", {})
    mean_var_norm_emb.spk_dict_std = norm_ckpt.get("spk_dict_std", {})
    mean_var_norm_emb.spk_dict_count = norm_ckpt.get("spk_dict_count", {})

    # Mover a device y poner en modo eval
    embedding_model = embedding_model.to(device).eval()
    mean_var_norm_emb = mean_var_norm_emb.to(device).eval()
    compute_features = compute_features.to(device)
    mean_var_norm = mean_var_norm.to(device)

    _cached_embed_model = {
        "compute_features": compute_features,
        "mean_var_norm": mean_var_norm,
        "embedding_model": embedding_model,
        "mean_var_norm_emb": mean_var_norm_emb,
        "device": device,
    }

    return _cached_embed_model


def _encode_batch(model_dict: dict, wavs: torch.Tensor) -> torch.Tensor:
    """
    Extrae embeddings de un batch de audio.

    Args:
        model_dict: Diccionario con los componentes del modelo
        wavs: Tensor de audio [batch, time] o [1, time]

    Returns:
        Embeddings [batch, 192]
    """
    device = model_dict["device"]
    wavs = wavs.to(device)

    # Asegurar forma correcta
    if wavs.dim() == 1:
        wavs = wavs.unsqueeze(0)

    with torch.no_grad():
        # Extraer features
        feats = model_dict["compute_features"](wavs)
        feats = model_dict["mean_var_norm"](feats, torch.ones(feats.shape[0], device=device))

        # Obtener embeddings
        embeddings = model_dict["embedding_model"](feats)
        embeddings = model_dict["mean_var_norm_emb"](
            embeddings, torch.ones(embeddings.shape[0], device=device)
        )

    return embeddings


def _load_vad_model():
    """Carga el modelo VAD (Voice Activity Detection) de Silero desde cache local."""
    global _cached_vad_model

    if _cached_vad_model is not None:
        return _cached_vad_model

    # Cargar desde cache local (sin internet)
    cache_dir = Path.home() / ".cache" / "torch" / "hub" / "snakers4_silero-vad_master"

    if cache_dir.exists():
        # Cargar desde directorio local
        model, utils = torch.hub.load(
            repo_or_dir=str(cache_dir),
            model="silero_vad",
            source="local",
            trust_repo=True,
        )
    else:
        # Fallback: descargar si no existe
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )

    get_speech_ts = utils[0]
    _cached_vad_model = (model, get_speech_ts)
    return _cached_vad_model


def _load_audio(audio_path: str, target_sr: int = 16000) -> tuple:
    """
    Carga audio usando pydub (soporta mp3, wav, etc).
    Retorna waveform como tensor y sample_rate.
    """
    from pydub import AudioSegment
    import io

    # Cargar con pydub (soporta muchos formatos)
    audio = AudioSegment.from_file(audio_path)

    # Convertir a mono
    if audio.channels > 1:
        audio = audio.set_channels(1)

    # Resamplear a target_sr
    if audio.frame_rate != target_sr:
        audio = audio.set_frame_rate(target_sr)

    # Convertir a numpy array normalizado
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples = samples / (2 ** 15)  # Normalizar a [-1, 1]

    # Convertir a tensor [1, time]
    waveform = torch.from_numpy(samples).unsqueeze(0)

    return waveform, target_sr


def _get_speech_segments(audio_path: str, vad_model, get_speech_ts) -> tuple:
    """Detecta segmentos de voz en el audio."""
    waveform, sample_rate = _load_audio(audio_path, target_sr=16000)

    # Detectar segmentos de voz
    speech_timestamps = get_speech_ts(waveform.squeeze(), vad_model)

    segments = []
    for ts in speech_timestamps:
        segments.append({
            "start": ts["start"] / sample_rate,
            "end": ts["end"] / sample_rate,
        })

    return segments, waveform, sample_rate


def _extract_embeddings(
    waveform: torch.Tensor,
    sample_rate: int,
    model_dict: dict,
    window: float = 1.5,
    period: float = 0.75,
) -> tuple:
    """
    Extrae embeddings de voz en ventanas deslizantes.
    """
    len_window = int(window * sample_rate)
    len_period = int(period * sample_rate)
    len_signal = waveform.shape[1]

    segments = []
    start = 0
    while start + len_window < len_signal:
        segments.append([start, start + len_window])
        start += len_period

    if start < len_signal:
        segments.append([start, len_signal])

    embeddings = []
    for i, j in segments:
        signal_seg = waveform[:, i:j]
        if signal_seg.shape[1] < 1600:  # Muy corto
            continue
        seg_embed = _encode_batch(model_dict, signal_seg.squeeze(0))
        embeddings.append(seg_embed.squeeze(0).cpu().numpy())

    # Convertir a tiempos
    segment_times = [
        {"start": s[0] / sample_rate, "end": s[1] / sample_rate}
        for s in segments[:len(embeddings)]
    ]

    # Asegurar que sea 2D: [num_segments, embedding_dim]
    embeddings_array = np.array(embeddings)
    if embeddings_array.ndim == 3:
        embeddings_array = embeddings_array.squeeze(1)

    return embeddings_array, segment_times


def _cluster_embeddings(
    embeddings: np.ndarray,
    num_speakers: Optional[int] = None,
    threshold: float = 0.25,
) -> np.ndarray:
    """
    Agrupa embeddings por speaker usando clustering jerárquico.
    """
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import pdist

    if len(embeddings) < 2:
        return np.zeros(len(embeddings), dtype=int)

    # Calcular distancias coseno
    distances = pdist(embeddings, metric="cosine")

    # Clustering jerárquico
    linkage_matrix = linkage(distances, method="average")

    if num_speakers is not None:
        labels = fcluster(linkage_matrix, num_speakers, criterion="maxclust")
    else:
        labels = fcluster(linkage_matrix, threshold, criterion="distance")

    return labels - 1  # Empezar desde 0


def diarize_audio(
    audio_path: str,
    transcription: dict,
    num_speakers: Optional[int] = None,
    threshold: float = 0.25,
) -> dict:
    """
    Detecta quién habla en cada segmento del audio.
    100% local, sin conexión a internet.

    Args:
        audio_path: Ruta al archivo de audio
        transcription: Resultado de la transcripción
        num_speakers: Número de speakers (None para auto-detectar)
        threshold: Umbral de similitud para clustering

    Returns:
        Transcripción actualizada con información de speakers
    """
    # Cargar modelos (desde cache o disco local)
    model_dict = _load_embedding_model_local()
    vad_model, get_speech_ts = _load_vad_model()

    # Obtener segmentos de voz y audio
    speech_segments, waveform, sample_rate = _get_speech_segments(
        audio_path, vad_model, get_speech_ts
    )

    # Extraer embeddings
    embeddings, segment_times = _extract_embeddings(
        waveform, sample_rate, model_dict
    )

    if len(embeddings) == 0:
        for seg in transcription["segments"]:
            seg["speaker"] = "Speaker 1"
        transcription["speakers"] = 1
        return transcription

    # Clustering de embeddings
    labels = _cluster_embeddings(embeddings, num_speakers, threshold)

    # Crear segmentos de diarización
    diar_segments = []
    for i, (seg_time, label) in enumerate(zip(segment_times, labels)):
        diar_segments.append({
            "start": seg_time["start"],
            "end": seg_time["end"],
            "label": int(label),
        })

    # Mapear speakers a segmentos de transcripción
    for trans_seg in transcription["segments"]:
        seg_start = trans_seg["start"]
        seg_end = trans_seg["end"]
        seg_mid = (seg_start + seg_end) / 2

        speaker = None
        for diar_seg in diar_segments:
            if diar_seg["start"] <= seg_mid <= diar_seg["end"]:
                speaker = f"Speaker {diar_seg['label'] + 1}"
                break

        if speaker is None and diar_segments:
            closest = min(
                diar_segments,
                key=lambda d: min(abs(d["start"] - seg_mid), abs(d["end"] - seg_mid))
            )
            speaker = f"Speaker {closest['label'] + 1}"

        trans_seg["speaker"] = speaker if speaker else "Unknown"

    # Post-procesamiento
    _smooth_speaker_changes(transcription["segments"])

    # Contar speakers únicos
    unique_speakers = set(
        seg.get("speaker") for seg in transcription["segments"]
        if seg.get("speaker") and seg.get("speaker") != "Unknown"
    )
    transcription["speakers"] = len(unique_speakers) if unique_speakers else 0

    return transcription


def _smooth_speaker_changes(segments: list) -> None:
    """Suaviza cambios bruscos de speaker."""
    if len(segments) < 3:
        return

    for i in range(1, len(segments) - 1):
        prev_speaker = segments[i - 1].get("speaker")
        curr_speaker = segments[i].get("speaker")
        next_speaker = segments[i + 1].get("speaker")

        if prev_speaker == next_speaker and curr_speaker != prev_speaker:
            seg_duration = segments[i]["end"] - segments[i]["start"]
            if seg_duration < 3.0:
                segments[i]["speaker"] = prev_speaker

    for i, seg in enumerate(segments):
        if seg.get("speaker") == "Unknown" or seg.get("speaker") is None:
            prev_speaker = None
            next_speaker = None

            for j in range(i - 1, -1, -1):
                if segments[j].get("speaker") and segments[j]["speaker"] != "Unknown":
                    prev_speaker = segments[j]["speaker"]
                    break

            for j in range(i + 1, len(segments)):
                if segments[j].get("speaker") and segments[j]["speaker"] != "Unknown":
                    next_speaker = segments[j]["speaker"]
                    break

            if prev_speaker:
                seg["speaker"] = prev_speaker
            elif next_speaker:
                seg["speaker"] = next_speaker
