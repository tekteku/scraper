"""
Générateur de fichier d'estimation final pour les matériaux de construction
"""

import pandas as pd
import json
import os
from datetime import datetime

def create_cost_estimation_file():
    """Crée un fichier d'estimation final avec les meilleurs prix"""
    
    # Charge les dernières données
    df = pd.read_csv("materials_data/raw/construction_materials_20250611_094114.csv")
    
    # Trouve le meilleur prix pour chaque matériau
    best_prices = []
    
    material_groups = {}
    for idx, row in df.iterrows():
        base_name = row['nom'].split(' - ')[0]
        if base_name not in material_groups:
            material_groups[base_name] = []
        material_groups[base_name].append(row)
    
    for material_name, products in material_groups.items():
        # Trouve le meilleur prix
        best_product = min(products, key=lambda x: x['prix'])
        
        # Calcule les statistiques
        prices = [p['prix'] for p in products]
        avg_price = sum(prices) / len(prices)
        max_price = max(prices)
        
        # Économie possible
        savings = max_price - best_product['prix']
        savings_percent = (savings / max_price) * 100 if max_price > 0 else 0
        
        best_prices.append({
            'Matériau': material_name,
            'Type_Détaillé': best_product['nom'],
            'Prix_Unitaire_TND': best_product['prix'],
            'Unité': best_product['unite'],
            'Meilleur_Fournisseur': best_product['fournisseur'],
            'Disponibilité': best_product['disponibilite'],
            'Prix_Moyen_TND': round(avg_price, 2),
            'Prix_Max_TND': max_price,
            'Économie_TND': round(savings, 2),
            'Économie_Pourcentage': round(savings_percent, 1),
            'Nombre_Fournisseurs': len(products),
            'Usage': best_product['usage'],
            'Catégorie': best_product['categorie']
        })
    
    # Crée le DataFrame final
    df_final = pd.DataFrame(best_prices)
    df_final = df_final.sort_values('Matériau')
    
    # Sauvegarde
    final_file = f"ESTIMATION_MATERIAUX_TUNISIE_{datetime.now().strftime('%Y%m%d')}.csv"
    df_final.to_csv(final_file, index=False, encoding='utf-8')
    
    return final_file, df_final

def create_project_template():
    """Crée un template pour estimation de projet"""
    
    template_data = [
        # GROS ŒUVRE
        {'Matériau': 'Ciment', 'Quantité_Maison_100m2': 50, 'Quantité_Villa_200m2': 100, 'Unité': 'sacs', 'Phase': 'Gros œuvre'},
        {'Matériau': 'Fer à béton', 'Quantité_Maison_100m2': 2000, 'Quantité_Villa_200m2': 4000, 'Unité': 'kg', 'Phase': 'Gros œuvre'},
        {'Matériau': 'Parpaing', 'Quantité_Maison_100m2': 800, 'Quantité_Villa_200m2': 1500, 'Unité': 'pièces', 'Phase': 'Gros œuvre'},
        {'Matériau': 'Brique', 'Quantité_Maison_100m2': 1000, 'Quantité_Villa_200m2': 2000, 'Unité': 'pièces', 'Phase': 'Gros œuvre'},
        
        # GRANULATS
        {'Matériau': 'Sable', 'Quantité_Maison_100m2': 15, 'Quantité_Villa_200m2': 30, 'Unité': 'm³', 'Phase': 'Gros œuvre'},
        {'Matériau': 'Gravier', 'Quantité_Maison_100m2': 20, 'Quantité_Villa_200m2': 40, 'Unité': 'm³', 'Phase': 'Gros œuvre'},
        
        # REVÊTEMENTS
        {'Matériau': 'Carrelage', 'Quantité_Maison_100m2': 100, 'Quantité_Villa_200m2': 200, 'Unité': 'm²', 'Phase': 'Finition'},
        {'Matériau': 'Peinture', 'Quantité_Maison_100m2': 8, 'Quantité_Villa_200m2': 15, 'Unité': 'bidons', 'Phase': 'Finition'},
        
        # ISOLATION
        {'Matériau': 'Isolant', 'Quantité_Maison_100m2': 120, 'Quantité_Villa_200m2': 240, 'Unité': 'm²', 'Phase': 'Second œuvre'},
        {'Matériau': 'Placo', 'Quantité_Maison_100m2': 200, 'Quantité_Villa_200m2': 400, 'Unité': 'm²', 'Phase': 'Second œuvre'},
    ]
    
    template_file = f"TEMPLATE_ESTIMATION_PROJET_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(template_data).to_csv(template_file, index=False, encoding='utf-8')
    
    return template_file

def main():
    print("🔨 Génération des fichiers d'estimation finaux...")
    
    # Fichier des meilleurs prix
    final_file, df_final = create_cost_estimation_file()
    print(f"✅ Fichier d'estimation créé: {final_file}")
    print(f"   - {len(df_final)} matériaux analysés")
    print(f"   - Meilleurs prix identifiés")
    print(f"   - Économies potentielles calculées")
    
    # Template de projet
    template_file = create_project_template()
    print(f"✅ Template de projet créé: {template_file}")
    
    # Statistiques importantes
    print(f"\n📊 RÉSUMÉ DES ÉCONOMIES POSSIBLES:")
    total_savings = df_final['Économie_TND'].sum()
    avg_savings_percent = df_final['Économie_Pourcentage'].mean()
    
    print(f"   - Économie totale possible: {total_savings:.2f} TND")
    print(f"   - Économie moyenne: {avg_savings_percent:.1f}%")
    print(f"   - Matériau avec plus d'économies: {df_final.loc[df_final['Économie_TND'].idxmax(), 'Matériau']}")
    
    # Top 5 des matériaux les plus chers
    print(f"\n💰 TOP 5 MATÉRIAUX LES PLUS CHERS:")
    top_expensive = df_final.nlargest(5, 'Prix_Unitaire_TND')
    for idx, row in top_expensive.iterrows():
        print(f"   {row['Matériau']}: {row['Prix_Unitaire_TND']} TND/{row['Unité']}")
    
    print(f"\n🎯 RECOMMANDATIONS:")
    print(f"   1. Utilisez {final_file} pour vos estimations")
    print(f"   2. Comparez toujours les fournisseurs")
    print(f"   3. Négociez les gros volumes")
    print(f"   4. Planifiez selon la disponibilité")

if __name__ == "__main__":
    main()
