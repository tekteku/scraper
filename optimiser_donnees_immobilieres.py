#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nettoyage Avancé des Données JSON Immobilières
Compresse et optimise les gros fichiers JSON de propriétés
"""

import os
import json
import gzip
import shutil
from datetime import datetime

class PropertyDataOptimizer:
    def __init__(self):
        self.base_path = r"c:\Users\TaherCh\Downloads\SCRAPER"
        self.properties_folder = os.path.join(self.base_path, "DONNEES_JSON_ORGANISEES", "02_PROPRIETES_IMMOBILIERES")
        self.space_saved = 0
        
    def compress_large_json(self, file_path, size_limit_mb=1):
        """Compresse les fichiers JSON volumineux"""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size_mb > size_limit_mb:
            # Créer version compressée
            compressed_path = file_path + '.gz'
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Supprimer l'original
            os.remove(file_path)
            
            # Calculer l'espace économisé
            compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
            saved_mb = file_size_mb - compressed_size_mb
            self.space_saved += saved_mb
            
            print(f"✅ Compressé: {os.path.basename(file_path)} ({file_size_mb:.1f}MB → {compressed_size_mb:.1f}MB)")
            return True
        return False
    
    def create_summary_file(self):
        """Crée un fichier résumé des propriétés au lieu de garder tous les détails"""
        summary_data = {
            "metadata": {
                "date_creation": datetime.now().isoformat(),
                "description": "Résumé optimisé des propriétés immobilières tunisiennes",
                "total_proprietes": 0,
                "sources": []
            },
            "statistiques_generales": {},
            "echantillons": []
        }
        
        # Parcourt tous les fichiers JSON de propriétés
        json_files = []
        if os.path.exists(self.properties_folder):
            for file in os.listdir(self.properties_folder):
                if file.endswith('.json') and 'proprietes' in file:
                    json_files.append(os.path.join(self.properties_folder, file))
        
        total_properties = 0
        sources = set()
        sample_properties = []
        
        for json_file in json_files[:3]:  # Limite à 3 fichiers pour éviter la surcharge
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    properties = data
                elif isinstance(data, dict) and 'proprietes' in data:
                    properties = data['proprietes']
                else:
                    continue
                
                total_properties += len(properties)
                
                # Prend quelques échantillons
                for prop in properties[:5]:  # 5 échantillons par fichier
                    if isinstance(prop, dict):
                        sample_properties.append({
                            "titre": prop.get('titre', '')[:100],
                            "prix": prop.get('prix', ''),
                            "localisation": prop.get('localisation', ''),
                            "type": prop.get('type', ''),
                            "source": prop.get('source', os.path.basename(json_file))
                        })
                        sources.add(prop.get('source', os.path.basename(json_file)))
                
            except Exception as e:
                print(f"⚠️ Erreur lecture {json_file}: {e}")
        
        summary_data["metadata"]["total_proprietes"] = total_properties
        summary_data["metadata"]["sources"] = list(sources)
        summary_data["echantillons"] = sample_properties[:20]  # Limite à 20 échantillons
        
        # Sauvegarde le résumé
        summary_path = os.path.join(self.properties_folder, "resume_proprietes_optimise.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Résumé créé: {total_properties} propriétés résumées")
        return summary_path
    
    def optimize_all_property_files(self):
        """Optimise tous les fichiers de propriétés"""
        print("🏠 Optimisation des données immobilières...")
        
        if not os.path.exists(self.properties_folder):
            print("❌ Dossier propriétés non trouvé")
            return
        
        # Crée d'abord le résumé
        self.create_summary_file()
        
        # Compresse ou supprime les gros fichiers
        for file in os.listdir(self.properties_folder):
            if file.endswith('.json') and file != "resume_proprietes_optimise.json":
                file_path = os.path.join(self.properties_folder, file)
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                
                if file_size_mb > 0.5:  # Fichiers de plus de 500KB
                    if 'proprietes_consolidees_resume' in file:
                        # Garde ce fichier important
                        print(f"📁 Conservé: {file} ({file_size_mb:.1f}MB)")
                    else:
                        # Supprime les gros fichiers redondants
                        os.remove(file_path)
                        self.space_saved += file_size_mb
                        print(f"🗑️ Supprimé: {file} ({file_size_mb:.1f}MB)")
        
        print(f"💾 Espace économisé: {self.space_saved:.1f}MB")

def main():
    """Fonction principale"""
    print("🚀 OPTIMISATION DES DONNÉES IMMOBILIÈRES")
    print("="*50)
    
    optimizer = PropertyDataOptimizer()
    optimizer.optimize_all_property_files()
    
    print("\n✅ Optimisation terminée!")

if __name__ == "__main__":
    main()
