#!/usr/bin/env python3
"""
Comparateur de Prix Multi-Sites pour Matériaux de Construction
Analyse et compare les prix entre différents fournisseurs tunisiens
"""

import pandas as pd
import json
from datetime import datetime
import numpy as np
from difflib import SequenceMatcher
import re

class MaterialPriceComparator:
    def __init__(self):
        self.data = None
        self.comparison_results = {}
        
    def load_data(self, csv_file=None, json_file=None):
        """Charger les données depuis CSV ou JSON"""
        if csv_file:
            self.data = pd.read_csv(csv_file)
        elif json_file:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.data = pd.DataFrame(data)
        else:
            print("❌ Aucun fichier de données fourni")
            return False
          print(f"✅ Données chargées: {len(self.data)} produits")
        return True
    
    def normalize_product_names(self):
        """Normaliser les noms de produits pour faciliter la comparaison"""
        if 'nom_normalise' not in self.data.columns:
            # Adapter selon la structure des données
            if 'nom' in self.data.columns:
                self.data['nom_normalise'] = self.data['nom'].apply(self.normalize_name)
            elif 'Matériau' in self.data.columns:
                self.data['nom_normalise'] = self.data['Matériau'].apply(self.normalize_name)
            else:
                print("❌ Aucune colonne de nom de produit trouvée")
                return
        
        print("✅ Noms de produits normalisés")
    
    def normalize_name(self, name):
        """Normaliser un nom de produit"""
        if not name:
            return ""
        
        # Convertir en minuscules
        name = name.lower()
        
        # Supprimer caractères spéciaux
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Supprimer mots vides
        stop_words = ['de', 'du', 'la', 'le', 'les', 'des', 'pour', 'avec', 'sans']
        words = [w for w in name.split() if w not in stop_words and len(w) > 2]
        
        return ' '.join(words)
      def find_similar_products(self, similarity_threshold=0.6):
        """Trouver des produits similaires entre sites"""
        similar_groups = []
        processed = set()
        
        for idx, row in self.data.iterrows():
            if idx in processed:
                continue
                
            similar_products = [{'idx': idx, 'data': row}]
            processed.add(idx)
            
            # Chercher produits similaires
            for idx2, row2 in self.data.iterrows():
                if idx2 in processed or idx == idx2:
                    continue
                
                similarity = SequenceMatcher(
                    None, 
                    row['nom_normalise'], 
                    row2['nom_normalise']
                ).ratio()
                
                if similarity >= similarity_threshold:
                    similar_products.append({'idx': idx2, 'data': row2})
                    processed.add(idx2)
            
            if len(similar_products) > 1:  # Plusieurs produits similaires
                similar_groups.append(similar_products)
        
        print(f"✅ {len(similar_groups)} groupes de produits similaires trouvés")
        return similar_groups
      def compare_prices(self, similar_groups):
        """Comparer les prix des produits similaires"""
        comparisons = []
        
        for group in similar_groups:
            if len(group) < 2:
                continue
            
            # Extraire données du groupe - adapter selon la structure
            group_data = []
            for item in group:
                row = item['data']
                group_data.append({
                    'nom': row.get('Matériau', row.get('nom', 'Produit inconnu')),
                    'prix': row.get('Prix_Unitaire_TND', row.get('prix_tnd', 0)),
                    'site': row.get('Meilleur_Fournisseur', row.get('site', 'Site inconnu'))
                })
            
            # Calculer statistiques
            prices = [item['prix'] for item in group_data]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = np.mean(prices)
            
            # Trouver le meilleur et pire fournisseur
            best_deal = min(group_data, key=lambda x: x['prix'])
            worst_deal = max(group_data, key=lambda x: x['prix'])
            
            # Calculer économies possibles
            savings = max_price - min_price
            savings_pct = (savings / max_price) * 100 if max_price > 0 else 0
            
            comparison = {
                'produit_type': group_data[0]['nom'][:50] + "...",
                'nb_fournisseurs': len(group_data),
                'prix_min': min_price,
                'prix_max': max_price,
                'prix_moyen': avg_price,
                'meilleur_fournisseur': best_deal['site'],
                'meilleur_prix': best_deal['prix'],
                'pire_fournisseur': worst_deal['site'],
                'pire_prix': worst_deal['prix'],
                'economie_possible': savings,
                'economie_pourcentage': savings_pct,
                'details': group_data
            }
            
            comparisons.append(comparison)
        
        self.comparison_results = comparisons
        print(f"✅ {len(comparisons)} comparaisons de prix générées")
        return comparisons
    
    def generate_savings_report(self):
        """Générer rapport d'économies possibles"""
        if not self.comparison_results:
            print("❌ Aucune comparaison disponible")
            return
        
        # Trier par économies décroissantes
        sorted_comparisons = sorted(
            self.comparison_results, 
            key=lambda x: x['economie_possible'], 
            reverse=True
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'rapport_economies_{timestamp}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("💰 RAPPORT D'ÉCONOMIES MATÉRIAUX DE CONSTRUCTION\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Produits analysés: {len(sorted_comparisons)}\n\n")
            
            # Résumé des économies
            total_savings = sum(c['economie_possible'] for c in sorted_comparisons)
            avg_savings_pct = np.mean([c['economie_pourcentage'] for c in sorted_comparisons])
            
            f.write(f"📊 RÉSUMÉ:\n")
            f.write(f"   - Économies totales possibles: {total_savings:.2f} TND\n")
            f.write(f"   - Économie moyenne: {avg_savings_pct:.1f}%\n")
            f.write(f"   - Meilleure économie: {sorted_comparisons[0]['economie_possible']:.2f} TND\n\n")
            
            # Top 10 des économies
            f.write("🏆 TOP 10 ÉCONOMIES POSSIBLES:\n")
            f.write("-" * 30 + "\n")
            
            for i, comp in enumerate(sorted_comparisons[:10], 1):
                f.write(f"{i}. {comp['produit_type']}\n")
                f.write(f"   💰 Économie: {comp['economie_possible']:.2f} TND ({comp['economie_pourcentage']:.1f}%)\n")
                f.write(f"   🏪 Meilleur: {comp['meilleur_fournisseur']} - {comp['meilleur_prix']:.2f} TND\n")
                f.write(f"   💸 Plus cher: {comp['pire_fournisseur']} - {comp['pire_prix']:.2f} TND\n")
                f.write(f"   📊 {comp['nb_fournisseurs']} fournisseurs comparés\n\n")
            
            # Analyse par fournisseur
            f.write("🏬 ANALYSE PAR FOURNISSEUR:\n")
            f.write("-" * 25 + "\n")
            
            fournisseur_stats = {}
            for comp in sorted_comparisons:
                best = comp['meilleur_fournisseur']
                if best not in fournisseur_stats:
                    fournisseur_stats[best] = {'count': 0, 'total_savings': 0}
                fournisseur_stats[best]['count'] += 1
                fournisseur_stats[best]['total_savings'] += comp['economie_possible']
            
            for fournisseur, stats in sorted(fournisseur_stats.items(), 
                                           key=lambda x: x[1]['count'], reverse=True):
                f.write(f"• {fournisseur}:\n")
                f.write(f"  - Meilleur prix sur {stats['count']} produits\n")
                f.write(f"  - Économies générées: {stats['total_savings']:.2f} TND\n\n")
        
        print(f"📄 Rapport d'économies généré: {report_file}")
        return report_file
    
    def export_comparison_table(self):
        """Exporter tableau de comparaison CSV"""
        if not self.comparison_results:
            print("❌ Aucune comparaison disponible")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f'comparaison_prix_{timestamp}.csv'
        
        # Préparer données pour CSV
        csv_data = []
        for comp in self.comparison_results:
            csv_data.append({
                'Produit': comp['produit_type'],
                'Nb_Fournisseurs': comp['nb_fournisseurs'],
                'Prix_Min_TND': comp['prix_min'],
                'Prix_Max_TND': comp['prix_max'],
                'Prix_Moyen_TND': comp['prix_moyen'],
                'Meilleur_Fournisseur': comp['meilleur_fournisseur'],
                'Meilleur_Prix_TND': comp['meilleur_prix'],
                'Economie_Possible_TND': comp['economie_possible'],
                'Economie_Pourcentage': comp['economie_pourcentage']
            })
        
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"📊 Tableau de comparaison exporté: {csv_file}")
        return csv_file

def main():
    """Test du comparateur"""
    comparator = MaterialPriceComparator()
    
    # Charger données existantes (adapter le nom du fichier)
    success = comparator.load_data(csv_file='ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
    
    if success:
        # Normaliser noms
        comparator.normalize_product_names()
        
        # Trouver produits similaires
        similar_groups = comparator.find_similar_products()
        
        # Comparer prix
        comparisons = comparator.compare_prices(similar_groups)
        
        # Générer rapports
        if comparisons:
            comparator.generate_savings_report()
            comparator.export_comparison_table()
        else:
            print("ℹ️ Aucune comparaison possible avec les données actuelles")

if __name__ == "__main__":
    main()
