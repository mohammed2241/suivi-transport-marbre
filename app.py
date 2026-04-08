import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime

# 1. Connexion au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Chargement des données (Refresh automatique)
df_global = conn.read()

# Initialisation si vide
if df_global is None or df_global.empty:
    df_global = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])

st.title("🏗️ Portail de Suivi Transport")

# --- SAISIE ---
with st.expander("📝 Enregistrer une nouvelle course", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        choix = st.selectbox("Transporteur", ["Azzedine", "Rachid", "AUTRE"])
        nom_final = st.text_input("Nom du nouveau") if choix == "AUTRE" else choix
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        mat = st.text_input("Matricule")
        pr = st.number_input("Prix (DH)", value=1500)

    if st.button("✅ Enregistrer"):
        if mat and nom_final:
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": nom_final,
                "Direction": direction,
                "Matricule": mat,
                "Prix": pr,
                "Statut": "Non Payé"
            }])
            df_updated = pd.concat([df_global, new_row], ignore_index=True)
            conn.update(data=df_updated)
            st.success(f"Enregistré pour {nom_final}")
            st.rerun()

st.divider()

# --- AFFICHAGE PAR TRANSPORTEUR ---
for t in df_global["Transporteur"].unique():
    with st.expander(f"👤 Dossier : {t}"):
        df_t = df_global[df_global["Transporteur"] == t]
        
        # Affichage avec bouton supprimer pour chaque ligne
        for index, row in df_t.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"{row['Date']} - {row['Direction']} ({row['Matricule']})")
            c2.write(f"{row['Prix']} DH")
            c3.write(row['Statut'])
            if c4.button("🗑️", key=f"del_{index}"):
                df_global = df_global.drop(index)
                conn.update(data=df_global)
                st.rerun()

        # Rapports PDF
        du = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
        st.metric("Reste à payer", f"{du} DH")
        
        # Ici, vous pouvez ajouter vos fonctions de téléchargement PDF habituelles
        if st.button(f"Solder {t}", key=f"pay_{t}"):
            df_global.loc[df_global["Transporteur"] == t, "Statut"] = "Payé"
            conn.update(data=df_global)
            st.rerun()
