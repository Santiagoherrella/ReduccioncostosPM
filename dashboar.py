# Para ejecutar: streamlit run dashboar.py
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Importar funciones del core logic
from core_logic import (
    preparar_datos,
    indicadores_globales,
    resumen_por_fase,
    resumen_por_responsable,
    detalle_finalizacion_por_fase,
    crear_grafica_avance_fase,
    crear_grafica_composicion_fase,
    crear_grafica_finalizacion_calidad
)

# URL RAW de tu CSV en GitHub
URL_CSV = "https://raw.githubusercontent.com/Santiagoherrella/ReduccioncostosPM/refs/heads/main/Actividades.csv"

@st.cache_data
def cargar_datos(url: str) -> pd.DataFrame:
    """
    Carga el CSV desde la URL de GitHub.
    Tu CSV usa separador coma (,) que es el predeterminado
    """
    try:
        df = pd.read_csv(url)  # ← SIN sep=';' porque tu CSV usa comas
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def main():
    """
    Función principal que orquesta toda la aplicación.
    """
    print("DEBUG: Iniciando aplicación Streamlit")
    
    # Configuración de página
    st.set_page_config(
        page_title="Dashboard PM - Actividades DMAIC",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Dashboard DMAIC - Gestión de Actividades PM")
    st.markdown("---")
    
    # CARGAR Y PROCESAR DATOS
    with st.spinner("🔄 Cargando y procesando datos..."):
        try:
            # 1. Cargar datos raw
            df_raw = cargar_datos(URL_CSV)
            
            if df_raw.empty:
                st.error("❌ No se pudieron cargar los datos. Verifica la URL del CSV.")
                return
            
            st.success(f"✅ Datos cargados: {len(df_raw)} filas, {len(df_raw.columns)} columnas")
            
            # 2. Preparar datos
            df_procesado = preparar_datos(df_raw)
            
            # 3. Generar agregados
            kpis = indicadores_globales(df_procesado)
            resumen_fase = resumen_por_fase(df_procesado)
            resumen_responsable = resumen_por_responsable(df_procesado)
            detalle_fin = detalle_finalizacion_por_fase(df_procesado)
            
        except Exception as e:
            st.error(f"❌ Error al procesar datos: {e}")
            st.write("Error detallado:", str(e))
            return
    
    # SECCIÓN 1: KPIS GLOBALES
    st.header("📈 Indicadores Globales del Proyecto DMAIC")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Actividades", kpis["total"])
    
    with col2:
        st.metric("✅ Finalizadas", kpis["finalizadas"])
    
    with col3:
        st.metric("🔄 En Proceso", kpis["en_proceso"])
    
    with col4:
        st.metric("⏸️ No Programadas", kpis["no_programadas"])
    
    with col5:
        if kpis["indicador"] is not None:
            st.metric("📊 Indicador Avance", f"{kpis['indicador']:.1f}%")
        else:
            st.metric("📊 Indicador Avance", "N/A")
    
    # SECCIÓN 2: CALIDAD DE FINALIZACIÓN
    if kpis["finalizadas"] > 0:
        st.header("🎯 Calidad de Finalización")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("⏰ A Tiempo", kpis["finalizadas_a_tiempo"])
        
        with col_b:
            st.metric("⚠️ Con Retraso", kpis["finalizadas_con_retraso"])
        
        with col_c:
            if kpis["pct_finalizadas_a_tiempo"] is not None:
                st.metric("% A Tiempo", f"{kpis['pct_finalizadas_a_tiempo']:.1f}%")
    
    st.markdown("---")
    
    # SECCIÓN 3: ANÁLISIS POR FASE DMAIC
    st.header("📋 Análisis por Fase DMAIC")
    
    # Tabla resumen
    st.subheader("Tabla Resumen por Fase")
    st.dataframe(resumen_fase, use_container_width=True)
    
    # Gráficas
    col_grafica1, col_grafica2 = st.columns(2)
    
    with col_grafica1:
        fig_avance = crear_grafica_avance_fase(resumen_fase)
        st.plotly_chart(fig_avance, use_container_width=True)
    
    with col_grafica2:
        fig_composicion = crear_grafica_composicion_fase(resumen_fase)
        st.plotly_chart(fig_composicion, use_container_width=True)
    
    # Gráfica de calidad (si hay finalizadas)
    if kpis["finalizadas"] > 0:
        st.subheader("Calidad de Finalización por Fase")
        fig_calidad = crear_grafica_finalizacion_calidad(detalle_fin)
        st.plotly_chart(fig_calidad, use_container_width=True)
    
    st.markdown("---")
    
    # SECCIÓN 4: ANÁLISIS POR RESPONSABLE
    st.header("👥 Análisis por Responsable")
    st.dataframe(resumen_responsable, use_container_width=True)
    
    # SECCIÓN 5: DATOS Y DEBUG
    with st.expander("🔍 Datos para Debug"):
        st.subheader("Estados Únicos en CSV")
        if "Estado" in df_procesado.columns:
            st.write("Estado (original):", df_procesado["Estado"].unique().tolist())
        st.write("EstadoOp (para dashboard):", df_procesado["EstadoOp"].unique().tolist())
        
        st.subheader("Conteos por Estado Operativo")
        conteos = df_procesado["EstadoOp"].value_counts()
        st.write(conteos)
        
        st.subheader("Muestra de Datos Procesados")
        st.dataframe(df_procesado.head(10))
        
        st.subheader("Datos Raw (primeras 5 filas)")
        st.dataframe(df_raw.head(5))

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
