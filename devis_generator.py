#!/usr/bin/env python3
"""
Générateur de Devis Automatique pour Matériaux de Construction
Génère des devis professionnels basés sur les prix scraped
"""

import pandas as pd
from datetime import datetime, timedelta
import json

# Tentative d'import de ReportLab - optionnel
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import os

class DevisGenerator:
    def __init__(self):
        self.load_materials_data()
        self.company_info = {
            'nom': 'MATÉRIAUX TUNISIE ESTIMATION',
            'adresse': 'Avenue Habib Bourguiba, Tunis 1000',
            'tel': '+216 71 XXX XXX',
            'email': 'contact@materiaux-tunisie.tn',
            'siret': 'TN123456789'
        }
    
    def load_materials_data(self):
        """Charger les données de matériaux"""
        try:
            self.materials_df = pd.read_csv('ESTIMATION_MATERIAUX_TUNISIE_20250611.csv')
            print(f"✅ {len(self.materials_df)} matériaux chargés")
        except Exception as e:
            print(f"❌ Erreur chargement matériaux: {e}")
            self.materials_df = pd.DataFrame()
    
    def create_devis(self, client_info, project_info, materials_list, options=None):
        """Créer un devis complet"""
        
        if options is None:
            options = {
                'tva': 19,  # TVA Tunisie
                'remise': 0,
                'validite_jours': 30,
                'conditions_paiement': "50% à la commande, 50% à la livraison",
                'delai_livraison': "7-15 jours ouvrables"
            }
        
        # Calculer les lignes du devis
        devis_lines = self.calculate_devis_lines(materials_list)
        
        if not devis_lines:
            print("❌ Aucun matériau valide pour le devis")
            return None
        
        # Calculer totaux
        sous_total = sum(line['total_ht'] for line in devis_lines)
        remise_montant = sous_total * (options['remise'] / 100)
        sous_total_apres_remise = sous_total - remise_montant
        tva_montant = sous_total_apres_remise * (options['tva'] / 100)
        total_ttc = sous_total_apres_remise + tva_montant
        
        # Préparer données du devis
        devis_data = {
            'numero': self.generate_devis_number(),
            'date': datetime.now().strftime('%d/%m/%Y'),
            'validite': (datetime.now() + timedelta(days=options['validite_jours'])).strftime('%d/%m/%Y'),
            'client': client_info,
            'project': project_info,
            'lines': devis_lines,
            'sous_total': sous_total,
            'remise_pct': options['remise'],
            'remise_montant': remise_montant,
            'sous_total_apres_remise': sous_total_apres_remise,
            'tva_pct': options['tva'],
            'tva_montant': tva_montant,
            'total_ttc': total_ttc,
            'conditions': options
        }
        
        # Générer PDF
        pdf_file = self.generate_pdf_devis(devis_data)
        
        # Générer JSON pour sauvegarde
        json_file = self.save_devis_json(devis_data)
        
        return {
            'pdf_file': pdf_file,
            'json_file': json_file,
            'devis_data': devis_data
        }
    
    def calculate_devis_lines(self, materials_list):
        """Calculer les lignes du devis"""
        lines = []
        
        for item in materials_list:
            material_name = item['materiau']
            quantity = item['quantite']
            
            # Trouver le matériau dans nos données
            material_data = self.materials_df[
                self.materials_df['Matériau'].str.contains(material_name, case=False, na=False)
            ]
            
            if material_data.empty:
                print(f"⚠️ Matériau non trouvé: {material_name}")
                continue
            
            # Prendre le premier match
            material = material_data.iloc[0]
            
            # Calculer la ligne
            prix_unitaire = material['Prix_Unitaire_TND']
            total_ht = prix_unitaire * quantity
            
            line = {
                'designation': material['Type_Détaillé'],
                'quantite': quantity,
                'unite': material['Unité'],
                'prix_unitaire': prix_unitaire,
                'total_ht': total_ht,
                'fournisseur': material['Meilleur_Fournisseur'],
                'disponibilite': material['Disponibilité'],
                'economie_possible': material['Économie_TND'] * quantity
            }
            
            lines.append(line)
        
        return lines
    
    def generate_devis_number(self):
        """Générer un numéro de devis unique"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        return f"DEV-{timestamp}"
      def generate_pdf_devis(self, devis_data):
        """Générer le PDF du devis"""
        if not REPORTLAB_AVAILABLE:
            print("⚠️ ReportLab non disponible, génération du devis texte uniquement")
            return self.generate_text_devis(devis_data)
        
        try:
            filename = f"devis_{devis_data['numero']}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4, 
                                  rightMargin=2*cm, leftMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.darkblue,
                alignment=1  # Center
            )
            
            # Contenu du PDF
            story = []
            
            # En-tête entreprise
            story.append(Paragraph(self.company_info['nom'], title_style))
            story.append(Paragraph(f"{self.company_info['adresse']}", styles['Normal']))
            story.append(Paragraph(f"Tél: {self.company_info['tel']} - Email: {self.company_info['email']}", styles['Normal']))
            story.append(Spacer(1, 1*cm))
            
            # Titre devis
            story.append(Paragraph(f"DEVIS N° {devis_data['numero']}", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Informations devis
            info_data = [
                ['Date:', devis_data['date'], 'Validité:', devis_data['validite']],
            ]
            info_table = Table(info_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Informations client
            story.append(Paragraph("CLIENT:", styles['Heading2']))
            story.append(Paragraph(f"<b>{devis_data['client']['nom']}</b>", styles['Normal']))
            story.append(Paragraph(f"{devis_data['client']['adresse']}", styles['Normal']))
            if 'tel' in devis_data['client']:
                story.append(Paragraph(f"Tél: {devis_data['client']['tel']}", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informations projet
            story.append(Paragraph("PROJET:", styles['Heading2']))
            story.append(Paragraph(f"<b>{devis_data['project']['nom']}</b>", styles['Normal']))
            story.append(Paragraph(f"Description: {devis_data['project']['description']}", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Tableau des matériaux
            story.append(Paragraph("DÉTAIL DES MATÉRIAUX:", styles['Heading2']))
            
            # En-tête du tableau
            table_data = [
                ['Désignation', 'Qté', 'Unité', 'P.U. HT', 'Total HT', 'Fournisseur']
            ]
            
            # Lignes du tableau
            for line in devis_data['lines']:
                table_data.append([
                    line['designation'][:40] + "..." if len(line['designation']) > 40 else line['designation'],
                    str(line['quantite']),
                    line['unite'],
                    f"{line['prix_unitaire']:.2f} TND",
                    f"{line['total_ht']:.2f} TND",
                    line['fournisseur'][:15]
                ])
            
            # Créer le tableau
            materials_table = Table(table_data, colWidths=[6*cm, 1.5*cm, 1.5*cm, 2*cm, 2*cm, 3*cm])
            materials_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            story.append(materials_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Totaux
            totals_data = [
                ['Sous-total HT:', f"{devis_data['sous_total']:.2f} TND"],
                [f"Remise ({devis_data['remise_pct']}%):", f"-{devis_data['remise_montant']:.2f} TND"],
                ['Sous-total après remise:', f"{devis_data['sous_total_apres_remise']:.2f} TND"],
                [f"TVA ({devis_data['tva_pct']}%):", f"{devis_data['tva_montant']:.2f} TND"],
                ['TOTAL TTC:', f"{devis_data['total_ttc']:.2f} TND"]
            ]
            
            totals_table = Table(totals_data, colWidths=[8*cm, 4*cm])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(totals_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Conditions
            story.append(Paragraph("CONDITIONS:", styles['Heading2']))
            story.append(Paragraph(f"• Conditions de paiement: {devis_data['conditions']['conditions_paiement']}", styles['Normal']))
            story.append(Paragraph(f"• Délai de livraison: {devis_data['conditions']['delai_livraison']}", styles['Normal']))
            story.append(Paragraph(f"• Devis valable jusqu'au: {devis_data['validite']}", styles['Normal']))
            
            # Économies possibles
            total_economies = sum(line['economie_possible'] for line in devis_data['lines'])
            if total_economies > 0:
                story.append(Spacer(1, 0.5*cm))
                story.append(Paragraph("💰 AVANTAGE PRIX:", styles['Heading2']))
                story.append(Paragraph(f"Économies possibles par rapport au marché: <b>{total_economies:.2f} TND</b>", styles['Normal']))
            
            # Construire le PDF
            doc.build(story)
            
            print(f"📄 Devis PDF généré: {filename}")
            return filename
            
        except ImportError:
            print("⚠️ ReportLab non installé, génération du devis texte uniquement")
            return self.generate_text_devis(devis_data)
        except Exception as e:
            print(f"❌ Erreur génération PDF: {e}")
            return self.generate_text_devis(devis_data)
    
    def generate_text_devis(self, devis_data):
        """Générer un devis au format texte"""
        filename = f"devis_{devis_data['numero']}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"DEVIS N° {devis_data['numero']}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date: {devis_data['date']}\n")
            f.write(f"Validité: {devis_data['validite']}\n\n")
            
            f.write("CLIENT:\n")
            f.write(f"  {devis_data['client']['nom']}\n")
            f.write(f"  {devis_data['client']['adresse']}\n\n")
            
            f.write("PROJET:\n")
            f.write(f"  {devis_data['project']['nom']}\n")
            f.write(f"  {devis_data['project']['description']}\n\n")
            
            f.write("DÉTAIL DES MATÉRIAUX:\n")
            f.write("-" * 60 + "\n")
            
            for line in devis_data['lines']:
                f.write(f"• {line['designation']}\n")
                f.write(f"  Quantité: {line['quantite']} {line['unite']}\n")
                f.write(f"  Prix unitaire: {line['prix_unitaire']:.2f} TND\n")
                f.write(f"  Total: {line['total_ht']:.2f} TND\n")
                f.write(f"  Fournisseur: {line['fournisseur']}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write(f"Sous-total HT: {devis_data['sous_total']:.2f} TND\n")
            f.write(f"TVA ({devis_data['tva_pct']}%): {devis_data['tva_montant']:.2f} TND\n")
            f.write(f"TOTAL TTC: {devis_data['total_ttc']:.2f} TND\n")
            f.write("=" * 60 + "\n")
        
        print(f"📄 Devis texte généré: {filename}")
        return filename
    
    def save_devis_json(self, devis_data):
        """Sauvegarder le devis en JSON"""
        filename = f"devis_{devis_data['numero']}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(devis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 Devis JSON sauvegardé: {filename}")
        return filename

# Exemples d'utilisation
def create_sample_devis():
    """Créer des devis d'exemple"""
    
    generator = DevisGenerator()
    
    # Exemple 1: Maison 100m²
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
    
    # Exemple 2: Rénovation
    client2 = {
        'nom': 'Mme Fatma Sassi',
        'adresse': 'Avenue Bourguiba, Sousse 4000',
        'tel': '+216 73 XXX XXX'
    }
    
    project2 = {
        'nom': 'Rénovation Appartement 80m²',
        'description': 'Rénovation complète avec isolation et carrelage'
    }
    
    materials2 = [
        {'materiau': 'Isolant', 'quantite': 80},
        {'materiau': 'Placo', 'quantite': 150},
        {'materiau': 'Carrelage', 'quantite': 80},
        {'materiau': 'Peinture', 'quantite': 6}
    ]
    
    options2 = {
        'tva': 19,
        'remise': 5,  # 5% de remise
        'validite_jours': 45,
        'conditions_paiement': "30% à la commande, 70% à la livraison",
        'delai_livraison': "10-20 jours ouvrables"
    }
    
    devis2 = generator.create_devis(client2, project2, materials2, options2)
    
    return [devis1, devis2]

if __name__ == "__main__":
    print("🏗️ Générateur de Devis Matériaux")
    print("=" * 35)
    
    devis_created = create_sample_devis()
    
    print(f"\n✅ {len([d for d in devis_created if d])} devis générés avec succès!")
    
    # Afficher résumé
    for i, devis in enumerate(devis_created, 1):
        if devis:
            data = devis['devis_data']
            print(f"\n📋 Devis {i}: {data['numero']}")
            print(f"   Client: {data['client']['nom']}")
            print(f"   Projet: {data['project']['nom']}")
            print(f"   Total TTC: {data['total_ttc']:.2f} TND")
            print(f"   Fichiers: {devis['pdf_file']}, {devis['json_file']}")
