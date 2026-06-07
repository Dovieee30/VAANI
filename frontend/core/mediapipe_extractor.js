import {
  HolisticLandmarker,
  FilesetResolver
} from '@mediapipe/tasks-vision';

export class MediaPipeExtractor {
  constructor(videoElement, canvasElement) {
    this.videoElement = videoElement;
    this.canvasElement = canvasElement;
    this.canvasCtx = canvasElement.getContext('2d');
    
    this.holisticLandmarker = null;
    this.runningMode = "VIDEO";
    this.lastVideoTime = -1;
    this.isRecording = false;
    
    // We keep a buffer of the last 30 frames
    this.frameBuffer = [];
    this.maxFrames = 30;
    
    this.onSequenceReady = null; // Callback when 30 frames are ready
    this.isPaused = false;
  }

  async initialize() {
    console.log("Initializing MediaPipe Holistic Landmarker...");
    try {
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
      );
      
      this.holisticLandmarker = await HolisticLandmarker.createFromOptions(vision, {
        baseOptions: {
          // Using the default holistic landmarker task model
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task",
          delegate: "GPU"
        },
        runningMode: this.runningMode,
      });
      
      console.log("MediaPipe Holistic initialized successfully.");
      return true;
    } catch (error) {
      console.error("Error initializing MediaPipe:", error);
      return false;
    }
  }

  async startWebcam() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Webcam access not supported. Are you on localhost or HTTPS?");
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "user"
      }
    });
    
    this.videoElement.srcObject = stream;
    this.videoElement.setAttribute('playsinline', '');
    this.videoElement.muted = true;
    
    return new Promise((resolve) => {
      this.videoElement.onloadedmetadata = async () => {
        try {
          await this.videoElement.play();
        } catch (e) {
          console.error("Error playing video:", e);
        }
        
        this.canvasElement.width = this.videoElement.videoWidth || 1280;
        this.canvasElement.height = this.videoElement.videoHeight || 720;
        
        // Start prediction loop only once
        if (!this.loopStarted) {
          this.loopStarted = true;
          this.predictWebcam();
        }
        resolve();
      };
    });
  }

  startRecording(callback) {
    this.isRecording = true;
    this.isPaused = false;
    this.frameBuffer = [];
    this.onSequenceReady = callback;
    console.log("Started recording a sign sequence...");
  }

  pauseRecording() {
    this.isPaused = true;
    console.log("Paused recording...");
  }

  resumeRecording() {
    this.isPaused = false;
    console.log("Resumed recording...");
  }

  stopRecording() {
    this.isRecording = false;
    this.isPaused = false;
  }

  async predictWebcam() {
    // Resize canvas if needed
    if (this.canvasElement.width !== this.videoElement.videoWidth) {
      this.canvasElement.width = this.videoElement.videoWidth;
      this.canvasElement.height = this.videoElement.videoHeight;
    }

    let startTimeMs = performance.now();
    if (this.lastVideoTime !== this.videoElement.currentTime) {
      this.lastVideoTime = this.videoElement.currentTime;
      
      if (this.holisticLandmarker) {
        const results = this.holisticLandmarker.detectForVideo(this.videoElement, startTimeMs);
        this.processAndDrawResults(results);
      }
    }

    // Loop
    window.requestAnimationFrame(this.predictWebcam.bind(this));
  }

  processAndDrawResults(results) {
    this.canvasCtx.save();
    this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

    // If we are recording and not paused, save the flat landmarks
    if (this.isRecording && !this.isPaused) {
      const flatFrame = this.flattenLandmarks(results);
      this.frameBuffer.push(flatFrame);
      
      if (this.frameBuffer.length >= this.maxFrames) {
        if (this.onSequenceReady) {
          this.onSequenceReady(this.frameBuffer); // Send 30 frames
        }
        this.frameBuffer = []; // Reset buffer but keep recording
      }
    }

    // Draw Face
    if (results.faceLandmarks && results.faceLandmarks.length > 0) {
      this.drawLandmarks(results.faceLandmarks[0], '#C94E2B', 1);
    }
    
    // Draw Pose
    if (results.poseLandmarks && results.poseLandmarks.length > 0) {
      this.drawLandmarks(results.poseLandmarks[0], '#1A5C6B', 2);
    }
    
    // Draw Left Hand
    if (results.leftHandLandmarks && results.leftHandLandmarks.length > 0) {
      this.drawLandmarks(results.leftHandLandmarks[0], '#2E7D52', 2);
    }
    
    // Draw Right Hand
    if (results.rightHandLandmarks && results.rightHandLandmarks.length > 0) {
      this.drawLandmarks(results.rightHandLandmarks[0], '#2E7D52', 2);
    }

    this.canvasCtx.restore();
  }

  drawLandmarks(landmarks, color, radius) {
    this.canvasCtx.fillStyle = color;
    for (const landmark of landmarks) {
      const x = landmark.x * this.canvasElement.width;
      const y = landmark.y * this.canvasElement.height;
      
      this.canvasCtx.beginPath();
      this.canvasCtx.arc(x, y, radius, 0, 2 * Math.PI);
      this.canvasCtx.fill();
    }
  }

  flattenLandmarks(results) {
    // 543 landmarks in total (Pose: 33, Face: 468, LeftHand: 21, RightHand: 21)
    // Format required for LSTM: [33*4 + 468*3 + 21*3 + 21*3] = 1662 coordinates
    // We'll flatten x,y,z (and visibility for pose if needed)
    
    const frameData = [];
    
    // 1. Pose Landmarks (33 * 4 = 132)
    if (results.poseLandmarks && results.poseLandmarks.length > 0) {
      results.poseLandmarks[0].forEach(l => {
        frameData.push(l.x, l.y, l.z, l.visibility || 0);
      });
    } else {
      for (let i = 0; i < 33 * 4; i++) frameData.push(0);
    }
    
    // 2. Face Landmarks (468 * 3 = 1404)
    if (results.faceLandmarks && results.faceLandmarks.length > 0) {
      results.faceLandmarks[0].slice(0, 468).forEach(l => {
        frameData.push(l.x, l.y, l.z);
      });
    } else {
      for (let i = 0; i < 468 * 3; i++) frameData.push(0);
    }
    
    // 3. Left Hand (21 * 3 = 63)
    if (results.leftHandLandmarks && results.leftHandLandmarks.length > 0) {
      results.leftHandLandmarks[0].forEach(l => {
        frameData.push(l.x, l.y, l.z);
      });
    } else {
      for (let i = 0; i < 21 * 3; i++) frameData.push(0);
    }
    
    // 4. Right Hand (21 * 3 = 63)
    if (results.rightHandLandmarks && results.rightHandLandmarks.length > 0) {
      results.rightHandLandmarks[0].forEach(l => {
        frameData.push(l.x, l.y, l.z);
      });
    } else {
      for (let i = 0; i < 21 * 3; i++) frameData.push(0);
    }
    
    return frameData;
  }
}
