#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage automatisé des données
Système d'estimation matériaux construction - Tunisie
"""

import os
import shutil
import glob
from datetime import datetime
import json

def nettoyer_donnees_projet():
    """Nettoie les données du projet en gardant l'essentiel"""
    
    base_path = "c:\\Users\\TaherCh\\Downloads\\SCRAPER"
    
    print("🧹 DÉBUT DU NETTOYAGE DES DONNÉES")
    print("=" * 50)
    
    # 1. Fichiers temporaires et logs
    print("\n1️⃣ Suppression des fichiers temporaires...")
    
    temp_patterns = [
        "*.log",
        "*.tmp", 
        "*.temp",
        "*~",
        "get-pip.py",
        "*.pyc",
        "__pycache__"
    ]
    
    for pattern in temp_patterns:
        files = glob.glob(os.path.join(base_path, pattern))
        for file in files:
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"   ✅ Supprimé: {os.path.basename(file)}")
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    print(f"   ✅ Dossier supprimé: {os.path.basename(file)}")
            except Exception as e:
                print(f"   ❌ Erreur {file}: {e}")
    
    # 2. Fichiers doublons CSV
    print("\n2️⃣ Nettoyage des doublons CSV...")
    
    csv_files = glob.glob(os.path.join(base_path, "*.csv"))
    csv_keep = [
        "ESTIMATION_MATERIAUX_TUNISIE_20250611.csv",
        "CATALOG_ESTIMATION_BRICODIRECT_20250611.csv"
    ]
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        if filename not in csv_keep:
            os.remove(csv_file)
            print(f"   ✅ CSV supprimé: {filename}")
    
    # 3. Anciens fichiers de rapport
    print("\n3️⃣ Suppression des anciens rapports...")
    
    report_patterns = [
        "*_20250611_*.txt",
        "DEMO_REPORT_*.txt",
        "CERTIFICATION_REPORT_*.txt",
        "RAPPORT_*.txt",
        "rapport_*.txt",
        "materials_report_*.txt"
    ]
    
    for pattern in report_patterns:
        files = glob.glob(os.path.join(base_path, pattern))
        for file in files:
            os.remove(file)
            print(f"   ✅ Rapport supprimé: {os.path.basename(file)}")
    
    # 4. Nettoyage des données immobilières (garder résumé seulement)
    print("\n4️⃣ Optimisation données immobilières...")
    
    immo_folder = os.path.join(base_path, "DONNEES_JSON_ORGANISEES", "02_PROPRIETES_IMMOBILIERES")
    
    if os.path.exists(immo_folder):
        # Garder seulement les fichiers essentiels
        files_to_keep = [
            "proprietes_consolidees_resume.json",
            "proprietes_fi_dari_tn.json",
            "proprietes_remax_com_tn.json", 
            "proprietes_mubawab_tn.json",
            "proprietes_tecnocasa_tn.json"
        ]
        
        all_files = os.listdir(immo_folder)
        deleted_count = 0
        
        for file in all_files:
            if file not in files_to_keep:
                file_path = os.path.join(immo_folder, file)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Erreur {file}: {e}")
        
        print(f"   ✅ {deleted_count} fichiers immobiliers détaillés supprimés")
    
    # 5. Optimisation dossier raw data
    print("\n5️⃣ Nettoyage données brutes...")
    
    raw_folders = [
        os.path.join(base_path, "real_estate_data"),
        os.path.join(base_path, "materials_data", "raw")
    ]
    
    for folder in raw_folders:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"   ✅ Dossier supprimé: {os.path.basename(folder)}")
            except Exception as e:
                print(f"   ❌ Erreur {folder}: {e}")
    
    # 6. Anciens scripts de test
    print("\n6️⃣ Suppression scripts de test...")
    
    test_patterns = [
        "*_test.py",
        "*_example.py", 
        "check_*.py",
        "agentql_*.py",
        "firecrawl_*.py",
        "*_updated.py",
        "*_final.py",
        "*_helper*.py",
        "combine_*.py"
    ]
    
    for pattern in test_patterns:
        files = glob.glob(os.path.join(base_path, pattern))
        for file in files:
            os.remove(file)
            print(f"   ✅ Script test supprimé: {os.path.basename(file)}")
    
    # 7. Base de données temporaire
    print("\n7️⃣ Nettoyage bases de données...")
    
    db_files = glob.glob(os.path.join(base_path, "*.db"))
    for db_file in db_files:
        os.remove(db_file)
        print(f"   ✅ Base de données supprimée: {os.path.basename(db_file)}")

def calculer_espace_libere():
    """Calcule l'espace libéré après nettoyage"""
    base_path = "c:\\Users\\TaherCh\\Downloads\\SCRAPER"
    
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                total_size += size
                file_count += 1
            except:
                pass
    
    size_mb = total_size / (1024 * 1024)
    
    print(f"\n📊 RÉSULTAT DU NETTOYAGE:")
    print(f"   📁 Nombre de fichiers restants: {file_count}")
    print(f"   💾 Taille totale: {size_mb:.2f} MB")
    
    return size_mb, file_count

def creer_rapport_nettoyage():
    """Crée un rapport de nettoyage"""
    
    rapport = {
        "date_nettoyage": datetime.now().isoformat(),
        "version": "1.0",
        "fichiers_conserves": [
            "Scripts principaux (.py)",
            "Données essentielles JSON",
            "2 catalogues CSV principaux", 
            "Documentation (README, etc.)",
            "Résumés immobiliers consolidés"
        ],
        "fichiers_supprimes": [
            "Logs et fichiers temporaires",
            "Doublons CSV",
            "Anciens rapports", 
            "Données brutes détaillées",
            "Scripts de test",
            "Bases de données temporaires"
        ],
        "recommandations": [
            "Maintenir uniquement les fichiers essentiels",
            "Effectuer nettoyage hebdomadaire",
            "Utiliser .gitignore pour éviter accumulation"
        ]
    }
    
    with open("RAPPORT_NETTOYAGE.json", 'w', encoding='utf-8') as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    
    print("📋 Rapport de nettoyage créé: RAPPORT_NETTOYAGE.json")

if __name__ == "__main__":
    print("🚀 Lancement du nettoyage automatisé...")
    
    # Calcul taille avant
    print("📏 Calcul de la taille actuelle...")
    size_before, files_before = calculer_espace_libere()
    
    # Nettoyage
    nettoyer_donnees_projet()
    
    # Calcul taille après
    print("\n📏 Recalcul après nettoyage...")
    size_after, files_after = calculer_espace_libere()
    
    # Statistiques
    space_saved = size_before - size_after
    files_removed = files_before - files_after
    
    print(f"\n🎉 NETTOYAGE TERMINÉ!")
    print(f"   💾 Espace libéré: {space_saved:.2f} MB")
    print(f"   🗑️ Fichiers supprimés: {files_removed}")
    print(f"   📉 Réduction: {(space_saved/size_before)*100:.1f}%")
    
    # Rapport
    creer_rapport_nettoyage()
    
    print("\n✅ Projet optimisé pour GitHub!")
