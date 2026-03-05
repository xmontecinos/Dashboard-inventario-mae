import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO (Asegúrate de que TODOS estos estén aquí)
# Basado en tus imágenes proporcionadas
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a", "2318170": "UBBP",
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
    # SFPs (Transceptores ópticos)
    "34060599": "SFP 10G-10km", "34060713": "SFP 10G-1km",
    "34061940": "SFP 25G-0.3km", "34060290": "SFP 1.25G-10km",
    "34060473": "SFP 1.25G-10km", "34060742": "SFP 10G-10km",
    "34061042": "SFP 10G-10km", "34062523": "SFP 1.2G-10km",
    "34061618": "SFP 25G-10km", "34061630": "SFP 11G-10km",
    "2315200": "SFP 1.2G-10km", "02313URL": "SFP 10G-10km"
}

# Limpieza preventiva del diccionario
CLEAN_MAP = {str(k).strip().upper().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Red Final", layout="wide")
st.title("📊 Auditoría de Hardware (PN a Nombre)")

file = st.file_uploader("Sube el archivo CSV de Inventario", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # 1. EXCLUSIÓN DE ENERGÍA (AC/DC)
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        # Filtramos para quitar lo que NO queremos ver
        df_f = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()

        # 2. MOTOR DE TRADUCCIÓN INTELIGENTE
        def traducir_hardware(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip().upper()
            
            # Limpiar PN: quitar sufijos (-001) y ceros iniciales
            pn_base = re.split(r'[- ]', pn_raw)[0]
            pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            
            # A. Buscar en el diccionario
            if pn_match in CLEAN_MAP:
                return CLEAN_MAP[pn_match]
            
            # B. Identificación por familia (Si empieza por 3406 es un SFP)
            if pn_match.startswith("3406"):
                return f"SFP Genérico ({pn_raw})"
            
            # C. Si no se encuentra, mostrar PN para identificarlo luego
            return f"PN: {pn_raw}"

        df_f['Nombre HW'] = df_f.apply(traducir_hardware, axis=1)

        # 3. INTERFAZ Y DESCARGA
        sitio_sel = st.selectbox("📍 Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio_sel == "Todos" else df_f[df_f['NEName'] == sitio_sel]

        # Gráfico de Barras
        conteo = df_final['Nombre HW'].value_counts().reset_index().head(15)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla de Detalle (Con Inventory Unit ID solicitado)
        cols_mostrar = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        st.dataframe(df_final[[c for c in cols_mostrar if c in df_final.columns]], use_container_width=True)

        # Botón Excel (Solo el detalle del cuadro)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[[c for c in cols_mostrar if c in df_final.columns]].to_excel(writer, index=False, sheet_name='Detalle')
        st.download_button("📥 Descargar Reporte Traducido", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
