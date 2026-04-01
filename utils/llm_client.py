#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module client LLM pour Ollama
"""

import requests
import json

class LLMClient:
    """Client pour interagir avec Ollama"""
    
    def __init__(self, config):
        """
        Initialise le client LLM
        """
        self.config = config
        self.model = config['model']
        self.url = config['url']
        self.max_tokens = config['max_tokens']
        self.temperature = config['temperature']
        self.system_prompt = config['system_prompt']
        
    def generate(self, prompt):
        """
        Génère une réponse à partir du prompt
        """
        # Construire le prompt complet
        full_prompt = f"{self.system_prompt}\n\nUtilisateur: {prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature
            }
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return "Désolé, je n'arrive pas à répondre pour le moment."
                
        except requests.exceptions.Timeout:
            return "Je réfléchis encore, pouvez-vous répéter ?"
        except requests.exceptions.ConnectionError:
            return "Je n'arrive pas à me connecter à Ollama. Vérifiez qu'il est démarré."
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return "Une erreur technique m'empêche de répondre."
    
    def check_health(self):
        """Vérifie si Ollama est accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False