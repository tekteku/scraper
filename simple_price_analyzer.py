#!/usr/bin/env python3
"""
Comparateur de Prix Simplifié pour les Données d'Estimation
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_price_data():
    """Analyser les données de prix existantes"""
    
    # Charger les données
    try:
        df = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
        print(f"✅ Données chargées: {len(df)} matériaux")
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        return
    
    # Analyse des économies par fournisseur
    print("\n🏪 ANALYSE PAR FOURNISSEUR:")
    print("=" * 40)
    
    fournisseur_stats = df.groupby('Meilleur_Fournisseur').agg({
        'Prix_Unitaire_TND': 'mean',
        'Économie_TND': ['sum', 'mean'],
        'Matériau': 'count'
    }).round(2)
    
    fournisseur_stats.columns = ['Prix_Moyen', 'Économies_Totales', 'Économies_Moyennes', 'Nb_Produits']
    print(fournisseur_stats)
    
    # Top économies
    print("\n💰 TOP 5 ÉCONOMIES POSSIBLES:")
    print("-" * 30)
    
    top_savings = df.nlargest(5, 'Économie_TND')[['Matériau', 'Économie_TND', 'Économie_Pourcentage', 'Meilleur_Fournisseur']]
    for _, row in top_savings.iterrows():
        print(f"• {row['Matériau']}: {row['Économie_TND']:.2f} TND ({row['Économie_Pourcentage']:.1f}%) - {row['Meilleur_Fournisseur']}")
    
    # Analyse par catégorie
    print("\n📊 ANALYSE PAR CATÉGORIE:")
    print("-" * 25)
    
    cat_stats = df.groupby('Catégorie').agg({
        'Prix_Unitaire_TND': ['mean', 'min', 'max'],
        'Économie_TND': 'sum',
        'Matériau': 'count'
    }).round(2)
    
    for cat in df['Catégorie'].unique():
        cat_data = df[df['Catégorie'] == cat]
        print(f"\n🔧 {cat.upper()}:")
        print(f"   - Nb produits: {len(cat_data)}")
        print(f"   - Prix moyen: {cat_data['Prix_Unitaire_TND'].mean():.2f} TND")
        print(f"   - Économies totales: {cat_data['Économie_TND'].sum():.2f} TND")
        print(f"   - Meilleur fournisseur: {cat_data.loc[cat_data['Économie_TND'].idxmax(), 'Meilleur_Fournisseur']}")
    
    # Génération de rapport de comparaison
    generate_comparison_report(df)

def generate_comparison_report(df):
    """Générer un rapport de comparaison détaillé"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'rapport_comparaison_{timestamp}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("📊 RAPPORT DE COMPARAISON PRIX MATÉRIAUX\n")
        f.write("=" * 45 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Matériaux analysés: {len(df)}\n\n")
        
        # Statistiques globales
        total_savings = df['Économie_TND'].sum()
        avg_savings_pct = df['Économie_Pourcentage'].mean()
        
        f.write("💰 RÉSUMÉ ÉCONOMIES:\n")
        f.write(f"   - Économies totales possibles: {total_savings:.2f} TND\n")
        f.write(f"   - Économie moyenne: {avg_savings_pct:.1f}%\n")
        f.write(f"   - Matériau le plus économique: {df.loc[df['Économie_TND'].idxmax(), 'Matériau']}\n\n")
        
        # Détail par matériau
        f.write("🔍 DÉTAIL PAR MATÉRIAU:\n")
        f.write("-" * 25 + "\n")
        
        for _, row in df.iterrows():
            f.write(f"\n• {row['Matériau']}:\n")
            f.write(f"  📍 Meilleur prix: {row['Prix_Unitaire_TND']:.2f} TND/{row['Unité']} ({row['Meilleur_Fournisseur']})\n")
            f.write(f"  📈 Prix moyen marché: {row['Prix_Moyen_TND']:.2f} TND\n")
            f.write(f"  📉 Prix maximum: {row['Prix_Max_TND']:.2f} TND\n")
            f.write(f"  💰 Économie possible: {row['Économie_TND']:.2f} TND ({row['Économie_Pourcentage']:.1f}%)\n")
            f.write(f"  🏪 Nb fournisseurs: {row['Nombre_Fournisseurs']}\n")
            f.write(f"  📦 Disponibilité: {row['Disponibilité']}\n")
        
        # Recommandations
        f.write("\n\n🎯 RECOMMANDATIONS:\n")
        f.write("-" * 15 + "\n")
        
        # Meilleur fournisseur global
        best_supplier = df.groupby('Meilleur_Fournisseur')['Économie_TND'].sum().idxmax()
        best_supplier_savings = df.groupby('Meilleur_Fournisseur')['Économie_TND'].sum().max()
        
        f.write(f"1. 🏆 Fournisseur recommandé: {best_supplier}\n")
        f.write(f"   - Économies générées: {best_supplier_savings:.2f} TND\n")
        f.write(f"   - Produits proposés: {len(df[df['Meilleur_Fournisseur'] == best_supplier])}\n\n")
        
        f.write("2. 📈 Matériaux prioritaires (plus fortes économies):\n")
        top_3 = df.nlargest(3, 'Économie_TND')
        for i, (_, row) in enumerate(top_3.iterrows(), 1):
            f.write(f"   {i}. {row['Matériau']}: {row['Économie_TND']:.2f} TND d'économie\n")
        
        f.write("\n3. ⚠️ Points d'attention:\n")
        stock_limite = df[df['Disponibilité'] == 'Stock limité']
        if not stock_limite.empty:
            f.write(f"   - {len(stock_limite)} matériaux en stock limité\n")
        
        sur_commande = df[df['Disponibilité'] == 'Sur commande']
        if not sur_commande.empty:
            f.write(f"   - {len(sur_commande)} matériaux sur commande\n")
    
    print(f"\n📄 Rapport détaillé généré: {report_file}")
    
    # Exporter aussi en CSV pour analyse
    csv_file = f'comparaison_detaillee_{timestamp}.csv'
    
    # Ajouter colonnes d'analyse
    df_export = df.copy()
    df_export['Ratio_Economie'] = df_export['Économie_TND'] / df_export['Prix_Unitaire_TND']
    df_export['Rang_Economie'] = df_export['Économie_TND'].rank(ascending=False)
    df_export['Categoria_Prix'] = pd.cut(df_export['Prix_Unitaire_TND'], 
                                        bins=3, 
                                        labels=['Économique', 'Moyen', 'Cher'])
    
    df_export.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"📊 Données d'analyse exportées: {csv_file}")

if __name__ == "__main__":
    analyze_price_data()
