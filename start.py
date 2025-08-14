# streamlit run start.py
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard DMAIC", layout="wide")
st.title("📊 Dashboard Seguimiento Proyecto DMAIC")

# URL RAW de tu CSV en GitHub
URL_CSV = "https://raw.githubusercontent.com/Santiagoherrella/ReduccioncostosPM/refs/heads/main/Actividades.csv"

def cargar_datos():
    return pd.read_csv(URL_CSV)
    
df = cargar_datos()
# Definir columnas a eliminar
columnas_a_eliminar = ["@odata.etag", "ItemInternalId", "Correo responsable"]
# Eliminar columnas
datos_limpios = df.drop(columns=columnas_a_eliminar, errors="ignore")
#Imprime las primeras columnas -- Pruebas para ver que si carga la tabla
#print(datos_limpios.head()) # esta impresion es en el teminal no en la interfaz streamlit
#Revisamos los datos porcetaje para sumarlos y calcular el indicador 
datos_limpios["Porcetaje"] = pd.to_numeric(datos_limpios["Porcetaje"], errors="coerce")
#Sumamos los valores que estan en procentaje
suma_porcentaje = datos_limpios["Porcetaje"].sum()   # Suma de la columna
#Contamos el numero de filas que tenemos en la tabla csv
num_filas = len(datos_limpios)
#Calculamos el indicador
if num_filas > 1: #Se activa si existe mas de una fila en el tabla la fila 1 es la tabla
    indicador = (suma_porcentaje / (num_filas - 1)) * 100 #Se calcula el indicador
    total_tareas = num_filas - 1 
else:
    indicador = 0
    total_tareas = 0
#Vamos a filtrar las actividades terminadas
Filter1 = ["Finalizado"]
# Filtrar las filas que tengan esos valores en 'Cronograma'
Filas_filter1 = df[df["Cronograma "].isin(Filter1)]
# Contar cuántas hay
finalizadas = len(Filas_filter1)
#Mostramos el indicador en streamlit

col1, col2, col3 = st.columns(3) # Creamos tres columnas para mostrar la información
col1.metric(label="Indicador", value=f"{indicador:.2f}%")
col2.metric(label="Total de actividades", value=f"{total_tareas}")
col3.metric(label ="Actividades terminadas", value=f"{total_tareas}")
st.divider()

