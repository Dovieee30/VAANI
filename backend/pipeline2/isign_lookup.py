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
        self.word_index = {
            "hello": "/videos/hello.mp4", "namaste": "/videos/namaste.mp4",
            "water": "/videos/water.mp4", "food": "/videos/food.mp4",
            "doctor": "/videos/doctor.mp4", "hospital": "/videos/hospital.mp4",
            "help": "/videos/help.mp4", "yes": "/videos/yes.mp4",
            "no": "/videos/no.mp4", "please": "/videos/please.mp4",
            "sorry": "/videos/sorry.mp4", "good": "/videos/good.mp4",
            "morning": "/videos/morning.mp4", "mother": "/videos/mother.mp4",
            "father": "/videos/father.mp4", "thank_you": "/videos/thank_you.mp4",
        }
        self.sentence_index = {
            "good morning": "/videos/good_morning.mp4",
            "thank you very much": "/videos/thank_you_very_much.mp4",
        }

    def _load_alphabet(self):
        for letter in "abcdefghijklmnopqrstuvwxyz":
            self.alphabet_videos[letter] = f"/videos/alphabet/{letter}.mp4"

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
