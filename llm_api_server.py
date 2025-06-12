#!/usr/bin/env python3
"""
🤖 API LLM pour Prédictions Matériaux de Construction
API REST permettant à un LLM de lire les données et faire des prédictions
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Configuration de l'API
app = FastAPI(
    title="🏗️ API Prédictions Matériaux Tunisiens",
    description="API permettant à un LLM de lire les données et prédire les prix de matériaux",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour accès web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour l'API
class MaterialQuery(BaseModel):
    materiau: str
    quantite: Optional[int] = 1
    projet_type: Optional[str] = "construction"
    surface: Optional[float] = 100.0

class PredictionRequest(BaseModel):
    materials: List[MaterialQuery]
    horizon_jours: Optional[int] = 30
    include_trends: Optional[bool] = True

class ProjectEstimation(BaseModel):
    nom_projet: str
    type_projet: str
    surface: float
    materials_requis: List[MaterialQuery]

class LLMQuery(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = {}

class APIResponse(BaseModel):
    status: str
    data: Any
    message: Optional[str] = None
    timestamp: datetime = datetime.now()

# Classe principale pour les prédictions
class MaterialsPredictionEngine:
    def __init__(self):
        self.data_file = "ESTIMATION_MATERIAUX_TUNISIE_20250611.csv"
        self.model_file = "materials_prediction_model.joblib"
        self.encoders_file = "label_encoders.joblib"
        
        self.df = None
        self.model = None
        self.encoders = {}
        
        self.load_data()
        self.prepare_model()
    
    def load_data(self):
        """Charger les données de matériaux"""
        try:
            self.df = pd.read_csv(self.data_file)
            print(f"✅ Données chargées: {len(self.df)} matériaux")
        except Exception as e:
            print(f"❌ Erreur chargement données: {e}")
            self.df = pd.DataFrame()
    
    def prepare_model(self):
        """Préparer le modèle de prédiction ML"""
        if self.df.empty:
            return
        
        try:
            # Préparer les données pour ML
            features = ['Matériau', 'Meilleur_Fournisseur', 'Catégorie', 'Nombre_Fournisseurs']
            target = 'Prix_Unitaire_TND'
            
            # Encoder les variables catégorielles
            df_encoded = self.df.copy()
            for feature in features:
                if df_encoded[feature].dtype == 'object':
                    if feature not in self.encoders:
                        self.encoders[feature] = LabelEncoder()
                        df_encoded[feature] = self.encoders[feature].fit_transform(df_encoded[feature].astype(str))
                    else:
                        df_encoded[feature] = self.encoders[feature].transform(df_encoded[feature].astype(str))
            
            # Préparer X et y
            X = df_encoded[features]
            y = df_encoded[target]
            
            # Entraîner le modèle si pas déjà fait
            if not os.path.exists(self.model_file):
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.model.fit(X_train, y_train)
                
                # Sauvegarder le modèle
                joblib.dump(self.model, self.model_file)
                joblib.dump(self.encoders, self.encoders_file)
                
                score = self.model.score(X_test, y_test)
                print(f"✅ Modèle entraîné avec R² = {score:.3f}")
            else:
                # Charger le modèle existant
                self.model = joblib.load(self.model_file)
                self.encoders = joblib.load(self.encoders_file)
                print("✅ Modèle chargé depuis fichier")
                
        except Exception as e:
            print(f"❌ Erreur préparation modèle: {e}")
            self.model = None
    
    def predict_price(self, materiau: str, fournisseur: str = None) -> Dict:
        """Prédire le prix d'un matériau"""
        if self.model is None or self.df.empty:
            return {"error": "Modèle non disponible"}
        
        try:
            # Trouver les données du matériau
            material_data = self.df[self.df['Matériau'].str.contains(materiau, case=False, na=False)]
            
            if material_data.empty:
                return {"error": f"Matériau '{materiau}' non trouvé"}
            
            material_row = material_data.iloc[0]
            
            # Préparer les features pour prédiction
            features_dict = {
                'Matériau': material_row['Matériau'],
                'Meilleur_Fournisseur': fournisseur or material_row['Meilleur_Fournisseur'],
                'Catégorie': material_row['Catégorie'],
                'Nombre_Fournisseurs': material_row['Nombre_Fournisseurs']
            }
            
            # Encoder les features
            features_encoded = []
            for feature in ['Matériau', 'Meilleur_Fournisseur', 'Catégorie', 'Nombre_Fournisseurs']:
                if feature in self.encoders and features_dict[feature]:
                    try:
                        encoded_val = self.encoders[feature].transform([str(features_dict[feature])])[0]
                        features_encoded.append(encoded_val)
                    except:
                        # Valeur inconnue, utiliser valeur par défaut
                        features_encoded.append(0)
                else:
                    features_encoded.append(features_dict[feature] if isinstance(features_dict[feature], (int, float)) else 0)
            
            # Prédiction
            predicted_price = self.model.predict([features_encoded])[0]
            
            # Ajouter tendance et confiance
            current_price = material_row['Prix_Unitaire_TND']
            trend = "stable"
            if predicted_price > current_price * 1.05:
                trend = "hausse"
            elif predicted_price < current_price * 0.95:
                trend = "baisse"
            
            return {
                "materiau": materiau,
                "prix_actuel": float(current_price),
                "prix_predit": float(predicted_price),
                "tendance": trend,
                "variation_pct": float(((predicted_price - current_price) / current_price) * 100),
                "fournisseur": features_dict['Meilleur_Fournisseur'],
                "unite": material_row['Unité'],
                "disponibilite": material_row['Disponibilité']
            }
            
        except Exception as e:
            return {"error": f"Erreur prédiction: {str(e)}"}

# Instance globale du moteur de prédiction
prediction_engine = MaterialsPredictionEngine()

# Endpoints de l'API

@app.get("/", response_model=APIResponse)
async def root():
    """Endpoint racine de l'API"""
    return APIResponse(
        status="success",
        data={
            "message": "API Prédictions Matériaux Tunisiens",
            "version": "1.0.0",
            "endpoints": [
                "/materials", "/predict", "/estimate", "/llm-query", 
                "/trends", "/suppliers", "/categories"
            ]
        }
    )

@app.get("/materials", response_model=APIResponse)
async def get_all_materials():
    """Obtenir tous les matériaux disponibles"""
    try:
        if prediction_engine.df.empty:
            raise HTTPException(status_code=404, detail="Aucune donnée disponible")
        
        materials = prediction_engine.df.to_dict('records')
        
        return APIResponse(
            status="success",
            data={
                "count": len(materials),
                "materials": materials
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/materials/{material_name}", response_model=APIResponse)
async def get_material_details(material_name: str):
    """Obtenir les détails d'un matériau spécifique"""
    try:
        material_data = prediction_engine.df[
            prediction_engine.df['Matériau'].str.contains(material_name, case=False, na=False)
        ]
        
        if material_data.empty:
            raise HTTPException(status_code=404, detail=f"Matériau '{material_name}' non trouvé")
        
        return APIResponse(
            status="success",
            data=material_data.iloc[0].to_dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=APIResponse)
async def predict_material_price(request: PredictionRequest):
    """Prédire les prix de matériaux"""
    try:
        predictions = []
        
        for material_query in request.materials:
            prediction = prediction_engine.predict_price(
                material_query.materiau,
                fournisseur=None
            )
            
            if "error" not in prediction:
                # Ajouter quantité et coût total
                prediction["quantite"] = material_query.quantite
                prediction["cout_total_actuel"] = prediction["prix_actuel"] * material_query.quantite
                prediction["cout_total_predit"] = prediction["prix_predit"] * material_query.quantite
            
            predictions.append(prediction)
        
        # Calculer totaux
        total_actuel = sum(p.get("cout_total_actuel", 0) for p in predictions if "error" not in p)
        total_predit = sum(p.get("cout_total_predit", 0) for p in predictions if "error" not in p)
        
        return APIResponse(
            status="success",
            data={
                "predictions": predictions,
                "resume": {
                    "total_actuel_tnd": total_actuel,
                    "total_predit_tnd": total_predit,
                    "variation_totale_tnd": total_predit - total_actuel,
                    "variation_totale_pct": ((total_predit - total_actuel) / total_actuel * 100) if total_actuel > 0 else 0,
                    "horizon_jours": request.horizon_jours
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/estimate", response_model=APIResponse)
async def estimate_project(project: ProjectEstimation):
    """Estimer le coût total d'un projet"""
    try:
        estimations = []
        total_cout = 0
        
        for material in project.materials_requis:
            # Obtenir prix actuel
            material_data = prediction_engine.df[
                prediction_engine.df['Matériau'].str.contains(material.materiau, case=False, na=False)
            ]
            
            if not material_data.empty:
                row = material_data.iloc[0]
                prix_unitaire = row['Prix_Unitaire_TND']
                cout_ligne = prix_unitaire * material.quantite
                total_cout += cout_ligne
                
                estimations.append({
                    "materiau": material.materiau,
                    "quantite": material.quantite,
                    "unite": row['Unité'],
                    "prix_unitaire": prix_unitaire,
                    "cout_ligne": cout_ligne,
                    "fournisseur": row['Meilleur_Fournisseur'],
                    "economie_possible": row['Économie_TND'] * material.quantite
                })
        
        # Calculs finaux
        tva_montant = total_cout * 0.19  # TVA Tunisie 19%
        total_ttc = total_cout + tva_montant
        
        return APIResponse(
            status="success",
            data={
                "projet": {
                    "nom": project.nom_projet,
                    "type": project.type_projet,
                    "surface": project.surface
                },
                "estimations": estimations,
                "totaux": {
                    "sous_total_ht": total_cout,
                    "tva_19_pct": tva_montant,
                    "total_ttc": total_ttc,
                    "cout_par_m2": total_ttc / project.surface if project.surface > 0 else 0
                },
                "economies_possibles": sum(e.get("economie_possible", 0) for e in estimations)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm-query", response_model=APIResponse)
async def process_llm_query(query: LLMQuery):
    """Endpoint spécialisé pour les requêtes LLM"""
    try:
        # Analyser la question du LLM
        question_lower = query.question.lower()
        
        # Préparer le contexte pour le LLM
        context_data = {
            "materials_count": len(prediction_engine.df),
            "categories": prediction_engine.df['Catégorie'].unique().tolist(),
            "suppliers": prediction_engine.df['Meilleur_Fournisseur'].unique().tolist(),
            "price_range": {
                "min": float(prediction_engine.df['Prix_Unitaire_TND'].min()),
                "max": float(prediction_engine.df['Prix_Unitaire_TND'].max()),
                "avg": float(prediction_engine.df['Prix_Unitaire_TND'].mean())
            },
            "total_savings_possible": float(prediction_engine.df['Économie_TND'].sum())
        }
        
        # Logique de réponse basée sur les mots-clés
        response_data = context_data
        
        if any(word in question_lower for word in ['prix', 'coût', 'tarif']):
            # Question sur les prix
            top_expensive = prediction_engine.df.nlargest(5, 'Prix_Unitaire_TND')[['Matériau', 'Prix_Unitaire_TND']].to_dict('records')
            top_cheap = prediction_engine.df.nsmallest(5, 'Prix_Unitaire_TND')[['Matériau', 'Prix_Unitaire_TND']].to_dict('records')
            
            response_data.update({
                "focus": "prix",
                "materiaux_plus_chers": top_expensive,
                "materiaux_moins_chers": top_cheap
            })
        
        elif any(word in question_lower for word in ['économie', 'économies', 'épargne']):
            # Question sur les économies
            top_savings = prediction_engine.df.nlargest(5, 'Économie_TND')[['Matériau', 'Économie_TND', 'Économie_Pourcentage']].to_dict('records')
            
            response_data.update({
                "focus": "économies",
                "meilleures_economies": top_savings
            })
        
        elif any(word in question_lower for word in ['fournisseur', 'vendeur', 'magasin']):
            # Question sur les fournisseurs
            supplier_stats = prediction_engine.df.groupby('Meilleur_Fournisseur').agg({
                'Prix_Unitaire_TND': 'mean',
                'Économie_TND': 'sum',
                'Matériau': 'count'
            }).to_dict('index')
            
            response_data.update({
                "focus": "fournisseurs",
                "statistiques_fournisseurs": supplier_stats
            })
        
        elif any(word in question_lower for word in ['prédire', 'prédiction', 'futur', 'tendance']):
            # Question sur les prédictions
            sample_predictions = []
            for _, row in prediction_engine.df.head(3).iterrows():
                pred = prediction_engine.predict_price(row['Matériau'])
                if "error" not in pred:
                    sample_predictions.append(pred)
            
            response_data.update({
                "focus": "prédictions",
                "exemples_predictions": sample_predictions
            })
        
        return APIResponse(
            status="success",
            data={
                "query": query.question,
                "response_type": "llm_context",
                "context": response_data,
                "suggestions": [
                    "Demandez des prédictions de prix pour des matériaux spécifiques",
                    "Obtenez des estimations complètes de projets",
                    "Comparez les fournisseurs et leurs économies",
                    "Analysez les tendances de prix par catégorie"
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends", response_model=APIResponse)
async def get_price_trends():
    """Obtenir les tendances de prix"""
    try:
        # Analyser les tendances par catégorie
        trends_by_category = prediction_engine.df.groupby('Catégorie').agg({
            'Prix_Unitaire_TND': ['mean', 'min', 'max'],
            'Économie_Pourcentage': 'mean',
            'Matériau': 'count'
        }).round(2)
        
        return APIResponse(
            status="success",
            data={
                "trends_by_category": trends_by_category.to_dict(),
                "analysis_date": datetime.now().isoformat(),
                "data_points": len(prediction_engine.df)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suppliers", response_model=APIResponse)
async def get_suppliers_analysis():
    """Analyse des fournisseurs"""
    try:
        suppliers_data = prediction_engine.df.groupby('Meilleur_Fournisseur').agg({
            'Prix_Unitaire_TND': 'mean',
            'Économie_TND': ['sum', 'mean'],
            'Matériau': 'count',
            'Économie_Pourcentage': 'mean'
        }).round(2)
        
        return APIResponse(
            status="success",
            data={
                "suppliers_analysis": suppliers_data.to_dict(),
                "best_supplier_by_savings": prediction_engine.df.groupby('Meilleur_Fournisseur')['Économie_TND'].sum().idxmax()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories", response_model=APIResponse)
async def get_categories_analysis():
    """Analyse par catégories"""
    try:
        categories_data = prediction_engine.df.groupby('Catégorie').agg({
            'Prix_Unitaire_TND': ['mean', 'min', 'max'],
            'Économie_TND': 'sum',
            'Matériau': 'count'
        }).round(2)
        
        return APIResponse(
            status="success",
            data={
                "categories_analysis": categories_data.to_dict(),
                "categories_list": prediction_engine.df['Catégorie'].unique().tolist()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour la santé de l'API
@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": not prediction_engine.df.empty,
        "model_ready": prediction_engine.model is not None
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Lancement de l'API LLM Prédictions Matériaux")
    print("📊 Accès documentation: http://localhost:8000/docs")
    print("🤖 Endpoint LLM: http://localhost:8000/llm-query")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
