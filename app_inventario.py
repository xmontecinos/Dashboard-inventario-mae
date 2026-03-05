import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO (Incluye tus SFPs y Hardware Crítico)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3", 
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3059607": "UMPTga2", "3058543": "UMPTg3",
    "02312QKD": "WD2MUEIUd", "02314GEE": "BBU5900C",
    "02311VGW": "FANF", "02312JWX": "FANh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe",
    "02312JWU": "UPEUh", "02312VRC": "RRU5513w",
    "02314PEF": "RRU5517t", "02312XMM": "AAU5339w",
    # SFPs Detallados
    "34060599": "10300Mb/s-1310.00nm-LC-10km",
    "34060713": "10300Mb/s-1310.00nm-LC-1km",
    "34061940": "25750Mb/s-1310.00nm-LC-0.3km",
    "34060290": "1300Mb/s-1310.00nm-LC-10km",
    "34060742": "10300Mb/s-1310.00nm-LC-10km",
    "34061618-002": "25750Mb/s-1310nm-LC-10km"
}

# Configuración de página
st.set_page_config(page_title="Inventario Cloud", layout="wide")
st.title("📊 Auditoría de Inventario de Red")

file = st.file_uploader("Sube tu archivo Inventory_Board.csv", type=["csv"])

if file:
    try:
        # Carga de datos
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- LÓGICA DE LIMPIEZA Y MAPEO ---
        if 'PN(BOM Code/Item)' in df.columns:
            # Quitamos espacios y ceros a la izquierda para la comparación
            df['PN_Clean'] = df['PN(BOM Code/Item)'].str.strip().str.lstrip('0')
            
            # Limpiamos también las llaves del diccionario para que coincidan
            CLEAN_MAP = {str(k).lstrip('0'): v for k, v in HW_MAP.items()}
            
            # Asignamos el nombre, si no existe ponemos el PN original
            df['Nombre HW'] = df['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro de Sitio
        sitios = sorted(df['NEName'].unique())
        sitio_sel = st.selectbox("📍 Seleccionar Sitio:", ["Todos"] + sitios)
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # --- GRÁFICA ---
        st.subheader(f"Distribución de Hardware - {sitio_sel}")
        conteo = df_f['Nombre HW'].value_counts().reset_index()
        conteo.columns = ['Hardware', 'Cantidad']
        fig = px.bar(conteo.head(20), x='Cantidad', y='Hardware', orientation='h', 
                     color='Cantidad', color_continuous_scale='Turbo')
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLA CON INVENTORY UNIT ID ---
        st.subheader("📋 Detalle de Equipos")
        columnas_visibles = [
            'NEName', 
            'Nombre HW', 
            'Board Name', 
            'Inventory Unit ID', 
            'Subrack No.', 
            'SN(Bar Code)'
        ]
        # Mostramos solo las columnas que existan en el CSV
        st.dataframe(df_f[[c for c in columnas_visibles if c in df_f.columns]], use_container_width=True)

        # --- BOTÓN DE DESCARGA ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Reporte Excel", output.getvalue(), 
                           file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Se produjo un error al procesar el archivo: {e}")