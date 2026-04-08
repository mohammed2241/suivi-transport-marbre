import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION ET CONNEXION ---
st.set_page_config(page_title="Portail Transport Orchidees", layout="wide")

# Connexion sécurisée au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données en temps réel
df_global = conn.read()

# Initialisation si le fichier est totalement vide
if df_global is None or df_global.empty:
    df_global = pd.DataFrame(columns=["Date", "Transporteur", "Direction", "Matricule", "Prix", "Statut"])

# --- FONCTION GÉNÉRATION PDF ---
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

# --- INTERFACE UTILISATEUR ---
st.title("🚛 Suivi de Paiement Transport Permanent")

# 1. FORMULAIRE DE SAISIE
with st.expander("📝 Enregistrer un nouveau chargement", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        choix_t = st.selectbox("Choisir le chauffeur", ["Azzedine", "Rachid", "AUTRE"])
        nom_final = st.text_input("Nom du nouveau transporteur") if choix_t == "AUTRE" else choix_t
        direction = st.selectbox("Direction", ["SINASTONE", "MEDIAL", "AUTRE"])
    with col2:
        matricule = st.text_input("Matricule du Camion")
        prix_saisi = st.number_input("Prix du voyage (DH)", min_value=0, step=50, value=1500)

    if st.button("✅ Valider et Enregistrer sur Google"):
        if matricule and nom_final:
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%d/%m/%Y"),
                "Transporteur": nom_final,
                "Direction": direction,
                "Matricule": matricule,
                "Prix": prix_saisi,
                "Statut": "Non Payé"
            }])
            df_updated = pd.concat([df_global, new_row], ignore_index=True)
            conn.update(data=df_updated)
            st.success(f"Course enregistrée pour {nom_final} !")
            st.rerun()
        else:
            st.error("Veuillez remplir tous les champs.")

st.divider()

# 2. AFFICHAGE DES DOSSIERS PAR TRANSPORTEUR
st.subheader("📊 Rapports et Situations (Données sauvegardées)")

tous_chauffeurs = df_global["Transporteur"].unique()

if len(tous_chauffeurs) == 0:
    st.info("Aucune donnée enregistrée pour le moment.")
else:
    for t in tous_chauffeurs:
        with st.expander(f"👤 Dossier : {t}", expanded=False):
            # Filtrer les données pour ce transporteur précis
            mask = df_global["Transporteur"] == t
            df_t = df_global[mask]
            
            col_tab, col_actions = st.columns([3, 1])
            
            with col_tab:
                # Affichage des lignes avec option de suppression
                for index, row in df_t.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
                    c1.write(f"**{row['Date']}** - {row['Direction']} ({row['Matricule']})")
                    c2.write(f"{row['Prix']} DH")
                    c3.write(f"Statut: {row['Statut']}")
                    if c4.button("🗑️", key=f"del_{index}"):
                        df_global = df_global.drop(index)
                        conn.update(data=df_global)
                        st.rerun()
            
            with col_actions:
                # Calculs financiers
                du = df_t[df_t["Statut"] == "Non Payé"]["Prix"].sum()
                st.metric("Reste à payer", f"{du} DH")
                
                # PDF 1 : Historique Complet
                pdf_all = create_pdf(df_t, t, "HISTORIQUE COMPLET")
                st.download_button(f"📄 Rapport Global {t}", data=pdf_all, file_name=f"Global_{t}.pdf", key=f"p1_{t}")
                
                # PDF 2 : Seulement les Impayés
                df_np = df_t[df_t["Statut"] == "Non Payé"]
                if not df_np.empty:
                    pdf_np = create_pdf(df_np, t, "IMPAYÉS (À RÉGLER)")
                    st.download_button(f"🚨 Liste Impayés {t}", data=pdf_np, file_name=f"Dette_{t}.pdf", key=f"p2_{t}")
                
                # Bouton pour solder le compte
                if st.button(f"Marquer {t} comme payé", key=f"pay_{t}"):
                    df_global.loc[df_global["Transporteur"] == t, "Statut"] = "Payé"
                    conn.update(data=df_global)
                    st.rerun()
