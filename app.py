
# ============================================================
#  POLITICAL TRENDS MONITOR - app.py
#  Streamlit dashboard per monitoraggio trend social politici
#  Autore: generato da Perplexity AI
#  Requisiti: pip install streamlit tweepy praw plotly pandas
#             transformers torch schedule python-dotenv
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import json

# --- Pagina config ---
st.set_page_config(
    page_title="📡 Political Trends Monitor",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SEZIONE 1 - Connettori API (decommentare con le tue API KEY)
# ============================================================

# --- X/Twitter ---
# import tweepy
# BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
# client = tweepy.Client(bearer_token=BEARER_TOKEN)
# def get_twitter_trends(woeid=23424853):  # 23424853 = Italia
#     trends = client.get_place_trends(id=woeid)
#     return [(t["name"], t.get("tweet_volume", 0)) for t in trends[0]["trends"]]

# --- Reddit ---
# import praw
# reddit = praw.Reddit(
#     client_id=os.getenv("REDDIT_CLIENT_ID"),
#     client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
#     user_agent="PoliticalTrendsMonitor/1.0"
# )
# def get_reddit_trends(subreddit_name="politicaitaliana"):
#     sub = reddit.subreddit(subreddit_name)
#     return [(post.title, post.score) for post in sub.hot(limit=20)]

# ============================================================
# SEZIONE 2 - Dati simulati (sostituire con funzioni API reali)
# ============================================================

POLITICAL_TOPICS = ["Economia", "Immigrazione", "Sanità", "Ambiente",
                    "Sicurezza", "Lavoro", "Tasse", "Scuola", "Giustizia", "Energia"]

PLATFORMS = ["X (Twitter)", "Facebook", "Instagram", "TikTok", "Reddit"]

def generate_weekly_data(weeks=8):
    """Genera dati trend simulati per N settimane."""
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
    """Cache dei dati per 1 ora. Sostituire con chiamate API reali."""
    return generate_weekly_data(weeks=8)

def get_top_hashtags(topic, n=10):
    """Hashtag simulati per topic. Collegare a API reale."""
    prefixes = ["#", "#politica", "#italia", "#governo"]
    base = topic.lower().replace(" ", "")
    return pd.DataFrame({
        "hashtag": [f"#{base}{i}" for i in range(n)],
        "volume": sorted([random.randint(100, 5000) for _ in range(n)], reverse=True)
    })

def sentiment_label(row):
    """Etichetta sentiment dominante."""
    scores = {"Positivo": row["sentiment_pos"],
              "Neutro":   row["sentiment_neu"],
              "Negativo": row["sentiment_neg"]}
    return max(scores, key=scores.get)

# ============================================================
# SEZIONE 3 - SIDEBAR
# ============================================================

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/320px-Flag_of_Italy.svg.png", width=100)
st.sidebar.title("⚙️ Impostazioni")

selected_platforms = st.sidebar.multiselect(
    "Piattaforme",
    options=PLATFORMS,
    default=PLATFORMS
)

selected_topics = st.sidebar.multiselect(
    "Topic politici",
    options=POLITICAL_TOPICS,
    default=POLITICAL_TOPICS[:5]
)

n_weeks = st.sidebar.slider("Numero di settimane", min_value=2, max_value=8, value=6)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Stato Connessioni")
st.sidebar.markdown("🔴 X/Twitter: _non connesso_  \n🔴 Reddit: _non connesso_  \n🔴 Facebook: _non connesso_")
st.sidebar.markdown("_Aggiungi le API KEY in `.env` per attivare i dati reali._")

# ============================================================
# SEZIONE 4 - HEADER
# ============================================================

st.title("📡 Political Trends Monitor")
st.markdown("**Dashboard settimanale dei trend sui social network** — Uso editoriale per trasmissioni politiche")
st.markdown(f"_Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}_")

# ============================================================
# SEZIONE 5 - KPI CARDS
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
# SEZIONE 6 - TREND SETTIMANALI
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
# SEZIONE 7 - HEATMAP
# ============================================================

st.subheader("🌡️ Heatmap Intensità Topic × Piattaforma")
heatmap_df = df_latest.groupby(["topic", "platform"])["volume"].sum().reset_index()
heatmap_pivot = heatmap_df.pivot(index="topic", columns="platform", values="volume").fillna(0)
fig_heat = px.imshow(
    heatmap_pivot,
    color_continuous_scale="Blues",
    labels=dict(color="Volume"),
    title="Intensità discussione per topic e piattaforma (settimana corrente)"
)
st.plotly_chart(fig_heat, use_container_width=True)

# ============================================================
# SEZIONE 8 - SENTIMENT ANALYSIS
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
# SEZIONE 9 - HASHTAG TRENDING
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
# SEZIONE 10 - SCHEDA EDITORIALE (per uso in trasmissione)
# ============================================================

st.subheader("📋 Scheda Editoriale Settimanale")
st.markdown("_Pronta per uso in regia o briefing giornalistico_")

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
# SEZIONE 11 - EXPORT
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
st.caption("Political Trends Monitor v1.0 | Generato con Perplexity AI | Dati simulati — collegare API reali per produzione")
