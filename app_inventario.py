import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# ... (Mantenemos tu HW_MAP y CLEAN_MAP igual) ...
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "03050BYF": "UBBPg1a", "03050BKS": "UBBPg3b",
    # ... resto del mapa ...
}
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Cloud Multi-formato", layout="wide")
st.title("📊 Hardware Huawei RED")

# Cambiamos los tipos aceptados
file = st.file_uploader("Sube tu inventario (CSV, XLSX o XML)", type=["csv", "xlsx", "xml"])

if file:
    try:
        # --- LÓGICA DE LECTURA SEGÚN EXTENSIÓN ---
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        elif file_extension == 'xlsx':
            df = pd.read_excel(file, dtype=str)
        elif file_extension == 'xml':
            # Nota: read_xml requiere que las filas estén bajo una etiqueta común
            df = pd.read_xml(file, dtype=str)
        
        # Limpieza básica de columnas
        df.columns = df.columns.str.strip()

        # 1. EXCLUSIÓN DE ENERGÍA
        if 'Board Name' in df.columns:
            df['Board Name'] = df['Board Name'].fillna('').astype(str)
            df_f = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()
        else:
            df_f = df.copy()

        # 2. MOTOR DE TRADUCCIÓN (Tu función original)
        def traducir_hardware(row):
            # Buscamos la columna de PN, a veces varía el nombre según el formato
            pn_col = next((c for c in df.columns if 'PN' in c or 'BOM' in c), None)
            if not pn_col: return "Columna PN no hallada"
            
            pn_raw = str(row.get(pn_col, '')).strip().upper()
            pn_base = re.split(r'[- ]', pn_raw)[0]
            pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            return CLEAN_MAP.get(pn_match, f"PN: {pn_raw}")

        df_f['Nombre HW'] = df_f.apply(traducir_hardware, axis=1)

        # 3. INTERFAZ Y FILTROS
        # Intentamos detectar la columna de nombre de sitio (NEName o similar)
        site_col = next((c for c in df_f.columns if 'NEName' in c or 'NE Name' in c), None)
        
        if site_col:
            sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df_f[site_col].unique().tolist()))
            df_final = df_f if sitio_sel == "Todos" else df_f[df_f[site_col] == sitio_sel]
        else:
            st.warning("No se detectó la columna 'NEName'. Mostrando todos los datos.")
            df_final = df_f

        # 4. GRÁFICOS Y TABLAS
        col1, col2 = st.columns([1, 2])
        
        with col1:
            conteo = df_final['Nombre HW'].value_counts().reset_index().head(15)
            conteo.columns = ['Hardware', 'Cantidad']
            st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', 
                                   title="Top Hardware Detectado", color='Cantidad'), use_container_width=True)

        with col2:
            st.subheader("📋 Detalle de Equipos")
            # Definimos columnas prioritarias para mostrar
            cols_interes = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'Subrack No.', 'Slot No.', 'SN(Bar Code)', 'Serial Number']
            cols_finales = [c for c in cols_interes if c in df_final.columns]
            st.dataframe(df_final[cols_finales], use_container_width=True, hide_index=True)

        # 5. EXPORTAR EXCEL
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Inventario_Procesado')
        
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=output.getvalue(),
            file_name=f"Inventario_Procesado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Hubo un problema al procesar el archivo: {e}")
        st.info("Asegúrate de que el XML tenga una estructura plana o que las columnas coincidan con el inventario estándar.")
