import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO (Basado en tus imágenes y reportes)
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a",
    "02311VGW": "FANF", "02312JWX": "FANh", "02312JWU": "UPEUh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312QKD": "WD2MUEIUd",
    "02314GEE": "BBU5900C", "02312VRC": "RRU5513w", "02314PEF": "RRU5517t",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "02313DMS": "HAAU5323", # <--- Corregido
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E",
    "02314UUR": "RRU5336E", "02312RXX": "RRU5304w", "02312PMH": "RRU5901",
    "02312TNN": "AAU5339w", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR",
    "02313AAR": "HAAU5222", "02314RER": "AAU5942", "02312VCW": "AAU5942",
    "02314TCS": "AAU5736", "02312QYQ": "AAU5639w",
    # SFPs (Transceptores)
    "34060599": "10300Mb/s-10km", "34060713": "10300Mb/s-1km",
    "34061940": "25750Mb/s-0.3km", "34060290": "1300Mb/s-10km",
    "34060742": "10300Mb/s-10km", "34061042": "10300Mb/s-10km",
    "34060495": "10300Mb/s-10km", "34061630": "11300Mb/s-10km",
    "2318170": "10300Mb/s-10km", "34060613": "10300Mb/s-10km",
    "02313URL": "SFP 10G-10km", "2315200": "1200Mb/s-10km"
}

# Normalización del diccionario: quitamos ceros a la izquierda y espacios para el match
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario de Red Pro", layout="wide")
st.title("📊 Auditoría de Inventario (Traducción PN)")

file = st.file_uploader("Sube el archivo CSV (Inventory_Board)", type=["csv"])

if file:
    try:
        # Carga de datos con manejo de codificación
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- CAPA 1: EXCLUIR AC/DC ---
        # Filtramos para quitar módulos de energía que ensucian el reporte
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        palabras_pwr = ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU", "PDF"]
        patron_pwr = '|'.join(palabras_pwr)
        df_f = df[~df['Board Name'].str.contains(patron_pwr, case=False, na=False)].copy()

        # --- CAPA 2: TRADUCCIÓN INTELIGENTE ---
        def smart_translate(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip()
            # 1. Quitar sufijos (-001, etc)
            pn_base = pn_raw.split('-')[0].strip()
            # 2. Quitar ceros a la izquierda para el match (02313DMS -> 2313DMS)
            pn_match = pn_base.lstrip('0')
            
            # Buscar en el diccionario normalizado
            return CLEAN_MAP.get(pn_match, f"PN: {pn_raw}")

        df_f['Nombre HW'] = df_f.apply(smart_translate, axis=1)

        # --- CAPA 3: VISUALIZACIÓN ---
        sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio_sel == "Todos" else df_f[df_f['NEName'] == sitio_sel]

        # Gráfico de Barras
        st.subheader(f"Resumen de Hardware en {sitio_sel}")
        resumen = df_final['Nombre HW'].value_counts().reset_index()
        resumen.columns = ['Hardware', 'Cantidad']
        fig = px.bar(resumen.head(20), x='Cantidad', y='Hardware', orientation='h', color='Cantidad', color_continuous_scale='Turbo')
        st.plotly_chart(fig, use_container_width=True)

        # Tabla de Detalle (Con Inventory Unit ID)
        st.subheader("📋 Detalle de Equipos Seleccionados")
        columnas_ver = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'Subrack No.', 'Slot No.', 'SN(Bar Code)']
        cols_finales = [c for c in columnas_ver if c in df_final.columns]
        st.dataframe(df_final[cols_finales], use_container_width=True)

        # Exportar a Excel (Solo el detalle mostrado)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[cols_finales].to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar este cuadro (Excel)", output.getvalue(), file_name=f"Reporte_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
