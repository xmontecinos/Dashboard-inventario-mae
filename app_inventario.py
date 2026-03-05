import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Diccionario maestro basado en tu lista enviada
HW_MAP = {
    "3059609": "UMPTga3", "02311VGW": "FANF", "02312JWX": "FANh", "02312QKD": "WD2MUEIUd",
    "02312JXA": "UPEUg", "02312VRC": "RRU5513w", "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b",
    "3058626": "UBBPg2", "02311TVH": "UPEUe", "02314PEF": "RRU5517t", "02312XMM": "AAU5339w",
    "02313GFY": "RRU5512", "3058543": "UMPTg3", "02313DMS": "HAAU5323", "3058627": "UBBPg3",
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w", "02312LWK": "RRU5818",
    "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E", "02314UUR": "RRU5336E", "02312RXX": "RRU5304w",
    "02314GEE": "BBU5900C", "02312PMH": "RRU5901", "02312JWU": "UPEUh", "02314SVW": "RRU5935E",
    "02312TNN": "AAU5339w", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR", "02313AAR": "HAAU5222",
    "3059607": "UMPTga2", "02314RER": "AAU5942", "02312VCW": "AAU5942", "02314TCS": "AAU5736",
    "3058707": "UBBPg2a", "02312QYQ": "AAU5639w",
    # SFPs Detallados
    "34060599": "10300Mb/s-10km", "34060713": "10300Mb/s-1km", "34061940": "25750Mb/s-0.3km",
    "34060290": "1300Mb/s-10km", "34060473": "1300Mb/s-10km", "34060742": "10300Mb/s-10km",
    "34061042": "10300Mb/s-10km", "34062523": "1200Mb/s-10km", "34061618-002": "25750Mb/s-10km",
    "34061630": "11300Mb/s-10km", "2318170": "10300Mb/s-10km", "34060298": "1300Mb/s-40km"
}

st.set_page_config(page_title="Auditoría HW", layout="wide")
st.title("📊 Dashboard de Inventario")

file = st.file_uploader("Sube el CSV Inventory_Board", type=["csv"])

if file:
    df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
    df.columns = df.columns.str.strip()
    
    # Crear columna Nombre HW
    if 'PN(BOM Code/Item)' in df.columns:
        df['Nombre HW'] = df['PN(BOM Code/Item)'].map(HW_MAP).fillna(df['PN(BOM Code/Item)'])

    # Filtros e Interfaz
    sitio = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
    df_f = df if sitio == "Todos" else df[df['NEName'] == sitio]

    # Gráfica de Barras
    conteo = df_f['Nombre HW'].value_counts().reset_index()
    conteo.columns = ['Hardware', 'Cantidad']
    fig = px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad', color_continuous_scale='Turbo')
    st.plotly_chart(fig, use_container_width=True)

    # Tabla
    st.dataframe(df_f[['NEName', 'Nombre HW', 'Board Name', 'Subrack No.', 'SN(Bar Code)']], use_container_width=True)