import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Transport Orchidees", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture forcée (on ne veut pas d'anciennes données en cache)
df_global = conn.read(ttl=0) 

# Initialisation de secours si le fichier est vide
if df_global is None or df_global.empty:
    df_global = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])

# --- INTERFACE ---
st.title("🚛 Portail Transport Orchidees")

# 1. FORMULAIRE
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        choix = st.selectbox("Chauffeur", ["Azzedine", "Rachid", "AUTRE"])
        nom = st.text_input("Nom du nouveau") if choix == "AUTRE" else choix
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        mat = st.text_input("Matricule")
        pr = st.number_input("Prix (DH)", value=1500)

    if st.button("✅ Enregistrer la course"):
        if mat and nom:
            # Création de la nouvelle ligne
            nouvelle_ligne = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": nom,
                "Direction": direction,
                "Matricule": mat,
                "Prix": pr,
                "Statut": "Non Payé"
            }])
            
            # On combine l'ancien tableau avec la nouvelle ligne
            df_final = pd.concat([df_global, nouvelle_ligne], ignore_index=True)
            
            # MISE À JOUR CRUCIALE : On renvoie TOUT le tableau mis à jour
            conn.update(data=df_final)
            
            st.success(f"Enregistré pour {nom}")
            st.rerun() # On force le portail à se recharger pour afficher la nouvelle ligne

st.divider()

# 2. AFFICHAGE PAR DOSSIER (PORTAIL)
tous_les_noms = df_global["Transporteur"].unique()

if len(tous_les_noms) == 0:
    st.info("Aucun trajet enregistré dans le Google Sheet.")
else:
    for t in tous_les_noms:
        # Création d'un dossier visuel pour chaque transporteur
        with st.expander(f"👤 Dossier de : {t}", expanded=True):
            # Filtrage des trajets du chauffeur
            df_chauffeur = df_global[df_global["Transporteur"] == t]
            
            # Affichage en tableau propre
            st.dataframe(df_chauffeur[["Date", "Direction", "Matricule", "Prix", "Statut"]], use_container_width=True)
            
            # Calcul du reste à payer
            reste = df_chauffeur[df_chauffeur["Statut"] == "Non Payé"]["Prix"].sum()
            
            c1, c2 = st.columns([1, 1])
            c1.metric("À régler", f"{reste} DH")
            
            if c2.button(f"Solder {t}", key=f"pay_{t}"):
                # Changer le statut dans le tableau global
                df_global.loc[df_global["Transporteur"] == t, "Statut"] = "Payé"
                conn.update(data=df_global)
                st.rerun()
