import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Diccionario extraído de tus imágenes (image_331c22.png)
HW_MAP = {
    "3059609": "UMPTga3", "02311VGW": "FANF", "02312JWX": "FANh",
    "02312QKD": "WD2MUEIUd", "02312JXA": "UPEUg", "02312VRC": "RRU5513w",
    "34060599": "SFP 10G-1310nm-10km", "34060713": "SFP 10G-1310nm-1km",
    "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b", "3058626": "UBBPg2",
    "02311TVH": "UPEUe", "02314PEF": "RRU5517t", "34061940": "SFP 25G-1310nm-0.3km",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "3058543": "UMPTg3",
    "3058627": "UBBPg3", "34060742": "SFP 10G-1310nm-10km", "02313AFM": "RRU5904w",
    "02311PFF": "RRU5301", "02312CMF": "RRU5904w", "34061042": "SFP 10G-1310nm-10km",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "34062523": "SFP 1.2G-1310nm-10km",
    "34061618": "SFP 25G-1310nm-10km", "02314SVV": "RRU5935E", "02314UUR": "RRU5336E",
    "02312RXX": "RRU5304w", "34060495": "SFP 10G-1310nm-10km", "02314GEE": "BBU5900C",
    "02312PMH": "RRU5901", "34061630": "SFP 11G-1310nm-10km", "02312JWU": "UPEUh",
    "02314SVW": "RRU5935E", "2318170": "SFP 10G-1310nm-10km", "02312TNN": "AAU5339w",
    "3059607": "UMPTga2", "3058707": "UBBPg2a", "2315200": "SFP 1.2G-1310nm-10km"
}

# Normalizamos el diccionario: quitamos ceros y espacios de las llaves
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría HW - Sin Desconocidos", layout="wide")
st.title("📊 Traducción de Inventario (PN a Nombre)")

file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # EXCLUIR AC/DC
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        pwr_list = ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU"]
        df_f = df[~df['Board Name'].str.contains('|'.join(pwr_list), case=False)].copy()

        # FUNCIÓN DE TRADUCCIÓN MEJORADA
        def smart_translate(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip()
            # 1. Quitamos sufijos como -001, -02, etc.
            pn_base = pn_raw.split('-')[0].strip()
            # 2. Quitamos ceros a la izquierda
            pn_clean = pn_base.lstrip('0')
            
            # Buscamos en el mapa limpio
            return CLEAN_MAP.get(pn_clean, f"PN: {pn_raw}")

        df_f['Nombre HW'] = df_f.apply(smart_translate, axis=1)

        # Gráfico
        st.subheader("📈 Distribución de Hardware")
        conteo = df_f['Nombre HW'].value_counts().reset_index()
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo.head(20), x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla de Detalle
        cols = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        st.dataframe(df_f[[c for c in cols if c in df_f.columns]], use_container_width=True)

        # Exportar
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[[c for c in cols if c in df_f.columns]].to_excel(writer, index=False, sheet_name='Detalle')
        st.download_button("📥 Descargar Reporte", output.getvalue(), file_name="Inventario_Limpio.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
