#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Assistant Vocal avec Interface Graphique Simple
Utilise Tkinter pour l'interface
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import queue
import time
import os
import sys
from datetime import datetime

# Ajouter le chemin
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyaudio
import wave
import tempfile
import numpy as np
import requests
import json

class AudioRecorderSimple:
    """Version simplifiée de l'enregistreur audio"""
    
    def __init__(self):
        self.sample_rates = [44100, 48000, 16000, 8000]  # Essayer différents taux
        self.channels = 1
        self.chunk = 1024
        self.format = pyaudio.paInt16
        
    def get_working_sample_rate(self):
        """Trouve un taux d'échantillonnage qui fonctionne"""
        p = None
        try:
            p = pyaudio.PyAudio()
            
            # Chercher un périphérique d'entrée
            device_index = None
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0:
                    device_index = i
                    break
            
            if device_index is None:
                return 16000
                
            # Tester chaque taux
            for rate in self.sample_rates:
                try:
                    stream = p.open(
                        format=self.format,
                        channels=self.channels,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=self.chunk
                    )
                    stream.close()
                    return rate
                except:
                    continue
                    
        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            if p:
                p.terminate()
                
        return 16000  # Valeur par défaut
    
    def record(self, duration=5):
        """Enregistre l'audio pendant une durée donnée"""
        sample_rate = self.get_working_sample_rate()
        
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            for i in range(0, int(sample_rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Sauvegarder
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                
            return temp_file.name, sample_rate
            
        except Exception as e:
            print(f"Erreur enregistrement: {e}")
            return None, None
        finally:
            p.terminate()

class SpeechToTextSimple:
    """Version simplifiée avec Vosk"""
    
    def __init__(self):
        self.model = None
        self.model_path = "models/vosk-model-small-fr-0.22"
        
    def download_model(self):
        """Télécharge le modèle si nécessaire"""
        import urllib.request
        import zipfile
        
        if os.path.exists(self.model_path):
            return True
            
        try:
            print("Téléchargement du modèle Vosk...")
            url = "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
            zip_path = "models/vosk-model-small-fr-0.22.zip"
            
            os.makedirs("models", exist_ok=True)
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("models")
            
            os.remove(zip_path)
            return True
        except:
            return False
    
    def load_model(self):
        """Charge le modèle"""
        if self.model is None:
            from vosk import Model
            if not self.download_model():
                return False
            self.model = Model(self.model_path)
        return True
    
    def transcribe(self, audio_file, sample_rate):
        """Transcrit l'audio"""
        if not self.load_model():
            return ""
            
        from vosk import KaldiRecognizer
        import json
        
        try:
            wf = wave.open(audio_file, "rb")
            rec = KaldiRecognizer(self.model, wf.getframerate())
            
            text = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text += result.get("text", "") + " "
            
            final = json.loads(rec.FinalResult())
            text += final.get("text", "")
            
            wf.close()
            os.unlink(audio_file)
            
            return text.strip()
        except:
            return ""

class LLMClient:
    """Client Ollama simplifié"""
    
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:3b"
        
    def generate(self, prompt):
        """Génère une réponse"""
        system_prompt = "Tu es un assistant vocal français amical. Réponds en 2-3 phrases maximum."
        full_prompt = f"{system_prompt}\n\nUtilisateur: {prompt}\n\nAssistant:"
        
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"num_predict": 150}
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "Désolé, je n'ai pas compris.")
        except:
            return "Je n'arrive pas à répondre pour le moment."
        
        return "Désolé, erreur de connexion."

class TextToSpeechSimple:
    """TTS simple avec gTTS"""
    
    def __init__(self):
        self.initialized = False
        
    def speak(self, text):
        """Parle le texte"""
        if not text:
            return
            
        try:
            from gtts import gTTS
            import pygame
            import tempfile
            
            if not self.initialized:
                pygame.mixer.init()
                self.initialized = True
                
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
            
            tts = gTTS(text=text, lang='fr', slow=False)
            tts.save(temp_file)
            
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            pygame.mixer.music.unload()
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"Erreur TTS: {e}")
            print(f"[PAROLE] {text}")

class AssistantGUI:
    """Interface graphique de l'assistant"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Assistant Vocal Français")
        self.root.geometry("700x600")
        self.root.configure(bg='#2c3e50')
        
        # Variables
        self.is_recording = False
        self.recording_thread = None
        self.audio_recorder = AudioRecorderSimple()
        self.stt = SpeechToTextSimple()
        self.llm = LLMClient()
        self.tts = TextToSpeechSimple()
        
        # Queue pour les messages
        self.message_queue = queue.Queue()
        
        self.setup_ui()
        self.check_ollama()
        
        # Démarrer la vérification des messages
        self.process_messages()
        
    def setup_ui(self):
        """Configure l'interface"""
        # Style
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Titre
        title = tk.Label(
            self.root,
            text="🤖 Assistant Vocal Français",
            font=('Arial', 20, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=20
        )
        title.grid(row=0, column=0, sticky='ew')
        
        # Zone de conversation
        self.conversation = scrolledtext.ScrolledText(
            self.root,
            height=15,
            font=('Arial', 11),
            bg='#ecf0f1',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.conversation.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')
        
        # Frame pour les contrôles
        control_frame = tk.Frame(self.root, bg='#2c3e50')
        control_frame.grid(row=2, column=0, pady=20)
        
        # Bouton d'enregistrement
        self.record_button = tk.Button(
            control_frame,
            text="🎤 Parler (5 secondes)",
            command=self.toggle_recording,
            font=('Arial', 14),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.record_button.pack(side=tk.LEFT, padx=10)
        
        # Statut
        self.status_label = tk.Label(
            control_frame,
            text="✅ Prêt",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#2ecc71'
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Frame pour les infos
        info_frame = tk.Frame(self.root, bg='#2c3e50')
        info_frame.grid(row=3, column=0, pady=10)
        
        # Label info
        info_text = tk.Label(
            info_frame,
            text="💡 Appuyez sur 'Parler' et parlez pendant 5 secondes\n"
                 "🗣️ Dites 'au revoir' pour quitter\n"
                 "🔊 La réponse sera vocalisée",
            font=('Arial', 9),
            bg='#2c3e50',
            fg='#95a5a6',
            justify=tk.CENTER
        )
        info_text.pack()
        
        # Ajouter un message de bienvenue
        self.add_message("Assistant", "Bonjour ! Je suis votre assistant vocal. Comment puis-je vous aider ?", "assistant")
        
    def add_message(self, sender, message, type_msg):
        """Ajoute un message à la conversation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if type_msg == "user":
            self.conversation.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.conversation.insert(tk.END, f"👤 Vous: ", "user_label")
            self.conversation.insert(tk.END, f"{message}\n\n", "user")
        else:
            self.conversation.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.conversation.insert(tk.END, f"🤖 Assistant: ", "assistant_label")
            self.conversation.insert(tk.END, f"{message}\n\n", "assistant")
        
        self.conversation.see(tk.END)
        
        # Configurer les couleurs
        self.conversation.tag_config("timestamp", foreground="#7f8c8d", font=('Arial', 8))
        self.conversation.tag_config("user_label", foreground="#3498db", font=('Arial', 10, 'bold'))
        self.conversation.tag_config("assistant_label", foreground="#2ecc71", font=('Arial', 10, 'bold'))
        self.conversation.tag_config("user", foreground="#2c3e50", font=('Arial', 10))
        self.conversation.tag_config("assistant", foreground="#27ae60", font=('Arial', 10))
    
    def check_ollama(self):
        """Vérifie si Ollama est accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="✅ Ollama connecté", fg="#2ecc71")
            else:
                self.status_label.config(text="⚠️ Ollama non disponible", fg="#e74c3c")
        except:
            self.status_label.config(text="❌ Ollama non démarré", fg="#e74c3c")
            messagebox.showwarning(
                "Ollama non disponible",
                "Ollama n'est pas démarré.\n\n"
                "Pour démarrer Ollama:\n"
                "1. Ouvrez un terminal\n"
                "2. Lancez: ollama serve\n"
                "3. Dans un autre terminal: ollama pull llama3.2:3b"
            )
    
    def toggle_recording(self):
        """Lance ou arrête l'enregistrement"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.record_button.config(state=tk.DISABLED, text="🎤 Enregistrement...")
        self.status_label.config(text="🔴 Enregistrement en cours...", fg="#e74c3c")
        
        # Démarrer l'enregistrement dans un thread
        self.recording_thread = threading.Thread(target=self.record_and_process)
        self.recording_thread.daemon = True
        self.recording_thread.start()
    
    def record_and_process(self):
        """Enregistre et traite l'audio"""
        try:
            # Enregistrer
            self.root.after(0, lambda: self.add_message("Système", "🎤 Enregistrement de 5 secondes...", "assistant"))
            
            audio_file, sample_rate = self.audio_recorder.record(duration=5)
            
            if audio_file:
                self.root.after(0, lambda: self.status_label.config(text="📝 Transcription en cours...", fg="#f39c12"))
                
                # Transcrire
                text = self.stt.transcribe(audio_file, sample_rate)
                
                if text:
                    self.root.after(0, lambda: self.add_message("Vous", text, "user"))
                    
                    # Vérifier si on doit quitter
                    if "au revoir" in text.lower() or "arrête" in text.lower():
                        self.root.after(0, lambda: self.add_message("Assistant", "Au revoir !", "assistant"))
                        self.root.after(0, lambda: self.tts.speak("Au revoir"))
                        self.root.after(1000, self.root.quit)
                        return
                    
                    # Générer réponse
                    self.root.after(0, lambda: self.status_label.config(text="🤔 Réflexion en cours...", fg="#3498db"))
                    
                    response = self.llm.generate(text)
                    
                    if response:
                        self.root.after(0, lambda: self.add_message("Assistant", response, "assistant"))
                        self.root.after(0, lambda: self.status_label.config(text="🔊 Parole en cours...", fg="#2ecc71"))
                        
                        # Parler
                        self.tts.speak(response)
                    else:
                        self.root.after(0, lambda: self.add_message("Assistant", "Désolé, je n'ai pas pu générer une réponse.", "assistant"))
                else:
                    self.root.after(0, lambda: self.add_message("Assistant", "Je n'ai pas compris. Pouvez-vous répéter ?", "assistant"))
                    self.root.after(0, lambda: self.tts.speak("Je n'ai pas compris. Pouvez-vous répéter ?"))
            else:
                self.root.after(0, lambda: self.add_message("Assistant", "Erreur d'enregistrement. Vérifiez votre microphone.", "assistant"))
                self.root.after(0, lambda: self.tts.speak("Erreur d'enregistrement. Vérifiez votre microphone."))
                
        except Exception as e:
            print(f"Erreur: {e}")
            self.root.after(0, lambda: self.add_message("Assistant", f"Erreur: {str(e)}", "assistant"))
        finally:
            self.is_recording = False
            self.root.after(0, lambda: self.record_button.config(state=tk.NORMAL, text="🎤 Parler (5 secondes)"))
            self.root.after(0, lambda: self.status_label.config(text="✅ Prêt", fg="#2ecc71"))
    
    def process_messages(self):
        """Traite les messages dans la queue"""
        try:
            while not self.message_queue.empty():
                msg_type, content = self.message_queue.get_nowait()
                if msg_type == "user":
                    self.add_message("Vous", content, "user")
                elif msg_type == "assistant":
                    self.add_message("Assistant", content, "assistant")
        except:
            pass
        finally:
            self.root.after(100, self.process_messages)
    
    def run(self):
        """Lance l'interface"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Fermeture propre"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'assistant ?"):
            self.root.quit()
            self.root.destroy()

def main():
    """Point d'entrée"""
    # Vérifier les dépendances
    try:
        import tkinter
        import pyaudio
        import vosk
        import requests
        import gtts
        import pygame
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("\n💡 Installez les dépendances:")
        print("pip install pyaudio vosk requests gtts pygame")
        sys.exit(1)
    
    # Lancer l'interface
    app = AssistantGUI()
    app.run()

if __name__ == "__main__":
    main()
    