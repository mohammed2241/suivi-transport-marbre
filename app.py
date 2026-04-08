import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Transport Orchidees", layout="wide")

# Connexion Google Sheets (Lecture sans cache pour voir les changements direct)
conn = st.connection("gsheets", type=GSheetsConnection)
df_global = conn.read(ttl=0)

if df_global is None or df_global.empty:
    df_global = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])

# --- FONCTION PDF ---
def generer_pdf(df_source, nom_t, titre_rapport):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"{titre_rapport} : {nom_t}", ln=True, align='C')
    pdf.ln(10)
    
    # Entête tableau
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Date", 1)
    pdf.cell(50, 10, "Direction", 1)
    pdf.cell(40, 10, "Matricule", 1)
    pdf.cell(35, 10, "Prix (DH)", 1)
    pdf.cell(35, 10, "Statut", 1)
    pdf.ln()
    
    # Lignes
    pdf.set_font("Arial", size=10)
    for _, row in df_source.iterrows():
        pdf.cell(30, 10, str(row['Date']), 1)
        pdf.cell(50, 10, str(row['Direction']), 1)
        pdf.cell(40, 10, str(row['Matricule']), 1)
        pdf.cell(35, 10, str(row['Prix']), 1)
        pdf.cell(35, 10, str(row['Statut']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE SAISIE ---
st.title("🚛 Gestion des Transports")

with st.expander("📝 Enregistrer une nouvelle opération", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        choix = st.selectbox("Chauffeur", ["Azzedine", "Rachid", "AUTRE"])
        nom = st.text_input("Nom si AUTRE") if choix == "AUTRE" else choix
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with c2:
        mat = st.text_input("Matricule")
        pr = st.number_input("Prix (DH)", value=1500)

    if st.button("✅ Valider l'enregistrement"):
        new_row = pd.DataFrame([{
            "Date": datetime.now().strftime("%d/%m/%Y"),
            "Transporteur": nom, "Direction": direction,
            "Matricule": mat, "Prix": pr, "Statut": "Non Payé"
        }])
        df_final = pd.concat([df_global, new_row], ignore_index=True)
        conn.update(data=df_final)
        st.success("Enregistré sur Google Sheets")
        st.rerun()

st.divider()

# --- AFFICHAGE PAR TRANSPORTEUR ---
chauffeurs = df_global["Transporteur"].unique()

for t in chauffeurs:
    with st.expander(f"👤 Dossier : {t}", expanded=True):
        df_t = df_global[df_global["Transporteur"] == t]
        
        # 1. Tableau avec bouton supprimer pour chaque ligne
        for index, row in df_t.iterrows():
            col_info, col_prix, col_statut, col_del = st.columns([4, 1, 2, 1])
            col_info.write(f"📅 {row['Date']} | {row['Direction']} ({row['Matricule']})")
            col_prix.write(f"{row['Prix']} DH")
            col_statut.write(f"*{row['Statut']}*")
            if col_del.button("🗑️", key=f"del_{index}"):
                df_global = df_global.drop(index)
                conn.update(data=df_global)
                st.rerun()
        
        st.write("---")
        
        # 2. Section Rapports et Actions
        c_met, c_btn = st.columns([1, 2])
        
        reste = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
        c_met.metric("Reste à payer", f"{reste} DH")
        
        with c_btn:
            # Bouton Solder
            if st.button(f"Solder le compte de {t}", key=f"pay_{t}"):
                df_global.loc[df_global["Transporteur"] == t, "Statut"] = "Payé"
                conn.update(data=df_global)
                st.rerun()
            
            # Boutons PDF
            col_pdf1, col_pdf2 = st.columns(2)
            
            # PDF GLOBAL
            pdf_g = generer_pdf(df_t, t, "RAPPORT GLOBAL")
            col_pdf1.download_button(f"📄 Rapport Global {t}", data=pdf_g, file_name=f"Global_{t}.pdf", key=f"pdfg_{t}")
            
            # PDF NON PAYÉ
            df_np = df_t[df_t["Statut"] == "Non Payé"]
            if not df_np.empty:
                pdf_np = generer_pdf(df_np, t, "ETAT DES IMPAYÉS")
                col_pdf2.download_button(f"🚨 Liste Non Payés {t}", data=pdf_np, file_name=f"Dette_{t}.pdf", key=f"pdfnp_{t}")
