import streamlit as st
import pandas as pd
import plotly.express as px
import io

# DICCIONARIO MAESTRO (Extraído de tus tablas image_331c22.png)
HW_MAP = {
    "3059609": "UMPTga3", "02311VGW": "FANF", "02312JWX": "FANh",
    "02312QKD": "WD2MUEIUd", "02312JXA": "UPEUg", "02312VRC": "RRU5513w",
    "34060599": "SFP 10G-1310nm-10km", "34060713": "SFP 10G-1310nm-1km",
    "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b", "3058626": "UBBPg2",
    "02311TVH": "UPEUe", "02314PEF": "RRU5517t", "34061940": "SFP 25G-1310nm-0.3km",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "34060290": "SFP 1.25G-1310nm-10km",
    "34060473": "SFP 1.25G-1310nm-10km", "3058543": "UMPTg3", "02313DMS": "HAAU5323",
    "3058627": "UBBPg3", "34060742": "SFP 10G-1310nm-10km", "02313AFM": "RRU5904w",
    "02311PFF": "RRU5301", "02312CMF": "RRU5904w", "34061042": "SFP 10G-1310nm-10km",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "34062523": "SFP 1.2G-1310nm-10km",
    "34061618": "SFP 25G-1310nm-10km", "02314SVV": "RRU5935E", "02314UUR": "RRU5336E",
    "02312RXX": "RRU5304w", "34060495": "SFP 10G-1310nm-10km", "02314GEE": "BBU5900C",
    "02312PMH": "RRU5901", "34061630": "SFP 11G-1310nm-10km", "02312JWU": "UPEUh",
    "02314SVW": "RRU5935E", "2318170": "SFP 10G-1310nm-10km", "02312TNN": "AAU5339w",
    "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR", "34060298": "SFP 1.25G-1310nm-40km",
    "34060613": "SFP 10G-1310nm-10km", "02313AAR": "HAAU5222", "3059607": "UMPTga2",
    "02314RER": "AAU5942", "02313URL": "SFP 10G-1310nm-10km", "02312VCW": "AAU5942",
    "34060484": "SFP 2.5G-1310nm-2km", "02314TCS": "AAU5736", "3058707": "UBBPg2a",
    "34060796": "SFP 10G-1550nm-40km", "02313BJH": "SFP 10G-1310nm-10km",
    "02312QYQ": "AAU5639w", "2315200": "SFP 1.2G-1310nm-10km"
}

# Limpieza automática del mapa
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Cloud Pro", layout="wide")
st.title("📊 Traducción de Hardware por PN")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # 1. EXCLUIR AC/DC (Limpieza solicitada)
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        pwr_keywords = ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU"]
        df_f = df[~df['Board Name'].str.contains('|'.join(pwr_keywords), case=False)].copy()

        # 2. TRADUCCIÓN DE PN A NOMBRE
        def translate(row):
            pn = str(row.get('PN(BOM Code/Item)', '')).split('-')[0].strip().lstrip('0')
            return CLEAN_MAP.get(pn, f"Desconocido ({pn})")

        df_f['Nombre HW'] = df_f.apply(translate, axis=1)

        # Gráfico de distribución
        conteo = df_f['Nombre HW'].value_counts().reset_index()
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo.head(20), x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla de visualización
        cols_show = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        valid_cols = [c for c in cols_show if c in df_f.columns]
        st.dataframe(df_f[valid_cols], use_container_width=True)

        # Exportar a Excel (Solo el detalle visible)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[valid_cols].to_excel(writer, index=False, sheet_name='Detalle')
        st.download_button("📥 Descargar Detalle Traducido", output.getvalue(), file_name="Inventario_Traducido.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
