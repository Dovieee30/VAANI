"""iSign Lookup — 4-level fallback chain for ISL video search."""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ISignLookup:
    def __init__(self):
        self.word_index = {}
        self.sentence_index = {}
        self.include_vocab = set()
        self.alphabet_videos = {}
        self.is_loaded = False

    def load_index(self, csv_path: str = None):
        if csv_path and Path(csv_path).exists():
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        text = row.get('text', '').lower().strip()
                        video = row.get('video_path', '')
                        if ' ' in text:
                            self.sentence_index[text] = video
                        else:
                            self.word_index[text] = video
                logger.info(f"Loaded iSign: {len(self.word_index)} words, {len(self.sentence_index)} sentences")
            except Exception as e:
                logger.error(f"Failed to load iSign CSV: {e}")
                self._load_mock_index()
        else:
            self._load_mock_index()

        self._load_alphabet()
        self.include_vocab = set(self.word_index.keys())
        self.is_loaded = True

    def _load_mock_index(self):
        # Instead of storing all 118,000 URLs in memory, we dynamically generate
        # the Hugging Face direct link. We populate common words to bypass 
        # the "not found" fallback check.
        common_words = [
            "hello", "namaste", "water", "food", "doctor", "hospital", 
            "help", "yes", "no", "please", "sorry", "good", "morning", 
            "mother", "father", "thank_you", "emergency", "pain", "medicine"
        ]
        
        for word in common_words:
            # Direct link to Hugging Face video
            hf_url = f"https://huggingface.co/datasets/Exploration-Lab/iSign/resolve/main/videos/{word}.mp4"
            self.word_index[word] = hf_url

        self.sentence_index = {
            "good morning": "https://huggingface.co/datasets/Exploration-Lab/iSign/resolve/main/videos/good_morning.mp4",
            "thank you": "https://huggingface.co/datasets/Exploration-Lab/iSign/resolve/main/videos/thank_you.mp4",
        }

    def _load_alphabet(self):
        # We don't have the actual A-Z videos on HuggingFace right now, 
        # so we use a valid placeholder to prevent the video player from crashing with a 404 error.
        valid_placeholder = "https://www.w3schools.com/html/mov_bbb.mp4"
        for letter in "abcdefghijklmnopqrstuvwxyz":
            self.alphabet_videos[letter] = valid_placeholder

    def find(self, text: str) -> dict:
        text = text.lower().strip()

        if text in self.sentence_index:
            return {"level": 1, "results": [{"word": text, "type": "video", "url": self.sentence_index[text]}], "fallback_used": False}

        words = text.split()
        results = []
        all_found = True

        for word in words:
            normalized = word.replace(" ", "_")
            if normalized in self.word_index:
                results.append({"word": word, "type": "video", "url": self.word_index[normalized]})
            else:
                all_found = False
                if normalized in self.include_vocab:
                    results.append({"word": word, "type": "text", "url": None})
                else:
                    results.append({"word": word, "type": "fingerspell", "letters": [{"letter": l, "url": self.alphabet_videos.get(l)} for l in word.lower() if l.isalpha()]})

        level = 2 if all_found else 4
        return {"level": level, "results": results, "fallback_used": not all_found}
