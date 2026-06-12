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
        self.device = None

    def load_model(self):
        if INCLUDE_AVAILABLE:
            try:
                import torch
                import json
                from configs import LstmConfig
                from models.lstm import LSTM

                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

                logger.info("Loading PyTorch Transformer model...")
                label_map_path = include_path / "label_maps" / "label_map.json"
                with open(label_map_path, 'r') as f:
                    labels_dict = json.load(f)
                
                # Invert dictionary to get index -> label mapping
                self.labels = [""] * len(labels_dict)
                for k, v in labels_dict.items():
                    self.labels[v] = k

                config = LstmConfig()
                self.model = LSTM(config, n_classes=len(self.labels))
                self.model = self.model.to(self.device)

                weights_path = include_path / "include_no_cnn_lstm.pth"
                if not weights_path.exists():
                    logger.warning(f"Weights file not found at {weights_path}. Using mock.")
                    self._load_mock()
                    return

                ckpt = torch.load(weights_path, map_location=self.device, weights_only=False)
                if "model" in ckpt:
                    self.model.load_state_dict(ckpt["model"])
                else:
                    self.model.load_state_dict(ckpt)
                
                self.model.eval()
                self.is_loaded = True
                logger.info("INCLUDE PyTorch model loaded successfully!")
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
            "hello", "thank_you", "please", "yes", "no", "water", "food", "help"
        ]

    def predict(self, sequence: np.ndarray) -> tuple:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded!")

        if self.model is None:
            random_index = np.random.randint(0, len(self.labels))
            predicted_word = self.labels[random_index]
            return predicted_word, 0.99

        import torch
        import torch.nn.functional as F

        # Sequence should be (frames, 134). Add batch dimension -> (1, frames, 134)
        input_tensor = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            preds = self.model(input_tensor)
            probs = torch.softmax(preds, dim=-1)
            confidence, class_idx = torch.max(probs, dim=-1)

        predicted_word = self.labels[class_idx.item()]
        return predicted_word, round(confidence.item(), 2)
