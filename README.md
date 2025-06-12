# 🏗️ Construction Materials Estimation System - Tunisia Market

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-orange.svg)](https://playwright.dev/)

> **Système complet d'estimation de matériaux de construction et d'analyse immobilière pour le marché tunisien** 🇹🇳

## 📋 Description

Ce projet offre une solution complète pour l'estimation automatisée de matériaux de construction en Tunisie, incluant :

- **🔍 Web Scraping** de 525+ produits depuis brico-direct.tn
- **🏠 Analyse immobilière** de 6,036+ propriétés tunisiennes
- **🤖 API ML/LLM** pour prédictions intelligentes
- **📊 Dashboard interactif** avec Streamlit
- **💰 Système de devis** automatisé

## 🚀 Fonctionnalités Principales

### 🔧 Scraping & Collecte de Données
- **Materials**: 525+ produits construction (brico-direct.tn)
- **Immobilier**: 6,036+ propriétés (7 sites tunisiens)
- **Prix temps réel** avec historique
- **Géolocalisation** automatique

### 🧠 Intelligence Artificielle
- **Prédictions ML** avec RandomForest/XGBoost
- **API LLM** pour requêtes en langage naturel  
- **Analyse prédictive** des prix
- **Recommandations** personnalisées

### 📈 Analyse & Reporting
- **Comparaisons** multi-sources
- **Tableaux de bord** interactifs
- **Rapports PDF** automatisés
- **Économies détectées** jusqu'à 19.9%

## 🗂️ Structure du Projet

```
SCRAPER/
├── 📊 DONNEES_JSON_ORGANISEES/          # Données structurées JSON
│   ├── 01_MATERIAUX_CONSTRUCTION/       # 525+ matériaux
│   ├── 02_PROPRIETES_IMMOBILIERES/      # 6,036+ propriétés
│   ├── 03_ESTIMATIONS_DEVIS/            # Templates & devis
│   └── 04_ANALYSES_RAPPORTS/            # Analyses marché
├── 🤖 llm_api_server.py                 # Serveur API ML/LLM
├── 🔍 *_scraper.py                      # Scripts scraping
├── 📋 materials_dashboard.py            # Dashboard Streamlit
├── 💰 price_corrector_final.py          # Correction prix
└── 📊 *.csv                            # Données principales
```

## 🛠️ Installation

### Prérequis
- Python 3.12+
- Node.js (pour Playwright)
- Git

### Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/tekteku/scraper.git
cd scraper

# Créer environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer dépendances
pip install -r requirements.txt

# Installer browsers Playwright
playwright install
```
## 🚀 Démarrage Rapide

### 1. 🤖 Lancer l'API ML/LLM
```bash
python llm_api_server.py
```
**Endpoints disponibles:**
- `POST /llm-query` - Requêtes LLM
- `POST /predict` - Prédictions ML
- `GET /products` - Catalogue produits
- `POST /estimate` - Génération devis

### 2. 📊 Dashboard Interactif
```bash
streamlit run materials_dashboard.py
```

### 3. 🔍 Scraping Manuel
```bash
# Scraper matériaux construction
python brico_direct_scraper.py

# Scraper immobilier multi-sites
python multi_site_scraper.py
```

## 📊 Données Disponibles

### 🔨 Matériaux Construction (525+ produits)
- **Source**: brico-direct.tn
- **Catégories**: 8 principales
- **Prix**: TND avec historique
- **Mise à jour**: Quotidienne

### 🏠 Propriétés Immobilières (6,036+ propriétés)
- **Sources**: remax.com.tn, fi-dari.tn, mubawab.tn, etc.
- **Couverture**: Tout le territoire tunisien
- **Géolocalisation**: Coordonnées GPS
- **Prix**: m² et total

## 🔗 API Usage

### Exemple LLM Query
```python
import requests

response = requests.post("http://localhost:8000/llm-query", 
    json={"query": "Quel est le prix du ciment en Tunisie?"})
print(response.json())
```

### Exemple Prédiction ML
```python
data = {
    "surface": 120,
    "gouvernorat": "Tunis", 
    "type_propriete": "Appartement"
}
response = requests.post("http://localhost:8000/predict", json=data)
```

## 📈 Performances

- **🎯 Précision scraping**: 98.1%
- **💰 Économies détectées**: 19.9% moyenne
- **⚡ Vitesse traitement**: <2s par requête
- **📊 Couverture marché**: 100% Tunisie

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📞 Contact

**Taher Chabaane** - [@tekteku](https://github.com/tekteku)

**Lien Projet**: [https://github.com/tekteku/scraper](https://github.com/tekteku/scraper)

## 🙏 Remerciements

- [Playwright](https://playwright.dev/) - Web scraping
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Streamlit](https://streamlit.io/) - Dashboard
- [AgentQL](https://agentql.com/) - Scraping intelligent

---

<div align="center">
  <strong>🇹🇳 Made with ❤️ for the Tunisian construction market</strong>
</div>

### Running Specialized Scrapers

For specific sites only:

```powershell
# Edit tunisian_property_scraper.py to include only desired sites in SITE_CONFIGS
python tunisian_property_scraper.py
```

### Extracting Detailed Property Information

For more detailed property information, you may want to visit individual property detail pages. Modify the scraper to:

1. Collect listing URLs from search pages
2. Visit each property detail page
3. Extract comprehensive property information

## 🙏 Acknowledgements

Thanks to the following libraries and tools:
- Playwright for browser automation
- pandas for data processing
- numpy for numerical operations
