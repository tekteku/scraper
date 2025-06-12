"""
Scraper spécialisé pour brico-direct.tn - Site de matériaux de construction tunisien
Collecte les données depuis les 8 pages de la section construction
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
        logging.FileHandler("brico_direct_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BricoDirectScraper")

# Configuration des dossiers
MATERIALS_DATA_FOLDER = "materials_data/raw"
CLEAN_MATERIALS_FOLDER = "materials_data/clean"

for folder in [MATERIALS_DATA_FOLDER, CLEAN_MATERIALS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

class BricoDirectScraper:
    def __init__(self):
        self.materials = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configuration du site brico-direct.tn
        self.base_url = "https://brico-direct.tn/218-construction"
        self.max_pages = 8
        
        # Catégories de matériaux
        self.categories = {
            'Ciment et béton': ['ciment', 'béton', 'beton', 'mortier', 'chaux', 'sable', 'gravier'],
            'Carrelage et revêtements': ['carrelage', 'carreau', 'faience', 'faïence', 'revetement', 'sol', 'mur'],
            'Peinture et enduits': ['peinture', 'enduit', 'vernis', 'pinceau', 'rouleau', 'brosse'],
            'Isolation': ['isolation', 'isolant', 'laine', 'polystyrene', 'polystyrène'],
            'Plomberie': ['tuyau', 'robinet', 'pvc', 'raccord', 'plomberie', 'sanitaire'],
            'Électricité': ['cable', 'câble', 'fil', 'electrique', 'électrique', 'prise'],
            'Menuiserie et bois': ['bois', 'porte', 'fenetre', 'fenêtre', 'menuiserie', 'planche'],
            'Fer et métallurgie': ['fer', 'acier', 'rond', 'ferraillage', 'treillis', 'tole'],
            'Toiture': ['tuile', 'toiture', 'zinc', 'gouttiere', 'gouttière', 'etancheite'],
            'Outillage': ['outil', 'marteau', 'perceuse', 'scie', 'tournevis', 'clé', 'niveau', 
                         'truelle', 'spatule', 'taloche', 'pied de biche', 'grattoir', 'pince',
                         'pistolet', 'massette', 'echelle', 'escabeau', 'equerre', 'regle'],
            'Quincaillerie': ['vis', 'clou', 'boulon', 'ecrou', 'écrou', 'rondelle', 'cheville',
                             'croisillon', 'mastic', 'silicone', 'bidon', 'seau', 'auge']
        }

    def clean_text(self, text):
        """Nettoie le texte"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    def clean_price(self, price_text):
        """Extrait et nettoie les prix tunisiens"""
        if not price_text:
            return None, ""
        
        original_text = price_text.strip()
        
        # Patterns pour les prix tunisiens (DT/TND)
        price_patterns = [
            r'(\d+(?:[,.\s]\d{3})*(?:[.,]\d{1,2})?)\s*(?:DT|dt|TND|tnd|dinars?)',
            r'(\d+(?:[,.\s]\d{3})*(?:[.,]\d{1,2})?)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text, re.IGNORECASE)
            if match:
                price_str = match.group(1)
                # Nettoie les séparateurs
                price_str = re.sub(r'[,\s]', '', price_str)
                price_str = price_str.replace(',', '.')
                
                try:
                    return float(price_str), original_text
                except ValueError:
                    continue
        
        return None, original_text

    def extract_unit(self, text):
        """Extrait l'unité de mesure"""
        if not text:
            return ""
        
        units_map = {
            r'\b(?:m2|m²|metre[s]?\s*carre[s]?)\b': 'm²',
            r'\b(?:m3|m³|metre[s]?\s*cube[s]?)\b': 'm³',
            r'\b(?:ml|m|metre[s]?)\b': 'ml',
            r'\b(?:kg|kilogramme[s]?)\b': 'kg',
            r'\b(?:tonne[s]?|t)\b': 't',
            r'\b(?:litre[s]?|l)\b': 'l',
            r'\b(?:sac[s]?)\b': 'sac',
            r'\b(?:piece[s]?|pcs|pc|unite[s]?)\b': 'pièce',
            r'\b(?:pack|paquet)\b': 'pack',
            r'\b(?:boite[s]?|box)\b': 'boîte',
            r'\b(?:rouleau[x]?)\b': 'rouleau'
        }
        
        text_lower = text.lower()
        for pattern, unit in units_map.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return unit
        
        return 'pièce'  # Unité par défaut

    def categorize_material(self, name, description=""):
        """Catégorise automatiquement les matériaux"""
        text = (name + " " + description).lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'Autres matériaux'

    def scrape_page(self, page_num):
        """Scrape une page spécifique"""
        if page_num == 1:
            url = self.base_url
        else:
            url = f"{self.base_url}?p={page_num}"
        
        logger.info(f"Scraping page {page_num}: {url}")
        
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche des produits avec différents sélecteurs possibles
            products = []
            selectors = [
                '.ajax_block_product',
                '.product-container', 
                '.product-miniature',
                '.product-item'
            ]
            
            for selector in selectors:
                products = soup.select(selector)
                if products:
                    logger.info(f"Trouvé {len(products)} produits avec le sélecteur '{selector}'")
                    break
            
            if not products:
                logger.warning(f"Aucun produit trouvé sur la page {page_num}")
                return
            
            for i, product in enumerate(products):
                try:
                    # Extraction du nom avec plusieurs sélecteurs
                    name = ""
                    name_selectors = [
                        'h5 a',
                        '.product-name a',
                        '.s_title_block a',
                        '.product-title a',
                        'a[title]',
                        'h3 a'
                    ]
                    
                    for selector in name_selectors:
                        name_elem = product.select_one(selector)
                        if name_elem:
                            name = self.clean_text(name_elem.get_text())
                            if not name:
                                name = self.clean_text(name_elem.get('title', ''))
                            break
                    
                    if not name:
                        continue
                    
                    # Extraction du prix avec plusieurs sélecteurs
                    price_text = ""
                    price_selectors = [
                        'span[itemprop="price"]',
                        '.price',
                        '.content_price',
                        '.product-price'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = product.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text()
                            break
                    
                    price_value, price_original = self.clean_price(price_text)
                    
                    # Extraction de la description
                    description = ""
                    desc_selectors = ['.product-desc', '.short-desc', 'p']
                    for selector in desc_selectors:
                        desc_elem = product.select_one(selector)
                        if desc_elem:
                            description = self.clean_text(desc_elem.get_text())
                            break
                    
                    # Extraction de l'URL du produit
                    product_url = ""
                    link_elem = product.select_one('a')
                    if link_elem:
                        product_url = link_elem.get('href', '')
                        if product_url and not product_url.startswith('http'):
                            product_url = urljoin(url, product_url)
                    
                    # Extraction de l'unité
                    unit = self.extract_unit(name + " " + description + " " + price_text)
                    
                    # Catégorisation
                    category = self.categorize_material(name, description)
                    
                    material_data = {
                        'nom': name,
                        'prix_tnd': price_value,
                        'prix_original': price_original,
                        'unite': unit,
                        'categorie': category,
                        'description': description,
                        'url_produit': product_url,
                        'source': 'brico-direct.tn',
                        'page': page_num,
                        'url_source': url,
                        'date_extraction': datetime.now().isoformat()
                    }
                    
                    self.materials.append(material_data)
                    logger.debug(f"Produit ajouté: {name} - {price_value} TND")
                    
                except Exception as e:
                    logger.warning(f"Erreur produit {i+1} page {page_num}: {e}")
                    continue
            
            logger.info(f"Page {page_num} terminée: {len([m for m in self.materials if m['page'] == page_num])} produits collectés")
            
        except Exception as e:
            logger.error(f"Erreur page {page_num}: {e}")

    def run_full_scraping(self):
        """Lance le scraping complet des 8 pages"""
        logger.info("=== DÉBUT SCRAPING BRICO-DIRECT.TN ===")
        logger.info(f"Scraping de {self.max_pages} pages")
        
        for page in range(1, self.max_pages + 1):
            self.scrape_page(page)
            
            # Pause entre les pages
            if page < self.max_pages:
                sleep_time = random.uniform(3, 6)
                logger.info(f"Pause de {sleep_time:.1f}s avant page suivante...")
                time.sleep(sleep_time)
        
        # Sauvegarde des données
        self.save_data()
        
        logger.info("=== SCRAPING TERMINÉ ===")
        logger.info(f"Total produits collectés: {len(self.materials)}")

    def save_data(self):
        """Sauvegarde les données collectées"""
        if not self.materials:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        # Sauvegarde JSON brute
        json_file = os.path.join(MATERIALS_DATA_FOLDER, f"brico_direct_raw_{TIMESTAMP}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.materials, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV brute
        csv_file = os.path.join(MATERIALS_DATA_FOLDER, f"brico_direct_raw_{TIMESTAMP}.csv")
        df = pd.DataFrame(self.materials)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Données nettoyées et statistiques
        self.create_clean_data()
        
        logger.info(f"Données sauvegardées:")
        logger.info(f"- JSON: {json_file}")
        logger.info(f"- CSV: {csv_file}")

    def create_clean_data(self):
        """Crée des données nettoyées avec statistiques"""
        if not self.materials:
            return
        
        df = pd.DataFrame(self.materials)
        
        # Nettoyage
        df_clean = df.drop_duplicates(subset=['nom'], keep='first')
        df_clean = df_clean[df_clean['nom'].str.len() > 3]
          # Statistiques
        stats = {
            'date_extraction': datetime.now().isoformat(),
            'total_produits': int(len(df_clean)),
            'produits_avec_prix': int(df_clean['prix_tnd'].notna().sum()),
            'prix_moyen': float(df_clean['prix_tnd'].mean()) if df_clean['prix_tnd'].notna().any() else 0,
            'prix_min': float(df_clean['prix_tnd'].min()) if df_clean['prix_tnd'].notna().any() else 0,
            'prix_max': float(df_clean['prix_tnd'].max()) if df_clean['prix_tnd'].notna().any() else 0,
            'categories': {k: int(v) for k, v in df_clean['categorie'].value_counts().to_dict().items()},
            'repartition_pages': {str(k): int(v) for k, v in df_clean['page'].value_counts().to_dict().items()}
        }
        
        # Sauvegarde données nettoyées
        clean_csv = os.path.join(CLEAN_MATERIALS_FOLDER, f"brico_direct_clean_{TIMESTAMP}.csv")
        df_clean.to_csv(clean_csv, index=False, encoding='utf-8')
        
        # Sauvegarde statistiques
        stats_file = os.path.join(CLEAN_MATERIALS_FOLDER, f"brico_direct_stats_{TIMESTAMP}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Données nettoyées: {clean_csv}")
        logger.info(f"Statistiques: {stats_file}")
        
        # Affichage des statistiques
        logger.info("\n=== STATISTIQUES ===")
        logger.info(f"Produits collectés: {stats['total_produits']}")
        logger.info(f"Avec prix: {stats['produits_avec_prix']}")
        logger.info(f"Prix moyen: {stats['prix_moyen']:.2f} TND")
        logger.info(f"Fourchette: {stats['prix_min']:.2f} - {stats['prix_max']:.2f} TND")
        logger.info("\nTop catégories:")
        for cat, count in list(stats['categories'].items())[:5]:
            logger.info(f"  {cat}: {count}")

def main():
    scraper = BricoDirectScraper()
    scraper.run_full_scraping()

if __name__ == "__main__":
    main()
