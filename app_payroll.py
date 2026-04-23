import streamlit as st
import pandas as pd
from groq import Groq
import urllib.parse
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Tariffario Extra - Interno 🛸", layout="wide", page_icon="🛸")

# Custom CSS avanzato
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    
    /* STILE BOTTONI HOME (CARD) */
    .home-card-container div.stButton > button {
        border-radius: 12px;
        padding: 40px 20px;
        border: 1px solid #d1d9e0;
        background-color: white;
        transition: 0.3s;
        height: 180px !important;
        width: 100%;
        display: block;
        white-space: pre-wrap; /* Permette l'andata a capo */
        line-height: 1.4;
    }
    
    .home-card-container div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
        box-shadow: 0px 6px 15px rgba(0,0,0,0.08);
    }

    /* DISTANZA TRA TAB E CONTENUTO */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 25px;
    }
    
    .stTabs [aria-selected="true"] { 
        background-color: #ff4b4b !important; 
        color: white !important; 
    }

    /* BOTTONE TORNA HOME (PICCOLO) */
    .back-btn div.stButton > button {
        padding: 5px 15px;
        height: auto !important;
        width: auto !important;
        font-weight: normal;
        font-size: 14px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE STATO ---
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# --- CARICAMENTO DATI ---
SHEET_ID = "1JHJ0hEa9N9u76S5ZnFqGVKIB5QGzCnBv_85Fr7qLRGk"

@st.cache_data(ttl=60)
def load_data():
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
    df_p = pd.read_csv(f"{base_url}&sheet=" + urllib.parse.quote("Piani"))
    df_i = pd.read_csv(f"{base_url}&sheet=" + urllib.parse.quote("Funzionalità incluse"))
    df_e = pd.read_csv(f"{base_url}&sheet=" + urllib.parse.quote("Extra"))
    
    for df in [df_p, df_i, df_e]:
        df.columns = [str(c).strip().upper() for c in df.columns]
        
    if 'TITOLO' in df_e.columns:
        df_e['TITOLO_CLEAN'] = df_e['TITOLO'].apply(lambda x: re.sub(r'\*\*', '', str(x)).strip() if pd.notna(x) else "")
    return df_p, df_i, df_e

try:
    df_piani, df_incluse, df_extra = load_data()
except Exception as e:
    st.error(f"Errore nel caricamento dati: {e}")
    st.stop()

# --- FUNZIONI HELPER ---
def get_unique_options(df, column):
    if column not in df.columns: return ["Tutti"]
    all_items = df[column].dropna().unique()
    split_items = []
    for item in all_items:
        split_items.extend([i.strip() for i in str(item).split(',')])
    return ["Tutti"] + sorted(list(set(split_items)))

def torna_home():
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("⬅️ Home", key="home_back"):
        st.session_state.page = "🏠 Home"
        st.session_state.search_query = ""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOGICA PAGINE ---

# 1. HOME PAGE
if st.session_state.page == "🏠 Home":
    st.title("Tariffario Attività Extra 🛸")
    st.markdown("### Ciao! Cosa desideri consultare?")
    
    sq = st.text_input("🔍 Cerca subito un servizio extra", placeholder="Es: F24, CIGO, Inps...")
    if sq:
        st.session_state.search_query = sq
        st.session_state.page = "💸 Extra"
        st.rerun()

    st.write("---")
    
    st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 PIANI & INCLUSIONI\n\nScopri cosa comprende l'abbonamento", use_container_width=True):
            st.session_state.page = "📊 Piani"
            st.rerun()
    with c2:
        if st.button("💸 LISTINO EXTRA\n\nConsulta costi e ripartizioni", use_container_width=True):
            st.session_state.page = "💸 Extra"
            st.rerun()
    with c3:
        if st.button("🤖 ASSISTENTE AI\n\nPreventivi e domande rapide", use_container_width=True):
            st.session_state.page = "🤖 AI"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 2. PAGINA PIANI
elif st.session_state.page == "📊 Piani":
    torna_home()
    st.title("📊 Piani & Inclusioni")
    
    nomi_piani = [c for c in df_piani.columns if "FUNZIONALITA" not in c]
    piano_sel = st.selectbox("Seleziona il Piano del Cliente:", nomi_piani)
    
    st.write("---")
    col_a, col_b = st.columns(2)
    for i, (_, row) in enumerate(df_piani.iterrows()):
        curr_col = col_a if i % 2 == 0 else col_b
        func = str(row.get("FUNZIONALITA'", ""))
        icon = "✅" if "✅" in str(row.get(piano_sel, "")) else "❌"
        with curr_col.expander(f"{icon} {func}"):
            if "Payroll all-inclusive" in func:
                mask = df_incluse['CATEGORIA'].str.upper().str.contains('ADEMPIMENTI|PAGHE|CONTABILE', na=False)
                for d in df_incluse[mask]['DETTAGLIO']: st.write(f"• {d}")
            elif "Consulente del Lavoro dedicato" in func:
                mask = df_incluse['CATEGORIA'].str.upper().str.contains('CONSULENZA', na=False)
                for d in df_incluse[mask]['DETTAGLIO']: st.write(f"• {d}")

# 3. PAGINA EXTRA
elif st.session_state.page == "💸 Extra":
    torna_home()
    st.title("💸 Listino Servizi Extra")
    
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        sq_input = st.text_input("🔍 Ricerca testuale", value=st.session_state.search_query)
    with f2:
        f_cat = st.selectbox("Filtra Categoria", get_unique_options(df_extra, "CATEGORIA"))
    with f3:
        f_ente = st.selectbox("Filtra Ente", get_unique_options(df_extra, "ENTE"))
    
    df_mkt = df_extra.copy()
    if sq_input:
        df_mkt = df_mkt[df_mkt['TITOLO_CLEAN'].str.contains(sq_input, case=False, na=False) | 
                        df_mkt['DESCRIZIONE'].str.contains(sq_input, case=False, na=False)]
    if f_cat != "Tutti":
        df_mkt = df_mkt[df_mkt['CATEGORIA'].str.contains(f_cat, case=False, na=False)]
    if f_ente != "Tutti":
        df_mkt = df_mkt[df_mkt['ENTE'].str.contains(f_ente, case=False, na=False)]

    st.write("---")
    t0, t1, t2 = st.tabs(["🌎 TUTTI", "🔵 ORION STP", "🔴 CONSULENTE"])
    
    def show_items(df_sub):
        if df_sub.empty:
            st.info("Nessun extra trovato con i filtri selezionati.")
            return
        for _, row in df_sub.iterrows():
            with st.expander(f"**{row['TITOLO_CLEAN']}** | {row['PREZZO']}€"):
                st.write(row.get('DESCRIZIONE', '-'))
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Responsabile:** {row.get('RESPONSABILE', '-')}")
                    st.markdown(f"**Unità/Molt:** {row.get('MOLTIPLICATORE', '-')}")
                with c2:
                    st.markdown(f"**Ente:** {row.get('ENTE','-')}")
                    st.markdown(f"**Range:** {row.get('RANGE', '-')}")
                
                try:
                    j_p = int(float(row.get('PERC_JET', 100)))
                    c_p = int(float(row.get('PERC_CDL', 100 - j_p)))
                    st.markdown(f"""
                        <div style="display: flex; width: 100%; background-color: #eee; border-radius: 5px; overflow: hidden; height: 20px; border: 1px solid #ccc; margin-top: 10px;">
                            <div style="width: {j_p}%; background-color: #1E88E5; color: white; text-align: center; font-size: 10px; line-height: 20px; font-weight: bold;">JET {j_p}%</div>
                            <div style="width: {c_p}%; background-color: #FF4B4B; color: white; text-align: center; font-size: 10px; line-height: 20px; font-weight: bold;">CDL {c_p}%</div>
                        </div>
                    """, unsafe_allow_html=True)
                except: pass
                
                if pd.notna(row.get('NOTE')) and str(row['NOTE']) != 'nan':
                    st.caption(f"📝 {row['NOTE']}")

    with t0: show_items(df_mkt)
    with t1: show_items(df_mkt[df_mkt['RESPONSABILE'].str.contains('SERVICE|SPECIALIST', case=False, na=False)])
    with t2: show_items(df_mkt[df_mkt['RESPONSABILE'].str.contains('CONSULENTE', case=False, na=False)])

# 4. PAGINA AI
elif st.session_state.page == "🤖 AI":
    torna_home()
    st.title("🤖 Assistente AI")
    
    if st.button("🗑️ Svuota chat", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Chiedimi un preventivo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Sei l'assistente tecnico del tariffario payroll. Rispondi basandoti su: " + df_extra.to_string()}] + st.session_state.messages,
                    model="llama-3.3-70b-versatile"
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error(f"Errore: {e}")
