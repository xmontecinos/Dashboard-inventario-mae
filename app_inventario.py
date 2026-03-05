import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO AMPLIADO (Basado en tus reportes)
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a",
    "02312QKD": "WD2MUEIUd", "02314GEE": "BBU5900C", "02311VGW": "FANF", 
    "02312JWX": "FANh", "02312JXA": "UPEUg", "02311TVH": "UPEUe",
    "02312JWU": "UPEUh", "02312VRC": "RRU5513w", "02314PEF": "RRU5517t",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "02313DMS": "HAAU5323",
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "02314SVV": "RRU5935E",
    "02314UUR": "RRU5336E", "02312RXX": "RRU5304w", "02312PMH": "RRU5901",
    "02312TNN": "AAU5339w", "02312VNR": "RHUB5963e", "02314MUJ": "pRRU5633GR",
    "02313AAR": "HAAU5222", "02314RER": "AAU5942", "02312VCW": "AAU5942",
    "02314TCS": "AAU5736", "02312QYQ": "AAU5639w",
    # SFPs 
    "34060599": "10300Mb/s-1310nm-10km", "34060713": "10300Mb/s-1310nm-1km",
    "34061940": "25750Mb/s-1310nm-0.3km", "34060290": "1300Mb/s-1310nm-10km",
    "34060473": "1300Mb/s-1310nm-10km", "34060742": "10300Mb/s-1310nm-10km",
    "34061042": "10300Mb/s-1310nm-10km", "34062523": "1200Mb/s-1310nm-10km",
    "34060495": "10300Mb/s-1310nm-10km", "34061630": "11300Mb/s-1310nm-10km",
    "2318170": "10300Mb/s-1310nm-10km", "34060298": "1300Mb/s-1310nm-40km",
    "34060613": "10300Mb/s-1310nm-10km", "02313URL": "10300Mb/s-1310nm-10km",
    "34060484": "2500Mb/s-1310nm-2km", "34060796": "10300Mb/s-1550nm-40km",
    "02313BJH": "10300Mb/s-1310nm-10km", "2315200": "1200Mb/s-1310nm-10km"
}

# Limpieza automática del diccionario para asegurar cruce sin errores de ceros
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Cloud", layout="wide")
st.title("📊 Auditoría de Inventario de Red")

file = st.file_uploader("Sube el archivo CSV Inventory_Board", type=["csv"])

if file:
    try:
        # Carga de datos con codificación flexible
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        if 'PN(BOM Code/Item)' in df.columns:
            # Normalización de Part Numbers del archivo
            df['PN_Clean'] = df['PN(BOM Code/Item)'].str.split('-').str[0] # Elimina sufijos -001, etc.
            df['PN_Clean'] = df['PN_Clean'].str.strip().str.lstrip('0')
            
            # Cruce de datos: si no existe en el mapa, muestra el PN original
            df['Nombre HW'] = df['PN_Clean'].map(CLEAN_MAP).fillna("PN: " + df['PN(BOM Code/Item)'])

        # Filtro de Sitio interactivo
        sitio_sel = st.selectbox("📍 Filtrar por Sitio (NEName):", ["Todos"] + sorted(df['NEName'].unique().tolist()))
        df_f = df if sitio_sel == "Todos" else df[df['NEName'] == sitio_sel]

        # Gráfica de distribución
        st.subheader(f"Distribución de Hardware en {sitio_sel}")
        resumen = df_f['Nombre HW'].value_counts().reset_index()
        resumen.columns = ['Hardware', 'Cantidad']
        fig = px.bar(resumen.head(20), x='Cantidad', y='Hardware', orientation='h', color='Cantidad', color_continuous_scale='Turbo')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN DE TABLA (Detalle del cuadro) ---
        st.subheader("📋 Detalle de Equipos Seleccionados")
        columnas_cuadro = [
            'NEName', 
            'Nombre HW', 
            'Board Name', 
            'Inventory Unit ID', 
            'Subrack No.', 
            'Slot No.',
            'SN(Bar Code)'
        ]
        
        # Filtramos columnas que realmente existan en el archivo subido
        cols_finales = [c for c in columnas_cuadro if c in df_f.columns]
        st.dataframe(df_f[cols_finales], use_container_width=True)

        # --- SECCIÓN DE DESCARGA (Solo el detalle del cuadro) ---
        df_excel = df_f[cols_finales]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Inventario_Filtrado')
            
            # Ajuste automático de ancho de columnas en Excel
            worksheet = writer.sheets['Inventario_Filtrado']
            for i, col in enumerate(df_excel.columns):
                column_len = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

        st.download_button(
            label="📥 Descargar Excel (Solo lo que muestra el cuadro)",
            data=output.getvalue(),
            file_name=f"Inventario_{sitio_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Se produjo un error al procesar el archivo: {e}")
