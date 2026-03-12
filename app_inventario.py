import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO
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
    "34061618": "25750Mb/s-1310nm-10km", "34061630": "11300Mb/s-1310nm-10km"
}

# Normalización del mapa: Claves sin ceros iniciales y sin espacios
CLEAN_MAP = {str(k).strip().upper().lstrip('0'): v for k, v in HW_MAP.items()}

def traducir_hardware(row, col_name):
    if not col_name: return "N/A"
    pn_raw = str(row.get(col_name, '')).strip().upper()
    
    # 1. Extraer la base del PN (quita lo que sigue a un guión o espacio)
    pn_base = re.split(r'[- ]', pn_raw)[0]
    
    # 2. Quitar caracteres no alfanuméricos y ceros iniciales
    pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
    
    # 3. Retornar traducción o el PN original si no existe en mapa
    return CLEAN_MAP.get(pn_match, f"PN: {pn_raw}")

# --- CONFIGURACIÓN DE STREAMLIT ---
st.set_page_config(page_title="Inventario Huawei Pro", layout="wide")
st.title("📊 Gestión de Hardware Huawei")

file = st.file_uploader("Sube tu archivo (CSV, XLSX o XML)", type=["csv", "xlsx", "xml"])

if file:
    try:
        # LECTURA MULTIFORMATO
        ext = file.name.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        elif ext == 'xlsx':
            df = pd.read_excel(file, dtype=str)
        elif ext == 'xml':
            df = pd.read_xml(file, dtype=str)
        
        df.columns = df.columns.str.strip()

        # IDENTIFICACIÓN DINÁMICA DE COLUMNAS
        pn_col = next((c for c in df.columns if 'PN' in c.upper() or 'BOM' in c.upper()), None)
        sitio_col = next((c for c in df.columns if 'NENAME' in c.upper().replace(" ", "")), "NEName")
        sn_col = next((c for c in df.columns if 'SN' in c.upper() or 'SERIAL' in c.upper()), None)

        # PROCESAMIENTO
        # Aplicar exclusión de energía según tus reglas
        if 'Board Name' in df.columns:
            df = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()
        
        df['Nombre HW'] = df.apply(lambda r: traducir_hardware(r, pn_col), axis=1)

        # --- INTERFAZ DE PESTAÑAS ---
        tab1, tab2 = st.tabs(["📈 Dashboard General", "🔍 Localizador por Serial"])

        with tab1:
            st.subheader("Filtros y Visualización")
            sitios_disponibles = ["Todos"] + sorted(df[sitio_col].unique().tolist()) if sitio_col in df.columns else ["Todos"]
            sitio_sel = st.selectbox("📍 Selecciona un Sitio:", sitios_disponibles)
            
            df_final = df if sitio_sel == "Todos" else df[df[sitio_col] == sitio_sel]

            # Gráfico de barras
            conteo = df_final['Nombre HW'].value_counts().reset_index().head(15)
            conteo.columns = ['Hardware', 'Cantidad']
            st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', 
                                   color='Cantidad', color_continuous_scale='Viridis'), use_container_width=True)

            # Detalle en tabla
            st.subheader("📋 Inventario Detallado")
            cols_ver = [sitio_col, 'Nombre HW', 'Board Name', 'Subrack No.', 'Slot No.', sn_col]
            cols_existentes = [c for c in cols_ver if c in df_final.columns]
            st.dataframe(df_final[cols_existentes], use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("🔎 Buscador de Posición")
            if sn_col:
                sn_input = st.text_input("Ingresa el Serial Number (SN):").strip()
                if sn_input:
                    res = df[df[sn_col].str.contains(sn_input, case=False, na=False)]
                    
                    if not res.empty:
                        for _, row in res.iterrows():
                            st.success(f"✅ Coincidencia encontrada en **{row.get(sitio_col, 'N/A')}**")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.write("**Equipo:**")
                                st.code(row['Nombre HW'])
                            with c2:
                                st.write("**Ubicación:**")
                                st.write(f"Subrack: {row.get('Subrack No.', 'N/A')}")
                                st.write(f"Slot: {row.get('Slot No.', 'N/A')}")
                            with c3:
                                st.write("**ID Unidad:**")
                                st.write(row.get('Inventory Unit ID', 'N/A'))
                            st.divider()
                    else:
                        st.error("No se encontró el Serial en la base de datos.")
            else:
                st.warning("No se detectó columna de Serial (SN) en el archivo.")

        # BOTÓN DE DESCARGA
        st.sidebar.header("Opciones")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        st.sidebar.download_button("📥 Descargar Todo en Excel", output.getvalue(), "Inventario_Procesado.xlsx")

    except Exception as e:
        st.error(f"Error crítico: {e}")
