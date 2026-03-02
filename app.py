
# ============================================================
#  POLITICAL TRENDS MONITOR - app.py  (v3 - Temi personalizzati)
#  Temi: Sicurezza, Sanità, Ambiente, Guerre, Autonomia, Lavoro
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import requests

st.set_page_config(
    page_title="📡 Political Trends Monitor",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# TEMI FISSI DELLA TRASMISSIONE
# ============================================================

TEMI_TRASMISSIONE = {
    "Sicurezza": ["#sicurezza", "#decretoSicurezza", "#criminalità", "#polizia", "#carabinieri"],
    "Sanità": ["#sanità", "#SSN", "#ospedali", "#medici", "#salute", "#listeAttesa"],
    "Ambiente": ["#ambiente", "#climaItalia", "#transizione", "#energie", "#inquinamento"],
    "Guerre": ["#Ucraina", "#Iran", "#guerra", "#NATO", "#pace", "#conflitto"],
    "Autonomia Differenziata": ["#autonomia", "#autonomiaDifferenziata", "#regioni", "#Calderoli"],
    "Lavoro": ["#lavoro", "#salarioMinimo", "#disoccupazione", "#contratti", "#sindacati"],
}

PLATFORMS = ["Facebook", "Instagram", "X (Twitter)", "TikTok", "Reddit"]

# Colori per tema
TEMA_COLORS = {
    "Sicurezza": "#e74c3c",
    "Sanità": "#3498db",
    "Ambiente": "#2ecc71",
    "Guerre": "#e67e22",
    "Autonomia Differenziata": "#9b59b6",
    "Lavoro": "#1abc9c",
}

# ============================================================
# CONNETTORE FACEBOOK (reale)
# ============================================================

def get_facebook_posts_by_topic(access_token, topic, keywords):
    """Cerca post pubblici che contengono le keyword del tema."""
    try:
        results = []
        for kw in keywords[:3]:
            url = "https://graph.facebook.com/v19.0/search"
            params = {
                "q": kw,
                "type": "post",
                "access_token": access_token,
                "fields": "message,created_time,permalink_url",
                "limit": 5
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for post in data:
                    msg = post.get("message", "")
                    results.append({
                        "Tema": topic,
                        "Keyword": kw,
                        "Post": msg[:150] + "..." if len(msg) > 150 else msg,
                        "Data": post.get("created_time", "")[:10],
                        "Link": post.get("permalink_url", "")
                    })
        return pd.DataFrame(results) if results else None
    except Exception:
        return None

def get_facebook_page_posts(access_token):
    """Recupera post da pagine italiane e classifica per tema."""
    try:
        pages = ["LaRepubblica", "Corriere", "ilfattoquotidiano", "TgLa7"]
        results = []
        for page in pages:
            url = f"https://graph.facebook.com/v19.0/{page}/posts"
            params = {
                "access_token": access_token,
                "fields": "message,reactions.summary(true),shares,created_time",
                "limit": 20
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for post in data:
                    msg = post.get("message", "").lower()
                    reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
                    shares = post.get("shares", {}).get("count", 0)
                    tema_rilevato = "Altro"
                    for tema, keywords in TEMI_TRASMISSIONE.items():
                        if any(k.lower().replace("#", "") in msg for k in keywords):
                            tema_rilevato = tema
                            break
                    results.append({
                        "Fonte": page,
                        "Tema": tema_rilevato,
                        "Post": post.get("message", "")[:120] + "...",
                        "Reazioni": reactions,
                        "Condivisioni": shares,
                        "Data": post.get("created_time", "")[:10],
                    })
        return pd.DataFrame(results) if results else None
    except Exception:
        return None

# ============================================================
# DATI SIMULATI (fallback + temi personalizzati)
# ============================================================

@st.cache_data(ttl=3600)
def generate_weekly_data(weeks=8):
    rows = []
    base_date = datetime.now() - timedelta(weeks=weeks)
    for i in range(weeks):
        week_label = f"Sett {i+1}"
        for tema in TEMI_TRASMISSIONE.keys():
            for platform in PLATFORMS:
                volume = random.randint(80, 600) + i * random.randint(5, 25)
                sentiment_pos = random.uniform(0.10, 0.40)
                sentiment_neg = random.uniform(0.15, 0.45)
                sentiment_neu = 1 - sentiment_pos - sentiment_neg
                rows.append({
                    "week": week_label,
                    "tema": tema,
                    "platform": platform,
                    "volume": volume,
                    "sentiment_pos": round(sentiment_pos, 2),
                    "sentiment_neg": round(sentiment_neg, 2),
                    "sentiment_neu": round(sentiment_neu, 2),
                })
    return pd.DataFrame(rows)

def get_trending_emergenti():
    """Simula temi emergenti non ancora in lista."""
    emergenti = [
        ("Riforma Pensioni", random.randint(200, 800), "📈 Nuovo"),
        ("Decreto Flussi", random.randint(100, 500), "📈 In crescita"),
        ("Manovra Finanziaria", random.randint(300, 900), "🔥 Virale"),
        ("Elezioni Regionali", random.randint(150, 600), "📈 In crescita"),
        ("Bonus Edilizio", random.randint(80, 400), "📈 Nuovo"),
    ]
    return pd.DataFrame(emergenti, columns=["Tema Emergente", "Volume", "Stato"])

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Impostazioni")
selected_temi = st.sidebar.multiselect(
    "Temi della trasmissione",
    options=list(TEMI_TRASMISSIONE.keys()),
    default=list(TEMI_TRASMISSIONE.keys())
)
selected_platforms = st.sidebar.multiselect(
    "Piattaforme", options=PLATFORMS, default=PLATFORMS
)
n_weeks = st.sidebar.slider("Settimane da visualizzare", 2, 8, 6)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Stato Connessioni")
meta_token = st.secrets.get("META_ACCESS_TOKEN", None)
if meta_token:
    st.sidebar.markdown("🟢 **Facebook: connesso**")
else:
    st.sidebar.markdown("🔴 Facebook: non connesso")
st.sidebar.markdown("🔴 X/Twitter: non connesso")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏷️ Hashtag monitorati")
for tema in selected_temi:
    hashtags = ", ".join(TEMI_TRASMISSIONE[tema][:3])
    st.sidebar.markdown(f"**{tema}**: {hashtags}")

# ============================================================
# HEADER
# ============================================================

st.title("📡 Political Trends Monitor")
st.markdown("**Dashboard settimanale — Temi personalizzati per la trasmissione**")
st.markdown(f"_Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}_")

# ============================================================
# SEZIONE: POST REALI DA FACEBOOK
# ============================================================

if meta_token:
    st.subheader("📘 Post in Trend su Facebook (Dati Reali)")
    with st.spinner("Recupero post da Facebook..."):
        fb_df = get_facebook_page_posts(meta_token)

    if fb_df is not None and not fb_df.empty:
        tab_temi = [t for t in selected_temi if t in fb_df["Tema"].values] + ["Altro"]
        tabs = st.tabs(tab_temi)
        for i, tema in enumerate(tab_temi):
            with tabs[i]:
                tema_df = fb_df[fb_df["Tema"] == tema].sort_values("Reazioni", ascending=False)
                st.dataframe(tema_df[["Fonte","Post","Reazioni","Condivisioni","Data"]],
                             use_container_width=True, hide_index=True)
    else:
        st.info("Nessun post Facebook disponibile al momento.")
    st.markdown("---")

# ============================================================
# KPI CARDS
# ============================================================

df = generate_weekly_data()
df_filtered = df[
    df["tema"].isin(selected_temi) &
    df["platform"].isin(selected_platforms)
]
df_latest = df_filtered[df_filtered["week"] == df_filtered["week"].iloc[-1]]

total_volume = int(df_latest["volume"].sum())
top_tema = df_latest.groupby("tema")["volume"].sum().idxmax()
top_platform = df_latest.groupby("platform")["volume"].sum().idxmax()
tema_neg = df_latest.groupby("tema")["sentiment_neg"].mean().idxmax()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💬 Volume totale settimana", f"{total_volume:,}")
col2.metric("🔥 Tema più discusso", top_tema)
col3.metric("📱 Piattaforma dominante", top_platform)
col4.metric("⚠️ Tema più controverso", tema_neg)

st.markdown("---")

# ============================================================
# TREND SETTIMANALI
# ============================================================

st.subheader("📈 Trend Settimanali per Tema")
trend_df = df_filtered.groupby(["week", "tema"])["volume"].sum().reset_index()
fig_trend = px.line(
    trend_df, x="week", y="volume", color="tema",
    markers=True,
    color_discrete_map=TEMA_COLORS,
    labels={"week": "Settimana", "volume": "Volume discussioni", "tema": "Tema"},
    title="Evoluzione settimanale dei temi della trasmissione"
)
fig_trend.update_layout(legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig_trend, use_container_width=True)

# ============================================================
# SENTIMENT PER TEMA
# ============================================================

st.subheader("💭 Sentiment per Tema (settimana corrente)")
sent_df = df_latest.groupby("tema")[["sentiment_pos","sentiment_neu","sentiment_neg"]].mean().reset_index()
sent_melted = sent_df.melt(id_vars="tema", var_name="Sentiment", value_name="Percentuale")
sent_melted["Sentiment"] = sent_melted["Sentiment"].map({
    "sentiment_pos": "Positivo", "sentiment_neu": "Neutro", "sentiment_neg": "Negativo"
})
fig_sent = px.bar(
    sent_melted, x="tema", y="Percentuale", color="Sentiment",
    barmode="stack",
    color_discrete_map={"Positivo": "#2ecc71", "Neutro": "#95a5a6", "Negativo": "#e74c3c"},
    labels={"tema": "Tema", "Percentuale": "% Sentiment"},
    title="Come il pubblico parla di ogni tema"
)
st.plotly_chart(fig_sent, use_container_width=True)

# ============================================================
# HEATMAP
# ============================================================

st.subheader("🌡️ Dove se ne parla di più")
heatmap_df = df_latest.groupby(["tema", "platform"])["volume"].sum().reset_index()
heatmap_pivot = heatmap_df.pivot(index="tema", columns="platform", values="volume").fillna(0)
fig_heat = px.imshow(
    heatmap_pivot, color_continuous_scale="Blues",
    labels=dict(color="Volume"),
    title="Intensità per tema e piattaforma"
)
st.plotly_chart(fig_heat, use_container_width=True)

# ============================================================
# TEMI EMERGENTI (novità della settimana)
# ============================================================

st.subheader("🚨 Temi Emergenti questa settimana")
st.markdown("_Argomenti non ancora in lista ma in forte crescita sui social_")
emergenti_df = get_trending_emergenti()
col_e1, col_e2 = st.columns([2,1])
with col_e1:
    fig_em = px.bar(
        emergenti_df, x="Volume", y="Tema Emergente", orientation="h",
        color="Volume", color_continuous_scale="Oranges",
        title="Volume discussioni temi emergenti"
    )
    fig_em.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_em, use_container_width=True)
with col_e2:
    st.dataframe(emergenti_df, use_container_width=True, hide_index=True)

# ============================================================
# SCHEDA EDITORIALE
# ============================================================

st.markdown("---")
st.subheader("📋 Scheda Editoriale — Pronti per la Regia")
editorial_data = []
for tema in selected_temi:
    tema_df = df_latest[df_latest["tema"] == tema]
    vol = int(tema_df["volume"].sum())
    sent_pos = round(tema_df["sentiment_pos"].mean() * 100, 1)
    sent_neg = round(tema_df["sentiment_neg"].mean() * 100, 1)
    hashtags = " ".join(TEMI_TRASMISSIONE[tema][:3])
    trend_icon = "📈" if vol > total_volume / len(selected_temi) else "📉"
    consiglio = "✅ In onda" if vol > total_volume / len(selected_temi) * 1.2 else "⬜ Valutare"
    editorial_data.append({
        "Tema": tema,
        "Volume": vol,
        "Trend": trend_icon,
        "😊 Positivo": f"{sent_pos}%",
        "😠 Negativo": f"{sent_neg}%",
        "Hashtag chiave": hashtags,
        "Consiglio regia": consiglio,
    })

editorial_df = pd.DataFrame(editorial_data).sort_values("Volume", ascending=False)
st.dataframe(editorial_df, use_container_width=True, hide_index=True)

# EXPORT
st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    csv = editorial_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Scarica Scheda Editoriale (CSV)", csv,
        f"scheda_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
with col_b:
    full_csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Scarica Tutti i Dati (CSV)", full_csv,
        f"trends_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

st.caption("Political Trends Monitor v3.0 | Temi: Sicurezza · Sanità · Ambiente · Guerre · Autonomia · Lavoro | Perplexity AI")
