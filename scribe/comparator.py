"""
Módulo para comparar transcripciones y detectar discrepancias.
"""

import difflib
from typing import List, Optional


def compare_transcriptions(
    full_transcription: dict,
    separated_transcriptions: List[dict],
) -> dict:
    """
    Compara la transcripción completa con las transcripciones separadas
    y marca discrepancias.

    Args:
        full_transcription: Transcripción del audio completo
        separated_transcriptions: Lista de transcripciones por speaker

    Returns:
        Transcripción con flags de verificación
    """
    # Combinar todas las transcripciones separadas en un diccionario por tiempo
    separated_by_time = _build_time_index(separated_transcriptions)

    # Comparar cada segmento
    for segment in full_transcription["segments"]:
        seg_start = segment["start"]
        seg_end = segment["end"]
        full_text = segment.get("text", "").strip()

        # Buscar texto correspondiente en transcripciones separadas
        separated_text = _find_matching_text(
            separated_by_time,
            seg_start,
            seg_end,
        )

        if separated_text:
            # Comparar textos
            similarity = _calculate_similarity(full_text, separated_text)

            if similarity < 0.85:  # Menos de 85% similar = posible error
                # Encontrar palabras diferentes
                diff_words = _find_different_words(full_text, separated_text)

                segment["needs_review"] = True
                segment["review_note"] = _create_short_note(diff_words)
                segment["verification"] = {
                    "separated_text": separated_text,
                    "similarity": round(similarity, 2),
                }
            else:
                # Alta similitud = verificado
                if "verification" not in segment:
                    segment["verification"] = {}
                segment["verification"]["verified"] = True
                segment["verification"]["similarity"] = round(similarity, 2)

    # Actualizar contador de revisiones necesarias
    needs_review_count = sum(
        1 for s in full_transcription["segments"]
        if s.get("needs_review", False)
    )
    full_transcription["review_needed"] = needs_review_count

    return full_transcription


def _build_time_index(transcriptions: List[dict]) -> dict:
    """
    Construye un índice de segmentos por tiempo para búsqueda rápida.
    """
    time_index = {}

    for trans in transcriptions:
        for segment in trans.get("segments", []):
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            text = segment.get("text", "").strip()

            # Usar el punto medio como clave
            mid = (start + end) / 2
            key = round(mid, 1)  # Redondear a 0.1 segundos

            if key not in time_index:
                time_index[key] = []
            time_index[key].append({
                "start": start,
                "end": end,
                "text": text,
            })

    return time_index


def _find_matching_text(
    time_index: dict,
    start: float,
    end: float,
    tolerance: float = 2.0,
) -> Optional[str]:
    """
    Busca texto que corresponda al rango de tiempo dado.
    """
    mid = (start + end) / 2
    matched_texts = []

    # Buscar en un rango de tolerancia
    for key in time_index:
        if abs(key - mid) <= tolerance:
            for segment in time_index[key]:
                # Verificar overlap
                seg_start = segment["start"]
                seg_end = segment["end"]

                if _has_overlap(start, end, seg_start, seg_end):
                    matched_texts.append(segment["text"])

    if matched_texts:
        return " ".join(matched_texts)
    return None


def _has_overlap(start1: float, end1: float, start2: float, end2: float) -> bool:
    """Verifica si dos rangos de tiempo se superponen."""
    return start1 < end2 and start2 < end1


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calcula la similitud entre dos textos usando SequenceMatcher.
    Retorna un valor entre 0 y 1.
    """
    if not text1 or not text2:
        return 0.0

    # Normalizar textos
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()

    return difflib.SequenceMatcher(None, text1, text2).ratio()


def _find_different_words(text1: str, text2: str) -> List[tuple]:
    """
    Encuentra palabras que difieren entre dos textos.
    Retorna lista de tuplas (palabra_original, palabra_separada).
    """
    words1 = text1.lower().split()
    words2 = text2.lower().split()

    differences = []

    # Usar SequenceMatcher para alinear palabras
    matcher = difflib.SequenceMatcher(None, words1, words2)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            orig = " ".join(words1[i1:i2])
            new = " ".join(words2[j1:j2])
            differences.append((orig, new))
        elif tag == "delete":
            orig = " ".join(words1[i1:i2])
            differences.append((orig, ""))
        elif tag == "insert":
            new = " ".join(words2[j1:j2])
            differences.append(("", new))

    return differences


def _create_short_note(differences: List[tuple], max_words: int = 3) -> str:
    """
    Crea una nota corta (máximo 3 palabras) describiendo la discrepancia.
    """
    if not differences:
        return "Check audio"

    # Tomar la primera diferencia significativa
    for orig, new in differences:
        if orig and new:
            # Truncar si es muy largo
            orig_short = orig.split()[0] if orig else ""
            new_short = new.split()[0] if new else ""
            return f"Check: {orig_short}/{new_short}"[:30]
        elif orig:
            return f"Missing: {orig.split()[0]}"[:20]
        elif new:
            return f"Extra: {new.split()[0]}"[:20]

    return "Check audio"
