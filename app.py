import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Suivi de Paiement Transport", layout="wide")

# Initialisation du journal dans la session
if 'journal' not in st.session_state:
    st.session_state.journal = pd.DataFrame(columns=[
        "Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"
    ])

# Fonction pour créer le PDF
def create_pdf(df_source, nom_transporteur, type_rapport="COMPLET"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Rapport {type_rapport} : {nom_transporteur}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Edite le : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    cols = ["Date", "Direction", "Matricule", "Prix (DH)", "Statut"]
    widths = [35, 45, 40, 35, 35]
    for i in range(len(cols)):
        pdf.cell(widths[i], 10, cols[i], 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    total_non_paye = 0
    for _, row in df_source.iterrows():
        pdf.cell(35, 10, str(row['Date']), 1)
        pdf.cell(45, 10, str(row['Direction']), 1)
        pdf.cell(40, 10, str(row['Matricule']), 1)
        pdf.cell(35, 10, f"{row['Prix']}", 1)
        pdf.cell(35, 10, str(row['Statut']), 1)
        pdf.ln()
        if row['Statut'] == "Non Payé":
            total_non_paye += row['Prix']
            
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"TOTAL EN ATTENTE : {total_non_paye} DH", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

st.title("🚛 Suivi de Paiement Transport")

# --- 1. SAISIE ---
st.subheader("📝 Nouveau chargement")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        choix_t = st.selectbox("Choisir le chauffeur", ["Azzedine", "Rachid", "AUTRE"])
        nom_final = choix_t
        if choix_t == "AUTRE":
            nom_final = st.text_input("Nom du nouveau transporteur")
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        matricule = st.text_input("Matricule du Camion")
        prix_saisi = st.number_input("Prix du voyage (DH)", min_value=0, step=50, value=1500)

    if st.button("✅ Enregistrer la course"):
        if matricule and nom_final:
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Transporteur": nom_final,
                "Direction": direction,
                "Matricule": matricule,
                "Prix": prix_saisi,
                "Statut": "Non Payé"
            }])
            st.session_state.journal = pd.concat([st.session_state.journal, new_row], ignore_index=True)
            st.success(f"Enregistré pour {nom_final}")
            st.rerun()

st.divider()

# --- 2. AFFICHAGE ET MODIFICATION ---
st.subheader("📊 Rapports et Gestion")

tous_chauffeurs = st.session_state.journal["Transporteur"].unique()

for t in tous_chauffeurs:
    with st.expander(f"👤 Dossier : {t}", expanded=True):
        # Filtrer les données pour ce transporteur
        mask = st.session_state.journal["Transporteur"] == t
        df_t = st.session_state.journal[mask]
        
        if not df_t.empty:
            # Affichage du tableau avec index pour repérer les lignes
            st.write("Détails des trajets :")
            
            # --- SYSTÈME DE SUPPRESSION PAR LIGNE ---
            for index, row in df_t.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 1, 2, 1])
                c1.text(row['Date'])
                c2.text(row['Direction'])
                c3.text(row['Matricule'])
                c4.text(f"{row['Prix']}DH")
                c5.text(row['Statut'])
                if c6.button("🗑️", key=f"del_{index}"):
                    st.session_state.journal = st.session_state.journal.drop(index)
                    st.rerun()

            st.divider()
            
            # --- ACTIONS ET PDF ---
            col_m, col_b1, col_b2, col_b3 = st.columns([1, 1, 1, 1])
            
            du = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
            col_m.metric("À payer", f"{du} DH")
            
            # PDF Complet
            pdf_all = create_pdf(df_t, t, "COMPLET")
            col_b1.download_button("📄 Rapport Complet", data=pdf_all, file_name=f"Total_{t}.pdf", key=f"pdf_all_{t}")
            
            # PDF Impayés
            df_np = df_t[df_t["Statut"] == "Non Payé"]
            if not df_np.empty:
                pdf_np = create_pdf(df_np, t, "IMPAYÉS")
                col_b2.download_button("🚨 Liste Impayés", data=pdf_np, file_name=f"Dette_{t}.pdf", key=f"pdf_np_{t}")
            
            if col_b3.button(f"Solder {t}", key=f"pay_{t}"):
                st.session_state.journal.loc[st.session_state.journal["Transporteur"] == t, "Statut"] = "Payé"
                st.rerun()
        else:
            st.info(f"Aucune donnée pour {t}")
