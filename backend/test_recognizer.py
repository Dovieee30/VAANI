import logging
logging.basicConfig(level=logging.INFO)

print("Starting test...")
import sys
from pathlib import Path

print("Importing pipeline1.recognizer...")
from pipeline1.recognizer import ISLRecognizer

print("Creating recognizer...")
r = ISLRecognizer()

print("Calling load_model...")
import time
start = time.time()
print("1. About to import torch...")
import torch
print(f"Torch imported in {time.time() - start:.2f}s")

print("2. About to check CUDA...")
start = time.time()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"CUDA checked in {time.time() - start:.2f}s. Device: {device}")

print("3. About to call r.load_model()...")
r.load_model()
print("Recognizer done:", r.is_loaded)
