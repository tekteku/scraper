#!/usr/bin/env python3
"""
Scraper Multi-Sites pour Matériaux de Construction Tunisiens
Sites ciblés: comaf.tn, sabradecommerce.com, arkan.tn, brico-direct.tn
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import logging
from datetime import datetime
import csv
import json
import random
import time

class MultiSiteMaterialScraper:
    def __init__(self):
        self.setup_logging()
        self.results = []
        
        # Configuration des sites
        self.sites_config = {
            'brico_direct': {
                'base_url': 'https://brico-direct.tn',
                'search_path': '/construction-et-gros-oeuvre/?page={}',
                'selectors': {
                    'price': 'span[itemprop="price"]',
                    'name': 'h5 a',
                    'image': '.product-image img'
                },
                'pages': 8
            },
            'comaf': {
                'base_url': 'https://comaf.tn',
                'search_path': '/categorie/materiaux-construction/',
                'selectors': {
                    'price': '.price, .prix, [class*="price"]',
                    'name': '.product-title, h3, h4, .nom-produit',
                    'image': '.product-img img, .image img'
                },
                'pages': 5
            },
            'sabra': {
                'base_url': 'https://sabradecommerce.com',
                'search_path': '/construction/',
                'selectors': {
                    'price': '.price, .prix, .montant',
                    'name': '.product-name, .titre, h3',
                    'image': '.product-image img'
                },
                'pages': 3
            },
            'arkan': {
                'base_url': 'https://arkan.tn',
                'search_path': '/materiaux/',
                'selectors': {
                    'price': '.price, .prix-produit',
                    'name': '.product-title, .nom',
                    'image': '.produit-img img'
                },
                'pages': 4
            }
        }
    
    def setup_logging(self):
        """Configuration du logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('multi_site_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def scrape_site(self, site_name, config):
        """Scraper un site spécifique"""
        self.logger.info(f"🔍 Début scraping de {site_name}")
        site_results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Scraper toutes les pages
                for page_num in range(1, config['pages'] + 1):
                    try:
                        url = config['base_url'] + config['search_path'].format(page_num)
                        self.logger.info(f"📄 Scraping {site_name} - Page {page_num}: {url}")
                        
                        await page.goto(url, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        # Extraire les données
                        products = await self.extract_products(page, config['selectors'], site_name)
                        site_results.extend(products)
                        
                        self.logger.info(f"✅ {len(products)} produits extraits de {site_name} page {page_num}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Erreur page {page_num} de {site_name}: {e}")
                        continue
                
            except Exception as e:
                self.logger.error(f"❌ Erreur générale {site_name}: {e}")
            
            finally:
                await browser.close()
        
        self.logger.info(f"🏁 {site_name} terminé: {len(site_results)} produits")
        return site_results
    
    async def extract_products(self, page, selectors, site_name):
        """Extraire les produits d'une page"""
        products = []
        
        try:
            # Attendre le chargement du contenu
            await page.wait_for_load_state('networkidle')
            
            # Chercher tous les éléments prix
            price_elems = await page.query_selector_all(selectors['price'])
            name_elems = await page.query_selector_all(selectors['name'])
            
            # Associer prix et noms
            for i, price_elem in enumerate(price_elems):
                try:
                    # Extraire prix
                    price_text = await price_elem.inner_text()
                    price = self.clean_price(price_text)
                    
                    # Extraire nom (correspondant ou proche)
                    name = "Produit inconnu"
                    if i < len(name_elems):
                        name_text = await name_elems[i].inner_text()
                        name = name_text.strip()[:100]  # Limiter la longueur
                    
                    if price and price > 0:
                        products.append({
                            'nom': name,
                            'prix_tnd': price,
                            'site': site_name,
                            'date_scraping': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'url_source': page.url
                        })
                
                except Exception as e:
                    self.logger.debug(f"Erreur extraction produit {i}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Erreur extraction page: {e}")
        
        return products
    
    def clean_price(self, price_text):
        """Nettoyer et convertir le prix en TND"""
        if not price_text:
            return None
        
        # Supprimer espaces et caractères spéciaux
        import re
        price_clean = re.sub(r'[^\d.,]', '', price_text.replace(' ', ''))
        
        if not price_clean:
            return None
        
        try:
            # Gérer virgules et points
            if ',' in price_clean and '.' in price_clean:
                price_clean = price_clean.replace(',', '')
            elif ',' in price_clean:
                price_clean = price_clean.replace(',', '.')
            
            price = float(price_clean)
            
            # Conversion millimes vers dinars si nécessaire
            if price > 1000:
                price = price / 100
            
            return round(price, 2)
        
        except:
            return None
    
    async def scrape_all_sites(self):
        """Scraper tous les sites configurés"""
        self.logger.info("🚀 Début du scraping multi-sites")
        all_results = []
        
        for site_name, config in self.sites_config.items():
            try:
                site_results = await self.scrape_site(site_name, config)
                all_results.extend(site_results)
                
                # Pause entre sites
                await asyncio.sleep(random.uniform(5, 10))
                
            except Exception as e:
                self.logger.error(f"❌ Échec complet du site {site_name}: {e}")
                continue
        
        self.results = all_results
        self.logger.info(f"✅ Scraping terminé: {len(all_results)} produits au total")
        
        return all_results
    
    def save_results(self):
        """Sauvegarder les résultats"""
        if not self.results:
            self.logger.warning("Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        csv_filename = f'materiaux_multi_sites_{timestamp}.csv'
        df = pd.DataFrame(self.results)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        # JSON
        json_filename = f'materiaux_multi_sites_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # Statistiques
        stats = self.generate_stats(df)
        stats_filename = f'stats_multi_sites_{timestamp}.txt'
        with open(stats_filename, 'w', encoding='utf-8') as f:
            f.write(stats)
        
        self.logger.info(f"💾 Résultats sauvegardés:")
        self.logger.info(f"   - CSV: {csv_filename}")
        self.logger.info(f"   - JSON: {json_filename}")
        self.logger.info(f"   - Stats: {stats_filename}")
    
    def generate_stats(self, df):
        """Générer des statistiques"""
        stats = f"""
📊 STATISTIQUES MULTI-SITES MATÉRIAUX DE CONSTRUCTION
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
====================================================

🔢 DONNÉES COLLECTÉES:
   - Total produits: {len(df)}
   - Sites scrapés: {df['site'].nunique()}
   - Prix moyen: {df['prix_tnd'].mean():.2f} TND
   - Prix médian: {df['prix_tnd'].median():.2f} TND
   - Prix min: {df['prix_tnd'].min():.2f} TND
   - Prix max: {df['prix_tnd'].max():.2f} TND

📈 RÉPARTITION PAR SITE:
"""
        
        for site, count in df['site'].value_counts().items():
            avg_price = df[df['site'] == site]['prix_tnd'].mean()
            stats += f"   - {site}: {count} produits (prix moyen: {avg_price:.2f} TND)\n"
        
        return stats

async def main():
    """Fonction principale"""
    scraper = MultiSiteMaterialScraper()
    
    try:
        # Lancer le scraping
        results = await scraper.scrape_all_sites()
        
        # Sauvegarder
        scraper.save_results()
        
        print(f"✅ Scraping terminé avec succès!")
        print(f"📦 {len(results)} produits collectés")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(main())
