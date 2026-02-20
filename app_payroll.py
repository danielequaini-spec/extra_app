import streamlit as st
import pandas as pd
from groq import Groq
import urllib.parse
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Tariffario extra", layout="wide", page_icon="🛸")

# Custom CSS: UI pulita, Tab rosse quando selezionate, no blu.
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 4px; padding: 10px 20px; color: #31333F;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ff4b4b !important; color: white !important; 
    }
    div[data-testid="stExpander"] { border: 1px solid #d1d9e0; border-radius: 8px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- FUNZIONE PULIZIA TITOLI ---
def clean_title(text):
    if pd.isna(text): return ""
    return re.sub(r'\*\*', '', str(text)).strip()

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
        df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
    
    if 'TITOLO' in df_e.columns:
        df_e['TITOLO_CLEAN'] = df_e['TITOLO'].apply(clean_title)
    
    return df_p, df_i, df_e

df_piani, df_incluse, df_extra = load_data()

# --- SIDEBAR: FILTRI DROPDOWN INTELLIGENTI ---
st.sidebar.header("🎯 Filtri Rapidi")

def get_unique_options(df, column):
    if column not in df.columns: return ["Tutti"]
    # Esplode le celle che contengono virgole per avere opzioni singole nel dropdown
    all_items = df[column].dropna().unique()
    split_items = []
    for item in all_items:
        split_items.extend([i.strip() for i in str(item).split(',')])
    return ["Tutti"] + sorted(list(set(split_items)))

f_cat = st.sidebar.selectbox("Filtra per Categoria", get_unique_options(df_extra, "CATEGORIA"))
f_ente = st.sidebar.selectbox("Filtra per Ente", get_unique_options(df_extra, "ENTE"))

if st.sidebar.button("Reset Chat"):
    st.session_state.messages = []
    st.rerun()

# --- LOGICA DI FILTRAGGIO ---
df_mkt = df_extra.copy()

if f_cat != "Tutti":
    df_mkt = df_mkt[df_mkt['CATEGORIA'].str.contains(f_cat, case=False, na=False)]
if f_ente != "Tutti":
    df_mkt = df_mkt[df_mkt['ENTE'].str.contains(f_ente, case=False, na=False)]

# --- HEADER E RICERCA GLOBALE ---
st.title("🛸 Tariffario extra")
search_q = st.text_input("🔍 Ricerca rapida (es: F24 crediti)", placeholder="Cerca nel titolo o descrizione...")

if search_q:
    words = search_q.split()
    for word in words:
        df_mkt = df_mkt[
            df_mkt['TITOLO_CLEAN'].str.contains(word, case=False, na=False) | 
            df_mkt['DESCRIZIONE'].str.contains(word, case=False, na=False)
        ]

# --- LAYOUT PRINCIPALE ---
col_sx, col_dx = st.columns([1, 1.2], gap="large")

with col_sx:
    st.subheader("📊 Piani & Inclusioni")
    nomi_piani = [c for c in df_piani.columns if "FUNZIONALITA" not in c]
    piano_sel = st.selectbox("Seleziona Piano Cliente:", nomi_piani)
    
    for _, row in df_piani.iterrows():
        func = str(row.get("FUNZIONALITA'", ""))
        is_inc = "✅" in str(row.get(piano_sel, ""))
        icon = "✅" if is_inc else "❌"
        
        with st.expander(f"{icon} {func}"):
            if "Payroll all-inclusive" in func:
                mask = df_incluse['CATEGORIA'].str.upper().str.contains('ADEMPIMENTI|PAGHE|CONTABILE', na=False)
                for d in df_incluse[mask]['DETTAGLIO']: st.write(f"• {d}")
            elif "Consulente del Lavoro dedicato" in func:
                mask = df_incluse['CATEGORIA'].str.upper().str.contains('CONSULENZA', na=False)
                for d in df_incluse[mask]['DETTAGLIO']: st.write(f"• {d}")

with col_dx:
    st.subheader("💸 Extra")
    t0, t1, t2 = st.tabs(["🌎 TUTTI", "🔵 HR JET", "🔴 CONSULENTE"])
    
    def show_items(df_sub):
        if df_sub.empty:
            st.info("Nessun extra trovato.")
        for _, row in df_sub.iterrows():
            with st.expander(f"**{row['TITOLO_CLEAN']}** | {row['PREZZO']}€"):
                st.write(row.get('DESCRIZIONE', '-'))
                st.markdown(f"**Resp:** {row['RESPONSABILE']} | **Ente:** {row.get('ENTE','-')}")
                if pd.notna(row.get('NOTE')) and str(row['NOTE']) != 'nan':
                    st.caption(f"📝 {row['NOTE']}")

    with t0: show_items(df_mkt)
    with t1: show_items(df_mkt[df_mkt['RESPONSABILE'].str.contains('SERVICE|SPECIALIST', case=False, na=False)])
    with t2: show_items(df_mkt[df_mkt['RESPONSABILE'].str.contains('CONSULENTE', case=False, na=False)])

# --- CHAT AI ---
st.divider()
st.header("🤖 Chiedi un preventivo")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Es. l'inserimento di un credito in F24 è un extra?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # INSERISCI QUI LA TUA CHIAVE GROQ
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        mini_extra = df_extra[['TITOLO_CLEAN', 'PREZZO', 'DESCRIZIONE', 'RESPONSABILE', 'MOLTIPLICATORE', 'RANGE', 'NOTE']].to_string(index=False)
        sys_prompt = f"""Sei l'esperto Payroll di riferimento. 
        LISTINO: {mini_extra}
        REGOLE:
        1. Se attività nelle inclusioni gratuite -> GRATUITA.
        2. Se Extra: classifica 'Extra Tipizzato' o 'Non Tipizzato'.
        3. Clasifica 'Prezzo Fisso' o 'Variabile'.
        4. Se l'utente corregge le ore, ricalcola.
        RISPOSTA OBBLIGATORIA:
        - STATO: [Incluso/Extra Tipizzato/Non Tipizzato]
        - TIPO: [Gratuito/Fisso/Variabile]
        - CALCOLO: [Dettaglio aritmetico]
        - RESPONSABILE: [JET o CDL]"""

        res = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.2
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})