
# ============================================================
#  POLITICAL TRENDS MONITOR - app.py (v5 - NewsAPI)
#  Notizie reali da media italiani per ogni tema
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
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
# TEMI E KEYWORD
# ============================================================

TEMI_TRASMISSIONE = {
    "Sicurezza":               ["sicurezza", "decreto sicurezza", "criminalità", "polizia"],
    "Sanità":                  ["sanità", "ospedali", "SSN", "liste attesa"],
    "Ambiente":                ["ambiente", "clima", "transizione energetica", "inquinamento"],
    "Guerre":                  ["Ucraina", "Iran", "guerra", "NATO", "pace"],
    "Autonomia Differenziata": ["autonomia differenziata", "Calderoli", "regioni"],
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
# CONNETTORE NEWSAPI
# ============================================================

def get_news_by_topic(api_key, keyword, language="it", page_size=10):
    """Recupera notizie reali italiane per keyword."""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": keyword,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": api_key,
            "domains": "repubblica.it,corriere.it,ansa.it,tgla7.it,ilmessaggero.it,lastampa.it,ilsole24ore.com"
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            return pd.DataFrame([{
                "Fonte": a.get("source", {}).get("name", ""),
                "Titolo": a.get("title", ""),
                "Descrizione": a.get("description", "")[:200] + "..." if a.get("description") and len(a.get("description","")) > 200 else a.get("description",""),
                "Link": a.get("url", ""),
                "Data": a.get("publishedAt", "")[:10],
            } for a in articles if a.get("title")])
        return None
    except Exception:
        return None

def get_top_headlines_italy(api_key):
    """Titoli di testa in Italia adesso."""
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": "it",
            "category": "politics",
            "pageSize": 15,
            "apiKey": api_key
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            return pd.DataFrame([{
                "Fonte": a.get("source", {}).get("name", ""),
                "Titolo": a.get("title", ""),
                "Data": a.get("publishedAt", "")[:10],
                "Link": a.get("url", ""),
            } for a in articles if a.get("title")])
        return None
    except Exception:
        return None

def classify_article_by_tema(title, description):
    """Classifica un articolo nel tema corretto."""
    text = (title + " " + (description or "")).lower()
    for tema, keywords in TEMI_TRASMISSIONE.items():
        if any(k.lower() in text for k in keywords):
            return tema
    return "Altro"

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

def get_trending_emergenti(api_key=None):
    """Se NewsAPI disponibile, usa titoli reali; altrimenti simulati."""
    if api_key:
        df = get_news_by_topic(api_key, "politica italia", page_size=5)
        if df is not None and not df.empty:
            df = df[["Titolo","Fonte","Data"]].head(5)
            df.columns = ["Tema Emergente","Fonte","Data"]
            return df
    items = [
        ("Riforma Pensioni", random.randint(200,800), "🔥 Virale"),
        ("Decreto Flussi", random.randint(100,500), "📈 In crescita"),
        ("Manovra Finanziaria", random.randint(300,900), "🔥 Virale"),
        ("Elezioni Regionali", random.randint(150,600), "📈 In crescita"),
        ("Bonus Edilizio", random.randint(80,400), "📈 Nuovo"),
    ]
    return pd.DataFrame(items, columns=["Tema Emergente","Volume","Stato"])

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
news_api_key = st.secrets.get("NEWS_API_KEY", None)
meta_token = st.secrets.get("META_ACCESS_TOKEN", None)
twitter_token = st.secrets.get("TWITTER_BEARER_TOKEN", None)

st.sidebar.markdown("🟢 **NewsAPI: connesso**" if news_api_key else "🔴 NewsAPI: non connesso")
st.sidebar.markdown("🟡 Facebook: limitato" if meta_token else "🔴 Facebook: non connesso")
st.sidebar.markdown("🟡 X/Twitter: limitato" if twitter_token else "🔴 X/Twitter: non connesso")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏷️ Keyword monitorate")
for tema in selected_temi:
    kw = " · ".join(TEMI_TRASMISSIONE[tema][:2])
    st.sidebar.markdown(f"**{tema}**: _{kw}_")

# ============================================================
# HEADER + KPI
# ============================================================

st.title("📡 Political Trends Monitor")
st.markdown(f"**Dashboard settimanale — Notizie reali dai media italiani** | _{datetime.now().strftime('%d/%m/%Y %H:%M')}_")

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
# BREAKING NEWS — Titoli politici in Italia adesso
# ============================================================

if news_api_key:
    st.subheader("🚨 Breaking News Politica — Italia adesso")
    with st.spinner("Carico le ultime notizie..."):
        headlines_df = get_top_headlines_italy(news_api_key)
    if headlines_df is not None and not headlines_df.empty:
        for _, row in headlines_df.iterrows():
            st.markdown(f"**{row['Fonte']}** · {row['Data']}  
📰 [{row['Titolo']}]({row['Link']})")
    else:
        st.info("Nessuna notizia disponibile al momento.")
    st.markdown("---")

# ============================================================
# DI COSA SI PARLA — Per tema specifico
# ============================================================

st.subheader("🔍 Di cosa si parla — Notizie specifiche per tema")
tema_selezionato = st.selectbox(
    "Scegli il tema:",
    options=selected_temi,
    format_func=lambda x: {
        "Sicurezza":"🔴 Sicurezza",
        "Sanità":"🔵 Sanità",
        "Ambiente":"🟢 Ambiente",
        "Guerre":"🟠 Guerre",
        "Autonomia Differenziata":"🟣 Autonomia Differenziata",
        "Lavoro":"🩵 Lavoro"
    }.get(x, x)
)

keyword_principale = TEMI_TRASMISSIONE[tema_selezionato][0]

if news_api_key:
    with st.spinner(f"Cerco notizie su '{tema_selezionato}'..."):
        news_df = get_news_by_topic(news_api_key, keyword_principale)

    if news_df is not None and not news_df.empty:
        st.success(f"✅ {len(news_df)} notizie trovate su **{tema_selezionato}**")

        # Mostra notizie come cards
        for _, row in news_df.iterrows():
            with st.container():
                col_info, col_link = st.columns([5,1])
                with col_info:
                    st.markdown(f"**{row['Fonte']}** · _{row['Data']}_")
                    st.markdown(f"### {row['Titolo']}")
                    if row['Descrizione']:
                        st.markdown(f"{row['Descrizione']}")
                with col_link:
                    st.markdown(f"[🔗 Leggi]({row['Link']})")
                st.divider()

        # Grafico fonti
        fonti_count = news_df["Fonte"].value_counts().reset_index()
        fonti_count.columns = ["Fonte","Articoli"]
        fig_fonti = px.bar(fonti_count, x="Articoli", y="Fonte", orientation="h",
            color="Articoli", color_continuous_scale=["#cfe2f3","#1a6fa8"],
            title=f"Quante notizie per fonte — '{tema_selezionato}'")
        fig_fonti.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_fonti, use_container_width=True)
    else:
        st.info("Nessuna notizia trovata. Prova a cambiare tema.")
else:
    st.warning("⚠️ NewsAPI non configurata. Aggiungi NEWS_API_KEY in Streamlit → Settings → Secrets.")

st.markdown("---")

# ============================================================
# TUTTI I TEMI — Panoramica notizie
# ============================================================

if news_api_key:
    st.subheader("📰 Panoramica notizie per tutti i temi")
    with st.spinner("Carico notizie per tutti i temi..."):
        all_news = []
        for tema, keywords in TEMI_TRASMISSIONE.items():
            if tema in selected_temi:
                df_tema = get_news_by_topic(news_api_key, keywords[0], page_size=5)
                if df_tema is not None and not df_tema.empty:
                    df_tema["Tema"] = tema
                    all_news.append(df_tema)

    if all_news:
        all_news_df = pd.concat(all_news, ignore_index=True)
        tabs = st.tabs([f"{'🔴' if t=='Sicurezza' else '🔵' if t=='Sanità' else '🟢' if t=='Ambiente' else '🟠' if t=='Guerre' else '🟣' if t=='Autonomia Differenziata' else '🩵'} {t}" for t in selected_temi])
        for i, tema in enumerate(selected_temi):
            with tabs[i]:
                t_df = all_news_df[all_news_df["Tema"]==tema][["Fonte","Titolo","Data","Link"]]
                for _, row in t_df.iterrows():
                    st.markdown(f"**{row['Fonte']}** · _{row['Data']}_  
📰 [{row['Titolo']}]({row['Link']})")
    st.markdown("---")

# ============================================================
# TREND SETTIMANALI + SENTIMENT
# ============================================================

st.subheader("📈 Trend Settimanali")
trend_df = df_f.groupby(["week","tema"])["volume"].sum().reset_index()
fig_trend = px.line(trend_df, x="week", y="volume", color="tema",
    markers=True, color_discrete_map=TEMA_COLORS,
    labels={"week":"Settimana","volume":"Volume","tema":"Tema"},
    title="Evoluzione settimanale dei temi")
fig_trend.update_layout(legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig_trend, use_container_width=True)

col_s, col_h = st.columns(2)
with col_s:
    st.subheader("💭 Sentiment per Tema")
    sent_df = df_latest.groupby("tema")[["sentiment_pos","sentiment_neu","sentiment_neg"]].mean().reset_index()
    sent_m = sent_df.melt(id_vars="tema", var_name="S", value_name="Pct")
    sent_m["S"] = sent_m["S"].map({"sentiment_pos":"Positivo","sentiment_neu":"Neutro","sentiment_neg":"Negativo"})
    fig_s = px.bar(sent_m, x="tema", y="Pct", color="S", barmode="stack",
        color_discrete_map={"Positivo":"#2ecc71","Neutro":"#95a5a6","Negativo":"#e74c3c"},
        labels={"tema":"Tema","Pct":"%","S":"Sentiment"})
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
em_df = get_trending_emergenti(news_api_key)
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
        "Keyword": kw,
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

st.caption("Political Trends Monitor v5.0 | NewsAPI + media italiani | Sicurezza · Sanità · Ambiente · Guerre · Autonomia · Lavoro")
