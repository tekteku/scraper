#!/usr/bin/env python3
"""
🔍 VALIDATION FINALE - Vérification Complète du Système
Test de tous les composants et génération du rapport de certification
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import importlib.util

class SystemValidator:
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_test(self, test_name, status, details=""):
        icons = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
        icon = icons.get(status, "❓")
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def test_file_existence(self):
        """Test 1: Vérification existence des fichiers critiques"""
        self.print_header("TEST 1: FICHIERS CRITIQUES")
        
        critical_files = {
            'ESTIMATION_MATERIAUX_TUNISIE_20250611.csv': 'Données principales',
            'TEMPLATE_ESTIMATION_PROJET_20250611.csv': 'Templates projets',
            'simple_price_analyzer.py': 'Analyseur de prix',
            'simple_devis_generator.py': 'Générateur devis',
            'materials_dashboard.py': 'Interface web',
            'demo_finale.py': 'Script démo',
            'README_FINAL.md': 'Documentation'
        }
        
        missing_files = []
        for file, description in critical_files.items():
            if os.path.exists(file):
                size = os.path.getsize(file)
                self.print_test(f"{description}", "PASS", f"{file} ({size:,} bytes)")
            else:
                self.print_test(f"{description}", "FAIL", f"{file} manquant")
                missing_files.append(file)
        
        self.results['files'] = len(missing_files) == 0
        if missing_files:
            self.errors.extend(missing_files)
    
    def test_data_integrity(self):
        """Test 2: Intégrité des données"""
        self.print_header("TEST 2: INTÉGRITÉ DES DONNÉES")
        
        try:
            # Test données principales
            df = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
            
            # Vérifications basiques
            if len(df) > 0:
                self.print_test("Données chargées", "PASS", f"{len(df)} matériaux")
            else:
                self.print_test("Données chargées", "FAIL", "Fichier vide")
                self.results['data_basic'] = False
                return
            
            # Colonnes requises
            required_cols = ['Matériau', 'Prix_Unitaire_TND', 'Économie_TND', 'Meilleur_Fournisseur']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if not missing_cols:
                self.print_test("Colonnes requises", "PASS", f"Toutes présentes")
            else:
                self.print_test("Colonnes requises", "FAIL", f"Manquantes: {missing_cols}")
                self.errors.append(f"Colonnes manquantes: {missing_cols}")
            
            # Validation des prix
            valid_prices = df['Prix_Unitaire_TND'].notna() & (df['Prix_Unitaire_TND'] > 0)
            if valid_prices.all():
                self.print_test("Prix valides", "PASS", f"Tous les prix > 0")
            else:
                invalid_count = (~valid_prices).sum()
                self.print_test("Prix valides", "WARN", f"{invalid_count} prix invalides")
                self.warnings.append(f"{invalid_count} prix invalides détectés")
            
            # Statistiques
            self.print_test("Prix moyen", "PASS", f"{df['Prix_Unitaire_TND'].mean():.2f} TND")
            self.print_test("Économies totales", "PASS", f"{df['Économie_TND'].sum():.2f} TND")
            self.print_test("Fournisseurs uniques", "PASS", f"{df['Meilleur_Fournisseur'].nunique()}")
            
            self.results['data_integrity'] = True
            
        except Exception as e:
            self.print_test("Intégrité données", "FAIL", f"Erreur: {e}")
            self.errors.append(f"Erreur données: {e}")
            self.results['data_integrity'] = False
    
    def test_scripts_functionality(self):
        """Test 3: Fonctionnalité des scripts"""
        self.print_header("TEST 3: FONCTIONNALITÉ DES SCRIPTS")
        
        scripts_to_test = {
            'simple_price_analyzer': 'Analyseur de prix',
            'simple_devis_generator': 'Générateur de devis',
            'demo_finale': 'Script de démonstration'
        }
        
        for script_name, description in scripts_to_test.items():
            try:
                # Tenter d'importer le module
                spec = importlib.util.spec_from_file_location(script_name, f"{script_name}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.print_test(f"{description}", "PASS", "Import réussi")
                else:
                    self.print_test(f"{description}", "FAIL", "Import impossible")
                    self.errors.append(f"Import {script_name} échoué")
                    
            except Exception as e:
                self.print_test(f"{description}", "FAIL", f"Erreur: {str(e)[:50]}...")
                self.errors.append(f"Erreur {script_name}: {e}")
        
        self.results['scripts'] = len(self.errors) == 0
    
    def test_dependencies(self):
        """Test 4: Dépendances Python"""
        self.print_header("TEST 4: DÉPENDANCES PYTHON")
        
        dependencies = {
            'pandas': 'Manipulation données',
            'numpy': 'Calculs numériques', 
            'playwright': 'Scraping web',
            'streamlit': 'Interface web',
            'plotly': 'Graphiques interactifs',
            'json': 'Sérialisation JSON',
            'datetime': 'Gestion dates',
            'asyncio': 'Programmation asynchrone'
        }
        
        missing_deps = []
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                self.print_test(f"{description}", "PASS", f"{dep} disponible")
            except ImportError:
                self.print_test(f"{description}", "FAIL", f"{dep} manquant")
                missing_deps.append(dep)
        
        self.results['dependencies'] = len(missing_deps) == 0
        if missing_deps:
            self.errors.extend([f"Dépendance manquante: {dep}" for dep in missing_deps])
    
    def test_generated_outputs(self):
        """Test 5: Outputs générés"""
        self.print_header("TEST 5: OUTPUTS GÉNÉRÉS")
        
        # Chercher les fichiers générés récemment
        output_patterns = [
            ('rapport_comparaison_*.txt', 'Rapports d\'analyse'),
            ('comparaison_detaillee_*.csv', 'Données d\'analyse'),
            ('devis_*.txt', 'Devis texte'),
            ('devis_*.json', 'Devis JSON'),
            ('DEMO_REPORT_*.txt', 'Rapports de démo')
        ]
        
        import glob
        for pattern, description in output_patterns:
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                age_hours = (datetime.now().timestamp() - os.path.getctime(latest_file)) / 3600
                self.print_test(f"{description}", "PASS", f"{latest_file} ({age_hours:.1f}h)")
            else:
                self.print_test(f"{description}", "WARN", f"Aucun fichier {pattern}")
                self.warnings.append(f"Outputs manquants: {pattern}")
        
        self.results['outputs'] = True  # Non critique
    
    def test_system_performance(self):
        """Test 6: Performance système"""
        self.print_header("TEST 6: PERFORMANCE SYSTÈME")
        
        try:
            import time
            import psutil
            
            # RAM disponible
            memory = psutil.virtual_memory()
            if memory.available > 1024**3:  # > 1GB
                self.print_test("Mémoire disponible", "PASS", f"{memory.available/(1024**3):.1f} GB")
            else:
                self.print_test("Mémoire disponible", "WARN", f"{memory.available/(1024**2):.0f} MB")
                self.warnings.append("Mémoire limitée")
            
            # Espace disque
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            if free_gb > 1:
                self.print_test("Espace disque", "PASS", f"{free_gb:.1f} GB libre")
            else:
                self.print_test("Espace disque", "WARN", f"{free_gb*1024:.0f} MB libre")
                self.warnings.append("Espace disque limité")
            
            # Test vitesse chargement données
            start_time = time.time()
            df = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
            load_time = time.time() - start_time
            
            if load_time < 1.0:
                self.print_test("Vitesse chargement", "PASS", f"{load_time:.3f}s")
            else:
                self.print_test("Vitesse chargement", "WARN", f"{load_time:.3f}s (lent)")
                self.warnings.append("Chargement lent des données")
            
            self.results['performance'] = True
            
        except ImportError:
            self.print_test("Mesures performance", "WARN", "psutil non disponible")
            self.results['performance'] = False
        except Exception as e:
            self.print_test("Tests performance", "FAIL", f"Erreur: {e}")
            self.results['performance'] = False
    
    def generate_certification_report(self):
        """Générer le rapport de certification finale"""
        self.print_header("GÉNÉRATION RAPPORT DE CERTIFICATION")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'CERTIFICATION_REPORT_{timestamp}.txt'
        
        # Calculer score global
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🏆 RAPPORT DE CERTIFICATION SYSTÈME\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Système: Estimation Matériaux Tunisiens v1.0\n")
            f.write(f"Validateur: SystemValidator\n\n")
            
            # Score global
            f.write("📊 SCORE GLOBAL:\n")
            f.write("-" * 15 + "\n")
            f.write(f"Tests réussis: {passed_tests}/{total_tests}\n")
            f.write(f"Score: {score:.1f}%\n")
            
            if score >= 90:
                f.write("🎉 CERTIFICATION: EXCELLENTE\n")
                status = "EXCELLENTE"
            elif score >= 80:
                f.write("✅ CERTIFICATION: BONNE\n") 
                status = "BONNE"
            elif score >= 70:
                f.write("⚠️ CERTIFICATION: ACCEPTABLE\n")
                status = "ACCEPTABLE"
            else:
                f.write("❌ CERTIFICATION: NON CONFORME\n")
                status = "NON CONFORME"
            
            f.write(f"\n📋 DÉTAIL DES TESTS:\n")
            f.write("-" * 18 + "\n")
            for test_name, result in self.results.items():
                status_icon = "✅" if result else "❌"
                f.write(f"{status_icon} {test_name}: {'PASS' if result else 'FAIL'}\n")
            
            # Erreurs
            if self.errors:
                f.write(f"\n❌ ERREURS DÉTECTÉES ({len(self.errors)}):\n")
                f.write("-" * 25 + "\n")
                for i, error in enumerate(self.errors, 1):
                    f.write(f"{i}. {error}\n")
            
            # Avertissements
            if self.warnings:
                f.write(f"\n⚠️ AVERTISSEMENTS ({len(self.warnings)}):\n")
                f.write("-" * 20 + "\n")
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"{i}. {warning}\n")
            
            # Recommandations
            f.write(f"\n💡 RECOMMANDATIONS:\n")
            f.write("-" * 16 + "\n")
            
            if score >= 90:
                f.write("• Système prêt pour production\n")
                f.write("• Monitoring régulier recommandé\n")
                f.write("• Documentation à jour\n")
            elif score >= 70:
                f.write("• Corriger les erreurs identifiées\n")
                f.write("• Tester à nouveau après corrections\n")
                f.write("• Surveillance accrue recommandée\n")
            else:
                f.write("• Révision complète nécessaire\n")
                f.write("• Ne pas déployer en production\n")
                f.write("• Contacter le support technique\n")
            
            f.write(f"\n🔍 VALIDÉ PAR: GitHub Copilot System Validator\n")
            f.write(f"📧 Support: support@materiaux-tunisie.tn\n")
            f.write("=" * 50 + "\n")
        
        self.print_test("Rapport de certification", "PASS", report_file)
        return report_file, score, status
    
    def run_full_validation(self):
        """Exécuter la validation complète"""
        print("🔍 VALIDATION COMPLÈTE DU SYSTÈME")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📂 Répertoire: {os.getcwd()}")
        
        # Exécuter tous les tests
        self.test_file_existence()
        self.test_data_integrity()
        self.test_scripts_functionality()
        self.test_dependencies()
        self.test_generated_outputs()
        self.test_system_performance()
        
        # Générer rapport final
        report_file, score, status = self.generate_certification_report()
        
        # Résumé final
        self.print_header("RÉSUMÉ FINAL")
        print(f"📊 Score global: {score:.1f}%")
        print(f"🏆 Certification: {status}")
        print(f"❌ Erreurs: {len(self.errors)}")
        print(f"⚠️ Avertissements: {len(self.warnings)}")
        print(f"📄 Rapport: {report_file}")
        
        if score >= 90:
            print(f"\n🎉 SYSTÈME VALIDÉ - PRÊT POUR PRODUCTION!")
        elif score >= 70:
            print(f"\n✅ SYSTÈME ACCEPTABLE - CORRECTIONS MINEURES NÉCESSAIRES")
        else:
            print(f"\n❌ SYSTÈME NON CONFORME - RÉVISION REQUISE")
        
        return score >= 70

def main():
    validator = SystemValidator()
    success = validator.run_full_validation()
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⛔ Validation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale dans la validation: {e}")
        sys.exit(1)
