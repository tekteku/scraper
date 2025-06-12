"""
Outil d'analyse et de visualisation des données de matériaux de construction
Génère des rapports complets pour l'estimation de coûts
"""

import json
import pandas as pd
from datetime import datetime
import os

class MaterialAnalyzer:
    def __init__(self, data_folder="materials_data"):
        self.data_folder = data_folder
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def load_latest_data(self):
        """Charge les dernières données disponibles"""
        raw_folder = os.path.join(self.data_folder, "raw")
        clean_folder = os.path.join(self.data_folder, "clean")
        
        # Trouve le fichier le plus récent
        csv_files = [f for f in os.listdir(raw_folder) if f.startswith("construction_materials") and f.endswith(".csv")]
        if not csv_files:
            print("Aucun fichier de données trouvé")
            return None
        
        latest_file = sorted(csv_files)[-1]
        csv_path = os.path.join(raw_folder, latest_file)
        
        self.df = pd.read_csv(csv_path)
        print(f"Données chargées: {len(self.df)} matériaux depuis {latest_file}")
        
        # Charge aussi les estimations
        estimates_files = [f for f in os.listdir(clean_folder) if f.startswith("project_estimates") and f.endswith(".json")]
        if estimates_files:
            latest_estimates = sorted(estimates_files)[-1]
            estimates_path = os.path.join(clean_folder, latest_estimates)
            with open(estimates_path, 'r', encoding='utf-8') as f:
                self.estimates = json.load(f)
        
        return self.df
    
    def generate_price_report(self):
        """Génère un rapport détaillé des prix"""
        print("\n" + "="*80)
        print("RAPPORT DÉTAILLÉ DES PRIX DES MATÉRIAUX DE CONSTRUCTION")
        print("="*80)
        
        # Statistiques générales
        print(f"\n📊 STATISTIQUES GÉNÉRALES")
        print(f"   Total matériaux analysés: {len(self.df)}")
        print(f"   Fourchette de prix: {self.df['prix'].min():.2f} - {self.df['prix'].max():.2f} TND")
        print(f"   Prix moyen: {self.df['prix'].mean():.2f} TND")
        
        # Analyse par catégorie
        print(f"\n🏗️ ANALYSE PAR CATÉGORIE")
        print("-" * 60)
        
        for category in self.df['categorie'].unique():
            cat_data = self.df[self.df['categorie'] == category]
            print(f"\n{category.upper().replace('_', ' ')}")
            print(f"   Nombre de produits: {len(cat_data)}")
            print(f"   Prix moyen: {cat_data['prix'].mean():.2f} TND")
            print(f"   Fourchette: {cat_data['prix'].min():.2f} - {cat_data['prix'].max():.2f} TND")
            
            # Top 3 des produits les plus chers de cette catégorie
            top_products = cat_data.nlargest(3, 'prix')
            print(f"   Produits les plus chers:")
            for idx, row in top_products.iterrows():
                print(f"     • {row['nom']}: {row['prix']} TND/{row['unite']}")
        
        # Analyse des fournisseurs
        print(f"\n🏪 ANALYSE PAR FOURNISSEUR")
        print("-" * 60)
        
        for supplier in self.df['fournisseur'].unique():
            sup_data = self.df[self.df['fournisseur'] == supplier]
            print(f"\n{supplier}")
            print(f"   Produits disponibles: {len(sup_data)}")
            print(f"   Prix moyen: {sup_data['prix'].mean():.2f} TND")
            
            # Disponibilité
            availability = sup_data['disponibilite'].value_counts()
            print(f"   Disponibilité: {dict(availability)}")
    
    def generate_project_estimates(self):
        """Affiche les estimations de projets"""
        if not hasattr(self, 'estimates'):
            print("Aucune estimation de projet disponible")
            return
        
        print(f"\n💰 ESTIMATIONS DE COÛTS POUR PROJETS TYPES")
        print("="*80)
        
        for project_name, project_data in self.estimates.items():
            print(f"\n🏠 {project_data['description'].upper()}")
            print(f"   Coût total estimé: {project_data['cout_total_tnd']:,.2f} TND")
            print(f"   Détail des matériaux:")
            
            for material, details in project_data['detail_materiaux'].items():
                print(f"     • {material}:")
                print(f"       - Prix unitaire: {details['prix_unitaire']} TND/{details['unite']}")
                print(f"       - Quantité: {details['quantite']} {details['unite']}")
                print(f"       - Coût total: {details['cout_total']:,.2f} TND")
    
    def generate_comparison_table(self):
        """Génère un tableau de comparaison des prix"""
        print(f"\n📋 TABLEAU COMPARATIF DES PRIX PRINCIPAUX")
        print("="*80)
        
        # Groupe par nom de base (sans le détail technique)
        material_groups = {}
        for idx, row in self.df.iterrows():
            base_name = row['nom'].split(' - ')[0]
            if base_name not in material_groups:
                material_groups[base_name] = []
            material_groups[base_name].append(row)
        
        for material_name, products in material_groups.items():
            if len(products) > 1:  # Seulement si plusieurs fournisseurs
                print(f"\n{material_name.upper()}")
                print("-" * 50)
                
                for product in products:
                    availability_icon = "✅" if product['disponibilite'] == "En stock" else "⚠️" if product['disponibilite'] == "Stock limité" else "📋"
                    print(f"   {availability_icon} {product['fournisseur']}: {product['prix']} TND/{product['unite']}")
                
                # Prix moyen et recommandation
                prices = [p['prix'] for p in products]
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                best_supplier = next(p['fournisseur'] for p in products if p['prix'] == min_price)
                
                print(f"   💡 Prix moyen: {avg_price:.2f} TND")
                print(f"   🏆 Meilleur prix: {best_supplier} ({min_price} TND)")
    
    def save_detailed_report(self):
        """Sauvegarde un rapport détaillé en fichier"""
        report_file = f"materials_report_{self.timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("RAPPORT COMPLET - MATÉRIAUX DE CONSTRUCTION TUNISIE\n")
            f.write("="*60 + "\n")
            f.write(f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n")
            
            # Recommandations pour économiser
            f.write("💡 CONSEILS POUR ÉCONOMISER:\n")
            f.write("-" * 40 + "\n")
            f.write("1. Comparer les prix entre fournisseurs (jusqu'à 20% d'écart)\n")
            f.write("2. Acheter en gros pour négocier des remises\n")
            f.write("3. Planifier les achats selon la disponibilité\n")
            f.write("4. Vérifier la qualité avant de choisir le moins cher\n\n")
            
            # Données détaillées
            f.write("DONNÉES DÉTAILLÉES:\n")
            f.write("-" * 40 + "\n")
            for idx, row in self.df.iterrows():
                f.write(f"• {row['nom']}\n")
                f.write(f"  Prix: {row['prix']} {row['devise']}/{row['unite']}\n")
                f.write(f"  Fournisseur: {row['fournisseur']}\n")
                f.write(f"  Disponibilité: {row['disponibilite']}\n")
                f.write(f"  Usage: {row['usage']}\n\n")
        
        print(f"\n📄 Rapport détaillé sauvegardé: {report_file}")
    
    def run_complete_analysis(self):
        """Exécute l'analyse complète"""
        if self.load_latest_data() is None:
            return
        
        self.generate_price_report()
        self.generate_project_estimates()
        self.generate_comparison_table()
        self.save_detailed_report()
        
        print(f"\n✅ Analyse terminée !")
        print(f"   - {len(self.df)} matériaux analysés")
        print(f"   - Rapport sauvegardé")
        print(f"   - Estimations de projets disponibles")

def main():
    analyzer = MaterialAnalyzer()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()
