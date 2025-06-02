/**
 * DeepgramCoach - Client-Side JavaScript Application
 * 
 * This file handles the frontend functionality for the DeepgramCoach language learning app.
 * It manages real-time audio communication with the Flask backend via WebSocket,
 * user interface interactions, and audio processing for voice-based learning.
 * 
 * Main Features:
 * - WebSocket communication with Flask-SocketIO backend
 * - Real-time audio capture and streaming
 * - Audio playback for AI responses
 * - Language and mode selection interface
 * - Visual feedback and conversation display
 * 
 * Dependencies:
 * - Socket.IO client library for WebSocket communication
 * - Web Audio API for audio processing
 * - MediaDevices API for microphone access
 * 
 * Author: Deepgram
 * License: MIT
 */

// Global variables for application state
let socket;                 // Socket.IO connection instance
let mediaRecorder;         // MediaRecorder for audio capture
let audioContext;          // Web Audio API context
let isRecording = false;   // Recording state flag
let isConnected = false;   // Connection state flag
let audioQueue = [];       // Queue for AI audio responses
let isPlaying = false;     // Audio playback state flag
let selectedLanguage = 'english';      // Currently selected language
let selectedMode = 'conversation';     // Currently selected learning mode

// DOM Elements - Cache frequently accessed elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.querySelector('.status');
const conversation = document.querySelector('.conversation');
const languageBtns = document.querySelectorAll('.language-btn');
const modeBtns = document.querySelectorAll('.mode-btn');
const visualizer = document.querySelector('.visualizer');

/**
 * Initialize Socket.IO connection and set up event handlers.
 * 
 * This function establishes the WebSocket connection to the Flask backend
 * and registers all necessary event handlers for real-time communication.
 */
function initSocket() {
    // Close existing connection if present
    if (socket) {
        socket.close();
    }

    // Create new Socket.IO connection
    socket = io();
    
    // Handle successful connection
    socket.on('connect', () => {
        console.log('Connected to server');
        isConnected = true;
        updateStatus('Connected to server');
        // Emit start_listening event to initialize Deepgram
        socket.emit('start_listening');
    });

    // Handle disconnection
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isConnected = false;
        isRecording = false;
        stopStreaming();
        updateStatus('Disconnected from server');
    });

    // Handle error events from backend
    socket.on('error', (data) => {
        console.error('Error:', data);
        showError(data.data.message);
    });

    // Handle conversation events (transcribed text and AI responses)
    socket.on('conversation', (data) => {
        console.log('Conversation:', data);
        appendMessage(data.data);
    });

    // Handle thinking events (AI is processing response)
    socket.on('thinking', (data) => {
        console.log('Thinking:', data);
    });

    // Handle agent speaking events (AI audio response)
    socket.on('agent_speaking', (data) => {
        console.log('Agent speaking:', data);
        if (data.audio) {
            const audioData = new Int16Array(data.audio);
            audioQueue.push(audioData);
            if (!isPlaying) {
                playNextInQueue();
            }
        }
    });

    // Listen for backend events to select language dynamically
    socket.on('select_language', (data) => {
        const lang = data.language.toLowerCase();
        languageBtns.forEach(btn => {
            if (btn.dataset.lang === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        selectedLanguage = lang;
        updateStatus(`Selected language: ${selectedLanguage}`);
    });

    // Listen for backend events to select mode dynamically
    socket.on('select_mode', (data) => {
        const mode = data.mode;
        modeBtns.forEach(btn => {
            if (btn.dataset.mode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        selectedMode = mode;
        updateStatus(`Selected mode: ${selectedMode}`);
    });
}

/**
 * Initialize audio context and start streaming audio to the backend.
 * 
 * This function sets up the Web Audio API, requests microphone access,
 * and begins streaming audio data to the Flask backend for processing.
 */
async function initAudio() {
    try {
        // Create audio context with 16kHz sample rate (optimal for speech)
        audioContext = new AudioContext({
            sampleRate: 16000
        });

        // Define microphone constraints for optimal speech recognition
        const constraints = {
            audio: {
                channelCount: 1,        // Mono audio
                sampleRate: 16000,      // 16kHz sample rate
                echoCancellation: true, // Reduce echo
                noiseSuppression: true, // Reduce background noise
                autoGainControl: true   // Automatic volume adjustment
            }
        };

        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(2048, 1, 1);

        // Connect audio processing chain
        source.connect(processor);
        processor.connect(audioContext.destination);

        // Audio processing variables
        let lastSendTime = 0;
        const sendInterval = 100; // Send audio data every 100ms

        // Process audio data in real-time
        processor.onaudioprocess = (e) => {
            const now = Date.now();
            // Throttle audio data sending to avoid overwhelming the backend
            if (socket?.connected && isRecording && now - lastSendTime >= sendInterval) {
                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = convertFloatToPcm(inputData);
                socket.emit('audio_data', pcmData);
                lastSendTime = now;
            }
        };

        // Update UI state
        startBtn.disabled = true;
        stopBtn.disabled = false;
        updateStatus('Listening...');
        visualizer.classList.add('active');
        isRecording = true;
    } catch (error) {
        console.error('Error initializing audio:', error);
        updateStatus('Error accessing microphone');
        showError('Failed to access microphone');
    }
}

/**
 * Start audio streaming (legacy function for compatibility).
 * 
 * This function maintains compatibility with older versions but
 * the main audio streaming logic is now in initAudio().
 */
function startStreaming() {
    if (!mediaRecorder || !isConnected) return;

    try {
        const source = audioContext.createMediaStreamSource(mediaRecorder);
        const processor = audioContext.createScriptProcessor(2048, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        let lastSendTime = 0;
        const sendInterval = 100;

        processor.onaudioprocess = (e) => {
            const now = Date.now();
            if (socket?.connected && now - lastSendTime >= sendInterval) {
                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = convertFloatToPcm(inputData);
                socket.emit('audio_data', pcmData, { binary: true });
                lastSendTime = now;
            }
        };

        startBtn.disabled = true;
        stopBtn.disabled = false;
        updateStatus('Listening...');
        visualizer.classList.add('active');
    } catch (error) {
        console.error('Error starting audio stream:', error);
        updateStatus('Error starting audio stream');
    }
}

/**
 * Stop audio streaming and clean up resources.
 * 
 * This function stops audio capture, cleans up audio resources,
 * and updates the UI to reflect the stopped state.
 */
function stopStreaming() {
    // Clear audio queue and playback state
    audioQueue = [];
    isPlaying = false;
    
    // Clean up audio processor
    if (processor) {
        processor.disconnect();
        processor = null;
    }
    
    // Stop media recorder tracks
    if (mediaRecorder) {
        mediaRecorder.getTracks().forEach(track => track.stop());
        mediaRecorder = null;
    }
    
    // Update UI state
    startBtn.disabled = false;
    stopBtn.disabled = true;
    updateStatus('Stopped listening');
    visualizer.classList.remove('active');
}

/**
 * Convert Float32Array audio data to Int16Array PCM format.
 * 
 * This function converts the Web Audio API's floating-point audio data
 * to 16-bit PCM format required by the Deepgram API.
 * 
 * @param {Float32Array} floatData - Input audio data in floating-point format
 * @returns {Int16Array} - Output audio data in 16-bit PCM format
 */
function convertFloatToPcm(floatData) {
    const pcmData = new Int16Array(floatData.length);
    // Convert floating-point values (-1.0 to 1.0) to 16-bit integers
    for (let i = 0; i < floatData.length; i++) {
        // Clamp values to valid range and convert to 16-bit PCM
        const s = Math.max(-1, Math.min(1, floatData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcmData;
}

/**
 * Play the next audio response from the queue.
 * 
 * This function processes the AI's audio responses sequentially,
 * converting them from PCM data to playable audio buffers.
 */
async function playNextInQueue() {
    // Check if queue is empty
    if (audioQueue.length === 0) {
        isPlaying = false;
        return;
    }

    isPlaying = true;
    const audioData = audioQueue.shift(); // Get next audio data

    try {
        // Resume audio context if suspended (required by some browsers)
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        // Create audio buffer from PCM data
        const buffer = audioContext.createBuffer(1, audioData.length, 24000);
        const channelData = buffer.getChannelData(0);

        // Convert Int16Array to Float32Array for Web Audio API
        for (let i = 0; i < audioData.length; i++) {
            channelData[i] = audioData[i] / 32768.0; // Normalize to -1.0 to 1.0 range
        }

        // Create and configure audio source
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        
        // Set up callback to play next audio when current finishes
        source.onended = () => playNextInQueue();
        source.start(0);
    } catch (error) {
        console.error('Error playing audio:', error);
        isPlaying = false;
        playNextInQueue(); // Continue with next audio despite error
    }
}

/**
 * Add a new message to the conversation display.
 * 
 * @param {Object} data - Message data containing role and content
 * @param {string} data.role - Message sender ('user' or 'assistant')
 * @param {string} data.content - Message text content
 */
function appendMessage(data) {
    const message = document.createElement('div');
    message.className = `message ${data.role}`;
    message.textContent = data.content;
    conversation.appendChild(message);
    // Auto-scroll to show latest message
    conversation.scrollTop = conversation.scrollHeight;
}

/**
 * Update the status display with current application state.
 * 
 * @param {string} text - Status message to display
 */
function updateStatus(text) {
    status.textContent = text;
}

/**
 * Handle language selection button clicks.
 * Updates the UI state and notifies the user of the selected language.
 */
languageBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all language buttons
        languageBtns.forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');
        // Update selected language
        selectedLanguage = btn.dataset.lang;
        updateStatus(`Selected language: ${selectedLanguage}`);
    });
});

/**
 * Handle learning mode selection button clicks.
 * Updates the UI state and notifies the user of the selected mode.
 */
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all mode buttons
        modeBtns.forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');
        // Update selected mode
        selectedMode = btn.dataset.mode;
        updateStatus(`Selected mode: ${selectedMode}`);
    });
});

/**
 * Handle start button click - Begin voice interaction.
 * Establishes connection and starts audio capture if needed.
 */
startBtn.addEventListener('click', async () => {
    if (!socket || !isConnected) {
        updateStatus('Connecting...');
        initSocket();
        // Wait for connection before starting audio
        socket.once('connect', () => {
            initAudio();
        });
    } else {
        initAudio();
    }
});

/**
 * Handle stop button click - End voice interaction.
 * Stops audio capture and cleans up resources.
 */
stopBtn.addEventListener('click', () => {
    stopStreaming();
});

/**
 * Clean up resources when the page is about to be unloaded.
 * Prevents resource leaks and connection issues.
 */
window.onbeforeunload = () => {
    stopStreaming();
    if (socket) {
        socket.close();
    }
};

/**
 * Display error messages to the user.
 * 
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        // Auto-hide error message after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DeepgramCoach application initialized');
    updateStatus('Click "Start Speaking" to begin your language practice');
}); 