#!/usr/bin/env python3
"""
Système de Monitoring des Prix des Matériaux de Construction
Surveillance automatique des variations de prix et alertes
"""

import asyncio
import pandas as pd
import json
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os
import logging

class PriceMonitor:
    def __init__(self, db_path='price_history.db'):
        self.db_path = db_path
        self.setup_database()
        self.setup_logging()
        
        # Configuration des seuils d'alerte
        self.alert_thresholds = {
            'price_increase': 10,  # % d'augmentation
            'price_decrease': 15,  # % de diminution
            'availability_change': True  # Changement de stock
        }
        
        # Configuration email (à personnaliser)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'your_email@gmail.com',
            'password': 'your_password',
            'recipients': ['alert@yourcompany.com']
        }
    
    def setup_logging(self):
        """Configuration du logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('price_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Initialiser la base de données SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table historique des prix
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                site TEXT NOT NULL,
                price REAL NOT NULL,
                availability TEXT,
                scraped_date DATETIME NOT NULL,
                url TEXT,
                category TEXT,
                UNIQUE(product_name, site, scraped_date)
            )
        ''')
        
        # Table des alertes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                site TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                old_price REAL,
                new_price REAL,
                change_percentage REAL,
                alert_date DATETIME NOT NULL,
                sent BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("✅ Base de données initialisée")
    
    def store_price_data(self, data_file):
        """Stocker les données de prix dans la base"""
        try:
            # Charger données
            if data_file.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            
            conn = sqlite3.connect(self.db_path)
            
            # Insérer données avec gestion des doublons
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO price_history 
                        (product_name, site, price, availability, scraped_date, url, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('nom', ''),
                        row.get('site', ''),
                        row.get('prix_tnd', 0),
                        row.get('disponibilite', 'Inconnue'),
                        row.get('date_scraping', datetime.now().isoformat()),
                        row.get('url_source', ''),
                        row.get('categorie', 'Autre')
                    ))
                except Exception as e:
                    self.logger.debug(f"Erreur insertion ligne: {e}")
            
            conn.commit()
            count = conn.execute('SELECT COUNT(*) FROM price_history').fetchone()[0]
            conn.close()
            
            self.logger.info(f"✅ {len(df)} nouveaux prix stockés. Total: {count} entrées")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur stockage prix: {e}")
            return False
    
    def detect_price_changes(self, days_back=7):
        """Détecter les changements de prix significatifs"""
        conn = sqlite3.connect(self.db_path)
        
        # Récupérer les prix récents vs anciens
        query = '''
            WITH latest_prices AS (
                SELECT product_name, site, price, scraped_date,
                       ROW_NUMBER() OVER (PARTITION BY product_name, site ORDER BY scraped_date DESC) as rn
                FROM price_history
            ),
            old_prices AS (
                SELECT product_name, site, price, scraped_date,
                       ROW_NUMBER() OVER (PARTITION BY product_name, site ORDER BY scraped_date DESC) as rn
                FROM price_history
                WHERE scraped_date <= datetime('now', '-{} days')
            )
            SELECT 
                l.product_name, l.site, 
                l.price as new_price, l.scraped_date as new_date,
                o.price as old_price, o.scraped_date as old_date,
                ((l.price - o.price) / o.price * 100) as change_pct
            FROM latest_prices l
            JOIN old_prices o ON l.product_name = o.product_name AND l.site = o.site
            WHERE l.rn = 1 AND o.rn = 1 
            AND ABS((l.price - o.price) / o.price * 100) >= ?
        '''.format(days_back)
        
        changes = pd.read_sql_query(
            query, 
            conn, 
            params=[min(self.alert_thresholds['price_increase'], 
                       self.alert_thresholds['price_decrease'])]
        )
        
        conn.close()
        
        if not changes.empty:
            self.logger.info(f"🔍 {len(changes)} changements de prix détectés")
            self.create_alerts(changes)
        else:
            self.logger.info("ℹ️ Aucun changement de prix significatif")
        
        return changes
    
    def create_alerts(self, changes_df):
        """Créer des alertes pour les changements détectés"""
        conn = sqlite3.connect(self.db_path)
        alerts_created = 0
        
        for _, change in changes_df.iterrows():
            try:
                # Déterminer type d'alerte
                if change['change_pct'] > self.alert_thresholds['price_increase']:
                    alert_type = 'HAUSSE'
                elif change['change_pct'] < -self.alert_thresholds['price_decrease']:
                    alert_type = 'BAISSE'
                else:
                    continue
                
                # Insérer alerte
                conn.execute('''
                    INSERT OR IGNORE INTO price_alerts
                    (product_name, site, alert_type, old_price, new_price, 
                     change_percentage, alert_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    change['product_name'],
                    change['site'],
                    alert_type,
                    change['old_price'],
                    change['new_price'],
                    change['change_pct'],
                    datetime.now().isoformat()
                ))
                
                alerts_created += 1
                
            except Exception as e:
                self.logger.error(f"Erreur création alerte: {e}")
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"🚨 {alerts_created} alertes créées")
        
        if alerts_created > 0:
            self.send_alert_notifications()
    
    def send_alert_notifications(self):
        """Envoyer les notifications d'alerte par email"""
        conn = sqlite3.connect(self.db_path)
        
        # Récupérer alertes non envoyées
        unsent_alerts = pd.read_sql_query('''
            SELECT * FROM price_alerts 
            WHERE sent = FALSE 
            ORDER BY alert_date DESC
        ''', conn)
        
        if unsent_alerts.empty:
            return
        
        try:
            # Composer email
            subject = f"🚨 Alerte Prix Matériaux - {len(unsent_alerts)} changements détectés"
            body = self.compose_alert_email(unsent_alerts)
            
            # Envoyer email (si configuré)
            if self.email_config['email'] != 'your_email@gmail.com':
                self.send_email(subject, body)
            
            # Générer rapport local
            self.generate_alert_report(unsent_alerts)
            
            # Marquer comme envoyées
            alert_ids = unsent_alerts['id'].tolist()
            conn.execute(f'''
                UPDATE price_alerts 
                SET sent = TRUE 
                WHERE id IN ({','.join(['?'] * len(alert_ids))})
            ''', alert_ids)
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi notifications: {e}")
        
        finally:
            conn.close()
    
    def compose_alert_email(self, alerts_df):
        """Composer le contenu de l'email d'alerte"""
        body = f"""
🚨 ALERTE PRIX MATÉRIAUX DE CONSTRUCTION
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================

{len(alerts_df)} changements de prix détectés:

"""
        
        for _, alert in alerts_df.iterrows():
            icon = "📈" if alert['alert_type'] == 'HAUSSE' else "📉"
            body += f"""
{icon} {alert['product_name']} - {alert['site']}
   Ancien prix: {alert['old_price']:.2f} TND
   Nouveau prix: {alert['new_price']:.2f} TND
   Variation: {alert['change_percentage']:+.1f}%
   Date: {alert['alert_date']}

"""
        
        body += """
⚠️ Vérifiez vos estimations de projets en cours.
📊 Consultez le rapport détaillé en pièce jointe.

Système de Monitoring Automatique
"""
        
        return body
    
    def send_email(self, subject, body):
        """Envoyer email via SMTP"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email'], self.email_config['recipients'], text)
            server.quit()
            
            self.logger.info("📧 Email d'alerte envoyé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi email: {e}")
    
    def generate_alert_report(self, alerts_df):
        """Générer rapport local des alertes"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'rapport_alertes_{timestamp}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🚨 RAPPORT D'ALERTES PRIX\n")
            f.write("=" * 25 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Alertes: {len(alerts_df)}\n\n")
            
            # Grouper par type
            hausses = alerts_df[alerts_df['alert_type'] == 'HAUSSE']
            baisses = alerts_df[alerts_df['alert_type'] == 'BAISSE']
            
            if not hausses.empty:
                f.write(f"📈 HAUSSES DE PRIX ({len(hausses)}):\n")
                f.write("-" * 20 + "\n")
                for _, alert in hausses.iterrows():
                    f.write(f"• {alert['product_name']} ({alert['site']})\n")
                    f.write(f"  {alert['old_price']:.2f} → {alert['new_price']:.2f} TND ")
                    f.write(f"({alert['change_percentage']:+.1f}%)\n\n")
            
            if not baisses.empty:
                f.write(f"📉 BAISSES DE PRIX ({len(baisses)}):\n")
                f.write("-" * 20 + "\n")
                for _, alert in baisses.iterrows():
                    f.write(f"• {alert['product_name']} ({alert['site']})\n")
                    f.write(f"  {alert['old_price']:.2f} → {alert['new_price']:.2f} TND ")
                    f.write(f"({alert['change_percentage']:+.1f}%)\n\n")
        
        self.logger.info(f"📄 Rapport d'alertes généré: {report_file}")
    
    def get_price_trends(self, product_name=None, days=30):
        """Analyser les tendances de prix"""
        conn = sqlite3.connect(self.db_path)
        
        where_clause = ""
        params = [days]
        if product_name:
            where_clause = "AND product_name LIKE ?"
            params.append(f"%{product_name}%")
        
        query = f'''
            SELECT product_name, site, price, scraped_date
            FROM price_history
            WHERE scraped_date >= datetime('now', '-{days} days')
            {where_clause}
            ORDER BY product_name, site, scraped_date
        '''
        
        trends = pd.read_sql_query(query, conn, params=params[1:] if product_name else [])
        conn.close()
        
        return trends

async def main():
    """Test du système de monitoring"""
    monitor = PriceMonitor()
    
    # Stocker données récentes (adapter le nom du fichier)
    success = monitor.store_price_data('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
    
    if success:
        # Détecter changements
        changes = monitor.detect_price_changes(days_back=7)
        
        # Analyser tendances
        trends = monitor.get_price_trends(days=30)
        
        print(f"✅ Monitoring terminé")
        print(f"📊 {len(trends)} points de données analysés")
        print(f"🚨 {len(changes)} changements détectés")

if __name__ == "__main__":
    asyncio.run(main())
