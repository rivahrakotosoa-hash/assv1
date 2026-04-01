#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de reconnaissance vocale avec Vosk
Plus léger que Whisper, parfait pour 8Go RAM
"""

import os
import json
import wave
from vosk import Model, KaldiRecognizer
import urllib.request
import zipfile

class SpeechToText:
    """Classe pour la conversion parole en texte avec Vosk"""
    
    def __init__(self, config):
        """
        Initialise le moteur de reconnaissance vocale
        """
        self.config = config
        self.model = None
        self.model_path = "models/vosk-model-small-fr-0.22"
        self.sample_rate = 16000
        
    def download_model(self):
        """Télécharge le modèle Vosk français"""
        if os.path.exists(self.model_path):
            return True
            
        print("📥 Téléchargement du modèle Vosk français...")
        os.makedirs("models", exist_ok=True)
        
        # Utiliser le modèle small français
        url = "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
        zip_path = "models/vosk-model-small-fr-0.22.zip"
        
        try:
            print("⏳ Téléchargement (environ 40 Mo)...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("📦 Décompression...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("models")
            
            os.remove(zip_path)
            print("✅ Modèle Vosk téléchargé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur téléchargement: {e}")
            print("💡 Vous pouvez télécharger manuellement depuis: https://alphacephei.com/vosk/models")
            return False
    
    def load_model(self):
        """Charge le modèle Vosk"""
        if self.model is None:
            if not self.download_model():
                return False
                
            print(f"📥 Chargement du modèle Vosk...")
            try:
                self.model = Model(self.model_path)
                print("✅ Modèle Vosk chargé avec succès")
                return True
            except Exception as e:
                print(f"❌ Erreur chargement modèle: {e}")
                return False
        return True
    
    def unload_model(self):
        """Décharge le modèle"""
        if self.model is not None:
            del self.model
            self.model = None
            import gc
            gc.collect()
            print("🗑️ Modèle Vosk déchargé")
    
    def transcribe(self, audio_file_path):
        """
        Transcrit un fichier audio en texte
        """
        if not os.path.exists(audio_file_path):
            print(f"❌ Fichier audio non trouvé: {audio_file_path}")
            return ""
            
        if not self.load_model():
            return ""
            
        try:
            # Ouvrir le fichier audio
            wf = wave.open(audio_file_path, "rb")
            
            # Vérifier le format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != self.sample_rate:
                print(f"⚠️ Format audio incorrect, tentative de lecture quand même...")
            
            # Créer le recognizer
            rec = KaldiRecognizer(self.model, wf.getframerate())
            
            # Transcrire
            text_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        text_parts.append(result["text"])
            
            # Récupérer le texte final
            final_result = json.loads(rec.FinalResult())
            if final_result.get("text"):
                text_parts.append(final_result["text"])
            
            wf.close()
            
            # Nettoyer le fichier temporaire
            try:
                os.unlink(audio_file_path)
            except:
                pass
                
            text = " ".join(text_parts).strip()
            return text
            
        except Exception as e:
            print(f"❌ Erreur transcription: {e}")
            return ""