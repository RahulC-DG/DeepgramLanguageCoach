let socket;
let mediaRecorder;
let audioContext;
let isRecording = false;
let isConnected = false;
let audioQueue = [];
let isPlaying = false;
let selectedLanguage = 'english';
let selectedMode = 'conversation';

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.querySelector('.status');
const conversation = document.querySelector('.conversation');
const languageBtns = document.querySelectorAll('.language-btn');
const modeBtns = document.querySelectorAll('.mode-btn');
const visualizer = document.querySelector('.visualizer');

// Initialize Socket.IO connection
function initSocket() {
    if (socket) {
        socket.close();
    }

    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
        isConnected = true;
        updateStatus('Connected to server');
        // Emit start_listening event to initialize Deepgram
        socket.emit('start_listening');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isConnected = false;
        isRecording = false;
        stopStreaming();
        updateStatus('Disconnected from server');
    });

    socket.on('error', (data) => {
        console.error('Error:', data);
        showError(data.data.message);
    });

    socket.on('conversation', (data) => {
        console.log('Conversation:', data);
        appendMessage(data.data);
    });

    socket.on('thinking', (data) => {
        console.log('Thinking:', data);
    });

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
}

// Initialize audio context and streaming
async function initAudio() {
    try {
        audioContext = new AudioContext({
            sampleRate: 16000
        });

        const constraints = {
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(2048, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        let lastSendTime = 0;
        const sendInterval = 100;

        processor.onaudioprocess = (e) => {
            const now = Date.now();
            if (socket?.connected && isRecording && now - lastSendTime >= sendInterval) {
                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = convertFloatToPcm(inputData);
                socket.emit('audio_data', pcmData);
                lastSendTime = now;
            }
        };

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

// Start audio streaming
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

// Stop audio streaming
function stopStreaming() {
    audioQueue = [];
    isPlaying = false;
    if (processor) {
        processor.disconnect();
        processor = null;
    }
    if (mediaRecorder) {
        mediaRecorder.getTracks().forEach(track => track.stop());
        mediaRecorder = null;
    }
    startBtn.disabled = false;
    stopBtn.disabled = true;
    updateStatus('Stopped listening');
    visualizer.classList.remove('active');
}

// Convert Float32Array to Int16Array
function convertFloatToPcm(floatData) {
    const pcmData = new Int16Array(floatData.length);
    for (let i = 0; i < floatData.length; i++) {
        const s = Math.max(-1, Math.min(1, floatData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcmData;
}

// Play audio from queue
async function playNextInQueue() {
    if (audioQueue.length === 0) {
        isPlaying = false;
        return;
    }

    isPlaying = true;
    const audioData = audioQueue.shift();

    try {
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        const buffer = audioContext.createBuffer(1, audioData.length, 24000);
        const channelData = buffer.getChannelData(0);

        for (let i = 0; i < audioData.length; i++) {
            channelData[i] = audioData[i] / 32768.0;
        }

        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.onended = () => playNextInQueue();
        source.start(0);
    } catch (error) {
        console.error('Error playing audio:', error);
        isPlaying = false;
        playNextInQueue();
    }
}

// Add message to conversation
function appendMessage(data) {
    const message = document.createElement('div');
    message.className = `message ${data.role}`;
    message.textContent = data.content;
    conversation.appendChild(message);
    conversation.scrollTop = conversation.scrollHeight;
}

// Update status message
function updateStatus(text) {
    status.textContent = text;
}

// Handle language selection
languageBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        languageBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedLanguage = btn.dataset.lang;
        updateStatus(`Selected language: ${selectedLanguage}`);
    });
});

// Handle mode selection
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedMode = btn.dataset.mode;
        updateStatus(`Selected mode: ${selectedMode}`);
    });
});

// Event Listeners
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

stopBtn.addEventListener('click', () => {
    stopStreaming();
});

// Clean up when the page is closed
window.onbeforeunload = () => {
    stopStreaming();
    if (socket) {
        socket.close();
    }
};

function showError(message) {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
} 