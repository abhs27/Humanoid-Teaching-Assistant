import os
import uuid
import glob
import numpy as np
import torch
import ChatTTS
import subprocess
import re
import unicodedata
import inflect
import sys
import threading
from scipy.io.wavfile import write as write_wav
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv


# Get the absolute path of the directory containing this script (app.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the folder containing your RAG system
module_path = os.path.join(script_dir, 'backend')

# Add that path to the beginning of Python's search paths
if module_path not in sys.path:
    sys.path.insert(0, module_path)

# Now you can import it directly, and Python will find it
from rag_system import RAGSystem


# Import your custom RAGSystem
from rag_system import RAGSystem
# Import the STT library
from RealtimeSTT import AudioToTextRecorder
# --- Initialization ---
print("🚀 Initializing application, please wait...")
load_dotenv()
p = inflect.engine()

# Initialize Flask App and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*",
                    async_mode='threading'
                    )

# Dictionaries to hold client-specific processes and threads
ffmpeg_processes = {}
client_threads = {}

# Create a single, shared instance of your RAG System
rag_system = RAGSystem()
print("✅ RAG System is ready.")

# Pre-load the ChatTTS model once at startup
chattts = ChatTTS.Chat()
chattts.load(compile=False)
print("✅ TTS Model is ready.")

# --- STT Initialization with Wake Word ---

def on_wakeword():
    print("👂 Wake word detected!")
    socketio.emit('wakeword_detected')

def on_transcription(text: str):
    if not text.strip():
        return
    print(f"🎤 Transcription received: '{text}'")
    socketio.emit('transcription_result', {'text': text})


# Create a single, shared instance of the STT recorder, using your config
stt_recorder = AudioToTextRecorder(
    spinner=False,
    use_microphone=False,
    device="cpu",
    wakeword_backend="pvporcupine",
    wake_words="jarvis",
    wake_words_sensitivity=0.6,
    on_wakeword_detected=on_wakeword,
    enable_realtime_transcription=True,
    on_realtime_transcription_stabilized =on_transcription
)
print("✅ STT Engine is ready and listening for 'jarvis'.")

# --- General Setup ---
AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
print("🎉 Application is ready to use!")

# --- Helper Functions (from your original script) ---
SYMBOL_MAP = {
    '+': 'plus', '-': 'minus', '*': 'times', '/': 'divided by', '=': 'equals',
    '%': 'percent', '>': 'greater than', '<': 'less than', '&': 'and',
    '@': 'at', '#': 'number', '$': 'dollar', '^': 'caret', '√': 'square root',
}

def clean_text(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    for symbol, word in SYMBOL_MAP.items():
        text = text.replace(symbol, f' {word} ')
    def replace_digits(match):
        num = int(match.group(0))
        return p.number_to_words(num)
    text = re.sub(r'\b\d+\b', replace_digits, text)
    text = re.sub(r'[^\w\s.,\'-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text else "Let's try again."

def generate_tts_audio(text: str) -> str:
    try:
        files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
        for f in files:
            os.remove(f)
    except Exception as e:
        print(f"Error cleaning up audio files: {e}")

    texts = [clean_text(text)]
    torch.manual_seed(1335)
    spk_id = chattts.sample_random_speaker()
    params_infer_code = ChatTTS.Chat.InferCodeParams(spk_emb=spk_id, temperature=0.7, top_P=0.9, top_K=30)
    params_refine_text = ChatTTS.Chat.RefineTextParams(prompt='[oral_2][laugh_0][break_6]')
    wavs = chattts.infer(texts, params_refine_text=params_refine_text, params_infer_code=params_infer_code, use_decoder=True)
    sample_rate = 24000
    silence = np.zeros(int(0.5 * sample_rate), dtype=np.float32)
    wav_padded = np.concatenate([wavs[0], silence])
    filename = f"{uuid.uuid4()}.wav"
    output_path = os.path.join(AUDIO_DIR, filename)
    write_wav(output_path, sample_rate, (wav_padded * 32767).astype(np.int16))
    return f"/static/audio/{filename}"

# --- Background Thread for Audio Processing ---
def read_ffmpeg_output(process, sid):
    """ This function runs in a background thread for each client. """
    while True:
        # Check if the process has been terminated
        if sid not in ffmpeg_processes or process.poll() is not None:
            print(f"FFmpeg process for {sid} ended. Stopping thread.")
            break
        # Read decoded audio in chunks
        decoded_audio = process.stdout.read(4096)
        if decoded_audio:
            stt_recorder.feed_audio(decoded_audio)
        else:
            # If there's no data, sleep briefly to prevent a busy loop
            socketio.sleep(0.01)

# --- HTTP Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400
    text_answer = rag_system.query(question)
    audio_url = generate_tts_audio(text_answer)
    return jsonify({"text_answer": text_answer, "audio_url": audio_url})

# --- WebSocket Events ---
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f'✅ Client connected: {sid}')
    stt_recorder.start()
    
    ffmpeg_command = ['ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ar', '16000', '-ac', '1', 'pipe:1']
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ffmpeg_processes[sid] = process
    
    # Start the background thread for this client
    thread = socketio.start_background_task(target=read_ffmpeg_output, process=process, sid=sid)
    client_threads[sid] = thread
    print(f"Started FFmpeg process and reader thread for {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'❌ Client disconnected: {sid}')
    stt_recorder.stop()
    
    if sid in ffmpeg_processes:
        try:
            ffmpeg_processes[sid].stdin.close()
            ffmpeg_processes[sid].terminate()
            ffmpeg_processes[sid].wait()
        except (IOError, BrokenPipeError):
            pass # Ignore errors on close, process might already be gone
        del ffmpeg_processes[sid]
        print(f"Terminated FFmpeg process for {sid}")
    
    if sid in client_threads:
        # No need to explicitly join the thread, it will exit on its own
        del client_threads[sid]

@socketio.on('audio_stream')
def handle_audio_stream(data):
    # print("📡 Audio stream received")  # This should now appear
    sid = request.sid
    process = ffmpeg_processes.get(sid)
    if process:
        try:
            # Convert the received data to bytes if it's not already
            if isinstance(data, str):
                # If data comes as base64 string, decode it
                import base64
                audio_bytes = base64.b64decode(data)
            else:
                # If data is already bytes (which it should be from frontend)
                audio_bytes = data
            
            process.stdin.write(audio_bytes)
            process.stdin.flush()  # Important: flush the buffer
        except (IOError, BrokenPipeError):
            print(f"Could not write to FFmpeg stdin for {sid}. It might have closed.")
        except Exception as e:
            print(f"Error writing to FFmpeg for {sid}: {e}")

# --- Main Execution ---
if __name__ == '__main__':
    print("🌍 Starting Flask server at http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000)
