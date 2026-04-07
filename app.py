import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Contrôle Transport", layout="wide")

# Initialisation du journal
if 'journal' not in st.session_state:
    st.session_state.journal = pd.DataFrame(columns=[
        "Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"
    ])

# Fonction pour créer le PDF (Indépendant pour chaque transporteur)
def create_pdf(df_transporteur, nom_transporteur):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Rapport de Transport : {nom_transporteur}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Edité le : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # En-têtes
    pdf.set_font("Arial", 'B', 10)
    cols = ["Date", "Direction", "Matricule", "Prix (DH)", "Statut"]
    widths = [35, 45, 40, 35, 35]
    for i in range(len(cols)):
        pdf.cell(widths[i], 10, cols[i], 1)
    pdf.ln()
    
    # Données
    pdf.set_font("Arial", size=10)
    total_du = 0
    for _, row in df_transporteur.iterrows():
        pdf.cell(35, 10, str(row['Date']), 1)
        pdf.cell(45, 10, str(row['Direction']), 1)
        pdf.cell(40, 10, str(row['Matricule']), 1)
        pdf.cell(35, 10, f"{row['Prix']}", 1)
        pdf.cell(35, 10, str(row['Statut']), 1)
        pdf.ln()
        if row['Statut'] == "Non Payé":
            total_du += row['Prix']
            
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"TOTAL NON PAYE : {total_du} DH", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

st.title("🚛 Suivi de Paiement Transport (Prix Libre)")

# --- 1. SAISIE MANUELLE SUR CHANTIER ---
st.subheader("📝 Nouveau chargement")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        transporteur = st.selectbox("Choisir le chauffeur", ["Azzedine", "Rachid"])
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        matricule = st.text_input("Matricule du Camion")
        # ICI : Vous introduisez le prix vous-même
        prix_saisi = st.number_input("Introduire le Prix du voyage (DH)", min_value=0, step=50, value=1500)

    if st.button("✅ Enregistrer la course"):
        if matricule and prix_saisi > 0:
            new_data = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": transporteur,
                "Direction": direction,
                "Matricule": matricule,
                "Prix": prix_saisi,
                "Statut": "Non Payé"
            }])
            st.session_state.journal = pd.concat([st.session_state.journal, new_data], ignore_index=True)
            st.success(f"Course de {transporteur} à {prix_saisi} DH enregistrée !")
        else:
            st.error("Veuillez remplir le matricule et le prix.")

st.divider()

# --- 2. GESTION DES ETATS SEPARES ---
st.subheader("📊 Rapports Individuels")

for t in ["Azzedine", "Rachid"]:
    st.write(f"### 👤 {t}")
    df_t = st.session_state.journal[st.session_state.journal["Transporteur"] == t]
    
    if not df_t.empty:
        col_t, col_p = st.columns([3, 1])
        with col_t:
            st.dataframe(df_t, use_container_width=True)
        with col_p:
            reste = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
            st.metric(f"Dû à {t}", f"{reste} DH")
            
            # Bouton PDF pour CE transporteur uniquement
            pdf_bytes = create_pdf(df_t, t)
            st.download_button(
                label=f"📄 Télécharger PDF {t}",
                data=pdf_bytes,
                file_name=f"Situation_{t}_{datetime.now().strftime('%d_%m')}.pdf",
                mime="application/pdf"
            )
            
            if st.button(f"Marquer {t} comme payé", key=f"pay_{t}"):
                st.session_state.journal.loc[st.session_state.journal["Transporteur"] == t, "Statut"] = "Payé"
                st.rerun()
    else:
        st.info(f"Pas de données pour {t}.")
