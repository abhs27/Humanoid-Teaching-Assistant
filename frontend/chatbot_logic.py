import os
import sys
import subprocess
import re
import inflect
import torch
import numpy as np
from scipy.io.wavfile import write as write_wav

# Your existing imports
parent_dir_of_repo = "./backend/ChatTTS" 
sys.path.insert(0, os.path.abspath(parent_dir_of_repo))
parent_dir_of_repo = "./backend" 
sys.path.insert(0, os.path.abspath(parent_dir_of_repo))
import ChatTTS
from backend.rag_system import RAGSystem

# This class encapsulates all the backend logic from your original script.
class ChatbotLogic:
    def __init__(self):
        print("Initializing Chatbot Logic...")
        # ----------------- SETUP -----------------
        self.p = inflect.engine()
        self.rag = RAGSystem()
        auto_ingest_docs(self.rag)

        # ----------------- TTS SETUP -----------------
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"TTS will use {device.upper()} for processing")
        self.chattts = ChatTTS.Chat()
        self.chattts.load(compile=False, device=device)
        torch.manual_seed(1330)
        spk_id = self.chattts.sample_random_speaker()

        self.params_infer_code = ChatTTS.Chat.InferCodeParams(
            spk_emb=spk_id, temperature=0.7, top_P=0.9, top_K=30
        )
        self.params_refine_text = ChatTTS.Chat.RefineTextParams()
        print("Chatbot Logic Initialized Successfully.")

    def get_response(self, text: str) -> str:
        """Queries the RAG system to get a text response."""
        return self.rag.query(text)

    def generate_tts(self, text: str, output_path="output.wav") -> str:
        """
        Generates TTS audio from text and SAVES it to a file.
        CRITICAL CHANGE: This function NO LONGER plays the audio.
        It just creates the file and returns the path.
        """
        try:
            safe_text = self._clean_text(text)
            wavs = self.chattts.infer(
                [safe_text],
                params_refine_text=self.params_refine_text,
                params_infer_code=self.params_infer_code,
                use_decoder=True
            )
            if not wavs or wavs[0] is None:
                print("⚠️ No audio generated.")
                return ""

            # Save the audio file
            write_wav(output_path, 24000, (wavs[0] * 32767).astype(np.int16))
            return output_path
        except Exception as e:
            print(f"⚠️ TTS Error: {str(e)}")
            return ""

    def launch_game(self, game_name: str):
        """Launches a game script as a new process."""
        script_path = None
        if game_name == "finger_counting":
            script_path = "image detector/finger_counting_game.py"
        elif game_name == "healthy_food":
            script_path = "image detector/healthyVSjunk.py"
        elif game_name == "puzzle":
            script_path = "image detector/puzzle.py"

        if script_path and os.path.exists(script_path):
            try:
                print(f"Launching game: {script_path}")
                subprocess.Popen([sys.executable, script_path])
            except Exception as e:
                print(f"An error occurred while launching the game: {e}")
        else:
            print(f"Error: Could not find the game script for '{game_name}'")


    def _clean_text(self, text: str) -> str:
        """
        Private helper method for cleaning text.
        (Copied directly from your clean_text function)
        """
        # --- All your text cleaning logic from teacher_chatbot.py goes here ---
        # (I've omitted the full code for brevity, but you should copy it here)
        SYMBOL_MAP = {'+': 'plus', '-': 'minus', '*': 'times', '/': 'divided by', '=': 'equals', '%': 'percent', '>': 'greater than', '<': 'less than', '&': 'and', '@': 'at', '#': 'number', '$': 'dollar', '^': 'caret', '√': 'square root'}
        for symbol, word in SYMBOL_MAP.items():
            text = text.replace(symbol, f' {word} ')
        def replace_digits(match):
            num = int(match.group(0))
            return self.p.number_to_words(num)
        text = re.sub(r'\b\d+\b', replace_digits, text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text or len(text.strip()) < 3:
            return "Let's try again with a different question!"
        return text

# Helper function also moved from the original script
def auto_ingest_docs(rag, docs_folder="./docs"):
    if not os.path.exists(docs_folder):
        os.makedirs(docs_folder)
        return
    supported_exts = {".pdf", ".docx", ".pptx", ".txt"}
    files = [f for f in os.listdir(docs_folder) if os.path.isfile(os.path.join(docs_folder, f))]
    for file_name in files:
        ext = os.path.splitext(file_name)[1].lower()
        if ext in supported_exts:
            file_path = os.path.join(docs_folder, file_name)
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                rag.ingest_file(file_name, file_bytes)
            except Exception as e:
                print(f"Failed to ingest {file_name}: {e}")