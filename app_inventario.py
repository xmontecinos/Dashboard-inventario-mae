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
    "02311VGW": "FANF", "02312JWX": "FANh", "02312JWU": "UPEUh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312QKD": "WD2MUEIUd",
    "02314GEE": "BBU5900C", "02312VRC": "RRU5513w", "02314PEF": "RRU5517t",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "02313DMS": "HAAU5323",
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E",
    "02314UUR": "RRU5336E", "02312RXX": "RRU5304w", "02312PMH": "RRU5901",
    "02312TNN": "AAU5339w", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR",
    "02313AAR": "HAAU5222", "02314RER": "AAU5942", "02312VCW": "AAU5942",
    "02314TCS": "AAU5736", "02312QYQ": "AAU5639w",
    # SFPs
    "34060599": "10300Mb/s-10km", "34060713": "10300Mb/s-1km",
    "34061940": "25750Mb/s-0.3km", "34060290": "1300Mb/s-10km",
    "34060742": "10300Mb/s-10km", "34061042": "10300Mb/s-10km",
    "2318170": "10300Mb/s-10km", "02313URL": "SFP 10G-10km"
}

# NORMALIZACIÓN AGRESIVA DEL DICCIONARIO
# Quitamos espacios, ceros a la izquierda y convertimos a mayúsculas
CLEAN_MAP = {str(k).strip().upper().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría HW - Corrección Total", layout="wide")
st.title("📊 Inventario Traducido (Sin PN vacíos)")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # 1. EXCLUIR AC/DC (Limpia la vista)
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        df_f = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()

        # 2. MOTOR DE TRADUCCIÓN REFORZADO
        def deep_clean_translate(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip().upper()
            
            # Limpieza 1: Quitar sufijos después del guion o espacio
            pn_base = re.split(r'[- ]', pn_raw)[0]
            
            # Limpieza 2: Quitar todo lo que no sea alfanumérico y quitar ceros iniciales
            pn_clean = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            
            # Búsqueda en el mapa limpio
            return CLEAN_MAP.get(pn_clean, f"PN: {pn_raw}")

        df_f['Nombre HW'] = df_f.apply(deep_clean_translate, axis=1)

        # 3. INTERFAZ Y FILTROS
        sitio_sel = st.selectbox("📍 Filtrar Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio_sel == "Todos" else df_f[df_f['NEName'] == sitio_sel]

        # Gráfico
        resumen = df_final['Nombre HW'].value_counts().reset_index().head(20)
        resumen.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(resumen, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla de Detalle
        cols_v = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        st.dataframe(df_final[[c for c in cols_v if c in df_final.columns]], use_container_width=True)

        # Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[[c for c in cols_v if c in df_final.columns]].to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Reporte", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error Crítico: {e}")
