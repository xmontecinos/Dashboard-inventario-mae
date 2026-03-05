import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO (Mantenemos los conocidos)
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a",
    "02311VGW": "FANF", "02312JWX": "FANh", "02312JWU": "UPEUh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312QKD": "WD2MUEIUd"
}

CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría AC/DC y HW", layout="wide")
st.title("📊 Control de Inventario y Energía (AC/DC)")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- LÓGICA DE DETECCIÓN INTELIGENTE ---
        def identificar_hardware(row):
            pn_original = str(row.get('PN(BOM Code/Item)', '')).strip()
            board_name = str(row.get('Board Name', '')).upper()
            
            # 1. Limpiar PN para buscar en diccionario
            pn_clean = pn_original.split('-')[0].lstrip('0')
            if pn_clean in CLEAN_MAP:
                return CLEAN_MAP[pn_clean]
            
            # 2. BUSCAR AC/DC O ENERGÍA POR NOMBRE (Si el PN no falló)
            if any(x in board_name for x in ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU"]):
                return f"⚡ Energía: {board_name}"
            
            # 3. Si no es nada de lo anterior, dejar el PN
            return f"PN: {pn_original}"

        df['Nombre HW'] = df.apply(identificar_hardware, axis=1)

        # Barra lateral con estadísticas
        total_pns = df['Nombre HW'].str.contains("PN:").sum()
        total_energia = df['Nombre HW'].str.contains("⚡").sum()
        
        st.sidebar.header("Resumen de Hallazgos")
        st.sidebar.metric("Módulos AC/DC Detectados", total_energia)
        st.sidebar.metric("PNs aún sin nombre", total_pns)

        # Filtro
        sitio_sel = st.selectbox("📍 Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # Gráfico
        st.subheader("📈 Distribución de Hardware y Energía")
        conteo = df_f['Nombre HW'].value_counts().reset_index().head(20)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla y Excel
        cols = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        cols_finales = [c for c in cols if c in df_f.columns]
        st.dataframe(df_f[cols_finales], use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[cols_finales].to_excel(writer, index=False, sheet_name='Inventario')
        st.download_button("📥 Descargar Reporte", output.getvalue(), file_name=f"Inventario_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
