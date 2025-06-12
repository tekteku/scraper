"""
Scraper simple pour les prix des matériaux de construction en Tunisie
Version simplifiée utilisant seulement requests + BeautifulSoup
"""

import os
import re
import csv
import json
import time
import random
import logging
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_material_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleMaterialScraper")

# Configuration des dossiers
MATERIALS_DATA_FOLDER = "materials_data/raw"
CLEAN_MATERIALS_FOLDER = "materials_data/clean"

for folder in [MATERIALS_DATA_FOLDER, CLEAN_MATERIALS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

class SimpleMaterialScraper:
    def __init__(self):
        self.materials = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configuration des sites à scraper (simplifiée)
        self.sites_config = [
            {
                'name': 'Comaf',
                'base_url': 'https://comaf.tn',
                'search_pages': [
                    'https://comaf.tn/catalogsearch/result/?q=ciment',
                    'https://comaf.tn/catalogsearch/result/?q=fer',
                    'https://comaf.tn/catalogsearch/result/?q=carrelage',
                    'https://comaf.tn/catalogsearch/result/?q=peinture',
                ],
                'product_selector': '.product-item',
                'name_selector': '.product-item-name a',
                'price_selector': '.price',
                'method': 'requests'
            },
            {
                'name': 'TunisiaNet',
                'base_url': 'https://www.tunisianet.com.tn',
                'search_pages': [
                    'https://www.tunisianet.com.tn/recherche?controller=search&s=ciment',
                    'https://www.tunisianet.com.tn/recherche?controller=search&s=fer',
                    'https://www.tunisianet.com.tn/recherche?controller=search&s=carrelage',
                ],
                'product_selector': '.product-miniature',
                'name_selector': '.product-title a',
                'price_selector': '.price',
                'method': 'requests'
            }
        ]
        
        # Catégories de matériaux
        self.categories = {
            'ciment': ['ciment', 'cement', 'béton', 'mortier'],
            'fer': ['fer', 'acier', 'rond', 'barre', 'steel'],
            'carrelage': ['carrelage', 'ceramic', 'tile', 'faience'],
            'peinture': ['peinture', 'paint', 'vernis', 'enduit'],
            'sanitaire': ['lavabo', 'wc', 'douche', 'robinet'],
            'électricité': ['câble', 'fil', 'disjoncteur', 'prise'],
            'plomberie': ['tuyau', 'pipe', 'raccord', 'valve'],
            'isolation': ['laine', 'isolant', 'polystyrène'],
            'toiture': ['tuile', 'tôle', 'zinc', 'roof'],
            'menuiserie': ['porte', 'fenêtre', 'bois', 'wood'],
            'autres': []
        }

    def clean_price(self, price_text):
        """Nettoie et extrait le prix"""
        if not price_text:
            return None, None
        
        # Supprime les espaces et convertit en minuscules
        price_clean = price_text.strip().lower()
        
        # Patterns pour extraire les prix
        patterns = [
            r'(\d+[,.]?\d*)\s*(dt|tnd|dinar)',  # TND
            r'(\d+[,.]?\d*)\s*(€|eur|euro)',     # EUR
            r'(\d+[,.]?\d*)\s*(\$|usd|dollar)',  # USD
            r'(\d+[,.]?\d*)',                     # Nombre seul
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_clean)
            if match:
                price_value = float(match.group(1).replace(',', '.'))
                currency = match.group(2) if len(match.groups()) > 1 else 'TND'
                return price_value, currency
        
        return None, None

    def categorize_material(self, name):
        """Catégorise automatiquement le matériau"""
        name_lower = name.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category
        
        return 'autres'

    def extract_unit(self, text):
        """Extrait l'unité de mesure"""
        units = ['m²', 'm2', 'kg', 'g', 'l', 'ml', 'pièce', 'pc', 'sac', 'boîte', 'rouleau']
        text_lower = text.lower()
        
        for unit in units:
            if unit.lower() in text_lower:
                return unit
        
        return 'pièce'  # Unité par défaut

    def scrape_site_with_requests(self, site_config):
        """Scrape un site avec requests + BeautifulSoup"""
        logger.info(f"Scraping {site_config['name']} avec requests...")
        
        for search_url in site_config['search_pages']:
            try:
                logger.info(f"Scraping page: {search_url}")
                
                # Délai aléatoire
                time.sleep(random.uniform(2, 5))
                
                response = self.session.get(search_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                products = soup.select(site_config['product_selector'])
                
                logger.info(f"Trouvé {len(products)} produits sur cette page")
                
                for product in products:
                    try:
                        # Extraction du nom
                        name_elem = product.select_one(site_config['name_selector'])
                        name = name_elem.get_text(strip=True) if name_elem else "Nom non trouvé"
                        
                        # Extraction du prix
                        price_elem = product.select_one(site_config['price_selector'])
                        price_text = price_elem.get_text(strip=True) if price_elem else ""
                        
                        price_value, currency = self.clean_price(price_text)
                        
                        if price_value and name != "Nom non trouvé":
                            material_data = {
                                'nom': name,
                                'prix': price_value,
                                'devise': currency,
                                'unite': self.extract_unit(name),
                                'categorie': self.categorize_material(name),
                                'site': site_config['name'],
                                'url': search_url,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            self.materials.append(material_data)
                            logger.debug(f"Matériau ajouté: {name} - {price_value} {currency}")
                    
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction d'un produit: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Erreur lors du scraping de {search_url}: {e}")
                continue

    def run_scraping(self):
        """Exécute le scraping complet"""
        logger.info("=== DÉBUT DU SCRAPING DES MATÉRIAUX ===")
        
        for site_config in self.sites_config:
            try:
                logger.info(f"Scraping du site: {site_config['name']}")
                self.scrape_site_with_requests(site_config)
                
                # Pause entre les sites
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"Erreur critique pour {site_config['name']}: {e}")
                continue
        
        # Sauvegarde des données
        self.save_data()
        
        logger.info("=== SCRAPING TERMINÉ ===")

    def save_data(self):
        """Sauvegarde les données collectées"""
        if not self.materials:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        # Sauvegarde JSON brute
        json_file = os.path.join(MATERIALS_DATA_FOLDER, f"materials_raw_{TIMESTAMP}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.materials, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV
        csv_file = os.path.join(MATERIALS_DATA_FOLDER, f"materials_raw_{TIMESTAMP}.csv")
        df = pd.DataFrame(self.materials)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Données nettoyées
        self.create_clean_data()
        
        logger.info(f"Données sauvegardées:")
        logger.info(f"- JSON brut: {json_file}")
        logger.info(f"- CSV brut: {csv_file}")
        logger.info(f"- Total matériaux: {len(self.materials)}")

    def create_clean_data(self):
        """Crée une version nettoyée des données"""
        if not self.materials:
            return
        
        df = pd.DataFrame(self.materials)
        
        # Suppression des doublons
        df_clean = df.drop_duplicates(subset=['nom', 'site'])
        
        # Filtrage des prix valides
        df_clean = df_clean[df_clean['prix'] > 0]
        
        # Statistiques par catégorie
        stats = df_clean.groupby('categorie').agg({
            'prix': ['count', 'mean', 'min', 'max'],
            'nom': 'count'
        }).round(2)
        
        # Sauvegarde des données nettoyées
        clean_csv = os.path.join(CLEAN_MATERIALS_FOLDER, f"materials_clean_{TIMESTAMP}.csv")
        df_clean.to_csv(clean_csv, index=False, encoding='utf-8')
        
        # Sauvegarde des statistiques
        stats_file = os.path.join(CLEAN_MATERIALS_FOLDER, f"materials_stats_{TIMESTAMP}.json")
        stats_dict = {}
        for category in stats.index:
            stats_dict[category] = {
                'count': int(stats.loc[category, ('prix', 'count')]),
                'prix_moyen': float(stats.loc[category, ('prix', 'mean')]),
                'prix_min': float(stats.loc[category, ('prix', 'min')]),
                'prix_max': float(stats.loc[category, ('prix', 'max')])
            }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Données nettoyées sauvegardées: {clean_csv}")
        logger.info(f"Statistiques sauvegardées: {stats_file}")
        logger.info(f"Matériaux après nettoyage: {len(df_clean)}")

def main():
    scraper = SimpleMaterialScraper()
    scraper.run_scraping()

if __name__ == "__main__":
    main()
