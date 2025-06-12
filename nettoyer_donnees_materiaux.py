#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Nettoyage Complet des Données de Matériaux
Optimise l'espace disque et organise les fichiers de scraping
"""

import os
import shutil
import json
import pandas as pd
from datetime import datetime
import glob

class MaterialsDataCleaner:
    def __init__(self):
        self.base_path = r"c:\Users\TaherCh\Downloads\SCRAPER"
        self.total_freed = 0
        self.files_deleted = 0
        self.files_kept = 0
        self.report = {
            "date_nettoyage": datetime.now().isoformat(),
            "actions_effectuees": [],
            "espace_libere_mb": 0,
            "fichiers_supprimes": 0,
            "fichiers_conserves": 0
        }
    
    def get_file_size_mb(self, filepath):
        """Retourne la taille d'un fichier en MB"""
        try:
            return os.path.getsize(filepath) / (1024 * 1024)
        except:
            return 0
    
    def log_action(self, action, details=""):
        """Enregistre une action dans le rapport"""
        self.report["actions_effectuees"].append({
            "action": action,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        print(f"✅ {action}: {details}")
    
    def nettoyer_donnees_brutes_materiaux(self):
        """Nettoie les données brutes de matériaux (garde seulement les plus récentes)"""
        print("🧹 Nettoyage des données brutes de matériaux...")
        
        raw_folder = os.path.join(self.base_path, "materials_data", "raw")
        if not os.path.exists(raw_folder):
            return
        
        # Trouve tous les fichiers de données brutes
        csv_files = glob.glob(os.path.join(raw_folder, "*_raw_*.csv"))
        json_files = glob.glob(os.path.join(raw_folder, "*_raw_*.json"))
        
        # Trie par date (garde seulement les 2 plus récents de chaque type)
        csv_files.sort(key=os.path.getmtime, reverse=True)
        json_files.sort(key=os.path.getmtime, reverse=True)
        
        # Supprime les anciens fichiers CSV
        for file_to_delete in csv_files[2:]:  # Garde les 2 plus récents
            size_mb = self.get_file_size_mb(file_to_delete)
            os.remove(file_to_delete)
            self.total_freed += size_mb
            self.files_deleted += 1
            self.log_action("Suppression CSV ancien", os.path.basename(file_to_delete))
        
        # Supprime les anciens fichiers JSON
        for file_to_delete in json_files[2:]:  # Garde les 2 plus récents
            size_mb = self.get_file_size_mb(file_to_delete)
            os.remove(file_to_delete)
            self.total_freed += size_mb
            self.files_deleted += 1
            self.log_action("Suppression JSON ancien", os.path.basename(file_to_delete))
    
    def nettoyer_logs_materiaux(self):
        """Nettoie les fichiers de logs anciens"""
        print("📝 Nettoyage des fichiers de logs...")
        
        log_files = glob.glob(os.path.join(self.base_path, "*.log"))
        
        # Supprime les logs anciens (garde seulement les 3 plus récents)
        log_files.sort(key=os.path.getmtime, reverse=True)
        
        for log_file in log_files[3:]:
            size_mb = self.get_file_size_mb(log_file)
            os.remove(log_file)
            self.total_freed += size_mb
            self.files_deleted += 1
            self.log_action("Suppression log ancien", os.path.basename(log_file))
    
    def nettoyer_rapports_anciens(self):
        """Nettoie les anciens rapports et analyses"""
        print("📊 Nettoyage des rapports anciens...")
        
        # Patterns de fichiers à nettoyer
        patterns = [
            "RAPPORT_*.txt",
            "rapport_*.txt", 
            "comparaison_*.csv",
            "materials_report_*.txt",
            "CERTIFICATION_REPORT_*.txt",
            "DEMO_REPORT_*.txt"
        ]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(self.base_path, pattern))
            files.sort(key=os.path.getmtime, reverse=True)
            
            # Garde seulement les 2 plus récents de chaque type
            for file_to_delete in files[2:]:
                size_mb = self.get_file_size_mb(file_to_delete)
                os.remove(file_to_delete)
                self.total_freed += size_mb
                self.files_deleted += 1
                self.log_action("Suppression rapport ancien", os.path.basename(file_to_delete))
    
    def nettoyer_duplicats_materiaux(self):
        """Supprime les fichiers en double de matériaux"""
        print("🔍 Recherche et suppression des doublons...")
        
        # Cherche les fichiers CSV similaires
        csv_files = glob.glob(os.path.join(self.base_path, "*.csv"))
        
        # Groupe par nom de base (sans timestamp)
        file_groups = {}
        for csv_file in csv_files:
            base_name = os.path.basename(csv_file)
            # Extrait le nom sans timestamp
            if "_20250611" in base_name:
                key = base_name.split("_20250611")[0]
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append(csv_file)
        
        # Garde seulement le plus récent de chaque groupe
        for group_name, files in file_groups.items():
            if len(files) > 1:
                files.sort(key=os.path.getmtime, reverse=True)
                for file_to_delete in files[1:]:  # Garde le plus récent
                    size_mb = self.get_file_size_mb(file_to_delete)
                    os.remove(file_to_delete)
                    self.total_freed += size_mb
                    self.files_deleted += 1
                    self.log_action("Suppression doublon", os.path.basename(file_to_delete))
    
    def optimiser_json_organisees(self):
        """Optimise les données JSON organisées (compresse les gros fichiers)"""
        print("📦 Optimisation des données JSON organisées...")
        
        json_folder = os.path.join(self.base_path, "DONNEES_JSON_ORGANISEES", "02_PROPRIETES_IMMOBILIERES")
        if not os.path.exists(json_folder):
            return
        
        # Supprime les fichiers JSON de pages individuelles (garde seulement les consolidés)
        page_files = glob.glob(os.path.join(json_folder, "*_page*.json"))
        
        for page_file in page_files:
            size_mb = self.get_file_size_mb(page_file)
            os.remove(page_file)
            self.total_freed += size_mb
            self.files_deleted += 1
            self.log_action("Suppression page JSON", os.path.basename(page_file))
    
    def nettoyer_fichiers_temporaires(self):
        """Nettoie les fichiers temporaires"""
        print("🗑️ Suppression des fichiers temporaires...")
        
        temp_patterns = [
            "*.tmp",
            "*.temp", 
            "*~",
            "*.bak",
            "__pycache__",
            ".pytest_cache"
        ]
        
        for pattern in temp_patterns:
            if pattern in ["__pycache__", ".pytest_cache"]:
                # Supprime les dossiers
                for root, dirs, files in os.walk(self.base_path):
                    for dir_name in dirs:
                        if dir_name == pattern:
                            dir_path = os.path.join(root, dir_name)
                            shutil.rmtree(dir_path)
                            self.log_action("Suppression dossier cache", dir_name)
            else:
                # Supprime les fichiers
                files = glob.glob(os.path.join(self.base_path, "**", pattern), recursive=True)
                for file_to_delete in files:
                    size_mb = self.get_file_size_mb(file_to_delete)
                    os.remove(file_to_delete)
                    self.total_freed += size_mb
                    self.files_deleted += 1
                    self.log_action("Suppression temporaire", os.path.basename(file_to_delete))
    
    def compter_fichiers_restants(self):
        """Compte les fichiers conservés"""
        print("📊 Comptage des fichiers conservés...")
        
        # Compte les fichiers essentiels conservés
        essential_files = [
            "ESTIMATION_MATERIAUX_TUNISIE_20250611.csv",
            "CATALOG_ESTIMATION_BRICODIRECT_20250611.csv",
            "llm_api_server.py",
            "materials_dashboard.py",
            "README.md",
            "requirements.txt"
        ]
        
        for file_name in essential_files:
            file_path = os.path.join(self.base_path, file_name)
            if os.path.exists(file_path):
                self.files_kept += 1
        
        # Compte les fichiers dans DONNEES_JSON_ORGANISEES
        json_folder = os.path.join(self.base_path, "DONNEES_JSON_ORGANISEES")
        if os.path.exists(json_folder):
            for root, dirs, files in os.walk(json_folder):
                self.files_kept += len(files)
    
    def generer_rapport_final(self):
        """Génère le rapport final de nettoyage"""
        self.report["espace_libere_mb"] = round(self.total_freed, 2)
        self.report["fichiers_supprimes"] = self.files_deleted
        self.report["fichiers_conserves"] = self.files_kept
        
        # Sauvegarde le rapport
        rapport_file = os.path.join(self.base_path, "RAPPORT_NETTOYAGE.json")
        with open(rapport_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        # Affiche le résumé
        print("\n" + "="*50)
        print("📋 RAPPORT DE NETTOYAGE DES DONNÉES MATÉRIAUX")
        print("="*50)
        print(f"🗑️  Fichiers supprimés: {self.files_deleted}")
        print(f"📁 Fichiers conservés: {self.files_kept}")
        print(f"💾 Espace libéré: {self.total_freed:.1f} MB")
        print(f"📄 Rapport détaillé: RAPPORT_NETTOYAGE.json")
        print("="*50)
        
        return rapport_file
    
    def executer_nettoyage_complet(self):
        """Exécute le nettoyage complet"""
        print("🚀 DÉMARRAGE DU NETTOYAGE DES DONNÉES MATÉRIAUX")
        print("="*60)
        
        # Étapes de nettoyage
        self.nettoyer_donnees_brutes_materiaux()
        self.nettoyer_logs_materiaux()
        self.nettoyer_rapports_anciens()
        self.nettoyer_duplicats_materiaux()
        self.optimiser_json_organisees()
        self.nettoyer_fichiers_temporaires()
        self.compter_fichiers_restants()
        
        # Rapport final
        rapport_file = self.generer_rapport_final()
        
        print(f"\n✅ NETTOYAGE TERMINÉ AVEC SUCCÈS!")
        return rapport_file

def main():
    """Fonction principale"""
    cleaner = MaterialsDataCleaner()
    rapport = cleaner.executer_nettoyage_complet()
    
    print(f"\n🎉 Le nettoyage est terminé!")
    print(f"📊 Consultez {rapport} pour les détails")

if __name__ == "__main__":
    main()
