#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'enregistrement audio avec gestion des erreurs améliorée
"""

import pyaudio
import wave
import numpy as np
import tempfile
import os
import time
import sys

class AudioRecorder:
    """Classe pour l'enregistrement audio avec détection de silence"""
    
    def __init__(self, config):
        """
        Initialise l'enregistreur audio
        """
        self.config = config
        self.sample_rate = config.get('sample_rate', 16000)
        self.channels = config.get('channels', 1)
        self.chunk_size = config.get('chunk_size', 1024)
        self.format = pyaudio.paInt16
        self.silence_threshold = config.get('silence_threshold', 500)
        self.silence_duration = config.get('silence_duration', 1.5)
        
        self.p = None
        self.stream = None
        self.device_index = None
        
    def list_devices(self):
        """Liste les périphériques audio disponibles"""
        if self.p is None:
            self.p = pyaudio.PyAudio()
        
        print("\n🎤 Périphériques audio disponibles:")
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                print(f"  {i}: {dev['name']} (canaux: {dev['maxInputChannels']})")
        print()
    
    def initialize(self):
        """Initialise PyAudio et trouve un périphérique valide"""
        if self.p is None:
            try:
                self.p = pyaudio.PyAudio()
                
                # Chercher un périphérique d'entrée valide
                for i in range(self.p.get_device_count()):
                    dev = self.p.get_device_info_by_index(i)
                    if dev['maxInputChannels'] > 0:
                        self.device_index = i
                        print(f"✅ Périphérique audio sélectionné: {dev['name']}")
                        break
                
                if self.device_index is None:
                    print("⚠️ Aucun périphérique d'entrée trouvé!")
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur initialisation audio: {e}")
                return False
        return True
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
            
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
            self.p = None
    
    def get_audio_level(self, data):
        """Calcule le niveau audio (RMS)"""
        try:
            audio_array = np.frombuffer(data, dtype=np.int16)
            if len(audio_array) > 0:
                rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
                return rms
        except:
            pass
        return 0
    
    def record_with_silence_detection(self):
        """Enregistre jusqu'à détection de silence"""
        if not self.initialize():
            return None
        
        # Ouvrir le stream avec gestion d'erreurs
        try:
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                start=False
            )
            self.stream.start_stream()
        except Exception as e:
            print(f"❌ Erreur ouverture stream audio: {e}")
            print("💡 Vérifiez que votre microphone est connecté et accessible")
            self.cleanup()
            return None
        
        print("🎤 Enregistrement en cours... Parlez maintenant")
        frames = []
        silent_chunks = 0
        max_silent_chunks = int(self.silence_duration * self.sample_rate / self.chunk_size)
        max_duration_chunks = int(10 * self.sample_rate / self.chunk_size)  # Maximum 10 secondes
        started = False
        chunks_recorded = 0
        
        try:
            while chunks_recorded < max_duration_chunks:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    level = self.get_audio_level(data)
                    
                    # Détection de début de parole
                    if not started and level > self.silence_threshold:
                        started = True
                        print("🔊 Parole détectée...")
                    
                    if started:
                        frames.append(data)
                        chunks_recorded += 1
                        
                        # Détection de silence
                        if level < self.silence_threshold:
                            silent_chunks += 1
                            if silent_chunks > max_silent_chunks:
                                print("🔇 Silence détecté, arrêt de l'enregistrement")
                                break
                        else:
                            silent_chunks = 0
                    else:
                        # Pas encore de parole, attendre
                        time.sleep(0.05)
                        
                except Exception as e:
                    print(f"⚠️ Erreur lecture audio: {e}")
                    break
                    
        except KeyboardInterrupt:
            print("\n⏸️ Enregistrement interrompu")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if not frames or len(frames) < 10:
            print("⚠️ Aucune parole détectée ou enregistrement trop court")
            return None
            
        # Sauvegarder dans un fichier temporaire
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
                
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde audio: {e}")
            return None
    
    def test_microphone(self):
        """Test simple du microphone"""
        print("\n🎤 Test du microphone...")
        audio_file = self.record_with_silence_detection()
        
        if audio_file:
            print(f"✅ Enregistrement réussi: {audio_file}")
            # Jouer le son enregistré (optionnel)
            # os.system(f"aplay {audio_file}")
            return True
        else:
            print("❌ Test du microphone échoué")
            return False