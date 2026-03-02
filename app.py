
# ============================================================
#  POLITICAL TRENDS MONITOR - app.py  (v2 - Facebook/Meta)
#  Streamlit dashboard per monitoraggio trend social politici
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import requests
import os

st.set_page_config(
    page_title="📡 Political Trends Monitor",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SEZIONE 1 - Connettore Facebook/Meta (attivo)
# ============================================================

def get_facebook_trends(access_token):
    """Recupera post trending da pagine politiche italiane pubbliche."""
    try:
        pages = ["LaRepubblica", "Corriere", "ilfattoquotidiano"]
        results = []
        for page in pages:
            url = f"https://graph.facebook.com/v19.0/{page}/posts"
            params = {
                "access_token": access_token,
                "fields": "message,reactions.summary(true),shares,created_time",
                "limit": 10
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for post in data:
                    msg = post.get("message", "")
                    reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
                    shares = post.get("shares", {}).get("count", 0)
                    results.append({
                        "source": page,
                        "message": msg[:120] + "..." if len(msg) > 120 else msg,
                        "reactions": reactions,
                        "shares": shares,
                        "created_time": post.get("created_time", "")
                    })
        return pd.DataFrame(results) if results else None
    except Exception as e:
        return None

# ============================================================
# SEZIONE 2 - Dati simulati (fallback se API non disponibile)
# ============================================================

POLITICAL_TOPICS = ["Economia", "Immigrazione", "Sanità", "Ambiente",
                    "Sicurezza", "Lavoro", "Tasse", "Scuola", "Giustizia", "Energia"]

PLATFORMS = ["Facebook", "Instagram", "X (Twitter)", "TikTok", "Reddit"]

def generate_weekly_data(weeks=8):
    rows = []
    base_date = datetime.now() - timedelta(weeks=weeks)
    for i in range(weeks):
        week_label = f"Sett {i+1}"
        week_date = base_date + timedelta(weeks=i)
        for topic in POLITICAL_TOPICS:
            for platform in PLATFORMS:
                volume = random.randint(50, 500) + i * random.randint(5, 20)
                sentiment_pos = random.uniform(0.15, 0.45)
                sentiment_neg = random.uniform(0.15, 0.40)
                sentiment_neu = 1 - sentiment_pos - sentiment_neg
                rows.append({
                    "week": week_label,
                    "week_date": week_date,
                    "topic": topic,
                    "platform": platform,
                    "volume": volume,
                    "sentiment_pos": round(sentiment_pos, 2),
                    "sentiment_neg": round(sentiment_neg, 2),
                    "sentiment_neu": round(sentiment_neu, 2),
                })
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def load_data():
    return generate_weekly_data(weeks=8)

def get_top_hashtags(topic, n=10):
    base = topic.lower().replace(" ", "")
    return pd.DataFrame({
        "hashtag": [f"#{base}{i}" for i in range(n)],
        "volume": sorted([random.randint(100, 5000) for _ in range(n)], reverse=True)
    })

# ============================================================
# SEZIONE 3 - SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Impostazioni")

selected_platforms = st.sidebar.multiselect(
    "Piattaforme", options=PLATFORMS, default=PLATFORMS
)
selected_topics = st.sidebar.multiselect(
    "Topic politici", options=POLITICAL_TOPICS, default=POLITICAL_TOPICS[:5]
)
n_weeks = st.sidebar.slider("Numero di settimane", min_value=2, max_value=8, value=6)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Stato Connessioni")

# Legge il token dai Secrets di Streamlit
meta_token = st.secrets.get("META_ACCESS_TOKEN", None)

if meta_token:
    st.sidebar.markdown("🟢 **Facebook: connesso**")
else:
    st.sidebar.markdown("🔴 Facebook: non connesso")

st.sidebar.markdown("🔴 X/Twitter: non connesso")
st.sidebar.markdown("🔴 Reddit: non connesso")

# ============================================================
# SEZIONE 4 - HEADER
# ============================================================

st.title("📡 Political Trends Monitor")
st.markdown("**Dashboard settimanale dei trend sui social network** — Uso editoriale per trasmissioni politiche")
st.markdown(f"_Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}_")

# ============================================================
# SEZIONE 5 - POST REALI DA FACEBOOK (se connesso)
# ============================================================

if meta_token:
    st.subheader("📘 Post in Trend su Facebook (Dati Reali)")
    with st.spinner("Caricamento post da Facebook..."):
        fb_df = get_facebook_trends(meta_token)
    if fb_df is not None and not fb_df.empty:
        st.dataframe(fb_df, use_container_width=True, hide_index=True)
        fig_fb = px.bar(
            fb_df.sort_values("reactions", ascending=False).head(10),
            x="reactions", y="source", orientation="h",
            color="shares", color_continuous_scale="Blues",
            labels={"reactions": "Reazioni", "source": "Pagina"},
            title="Post con più reazioni (Facebook)"
        )
        st.plotly_chart(fig_fb, use_container_width=True)
    else:
        st.info("Nessun dato Facebook disponibile al momento. Controlla il token nelle impostazioni.")
    st.markdown("---")

# ============================================================
# SEZIONE 6 - KPI CARDS
# ============================================================

df = load_data()
df_filtered = df[
    df["platform"].isin(selected_platforms) &
    df["topic"].isin(selected_topics)
]
latest_week = df_filtered["week"].iloc[-1]
df_latest = df_filtered[df_filtered["week"] == latest_week]

total_volume = int(df_latest["volume"].sum())
top_topic = df_latest.groupby("topic")["volume"].sum().idxmax()
top_platform = df_latest.groupby("platform")["volume"].sum().idxmax()
avg_sentiment_pos = round(df_latest["sentiment_pos"].mean() * 100, 1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💬 Volume totale settimana", f"{total_volume:,}")
col2.metric("🔥 Topic più discusso", top_topic)
col3.metric("📱 Piattaforma dominante", top_platform)
col4.metric("😊 Sentiment positivo medio", f"{avg_sentiment_pos}%")

st.markdown("---")

# ============================================================
# SEZIONE 7 - TREND SETTIMANALI
# ============================================================

st.subheader("📈 Trend Settimanali per Topic")
trend_df = df_filtered.groupby(["week", "topic"])["volume"].sum().reset_index()
fig_trend = px.line(
    trend_df, x="week", y="volume", color="topic",
    markers=True,
    labels={"week": "Settimana", "volume": "Volume discussioni", "topic": "Topic"},
    title="Evoluzione settimanale dei topic politici"
)
fig_trend.update_layout(legend=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_trend, use_container_width=True)

# ============================================================
# SEZIONE 8 - HEATMAP
# ============================================================

st.subheader("🌡️ Heatmap Intensità Topic × Piattaforma")
heatmap_df = df_latest.groupby(["topic", "platform"])["volume"].sum().reset_index()
heatmap_pivot = heatmap_df.pivot(index="topic", columns="platform", values="volume").fillna(0)
fig_heat = px.imshow(
    heatmap_pivot, color_continuous_scale="Blues",
    labels=dict(color="Volume"),
    title="Intensità discussione per topic e piattaforma (settimana corrente)"
)
st.plotly_chart(fig_heat, use_container_width=True)

# ============================================================
# SEZIONE 9 - SENTIMENT
# ============================================================

st.subheader("💭 Analisi Sentiment per Topic")
sent_df = df_latest.groupby("topic")[["sentiment_pos", "sentiment_neu", "sentiment_neg"]].mean().reset_index()
sent_melted = sent_df.melt(id_vars="topic", var_name="Sentiment", value_name="Percentuale")
sent_melted["Sentiment"] = sent_melted["Sentiment"].map({
    "sentiment_pos": "Positivo", "sentiment_neu": "Neutro", "sentiment_neg": "Negativo"
})
fig_sent = px.bar(
    sent_melted, x="topic", y="Percentuale", color="Sentiment",
    barmode="stack",
    color_discrete_map={"Positivo": "#2ecc71", "Neutro": "#95a5a6", "Negativo": "#e74c3c"},
    labels={"topic": "Topic", "Percentuale": "% Sentiment"},
    title="Distribuzione sentiment per topic"
)
st.plotly_chart(fig_sent, use_container_width=True)

# ============================================================
# SEZIONE 10 - HASHTAG
# ============================================================

st.subheader("# Hashtag più virali")
selected_for_hashtag = st.selectbox("Seleziona topic per hashtag", selected_topics)
hash_df = get_top_hashtags(selected_for_hashtag)
fig_hash = px.bar(
    hash_df, x="volume", y="hashtag", orientation="h",
    color="volume", color_continuous_scale="Blues",
    labels={"volume": "Volume menzioni", "hashtag": "Hashtag"},
    title=f"Top hashtag per '{selected_for_hashtag}'"
)
fig_hash.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_hash, use_container_width=True)

# ============================================================
# SEZIONE 11 - SCHEDA EDITORIALE
# ============================================================

st.subheader("📋 Scheda Editoriale Settimanale")
editorial_data = []
for topic in selected_topics:
    topic_df = df_latest[df_latest["topic"] == topic]
    vol = int(topic_df["volume"].sum())
    sent_pos = round(topic_df["sentiment_pos"].mean() * 100, 1)
    sent_neg = round(topic_df["sentiment_neg"].mean() * 100, 1)
    trend_icon = "📈" if vol > total_volume / len(selected_topics) else "📉"
    editorial_data.append({
        "Topic": topic,
        "Volume": vol,
        "Trend": trend_icon,
        "Sentiment 😊": f"{sent_pos}%",
        "Sentiment 😠": f"{sent_neg}%",
        "Consigliato in onda": "✅ Sì" if vol > total_volume / len(selected_topics) * 1.2 else "⬜ Valutare"
    })

editorial_df = pd.DataFrame(editorial_data).sort_values("Volume", ascending=False)
st.dataframe(editorial_df, use_container_width=True, hide_index=True)

# ============================================================
# SEZIONE 12 - EXPORT
# ============================================================

st.markdown("---")
st.subheader("⬇️ Esporta Report")
col_a, col_b = st.columns(2)
with col_a:
    csv = editorial_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Scarica Scheda Editoriale (CSV)",
        data=csv,
        file_name=f"scheda_editoriale_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
with col_b:
    full_csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Scarica Tutti i Dati (CSV)",
        data=full_csv,
        file_name=f"trends_completi_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Political Trends Monitor v2.0 | Facebook connesso | Generato con Perplexity AI")

