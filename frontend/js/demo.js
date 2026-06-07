import { MediaPipeExtractor } from '../core/mediapipe_extractor.js';

document.addEventListener('DOMContentLoaded', async () => {
  // DOM Elements
  const videoElement = document.getElementById('demo-video');
  const canvasElement = document.getElementById('landmarks-canvas');
  const camButton = document.getElementById('cam-button');
  const pauseButton = document.getElementById('pause-button');
  const stopButton = document.getElementById('stop-button');
  const recognizedText = document.getElementById('recognized-text');
  const tabBtns = document.querySelectorAll('.tab-btn');
  const viewPanels = document.querySelectorAll('.view-panel');

  const API_BASE = 'http://localhost:8000';

  // Audio Queue
  const audioQueue = [];
  let isPlayingAudio = false;

  async function playNextAudio() {
    if (audioQueue.length === 0) {
      isPlayingAudio = false;
      return;
    }
    isPlayingAudio = true;
    const blob = audioQueue.shift();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.volume = 1.0;
    
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      playNextAudio();
    };
    
    audio.onerror = (e) => {
      console.error("Audio playback error:", e);
      URL.revokeObjectURL(audioUrl);
      playNextAudio();
    };
    
    try {
      await audio.play();
    } catch(err) {
      console.error("Audio play failed:", err);
      playNextAudio();
    }
  }

  function enqueueAudio(blob) {
    audioQueue.push(blob);
    if (!isPlayingAudio) {
      playNextAudio();
    }
  }

  function initAudio() {
    // Standard Audio doesn't strictly need a dummy init like WebAudio, 
    // but we leave this here to avoid breaking the camButton click handler.
  }

  // Initialize MediaPipe
  const extractor = new MediaPipeExtractor(videoElement, canvasElement);
  
  try {
    recognizedText.innerText = "Initializing Camera...";
    await extractor.initialize();
    await extractor.startWebcam();
    recognizedText.innerText = "Point camera to sign & tap Record";
  } catch (err) {
    console.error(err);
    recognizedText.innerText = "Camera access denied or error.";
  }

  // Camera Recording Logic
  let isRecording = false;
  let isPaused = false;

  camButton.addEventListener('click', () => {
    initAudio(); // Initialize audio on first user gesture
    
    if (isRecording) return; // Already recording

    isRecording = true;
    isPaused = false;
    
    // Update UI
    camButton.classList.add('recording');
    camButton.classList.add('hidden'); // Hide record
    pauseButton.classList.remove('hidden'); // Show pause
    stopButton.classList.remove('hidden'); // Show stop
    
    pauseButton.classList.remove('paused');
    recognizedText.innerText = "Recording... (Keep signing)";

    extractor.startRecording(async (frames) => {
      // Sequence ready (30 frames) - this fires continuously!
      recognizedText.innerText = "Processing...";

      try {
        // 1. Predict Sign
        const predictRes = await fetch(`${API_BASE}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sequence: frames })
        });
        
        if (!predictRes.ok) throw new Error("Prediction failed");
        const predictData = await predictRes.json();
        const sign = predictData.sign;
        const confidence = Math.round(predictData.confidence * 100);

        if (predictData.warning || predictData.confidence < 0.5) {
          recognizedText.innerText = `No sign detected (${confidence}%)`;
          return; // Do not speak low confidence noise
        }

        recognizedText.innerText = `${sign.toUpperCase()} (${confidence}%)`;

        // 2. Speak the text (Queue it up)
        const speakRes = await fetch(`${API_BASE}/speak`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: sign, lang: 'en' })
        });

        if (speakRes.ok) {
          const blob = await speakRes.blob();
          enqueueAudio(blob);
        }

      } catch (err) {
        console.error(err);
        if (isRecording && !isPaused) {
          recognizedText.innerText = "Error connecting to server";
        }
      }
    });
  });

  pauseButton.addEventListener('click', () => {
    if (!isRecording) return;
    
    if (isPaused) {
      // Resume
      isPaused = false;
      extractor.resumeRecording();
      pauseButton.classList.remove('paused');
      recognizedText.innerText = "Recording... (Keep signing)";
    } else {
      // Pause
      isPaused = true;
      extractor.pauseRecording();
      pauseButton.classList.add('paused');
      recognizedText.innerText = "Paused";
    }
  });

  stopButton.addEventListener('click', () => {
    if (!isRecording) return;
    
    isRecording = false;
    isPaused = false;
    extractor.stopRecording();
    
    // Update UI
    camButton.classList.remove('recording');
    camButton.classList.remove('hidden');
    pauseButton.classList.add('hidden');
    stopButton.classList.add('hidden');
    pauseButton.classList.remove('paused');
    
    recognizedText.innerText = "Point camera to sign & tap Record";
  });

  // Tab Switching Logic
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-target');
      document.getElementById(targetId).classList.add('active');
    });
  });
});
