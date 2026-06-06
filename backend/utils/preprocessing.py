"""
Preprocessing — validates and normalizes MediaPipe landmark sequences.
"""

import numpy as np
from config import NUM_FRAMES, LANDMARK_DIMS


def validate_sequence(sequence: list) -> np.ndarray:
    """Validates raw landmark data from frontend and ensures correct shape."""
    arr = np.array(sequence, dtype=np.float32)

    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got {arr.ndim}D")

    if arr.shape[1] != LANDMARK_DIMS:
        raise ValueError(f"Expected {LANDMARK_DIMS} values per frame, got {arr.shape[1]}")

    arr = pad_or_truncate(arr, NUM_FRAMES)
    return arr


def pad_or_truncate(sequence: np.ndarray, target_length: int) -> np.ndarray:
    """Pads with zeros or truncates to exactly target_length frames."""
    current_length = sequence.shape[0]

    if current_length == target_length:
        return sequence
    elif current_length < target_length:
        padding = np.zeros(
            (target_length - current_length, sequence.shape[1]),
            dtype=np.float32
        )
        return np.concatenate([sequence, padding], axis=0)
    else:
        return sequence[:target_length]


def normalize_landmarks(sequence: np.ndarray) -> np.ndarray:
    """Normalizes landmarks (placeholder — INCLUDE handles its own normalization)."""
    return sequence
