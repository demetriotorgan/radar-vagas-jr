import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="Radar Vagas - Demétrio", layout="wide", page_icon="🎯")
st.title("🎯 Radar de Vagas Jr - Maringá / Londrina / Remoto")
st.caption("Banco acumulado pelo GitHub Actions + DuckDB + Score TF-IDF")

@st.cache_data(ttl=600)
def load_data():
    con = duckdb.connect("vagas.duckdb", read_only=True)
    try:
        df = con.execute("SELECT * FROM vagas ORDER BY score DESC").df()
    except:
        df = con.execute("SELECT * FROM vagas").df()
    con.close()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"vagas.duckdb não encontrado ainda. Roda seu main.py primeiro! Erro: {e}")
    st.stop()

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total acumulado", len(df))
c2.metric("Média Score", f"{df['score'].mean():.1f}%" if len(df)>0 else "0%")
c3.metric("Score >= 50%", len(df[df['score']>=50]))
c4.metric("Última coleta", str(df['data_coleta'].max())[:16] if 'data_coleta' in df.columns else "hoje")

# Filtros
st.sidebar.header("🔍 Filtros")
cidades = st.sidebar.multiselect("Cidade", sorted(df['cidade'].dropna().unique()), default=sorted(df['cidade'].dropna().unique()))
score_min = st.sidebar.slider("Score mínimo", 0, 100, 35)
busca = st.sidebar.text_input("Buscar empresa/título")

df_f = df[df['cidade'].isin(cidades)] if cidades else df
df_f = df_f[df_f['score'] >= score_min]

if busca:
    col_busca = 'empresa_norm' if 'empresa_norm' in df_f.columns else 'empresa'
    df_f = df_f[df_f[col_busca].astype(str).str.contains(busca, case=False, na=False) | df_f['titulo'].astype(str).str.contains(busca, case=False, na=False)]

# Tabela
st.subheader(f"Vagas encontradas: {len(df_f)}")
cols_show = [c for c in ['titulo','empresa_norm','empresa','cidade','score','link'] if c in df_f.columns]
st.dataframe(df_f[cols_show], use_container_width=True, column_config={"link": st.column_config.LinkColumn("Link")})

st.divider()
st.subheader("📊 Distribuição por cidade (geral)")
# Usa o total, não o filtrado, pra não virar retangulão
city_counts = df['cidade'].value_counts()
st.bar_chart(city_counts)

if len(df_f) > 0 and 'empresa_norm' in df_f.columns:
    st.subheader("🏢 Top empresas no filtro atual")
    st.bar_chart(df_f['empresa_norm'].value_counts().head(8))
