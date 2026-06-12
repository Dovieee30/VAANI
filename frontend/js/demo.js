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

  // If running as a native Capacitor app, there is no Vite proxy, so we must point directly to the backend IP.
  // Otherwise, we rely on the Vite dev server proxy using empty string.
  const isCapacitor = typeof window.Capacitor !== 'undefined';
  const BACKEND_IP = '10.29.82.162:8000';
  const API_BASE = isCapacitor ? `http://${BACKEND_IP}` : '';

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
    recognizedText.innerText = "Opening Camera...";
    await extractor.startWebcam(); // This opens the camera instantly!
    
    recognizedText.innerText = "Loading AI Models...";
    await extractor.initialize();  // This downloads the heavy models in the background.
    
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

  let audioContext = null;
  let audioProcessor = null;
  let audioSource = null;
  let ws = null;
  let finalResultText = "";
  let currentPartialText = "";

  let currentStream = null;
  let isConnecting = false;
  let isRecordingAudio = false;

  if (micButton) {
    const startRecording = async (e) => {
      if (e) e.preventDefault();
      console.log("Mic button clicked! Starting recording...");
      if (isRecordingAudio || isConnecting) return;
      
      isConnecting = true;
      speechTranscript.innerText = `[1/4] Requesting mic... (Capacitor: ${isCapacitor})`;
      
      try {
        currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        speechTranscript.innerText = "[2/4] Mic granted. Setup AudioContext...";
        
        // Initialize AudioContext
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioSource = audioContext.createMediaStreamSource(currentStream);
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        speechTranscript.innerText = "[3/4] Audio ready. Connecting to Server...";
        
        // Get selected language
        const selectedLang = document.getElementById('language-select') ? document.getElementById('language-select').value : 'en';

        // Connect WebSocket dynamically
        let wsUrl;
        if (isCapacitor) {
          wsUrl = `ws://${BACKEND_IP}/ws/listen?language=${selectedLang}`;
        } else {
          const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          wsUrl = `${wsProtocol}//${window.location.host}/ws/listen?language=${selectedLang}`;
        }
        
        speechTranscript.innerText = `[4/4] Connecting WS: ${wsUrl}...`;
        ws = new WebSocket(wsUrl);
        finalResultText = "";
        currentPartialText = "";
        let wsErrorOccurred = false;
        
        ws.onopen = () => {
          console.log("WebSocket connected.");
          
          // Connect nodes to start capturing without causing feedback echo
          const gainNode = audioContext.createGain();
          gainNode.gain.value = 0; // Mute the output to speakers
          
          audioSource.connect(audioProcessor);
          audioProcessor.connect(gainNode);
          gainNode.connect(audioContext.destination);
          
          isRecordingAudio = true;
          isConnecting = false;
          micButton.style.background = '#ff3b30'; // Red when recording
          micButton.style.transform = 'scale(0.9)'; // Visual feedback
          speechTranscript.innerText = "Listening... (Tap again to stop)";
        };
        
        ws.onerror = (error) => {
          console.error("WebSocket Error:", error);
          wsErrorOccurred = true;
          speechTranscript.innerText = "Error connecting to server. Is backend running?";
          isRecordingAudio = false;
          isConnecting = false;
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'partial') {
            currentPartialText = data.text;
            let display = finalResultText;
            if (currentPartialText) display += (display ? " " : "") + currentPartialText;
            speechTranscript.innerText = display ? `"${display}"...` : "Listening...";
          } else if (data.type === 'final') {
            finalResultText += (finalResultText ? " " : "") + data.text;
            currentPartialText = "";
            speechTranscript.innerText = `"${finalResultText}"`;
          }
        };

        ws.onclose = (event) => {
            console.log("WebSocket closed.", event.code, event.reason);
            isRecordingAudio = false;
            isConnecting = false;
            if (wsErrorOccurred) return; // Don't overwrite the error message
            
            // Use whatever text we have (final + any lingering partial)
            let combined = finalResultText;
            if (currentPartialText && !combined.endsWith(currentPartialText)) {
                combined += (combined ? " " : "") + currentPartialText;
            }
            if (combined.trim()) {
               speechTranscript.innerText = "Processing...";
               lookupText(combined.trim());
            } else {
               speechTranscript.innerText = `No speech detected. (Code: ${event.code})`;
            }
        };
        
        let audioLogCounter = 0;
        audioProcessor.onaudioprocess = (e) => {
          if (!isRecordingAudio || ws.readyState !== WebSocket.OPEN) return;
          const inputData = e.inputBuffer.getChannelData(0);
          
          // Debug: log volume and sample rate periodically
          audioLogCounter++;
          if (audioLogCounter % 20 === 1) {
            let maxVal = 0, sum = 0;
            for (let i = 0; i < inputData.length; i++) {
              const abs = Math.abs(inputData[i]);
              sum += abs;
              if (abs > maxVal) maxVal = abs;
            }
            const avg = sum / inputData.length;
            console.log(`[Audio] sampleRate=${audioContext.sampleRate}, bufferLen=${inputData.length}, avgLevel=${avg.toFixed(5)}, maxLevel=${maxVal.toFixed(4)}`);
          }
          
          // Proper resampling to 16kHz using linear interpolation
          const actualRate = audioContext.sampleRate;
          const targetRate = 16000;
          
          let pcm16;
          if (Math.abs(actualRate - targetRate) < 100) {
            // Already at ~16kHz, just convert to Int16
            pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]));
              pcm16[i] = s * 0x7FFF;
            }
          } else {
            // Resample using linear interpolation (much better than decimation)
            const ratio = actualRate / targetRate;
            const outputLen = Math.floor(inputData.length / ratio);
            pcm16 = new Int16Array(outputLen);
            for (let i = 0; i < outputLen; i++) {
              const srcIdx = i * ratio;
              const idx0 = Math.floor(srcIdx);
              const idx1 = Math.min(idx0 + 1, inputData.length - 1);
              const frac = srcIdx - idx0;
              const sample = inputData[idx0] + frac * (inputData[idx1] - inputData[idx0]);
              const clamped = Math.max(-1, Math.min(1, sample));
              pcm16[i] = clamped * 0x7FFF;
            }
          }
          
          ws.send(pcm16.buffer);
        };
        
      } catch (err) {
        console.error("Microphone error:", err);
        speechTranscript.innerText = `Microphone error: ${err.message || err.name || err}. Please check permissions.`;
        isConnecting = false;
      }
    };

    const stopRecording = (e) => {
      if (e) e.preventDefault();
      if (!isRecordingAudio) return;
      
      isRecordingAudio = false;
      micButton.style.background = ''; // Reset to default
      micButton.style.transform = 'scale(1)';
      speechTranscript.innerText = "Processing...";
      
      // Stop audio capture first
      if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
      }
      if (audioSource) {
        audioSource.disconnect();
        audioSource = null;
      }
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
      }
      if (audioContext) {
        audioContext.close();
        audioContext = null;
      }
      
      // Wait a bit for Vosk to process remaining audio, then close WebSocket
      setTimeout(() => {
        if (ws) {
          ws.close();
          ws = null;
        }
      }, 500);
    };

    // Toggle recording on click
    micButton.addEventListener('click', (e) => {
      if (e) e.preventDefault();
      if (isRecordingAudio) {
        stopRecording(e);
      } else {
        startRecording(e);
      }
    });
  }

  async function lookupText(text) {
    try {
      speechTranscript.innerText = `"${text}"`;

      // Send to /lookup
      const lookupRes = await fetch(`${API_BASE}/lookup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (!lookupRes.ok) throw new Error("Lookup failed");
      const lookupData = await lookupRes.json();

      // Play video sequence
      playSequence(lookupData.results);

    } catch (err) {
      console.error(err);
      speechTranscript.innerText = "Error playing videos.";
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
