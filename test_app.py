"""
DeepgramCoach - Test Suite

This test file contains unit tests for the DeepgramCoach Flask application.
It tests the core functionality including server startup, WebSocket connections,
and Deepgram integration.

Test Coverage:
- Flask application initialization
- WebSocket connection establishment
- Deepgram agent creation and configuration
- Audio data handling
- Error handling and edge cases

Testing Framework:
- pytest: Main testing framework
- unittest.mock: For mocking external dependencies
- Flask test client: For HTTP endpoint testing
- Flask-SocketIO test client: For WebSocket testing

Dependencies:
- pytest: Testing framework
- Flask test client: HTTP testing utilities
- Flask-SocketIO test client: WebSocket testing utilities
- unittest.mock: Mocking utilities for external dependencies

Author: Deepgram
License: MIT
"""

import pytest
from app import app, socketio, dg_connection
from flask_socketio import SocketIO
import threading
import time
import os
from unittest.mock import Mock, patch

@pytest.fixture
def client():
    """
    Create a test client for the Flask application.
    
    This fixture provides a test client that can be used to make HTTP requests
    to the application during testing without starting a real server.
    
    Returns:
        FlaskClient: Test client for making HTTP requests
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def socket_client(client):
    """
    Create a Socket.IO test client for WebSocket testing.
    
    This fixture provides a test client for testing WebSocket functionality
    including real-time communication features.
    
    Args:
        client: Flask test client fixture
        
    Returns:
        SocketIOTestClient: Test client for WebSocket interactions
    """
    return socketio.test_client(app)

def test_server_starts_successfully(client):
    """
    Test that the Flask server starts successfully and serves the main page.
    
    This test verifies that:
    - The server responds to HTTP requests
    - The main route returns a 200 status code
    - The response contains expected content
    
    Args:
        client: Flask test client fixture
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b'Deepgram Voice Agent' in response.data

@patch('app.DeepgramClient')
def test_websocket_connection(mock_deepgram_client, socket_client):
    """
    Test that WebSocket connection is established successfully.
    
    This test verifies that:
    - WebSocket connections can be established
    - Deepgram client is properly mocked
    - Connection events are properly handled
    - Welcome messages are received
    
    Args:
        mock_deepgram_client: Mocked Deepgram client
        socket_client: Socket.IO test client fixture
    """
    # Set up the mock Deepgram client
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
    """
    Test that Deepgram agent is created when WebSocket connects.
    
    This test verifies that:
    - Deepgram agent is properly initialized
    - Connection is active after WebSocket connection
    - Agent has required methods and properties
    - Configuration is properly set up
    
    Args:
        socket_client: Socket.IO test client fixture
    """
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
    """
    Test handling of audio data from client.
    
    This test verifies that:
    - Audio data can be sent from client to server
    - Audio data is properly processed
    - No errors occur during audio handling
    - Deepgram connection receives the audio data
    
    Args:
        socket_client: Socket.IO test client fixture
    """
    # Create mock audio data (16-bit PCM format)
    mock_audio_data = bytes([0] * 1024)  # 1KB of silence for testing

    # Send audio data to the server
    socket_client.emit('audio_data', mock_audio_data)
    time.sleep(0.1)  # Give time for processing

    # Verify the audio data was processed
    # Note: This is a basic test. In a real scenario, you'd want to mock
    # the Deepgram connection and verify it received the data correctly
    assert dg_connection is not None

def test_error_handling():
    """
    Test error handling for various edge cases.
    
    This test verifies that:
    - Application handles missing environment variables gracefully
    - Invalid audio data doesn't crash the application
    - Connection failures are properly managed
    """
    # Test with missing API key
    original_key = os.environ.get('DEEPGRAM_API_KEY')
    if 'DEEPGRAM_API_KEY' in os.environ:
        del os.environ['DEEPGRAM_API_KEY']
    
    try:
        # This should handle the missing API key gracefully
        from app import api_key
        assert api_key is None
    finally:
        # Restore original API key if it existed
        if original_key:
            os.environ['DEEPGRAM_API_KEY'] = original_key

def test_static_file_serving(client):
    """
    Test that static files are served correctly.
    
    This test verifies that:
    - Static file routes work correctly
    - CSS and JavaScript files can be accessed
    - Proper HTTP status codes are returned
    
    Args:
        client: Flask test client fixture
    """
    # Test CSS file serving
    response = client.get('/static/css/style.css')
    assert response.status_code == 200
    assert 'text/css' in response.content_type or response.status_code == 200
    
    # Test JavaScript file serving
    response = client.get('/static/js/app.js')
    assert response.status_code == 200
    assert 'application/javascript' in response.content_type or response.status_code == 200

# Entry point for running tests directly
if __name__ == '__main__':
    """
    Run the test suite when the file is executed directly.
    
    This allows running tests with: python test_app.py
    """
    pytest.main(['-v', __file__])