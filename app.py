import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración del Entorno y UI
st.set_page_config(page_title="Control Tower - Anonimizada", layout="wide")
st.title("🚢 Torre de Control Logística (Entorno de Prueba Seguro)")
st.markdown("---")

# 2. Módulo de Ingesta de Datos
st.sidebar.header("📥 Carga de Data Maestra")
st.sidebar.info("Modo Seguro: Los datos de Sourcing serán enmascarados automáticamente.")
uploaded_file = st.sidebar.file_uploader("Cargue su hoja 'Consolidado' (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Lectura del archivo en memoria RAM temporal
        df = pd.read_excel(uploaded_file, sheet_name='Consolidado')
        
        # ==================================================
        # 🛡️ MÓDULO DE DATA MASKING (PROTECCIÓN SOURCING)
        # ==================================================
        # Columnas críticas que el sistema destruirá o anonimizará
        columnas_sensibles_eliminar = ['Acreedor', 'Costo', 'Valor FOB', 'Precio', 'Material']
        
        # Eliminar datos financieros o de material directo
        columnas_a_borrar = [col for col in columnas_sensibles_eliminar if col in df.columns]
        if columnas_a_borrar:
            df = df.drop(columns=columnas_a_borrar)
        
        # Enmascarar el Nombre del Proveedor (Sustituir por alias genérico)
        if 'Nombre del Proveedor' in df.columns:
            # Agrupa a los proveedores y les asigna un número secuencial (ej. Proveedor_1)
            df['Nombre del Proveedor'] = 'Proveedor_' + (df.groupby('Nombre del Proveedor').ngroup() + 1).astype(str)

        # Formateo de fechas críticas para medición de Lead Time
        if 'CRD Negociada' in df.columns:
            df['CRD Negociada'] = pd.to_datetime(df['CRD Negociada'], errors='coerce').dt.date

        st.success("✅ Base de datos cargada. Protocolo de Data Masking aplicado: Riesgo Sourcing mitigado.")
        # ==================================================

        # 3. Cálculo de KPIs Logísticos de Alto Nivel
        total_pos = df['Contrato Marco'].nunique() if 'Contrato Marco' in df.columns else len(df)
        
        if 'Sistema de Alertas Tempranas (EWS)' in df.columns:
            alertas_ews = df[df['Sistema de Alertas Tempranas (EWS)'] == 'AVISAR']
            total_alertas = len(alertas_ews)
        else:
            alertas_ews = pd.DataFrame()
            total_alertas = 0

        # 4. Renderizado de Tarjetas Ejecutivas
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Contratos (PO) en Tránsito", total_pos)
        col2.metric("🚨 Excepciones EWS Activas", total_alertas, delta_color="inverse")
        
        # 5. Dashboarding: Análisis de Desviaciones
        st.markdown("### 📊 Análisis de Causa Raíz (Excepciones)")
        if 'Atraso principal' in df.columns:
            df_atrasos = df['Atraso principal'].value_counts().reset_index()
            df_atrasos.columns = ['Agente Responsable', 'Frecuencia de Desviación']
            
            # Gráfico de barras interactivo
            fig = px.bar(df_atrasos, x='Agente Responsable', y='Frecuencia de Desviación', 
                         title="Concentración de Cuellos de Botella Logísticos",
                         color='Agente Responsable', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se detectó la métrica 'Atraso principal' para mapear desviaciones.")

        # 6. Panel Táctico para Despachadores (Forwarders)
        st.markdown("### ⚠️ Panel Táctico: Órdenes con Alerta EWS (Anonimizado)")
        if not alertas_ews.empty:
            cols_vista = ['Contrato Marco', 'Nombre del Proveedor', 'PAIS', 'Status Corona', 'CRD Negociada']
            columnas_mostrar = [c for c in cols_vista if c in df.columns]
            st.dataframe(alertas_ews[columnas_mostrar], use_container_width=True)
        else:
            st.info("Tránsito fluido: No se registran alertas operativas en este corte.")

    except Exception as e:
        st.error(f"Falla en la ingesta del archivo matriz: {e}")
else:
    st.info("En espera de datos... Arrastre su matriz 'Consolidado' para iniciar el motor analítico.")
