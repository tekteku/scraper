#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'Installation Automatique
Système d'Estimation Matériaux Tunisiens
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class AutoInstaller:
    def __init__(self):
        self.os_type = platform.system()
        self.python_version = sys.version_info
        self.errors = []
        self.success_steps = []
        
    def print_header(self):
        print("=" * 70)
        print("🏗️ INSTALLATION AUTOMATIQUE")
        print("   Système d'Estimation Matériaux Tunisiens")
        print("=" * 70)
        print(f"OS détecté: {self.os_type}")
        print(f"Python: {self.python_version.major}.{self.python_version.minor}")
        print("=" * 70)
    
    def check_python_version(self):
        """Vérifie la version de Python"""
        print("🐍 Vérification version Python...")
        
        if self.python_version.major < 3 or self.python_version.minor < 8:
            self.errors.append("Python 3.8+ requis")
            print("❌ Python 3.8+ requis")
            return False
        
        print(f"✅ Python {self.python_version.major}.{self.python_version.minor} OK")
        self.success_steps.append("Python version OK")
        return True
    
    def check_git(self):
        """Vérifie si Git est installé"""
        print("📦 Vérification Git...")
        
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Git installé: {result.stdout.strip()}")
                self.success_steps.append("Git disponible")
                return True
            else:
                self.errors.append("Git non trouvé")
                print("❌ Git non installé")
                return False
        except FileNotFoundError:
            self.errors.append("Git non installé")
            print("❌ Git non trouvé - Installer depuis https://git-scm.com/")
            return False
    
    def create_virtual_environment(self):
        """Crée l'environnement virtuel"""
        print("🔧 Création environnement virtuel...")
        
        venv_path = Path("venv")
        if venv_path.exists():
            print("✅ Environnement virtuel existe déjà")
            self.success_steps.append("Venv existe")
            return True
        
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                          check=True)
            print("✅ Environnement virtuel créé")
            self.success_steps.append("Venv créé")
            return True
        except subprocess.CalledProcessError:
            self.errors.append("Échec création venv")
            print("❌ Échec création environnement virtuel")
            return False
    
    def get_pip_command(self):
        """Retourne la commande pip selon l'OS"""
        if self.os_type == "Windows":
            return os.path.join("venv", "Scripts", "pip")
        else:
            return os.path.join("venv", "bin", "pip")
    
    def get_python_command(self):
        """Retourne la commande python selon l'OS"""
        if self.os_type == "Windows":
            return os.path.join("venv", "Scripts", "python")
        else:
            return os.path.join("venv", "bin", "python")
    
    def install_requirements(self):
        """Installe les dépendances"""
        print("📚 Installation des dépendances...")
        
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip
        try:
            subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], 
                          check=True)
            print("✅ Pip mis à jour")
        except subprocess.CalledProcessError:
            print("⚠️ Impossible de mettre à jour pip")
        
        # Install requirements
        if Path("requirements.txt").exists():
            try:
                subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], 
                              check=True)
                print("✅ Dépendances installées")
                self.success_steps.append("Requirements installés")
                return True
            except subprocess.CalledProcessError:
                self.errors.append("Échec installation requirements")
                print("❌ Échec installation dépendances")
                return False
        else:
            self.errors.append("requirements.txt manquant")
            print("❌ Fichier requirements.txt non trouvé")
            return False
    
    def install_playwright(self):
        """Installe les navigateurs Playwright"""
        print("🌐 Installation navigateurs Playwright...")
        
        python_cmd = self.get_python_command()
        
        try:
            subprocess.run([python_cmd, '-m', 'playwright', 'install'], 
                          check=True)
            print("✅ Navigateurs Playwright installés")
            self.success_steps.append("Playwright installé")
            return True
        except subprocess.CalledProcessError:
            self.errors.append("Échec installation Playwright")
            print("❌ Échec installation navigateurs Playwright")
            return False
    
    def test_installation(self):
        """Teste l'installation"""
        print("🧪 Test de l'installation...")
        
        python_cmd = self.get_python_command()
        
        test_imports = [
            "import fastapi",
            "import streamlit", 
            "import pandas",
            "import playwright",
            "print('✅ Tous les imports OK!')"
        ]
        
        test_script = "; ".join(test_imports)
        
        try:
            result = subprocess.run([python_cmd, '-c', test_script], 
                                  capture_output=True, text=True, check=True)
            print("✅ Test imports réussi")
            self.success_steps.append("Imports testés")
            return True
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Test imports échoué: {e.stderr}")
            print(f"❌ Test imports échoué: {e.stderr}")
            return False
    
    def show_next_steps(self):
        """Affiche les prochaines étapes"""
        print("\n" + "=" * 70)
        print("🎉 INSTALLATION TERMINÉE")
        print("=" * 70)
        
        if self.os_type == "Windows":
            activate_cmd = "venv\\Scripts\\activate"
        else:
            activate_cmd = "source venv/bin/activate"
        
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("=" * 30)
        print(f"1. Activer l'environnement: {activate_cmd}")
        print("2. Lancer l'API: python llm_api_server.py")
        print("3. Lancer le dashboard: streamlit run materials_dashboard.py")
        print("\n🌐 ACCÈS:")
        print("   Dashboard: http://localhost:8501")
        print("   API: http://localhost:8000")
        print("   Documentation: http://localhost:8000/docs")
        
        print(f"\n✅ Étapes réussies: {len(self.success_steps)}")
        for step in self.success_steps:
            print(f"   ✓ {step}")
        
        if self.errors:
            print(f"\n❌ Erreurs: {len(self.errors)}")
            for error in self.errors:
                print(f"   ✗ {error}")
    
    def run_installation(self):
        """Lance l'installation complète"""
        self.print_header()
        
        steps = [
            ("Vérification Python", self.check_python_version),
            ("Vérification Git", self.check_git),
            ("Création venv", self.create_virtual_environment),
            ("Installation dépendances", self.install_requirements),
            ("Installation Playwright", self.install_playwright),
            ("Test installation", self.test_installation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Arrêt sur: {step_name}")
                break
            print(f"✅ {step_name} terminé")
        
        self.show_next_steps()

def main():
    """Fonction principale"""
    installer = AutoInstaller()
    installer.run_installation()

if __name__ == "__main__":
    main()
