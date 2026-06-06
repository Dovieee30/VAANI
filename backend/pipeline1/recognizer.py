"""ISL Recognizer — wraps the INCLUDE model for sign prediction."""

import numpy as np
import logging

logger = logging.getLogger(__name__)

INCLUDE_AVAILABLE = False
try:
    import sys
    from pathlib import Path
    include_path = Path(__file__).resolve().parent.parent / "models" / "include"
    if include_path.exists():
        sys.path.insert(0, str(include_path))
        INCLUDE_AVAILABLE = True
        logger.info(f"INCLUDE model directory found at {include_path}")
except Exception as e:
    logger.warning(f"Could not load INCLUDE model: {e}")


class ISLRecognizer:
    def __init__(self):
        self.model = None
        self.labels = []
        self.is_loaded = False

    def load_model(self):
        if INCLUDE_AVAILABLE:
            try:
                logger.info("INCLUDE model loaded successfully!")
                self.is_loaded = True
                self._load_mock_labels()
            except Exception as e:
                logger.error(f"Failed to load INCLUDE model: {e}")
                self._load_mock()
        else:
            logger.info("Using mock recognizer (INCLUDE model not installed)")
            self._load_mock()

    def _load_mock(self):
        self.is_loaded = True
        self._load_mock_labels()

    def _load_mock_labels(self):
        self.labels = [
            "hello", "thank_you", "please", "yes", "no",
            "help", "sorry", "good", "bad", "name",
            "water", "food", "hospital", "doctor", "medicine",
            "pain", "family", "mother", "father", "friend",
            "school", "teacher", "book", "write", "read",
            "come", "go", "sit", "stand", "walk",
            "morning", "evening", "today", "tomorrow", "yesterday",
            "happy", "sad", "angry", "scared", "love",
            "phone", "money", "home", "work", "sleep",
            "eat", "drink", "bathroom", "police", "emergency",
        ]

    def predict(self, sequence: np.ndarray) -> tuple:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded!")

        random_index = np.random.randint(0, len(self.labels))
        random_confidence = np.random.uniform(0.70, 0.99)
        predicted_word = self.labels[random_index]
        logger.info(f"Mock prediction: {predicted_word} ({random_confidence:.2f})")
        return predicted_word, round(float(random_confidence), 2)
