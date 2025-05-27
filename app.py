from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    AgentWebSocketEvents,
    SettingsOptions,
    FunctionCallRequest,
    FunctionCallResponse,
    Input,
    Output,
)
import os
import json
from dotenv import load_dotenv
load_dotenv()

# Add debug prints for environment variables
api_key = os.getenv("DEEPGRAM_API_KEY")
if not api_key:
    print("WARNING: DEEPGRAM_API_KEY not found in environment variables!")
    print("Please make sure your .env file exists and contains DEEPGRAM_API_KEY=your_key_here")
else:
    print("DEEPGRAM_API_KEY found in environment variables")
    print(f"API Key length: {len(api_key)} characters")

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*", path='/socket.io')

# Initialize Deepgram client
config = DeepgramClientOptions(
    options={
        "keepalive": "true",
        "microphone_record": "true",
        "speaker_playback": "true",
    }
)

try:
    deepgram = DeepgramClient(api_key, config)
    print("Successfully initialized Deepgram client")
except Exception as e:
    print(f"Error initializing Deepgram client: {str(e)}")
    raise

dg_connection = deepgram.agent.websocket.v("1")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Don't initialize Deepgram here anymore
    return

@socketio.on('start_listening')
def handle_start_listening():
    print("Starting Deepgram connection...")
    options = SettingsOptions()

    # Configure audio input settings
    options.audio.input = Input(
        encoding="linear16",
        sample_rate=16000
    )

    # Configure audio output settings
    options.audio.output = Output(
        encoding="linear16",
        sample_rate=16000,
        container="none"
    )

    # LLM provider configuration
    options.agent.think.provider.type = "open_ai"
    options.agent.think.provider.model = "gpt-4o-mini"
    options.agent.think.prompt = (
        "You are DeepgramCoach, a highly versatile, friendly, and patient AI language learning partner. "
        "Your core mission is to help the user master spoken language, focusing on both conversational fluency and precise pronunciation. "
        "You will adapt your interaction style based on the user's chosen mode.\n\n"
        
        "Core Principles:\n"
        "- Immersive First: Prioritize speaking in the user's target language unless explicitly asked for clarification\n"
        "- Encouraging & Patient: Maintain a positive and supportive learning environment\n"
        "- Adaptive & Responsive: Adjust your pace, vocabulary, and complexity to the user's proficiency\n"
        "- No Technical Jargon: Do not mention LLMs, Deepgram, APIs, or model names\n"
        "- Safety & Ethics: Do not engage in harmful or inappropriate conversations\n\n"
        
        "Modes of Operation:\n"
        "1. Conversational Fluency Practice (Default):\n"
        "   - Enhance conversational skills and vocabulary\n"
        "   - Gently correct grammatical errors by rephrasing\n"
        "   - Introduce new vocabulary naturally\n"
        "   - Keep responses concise (1-2 sentences)\n\n"
        
        "2. Repetition & Pronunciation Practice:\n"
        "   - Activated when user requests pronunciation practice\n"
        "   - Provide clear, actionable feedback on pronunciation\n"
        "   - Break down complex phrases when needed\n"
        "   - Celebrate progress and offer specific improvement tips\n\n"
        
        "Remember:\n"
        "- Keep responses concise (1-2 sentences)\n"
        "- Ask one follow-up question at a time\n"
        "- If a question is unclear, ask for clarification\n"
        "- All responses will be spoken aloud through the voice interface"
    )

    # Deepgram provider configuration
    options.agent.listen.provider.keyterms = ["hello", "goodbye", "practice", "pronunciation", "fluency", "language", "switch", "change"]
    options.agent.listen.provider.model = "nova-3"
    options.agent.listen.provider.type = "deepgram"
    
    # Configure language-specific settings
    options.agent.listen.provider.language = "auto"
    options.agent.listen.provider.model_config = {
        "language": "auto",
        "detect_language": True,
        "punctuate": True,
        "diarize": False,
        "smart_format": True,
        "model": "nova-3",
        "language_detection": {
            "enabled": True,
            "confidence_threshold": 0.7
        }
    }
    
    # Configure TTS with language-specific voices
    options.agent.speak.provider.type = "deepgram"
    options.agent.speak.provider.model = "aura-2"
    options.agent.speak.provider.voice_config = {
        "model": "aura-2",
        "voice": "auto",
        "language": "auto",
        "style": "conversational"
    }

    # Sets Agent greeting
    options.agent.greeting = "Hello! I'm DeepgramCoach, your language learning partner. Which language would you like to practice today, and would you like to work on conversation practice or pronunciation practice?"

    # Function to update voice based on language
    def update_voice_for_language(language):
        voice_mapping = {
            "english": "en-US-Neural2-F",
            "spanish": "es-ES-Neural2-A",
            "french": "fr-FR-Neural2-A",
            "german": "de-DE-Neural2-A",
            "italian": "it-IT-Neural2-A",
            "portuguese": "pt-BR-Neural2-A",
            "japanese": "ja-JP-Neural2-A",
            "korean": "ko-KR-Neural2-A",
            "chinese": "cmn-CN-Neural2-A",
            "russian": "ru-RU-Neural2-A",
            "dutch": "nl-NL-Neural2-A",
            "hindi": "hi-IN-Neural2-A",
            "arabic": "ar-XA-Neural2-A"
        }
        
        # Convert language to lowercase and get the voice
        language_key = language.lower()
        voice = voice_mapping.get(language_key, "en-US-Neural2-F")  # Default to English if language not found
        
        print(f"Switching to {language_key} voice: {voice}")
        
        # Update the voice configuration
        options.agent.speak.provider.voice_config["voice"] = voice
        options.agent.speak.provider.voice_config["language"] = language_key
        
        # Update the connection with new settings
        try:
            dg_connection.update_settings(options)
            print(f"Successfully updated voice settings for {language_key}")
        except Exception as e:
            print(f"Error updating voice settings: {str(e)}")

    # Event handlers
    def on_open(self, open, **kwargs):
        print("Open event received:", open.__dict__)
        socketio.emit('open', {'data': open.__dict__})

    def on_welcome(self, welcome, **kwargs):
        print("Welcome event received:", welcome.__dict__)
        socketio.emit('welcome', {'data': welcome.__dict__})

    def on_conversation_text(self, conversation_text, **kwargs):
        print("\n=== DEBUG: Conversation Text Object ===")
        print("Type:", conversation_text.type)
        print("Role:", conversation_text.role)
        print("Content:", conversation_text.content)
        
        try:
            # Only process user messages
            if conversation_text.role == 'user':
                text = conversation_text.content.lower()
                print(f"\nProcessing user message: {text}")
                
                # Check for explicit language selection
                if any(phrase in text for phrase in ["i want to learn", "let's practice", "switch to", "change to", "i would like to practice"]):
                    print("Found trigger phrase!")
                    for language in ["english", "spanish", "french", "german", "italian", "portuguese", 
                                   "japanese", "korean", "chinese", "russian", "dutch", "hindi", "arabic"]:
                        if language in text:
                            print(f"Found language: {language}")
                            update_voice_for_language(language)
                            socketio.emit('select_language', {'language': language})
                            break
                # Check for mode selection
                if "conversation" in text:
                    socketio.emit('select_mode', {'mode': 'conversation'})
                elif "pronunciation" in text:
                    socketio.emit('select_mode', {'mode': 'pronunciation'})
        
        except Exception as e:
            print(f"Error processing conversation text: {str(e)}")
            print("Full conversation text object:", conversation_text.__dict__)
        
        socketio.emit('conversation', {'data': conversation_text.__dict__})

    def on_agent_thinking(self, agent_thinking, **kwargs):
        print("Thinking event received:", agent_thinking.__dict__)
        socketio.emit('thinking', {'data': agent_thinking.__dict__})

    def on_function_call_request(self, function_call_request: FunctionCallRequest, **kwargs):
        print("Function call event received:", function_call_request.__dict__)
        response = FunctionCallResponse(
            function_call_id=function_call_request.function_call_id,
            output="Function response here"
        )
        dg_connection.send_function_call_response(response)
        socketio.emit('function_call', {'data': function_call_request.__dict__})

    def on_agent_started_speaking(self, agent_started_speaking, **kwargs):
        print("Agent speaking event received:", agent_started_speaking.__dict__)
        socketio.emit('agent_speaking', {'data': agent_started_speaking.__dict__})

    def on_error(self, error, **kwargs):
        print("Error event received:", error.__dict__)
        error_data = {
            'message': str(error),
            'type': error.__class__.__name__,
            'details': error.__dict__
        }
        print("Sending error to client:", error_data)
        socketio.emit('error', {'data': error_data})

    # Register event handlers
    dg_connection.on(AgentWebSocketEvents.Open, on_open)
    dg_connection.on(AgentWebSocketEvents.Welcome, on_welcome)
    dg_connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
    dg_connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
    dg_connection.on(AgentWebSocketEvents.FunctionCallRequest, on_function_call_request)
    dg_connection.on(AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking)
    dg_connection.on(AgentWebSocketEvents.Error, on_error)

    # Initialize Deepgram connection
    if not dg_connection.start(options):
        print("Failed to start Deepgram connection")
        socketio.emit('error', {'data': {'message': 'Failed to start connection'}})
        return False
    
    print("Deepgram connection started successfully")
    return True

@socketio.on('audio_data')
def handle_audio_data(data):
    try:
        if dg_connection:
            print("Received audio data:", len(data), "bytes")
            # Convert to bytes if needed
            if isinstance(data, list):
                data = bytes(data)
            dg_connection.send_audio(data)
        else:
            print("No Deepgram connection available")
            socketio.emit('error', {'data': {'message': 'No Deepgram connection available'}})
    except Exception as e:
        print("Error handling audio data:", str(e))
        socketio.emit('error', {'data': {'message': f'Error handling audio data: {str(e)}'}})

@socketio.on('disconnect')
def handle_disconnect():
    dg_connection.finish()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=3000, host='0.0.0.0')