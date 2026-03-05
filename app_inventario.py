import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO (Asegúrate de ir agregando aquí los nuevos PNs)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3",
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3050BKS": "UBBPg3b", "03050BKS": "UBBPg3b",
    "3050BYF": "UBBPg1a", "03050BYF": "UBBPg1a",
    "3058627": "UBBPg3", "03058627": "UBBPg3",
    "02311VGW": "FANF", "02312JWX": "FANh",
    "02312QKD": "WD2MUEIUd", "02314GEE": "BBU5900C",
    "34060599": "10300Mb/s-1310nm-10km",
    "34060713": "10300Mb/s-1310nm-1km",
    "34061940": "25750Mb/s-1310nm-0.3km"
}

# Limpieza automática del mapa para que no importen los ceros
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Cloud Final", layout="wide")
st.title("📊 Auditoría de Inventario con Gráficos")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        if 'PN(BOM Code/Item)' in df.columns:
            # Limpieza del dato del archivo
            df['PN_Clean'] = df['PN(BOM Code/Item)'].str.strip().str.lstrip('0')
            # Asignación de nombre o mostrar el PN si es desconocido
            df['Nombre HW'] = df['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro de Sitio
        sitio_sel = st.selectbox("📍 Filtrar por Sitio:", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # --- SECCIÓN DE GRÁFICOS (Recuperada) ---
        st.subheader(f"📈 Distribución de Hardware - {sitio_sel}")
        conteo = df_f['Nombre HW'].value_counts().reset_index()
        conteo.columns = ['Hardware', 'Cantidad']
        
        # Gráfico de barras horizontales
        fig = px.bar(conteo.head(15), x='Cantidad', y='Hardware', orientation='h', 
                     color='Cantidad', color_continuous_scale='Turbo',
                     labels={'Cantidad': 'N° de Unidades', 'Hardware': 'Tipo de Equipo'})
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN DE TABLA ---
        st.subheader("📋 Detalle del Cuadro")
        cols_cuadro = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        cols_validas = [c for c in cols_cuadro if c in df_f.columns]
        
        st.dataframe(df_f[cols_validas], use_container_width=True)

        # --- SECCIÓN DE EXCEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f[cols_validas].to_excel(writer, index=False, sheet_name='Detalle')
        
        st.download_button(
            label="📥 Descargar este cuadro en Excel", 
            data=output.getvalue(), 
            file_name=f"Inventario_{sitio_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error: {e}")
