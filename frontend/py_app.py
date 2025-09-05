import sys
import time # <-- Import for heartbeat sleep
import pyaudio # <-- Import for listing audio devices
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QUrl
from PyQt6.QtMultimedia import QSoundEffect

from chatbot_logic import ChatbotLogic
from RealtimeSTT import AudioToTextRecorder

def list_audio_devices():
    """Helper function to print available audio input devices."""
    print("🎤 Listing available audio input devices...")
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    for i in range(0, num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if (device_info.get('maxInputChannels')) > 0:
            print(f"   - Device index {i}: {device_info.get('name')}")
    p.terminate()
    print("--------------------------------------------------")


class BackendWorker(QObject):
    state_changed = pyqtSignal(str)
    tts_audio_ready = pyqtSignal(str)

    def __init__(self, chatbot_logic: ChatbotLogic):
        super().__init__()
        self.chatbot_logic = chatbot_logic
        self.is_running = True
        self.recorder = None

    def run(self):
        """The main STT -> LLM -> TTS pipeline loop."""
        print("Backend worker running...")
        list_audio_devices()
        
        try:
            print("🔧 Setting up AudioToTextRecorder...")
            self.recorder = AudioToTextRecorder(
                wakeword_backend="openwakeword",
                wake_words="jarvis",
                wake_words_sensitivity=0.5,
                on_wakeword_detected=self._on_wakeword_detected,
                on_vad_start=self._on_vad_start,
                spinner=False,
                use_microphone=True,
                device="cpu",
                input_device_index=None,
                level=1,
                min_length_of_recording=0.5,
                min_gap_between_recordings=0.5
            )
            
            print("✅ AudioToTextRecorder initialized successfully")
            self.state_changed.emit("idle")
            
            while self.is_running:
                print("... waiting for transcription ...")
                text = self.recorder.text()
                
                if text and self.is_running:
                    self._process_text(text.strip())
                elif not self.is_running:
                    break

        except Exception as e:
            print(f"An error occurred in the backend worker: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.recorder:
                self.recorder.stop()
            print("Backend worker stopped.")

    def _on_wakeword_detected(self):
        """Callback when wake word is detected."""
        print("🎤 Wake word 'hey_jarvis' detected!")
        self.state_changed.emit("listening")

    def _on_vad_start(self):
        """Callback when voice activity starts (speech begins)."""
        print("👂 Speech detected, listening...")
        self.state_changed.emit("listening")

    def _process_text(self, text):
        """Processes transcribed text to generate and play a response."""
        if not text.strip() or len(text.strip()) < 3:
            self.state_changed.emit("idle")
            return

        print(f"Transcribed Text: {text}")

        self.state_changed.emit("thinking")
        response_text = self.chatbot_logic.get_response(text)
        print(f"RAG Response: {response_text}")

        output_path = self.chatbot_logic.generate_tts(response_text)

        if output_path:
            self.state_changed.emit("speaking")
            self.tts_audio_ready.emit(output_path)
        else:
            self.state_changed.emit("idle")

    def stop(self):
        """Signals the run loop to exit and aborts blocking calls."""
        print("Signaling backend worker to stop...")
        self.is_running = False
        if self.recorder:
            self.recorder.abort()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Humanoid Teaching Assistant")
        self.layout = QVBoxLayout()

        self.humanoid_label = QLabel("Press Start to Begin")
        self.layout.addWidget(self.humanoid_label)
        
        # --- ANIMATION SETUP WITH ERROR HANDLING ---
        self.setup_animations()
        
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.stop_button)
        self.setLayout(self.layout)

        # --- INITIALIZE CHATBOT LOGIC ---
        # This can take a while, so we do it once when the app starts
        self.chatbot_logic = ChatbotLogic()
        
        # --- ADD AUDIO PLAYER ---
        self.audio_player = QSoundEffect()
        
        # --- CONNECTIONS ---
        self.start_button.clicked.connect(self.start_backend)
        self.stop_button.clicked.connect(self.stop_backend)
        self.audio_player.playingChanged.connect(self._on_audio_finished)

    def setup_animations(self):
        """Setup animations with fallback handling."""
        try:
            self.listening_anim = QMovie("animations/listening.gif")
            self.thinking_anim = QMovie("animations/thinking.gif")
            self.speaking_anim = QMovie("animations/speaking.gif")
            self.idle_anim = QMovie("animations/idle.gif")
            
            # Check if animations loaded successfully
            if not all([self.listening_anim.isValid(), self.thinking_anim.isValid(), 
                       self.speaking_anim.isValid(), self.idle_anim.isValid()]):
                raise FileNotFoundError("Some animation files are invalid")
                
        except (FileNotFoundError, Exception) as e:
            print(f"Warning: Animation files not found: {e}")
            print("Using text-based state indicators instead")
            
            # Create fallback text-based animations
            self.listening_anim = None
            self.thinking_anim = None
            self.speaking_anim = None
            self.idle_anim = None

    def start_backend(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.backend_thread = QThread()
        # Pass the initialized chatbot logic to the worker
        self.backend_worker = BackendWorker(self.chatbot_logic)
        self.backend_worker.moveToThread(self.backend_thread)

        # Connect signals
        self.backend_worker.state_changed.connect(self.update_humanoid_state)
        self.backend_worker.tts_audio_ready.connect(self.play_audio)
        self.backend_thread.started.connect(self.backend_worker.run)
        
        self.backend_thread.start()
        self.humanoid_label.setText("Starting session... Say 'Hey Jarvis' to begin.")

    def stop_backend(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if hasattr(self, 'backend_thread') and self.backend_thread.isRunning():
            self.backend_worker.stop() # Gracefully stop the loop
            self.backend_thread.quit()
            self.backend_thread.wait()
        self.humanoid_label.setMovie(self.idle_anim) # Reset to idle
        if self.idle_anim:
            self.idle_anim.start()
        self.humanoid_label.setText("Session Ended.")

    def update_humanoid_state(self, state):
        print(f"UI changing to state: {state}")
        
        # Handle animations if available, otherwise use text
        if self.listening_anim and self.thinking_anim and self.speaking_anim and self.idle_anim:
            # Use animations
            if state == "idle":
                self.humanoid_label.setMovie(self.idle_anim)
                self.idle_anim.start()
            elif state == "listening":
                self.humanoid_label.setMovie(self.listening_anim)
                self.listening_anim.start()
            elif state == "thinking":
                self.humanoid_label.setMovie(self.thinking_anim)
                self.thinking_anim.start()
            elif state == "speaking":
                self.humanoid_label.setMovie(self.speaking_anim)
                self.speaking_anim.start()
        else:
            # Use text-based state indicators
            if state == "idle":
                self.humanoid_label.setText("🔄 Waiting for 'Hey Jarvis'...")
            elif state == "listening":
                self.humanoid_label.setText("👂 Listening... Speak now!")
            elif state == "thinking":
                self.humanoid_label.setText("🤔 Thinking...")
            elif state == "speaking":
                self.humanoid_label.setText("🗣 Speaking...")
            
    def play_audio(self, path: str):
        """Slot to play the generated audio file."""
        if path:
            print(f"UI playing audio: {path}")
            url = QUrl.fromLocalFile(path)
            # By adding a unique query string, we force QSoundEffect to reload the file
            # and not use a cached version.
            url.setQuery(f"v={time.time()}")
            self.audio_player.setSource(url)
            self.audio_player.play()

    def _on_audio_finished(self):
        """Callback when audio playback state changes."""
        if not self.audio_player.isPlaying():
            print("Audio finished, returning to idle state.")
            self.update_humanoid_state("idle")

# The main execution block remains the same
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())