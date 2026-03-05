import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO AMPLIADO (Incluye UBBPg3b y corrección de ceros)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3",
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3050BKS": "UBBPg3b", "03050BKS": "UBBPg3b",  # <--- UBBPg3b Agregado
    "3050BYF": "UBBPg1a", "03050BYF": "UBBPg1a",
    "3058627": "UBBPg3", "03058627": "UBBPg3",
    "3058707": "UBBPg2a", "03058707": "UBBPg2a",
    "02312QKD": "WD2MUEIUd", "02314GEE": "BBU5900C",
    "02311VGW": "FANF", "02312JWX": "FANh",
    "34060599": "10300Mb/s-1310.00nm-LC-10km",
    "34060713": "10300Mb/s-1310.00nm-LC-1km",
    "34061940": "25750Mb/s-1310.00nm-LC-0.3km",
    "34060290": "1300Mb/s-1310.00nm-LC-10km",
    "34060742": "10300Mb/s-1310.00nm-LC-10km"
}

st.set_page_config(page_title="Auditoría de Red Cloud", layout="wide")
st.title("📊 Reporte de Inventario con Inventory Unit ID")

file = st.file_uploader("Sube el archivo CSV (Inventory_Board)", type=["csv"])

if file:
    try:
        # Lectura robusta del CSV
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- LÓGICA DE TRADUCCIÓN DE HARDWARE ---
        if 'PN(BOM Code/Item)' in df.columns:
            # Limpiamos PN: quitamos espacios y ceros a la izquierda para el match
            df['PN_Match'] = df['PN(BOM Code/Item)'].str.strip().str.lstrip('0')
            
            # Limpiamos llaves del diccionario para asegurar compatibilidad
            CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}
            
            # Crear columna descriptiva
            df['Nombre HW'] = df['PN_Match'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro de Sitio (NEName)
        sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # --- VISUALIZACIÓN GRÁFICA ---
        st.subheader(f"Distribución en {sitio_sel}")
        resumen = df_f['Nombre HW'].value_counts().reset_index()
        resumen.columns = ['Hardware', 'Cantidad']
        fig = px.bar(resumen.head(15), x='Cantidad', y='Hardware', orientation='h', color='Cantidad')
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLA DE DATOS CON INVENTORY UNIT ID ---
        st.subheader("📋 Detalle de Hardware Registrado")
        
        # Columnas que queremos mostrar (incluyendo Inventory Unit ID)
        columnas_finales = [
            'NEName', 
            'Nombre HW', 
            'Board Name', 
            'Inventory Unit ID', # <--- Columna solicitada añadida
            'Subrack No.', 
            'Slot No.',
            'SN(Bar Code)'
        ]
        
        # Filtramos solo las que existan en el archivo por seguridad
        cols_existentes = [c for c in columnas_finales if c in df_f.columns]
        st.dataframe(df_f[cols_existentes], use_container_width=True)

        # --- EXPORTAR ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar este reporte (Excel)", output.getvalue(), 
                           file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error procesando los datos: {e}")
