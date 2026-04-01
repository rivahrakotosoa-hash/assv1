#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Script de test simple pour le microphone"""

import pyaudio
import wave
import sys
import tempfile
import os

def test_microphone():
    """Test simple du microphone"""
    print("🎤 Test du microphone")
    print("=" * 50)
    
    # Initialiser PyAudio
    p = pyaudio.PyAudio()
    
    # Lister les périphériques
    print("\nPériphériques audio disponibles:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"  {i}: {dev['name']}")
    
    # Paramètres d'enregistrement
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 5
    
    print(f"\n📝 Enregistrement de {RECORD_SECONDS} secondes...")
    
    # Ouvrir le stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    print("🎤 Parlez maintenant...")
    frames = []
    
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        # Afficher une progression simple
        if i % 10 == 0:
            print(".", end="", flush=True)
    
    print("\n✅ Enregistrement terminé")
    
    # Arrêter et fermer
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Sauvegarder
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    print(f"💾 Fichier sauvegardé: {temp_file.name}")
    print(f"📊 Taille: {len(b''.join(frames))} octets")
    
    # Option: jouer le son
    play = input("\n🔊 Jouer l'enregistrement? (o/n): ")
    if play.lower() == 'o':
        os.system(f"aplay {temp_file.name} 2>/dev/null || play {temp_file.name} 2>/dev/null")
    
    return temp_file.name

if __name__ == "__main__":
    test_microphone()