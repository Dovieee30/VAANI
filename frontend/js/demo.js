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
          recognizedText.innerText = `Low Confidence: ${sign.toUpperCase()} (${confidence}%)`;
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

  // ==========================================
  // PIPELINE 2: SPEECH-TO-SIGN LOGIC
  // ==========================================
  const micButton = document.getElementById('mic-button');
  const avatarPlaceholder = document.getElementById('avatar-placeholder');
  const signPlayer = document.getElementById('sign-player');
  const speechTranscript = document.getElementById('speech-transcript');

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecordingAudio = false;

  if (micButton) {
    const startRecording = async (e) => {
      e.preventDefault();
      if (isRecordingAudio) return;
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          await processAudio(audioBlob);
        };

        mediaRecorder.start();
        isRecordingAudio = true;
        micButton.style.background = '#ff3b30'; // Red when recording
        micButton.style.transform = 'scale(0.9)'; // Visual feedback
        speechTranscript.innerText = "Listening... (Release to send)";
      } catch (err) {
        console.error("Microphone access denied", err);
        speechTranscript.innerText = "Microphone access denied.";
      }
    };

    const stopRecording = (e) => {
      e.preventDefault();
      if (!isRecordingAudio) return;
      
      mediaRecorder.stop();
      isRecordingAudio = false;
      micButton.style.background = ''; // Reset to default
      micButton.style.transform = 'scale(1)';
      speechTranscript.innerText = "Processing...";
      
      // Stop all tracks to release mic
      if (mediaRecorder && mediaRecorder.stream) {
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
    };

    // Mobile touch events (Push-to-Talk)
    micButton.addEventListener('touchstart', startRecording, {passive: false});
    micButton.addEventListener('touchend', stopRecording);
    micButton.addEventListener('touchcancel', stopRecording);
    
    // Desktop mouse events (Push-to-Talk)
    micButton.addEventListener('mousedown', startRecording);
    window.addEventListener('mouseup', stopRecording); // Attach to window in case cursor moves off button
  }

  async function processAudio(audioBlob) {
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "speech.wav");

      // 1. Send to /listen (using English model since you are speaking English)
      const listenRes = await fetch(`${API_BASE}/listen?language=en`, {
        method: 'POST',
        body: formData
      });
      
      if (!listenRes.ok) throw new Error("Listen failed");
      const listenData = await listenRes.json();

      
      const text = listenData.text;
      if (!text) {
        speechTranscript.innerText = "Could not understand audio.";
        return;
      }
      
      speechTranscript.innerText = `"${text}"`;

      // 2. Send to /lookup
      const lookupRes = await fetch(`${API_BASE}/lookup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (!lookupRes.ok) throw new Error("Lookup failed");
      const lookupData = await lookupRes.json();

      // 3. Play video sequence
      playSequence(lookupData.results);

    } catch (err) {
      console.error(err);
      speechTranscript.innerText = "Error processing audio.";
    }
  }

  function playSequence(results) {
    if (!results || results.length === 0) return;
    
    // Hide avatar, show player
    avatarPlaceholder.classList.add('hidden');
    signPlayer.classList.remove('hidden');

    let currentIndex = 0;

    function playNext() {
      if (currentIndex >= results.length) {
        // Finished playing all videos
        setTimeout(() => {
          signPlayer.classList.add('hidden');
          avatarPlaceholder.classList.remove('hidden');
          speechTranscript.innerText = "Tap mic to speak again.";
        }, 1000);
        return;
      }

      const item = results[currentIndex];
      
      if (item.type === 'video' && item.url) {
        speechTranscript.innerHTML = `<strong>${item.word.toUpperCase()}</strong>`;
        signPlayer.src = item.url;
        signPlayer.onended = () => {
          currentIndex++;
          playNext();
        };
        signPlayer.play().catch(err => {
          console.error("Video play error:", err);
          currentIndex++;
          playNext();
        });
      } else if (item.type === 'text') {
        // Fallback Level 3: Show Text
        signPlayer.classList.add('hidden');
        avatarPlaceholder.classList.remove('hidden');
        speechTranscript.innerHTML = `[ ${item.word.toUpperCase()} ]`;
        
        setTimeout(() => {
          signPlayer.classList.remove('hidden');
          avatarPlaceholder.classList.add('hidden');
          currentIndex++;
          playNext();
        }, 1500); // Wait 1.5 seconds for text reading
      } else if (item.type === 'fingerspell') {
        // Fallback Level 4: Fingerspell Letters
        playFingerspell(item.word, item.letters, () => {
          currentIndex++;
          playNext();
        });
      } else {
        currentIndex++;
        playNext();
      }
    }

    function playFingerspell(word, letters, onComplete) {
      let lIndex = 0;
      function playNextLetter() {
        if (lIndex >= letters.length) {
          onComplete();
          return;
        }
        const lItem = letters[lIndex];
        speechTranscript.innerHTML = `<strong>${word.toUpperCase()}</strong><br><small>Letter: ${lItem.letter.toUpperCase()}</small>`;
        
        if (lItem.url) {
          signPlayer.src = lItem.url;
          signPlayer.onended = () => {
            lIndex++;
            playNextLetter();
          };
          signPlayer.play().catch(err => {
            lIndex++;
            playNextLetter();
          });
        } else {
          lIndex++;
          playNextLetter();
        }
      }
      playNextLetter();
    }

    playNext();
  }
});
