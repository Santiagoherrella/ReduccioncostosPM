import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# URL RAW de tu CSV en GitHub
URL_CSV = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/data/actividades.csv"

@st.cache_data(ttl=3600)
def cargar_datos():
    df = pd.read_csv(URL_CSV)
    if "FechaProgramada" in df.columns:
        df["FechaProgramada"] = pd.to_datetime(df["FechaProgramada"], errors="coerce")
    return df

df = cargar_datos()

st.set_page_config(page_title="Dashboard DMAIC", layout="wide")
st.title("📊 Dashboard Seguimiento Proyecto DMAIC")

# ===================== KPIs Generales =====================
total = len(df)
completadas = len(df[df["Estado"].str.lower() == "completado"])
avance_global = round((completadas / total) * 100, 2)

# Retrasadas
hoy = datetime.today()
if "FechaProgramada" in df.columns:
    retrasadas = df[(df["Estado"].str.lower() != "completado") & (df["FechaProgramada"] < hoy)]
else:
    retrasadas = pd.DataFrame()

col1, col2, col3 = st.columns(3)
col1.metric("Avance Global", f"{avance_global}%", delta=None)
col2.metric("Tareas Completadas", completadas)
col3.metric("Tareas Retrasadas", len(retrasadas))

st.divider()

# ===================== Avance por Fase =====================
avance_fase = df.groupby("Fase")["Estado"].apply(
    lambda x: (x.str.lower() == "completado").sum() / len(x) * 100
).reset_index(name="Avance (%)")

fig_fase = px.bar(avance_fase, x="Fase", y="Avance (%)", title="Avance por Fase DMAIC",
                  text="Avance (%)", range_y=[0, 100])
st.plotly_chart(fig_fase, use_container_width=True)

# ===================== Avance por Responsable =====================
avance_resp = df.groupby("Responsable")["Estado"].apply(
    lambda x: (x.str.lower() == "completado").sum() / len(x) * 100
).reset_index(name="Avance (%)")

fig_resp = px.bar(avance_resp, x="Responsable", y="Avance (%)", title="Avance por Responsable",
                  text="Avance (%)", range_y=[0, 100])
st.plotly_chart(fig_resp, use_container_width=True)

# ===================== Tabla filtrable =====================
fase_sel = st.selectbox("Filtrar por Fase", ["Todas"] + list(df["Fase"].unique()))
estado_sel = st.selectbox("Filtrar por Estado", ["Todos"] + list(df["Estado"].unique()))

df_filtrado = df.copy()
if fase_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Fase"] == fase_sel]
if estado_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == estado_sel]

st.dataframe(df_filtrado)
