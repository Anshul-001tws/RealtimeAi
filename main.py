import asyncio
import base64
import json
import traceback
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

from audio_utils import convert_webm_chunk_to_pcm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key="AIzaSyB1Z7P8R6d-9TeQSKGNwlEfUq0_-9OnAv4",
)


# Serve static files
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def render_html():
    """Serve the main HTML page."""
    html_path = Path("static/index.html")
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>index.html not found</h1>"


@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming with Gemini."""
    await websocket.accept()
    print("✓ WebSocket connection established")
    
    session = None
    context_manager = None
    receive_task = None
    gemini_receive_task = None
    
    try:
        # Create config - simplified to avoid serialization issues
        config = {
            "response_modalities": ["AUDIO"],
        }
        
        # Connect to Gemini Live API
        context_manager = client.aio.live.connect(model=MODEL, config=config)
        session = await context_manager.__aenter__()
        print("✓ Connected to Gemini Live API")
        
        # Send initial greeting
        await websocket.send_json({
            "type": "status",
            "message": "Connected to AI. Start speaking!"
        })
        
        async def send_responses_to_client():
            """Continuously receive responses from Gemini and send to client."""
            try:
                while True:
                    async for response in session.receive():
                        # Handle audio responses
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                # Skip thoughts
                                if getattr(part, "thought", False):
                                    continue
                                
                                # Send audio data to client
                                if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                                    audio_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                                    await websocket.send_json({
                                        "type": "audio",
                                        "data": audio_base64,
                                        "mime_type": part.inline_data.mime_type
                                    })
                                    print(f"Sent audio chunk: {len(part.inline_data.data)} bytes")
                                
                                # Send text responses if any
                                if hasattr(part, "text") and part.text:
                                    await websocket.send_json({
                                        "type": "text",
                                        "text": part.text
                                    })
                                    print(f"Response text: {part.text}")
                        
                        # Handle usage metadata
                        if getattr(response, "usage_metadata", None):
                            print(f"Usage metadata: {response.usage_metadata}")
            except Exception as e:
                print(f"Error in Gemini receive loop: {e}")
                traceback.print_exc()
        
        # Start receiving responses from Gemini
        gemini_receive_task = asyncio.create_task(send_responses_to_client())
        
        # Main loop: receive audio from client and send to Gemini
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data["type"] == "audio_chunk":
                    # Decode base64 audio data
                    audio_bytes = base64.b64decode(data["data"])
                    print(f"Received audio chunk: {len(audio_bytes)} bytes")
                    
                    # Send PCM audio directly to Gemini
                    # Use dictionary format which the library handles correctly
                    try:
                        # Send audio chunk as dictionary (library will base64-encode it)
                        await session.send(
                            input={'data': audio_bytes, 'mimeType': 'audio/pcm;rate=16000'}
                        )
                        print(f"Sent to Gemini: {len(audio_bytes)} bytes PCM")
                        
                    except Exception as e:
                        print(f"Error processing audio chunk: {e}")
                        traceback.print_exc()
                        # If session is dead, we must stop processing to trigger reconnection
                        break
                
                elif data["type"] == "audio_end":
                    # Signal end of audio stream
                    print("Audio stream ended by client")
                    await session.send(input=[], end_of_turn=True)
                    
                    await websocket.send_json({
                        "type": "status",
                        "message": "Processing complete"
                    })
                
                elif data["type"] == "image":
                    # Decode base64 image data
                    image_bytes = base64.b64decode(data["data"])
                    
                    # Send image to Gemini
                    try:
                        await session.send(
                            input={'data': image_bytes, 'mimeType': 'image/jpeg'}
                        )
                        print(f"Sent image frame: {len(image_bytes)} bytes")
                    except Exception as e:
                        print(f"Error sending image: {e}")
                
                elif data["type"] == "ping":
                    # Keepalive ping
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                print("WebSocket disconnected")
                break
            except json.JSONDecodeError:
                print("Invalid JSON received")
                continue
            except Exception as e:
                print(f"Error in WebSocket loop: {e}")
                traceback.print_exc()
                break
    
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        # Cleanup
        if gemini_receive_task:
            gemini_receive_task.cancel()
            try:
                await gemini_receive_task
            except asyncio.CancelledError:
                pass
        
        if context_manager:
            try:
                await context_manager.__aexit__(None, None, None)
                print("✓ Gemini session closed")
            except:
                pass
        
        try:
            await websocket.close()
        except:
            pass
        
        print("✓ WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)