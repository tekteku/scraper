#!/usr/bin/env python3
"""
🚀 Lanceur du Tableau de Bord Matériaux
Script pour démarrer l'interface web Streamlit
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Timer

def check_streamlit():
    """Vérifier si Streamlit est disponible"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def start_dashboard():
    """Démarrer le tableau de bord"""
    
    print("🚀 LANCEMENT DU TABLEAU DE BORD MATÉRIAUX")
    print("=" * 50)
    
    # Vérifier Streamlit
    if not check_streamlit():
        print("❌ Streamlit non installé. Installation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
    
    # Vérifier les données
    data_file = "ESTIMATION_MATERIAUX_TUNISIE_20250611.csv"
    if not os.path.exists(data_file):
        print(f"❌ Fichier de données manquant: {data_file}")
        print("💡 Exécutez d'abord 'python demo_finale.py' pour générer les données")
        return False
    
    print(f"✅ Données trouvées: {data_file}")
    print(f"✅ Streamlit disponible")
    
    # Informations de lancement
    print(f"\n📊 Le tableau de bord va s'ouvrir dans votre navigateur...")
    print(f"🌐 URL: http://localhost:8501")
    print(f"⏹️ Pour arrêter: Ctrl+C dans ce terminal")
    
    # Ouvrir le navigateur après 3 secondes
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open('http://localhost:8501')
        except:
            pass
    
    Timer(3.0, open_browser).start()
    
    # Lancer Streamlit
    try:
        print(f"\n🎯 Lancement du serveur Streamlit...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "materials_dashboard.py",
            "--server.port=8501",
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print(f"\n⛔ Tableau de bord arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = start_dashboard()
    if not success:
        print(f"\n💡 ALTERNATIVES:")
        print(f"   - Exécutez: streamlit run materials_dashboard.py")
        print(f"   - Ou visitez: http://localhost:8501")
        sys.exit(1)
