import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO COMPLETO (Extraído de tus imágenes)
HW_MAP = {
    # Unidades de Control y Procesamiento
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b",
    # Módulos de Energía, Fans y Otros
    "02311VGW": "FANF", "02312JWX": "FANh", "02312QKD": "WD2MUEIUd",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312JWU": "UPEUh",
    "02314GEE": "BBU5900C", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR",
    # Radios (RRU / AAU)
    "02312VRC": "RRU5513w", "02314PEF": "RRU5517t", "02312XMM": "AAU5339w",
    "02313GFY": "RRU5512", "02313DMS": "HAAU5323", "02313AFM": "RRU5904w",
    "02311PFF": "RRU5301", "02312CMF": "RRU5904w", "02312LWK": "RRU5818",
    "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E", "02314UUR": "RRU5336E",
    "02312RXX": "RRU5304w", "02312PMH": "RRU5901", "02314SVW": "RRU5935E",
    "02312TNN": "AAU5339w", "02313AAR": "HAAU5222", "02314RER": "AAU5942",
    "02312VCW": "AAU5942", "02314TCS": "AAU5736", "02312QYQ": "AAU5639w",
    # SFPs (Transceptores Ópticos)
    "34060599": "10300Mb/s-1310nm-10km", "34060713": "10300Mb/s-1310nm-1km",
    "34061940": "25750Mb/s-1310nm-0.3km", "34060290": "1300Mb/s-1310nm-10km",
    "34060473": "1300Mb/s-1310nm-10km", "34060742": "10300Mb/s-1310nm-10km",
    "34061042": "10300Mb/s-1310nm-10km", "34062523": "1200Mb/s-1310nm-10km",
    "34061618": "25750Mb/s-1310nm-10km", "34060495": "10300Mb/s-1310nm-10km",
    "34061630": "11300Mb/s-1310nm-10km", "2318170": "10300Mb/s-1310nm-10km",
    "34060298": "1300Mb/s-1310nm-40km", "34060613": "10300Mb/s-1310nm-10km",
    "02313URL": "10300Mb/s-1310nm-10km", "34060672": "10300Mb/s-1310nm-10km",
    "34060484": "2500Mb/s-1310nm-2km", "34060796": "10300Mb/s-1550nm-40km",
    "02313BJH": "10300Mb/s-1310nm-10km", "2315200": "1200Mb/s-1310nm-10km"
}

# Normalización del mapa (quitar ceros a la izquierda y espacios)
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Cloud Final", layout="wide")
st.title("📊 Hardware Huawei RED")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # 1. EXCLUSIÓN DE ENERGÍA (AC/DC)
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        df_f = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()

        # 2. MOTOR DE TRADUCCIÓN REFORZADO
        def traducir_hardware(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip().upper()
            
            # Limpiar PN: quitar sufijos (-001) y ceros iniciales
            pn_base = re.split(r'[- ]', pn_raw)[0]
            pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            
            # Buscar en el diccionario
            return CLEAN_MAP.get(pn_match, f"PN: {pn_raw}")

        df_f['Nombre HW'] = df_f.apply(traducir_hardware, axis=1)

        # 3. INTERFAZ
        sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio_sel == "Todos" else df_f[df_f['NEName'] == sitio_sel]

        # Gráfico
        conteo = df_final['Nombre HW'].value_counts().reset_index().head(20)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # 4. TABLA DE DETALLE (Con Subrack, Slot e Inventory Unit ID)
        st.subheader("📋 Detalle de Equipos")
        cols_mostrar = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'Subrack No.', 'Slot No.', 'SN(Bar Code)']
        cols_finales = [c for c in cols_mostrar if c in df_final.columns]
        st.dataframe(df_final[cols_finales], use_container_width=True)

        # 5. EXPORTAR EXCEL
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[cols_finales].to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Reporte Completo", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")

