
# ============================================================
#  POLITICAL TRENDS MONITOR - app.py (v4 - Facebook + Twitter)
#  Mostra hashtag e argomenti specifici in tempo reale
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
# TEMI FISSI
# ============================================================

TEMI_TRASMISSIONE = {
    "Sicurezza":               ["sicurezza", "decreto sicurezza", "criminalità", "polizia"],
    "Sanità":                  ["sanità", "ospedali", "SSN", "liste attesa", "medici"],
    "Ambiente":                ["ambiente", "clima", "transizione energetica", "inquinamento"],
    "Guerre":                  ["Ucraina", "Iran", "guerra", "NATO", "conflitto", "pace"],
    "Autonomia Differenziata": ["autonomia differenziata", "Calderoli", "regioni", "autonomia"],
    "Lavoro":                  ["lavoro", "salario minimo", "disoccupazione", "sindacati"],
}

TEMA_COLORS = {
    "Sicurezza": "#e74c3c",
    "Sanità": "#3498db",
    "Ambiente": "#2ecc71",
    "Guerre": "#e67e22",
    "Autonomia Differenziata": "#9b59b6",
    "Lavoro": "#1abc9c",
}

PLATFORMS = ["Facebook", "X (Twitter)", "Instagram", "TikTok", "Reddit"]

# ============================================================
# CONNETTORE X/TWITTER
# ============================================================

def get_twitter_trending_italy(bearer_token):
    """Ottieni trending topics in Italia (WOEID 23424853)."""
    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = "https://api.twitter.com/1.1/trends/place.json?id=23424853"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            trends = r.json()[0]["trends"]
            return pd.DataFrame([{
                "Hashtag/Trend": t["name"],
                "Volume tweet": t.get("tweet_volume") or 0,
                "URL": t.get("url", "")
            } for t in trends]).sort_values("Volume tweet", ascending=False)
        return None
    except Exception:
        return None

def get_twitter_posts_by_topic(bearer_token, query, max_results=10):
    """Cerca tweet recenti per keyword."""
    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": f"{query} lang:it -is:retweet",
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,text"
        }
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            tweets = r.json().get("data", [])
            return pd.DataFrame([{
                "Testo": t["text"][:180] + "..." if len(t["text"]) > 180 else t["text"],
                "Like": t.get("public_metrics", {}).get("like_count", 0),
                "Retweet": t.get("public_metrics", {}).get("retweet_count", 0),
                "Data": t.get("created_at", "")[:10]
            } for t in tweets])
        return None
    except Exception:
        return None

# ============================================================
# CONNETTORE FACEBOOK
# ============================================================

def get_facebook_posts_by_topic(access_token, keyword):
    """Cerca post Facebook pubblici per keyword."""
    try:
        pages = ["LaRepubblica", "Corriere", "ilfattoquotidiano", "TgLa7"]
        results = []
        for page in pages:
            url = f"https://graph.facebook.com/v19.0/{page}/posts"
            params = {
                "access_token": access_token,
                "fields": "message,reactions.summary(true),shares,created_time",
                "limit": 25
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                for post in r.json().get("data", []):
                    msg = post.get("message", "")
                    if keyword.lower() in msg.lower():
                        results.append({
                            "Fonte": page,
                            "Testo": msg[:180] + "..." if len(msg) > 180 else msg,
                            "Reazioni": post.get("reactions", {}).get("summary", {}).get("total_count", 0),
                            "Condivisioni": post.get("shares", {}).get("count", 0),
                            "Data": post.get("created_time", "")[:10],
                        })
        return pd.DataFrame(results).sort_values("Reazioni", ascending=False) if results else None
    except Exception:
        return None

# ============================================================
# DATI SIMULATI
# ============================================================

@st.cache_data(ttl=3600)
def generate_weekly_data(weeks=8):
    rows = []
    for i in range(weeks):
        for tema in TEMI_TRASMISSIONE:
            for platform in PLATFORMS:
                volume = random.randint(80, 600) + i * random.randint(5, 25)
                sp = random.uniform(0.10, 0.40)
                sn = random.uniform(0.15, 0.45)
                rows.append({
                    "week": f"Sett {i+1}",
                    "tema": tema, "platform": platform,
                    "volume": volume,
                    "sentiment_pos": round(sp, 2),
                    "sentiment_neg": round(sn, 2),
                    "sentiment_neu": round(1 - sp - sn, 2),
                })
    return pd.DataFrame(rows)

def get_trending_emergenti():
    items = [
        ("Riforma Pensioni", random.randint(200,800), "🔥 Virale"),
        ("Decreto Flussi", random.randint(100,500), "📈 In crescita"),
        ("Manovra Finanziaria", random.randint(300,900), "🔥 Virale"),
        ("Elezioni Regionali", random.randint(150,600), "📈 In crescita"),
        ("Bonus Edilizio", random.randint(80,400), "📈 Nuovo"),
    ]
    return pd.DataFrame(items, columns=["Tema Emergente", "Volume", "Stato"])

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Impostazioni")
selected_temi = st.sidebar.multiselect(
    "Temi trasmissione",
    options=list(TEMI_TRASMISSIONE.keys()),
    default=list(TEMI_TRASMISSIONE.keys())
)
selected_platforms = st.sidebar.multiselect(
    "Piattaforme", options=PLATFORMS, default=PLATFORMS
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Stato Connessioni")
meta_token = st.secrets.get("META_ACCESS_TOKEN", None)
twitter_token = st.secrets.get("TWITTER_BEARER_TOKEN", None)
st.sidebar.markdown("🟢 **Facebook: connesso**" if meta_token else "🔴 Facebook: non connesso")
st.sidebar.markdown("🟢 **X/Twitter: connesso**" if twitter_token else "🔴 X/Twitter: non connesso")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏷️ Keyword monitorate")
for tema in selected_temi:
    kw = ", ".join(TEMI_TRASMISSIONE[tema][:3])
    st.sidebar.markdown(f"**{tema}**: _{kw}_")

# ============================================================
# HEADER + KPI
# ============================================================

st.title("📡 Political Trends Monitor")
st.markdown(f"**Dashboard settimanale — Temi personalizzati** | _Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}_")

df = generate_weekly_data()
df_f = df[df["tema"].isin(selected_temi) & df["platform"].isin(selected_platforms)]
df_latest = df_f[df_f["week"] == df_f["week"].iloc[-1]]
total_vol = int(df_latest["volume"].sum())
top_tema = df_latest.groupby("tema")["volume"].sum().idxmax()
top_platform = df_latest.groupby("platform")["volume"].sum().idxmax()
tema_neg = df_latest.groupby("tema")["sentiment_neg"].mean().idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("💬 Volume totale", f"{total_vol:,}")
c2.metric("🔥 Tema più discusso", top_tema)
c3.metric("📱 Piattaforma top", top_platform)
c4.metric("⚠️ Tema più controverso", tema_neg)

st.markdown("---")

# ============================================================
# SEZIONE PRINCIPALE: ARGOMENTI SPECIFICI PER TEMA
# ============================================================

st.subheader("🔍 Di cosa si parla — Contenuti specifici per tema")
st.markdown("_Seleziona un tema per vedere i post reali, gli hashtag e gli argomenti più discussi_")

tema_selezionato = st.selectbox(
    "Scegli il tema da analizzare:",
    options=selected_temi,
    format_func=lambda x: f"{'🔴' if x=='Sicurezza' else '🔵' if x=='Sanità' else '🟢' if x=='Ambiente' else '🟠' if x=='Guerre' else '🟣' if x=='Autonomia Differenziata' else '🩵'} {x}"
)

keyword_principale = TEMI_TRASMISSIONE[tema_selezionato][0]

col_tw, col_fb = st.columns(2)

# --- TWITTER ---
with col_tw:
    st.markdown("### 🐦 X/Twitter")
    if twitter_token:
        with st.spinner(f"Carico tweet su '{keyword_principale}'..."):
            tw_df = get_twitter_posts_by_topic(twitter_token, keyword_principale)
        if tw_df is not None and not tw_df.empty:
            st.dataframe(tw_df, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun tweet trovato per questo tema al momento.")

        st.markdown("#### 🇮🇹 Trending in Italia adesso")
        with st.spinner("Carico trending topics Italia..."):
            trending_df = get_twitter_trending_italy(twitter_token)
        if trending_df is not None and not trending_df.empty:
            st.dataframe(
                trending_df[["Hashtag/Trend", "Volume tweet"]].head(20),
                use_container_width=True, hide_index=True
            )
    else:
        st.warning("Token X/Twitter non configurato in Secrets.")

# --- FACEBOOK ---
with col_fb:
    st.markdown("### 📘 Facebook")
    if meta_token:
        with st.spinner(f"Carico post su '{keyword_principale}'..."):
            fb_df = get_facebook_posts_by_topic(meta_token, keyword_principale)
        if fb_df is not None and not fb_df.empty:
            st.dataframe(fb_df[["Fonte","Testo","Reazioni","Condivisioni","Data"]],
                         use_container_width=True, hide_index=True)
            fig_fb = px.bar(
                fb_df.head(8), x="Reazioni", y="Fonte", orientation="h",
                color="Condivisioni", color_continuous_scale="Blues",
                title=f"Post più condivisi su '{tema_selezionato}'"
            )
            st.plotly_chart(fig_fb, use_container_width=True)
        else:
            st.info("Nessun post trovato per questo tema al momento.")
    else:
        st.warning("Token Facebook non configurato in Secrets.")

st.markdown("---")

# ============================================================
# TREND SETTIMANALI
# ============================================================

st.subheader("📈 Trend Settimanali")
trend_df = df_f.groupby(["week","tema"])["volume"].sum().reset_index()
fig_trend = px.line(trend_df, x="week", y="volume", color="tema",
    markers=True, color_discrete_map=TEMA_COLORS,
    labels={"week":"Settimana","volume":"Volume","tema":"Tema"},
    title="Evoluzione settimanale dei temi")
fig_trend.update_layout(legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig_trend, use_container_width=True)

# ============================================================
# SENTIMENT + HEATMAP
# ============================================================

col_s, col_h = st.columns(2)
with col_s:
    st.subheader("💭 Sentiment per Tema")
    sent_df = df_latest.groupby("tema")[["sentiment_pos","sentiment_neu","sentiment_neg"]].mean().reset_index()
    sent_m = sent_df.melt(id_vars="tema", var_name="S", value_name="Pct")
    sent_m["S"] = sent_m["S"].map({"sentiment_pos":"Positivo","sentiment_neu":"Neutro","sentiment_neg":"Negativo"})
    fig_s = px.bar(sent_m, x="tema", y="Pct", color="S", barmode="stack",
        color_discrete_map={"Positivo":"#2ecc71","Neutro":"#95a5a6","Negativo":"#e74c3c"},
        labels={"tema":"Tema","Pct":"% Sentiment","S":"Sentiment"})
    st.plotly_chart(fig_s, use_container_width=True)

with col_h:
    st.subheader("🌡️ Dove se ne parla di più")
    hm = df_latest.groupby(["tema","platform"])["volume"].sum().reset_index()
    hm_p = hm.pivot(index="tema", columns="platform", values="volume").fillna(0)
    fig_h = px.imshow(hm_p, color_continuous_scale="Blues", labels=dict(color="Volume"))
    st.plotly_chart(fig_h, use_container_width=True)

# ============================================================
# TEMI EMERGENTI
# ============================================================

st.markdown("---")
st.subheader("🚨 Temi Emergenti questa settimana")
em_df = get_trending_emergenti()
col_em1, col_em2 = st.columns([2,1])
with col_em1:
    fig_em = px.bar(em_df, x="Volume", y="Tema Emergente", orientation="h",
        color="Volume", color_continuous_scale="Oranges",
        title="Argomenti in forte crescita (non ancora in lista)")
    fig_em.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_em, use_container_width=True)
with col_em2:
    st.dataframe(em_df, use_container_width=True, hide_index=True)

# ============================================================
# SCHEDA EDITORIALE
# ============================================================

st.markdown("---")
st.subheader("📋 Scheda Editoriale — Pronti per la Regia")
ed = []
for tema in selected_temi:
    t_df = df_latest[df_latest["tema"] == tema]
    vol = int(t_df["volume"].sum())
    sp = round(t_df["sentiment_pos"].mean()*100, 1)
    sn = round(t_df["sentiment_neg"].mean()*100, 1)
    kw = " · ".join([f"#{k.replace(' ','')}" for k in TEMI_TRASMISSIONE[tema][:3]])
    ed.append({
        "Tema": tema,
        "Volume": vol,
        "Trend": "📈" if vol > total_vol/len(selected_temi) else "📉",
        "😊 Pos": f"{sp}%",
        "😠 Neg": f"{sn}%",
        "Keyword chiave": kw,
        "Regia": "✅ In onda" if vol > total_vol/len(selected_temi)*1.2 else "⬜ Valutare",
    })

ed_df = pd.DataFrame(ed).sort_values("Volume", ascending=False)
st.dataframe(ed_df, use_container_width=True, hide_index=True)

st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    st.download_button("📥 Scarica Scheda Editoriale (CSV)",
        ed_df.to_csv(index=False).encode("utf-8"),
        f"scheda_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
with col_b:
    st.download_button("📥 Scarica Tutti i Dati (CSV)",
        df_f.to_csv(index=False).encode("utf-8"),
        f"trends_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

st.caption("Political Trends Monitor v4.0 | Facebook + X/Twitter | Sicurezza · Sanità · Ambiente · Guerre · Autonomia · Lavoro")
