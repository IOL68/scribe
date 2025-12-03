"""
Módulo de proofing - análisis de confianza de transcripción
"""

import math


def add_confidence_markers(transcription: dict, threshold: float = -0.5) -> dict:
    """
    Analiza la confianza de cada segmento y marca los que necesitan revisión.

    Args:
        transcription: Resultado de la transcripción con diarización
        threshold: Umbral de log probability (menor = menos confiable)

    Returns:
        Transcripción con marcadores de confianza
    """
    for segment in transcription["segments"]:
        # Whisper usa log probabilities, más cercano a 0 = más confiable
        # Típicamente: -0.2 a 0 = muy bueno, -0.5 a -0.2 = bueno, < -0.5 = revisar
        raw_confidence = segment.get("confidence", 0)
        no_speech = segment.get("no_speech_prob", 0)

        # Convertir log probability a porcentaje aproximado
        # exp(-0.1) ≈ 0.90, exp(-0.5) ≈ 0.60, exp(-1.0) ≈ 0.37
        confidence_pct = math.exp(raw_confidence) if raw_confidence < 0 else 0.95

        # Ajustar por probabilidad de no-speech
        confidence_pct = confidence_pct * (1 - no_speech)

        # Marcar como "needs_review" si está bajo el umbral
        segment["confidence_score"] = round(confidence_pct, 2)
        segment["needs_review"] = raw_confidence < threshold or no_speech > 0.5

    # Contar segmentos que necesitan revisión
    needs_review_count = sum(1 for s in transcription["segments"] if s.get("needs_review"))
    transcription["review_needed"] = needs_review_count

    return transcription
