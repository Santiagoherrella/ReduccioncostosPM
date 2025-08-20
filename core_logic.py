import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Orden de fases para mantener consistencia
FASE_ORDEN = ["Definición", "Medición", "Analizar", "Implementar", "Controlar"]

# Vocabularios válidos según tu definición
ESTADOS_VALIDOS = {"Sin programar", "En proceso", "Finalizado"}
CRONOGRAMAS_VALIDOS = {"A tiempo", "Con retraso"}

# =============================================================================
# FUNCIONES CORE LOGIC (CARGA, LIMPIEZA, TRANSFORMACIÓN)
# =============================================================================

def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia, normaliza y transforma el DataFrame raw para análisis.
    """
    print("DEBUG: Iniciando preparación de datos")
    print(f"DEBUG: Columnas originales: {df.columns.tolist()}")
    print(f"DEBUG: Shape original: {df.shape}")
    
    # 1. Filtrar columnas relevantes (usar nombres exactos del CSV)
    cols_relevantes = [
        "Fase", "Tipo", "Actividad", "Responsable",
        "Estado", "Porcetaje", "Cronograma", "Correo responsable"  # ← "Porcetaje" tal como está en el CSV
    ]
    df = df[[c for c in cols_relevantes if c in df.columns]].copy()
    print(f"DEBUG: Columnas mantenidas: {df.columns.tolist()}")
    
    # 2. Renombrar columna mal escrita
    if "Porcetaje" in df.columns:
        df = df.rename(columns={"Porcetaje": "Porcentaje"})
        print("DEBUG: Renombrada 'Porcetaje' -> 'Porcentaje'")
    
    # 3. Normalizar texto básico (quitar espacios extra)
    for c in ["Fase", "Tipo", "Actividad", "Responsable", "Estado", "Cronograma", "Correo responsable"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    
    print(f"DEBUG: Estados únicos después de limpiar: {df['Estado'].unique()}")
    
    # 4. Estandarizar fases (sin tilde -> con tilde)
    if "Fase" in df.columns:
        mapa_fase = {
            "Definicion": "Definición",    # tu CSV no tiene tildes
            "Medicion": "Medición",        # tu CSV no tiene tildes
            "Analizar": "Analizar",
            "Implementar": "Implementar",
            "Controlar": "Controlar"
        }
        df["Fase"] = df["Fase"].map(lambda x: mapa_fase.get(x, x))
        df["Fase"] = pd.Categorical(df["Fase"], categories=FASE_ORDEN, ordered=True)
        print(f"DEBUG: Fases después de normalizar: {df['Fase'].unique()}")
    
    # 5. Convertir porcentaje
    if "Porcentaje" in df.columns:
        ser_porcentaje = df["Porcentaje"].astype(str).str.replace(",", ".", regex=False)
        df["Porcentaje"] = pd.to_numeric(ser_porcentaje, errors="coerce").fillna(0.0).clip(0, 1)
        print(f"DEBUG: Rango de porcentajes: {df['Porcentaje'].min()} - {df['Porcentaje'].max()}")
    
    # 6. Normalizar Estados (tu CSV ya tiene los nombres correctos)
    if "Estado" in df.columns:
        # Tu CSV ya tiene "En proceso", "Finalizado", "Sin programar" - no necesita mapeo
        estados_encontrados = df['Estado'].unique()
        print(f"DEBUG: Estados encontrados: {estados_encontrados}")
    
    # 7. Crear EstadoOp (usar directamente los estados de tu CSV)
    def clasificar_estado_op(estado, porcentaje):
        if estado == "Finalizado":
            return "Finalizado"
        elif estado == "En proceso":
            return "En proceso"
        elif estado == "Sin programar":
            # Si tiene porcentaje > 0, considerarlo en proceso
            if isinstance(porcentaje, (int, float)) and 0 < porcentaje < 1:
                return "En proceso"
            return "No programado"
        else:
            # Estados no reconocidos
            print(f"DEBUG: Estado no reconocido: '{estado}'")
            if isinstance(porcentaje, (int, float)) and 0 < porcentaje < 1:
                return "En proceso"
            return "No programado"
    
    df["EstadoOp"] = df.apply(
        lambda fila: clasificar_estado_op(fila.get("Estado"), fila.get("Porcentaje", 0)), 
        axis=1
    )
    
    print(f"DEBUG: Estados operativos únicos: {df['EstadoOp'].unique()}")
    print(f"DEBUG: Conteo por EstadoOp: {df['EstadoOp'].value_counts().to_dict()}")
    
    # 8. Crear etiqueta de finalización
    df["Finalización"] = None
    mask_finalizadas = df["EstadoOp"] == "Finalizado"
    df.loc[mask_finalizadas, "Finalización"] = df.loc[mask_finalizadas, "Cronograma"].fillna("A tiempo")
    
    print(f"DEBUG: Preparación completada. Shape final: {df.shape}")
    return df

def resumen_por_fase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resumen por fase usando "En proceso"
    """
    print("DEBUG: Generando resumen por fase")
    
    total = df.groupby("Fase").size().rename("Total")
    finalizadas = df[df["EstadoOp"] == "Finalizado"].groupby("Fase").size().rename("Finalizadas")
    en_proceso = df[df["EstadoOp"] == "En proceso"].groupby("Fase").size().rename("En proceso")
    
    resumen = (
        total.to_frame()
        .join(finalizadas, how="left")
        .join(en_proceso, how="left")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    
    resumen["No programadas"] = (
        resumen["Total"] - resumen["Finalizadas"] - resumen["En proceso"]
    ).clip(lower=0)
    
    resumen = resumen.sort_values("Fase").reset_index(drop=True)
    print(f"DEBUG: Resumen por fase generado:\n{resumen}")
    return resumen

def resumen_por_responsable(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resumen por responsable usando "En proceso"
    """
    print("DEBUG: Generando resumen por responsable")
    
    total = df.groupby("Responsable").size().rename("Total")
    finalizadas = df[df["EstadoOp"] == "Finalizado"].groupby("Responsable").size().rename("Finalizadas")
    en_proceso = df[df["EstadoOp"] == "En proceso"].groupby("Responsable").size().rename("En proceso")
    
    resumen = (
        total.to_frame()
        .join(finalizadas, how="left")
        .join(en_proceso, how="left")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    
    resumen["No programadas"] = (
        resumen["Total"] - resumen["Finalizadas"] - resumen["En proceso"]
    ).clip(lower=0)
    
    resumen = resumen.sort_values(["Total", "Responsable"], ascending=[False, True])
    return resumen

def detalle_finalizacion_por_fase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuenta actividades finalizadas "A tiempo" vs "Con retraso" por fase.
    """
    print("DEBUG: Generando detalle de finalización por fase")
    
    finalizadas = df[df["EstadoOp"] == "Finalizado"]
    
    if len(finalizadas) == 0:
        return pd.DataFrame({
            "Fase": [],
            "A tiempo": [],
            "Con retraso": []
        })
    
    tabla = finalizadas.pivot_table(
        index="Fase",
        columns="Finalización",
        values="Actividad",
        aggfunc="count",
        fill_value=0
    )
    
    for col in ["A tiempo", "Con retraso"]:
        if col not in tabla.columns:
            tabla[col] = 0
    
    tabla = tabla[["A tiempo", "Con retraso"]].reset_index()
    return tabla.sort_values("Fase")

def indicadores_globales(df: pd.DataFrame) -> dict:
    """
    KPIs globales usando "En proceso"
    """
    print("DEBUG: Calculando indicadores globales")
    
    n_total = len(df)
    n_finalizadas = int((df["EstadoOp"] == "Finalizado").sum())
    n_en_proceso = int((df["EstadoOp"] == "En proceso").sum())
    n_no_programadas = int((df["EstadoOp"] == "No programado").sum())
    
    # Tu fórmula de indicador: (Suma(Porcentaje) / (N-1)) * 100
    indicador = None
    if "Porcentaje" in df.columns and n_total > 1:
        suma_porcentaje = float(df["Porcentaje"].sum())
        indicador = (suma_porcentaje / (n_total - 1)) * 100
    
    # Desglose de finalización
    finalizadas_a_tiempo = int(
        ((df["EstadoOp"] == "Finalizado") & (df["Finalización"] == "A tiempo")).sum()
    )
    finalizadas_con_retraso = int(
        ((df["EstadoOp"] == "Finalizado") & (df["Finalización"] == "Con retraso")).sum()
    )
    
    pct_a_tiempo = None
    if n_finalizadas > 0:
        pct_a_tiempo = (finalizadas_a_tiempo / n_finalizadas) * 100
    
    kpis = {
        "total": n_total,
        "finalizadas": n_finalizadas,
        "en_proceso": n_en_proceso,
        "no_programadas": n_no_programadas,
        "indicador": indicador,
        "finalizadas_a_tiempo": finalizadas_a_tiempo,
        "finalizadas_con_retraso": finalizadas_con_retraso,
        "pct_finalizadas_a_tiempo": pct_a_tiempo,
    }
    
    print(f"DEBUG: KPIs calculados: {kpis}")
    return kpis

# =============================================================================
# FUNCIONES DE VISUALIZACIÓN
# =============================================================================

def crear_grafica_avance_fase(resumen_fase: pd.DataFrame):
    """
    Gráfica con "En proceso"
    """
    print("DEBUG: Creando gráfica de avance por fase")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=resumen_fase["Fase"],
        y=resumen_fase["Total"],
        name="Total actividades",
        marker_color="orange",
        opacity=0.5
    ))
    
    fig.add_trace(go.Bar(
        x=resumen_fase["Fase"],
        y=resumen_fase["Finalizadas"],
        name="Finalizadas",
        marker_color="green",
        opacity=0.9
    ))
    
    fig.add_trace(go.Bar(
        x=resumen_fase["Fase"],
        y=resumen_fase["En proceso"],
        name="En proceso",
        marker_color="royalblue",
        opacity=0.9
    ))
    
    fig.update_layout(
        barmode="overlay",
        title="Avance por Fase: Total vs Finalizadas vs En Proceso",
        xaxis_title="Fase",
        yaxis_title="Número de Actividades",
        legend_title="Estado",
        bargap=0.2,
        height=500
    )
    
    return fig

def crear_grafica_composicion_fase(resumen_fase: pd.DataFrame):
    """
    Gráfica de composición con "En proceso"
    """
    print("DEBUG: Creando gráfica de composición por fase")
    
    resumen_pct = resumen_fase.copy()
    denominador = resumen_pct["Total"].replace(0, 1)
    
    resumen_pct["Finalizadas %"] = (resumen_pct["Finalizadas"] / denominador) * 100
    resumen_pct["En proceso %"] = (resumen_pct["En proceso"] / denominador) * 100
    resumen_pct["No programadas %"] = (resumen_pct["No programadas"] / denominador) * 100
    
    fig = px.bar(
        resumen_pct,
        x="Fase",
        y=["Finalizadas %", "En proceso %", "No programadas %"],
        title="Composición por Fase (%)",
        labels={"value": "Porcentaje", "variable": "Estado"},
        color_discrete_map={
            "Finalizadas %": "green",
            "En proceso %": "royalblue",
            "No programadas %": "lightcoral"
        }
    )
    
    fig.update_layout(
        barmode="stack",
        yaxis_title="Porcentaje (%)",
        legend_title="Estado",
        height=500
    )
    
    return fig

def crear_grafica_finalizacion_calidad(detalle_fin: pd.DataFrame):
    """
    Crea gráfica de finalizadas A tiempo vs Con retraso por fase.
    """
    if len(detalle_fin) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay actividades finalizadas aún",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title="Calidad de Finalización por Fase")
        return fig
    
    print("DEBUG: Creando gráfica de calidad de finalización")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=detalle_fin["Fase"],
        y=detalle_fin["A tiempo"],
        name="A tiempo",
        marker_color="darkgreen"
    ))
    
    fig.add_trace(go.Bar(
        x=detalle_fin["Fase"],
        y=detalle_fin["Con retraso"],
        name="Con retraso",
        marker_color="darkred"
    ))
    
    fig.update_layout(
        barmode="stack",
        title="Calidad de Finalización por Fase",
        xaxis_title="Fase",
        yaxis_title="Actividades Finalizadas",
        legend_title="Cronograma",
        height=400
    )
    
    return fig
