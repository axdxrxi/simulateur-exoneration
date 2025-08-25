import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="Simulateur d'exonération", layout="centered")

st.title("Simulateur d'exonération d’ombrières photovoltaïques (CNA)")
st.markdown("""
Ce simulateur permet d'évaluer si un projet d’ombrière peut être exonéré pour **non-viabilité économique** 
(selon la loi APER). Il calcule automatiquement le **Coût Net Actualisé (CNA)** et le compare au **seuil d’exonération**.
""")

st.header("🔢 Paramètres à renseigner")

# Nouveau champ texte pour nom du site
nom_site = st.text_input("Nom du site", value="")

# Inputs avec annotations et cases à cocher
checkbox_states = []

def champ_avec_checkbox(label, value):
    col1, col2 = st.columns([3, 1])
    with col1:
        val = st.number_input(label, value=value)
    with col2:
        checked = st.checkbox("Donnée vérifiée", key=label)
    checkbox_states.append(checked)
    return val

def curseur_avec_checkbox(label, min_val, max_val, value, aide):
    col1, col2 = st.columns([3, 1])
    with col1:
        val = st.slider(label, min_val, max_val, value)
        st.caption(aide)
    with col2:
        checked = st.checkbox("Donnée vérifiée", key=label)
    checkbox_states.append(checked)
    return val

surface_parking = champ_avec_checkbox("Surface du parking (m²)", 3000.0)
surface_ombriere = champ_avec_checkbox("Surface à couvrir par l’ombrière (m²)", 2000.0)
valeur_parking = champ_avec_checkbox("Valeur vénale du parking (€)", 300000.0)
cout_initial = champ_avec_checkbox("Coût initial (CAPEX) du projet (€)", 420000.0)
duree = curseur_avec_checkbox("Durée d’étude (ans)", 0, 30, 20, "Durée standard recommandée : 20 ans")
taux_actualisation = curseur_avec_checkbox("Taux d’actualisation (%)", 0.0, 10.0, 5.0, "Taux recommandé : entre 4 % et 6 %")
seuil_exoneration_pourcent = curseur_avec_checkbox("Seuil d’exonération (%)", 0.0, 30.0, 10.0, "Seuil légal selon l'article R*111-24 du code de l'urbanisme")
cout_maintenance_annuel = champ_avec_checkbox("Coûts de maintenance annuels (€)", 3000.0)
cout_recyclage = champ_avec_checkbox("Coût total de démantèlement/recyclage (€)", 20000.0)
production_annuelle = champ_avec_checkbox("Production annuelle estimée (kWh)", 180000.0)
prix_kwh = champ_avec_checkbox("Prix de vente ou autoconsommation du kWh (€)", 0.08)
aides_total = champ_avec_checkbox("Montant total des aides ou subventions (€)", 0.0)

if not nom_site.strip():
    st.warning("Veuillez renseigner le nom du site pour continuer.")
elif not all(checkbox_states):
    st.warning("Veuillez cocher toutes les cases 'Donnée vérifiée' pour afficher les résultats.")
else:
    # Calculs
    r = taux_actualisation / 100
    revenus_actualises = sum((production_annuelle * prix_kwh) / ((1 + r) ** t) for t in range(1, duree + 1))
    revenus_actualises += aides_total

    maintenance_actualisee = sum(cout_maintenance_annuel / ((1 + r) ** t) for t in range(1, duree + 1))
    couts_actualises = cout_initial + maintenance_actualisee + (cout_recyclage / ((1 + r) ** duree))

    cna = couts_actualises - revenus_actualises
    seuil_exon = valeur_parking * (seuil_exoneration_pourcent / 100)
    exonere = "✅ OUI" if cna > seuil_exon else "❌ NON"

    st.header("📊 Résultats")
    st.metric("Revenus actualisés (€)", f"{revenus_actualises:,.2f}")
    st.metric("Coûts actualisés (€)", f"{couts_actualises:,.2f}")
    st.metric("Coût Net Actualisé (CNA) (€)", f"{cna:,.2f}")
    st.metric(f"Seuil d’exonération ({seuil_exoneration_pourcent:.0f}%) (€)", f"{seuil_exon:,.2f}")
    st.metric("Exonération possible ?", exonere)

    st.markdown("💡 **Conseil :** Si le CNA dépasse le seuil d’exonération, vous pouvez inclure ces résultats dans votre dossier préfectoral pour justifier l’exemption.")

    # PDF Export
    def generate_pdf(donnees, resultats, nom_site_pdf):
        def clean(text):
            return str(text).replace("’", "'").replace("–", "-").replace("€", "EUR").replace("✅", "OUI").replace("❌", "NON").replace("Σ", "Somme")

        donnees_clean = {clean(k): clean(v) for k, v in donnees.items()}
        resultats_clean = {clean(k): clean(v) for k, v in resultats.items()}

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Synthese du projet - Simulateur d'exoneration", ln=True, align='C')
        pdf.ln(8)
        pdf.set_font("Arial", 'I', 14)
        pdf.cell(0, 10, f"Site : {nom_site_pdf}", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "1. Données renseignées :", ln=True)
        pdf.set_font("Arial", '', 11)
        for k, v in donnees_clean.items():
            pdf.cell(0, 8, f"- {k} : {v}", ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Résultats calculés :", ln=True)
        pdf.set_font("Arial", '', 11)
        for k, v in resultats_clean.items():
            pdf.cell(0, 8, f"- {k} : {v}", ln=True)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Méthodologie de calcul", ln=True, align='C')
        pdf.ln(8)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, clean("""
Cette page détaille les formules utilisées dans le calcul du Cout Net Actualisé (CNA) et les critères d'exoneration.

1. Revenus actualisés = Somme sur la durée :
   (Production annuelle × Prix du kWh) / (1 + taux)^t + aides

2. Coûts actualisés = Coût initial + Somme des maintenances actualisées + Recyclage actualisé :
   CAPEX + Somme (maintenance / (1 + taux)^t) + (recyclage / (1 + taux)^durée)

3. CNA = Coûts actualisés - Revenus actualisés

4. Seuil d'exoneration = Valeur venale du parking × seuil %

5. Exoneration accordée si CNA > Seuil

Sources légales : Loi APER, décret d'application sur les ombrières photovoltaïques, articles du Code de l'urbanisme (R111-24 et suivants).
"""))

        output_path = "simulation_exoneration.pdf"
        pdf.output(output_path)
        return output_path

    donnees_pdf = {
        "Surface du parking (m²)": surface_parking,
        "Surface de l’ombrière (m²)": surface_ombriere,
        "Valeur vénale du parking (€)": valeur_parking,
        "Coût initial (€)": cout_initial,
        "Durée d’étude (ans)": duree,
        "Taux d’actualisation (%)": taux_actualisation,
        "Seuil d’exonération (%)": seuil_exoneration_pourcent,
        "Maintenance annuelle (€)": cout_maintenance_annuel,
        "Coût recyclage (€)": cout_recyclage,
        "Production annuelle (kWh)": production_annuelle,
        "Prix kWh (€)": prix_kwh,
        "Montant des aides (€)": aides_total
    }

    resultats_pdf = {
        "Revenus actualisés (€)": f"{revenus_actualises:,.2f}",
        "Coûts actualisés (€)": f"{couts_actualises:,.2f}",
        "CNA (€)": f"{cna:,.2f}",
        f"Seuil d’exonération ({seuil_exoneration_pourcent:.0f}%) (€)": f"{seuil_exon:,.2f}",
        "Exonération possible ?": exonere
    }

    chemin_pdf = generate_pdf(donnees_pdf, resultats_pdf, nom_site)
    with open(chemin_pdf, "rb") as file:
        st.download_button(
            label="📥 Télécharger le PDF",
            data=file,
            file_name="simulation_exoneration.pdf",
            mime="application/pdf"
        )
