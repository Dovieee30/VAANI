import os
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(r"C:\Users\ASUS\OneDrive\Desktop\Projects\VAANI\backend")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MODELS = {
    "vosk-model-small-hi-0.22": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip",
    "vosk-model-small-en-us-0.15": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    "vosk-model-small-en-in-0.4": "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
}

def download_and_extract():
    for model_name, url in MODELS.items():
        zip_path = DATA_DIR / f"{model_name}.zip"
        extract_path = DATA_DIR / model_name
        
        if not extract_path.exists():
            print(f"Downloading {model_name}...")
            urllib.request.urlretrieve(url, zip_path)
            
            print(f"Extracting {model_name}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DATA_DIR)
                
            os.remove(zip_path)
            print(f"Finished {model_name}!")
        else:
            print(f"{model_name} already exists.")

if __name__ == "__main__":
    download_and_extract()
