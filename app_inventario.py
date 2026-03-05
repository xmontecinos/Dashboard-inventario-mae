import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO REFORZADO
HW_MAP = {
    # Control y Procesamiento
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a", "2318170": "UBBP",
    # Módulos Críticos
    "02311VGW": "FANF", "02312JWX": "FANh", "02312JWU": "UPEUh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312QKD": "WD2MUEIUd",
    "02314GEE": "BBU5900C", "02312VNR": "RHUB5963e",
    # Radios y AAUs
    "02312VRC": "RRU5513w", "02314PEF": "RRU5517t", "02312XMM": "AAU5339w",
    "02313GFY": "RRU5512", "02313DMS": "HAAU5323", "02313AFM": "RRU5904w",
    "02311PFF": "RRU5301", "02312CMF": "RRU5904w", "02312LWK": "RRU5818",
    "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E", "02314UUR": "RRU5336E",
    "02312RXX": "RRU5304w", "02312PMH": "RRU5901", "02314SVW": "RRU5935E",
    "02312TNN": "AAU5339w", "02314MUJ": "pRRU5633GR", "02313AAR": "HAAU5222",
    "02314RER": "AAU5942", "02312VCW": "AAU5942", "02314TCS": "AAU5736",
    "02312QYQ": "AAU5639w",
    # SFPs 
    "34060599": "SFP 10G-10km", "34060713": "SFP 10G-1km",
    "34061940": "SFP 25G-0.3km", "34060290": "SFP 1.25G-10km",
    "34060473": "SFP 1.25G-10km", "34060742": "SFP 10G-10km",
    "34061042": "SFP 10G-10km", "34062523": "SFP 1.2G-10km",
    "34061618": "SFP 25G-10km", "34061630": "SFP 11G-10km",
    "34060298": "SFP 1.25G-40km", "34060495": "SFP 10G-10km",
    "34060613": "SFP 10G-10km", "02313URL": "SFP 10G-10km",
    "34060484": "SFP 2.5G-2km", "34060796": "SFP 10G-40km",
    "2315200": "SFP 1.2G-10km"
}

# Limpieza profunda del diccionario al iniciar
CLEAN_MAP = {str(k).strip().upper().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría de Red Pro", layout="wide")
st.title("📊 Control de Inventario de Red")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        if 'PN(BOM Code/Item)' in df.columns:
            # 1. Limpieza de datos con RegEx (quita todo lo que no sea letras o números)
            def clean_pn(val):
                if pd.isna(val): return ""
                val = str(val).split('-')[0] # Quitar sufijos -001
                val = re.sub(r'[^a-zA-Z0-9]', '', val) # Quitar espacios y símbolos
                return val.strip().upper().lstrip('0')

            df['PN_Match'] = df['PN(BOM Code/Item)'].apply(clean_pn)
            
            # 2. Mapeo
            df['Nombre HW'] = df['PN_Match'].map(CLEAN_MAP)
            
            # 3. Si sigue siendo nulo, intentar buscarlo sin quitar el cero (por si acaso)
            df['Nombre HW'] = df['Nombre HW'].fillna(df['PN(BOM Code/Item)'].str.strip().map(CLEAN_MAP))
            
            # 4. Finalmente, marcar como PN: los que no se encontraron
            df['Nombre HW'] = df['Nombre HW'].fillna("PN: " + df['PN(BOM Code/Item)'])

        # Estadísticas en barra lateral
        pendientes = df['Nombre HW'].str.contains("PN:").sum()
        st.sidebar.metric("Codigos sin nombre", pendientes)
        if pendientes > 0:
            st.sidebar.warning(f"Hay {pendientes} códigos que no están en el diccionario.")

        # Filtros
        sitio_sel = st.selectbox("📍 Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # Gráfico
        st.subheader("📈 Resumen de Equipos")
        conteo = df_f['Nombre HW'].value_counts().reset_index().head(15)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla y Excel
        cols = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        cols_finales = [c for c in cols if c in df_f.columns]
        st.dataframe(df_f[cols_finales], use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[cols_finales].to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Excel", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
