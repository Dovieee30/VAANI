"""
Preprocessing — validates and normalizes MediaPipe landmark sequences.
"""

import numpy as np
from config import NUM_FRAMES, LANDMARK_DIMS


def extract_include_features(frame: np.ndarray) -> np.ndarray:
    features = []
    # 1. 25 pose landmarks: x, y (interleaved)
    for i in range(25):
        features.append(frame[i*4] * 1920.0)       # pose_x
        features.append(frame[i*4 + 1] * 1080.0)   # pose_y
        
    # 2. 21 left_hand landmarks: x, y
    for i in range(21):
        features.append(frame[1536 + i*3] * 1920.0)      # left_hand_x
        features.append(frame[1536 + i*3 + 1] * 1080.0)  # left_hand_y
        
    # 3. 21 right_hand landmarks: x, y
    for i in range(21):
        features.append(frame[1599 + i*3] * 1920.0)      # right_hand_x
        features.append(frame[1599 + i*3 + 1] * 1080.0)  # right_hand_y
        
    return np.array(features, dtype=np.float32)

def validate_sequence(sequence: list) -> np.ndarray:
    arr = np.array(sequence, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got {arr.ndim}D")

    if arr.shape[1] == LANDMARK_DIMS:
        # Convert 1662 to 134
        new_arr = np.zeros((arr.shape[0], 134), dtype=np.float32)
        for i in range(arr.shape[0]):
            new_arr[i] = extract_include_features(arr[i])
        arr = new_arr
    elif arr.shape[1] != 134:
        raise ValueError(f"Expected {LANDMARK_DIMS} or 134 values per frame, got {arr.shape[1]}")

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
