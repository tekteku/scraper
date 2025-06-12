#!/usr/bin/env python3
"""
Générateur de Devis Simplifié - Version Texte
"""

import pandas as pd
from datetime import datetime, timedelta
import json

class SimpleDevisGenerator:
    def __init__(self):
        self.load_materials_data()
        self.company_info = {
            'nom': 'MATÉRIAUX TUNISIE ESTIMATION',
            'adresse': 'Avenue Habib Bourguiba, Tunis 1000',
            'tel': '+216 71 XXX XXX',
            'email': 'contact@materiaux-tunisie.tn'
        }
    
    def load_materials_data(self):
        """Charger les données de matériaux"""
        try:
            self.materials_df = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
            print(f"✅ {len(self.materials_df)} matériaux chargés")
        except Exception as e:
            print(f"❌ Erreur chargement matériaux: {e}")
            self.materials_df = pd.DataFrame()
    
    def create_devis(self, client_info, project_info, materials_list):
        """Créer un devis complet"""
        
        # Options par défaut
        options = {
            'tva': 19,  # TVA Tunisie
            'remise': 0,
            'validite_jours': 30
        }
        
        # Calculer les lignes du devis
        devis_lines = []
        
        for item in materials_list:
            material_name = item['materiau']
            quantity = item['quantite']
            
            # Trouver le matériau
            material_data = self.materials_df[
                self.materials_df['Matériau'].str.contains(material_name, case=False, na=False)
            ]
            
            if not material_data.empty:
                material = material_data.iloc[0]
                prix_unitaire = material['Prix_Unitaire_TND']
                total_ht = prix_unitaire * quantity
                
                devis_lines.append({
                    'designation': material['Type_Détaillé'],
                    'quantite': quantity,
                    'unite': material['Unité'],
                    'prix_unitaire': prix_unitaire,
                    'total_ht': total_ht,
                    'fournisseur': material['Meilleur_Fournisseur'],
                    'economie_possible': material['Économie_TND'] * quantity
                })
        
        if not devis_lines:
            print("❌ Aucun matériau valide trouvé")
            return None
        
        # Calculer totaux
        sous_total = sum(line['total_ht'] for line in devis_lines)
        tva_montant = sous_total * (options['tva'] / 100)
        total_ttc = sous_total + tva_montant
        
        # Données du devis
        devis_data = {
            'numero': f"DEV-{datetime.now().strftime('%Y%m%d%H%M')}",
            'date': datetime.now().strftime('%d/%m/%Y'),
            'validite': (datetime.now() + timedelta(days=options['validite_jours'])).strftime('%d/%m/%Y'),
            'client': client_info,
            'project': project_info,
            'lines': devis_lines,
            'sous_total': sous_total,
            'tva_montant': tva_montant,
            'total_ttc': total_ttc,
            'total_economies': sum(line['economie_possible'] for line in devis_lines)
        }
        
        # Générer fichiers
        txt_file = self.generate_text_devis(devis_data)
        json_file = self.save_devis_json(devis_data)
        
        return {
            'txt_file': txt_file,
            'json_file': json_file,
            'devis_data': devis_data
        }
    
    def generate_text_devis(self, devis_data):
        """Générer un devis au format texte"""
        filename = f"devis_{devis_data['numero']}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"🏗️ DEVIS MATÉRIAUX DE CONSTRUCTION N° {devis_data['numero']}\n")
            f.write("=" * 70 + "\n\n")
            
            # Informations entreprise
            f.write(f"{self.company_info['nom']}\n")
            f.write(f"{self.company_info['adresse']}\n")
            f.write(f"Tél: {self.company_info['tel']} - Email: {self.company_info['email']}\n\n")
            
            f.write(f"📅 Date: {devis_data['date']}\n")
            f.write(f"⏰ Validité: {devis_data['validite']}\n\n")
            
            # Client
            f.write("👤 CLIENT:\n")
            f.write("-" * 10 + "\n")
            f.write(f"Nom: {devis_data['client']['nom']}\n")
            f.write(f"Adresse: {devis_data['client']['adresse']}\n")
            if 'tel' in devis_data['client']:
                f.write(f"Téléphone: {devis_data['client']['tel']}\n")
            f.write("\n")
            
            # Projet
            f.write("🏗️ PROJET:\n")
            f.write("-" * 10 + "\n")
            f.write(f"Nom: {devis_data['project']['nom']}\n")
            f.write(f"Description: {devis_data['project']['description']}\n\n")
            
            # Matériaux
            f.write("📦 DÉTAIL DES MATÉRIAUX:\n")
            f.write("-" * 25 + "\n")
            
            for i, line in enumerate(devis_data['lines'], 1):
                f.write(f"{i}. {line['designation']}\n")
                f.write(f"   Quantité: {line['quantite']} {line['unite']}\n")
                f.write(f"   Prix unitaire: {line['prix_unitaire']:.2f} TND\n")
                f.write(f"   Total ligne: {line['total_ht']:.2f} TND\n")
                f.write(f"   Fournisseur: {line['fournisseur']}\n")
                if line['economie_possible'] > 0:
                    f.write(f"   💰 Économie vs marché: {line['economie_possible']:.2f} TND\n")
                f.write("\n")
            
            # Totaux
            f.write("=" * 40 + "\n")
            f.write(f"💰 RÉCAPITULATIF FINANCIER:\n")
            f.write("-" * 25 + "\n")
            f.write(f"Sous-total HT: {devis_data['sous_total']:.2f} TND\n")
            f.write(f"TVA (19%): {devis_data['tva_montant']:.2f} TND\n")
            f.write(f"TOTAL TTC: {devis_data['total_ttc']:.2f} TND\n")
            f.write("=" * 40 + "\n\n")
            
            # Avantages
            if devis_data['total_economies'] > 0:
                f.write(f"🎯 AVANTAGE PRIX TOTAL: {devis_data['total_economies']:.2f} TND\n")
                savings_pct = (devis_data['total_economies'] / devis_data['sous_total']) * 100
                f.write(f"   Soit {savings_pct:.1f}% d'économie par rapport aux prix moyens du marché\n\n")
            
            # Conditions
            f.write("📋 CONDITIONS:\n")
            f.write("-" * 12 + "\n")
            f.write("• Devis valable 30 jours\n")
            f.write("• Paiement: 50% à la commande, 50% à la livraison\n")
            f.write("• Délai de livraison: 7-15 jours ouvrables\n")
            f.write("• Prix TTC incluant TVA tunisienne (19%)\n")
            f.write("• Livraison: En supplément selon distance\n\n")
            
            f.write("📞 Pour toute question, contactez-nous:\n")
            f.write(f"   {self.company_info['tel']} - {self.company_info['email']}\n\n")
            
            f.write("Merci de votre confiance ! 🙏\n")
            f.write("=" * 70 + "\n")
        
        print(f"📄 Devis texte généré: {filename}")
        return filename
    
    def save_devis_json(self, devis_data):
        """Sauvegarder le devis en JSON"""
        filename = f"devis_{devis_data['numero']}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(devis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 Devis JSON sauvegardé: {filename}")
        return filename

def create_sample_devis():
    """Créer des devis d'exemple"""
    
    generator = SimpleDevisGenerator()
    
    if generator.materials_df.empty:
        print("❌ Impossible de créer des devis sans données de matériaux")
        return []
    
    devis_list = []
    
    # Exemple 1: Maison 100m²
    print("\n🏠 Création devis Maison 100m²...")
    client1 = {
        'nom': 'M. Ahmed Ben Ali',
        'adresse': 'Rue de la République, Sfax 3000',
        'tel': '+216 74 XXX XXX'
    }
    
    project1 = {
        'nom': 'Construction Maison 100m²',
        'description': 'Construction neuve avec matériaux de qualité standard'
    }
    
    materials1 = [
        {'materiau': 'Ciment', 'quantite': 50},
        {'materiau': 'Brique', 'quantite': 1000},
        {'materiau': 'Sable', 'quantite': 15},
        {'materiau': 'Carrelage', 'quantite': 100},
        {'materiau': 'Peinture', 'quantite': 8}
    ]
    
    devis1 = generator.create_devis(client1, project1, materials1)
    if devis1:
        devis_list.append(devis1)
    
    # Exemple 2: Rénovation
    print("\n🔧 Création devis Rénovation...")
    client2 = {
        'nom': 'Mme Fatma Sassi',
        'adresse': 'Avenue Bourguiba, Sousse 4000',
        'tel': '+216 73 XXX XXX'
    }
    
    project2 = {
        'nom': 'Rénovation Appartement 80m²',
        'description': 'Rénovation complète avec isolation et finitions'
    }
    
    materials2 = [
        {'materiau': 'Isolant', 'quantite': 80},
        {'materiau': 'Placo', 'quantite': 150},
        {'materiau': 'Carrelage', 'quantite': 80},
        {'materiau': 'Peinture', 'quantite': 6}
    ]
    
    devis2 = generator.create_devis(client2, project2, materials2)
    if devis2:
        devis_list.append(devis2)
    
    return devis_list

if __name__ == "__main__":
    print("🏗️ GÉNÉRATEUR DE DEVIS MATÉRIAUX")
    print("=" * 40)
    
    devis_created = create_sample_devis()
    
    print(f"\n✅ {len(devis_created)} devis générés avec succès!")
    
    # Afficher résumé
    for i, devis in enumerate(devis_created, 1):
        data = devis['devis_data']
        print(f"\n📋 Devis {i}: {data['numero']}")
        print(f"   👤 Client: {data['client']['nom']}")
        print(f"   🏗️ Projet: {data['project']['nom']}")
        print(f"   💰 Total TTC: {data['total_ttc']:.2f} TND")
        print(f"   🎯 Économies: {data['total_economies']:.2f} TND")
        print(f"   📄 Fichiers: {devis['txt_file']}, {devis['json_file']}")
    
    print(f"\n🎉 Tous les devis ont été générés dans le répertoire courant!")
