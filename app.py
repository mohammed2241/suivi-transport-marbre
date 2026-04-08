import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime

# 1. CONFIGURATION
st.set_page_config(page_title="Suivi Transport Orchidees", layout="wide")

# 2. TENTATIVE DE CONNEXION GOOGLE (SANS BLOQUER LE SITE)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_global = conn.read()
    storage_mode = "GOOGLE"
except Exception:
    storage_mode = "LOCAL"
    if 'journal_local' not in st.session_state:
        st.session_state.journal_local = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])
    df_global = st.session_state.journal_local

# Nettoyage si données vides
if df_global is None or (isinstance(df_global, pd.DataFrame) and df_global.empty):
    df_global = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])

# 3. DESIGN DU PORTAIL (COMME AU DÉBUT)
st.title("🚛 Suivi de Paiement Transport")
if storage_mode == "GOOGLE":
    st.caption("✅ Connecté en temps réel à Google Sheets")
else:
    st.caption("⚠️ Mode Local (Vérifiez vos Secrets Streamlit pour activer Google)")

# --- FORMULAIRE DE SAISIE ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        choix = st.selectbox("Chauffeur", ["Azzedine", "Rachid", "AUTRE"])
        nom = st.text_input("Nom du nouveau") if choix == "AUTRE" else choix
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        mat = st.text_input("Matricule")
        pr = st.number_input("Prix (DH)", value=1500, step=50)

    if st.button("✅ Enregistrer la course"):
        new_data = pd.DataFrame([{
            "Date": datetime.now().strftime("%d/%m/%Y"),
            "Transporteur": nom,
            "Direction": direction,
            "Matricule": mat,
            "Prix": pr,
            "Statut": "Non Payé"
        }])
        
        if storage_mode == "GOOGLE":
            df_up = pd.concat([df_global, new_data], ignore_index=True)
            conn.update(data=df_up)
        else:
            st.session_state.journal_local = pd.concat([st.session_state.journal_local, new_data], ignore_index=True)
        
        st.success(f"Enregistré : {nom}")
        st.rerun()

st.divider()

# --- AFFICHAGE DES RAPPORTS ---
tous_t = df_global["Transporteur"].unique()

for t in tous_t:
    with st.expander(f"👤 Dossier : {t}", expanded=True):
        df_t = df_global[df_global["Transporteur"] == t]
        
        # Affichage Tableau
        st.table(df_t[["Date", "Direction", "Matricule", "Prix", "Statut"]])
        
        col_m, col_b = st.columns([1, 1])
        du = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
        col_m.metric("Dû à ce jour", f"{du} DH")
        
        if col_b.button(f"Solder {t}", key=f"pay_{t}"):
            df_global.loc[df_global["Transporteur"] == t, "Statut"] = "Payé"
            if storage_mode == "GOOGLE":
                conn.update(data=df_global)
            st.rerun()
