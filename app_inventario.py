import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO (Asegúrate de ir agregando aquí los nuevos PNs)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3",
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3050BKS": "UBBPg3b", "03050BKS": "UBBPg3b",
    "3050BYF": "UBBPg1a", "03050BYF": "UBBPg1a",
    "02311VGW": "FANF", "02312JWX": "FANh",
    # SFPs (Ejemplos)
    "34060599": "10300Mb/s-1310nm-10km",
    "34060713": "10300Mb/s-1310nm-1km"
}

# Limpieza automática del mapa para que no importen los ceros
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Final", layout="wide")
st.title("📊 Auditoría de Inventario")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        if 'PN(BOM Code/Item)' in df.columns:
            # Limpiamos el dato del archivo quitando espacios y ceros iniciales
            df['PN_Clean'] = df['PN(BOM Code/Item)'].str.strip().str.lstrip('0')
            
            # Si el código existe en el diccionario, pone el nombre. Si no, pone "PN: [código]"
            df['Nombre HW'] = df['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro y Tabla
        sitio_sel = st.selectbox("📍 Filtrar Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # Columnas solicitadas (incluyendo Inventory Unit ID)
        cols_cuadro = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        cols_validas = [c for c in cols_cuadro if c in df_f.columns]
        
        st.dataframe(df_f[cols_validas], use_container_width=True)

        # Botón de descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[cols_validas].to_excel(writer, index=False, sheet_name='Detalle')
        
        st.download_button("📥 Descargar este cuadro en Excel", output.getvalue(), file_name="detalle.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
