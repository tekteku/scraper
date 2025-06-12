"""
Scraper complet pour les prix des matériaux de construction en Tunisie
Collecte les données depuis plusieurs sites tunisiens de matériaux de construction
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
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("material_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MaterialScraper")

# Configuration des dossiers
MATERIALS_DATA_FOLDER = "materials_data/raw"
CLEAN_MATERIALS_FOLDER = "materials_data/clean"
SCREENSHOTS_FOLDER = "materials_data/screenshots"

for folder in [MATERIALS_DATA_FOLDER, CLEAN_MATERIALS_FOLDER, SCREENSHOTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

class MaterialScraper:
    def __init__(self):
        self.materials = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
          # Configuration des sites à scraper
        self.sites_config = [
            {
                "name": "brico-direct.tn",
                "base_url": "https://brico-direct.tn/218-construction",
                "type": "requests",
                "pagination": True,
                "max_pages": 8,
                "page_param": "p",
                "selectors": {
                    "products": ".product-container, .ajax_block_product",
                    "name": "h5 a, .product-name a, .s_title_block a",
                    "price": 'span[itemprop="price"], .price, .content_price',
                    "description": ".product-desc, .short-desc",
                    "image": ".left-block img, .product-image img"
                }
            },
            {
                "name": "comaf.tn",
                "url": "https://www.comaf.tn/70-materiaux-de-construction.html",
                "type": "requests",  # Utilise requests + BeautifulSoup
                "selectors": {
                    "products": ".product-container, .ajax_block_product, .item-container",
                    "name": ".product-name, h3, .product-title, a[title]",
                    "price": ".price, .content_price, .product-price",
                    "description": ".product-desc, .short-desc, p",
                    "image": "img.replace-2x, .product-image img, img"
                }
            },
            {
                "name": "sabradecommerce.com",
                "url": "http://sabradecommerce.com/12-produit-de-construction",
                "type": "requests",
                "selectors": {
                    "products": ".ajax_block_product, .product-container",
                    "name": ".s_title_block a, .product-name a, h5 a",
                    "price": ".content_price, .price, .right-block .price",
                    "description": ".product-desc",
                    "image": ".left-block img, .product-image img"
                }
            },
            {
                "name": "arkan.tn",
                "url": "https://arkan.tn/materiaux-de-construction.html",
                "type": "playwright",  # Utilise Playwright pour les sites dynamiques
                "selectors": {
                    "products": ".product-item, .item, .product-container",
                    "name": "h3, .product-title, .item-title",
                    "price": ".price, .product-price, .cost",
                    "description": ".description, .product-desc",
                    "image": ".product-image img, img"
                }
            },
            {
                "name": "tunisianet.com.tn",
                "url": "https://www.tunisianet.com.tn/631-bricolage-jardinage",
                "type": "requests",
                "selectors": {
                    "products": ".ajax_block_product, .product-miniature",
                    "name": ".product-title a, h3 a",
                    "price": ".price, .product-price-and-shipping .price",
                    "description": ".product-desc",
                    "image": ".product-thumbnail img"
                }
            },
            {
                "name": "jumia.com.tn",
                "url": "https://www.jumia.com.tn/bricolage-jardinage/",
                "type": "playwright",
                "selectors": {
                    "products": "article.prd, .sku",
                    "name": ".name, .title, h3",
                    "price": ".prc, .price-has-discount, .price",
                    "description": ".description",
                    "image": ".img img"
                }
            }
        ]
    
    def clean_text(self, text):
        """Nettoie le texte"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def clean_price(self, price_text):
        """Extrait et nettoie les prix"""
        if not price_text:
            return None, ""
        
        original_text = price_text.strip()
        
        # Patterns pour différents formats de prix
        price_patterns = [
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:TND|DT|dt|dinars?|د\.ت)',
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:€|EUR)',
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:\$|USD)',
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text, re.IGNORECASE)
            if match:
                price_str = match.group(1)
                # Normalise le format (virgule/point)
                if ',' in price_str and '.' in price_str:
                    # Format 1,234.56
                    price_str = price_str.replace(',', '')
                elif ',' in price_str:
                    # Vérifie si c'est un séparateur de milliers ou de décimales
                    parts = price_str.split(',')
                    if len(parts) == 2 and len(parts[1]) <= 2:
                        # Décimales: 123,45
                        price_str = price_str.replace(',', '.')
                    else:
                        # Milliers: 1,234
                        price_str = price_str.replace(',', '')
                
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
            r'\b(?:m2|m²|mètre[s]?\s*carré[s]?|metre[s]?\s*carre[s]?)\b': 'm²',
            r'\b(?:m3|m³|mètre[s]?\s*cube[s]?|metre[s]?\s*cube[s]?)\b': 'm³',
            r'\b(?:ml|m|mètre[s]?\s*linéaire[s]?|metre[s]?\s*lineaire[s]?)\b': 'ml',
            r'\b(?:kg|kilogramme[s]?)\b': 'kg',
            r'\b(?:tonne[s]?|t)\b': 't',
            r'\b(?:litre[s]?|l)\b': 'l',
            r'\b(?:sac[s]?)\b': 'sac',
            r'\b(?:pièce[s]?|piece[s]?|pcs|pc|unité[s]?|unite[s]?)\b': 'pièce',
            r'\b(?:palette[s]?)\b': 'palette',
            r'\b(?:boîte[s]?|boite[s]?|box)\b': 'boîte',
            r'\b(?:rouleau[x]?)\b': 'rouleau',
            r'\b(?:tube[s]?)\b': 'tube'
        }
        
        text_lower = text.lower()
        for pattern, unit in units_map.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return unit
        
        return ""
    
    def categorize_material(self, name, description=""):
        """Catégorise automatiquement les matériaux"""
        text = (name + " " + description).lower()
        
        categories = {
            'Ciment et béton': [
                'ciment', 'béton', 'beton', 'mortier', 'chaux', 'clinker',
                'portland', 'hydraulique', 'sable', 'gravier', 'agregat'
            ],
            'Carrelage et revêtements': [
                'carrelage', 'carreau', 'faience', 'faïence', 'revetement',
                'revêtement', 'sol', 'mur', 'ceramique', 'céramique', 'marbre'
            ],
            'Peinture et enduits': [
                'peinture', 'enduit', 'vernis', 'laque', 'primer', 'sous-couche',
                'acrylique', 'glycero', 'anti-rouille', 'pinceau', 'rouleau'
            ],
            'Isolation thermique': [
                'isolation', 'isolant', 'laine', 'polystyrene', 'polystyrène',
                'polyurethane', 'polyuréthane', 'thermique', 'acoustique'
            ],
            'Plomberie': [
                'tuyau', 'robinet', 'pvc', 'raccord', 'plomberie', 'sanitaire',
                'canalisation', 'siphon', 'joint', 'colle'
            ],
            'Électricité': [
                'cable', 'câble', 'fil', 'electrique', 'électrique', 'prise',
                'interrupteur', 'disjoncteur', 'tableau', 'gaine'
            ],
            'Menuiserie et bois': [
                'bois', 'porte', 'fenetre', 'fenêtre', 'menuiserie', 'planche',
                'contreplaque', 'contreplaqué', 'agglomere', 'aggloméré', 'pin'
            ],
            'Fer et métallurgie': [
                'fer', 'acier', 'rond', 'ferraillage', 'treillis', 'poutrelle',
                'corniere', 'cornière', 'tole', 'tôle', 'galvanise'
            ],
            'Toiture et étanchéité': [
                'tuile', 'toiture', 'zinc', 'gouttiere', 'gouttière', 'etancheite',
                'étanchéité', 'membrane', 'bardeau', 'couverture'
            ],
            'Outillage': [
                'outil', 'marteau', 'perceuse', 'scie', 'tournevis', 'clé',
                'niveau', 'mètre', 'équerre', 'pelle', 'brouette'
            ],
            'Quincaillerie': [
                'vis', 'clou', 'boulon', 'ecrou', 'écrou', 'rondelle',
                'cheville', 'serrure', 'poignee', 'poignée', 'penture'
            ]
        }
          for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'Autres matériaux'
    
    def scrape_with_requests(self, site_config):
        """Scrape un site en utilisant requests + BeautifulSoup"""
        site_name = site_config["name"]
        
        # Gestion de la pagination pour brico-direct.tn
        if site_config.get("pagination", False):
            base_url = site_config["base_url"]
            max_pages = site_config.get("max_pages", 1)
            page_param = site_config.get("page_param", "p")
            
            for page in range(1, max_pages + 1):
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}?{page_param}={page}"
                
                logger.info(f"Scraping {site_name} - Page {page}: {url}")
                self._scrape_single_page_requests(url, site_config, site_name)
                
                # Pause entre les pages
                time.sleep(random.uniform(2, 4))
        else:
            # Site sans pagination
            url = site_config["url"]
            logger.info(f"Scraping {site_name} avec requests...")
            self._scrape_single_page_requests(url, site_config, site_name)
    
    def _scrape_single_page_requests(self, url, site_config, site_name):
        """Scrape une seule page avec requests"""
        selectors = site_config["selectors"]
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche des produits
            products = soup.select(selectors["products"])
            logger.info(f"Trouvé {len(products)} produits sur {site_name}")
            
            for product in products:
                try:
                    # Extraction du nom
                    name_elem = product.select_one(selectors["name"])
                    name = self.clean_text(name_elem.get_text() if name_elem else "")
                    
                    if not name:
                        continue
                    
                    # Extraction du prix
                    price_elem = product.select_one(selectors["price"])
                    price_text = price_elem.get_text() if price_elem else ""
                    price_value, price_original = self.clean_price(price_text)
                    
                    # Extraction de la description
                    desc_elem = product.select_one(selectors["description"])
                    description = self.clean_text(desc_elem.get_text() if desc_elem else "")
                    
                    # Extraction de l'image
                    img_elem = product.select_one(selectors["image"])
                    image_url = ""
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src') or ""
                        if image_url and not image_url.startswith('http'):
                            image_url = urljoin(url, image_url)
                    
                    # Extraction de l'unité
                    unit = self.extract_unit(name + " " + description + " " + price_text)
                    
                    # Catégorisation
                    category = self.categorize_material(name, description)
                    
                    self.materials.append({
                        'nom': name,
                        'prix_tnd': price_value,
                        'prix_original': price_original,
                        'unite': unit,
                        'categorie': category,
                        'description': description,
                        'image_url': image_url,
                        'source': site_name,
                        'url_source': url,
                        'date_extraction': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement d'un produit sur {site_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur lors du scraping de {url}: {e}")
    
    def scrape_with_playwright(self, site_config):
        """Scrape un site en utilisant Playwright"""
        site_name = site_config["name"]
        url = site_config["url"]
        selectors = site_config["selectors"]
        
        logger.info(f"Scraping {site_name} avec Playwright...")
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)  # Attendre le chargement dynamique
                
                # Prendre une capture d'écran pour debug
                screenshot_path = os.path.join(SCREENSHOTS_FOLDER, f"{site_name}_{TIMESTAMP}.png")
                page.screenshot(path=screenshot_path)
                
                # Recherche des produits
                products = page.query_selector_all(selectors["products"])
                logger.info(f"Trouvé {len(products)} produits sur {site_name}")
                
                for i, product in enumerate(products):
                    try:
                        # Extraction du nom
                        name_elem = product.query_selector(selectors["name"])
                        name = self.clean_text(name_elem.text_content() if name_elem else "")
                        
                        if not name:
                            continue
                        
                        # Extraction du prix
                        price_elem = product.query_selector(selectors["price"])
                        price_text = price_elem.text_content() if price_elem else ""
                        price_value, price_original = self.clean_price(price_text)
                        
                        # Extraction de la description
                        desc_elem = product.query_selector(selectors["description"])
                        description = self.clean_text(desc_elem.text_content() if desc_elem else "")
                        
                        # Extraction de l'image
                        img_elem = product.query_selector(selectors["image"])
                        image_url = ""
                        if img_elem:
                            image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ""
                            if image_url and not image_url.startswith('http'):
                                image_url = urljoin(url, image_url)
                        
                        # Extraction de l'unité
                        unit = self.extract_unit(name + " " + description + " " + price_text)
                        
                        # Catégorisation
                        category = self.categorize_material(name, description)
                        
                        self.materials.append({
                            'nom': name,
                            'prix_tnd': price_value,
                            'prix_original': price_original,
                            'unite': unit,
                            'categorie': category,
                            'description': description,
                            'image_url': image_url,
                            'source': site_name,
                            'url_source': url,
                            'date_extraction': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement du produit {i+1} sur {site_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Erreur lors du scraping de {site_name}: {e}")
            
            finally:
                browser.close()
    
    def save_raw_data(self):
        """Sauvegarde les données brutes"""
        if not self.materials:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        # CSV
        csv_file = os.path.join(MATERIALS_DATA_FOLDER, f"materials_raw_{TIMESTAMP}.csv")
        df = pd.DataFrame(self.materials)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        # JSON
        json_file = os.path.join(MATERIALS_DATA_FOLDER, f"materials_raw_{TIMESTAMP}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.materials, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Données brutes sauvegardées: {len(self.materials)} matériaux")
        logger.info(f"CSV: {csv_file}")
        logger.info(f"JSON: {json_file}")
    
    def clean_and_export_data(self):
        """Nettoie et exporte les données finales"""
        if not self.materials:
            logger.warning("Aucune donnée à nettoyer")
            return
        
        logger.info("Nettoyage des données...")
        
        # Conversion en DataFrame
        df = pd.DataFrame(self.materials)
        
        # Suppression des doublons
        initial_count = len(df)
        df = df.drop_duplicates(subset=['nom', 'source'], keep='first')
        logger.info(f"Doublons supprimés: {initial_count - len(df)}")
        
        # Filtrage des données valides
        df = df[df['nom'].str.len() > 3]  # Noms trop courts
        df = df[~df['nom'].str.contains(r'^[^a-zA-ZÀ-ÿ]*$', na=False)]  # Noms sans lettres
        
        # Ajout de colonnes calculées
        df['has_price'] = df['prix_tnd'].notna()
        df['price_range'] = pd.cut(df['prix_tnd'], 
                                  bins=[0, 50, 200, 500, 1000, float('inf')], 
                                  labels=['0-50 TND', '50-200 TND', '200-500 TND', '500-1000 TND', '1000+ TND'])
        
        # Statistiques par catégorie
        stats = df.groupby('categorie').agg({
            'nom': 'count',
            'prix_tnd': ['mean', 'median', 'min', 'max'],
            'has_price': 'sum'
        }).round(2)
        
        # Export des données nettoyées
        clean_csv = os.path.join(CLEAN_MATERIALS_FOLDER, f"materials_clean_{TIMESTAMP}.csv")
        df.to_csv(clean_csv, index=False, encoding='utf-8-sig')
        
        # Export des statistiques
        stats_csv = os.path.join(CLEAN_MATERIALS_FOLDER, f"materials_stats_{TIMESTAMP}.csv")
        stats.to_csv(stats_csv, encoding='utf-8-sig')
        
        # Rapport de synthèse
        report = {
            'date_extraction': datetime.now().isoformat(),
            'total_materials': len(df),
            'materials_with_price': df['has_price'].sum(),
            'categories': df['categorie'].value_counts().to_dict(),
            'sources': df['source'].value_counts().to_dict(),
            'price_stats': {
                'min': float(df['prix_tnd'].min()) if df['prix_tnd'].notna().any() else None,
                'max': float(df['prix_tnd'].max()) if df['prix_tnd'].notna().any() else None,
                'mean': float(df['prix_tnd'].mean()) if df['prix_tnd'].notna().any() else None,
                'median': float(df['prix_tnd'].median()) if df['prix_tnd'].notna().any() else None
            }
        }
        
        report_file = os.path.join(CLEAN_MATERIALS_FOLDER, f"extraction_report_{TIMESTAMP}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Données nettoyées exportées: {len(df)} matériaux")
        logger.info(f"CSV nettoyé: {clean_csv}")
        logger.info(f"Statistiques: {stats_csv}")
        logger.info(f"Rapport: {report_file}")
        
        # Affichage des statistiques
        logger.info("\n=== STATISTIQUES D'EXTRACTION ===")
        logger.info(f"Total matériaux collectés: {len(df)}")
        logger.info(f"Matériaux avec prix: {df['has_price'].sum()}")
        logger.info(f"Sources: {', '.join(df['source'].unique())}")
        logger.info("\nRépartition par catégorie:")
        for cat, count in df['categorie'].value_counts().head(10).items():
            logger.info(f"  {cat}: {count}")
    
    def run_full_scraping(self):
        """Lance le scraping complet"""
        logger.info("=== DÉBUT DU SCRAPING DES MATÉRIAUX DE CONSTRUCTION ===")
        
        for site_config in self.sites_config:
            try:
                if site_config["type"] == "requests":
                    self.scrape_with_requests(site_config)
                elif site_config["type"] == "playwright":
                    self.scrape_with_playwright(site_config)
                
                # Pause entre les sites
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"Erreur critique pour {site_config['name']}: {e}")
                continue
        
        # Sauvegarde et nettoyage
        self.save_raw_data()
        self.clean_and_export_data()
        
        logger.info("=== SCRAPING TERMINÉ ===")

def main():
    scraper = MaterialScraper()
    scraper.run_full_scraping()

if __name__ == "__main__":
    main()
