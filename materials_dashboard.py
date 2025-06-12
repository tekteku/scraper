#!/usr/bin/env python3
"""
Tableau de Bord Interactif pour l'Analyse des Prix des Matériaux
Interface web avec Streamlit pour visualiser les données et tendances
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json

# Configuration de la page
st.set_page_config(
    page_title="📊 Tableau de Bord Matériaux",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MaterialsDashboard:
    def __init__(self):
        self.load_data()
    
    @st.cache_data
    def load_data(_self):
        """Charger les données avec cache"""
        try:
            # Charger données d'estimation
            df_estimation = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
            
            # Charger historique des prix (si disponible)
            try:
                conn = sqlite3.connect('price_history.db')
                df_history = pd.read_sql_query('''
                    SELECT * FROM price_history 
                    ORDER BY scraped_date DESC
                ''', conn)
                conn.close()
            except:
                df_history = pd.DataFrame()
            
            return df_estimation, df_history
        except Exception as e:
            st.error(f"Erreur chargement données: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def render_sidebar(self):
        """Rendu de la barre latérale"""
        st.sidebar.header("🔧 Filtres et Options")
        
        # Filtre par matériau
        if not self.df_estimation.empty:
            materials = ["Tous"] + list(self.df_estimation['Matériau'].unique())
            selected_material = st.sidebar.selectbox("Matériau", materials)
            
            # Filtre par catégorie
            categories = ["Toutes"] + list(self.df_estimation['Catégorie'].unique())
            selected_category = st.sidebar.selectbox("Catégorie", categories)
            
            # Filtre par fournisseur
            suppliers = ["Tous"] + list(self.df_estimation['Meilleur_Fournisseur'].unique())
            selected_supplier = st.sidebar.selectbox("Fournisseur", suppliers)
            
            return selected_material, selected_category, selected_supplier
        
        return "Tous", "Toutes", "Tous"
    
    def apply_filters(self, df, material, category, supplier):
        """Appliquer les filtres aux données"""
        filtered_df = df.copy()
        
        if material != "Tous":
            filtered_df = filtered_df[filtered_df['Matériau'] == material]
        
        if category != "Toutes":
            filtered_df = filtered_df[filtered_df['Catégorie'] == category]
        
        if supplier != "Tous":
            filtered_df = filtered_df[filtered_df['Meilleur_Fournisseur'] == supplier]
        
        return filtered_df
    
    def render_overview(self, df):
        """Rendu de la vue d'ensemble"""
        st.header("📊 Vue d'Ensemble")
        
        if df.empty:
            st.warning("Aucune donnée disponible")
            return
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Matériaux",
                len(df),
                delta=None
            )
        
        with col2:
            avg_price = df['Prix_Unitaire_TND'].mean()
            st.metric(
                "Prix Moyen",
                f"{avg_price:.2f} TND",
                delta=None
            )
        
        with col3:
            total_savings = df['Économie_TND'].sum()
            st.metric(
                "Économies Totales",
                f"{total_savings:.2f} TND",
                delta=None
            )
        
        with col4:
            avg_savings_pct = df['Économie_Pourcentage'].mean()
            st.metric(
                "Économie Moyenne",
                f"{avg_savings_pct:.1f}%",
                delta=None
            )
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Répartition des Prix par Catégorie")
            fig_cat = px.box(
                df, 
                x='Catégorie', 
                y='Prix_Unitaire_TND',
                title="Distribution des Prix par Catégorie"
            )
            fig_cat.update_xaxes(tickangle=45)
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader("📈 Économies par Matériau")
            fig_savings = px.bar(
                df.nlargest(10, 'Économie_TND'),
                x='Matériau',
                y='Économie_TND',
                title="Top 10 Économies Possibles"
            )
            fig_savings.update_xaxes(tickangle=45)
            st.plotly_chart(fig_savings, use_container_width=True)
    
    def render_price_analysis(self, df):
        """Rendu de l'analyse des prix"""
        st.header("💲 Analyse des Prix")
        
        if df.empty:
            st.warning("Aucune donnée disponible")
            return
        
        # Graphique de dispersion prix vs économies
        st.subheader("📊 Prix vs Économies Possibles")
        fig_scatter = px.scatter(
            df,
            x='Prix_Unitaire_TND',
            y='Économie_TND',
            size='Économie_Pourcentage',
            color='Catégorie',
            hover_data=['Matériau', 'Meilleur_Fournisseur'],
            title="Relation Prix/Économies par Catégorie"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Analyse par fournisseur
        st.subheader("🏪 Performance des Fournisseurs")
        supplier_stats = df.groupby('Meilleur_Fournisseur').agg({
            'Prix_Unitaire_TND': 'mean',
            'Économie_TND': 'sum',
            'Matériau': 'count'
        }).round(2)
        supplier_stats.columns = ['Prix Moyen', 'Économies Totales', 'Nb Produits']
        
        fig_suppliers = px.bar(
            supplier_stats.reset_index(),
            x='Meilleur_Fournisseur',
            y='Économies Totales',
            title="Économies Générées par Fournisseur"
        )
        st.plotly_chart(fig_suppliers, use_container_width=True)
        
        # Tableau détaillé
        st.subheader("📋 Détails par Fournisseur")
        st.dataframe(supplier_stats, use_container_width=True)
    
    def render_project_estimator(self, df):
        """Rendu de l'estimateur de projet"""
        st.header("🏗️ Estimateur de Projet")
        
        if df.empty:
            st.warning("Aucune donnée disponible")
            return
        
        # Sélection du type de projet
        project_type = st.selectbox(
            "Type de Projet",
            ["Maison 100m²", "Villa 200m²", "Rénovation 80m²", "Personnalisé"]
        )
        
        # Quantités par défaut selon le type
        quantities = {
            "Maison 100m²": {
                "Ciment": 50, "Fer à béton": 2000, "Parpaing": 800,
                "Brique": 1000, "Sable": 15, "Gravier": 20,
                "Carrelage": 100, "Peinture": 8, "Isolant": 120, "Placo": 200
            },
            "Villa 200m²": {
                "Ciment": 100, "Fer à béton": 4000, "Parpaing": 1500,
                "Brique": 2000, "Sable": 30, "Gravier": 40,
                "Carrelage": 200, "Peinture": 15, "Isolant": 240, "Placo": 400
            },
            "Rénovation 80m²": {
                "Ciment": 20, "Fer à béton": 500, "Parpaing": 200,
                "Brique": 300, "Sable": 8, "Gravier": 10,
                "Carrelage": 80, "Peinture": 6, "Isolant": 80, "Placo": 150
            }
        }
        
        # Interface pour quantités
        st.subheader("📝 Quantités Nécessaires")
        
        if project_type != "Personnalisé":
            default_qty = quantities[project_type]
            st.info(f"Quantités par défaut pour {project_type}")
        else:
            default_qty = {}
        
        # Formulaire de quantités
        project_materials = {}
        cols = st.columns(2)
        
        for i, material in enumerate(df['Matériau'].unique()):
            col = cols[i % 2]
            with col:
                default_val = default_qty.get(material, 0)
                quantity = st.number_input(
                    f"{material}",
                    min_value=0,
                    value=default_val,
                    key=f"qty_{material}"
                )
                if quantity > 0:
                    project_materials[material] = quantity
        
        # Calcul de l'estimation
        if st.button("💰 Calculer l'Estimation"):
            if project_materials:
                estimation = self.calculate_project_cost(df, project_materials)
                self.display_estimation(estimation)
            else:
                st.warning("Veuillez saisir au moins une quantité")
    
    def calculate_project_cost(self, df, materials):
        """Calculer le coût d'un projet"""
        total_cost = 0
        total_savings = 0
        estimation_details = []
        
        for material, quantity in materials.items():
            material_data = df[df['Matériau'] == material]
            
            if not material_data.empty:
                row = material_data.iloc[0]
                unit_price = row['Prix_Unitaire_TND']
                savings_per_unit = row['Économie_TND']
                unit = row['Unité']
                supplier = row['Meilleur_Fournisseur']
                
                line_cost = unit_price * quantity
                line_savings = savings_per_unit * quantity
                
                total_cost += line_cost
                total_savings += line_savings
                
                estimation_details.append({
                    'Matériau': material,
                    'Quantité': quantity,
                    'Unité': unit,
                    'Prix_Unitaire': unit_price,
                    'Coût_Total': line_cost,
                    'Économie_Ligne': line_savings,
                    'Fournisseur': supplier
                })
        
        return {
            'details': estimation_details,
            'total_cost': total_cost,
            'total_savings': total_savings
        }
    
    def display_estimation(self, estimation):
        """Afficher l'estimation calculée"""
        st.subheader("📊 Résultat de l'Estimation")
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Coût Total",
                f"{estimation['total_cost']:.2f} TND",
                delta=None
            )
        
        with col2:
            st.metric(
                "Économies Possibles",
                f"{estimation['total_savings']:.2f} TND",
                delta=None
            )
        
        with col3:
            savings_pct = (estimation['total_savings'] / estimation['total_cost']) * 100
            st.metric(
                "% Économies",
                f"{savings_pct:.1f}%",
                delta=None
            )
        
        # Tableau détaillé
        st.subheader("📋 Détail de l'Estimation")
        df_estimation = pd.DataFrame(estimation['details'])
        
        # Formatage des colonnes
        df_estimation['Prix_Unitaire'] = df_estimation['Prix_Unitaire'].apply(lambda x: f"{x:.2f} TND")
        df_estimation['Coût_Total'] = df_estimation['Coût_Total'].apply(lambda x: f"{x:.2f} TND")
        df_estimation['Économie_Ligne'] = df_estimation['Économie_Ligne'].apply(lambda x: f"{x:.2f} TND")
        
        st.dataframe(df_estimation, use_container_width=True)
        
        # Graphique répartition des coûts
        fig_pie = px.pie(
            estimation['details'],
            values='Coût_Total',
            names='Matériau',
            title="Répartition des Coûts par Matériau"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    def render_data_table(self, df):
        """Rendu du tableau de données"""
        st.header("🗂️ Données Détaillées")
        
        if df.empty:
            st.warning("Aucune donnée disponible")
            return
        
        # Options d'affichage
        st.subheader("⚙️ Options d'Affichage")
        show_all = st.checkbox("Afficher toutes les colonnes")
        
        if not show_all:
            columns_to_show = st.multiselect(
                "Colonnes à afficher",
                df.columns.tolist(),
                default=['Matériau', 'Prix_Unitaire_TND', 'Économie_TND', 'Meilleur_Fournisseur']
            )
            df_display = df[columns_to_show] if columns_to_show else df
        else:
            df_display = df
        
        # Affichage du tableau
        st.dataframe(df_display, use_container_width=True)
        
        # Bouton de téléchargement
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name=f"materiaux_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    def run(self):
        """Lancer le tableau de bord"""
        st.title("🏗️ Tableau de Bord Matériaux de Construction")
        st.markdown("---")
        
        # Charger données
        self.df_estimation, self.df_history = self.load_data()
        
        # Barre latérale
        material_filter, category_filter, supplier_filter = self.render_sidebar()
        
        # Appliquer filtres
        df_filtered = self.apply_filters(
            self.df_estimation, 
            material_filter, 
            category_filter, 
            supplier_filter
        )
        
        # Onglets
        tabs = st.tabs([
            "📊 Vue d'Ensemble", 
            "💲 Analyse Prix", 
            "🏗️ Estimateur", 
            "🗂️ Données"
        ])
        
        with tabs[0]:
            self.render_overview(df_filtered)
        
        with tabs[1]:
            self.render_price_analysis(df_filtered)
        
        with tabs[2]:
            self.render_project_estimator(df_filtered)
        
        with tabs[3]:
            self.render_data_table(df_filtered)

if __name__ == "__main__":
    dashboard = MaterialsDashboard()
    dashboard.run()
