#!/bin/bash

echo "========================================="
echo "   Installation Assistant Vocal GUI"
echo "========================================="

# Créer environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv assistant_env
source assistant_env/bin/activate

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install pyaudio numpy vosk requests gtts pygame

# Télécharger le modèle Vosk
echo "📥 Téléchargement du modèle Vosk..."
python3 -c "
import os
import urllib.request
import zipfile

if not os.path.exists('models/vosk-model-small-fr-0.22'):
    print('Téléchargement...')
    os.makedirs('models', exist_ok=True)
    url = 'https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip'
    urllib.request.urlretrieve(url, 'models/model.zip')
    with zipfile.ZipFile('models/model.zip', 'r') as zip_ref:
        zip_ref.extractall('models')
    os.remove('models/model.zip')
    print('✅ Modèle téléchargé')
"

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Pour lancer l'assistant:"
echo "  source assistant_env/bin/activate"
echo "  python3 assistant_vocal.py"