import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configuration
st.set_page_config(page_title="Suivi de Paiement Transport", layout="wide")

if 'journal' not in st.session_state:
    st.session_state.journal = pd.DataFrame(columns=[
        "Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"
    ])

def create_pdf(df_source, nom_transporteur, type_rapport="COMPLET"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Rapport {type_rapport} : {nom_transporteur}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Edité le : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
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

# --- 1. SAISIE AVEC OPTION "AUTRE" ---
st.subheader("📝 Nouveau chargement")
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        # Liste avec option Autre
        choix_transporteur = st.selectbox("Choisir le chauffeur", ["Azzedine", "Rachid", "AUTRE (Saisie manuelle)"])
        
        # SI "AUTRE" est choisi, on affiche une case pour taper le nom
        nom_final = choix_transporteur
        if choix_transporteur == "AUTRE (Saisie manuelle)":
            nom_final = st.text_input("Tapez le nom du nouveau transporteur")
            
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        matricule = st.text_input("Matricule du Camion")
        prix_saisi = st.number_input("Prix du voyage (DH)", min_value=0, step=50, value=1500)

    if st.button("✅ Enregistrer la course"):
        if matricule and nom_final:
            new_data = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": nom_final,
                "Direction": direction,
                "Matricule": matricule,
                "Prix": prix_saisi,
                "Statut": "Non Payé"
            }])
            st.session_state.journal = pd.concat([st.session_state.journal, new_data], ignore_index=True)
            st.success(f"Enregistré pour {nom_final} ({prix_saisi} DH)")
        else:
            st.error("Veuillez remplir le nom et le matricule.")

st.divider()

# --- 2. AFFICHAGE DYNAMIQUE DES RAPPORTS ---
st.subheader("📊 Rapports et Situations")

# On récupère tous les noms uniques présents dans le journal (Azzedine, Rachid + les nouveaux)
tous_les_chauffeurs = st.session_state.journal["Transporteur"].unique()

for t in tous_les_chauffeurs:
    with st.expander(f"👤 Dossier : {t}", expanded=True):
        df_t = st.session_state.journal[st.session_state.journal["Transporteur"] == t]
        
        col_tab, col_pdf = st.columns([2, 1])
        with col_tab:
            st.dataframe(df_t, use_container_width=True)
        
        with col_pdf:
            du = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
            st.metric(f"Dû à {t}", f"{du} DH")
            
            # Rapport COMPLET
            pdf_complet = create_pdf(df_t, t, "COMPLET")
            st.download_button(label=f"📥 Rapport complet {t}", data=pdf_complet, file_name=f"Historique_{t}.pdf", key=f"all_{t}")
            
            # Rapport IMPAYÉS UNIQUEMENT
            df_np = df_t[df_t["Statut"] == "Non Payé"]
            if not df_np.empty:
                pdf_np = create_pdf(df_np, t, "IMPAYÉS")
                st.download_button(label=f"🚨 Liste Impayés {t}", data=pdf_np, file_name=f"Impayes_{t}.pdf", key=f"np_{t}")
            
            if st.button(f"Solder {t}", key=f"pay_{t}"):
                st.session_state.journal.loc[st.session_state.journal["Transporteur"] == t, "Statut"] = "Payé"
                st.rerun()
