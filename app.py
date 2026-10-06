import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DEL ENTORNO
st.set_page_config(page_title="Control Tower - Logística", page_icon="🚢", layout="wide")
st.title("🚢 Torre de Control Logística (Entorno Seguro)")
st.markdown("---")

# 2. MOTOR DE CACHÉ Y LIMPIEZA (Optimización tipo Power BI)
@st.cache_data
def load_and_clean_data(file):
    df = pd.read_excel(file, sheet_name='Consolidado')
    
    # Data Masking (Protección de Sourcing)
    columnas_sensibles = ['Acreedor', 'Costo', 'Valor FOB', 'Precio', 'Material']
    df = df.drop(columns=[c for c in columnas_sensibles if c in df.columns])
    
    if 'Nombre del Proveedor' in df.columns:
        df['Nombre del Proveedor'] = 'Proveedor_' + (df.groupby('Nombre del Proveedor').ngroup() + 1).astype(str)
        
    if 'CRD Negociada' in df.columns:
        df['CRD Negociada'] = pd.to_datetime(df['CRD Negociada'], errors='coerce').dt.date
        
    # Limpiar nulos en columnas categóricas para evitar errores en filtros
    cols_categoricas = ['PAIS', 'Status Corona', 'Sistema de Alertas Tempranas (EWS)', 'Atraso principal']
    for col in cols_categoricas:
        if col in df.columns:
            df[col] = df[col].fillna('Sin Definir').astype(str)
            
    return df

# 3. BARRA LATERAL: INGESTA Y PARÁMETROS (SLICERS)
st.sidebar.header("📥 Ingesta de Data Maestra")
uploaded_file = st.sidebar.file_uploader("Cargue su hoja 'Consolidado' (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cargar datos
        df_raw = load_and_clean_data(uploaded_file)
        
        # --- SECCIÓN DE FILTROS DINÁMICOS (Tipo Power BI) ---
        st.sidebar.markdown("### 🎛️ Filtros de Navegación")
        
        df_filtered = df_raw.copy()
        
        # Filtro 1: Sistema EWS
        if 'Sistema de Alertas Tempranas (EWS)' in df_filtered.columns:
            opciones_ews = df_filtered['Sistema de Alertas Tempranas (EWS)'].unique().tolist()
            seleccion_ews = st.sidebar.multiselect("🚨 Filtro EWS", opciones_ews, default=opciones_ews)
            if seleccion_ews:
                df_filtered = df_filtered[df_filtered['Sistema de Alertas Tempranas (EWS)'].isin(seleccion_ews)]
                
        # Filtro 2: Status Corona (Estado Operativo)
        if 'Status Corona' in df_filtered.columns:
            opciones_status = df_filtered['Status Corona'].unique().tolist()
            seleccion_status = st.sidebar.multiselect("📌 Status Operativo", opciones_status, default=opciones_status)
            if seleccion_status:
                df_filtered = df_filtered[df_filtered['Status Corona'].isin(seleccion_status)]
                
        # Filtro 3: País de Origen
        if 'PAIS' in df_filtered.columns:
            opciones_pais = df_filtered['PAIS'].unique().tolist()
            seleccion_pais = st.sidebar.multiselect("🌍 País de Origen", opciones_pais, default=opciones_pais)
            if seleccion_pais:
                df_filtered = df_filtered[df_filtered['PAIS'].isin(seleccion_pais)]
                
        # Filtro 4: Causa Raíz de Atraso
        if 'Atraso principal' in df_filtered.columns:
            opciones_atraso = df_filtered['Atraso principal'].unique().tolist()
            seleccion_atraso = st.sidebar.multiselect("⚠️️ Responsable Desviación", opciones_atraso, default=opciones_atraso)
            if seleccion_atraso:
                df_filtered = df_filtered[df_filtered['Atraso principal'].isin(seleccion_atraso)]

        # ==================================================
        # 4. RENDERIZADO DE DASHBOARD EJECUTIVO
        # ==================================================
        
        # Cálculo de KPIs basados en la data FILTRADA
        total_pos = df_filtered['Contrato Marco'].nunique() if 'Contrato Marco' in df_filtered.columns else len(df_filtered)
        
        if 'Sistema de Alertas Tempranas (EWS)' in df_filtered.columns:
            total_alertas = len(df_filtered[df_filtered['Sistema de Alertas Tempranas (EWS)'] == 'AVISAR'])
        else:
            total_alertas = 0

        # Tarjetas (KPI Cards)
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Contratos (PO) Seleccionados", total_pos)
        col2.metric("🚨 Excepciones EWS en Selección", total_alertas, delta_color="inverse")
        
        st.markdown("---")
        
        # GRÁFICOS INTERACTIVOS
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### Análisis de Causa Raíz (Excepciones)")
            if 'Atraso principal' in df_filtered.columns:
                df_atrasos = df_filtered[df_filtered['Atraso principal'] != 'Sin Definir']['Atraso principal'].value_counts().reset_index()
                df_atrasos.columns = ['Agente Responsable', 'Frecuencia']
                if not df_atrasos.empty:
                    fig_bar = px.bar(df_atrasos, x='Agente Responsable', y='Frecuencia', 
                                     color='Agente Responsable', text_auto=True,
                                     color_discrete_sequence=px.colors.qualitative.Set1)
                    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cant. Casos")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sin desviaciones en la selección actual.")
            
        with col_graf2:
            st.markdown("#### Distribución de Estatus Operativo")
            if 'Status Corona' in df_filtered.columns:
                df_status = df_filtered['Status Corona'].value_counts().reset_index()
                df_status.columns = ['Estatus', 'Cantidad']
                fig_donut = px.pie(df_status, values='Cantidad', names='Estatus', hole=0.4,
                                   color_discrete_sequence=px.colors.sequential.Blues_r)
                st.plotly_chart(fig_donut, use_container_width=True)

        # TABLA DE DETALLE (Grid)
        st.markdown("### 📋 Matriz de Detalle Operativo")
        cols_mostrar = ['Contrato Marco', 'Nombre del Proveedor', 'PAIS', 'Status Corona', 
                        'CRD Negociada', 'Sistema de Alertas Tempranas (EWS)', 'Atraso principal']
        columnas_finales = [c for c in cols_mostrar if c in df_filtered.columns]
        
        # Dataframe interactivo tipo matriz de PBI
        st.dataframe(df_filtered[columnas_finales], use_container_width=True, height=300)

    except Exception as e:
        st.error(f"Falla crítica en el procesamiento del modelo de datos: {e}")
else:
    st.info("👈 Por favor, arrastre su matriz 'Consolidado' en el menú lateral para iniciar la Torre de Control.")
