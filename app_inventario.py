import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO AMPLIADO (Basado en tus imágenes)
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a",
    "02312QKD": "WD2MUEIUd", "02314GEE": "BBU5900C", "02311VGW": "FANF", 
    "02312JWX": "FANh", "02312JXA": "UPEUg", "02311TVH": "UPEUe",
    "02312JWU": "UPEUh", "02312VRC": "RRU5513w", "02314PEF": "RRU5517t",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "02313DMS": "HAAU5323",
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E",
    "02314UUR": "RRU5336E", "02312RXX": "RRU5304w", "02312PMH": "RRU5901",
    "02312TNN": "AAU5339w", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR",
    "02313AAR": "HAAU5222", "02314RER": "AAU5942", "02312VCW": "AAU5942",
    "02314TCS": "AAU5736", "02312QYQ": "AAU5639w",
    # SFPs (Códigos de 8 dígitos)
    "34060599": "10300Mb/s-1310nm-10km", "34060713": "10300Mb/s-1310nm-1km",
    "34061940": "25750Mb/s-1310nm-0.3km", "34060290": "1300Mb/s-1310nm-10km",
    "34060473": "1300Mb/s-1310nm-10km", "34060742": "10300Mb/s-1310nm-10km",
    "34061042": "10300Mb/s-1310nm-10km", "34062523": "1200Mb/s-1310nm-10km",
    "34060495": "10300Mb/s-1310nm-10km", "34061630": "11300Mb/s-1310nm-10km",
    "2318170": "10300Mb/s-1310nm-10km", "34060298": "1300Mb/s-1310nm-40km",
    "34060613": "10300Mb/s-1310nm-10km", "02313URL": "10300Mb/s-1310nm-10km",
    "34060484": "2500Mb/s-1310nm-2km", "34060796": "10300Mb/s-1550nm-40km",
    "02313BJH": "10300Mb/s-1310nm-10km", "2315200": "1200Mb/s-1310nm-10km"
}

# Limpieza preventiva del diccionario (quita ceros y espacios de las llaves)
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría HW Cloud", layout="wide")
st.title("📊 Inventario de Hardware de Red")

file = st.file_uploader("Sube el archivo CSV de inventario", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        if 'PN(BOM Code/Item)' in df.columns:
            # NORMALIZACIÓN: Quita ceros a la izquierda, espacios y guiones finales
            df['PN_Clean'] = df['PN(BOM Code/Item)'].str.split('-').str[0] # Quita sufijos como -001
            df['PN_Clean'] = df['PN_Clean'].str.strip().str.lstrip('0')
            
            # Asignación del nombre usando el mapa limpio
            df['Nombre HW'] = df['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro de Sitio
        sitios = sorted(df['NEName'].unique().tolist())
        sitio_sel = st.selectbox("📍 Seleccionar Sitio:", ["Todos"] + sitios)
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # Gráfica de Barras
        st.subheader(f"Resumen de Equipos en {sitio_sel}")
        resumen = df_f['Nombre HW'].value_counts().reset_index()
        resumen.columns = ['Hardware', 'Cantidad']
        fig = px.bar(resumen.head(20), x='Cantidad', y='Hardware', orientation='h', color='Cantidad', color_continuous_scale='Turbo')
        st.plotly_chart(fig, use_container_width=True)

        # Tabla de Datos con Inventory Unit ID
        st.subheader("📋 Detalle Completo")
        columnas_ver = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'Subrack No.', 'Slot No.', 'SN(Bar Code)']
        cols_finales = [c for c in columnas_ver if c in df_f.columns]
        st.dataframe(df_f[cols_finales], use_container_width=True)

        # Exportar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Excel", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
