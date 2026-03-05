import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re

# 1. DICCIONARIO MAESTRO AMPLIADO
HW_MAP = {
    "3059609": "UMPTga3", "3059607": "UMPTga2", "3058543": "UMPTg3",
    "3058626": "UBBPg2", "3058627": "UBBPg3", "3058707": "UBBPg2a",
    "3050BKS": "UBBPg3b", "3050BYF": "UBBPg1a", "2318170": "UBBP",
    "02311VGW": "FANF", "02312JWX": "FANh", "02312JWU": "UPEUh",
    "02312JXA": "UPEUg", "02311TVH": "UPEUe", "02312QKD": "WD2MUEIUd",
    "02314GEE": "BBU5900C", "02312VRC": "RRU5513w", "02314PEF": "RRU5517t",
    "02312XMM": "AAU5339w", "02313GFY": "RRU5512", "02313DMS": "HAAU5323",
    "02313AFM": "RRU5904w", "02311PFF": "RRU5301", "02312CMF": "RRU5904w",
    "02312LWK": "RRU5818", "02312SSQ": "RRU5336E", "34060599": "SFP 10G-10km",
    "34060713": "SFP 10G-1km", "34061940": "SFP 25G-0.3km", "02313URL": "SFP 10G-10km"
}

CLEAN_MAP = {str(k).strip().upper().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Inventario Red Final", layout="wide")
st.title("📊 Auditoría de Hardware (Detalle Completo)")

file = st.file_uploader("Sube el archivo CSV de Inventario", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # 1. EXCLUSIÓN DE ENERGÍA (AC/DC)
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        df_f = df[~df['Board Name'].str.contains("AC|DC|PWR|POWER|PMU|ETP|DCDU", case=False, na=False)].copy()

        # 2. MOTOR DE TRADUCCIÓN
        def traducir_hardware(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip().upper()
            pn_base = re.split(r'[- ]', pn_raw)[0]
            pn_match = re.sub(r'[^A-Z0-9]', '', pn_base).lstrip('0')
            if pn_match in CLEAN_MAP:
                return CLEAN_MAP[pn_match]
            if pn_match.startswith("3406"):
                return f"SFP Genérico ({pn_raw})"
            return f"PN: {pn_raw}"

        df_f['Nombre HW'] = df_f.apply(traducir_hardware, axis=1)

        # 3. INTERFAZ
        sitio_sel = st.selectbox("📍 Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio_sel == "Todos" else df_f[df_f['NEName'] == sitio_sel]

        # Gráfico
        conteo = df_final['Nombre HW'].value_counts().reset_index().head(15)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # --- TABLA DE DETALLE (Con Subrack y Slot recuperados) ---
        st.subheader("📋 Detalle de Equipos Seleccionados")
        cols_mostrar = [
            'NEName', 
            'Nombre HW', 
            'Board Name', 
            'Inventory Unit ID', 
            'Subrack No.', 
            'Slot No.', 
            'SN(Bar Code)'
        ]
        
        # Filtramos solo las que existan en el archivo para evitar errores
        cols_finales = [c for c in cols_mostrar if c in df_final.columns]
        st.dataframe(df_final[cols_finales], use_container_width=True)

        # --- BOTÓN EXCEL (Solo el detalle del cuadro) ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[cols_finales].to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📥 Descargar Excel del Cuadro", 
            data=output.getvalue(), 
            file_name=f"Inventario_{sitio_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
