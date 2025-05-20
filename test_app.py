import pytest
from app import app, socketio, dg_connection
from flask_socketio import SocketIO
import threading
import time
import os
from unittest.mock import Mock, patch

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def socket_client(client):
    """Create a Socket.IO test client."""
    return socketio.test_client(app)

def test_server_starts_successfully(client):
    """Test that the server starts successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Deepgram Voice Agent' in response.data

@patch('app.DeepgramClient')
def test_websocket_connection(mock_deepgram_client, socket_client):
    """Test that WebSocket connection is established."""
    # Set up the mock
    mock_instance = mock_deepgram_client.return_value
    mock_agent = Mock()
    mock_instance.agent = mock_agent
    mock_websocket = Mock()
    mock_agent.websocket = mock_websocket
    mock_websocket.v.return_value = Mock()

    # Clear any existing received messages
    socket_client.get_received()

    # Trigger a connection
    socket_client.emit('connect')

    # Wait for and verify the open event
    received = socket_client.get_received()
    assert len(received) > 0
    assert received[0]['name'] == 'open'

    # Simulate the welcome event from Deepgram by emitting it through socketio
    welcome_data = {'request_id': 'test-request-id'}
    socketio.emit('welcome', {'data': welcome_data})

    # Wait a bit for the welcome event to be processed
    time.sleep(0.5)

    # Get all received messages
    all_received = socket_client.get_received()

    # Find the welcome message
    welcome_messages = [msg for msg in all_received if msg['name'] == 'welcome']
    assert len(welcome_messages) > 0, "No welcome message received"
    assert 'request_id' in welcome_messages[0]['args'][0]['data']

def test_deepgram_agent_creation(socket_client):
    """Test that Deepgram agent is created when WebSocket connects."""
    # Clear any existing received messages
    socket_client.get_received()

    # Trigger a connection
    socket_client.emit('connect')

    # Wait for the connection to be processed
    time.sleep(0.5)

    # Verify we get the open event
    received = socket_client.get_received()
    assert len(received) > 0, "No events received after connection"
    assert received[0]['name'] == 'open', "Open event not received"

    # Verify the connection is active
    assert socket_client.is_connected(), "Socket connection not active"

    # Verify the Deepgram connection exists and is configured
    assert dg_connection is not None, "Deepgram connection not created"
    assert hasattr(dg_connection, 'on'), "Deepgram connection not properly initialized"
    assert hasattr(dg_connection, 'start'), "Deepgram connection not properly initialized"

def test_handle_audio_data(socket_client):
    """Test handling of audio data from client."""
    # Create mock audio data (16-bit PCM)
    mock_audio_data = bytes([0] * 1024)  # 1KB of silence

    # Send audio data
    socket_client.emit('audio_data', mock_audio_data)
    time.sleep(0.1)  # Give time for processing

    # Verify the audio data was sent to Deepgram
    # Note: This is a basic test. In a real scenario, you'd want to mock
    # the Deepgram connection and verify it received the data
    assert dg_connection is not None

if __name__ == '__main__':
    pytest.main(['-v'])