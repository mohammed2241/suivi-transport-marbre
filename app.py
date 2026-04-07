import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Contrôle Transport Marbre", layout="wide")

# Initialisation du journal si inexistant
if 'journal' not in st.session_state:
    st.session_state.journal = pd.DataFrame(columns=[
        "Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"
    ])

# Fonction pour créer le PDF
def create_pdf(df_transporteur, nom_transporteur):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Rapport de Transport : {nom_transporteur}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Edité le : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # En-têtes du tableau
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Direction", 1)
    pdf.cell(40, 10, "Matricule", 1)
    pdf.cell(35, 10, "Prix (DH)", 1)
    pdf.cell(35, 10, "Statut", 1)
    pdf.ln()
    
    # Données
    pdf.set_font("Arial", size=10)
    total = 0
    for i, row in df_transporteur.iterrows():
        pdf.cell(40, 10, str(row['Date']), 1)
        pdf.cell(40, 10, str(row['Direction']), 1)
        pdf.cell(40, 10, str(row['Matricule']), 1)
        pdf.cell(35, 10, f"{row['Prix']}", 1)
        pdf.cell(35, 10, str(row['Statut']), 1)
        pdf.ln()
        if row['Statut'] == "Non Payé":
            total += row['Prix']
            
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"TOTAL RESTE A PAYER : {total} DH", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

st.title("🏗️ Suivi de Paiement Transport Loué")

# --- 1. SAISIE RAPIDE SUR CHANTIER ---
st.subheader("📝 Nouvelle Entrée")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        transporteur = st.selectbox("Transporteur", ["Azzedine", "Rachid"])
    with col2:
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL"])
        prix = 1500 if direction == "SINASTONE" else 2500
    with col3:
        matricule = st.text_input("Matricule du Camion")

    if st.button("➕ Enregistrer la course"):
        if matricule:
            new_data = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": transporteur,
                "Direction": direction,
                "Matricule": matricule,
                "Prix": prix,
                "Statut": "Non Payé"
            }])
            st.session_state.journal = pd.concat([st.session_state.journal, new_data], ignore_index=True)
            st.success(f"Course de {transporteur} enregistrée !")
        else:
            st.error("Veuillez saisir le matricule.")

st.divider()

# --- 2. GESTION ET PDF PAR TRANSPORTEUR ---
st.subheader("📊 États de situation")

for t in ["Azzedine", "Rachid"]:
    st.write(f"### Suivi {t}")
    df_t = st.session_state.journal[st.session_state.journal["Transporteur"] == t]
    
    if not df_t.empty:
        col_table, col_actions = st.columns([3, 1])
        
        with col_table:
            st.dataframe(df_t, use_container_width=True)
        
        with col_actions:
            # Calcul du montant dû
            reste = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
            st.metric("Reste à payer", f"{reste} DH")
            
            # Bouton PDF
            pdf_data = create_pdf(df_t, t)
            st.download_button(
                label=f"📄 Télécharger PDF {t}",
                data=pdf_data,
                file_name=f"Rapport_Transport_{t}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
            # Bouton pour solder
            if st.button(f"Solder les comptes de {t}", key=f"btn_{t}"):
                st.session_state.journal.loc[st.session_state.journal["Transporteur"] == t, "Statut"] = "Payé"
                st.rerun()
    else:
        st.info(f"Aucun trajet enregistré pour {t}.")
