import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO (Hardware que SI queremos ver)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3",
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3050BKS": "UBBPg3b", "03050BKS": "UBBPg3b",
    "3050BYF": "UBBPg1a", "03050BYF": "UBBPg1a",
    "3058627": "UBBPg3", "03058627": "UBBPg3",
    "3058707": "UBBPg2a", "03058707": "UBBPg2a",
    "02311VGW": "FANF", "02312JWX": "FANh"
}

CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría HW - Excluyendo AC/DC", layout="wide")
st.title("📊 Inventario de Red (Solo Tarjetas y SFPs)")

file = st.file_uploader("Sube el archivo CSV Inventory_Board", type=["csv"])

if file:
    try:
        # Carga de datos
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- LÓGICA DE EXCLUSIÓN AC/DC ---
        # Convertimos a mayúsculas para asegurar que encuentre "ac" o "AC"
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        palabras_excluir = ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU", "PDF"]
        
        # Filtramos: Solo nos quedamos con filas que NO tengan esas palabras
        patron_excluir = '|'.join(palabras_excluir)
        df_limpio = df[~df['Board Name'].str.contains(patron_excluir, case=False, na=False)].copy()

        # --- PROCESAMIENTO DE NOMBRES ---
        if 'PN(BOM Code/Item)' in df_limpio.columns:
            df_limpio['PN_Clean'] = df_limpio['PN(BOM Code/Item)'].str.split('-').str[0].str.strip().str.lstrip('0')
            df_limpio['Nombre HW'] = df_limpio['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df_limpio['PN(BOM Code/Item)'])

        # Estadísticas en barra lateral
        total_original = len(df)
        total_actual = len(df_limpio)
        excluidos = total_original - total_actual
        
        st.sidebar.header("Resumen de Filtros")
        st.sidebar.write(f"✅ Registros de Hardware: {total_actual}")
        st.sidebar.error(f"❌ Registros AC/DC Excluidos: {excluidos}")

        # Filtro de Sitio
        sitio_sel = st.selectbox("📍 Seleccionar Sitio:", ["Todos"] + sorted(df_limpio['NEName'].unique().tolist()))
        df_f = df_limpio if sitio_sel == "Todos" else df_limpio[df_limpio['NEName'] == sitio_sel]

        # Gráfico
        st.subheader(f"📈 Distribución de Hardware - {sitio_sel}")
        conteo = df_f['Nombre HW'].value_counts().reset_index().head(20)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla (Detalle solicitado)
        st.subheader("📋 Detalle del Cuadro (Sin Energía)")
        cols_finales = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        st.dataframe(df_f[[c for c in cols_finales if c in df_f.columns]], use_container_width=True)

        # Exportar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[[c for c in cols_finales if c in df_f.columns]].to_excel(writer, index=False, sheet_name='Detalle_Hardware')
        
        st.download_button("📥 Descargar este cuadro (Excel)", output.getvalue(), file_name=f"Hardware_{sitio_sel}.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
