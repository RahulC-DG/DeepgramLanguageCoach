# DeepgramCoach - AI Language Learning Partner

**DeepgramCoach** is an interactive AI-powered language learning application that provides real-time voice-based language practice. Using Deepgram's advanced Voice Agent API, this application offers personalized conversation practice and pronunciation coaching across multiple languages.

## 🌟 What is DeepgramCoach?

DeepgramCoach is your personal AI language tutor that helps you:

- **Practice Conversations**: Engage in natural, flowing conversations in your target language
- **Improve Pronunciation**: Get real-time feedback on your pronunciation and speaking clarity
- **Learn Multiple Languages**: Support for 13+ languages including English, Spanish, French, German, Japanese, Chinese, and more
- **Adaptive Learning**: AI adapts to your proficiency level and learning pace
- **Immersive Experience**: Voice-first learning that prioritizes speaking practice

### Key Features

🎯 **Two Learning Modes**:
- **Conversation Practice**: Focus on fluency, vocabulary, and natural communication
- **Pronunciation Practice**: Detailed feedback on accent, clarity, and pronunciation accuracy

🌍 **Multi-Language Support**:
- English, Spanish, French, German, Italian, Portuguese
- Japanese, Korean, Chinese (Mandarin), Russian
- Dutch, Hindi, Arabic
- Automatic language detection and voice adaptation

🤖 **AI-Powered Coaching**:
- GPT-4o-mini powered conversation engine
- Deepgram's Nova-3 speech recognition
- Aura-2 text-to-speech with native speaker voices
- Contextual grammar correction and vocabulary expansion

💻 **Modern Web Interface**:
- Real-time voice interaction
- Visual audio feedback
- Conversation history
- Responsive design for desktop and mobile

## 🚀 Technology Stack

- **Backend**: Flask with Flask-SocketIO for real-time communication
- **AI Services**: Deepgram Voice Agent API (Speech-to-Text, Text-to-Speech, AI Conversation)
- **Frontend**: Vanilla JavaScript with Web Audio API
- **Styling**: Modern CSS with responsive design
- **Testing**: pytest for comprehensive test coverage

## 📋 Prerequisites

Before installing DeepgramCoach, ensure you have:

- **Python 3.8 or higher** installed
- **Modern web browser** with microphone support (Chrome, Firefox, Safari, Edge)
- **Deepgram API key** (sign up at [deepgram.com](https://deepgram.com) for free)
- **Active internet connection** for AI services

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Audio**: Working microphone and speakers/headphones
- **Browser**: Chrome 88+, Firefox 85+, Safari 14+, Edge 88+

## 🛠️ Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/deepgram-starters/flask-voice-agent.git
cd flask-voice-agent
```

### Step 2: Set Up Python Environment (Recommended)

Create a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Dependencies:**
- `flask==3.0.2` - Web framework
- `deepgram-sdk==4.0.0` - Deepgram Voice Agent API
- `python-dotenv==1.0.1` - Environment variable management
- `PyAudio==0.2.14` - Audio processing (may require system audio libraries)
- `flask-cors==4.0.0` - Cross-origin resource sharing
- `flask-socketio==5.3.6` - Real-time WebSocket communication
- `pytest==8.0.0` - Testing framework

### Step 4: Set Up Environment Variables

1. Create a `.env` file in the project root:

```bash
touch .env
```

2. Add your Deepgram API key to the `.env` file:

```bash
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

**Getting a Deepgram API Key:**
1. Visit [console.deepgram.com](https://console.deepgram.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

### Step 5: Handle PyAudio Installation (if needed)

PyAudio may require additional system dependencies:

**On macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**On Windows:**
PyAudio should install automatically with pip. If you encounter issues:
```bash
pip install pipwin
pipwin install pyaudio
```

## 🏃‍♂️ Running the Application

### Start the Development Server

```bash
python app.py
```

The application will start on `http://localhost:3000`

### Using the Application

1. **Open your browser** and navigate to `http://localhost:3000`
2. **Allow microphone access** when prompted by your browser
3. **Select your target language** using the language buttons or by speaking (e.g., "I want to practice Spanish")
4. **Choose your learning mode**:
   - "I want to practice conversation" for fluency training
   - "Let's work on pronunciation" for pronunciation coaching
5. **Click "Start Speaking"** to begin your language learning session
6. **Start talking!** The AI will respond in real-time and adapt to your level

### Sample Conversation Starters

- "Hello, I'm learning [language]. Can we have a conversation about daily activities?"
- "I'd like to practice ordering food in a restaurant."
- "Can you help me with pronunciation of difficult words?"
- "Let's talk about travel and culture."

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest -v

# Run specific test file
pytest -v test_app.py

# Run with coverage report
pip install pytest-cov
pytest --cov=app test_app.py
```

**Test Coverage:**
- Flask application initialization
- WebSocket connection establishment
- Deepgram agent configuration
- Audio data handling
- Error handling and edge cases
- Static file serving

## 🐛 Troubleshooting

### Common Issues

**1. Microphone Access Denied**
- Ensure your browser has microphone permissions
- Check system privacy settings
- Try refreshing the page and allowing access again

**2. API Key Errors**
```
WARNING: DEEPGRAM_API_KEY not found in environment variables!
```
- Verify your `.env` file exists in the project root
- Check that your API key is correctly formatted
- Ensure no extra spaces or quotes around the key

**3. PyAudio Installation Issues**
- Install system audio libraries (see installation section)
- Try using conda instead of pip: `conda install pyaudio`
- On some systems, use: `pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio`

**4. WebSocket Connection Errors**
- Check your internet connection
- Verify firewall settings allow WebSocket connections
- Ensure port 3000 is available

**5. Audio Playback Issues**
- Check system audio settings
- Try different browsers
- Ensure speakers/headphones are working
- Check browser audio permissions

### Getting Debug Information

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export FLASK_DEBUG=1
python app.py
```

## 🔧 Configuration Options

### Environment Variables

Create additional configuration in your `.env` file:

```bash
# Required
DEEPGRAM_API_KEY=your_api_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=1
HOST=0.0.0.0
PORT=3000
```

### Customizing the AI Coach

Modify the AI prompt in `app.py` around line 140 to customize the learning experience:

```python
options.agent.think.prompt = "Your custom coaching instructions here..."
```

## 📚 Project Structure

```
DeepgramLanguageCoach/
├── app.py                 # Main Flask application with Deepgram integration
├── test_app.py           # Comprehensive test suite
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── README.md            # This documentation
├── templates/
│   └── index.html       # Main application interface
├── static/
│   ├── css/
│   │   └── style.css    # Application styling
│   └── js/
│       └── app.js       # Client-side JavaScript
└── .gitignore           # Git ignore file
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code style and standards
- Pull request process
- Issue reporting
- Feature requests

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🆘 Support & Community

- **Issues**: [GitHub Issues](https://github.com/deepgram-starters/flask-voice-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/orgs/deepgram/discussions)
- **Discord**: [Deepgram Community](https://discord.gg/xWRaCDBtW4)
- **Documentation**: [Deepgram Docs](https://developers.deepgram.com)

## 🏆 About Deepgram

[Deepgram](https://deepgram.com) is the AI speech platform providing real-time speech-to-text, text-to-speech, and voice AI solutions. Over 200,000+ developers use Deepgram to build voice AI products and features.

**Why Deepgram?**
- Industry-leading accuracy and speed
- Support for 30+ languages
- Real-time and batch processing
- Easy-to-use APIs
- Comprehensive documentation and support

---

Ready to master a new language? Start your journey with DeepgramCoach today! 🎯🗣️
