#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de synthèse vocale
"""

import pyttsx3
import tempfile
import os
import pygame
from gtts import gTTS
import threading

class TextToSpeech:
    """Classe pour la synthèse vocale"""
    
    def __init__(self, config):
        """
        Initialise le moteur TTS
        """
        self.config = config
        self.engine_type = config['engine']
        self.engine = None
        self.rate = config.get('rate', 170)
        self.volume = config.get('volume', 0.9)
        
        if self.engine_type == "pyttsx3":
            self._init_pyttsx3()
        else:
            self._init_gtts()
    
    def _init_pyttsx3(self):
        """Initialise pyttsx3"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Chercher une voix française
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                    
            print("✅ Moteur TTS (pyttsx3) initialisé")
        except Exception as e:
            print(f"⚠️ Erreur pyttsx3: {e}, utilisation de gTTS")
            self.engine_type = "gtts"
            self._init_gtts()
    
    def _init_gtts(self):
        """Initialise gTTS"""
        try:
            if not pygame.get_init():
                pygame.mixer.init()
            print("✅ Moteur TTS (gTTS) initialisé")
        except Exception as e:
            print(f"⚠️ Erreur gTTS: {e}")
            self.engine = None
    
    def speak(self, text):
        """Convertit le texte en parole"""
        if not text or text.strip() == "":
            return
            
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"❌ Erreur synthèse: {e}")
                print(f"🔊 {text}")
        elif self.engine_type == "gtts":
            self._speak_gtts(text)
        else:
            print(f"🔊 {text}")
    
    def _speak_gtts(self, text):
        """Parle avec gTTS"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
            
            tts = gTTS(text=text, lang='fr', slow=False)
            tts.save(temp_file)
            
            if not pygame.get_init():
                pygame.mixer.init()
                
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            pygame.mixer.music.unload()
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"❌ Erreur gTTS: {e}")
            print(f"🔊 {text}")