import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO (Simplificado para el ejemplo, mantén el tuyo completo)
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b",
    "02312VRC": "RRU5513w", "02314PEF": "RRU5517t", "02312XMM": "AAU5339w"
}

CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Huawei", layout="wide")
st.title("📊 Gestión de Hardware Huawei")

# Selector de archivos multiformato
file = st.file_uploader("Sube tu inventario (CSV, XLSX o XML)", type=["csv", "xlsx", "xml"])

if file:
    try:
        # --- LECTURA DE ARCHIVOS ---
        ext = file.name.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        elif ext == 'xlsx':
            df = pd.read_excel(file, dtype=str)
        elif ext == 'xml':
            df = pd.read_xml(file, dtype=str)
        
        df.columns = df.columns.str.strip()

        # --- PROCESAMIENTO ---
        def traducir_hardware(row):
            pn_col = next((c for c in df.columns if 'PN' in c or 'BOM' in c), None)
            if not pn_col: return "N/A"
            pn_raw = str(row.get(pn_col, '')).strip().upper()
            pn_base = re.split(r'[- ]', pn_raw)[0]
            pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            return CLEAN_MAP.get(pn_match, f"PN: {pn_raw}")

        df['Nombre HW'] = df.apply(traducir_hardware, axis=1)

        # --- CREACIÓN DE PESTAÑAS ---
        tab1, tab2 = st.tabs(["📈 Dashboard e Inventario", "🔍 Buscador por Serial"])

        with tab1:
            # Tu lógica original de filtrado y gráfico
            sitio_col = next((c for c in df.columns if 'NEName' in c or 'NE Name' in c), 'NEName')
            sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df[sitio_col].unique().tolist()))
            
            df_view = df if sitio_sel == "Todos" else df[df[sitio_col] == sitio_sel]
            
            conteo = df_view['Nombre HW'].value_counts().reset_index().head(15)
            conteo.columns = ['Hardware', 'Cantidad']
            st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)
            
            st.subheader("📋 Detalle de Equipos")
            st.dataframe(df_view, use_container_width=True)

        with tab2:
            st.subheader("🔎 Localizador de Sitios por Serial")
            st.info("Ingresa el Serial Number (SN) para saber a qué sitio pertenece el equipo.")
            
            # Identificar la columna de Serial (puede variar según el reporte)
            sn_col = next((c for c in df.columns if 'SN' in c or 'Serial' in c or 'Bar Code' in c), None)
            
            if sn_col:
                sn_input = st.text_input("Introduce el Serial Number:").strip()
                
                if sn_input:
                    # Buscamos coincidencias (case insensitive)
                    resultado = df[df[sn_col].str.contains(sn_input, case=False, na=False)]
                    
                    if not resultado.empty:
                        for i, row in resultado.iterrows():
                            st.success(f"✅ **Equipo encontrado:**")
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Sitio (NEName)", row.get(sitio_col, "No encontrado"))
                            c2.metric("Hardware", row['Nombre HW'])
                            c3.metric("Slot / Subrack", f"{row.get('Subrack No.', '0')} / {row.get('Slot No.', '0')}")
                            
                            st.write("---")
                            st.write("**Detalles técnicos completos:**")
                            st.json(row.to_dict())
                    else:
                        st.error("No se encontró ningún equipo con ese Serial en la base de datos.")
            else:
                st.warning("No se encontró una columna de Serial Number en el archivo subido.")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
