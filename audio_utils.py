import io
from pydub import AudioSegment


def convert_audio_to_pcm(audio_bytes: bytes, filename: str) -> tuple[bytes, int]:
    """Convert any audio format to PCM.
    
    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename to determine format
        
    Returns:
        Tuple of (pcm_data, sample_rate)
    """
    try:
        file_ext = filename.lower().split(".")[-1]
        
        print(f"Converting {file_ext} to PCM...")
        
        # Load audio using pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=file_ext)
        
        # Convert to mono, 16-bit, 16kHz
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        audio = audio.set_frame_rate(16000)
        
        # Export as raw PCM
        pcm_buffer = io.BytesIO()
        audio.export(pcm_buffer, format="s16le")
        pcm_data = pcm_buffer.getvalue()
        
        print(f"✓ Converted to PCM: {len(pcm_data)} bytes, 16kHz, mono, 16-bit")
        print(f"  Duration: {len(audio) / 1000:.2f} seconds")
        
        return pcm_data, 16000
        
    except Exception as e:
        print(f"Error converting audio: {e}")
        raise


def convert_webm_chunk_to_pcm(audio_bytes: bytes) -> tuple[bytes, int]:
    """Convert WebM audio chunk to PCM format for Gemini.
    
    Args:
        audio_bytes: Raw WebM/Opus audio bytes from browser
        
    Returns:
        Tuple of (pcm_data, sample_rate)
    """
    try:
        # Load WebM audio using pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        
        # Convert to mono, 16-bit, 16kHz (required by Gemini)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        audio = audio.set_frame_rate(16000)
        
        # Export as raw PCM
        pcm_buffer = io.BytesIO()
        audio.export(pcm_buffer, format="s16le")
        pcm_data = pcm_buffer.getvalue()
        
        return pcm_data, 16000
        
    except Exception as e:
        print(f"Error converting WebM chunk: {e}")
        raise
