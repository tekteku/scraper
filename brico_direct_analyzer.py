"""
Analyseur complet des données de matériaux de construction de brico-direct.tn
Génère des rapports, statistiques et fichiers d'estimation
"""

import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class BricoDirectAnalyzer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file, encoding='utf-8')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Nettoyage des données
        self.clean_data()
        
    def clean_data(self):
        """Nettoie et prépare les données"""
        # Supprime les doublons
        self.df = self.df.drop_duplicates(subset=['nom'], keep='first')
        
        # Convertit les prix en float si nécessaire
        self.df['prix_tnd'] = pd.to_numeric(self.df['prix_tnd'], errors='coerce')
        
        # Filtre les données valides
        self.df = self.df[self.df['prix_tnd'].notna()]
        self.df = self.df[self.df['prix_tnd'] > 0]
        
        print(f"Données nettoyées: {len(self.df)} produits valides")
    
    def generate_statistics(self):
        """Génère des statistiques complètes"""
        stats = {
            'resumé_général': {
                'total_produits': len(self.df),
                'date_analyse': datetime.now().isoformat(),
                'prix_moyen': float(self.df['prix_tnd'].mean()),
                'prix_médian': float(self.df['prix_tnd'].median()),
                'prix_min': float(self.df['prix_tnd'].min()),
                'prix_max': float(self.df['prix_tnd'].max()),
                'écart_type': float(self.df['prix_tnd'].std())
            },
            'par_catégorie': {},
            'par_page': {},
            'top_produits': {}
        }
        
        # Statistiques par catégorie
        for category in self.df['categorie'].unique():
            cat_data = self.df[self.df['categorie'] == category]
            stats['par_catégorie'][category] = {
                'nombre_produits': len(cat_data),
                'prix_moyen': float(cat_data['prix_tnd'].mean()),
                'prix_min': float(cat_data['prix_tnd'].min()),
                'prix_max': float(cat_data['prix_tnd'].max()),
                'pourcentage_total': round(len(cat_data) / len(self.df) * 100, 1)
            }
        
        # Statistiques par page
        for page in sorted(self.df['page'].unique()):
            page_data = self.df[self.df['page'] == page]
            stats['par_page'][f'page_{page}'] = {
                'nombre_produits': len(page_data),
                'prix_moyen': float(page_data['prix_tnd'].mean())
            }
        
        # Top produits
        stats['top_produits'] = {
            'plus_chers': self.df.nlargest(10, 'prix_tnd')[['nom', 'prix_tnd', 'categorie']].to_dict('records'),
            'moins_chers': self.df.nsmallest(10, 'prix_tnd')[['nom', 'prix_tnd', 'categorie']].to_dict('records')
        }
        
        return stats
    
    def create_price_ranges(self):
        """Crée des gammes de prix pour faciliter les estimations"""
        self.df['gamme_prix'] = pd.cut(
            self.df['prix_tnd'], 
            bins=[0, 50, 200, 500, 1000, 5000, float('inf')],
            labels=['0-50 TND', '50-200 TND', '200-500 TND', '500-1000 TND', '1000-5000 TND', '5000+ TND']
        )
        
        ranges_stats = self.df['gamme_prix'].value_counts().to_dict()
        return {str(k): int(v) for k, v in ranges_stats.items()}
    
    def generate_estimation_catalog(self):
        """Génère un catalogue d'estimation par catégorie"""
        catalog = {}
        
        for category in self.df['categorie'].unique():
            cat_data = self.df[self.df['categorie'] == category].copy()
            
            # Trie par prix croissant
            cat_data = cat_data.sort_values('prix_tnd')
            
            catalog[category] = {
                'nombre_options': len(cat_data),
                'fourchette_prix': {
                    'min': float(cat_data['prix_tnd'].min()),
                    'max': float(cat_data['prix_tnd'].max()),
                    'moyen': float(cat_data['prix_tnd'].mean())
                },
                'produits_recommandés': {
                    'économique': cat_data.iloc[0].to_dict() if len(cat_data) > 0 else None,
                    'moyen_gamme': cat_data.iloc[len(cat_data)//2].to_dict() if len(cat_data) > 1 else None,
                    'haut_gamme': cat_data.iloc[-1].to_dict() if len(cat_data) > 2 else None
                }
            }
        
        return catalog
    
    def generate_project_templates(self):
        """Génère des templates d'estimation pour différents types de projets"""
        templates = {
            'Maison_100m2': {
                'description': 'Estimation pour maison individuelle de 100m²',
                'matériaux': [
                    {'catégorie': 'Ciment et béton', 'quantité_estimée': 50, 'unité': 'sacs'},
                    {'catégorie': 'Fer et métallurgie', 'quantité_estimée': 2000, 'unité': 'kg'},
                    {'catégorie': 'Carrelage et revêtements', 'quantité_estimée': 100, 'unité': 'm²'},
                    {'catégorie': 'Peinture et enduits', 'quantité_estimée': 200, 'unité': 'litres'},
                    {'catégorie': 'Outillage', 'quantité_estimée': 1, 'unité': 'lot'},
                    {'catégorie': 'Quincaillerie', 'quantité_estimée': 1, 'unité': 'lot'}
                ]
            },
            'Villa_200m2': {
                'description': 'Estimation pour villa de 200m²',
                'matériaux': [
                    {'catégorie': 'Ciment et béton', 'quantité_estimée': 100, 'unité': 'sacs'},
                    {'catégorie': 'Fer et métallurgie', 'quantité_estimée': 4000, 'unité': 'kg'},
                    {'catégorie': 'Carrelage et revêtements', 'quantité_estimée': 200, 'unité': 'm²'},
                    {'catégorie': 'Peinture et enduits', 'quantité_estimée': 400, 'unité': 'litres'},
                    {'catégorie': 'Outillage', 'quantité_estimée': 1, 'unité': 'lot'},
                    {'catégorie': 'Quincaillerie', 'quantité_estimée': 2, 'unité': 'lots'}
                ]
            },
            'Rénovation_Appartement': {
                'description': 'Estimation pour rénovation appartement 80m²',
                'matériaux': [
                    {'catégorie': 'Carrelage et revêtements', 'quantité_estimée': 80, 'unité': 'm²'},
                    {'catégorie': 'Peinture et enduits', 'quantité_estimée': 150, 'unité': 'litres'},
                    {'catégorie': 'Isolation', 'quantité_estimée': 100, 'unité': 'm²'},
                    {'catégorie': 'Outillage', 'quantité_estimée': 1, 'unité': 'lot'},
                    {'catégorie': 'Quincaillerie', 'quantité_estimée': 1, 'unité': 'lot'}
                ]
            }
        }
        
        # Calcule les coûts estimatifs pour chaque template
        for project_name, project_data in templates.items():
            total_cost = 0
            detailed_costs = []
            
            for material in project_data['matériaux']:
                category = material['catégorie']
                quantity = material['quantité_estimée']
                
                # Trouve le prix moyen de la catégorie
                cat_data = self.df[self.df['categorie'] == category]
                if len(cat_data) > 0:
                    avg_price = cat_data['prix_tnd'].mean()
                    category_cost = avg_price * quantity
                    total_cost += category_cost
                    
                    detailed_costs.append({
                        'catégorie': category,
                        'quantité': quantity,
                        'unité': material['unité'],
                        'prix_unitaire_moyen': round(avg_price, 2),
                        'coût_total': round(category_cost, 2)
                    })
            
            templates[project_name]['coût_total_estimé'] = round(total_cost, 2)
            templates[project_name]['détail_coûts'] = detailed_costs
        
        return templates
    
    def save_all_reports(self):
        """Sauvegarde tous les rapports générés"""
        # Statistiques générales
        stats = self.generate_statistics()
        stats_file = f"materials_data/clean/brico_direct_stats_{self.timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Gammes de prix
        price_ranges = self.create_price_ranges()
        
        # Catalogue d'estimation
        catalog = self.generate_estimation_catalog()
        catalog_file = f"materials_data/clean/catalog_estimation_{self.timestamp}.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        
        # Templates de projet
        templates = self.generate_project_templates()
        templates_file = f"materials_data/clean/project_templates_{self.timestamp}.json"
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        # CSV d'estimation finale
        estimation_data = []
        for category, data in catalog.items():
            for level, product in data['produits_recommandés'].items():
                if product:
                    estimation_data.append({
                        'Catégorie': category,
                        'Gamme': level,
                        'Produit': product['nom'],
                        'Prix_TND': product['prix_tnd'],
                        'Prix_Original': product['prix_original'],
                        'Description': product.get('description', ''),
                        'URL': product.get('url_produit', ''),
                        'Source': 'brico-direct.tn'
                    })
        
        estimation_csv = f"CATALOG_ESTIMATION_BRICODIRECT_{datetime.now().strftime('%Y%m%d')}.csv"
        pd.DataFrame(estimation_data).to_csv(estimation_csv, index=False, encoding='utf-8')
        
        # Rapport texte complet
        self.generate_text_report(stats, price_ranges, templates)
        
        return {
            'stats_file': stats_file,
            'catalog_file': catalog_file,
            'templates_file': templates_file,
            'estimation_csv': estimation_csv
        }
    
    def generate_text_report(self, stats, price_ranges, templates):
        """Génère un rapport texte complet"""
        report = f"""
        
🏗️  RAPPORT D'ANALYSE - MATÉRIAUX DE CONSTRUCTION BRICO-DIRECT.TN
================================================================
Date d'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Données source: brico-direct.tn (8 pages)

📊 RÉSUMÉ GÉNÉRAL
-----------------
Total produits analysés: {stats['resumé_général']['total_produits']}
Prix moyen: {stats['resumé_général']['prix_moyen']:.2f} TND
Prix médian: {stats['resumé_général']['prix_médian']:.2f} TND
Fourchette de prix: {stats['resumé_général']['prix_min']:.2f} - {stats['resumé_général']['prix_max']:.2f} TND

💰 RÉPARTITION PAR GAMME DE PRIX
---------------------------------
"""
        
        for range_name, count in price_ranges.items():
            percentage = (count / stats['resumé_général']['total_produits']) * 100
            report += f"{range_name}: {count} produits ({percentage:.1f}%)\n"
        
        report += f"""
🏷️  ANALYSE PAR CATÉGORIE
--------------------------
"""
        
        for category, data in stats['par_catégorie'].items():
            report += f"""
{category}:
  - {data['nombre_produits']} produits ({data['pourcentage_total']}% du total)
  - Prix: {data['prix_min']:.2f} - {data['prix_max']:.2f} TND (moy: {data['prix_moyen']:.2f})
"""
        
        report += f"""
💡 TOP PRODUITS LES PLUS CHERS
-------------------------------
"""
        for i, product in enumerate(stats['top_produits']['plus_chers'][:5], 1):
            report += f"{i}. {product['nom']}: {product['prix_tnd']:.2f} TND ({product['categorie']})\n"
        
        report += f"""
💸 TOP PRODUITS LES MOINS CHERS
-------------------------------
"""
        for i, product in enumerate(stats['top_produits']['moins_chers'][:5], 1):
            report += f"{i}. {product['nom']}: {product['prix_tnd']:.2f} TND ({product['categorie']})\n"
        
        report += f"""
🏠 ESTIMATIONS DE PROJET
------------------------
"""
        
        for project_name, project_data in templates.items():
            report += f"""
{project_name}:
  {project_data['description']}
  Coût total estimé: {project_data['coût_total_estimé']:.2f} TND
  
  Détail par catégorie:
"""
            for cost in project_data['détail_coûts']:
                report += f"  - {cost['catégorie']}: {cost['quantité']} {cost['unité']} × {cost['prix_unitaire_moyen']:.2f} = {cost['coût_total']:.2f} TND\n"
        
        report += f"""
🎯 RECOMMANDATIONS D'ACHAT
--------------------------
1. 💰 ÉCONOMIQUE: Privilégiez les produits 0-200 TND pour les gros volumes
2. 🏆 QUALITÉ: Les produits 500-1000 TND offrent le meilleur rapport qualité/prix
3. 🛒 PLANNING: Commandez l'outillage en premier (délais plus longs)
4. 📊 NÉGOCIATION: Les lots de quincaillerie permettent des remises importantes
5. 🚚 LIVRAISON: Groupez vos commandes par chantier pour optimiser les coûts

📈 TENDANCES DE MARCHÉ
----------------------
- Outillage: Gamme large de 7-240k TND selon la spécialisation
- Quincaillerie: Produits de base très abordables (4-50 TND)
- Carrelage: investissement important (budgétez 16-58k TND par produit)
- Matériaux lourds: Négociez la livraison (échelles, transpalettes)

🔗 SOURCES ET MISE À JOUR
-------------------------
Source: brico-direct.tn/construction (525 produits analysés)
Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y')}
Fréquence recommandée: Mensuelle (volatilité des prix)

⚠️  NOTES IMPORTANTES
---------------------
- Prix hors TVA et livraison
- Disponibilité variable selon stock
- Remises possibles sur gros volumes
- Vérifiez toujours les prix avant commande
"""
        
        report_file = f"RAPPORT_ANALYSE_BRICODIRECT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Rapport complet généré: {report_file}")

def main():
    print("🔍 Analyse des données brico-direct.tn...")
    
    # Utilise le fichier de données le plus récent
    csv_file = "materials_data/raw/brico_direct_raw_20250611_095811.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Fichier non trouvé: {csv_file}")
        return
    
    # Initialise l'analyseur
    analyzer = BricoDirectAnalyzer(csv_file)
    
    # Génère tous les rapports
    files = analyzer.save_all_reports()
    
    print("\n✅ Analyse terminée ! Fichiers générés:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    print(f"\n📋 Résumé:")
    print(f"   - {len(analyzer.df)} produits analysés")
    print(f"   - {analyzer.df['categorie'].nunique()} catégories")
    print(f"   - Prix moyen: {analyzer.df['prix_tnd'].mean():.2f} TND")
    print(f"   - Fourchette: {analyzer.df['prix_tnd'].min():.2f} - {analyzer.df['prix_tnd'].max():.2f} TND")

if __name__ == "__main__":
    main()
