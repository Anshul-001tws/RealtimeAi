# Live AI Voice Chat with WebSocket

Real-time voice chatbot powered by Google Gemini AI with bidirectional WebSocket streaming.

## Features

✅ **Real-time Audio Streaming** - Continuous bidirectional audio communication  
✅ **WebSocket Architecture** - Low-latency real-time data exchange  
✅ **Audio Visualization** - Live waveform display during recording  
✅ **Modern UI** - Beautiful gradient design with smooth animations  
✅ **Gemini Integration** - Powered by Gemini 2.5 Flash Native Audio model  
✅ **Auto Format Conversion** - Automatic WebM to PCM conversion for AI processing

## Architecture

This project converts the API-based chatbot from `backup.py` to a real-time WebSocket implementation:

- **Backend**: FastAPI with WebSocket support
- **AI Model**: Gemini 2.5 Flash Native Audio Preview
- **Audio Processing**: Pydub for format conversion (WebM → PCM)
- **Frontend**: Vanilla JavaScript with MediaRecorder API
- **Communication**: Bidirectional WebSocket streaming

## Installation

1. **Install dependencies**:
```bash
cd /home/pankaj/Desktop/LiveChatBotWebSocket
pip install -r requirements.txt
```

2. **Install system dependencies** (for audio processing):
```bash
# On Ubuntu/Debian
sudo apt-get install ffmpeg

# On macOS
brew install ffmpeg
```

## Usage

1. **Start the server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Open your browser**:
```
http://localhost:8000
```

3. **Start chatting**:
   - Click "Start Recording" and speak
   - The AI will respond with voice
   - Click "Stop Recording" when done
   - Continue the conversation naturally

## How It Works

### Real-time Audio Flow

1. **Client → Server**:
   - Browser captures audio via MediaRecorder (WebM/Opus format)
   - Audio chunks sent to server every 100ms via WebSocket
   - Server converts WebM to PCM (16kHz, mono, 16-bit)
   - PCM audio forwarded to Gemini Live API

2. **Server → Client**:
   - Gemini generates audio response (PCM 24kHz)
   - Server streams audio chunks back via WebSocket
   - Client decodes and plays audio in real-time

### Key Components

- **`main.py`**: FastAPI WebSocket server with Gemini integration
- **`audio_utils.py`**: Audio format conversion utilities
- **`static/index.html`**: Interactive frontend with recording controls
- **`requirements.txt`**: Python dependencies

## API Endpoints

- **GET `/`**: Serve the main HTML interface
- **WebSocket `/ws/audio`**: Real-time bidirectional audio streaming

## WebSocket Message Format

### Client → Server
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_webm_audio"
}
```

```json
{
  "type": "audio_end"
}
```

### Server → Client
```json
{
  "type": "audio",
  "data": "base64_encoded_pcm_audio",
  "mime_type": "audio/pcm"
}
```

```json
{
  "type": "status",
  "message": "Connection status"
}
```

## Configuration

The Gemini configuration in `main.py`:
- **Model**: `gemini-2.5-flash-native-audio-preview-12-2025`
- **Voice**: Zephyr (prebuilt voice)
- **Response Mode**: Audio only
- **Sample Rate**: 16kHz input, 24kHz output

## Differences from backup.py

| Feature | backup.py (API) | This Project (WebSocket) |
|---------|-----------------|--------------------------|
| Communication | HTTP POST requests | WebSocket streaming |
| Audio Flow | Upload → Wait → Download | Real-time bidirectional |
| Latency | High (full audio required) | Low (streaming chunks) |
| User Experience | Upload & wait | Continuous conversation |
| Format | File upload | Live recording |

## Troubleshooting

**Microphone not working?**
- Ensure HTTPS or localhost (required for microphone access)
- Check browser permissions for microphone access

**No audio response?**
- Check browser console for errors
- Verify ffmpeg is installed for audio conversion
- Check Gemini API key is valid

**WebSocket connection failed?**
- Ensure server is running on port 8000
- Check firewall settings

## Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, Edge)
- Microphone access
- ffmpeg (for audio conversion)

## License

This project uses the same functionality as backup.py, adapted for real-time WebSocket streaming.
