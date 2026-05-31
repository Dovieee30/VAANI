import { MediaPipeExtractor } from '../core/mediapipe_extractor.js';

document.addEventListener('DOMContentLoaded', async () => {
  const videoElement = document.getElementById('demo-video');
  const canvasElement = document.getElementById('landmarks-canvas');
  const recognizedText = document.getElementById('recognized-text');

  if (!videoElement || !canvasElement) return;

  const extractor = new MediaPipeExtractor(videoElement, canvasElement);
  
  // Callback when 30 frames are ready to be sent to the backend
  extractor.onSequenceReady = async (sequenceData) => {
    console.log(`Captured ${sequenceData.length} frames of landmarks.`);
    if (recognizedText) recognizedText.innerText = "Processing...";
    
    // TODO: In the future, send 'sequenceData' to the FastAPI backend
    // const response = await fetch('http://localhost:8000/predict', { ... })
    
    // Mock response for now
    setTimeout(() => {
      if (recognizedText) recognizedText.innerText = "नमस्ते (Hello)";
    }, 1000);
  };

  const camBtn = document.querySelector('.cam-button');
  
  let cameraReady = false;
  let isRecording = false;

  if (camBtn) {
    camBtn.addEventListener('click', async () => {
      // If camera isn't on yet, first click initializes it AND starts recording
      if (!cameraReady) {
        camBtn.disabled = true;
        camBtn.style.opacity = '0.5';

        try {
          if (recognizedText) recognizedText.innerText = "Starting Camera...";
          await extractor.startWebcam();
          videoElement.style.display = 'block';
          
          if (recognizedText) recognizedText.innerText = "Loading AI Model...";
          const isInitialized = await extractor.initialize();
          
          if (isInitialized) {
            cameraReady = true;
            isRecording = true;
            camBtn.style.background = '#e74c3c'; // Red for recording
            if (recognizedText) recognizedText.innerText = "Recording...";
            extractor.startRecording();
          } else {
            if (recognizedText) recognizedText.innerText = "Failed to initialize";
          }
        } catch (e) {
          console.error(e);
          if (recognizedText) recognizedText.innerText = "Error starting demo";
        } finally {
          camBtn.disabled = false;
          camBtn.style.opacity = '1';
        }
      } 
      // If camera is ready, toggle recording on/off
      else {
        if (!isRecording) {
          // Start Recording
          isRecording = true;
          camBtn.style.background = '#e74c3c'; // Red for recording
          if (recognizedText) recognizedText.innerText = "Recording...";
          extractor.startRecording();
        } else {
          // Stop Recording
          isRecording = false;
          camBtn.style.background = 'var(--color-teal)';
          if (recognizedText) recognizedText.innerText = "Processing...";
          extractor.stopRecording();
          
          // Note: When stopped manually before 30 frames, we might need 
          // to trigger the backend call here manually in the future!
        }
      }
    });
  }

  // Tab Switching Logic
  const tabBtns = document.querySelectorAll('.tab-btn');
  const viewPanels = document.querySelectorAll('.view-panel');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Remove active class from all tabs
      tabBtns.forEach(b => b.classList.remove('active'));
      // Remove active class from all panels
      viewPanels.forEach(p => p.classList.remove('active'));

      // Add active to clicked tab
      btn.classList.add('active');
      // Show target panel
      const targetId = btn.getAttribute('data-target');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }
    });
  });
});
