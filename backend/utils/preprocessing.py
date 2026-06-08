"""
Preprocessing — validates and normalizes MediaPipe landmark sequences.
"""

import numpy as np
from config import NUM_FRAMES, LANDMARK_DIMS


def extract_include_features(frame: np.ndarray) -> np.ndarray:
    features = []
    
    # --- DYNAMIC SPATIAL NORMALIZATION ---
    # The INCLUDE dataset has signers perfectly framed. We need to shift and scale
    # the user's live webcam coordinates to match that exact framing.
    
    # Base reference points from raw normalized [0, 1] frame
    nose_x = frame[0*4]
    nose_y = frame[0*4 + 1]
    
    shoulder_l_x = frame[11*4]
    shoulder_r_x = frame[12*4]
    
    # Calculate scale factor to force shoulder width to ~0.22 (which is ~420 pixels on 1920 canvas)
    shoulder_width = abs(shoulder_l_x - shoulder_r_x)
    if shoulder_width < 0.05: 
        shoulder_width = 0.22 # Fallback if shoulders not detected well
        
    scale_factor = 0.22 / shoulder_width
    
    # Helper to shift, scale, and project to 1920x1080
    def norm_point(x, y):
        nx = (x - nose_x) * scale_factor
        ny = (y - nose_y) * scale_factor
        # Shift to target nose position (0.5 center X, 0.3 top Y)
        return (0.5 + nx) * 1920.0, (0.3 + ny) * 1080.0

    # 1. 25 pose landmarks: x, y (interleaved)
    for i in range(25):
        px, py = norm_point(frame[i*4], frame[i*4 + 1])
        features.append(px)
        features.append(py)
        
    # 2. 21 left_hand landmarks: x, y
    for i in range(21):
        hx, hy = norm_point(frame[1536 + i*3], frame[1536 + i*3 + 1])
        features.append(hx)
        features.append(hy)
        
    # 3. 21 right_hand landmarks: x, y
    for i in range(21):
        hx, hy = norm_point(frame[1599 + i*3], frame[1599 + i*3 + 1])
        features.append(hx)
        features.append(hy)
        
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
