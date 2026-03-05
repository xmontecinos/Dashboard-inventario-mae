import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. DICCIONARIO MAESTRO AMPLIADO (Basado en tus listas)
HW_MAP = {
    "3059609": "UMPTga3", "03059609": "UMPTga3",
    "3058626": "UBBPg2", "03058626": "UBBPg2",
    "3050BKS": "UBBPg3b", "03050BKS": "UBBPg3b",
    "3050BYF": "UBBPg1a", "03050BYF": "UBBPg1a",
    "3058627": "UBBPg3", "03058627": "UBBPg3",
    "3058707": "UBBPg2a", "03058707": "UBBPg2a",
    "3059607": "UMPTga2", "03059607": "UMPTga2",
    "02311VGW": "FANF", "02312JWX": "FANh"
}

# Limpieza del mapa para match perfecto
CLEAN_MAP = {str(k).strip().lstrip('0'): v for k, v in HW_MAP.items()}

st.set_page_config(page_title="Auditoría Pro", layout="wide")
st.title("📊 Inventario de Red (Filtrado y Mapeado)")

file = st.file_uploader("Sube el archivo CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', dtype=str)
        df.columns = df.columns.str.strip()

        # --- PASO 1: EXCLUIR AC/DC ---
        df['Board Name'] = df['Board Name'].fillna('').astype(str)
        palabras_pwr = ["AC", "DC", "PWR", "POWER", "PMU", "ETP", "DCDU", "PDF", "CHASSIS"]
        patron_pwr = '|'.join(palabras_pwr)
        df_f = df[~df['Board Name'].str.contains(patron_pwr, case=False, na=False)].copy()

        # --- PASO 2: MAPEO INTELIGENTE ---
        def traducir_hw(row):
            pn_raw = str(row.get('PN(BOM Code/Item)', '')).strip()
            board = str(row.get('Board Name', '')).upper()
            
            # Limpieza para el diccionario
            pn_clean = pn_raw.split('-')[0].lstrip('0')
            
            # A. Buscar en el diccionario
            if pn_clean in CLEAN_MAP:
                return CLEAN_MAP[pn_clean]
            
            # B. Identificación automática de SFPs (Códigos que inician con 3406)
            if pn_clean.startswith("3406"):
                if "10G" in board or "10300" in board: return "SFP 10G"
                if "25G" in board or "25750" in board: return "SFP 25G"
                return f"SFP Genérico ({pn_clean})"
            
            # C. Si nada funciona, mostrar el PN
            return f"PN: {pn_raw}"

        df_f['Nombre HW'] = df_f.apply(traducir_hw, axis=1)

        # --- INTERFAZ ---
        st.sidebar.metric("Equipos Filtrados", len(df_f))
        
        sitio = st.selectbox("📍 Sitio:", ["Todos"] + sorted(df_f['NEName'].unique().tolist()))
        df_final = df_f if sitio == "Todos" else df_f[df_f['NEName'] == sitio]

        # Gráfico
        st.subheader("📈 Distribución de Hardware")
        conteo = df_final['Nombre HW'].value_counts().reset_index().head(20)
        conteo.columns = ['Hardware', 'Cantidad']
        st.plotly_chart(px.bar(conteo, x='Cantidad', y='Hardware', orientation='h', color='Cantidad'), use_container_width=True)

        # Tabla (Incluyendo Inventory Unit ID)
        st.subheader("📋 Detalle del Cuadro")
        cols_v = ['NEName', 'Nombre HW', 'Board Name', 'Inventory Unit ID', 'SN(Bar Code)']
        st.dataframe(df_final[[c for c in cols_v if c in df_final.columns]], use_container_width=True)

        # Excel (Solo el cuadro)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[[c for c in cols_v if c in df_final.columns]].to_excel(writer, index=False, sheet_name='Detalle')
        st.download_button("📥 Descargar Excel", output.getvalue(), file_name=f"Inventario_{sitio}.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
