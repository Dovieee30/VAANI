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
        placeholder_vid = "https://www.w3schools.com/html/mov_bbb.mp4"
        self.word_index = {
            "hello": placeholder_vid, "namaste": placeholder_vid,
            "water": placeholder_vid, "food": placeholder_vid,
            "doctor": placeholder_vid, "hospital": placeholder_vid,
            "help": placeholder_vid, "yes": placeholder_vid,
            "no": placeholder_vid, "please": placeholder_vid,
            "sorry": placeholder_vid, "good": placeholder_vid,
            "morning": placeholder_vid, "mother": placeholder_vid,
            "father": placeholder_vid, "thank_you": placeholder_vid,
        }
        self.sentence_index = {
            "good morning": placeholder_vid,
            "thank you very much": placeholder_vid,
        }

    def _load_alphabet(self):
        placeholder_vid = "https://www.w3schools.com/html/mov_bbb.mp4"
        for letter in "abcdefghijklmnopqrstuvwxyz":
            self.alphabet_videos[letter] = placeholder_vid

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
