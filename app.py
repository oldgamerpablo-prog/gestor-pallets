# ============================================================
# MAIN DASHBOARD Y SISTEMA WMS - CÓDIGO COMPLETO Y ACTUALIZADO
# Rama: desarrollo | Incluye: Visor 3D SketchUp, 2D Layout & Analytics
# ============================================================

import base64
import io
import os
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ------------------------------------------------------------
st.set_page_config(
    page_title="WMS Analytics Hub", layout="wide", page_icon="📦"
)

# Constantes globales
MAX_PESO_PALLET = 1200
PESO_MADERA_PALLET = 25

# CSS Personalizado
css_styles = """
<style>
    .main-header {
        background: #1e293b;
        padding: 20px 25px;
        border-radius: 12px 12px 0 0;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 15px;
        margin-bottom: 25px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        margin-top: 5px;
        color: #0f172a;
    }
    .tarjeta-sku {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-top: 12px;
        background: #ffffff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.04);
        font-family: system-ui, -apple-system, sans-serif;
    }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# ------------------------------------------------------------
# 2. INICIALIZACIÓN DE MEMORIA Y ESTADO (SESSION STATE)
# ------------------------------------------------------------
if "menu_seleccion" not in st.session_state:
  st.session_state.menu_seleccion = "📊 Dashboard WMS"

if "df_resultados" not in st.session_state:
  # Datos por defecto si no se carga archivo externo
  datos_inventario = {
      "Codigo_Producto": ["P-1", "H-1", "AD-3", "B-200", "C-300"],
      "Formato_Principal": [
          "Caja de Cartón",
          "Balde Plástico",
          "Tambor Metálico",
          "Caja de Cartón",
          "Balde Plástico",
      ],
      "Stock_Promedio": [600, 250, 100, 0, 1250],
      "Stock_Maximo": [1000, 200, 150, 500, 1000],
      "Unidades_por_Pallet": [50, 50, 10, 25, 50],
      "Altura_Total_Palletizada_cm": [160, 140, 120, 150, 170],
  }
  df = pd.DataFrame(datos_inventario)
  df["Pallets_Requeridos"] = np.ceil(
      df["Stock_Promedio"] / df["Unidades_por_Pallet"].replace(0, 1)
  ).astype(int)
  mask_rev = (df["Stock_Maximo"].isna()) | (
      df["Stock_Maximo"] < df["Stock_Promedio"]
  )
  df["Estado_Calculo"] = np.where(mask_rev, "REVISAR", "OK")
  st.session_state.df_resultados = df

df_resultados = st.session_state.df_resultados
MAPA = {
    "sku": "Codigo_Producto",
    "stock_prom": "Stock_Promedio",
    "unidades_pallet": "Unidades_por_Pallet",
}

# ------------------------------------------------------------
# 3. FUNCIONES AUXILIARES Y GENERADOR DE PLANO 2D
# ------------------------------------------------------------
def generar_grafico_plano_2d(alto_cm, formato):
  fig, ax = plt.subplots(figsize=(2.5, 2.5))
  ax.add_patch(plt.Rectangle((10, 0), 100, 15, color="#8d5b4c", ec="black"))
  alto_dibujo = min(
      max(float(alto_cm if pd.notna(alto_cm) else 150) - 15, 30), 160
  )
  color_carga = (
      "#3b82f6"
      if "Caja" in str(formato)
      else ("#f59e0b" if "Balde" in str(formato) else "#10b981")
  )
  ax.add_patch(
      plt.Rectangle(
          (10, 15),
          100,
          alto_dibujo,
          color=color_carga,
          ec="black",
          alpha=0.85,
      )
  )
  for h in np.linspace(15, 15 + alto_dibujo, 5):
    ax.plot([10, 110], [h, h], color="black", lw=0.8, ls="--")
  ax.set_xlim(0, 120)
  ax.set_ylim(-10, 190)
  ax.axis("off")
  buf = io.BytesIO()
  plt.savefig(buf, format="png", bbox_inches="tight", transparent=True, dpi=100)
  plt.close(fig)
  img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
  return f'<img src="data:image/png;base64,{img_b64}" style="max-height: 110px; border-radius: 6px;"/>'


def generar_tarjeta_sku(fila):
  sku = fila[MAPA["sku"]]
  formato = fila.get("Formato_Principal", "Estándar")
  estado = fila.get("Estado_Calculo", "OK")
  stock = fila.get("Stock_Promedio", 0)
  pallets = fila.get("Pallets_Requeridos", 0)
  alto = fila.get("Altura_Total_Palletizada_cm", 150)
  img_html = generar_grafico_plano_2d(alto, formato)
  color_badge = "#ef4444" if estado in ["REVISAR", "PELIGRO"] else "#10b981"

  return f"""
    <div class="tarjeta-sku" style="display: flex; gap: 20px; align-items: center;">
        <div style="background: #f1f5f9; padding: 6px; border-radius: 8px; text-align: center;">
            {img_html}
            <div style="font-size: 10px; color: #64748b; font-weight: bold; margin-top: 2px;">ESQUEMA 2D</div>
        </div>
        <div style="flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin:0; color:#1e293b; font-size:18px;">📦 SKU: <b>{sku}</b> — <i>{formato}</i></h3>
                <span style="background: {color_badge}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">{estado}</span>
            </div>
            <div style="margin-top: 12px; color:#475569; font-size:14px; display: flex; gap: 20px;">
                <span>Stock Promedio: <b>{stock:,.0f} UN</b></span>
                <span>|</span>
                <span>Pallets Requeridos: <b>{pallets:,}</b></span>
                <span>|</span>
                <span>Altura: <b>{alto} cm</b></span>
            </div>
        </div>
    </div>
    """


# ------------------------------------------------------------
# 4. MENÚ NAVEGACIÓN EN SIDEBAR
# ------------------------------------------------------------
st.sidebar.title("📌 Menú WMS Analytics")
st.session_state.menu_seleccion = st.sidebar.radio(
    "Selecciona una vista:",
    [
        "📊 Dashboard WMS",
        "🔍 Buscador y Alertas",
        "📦 Modelo 3D SketchUp",
        "📐 Configuración y Layout",
    ],
)

# ------------------------------------------------------------
# VISTA 1: DASHBOARD WMS & KPIS
# ------------------------------------------------------------
if st.session_state.menu_seleccion == "📊 Dashboard WMS":
  st.markdown(
      """
    <div class="main-header">
        <div>
            <h2 style="margin:0; font-size: 22px;">WMS Analytics: Ingeniería de Paletizado</h2>
            <p style="margin: 4px 0 0 0; font-size: 13px; color: #94a3b8;">Sistema Integrado de Control de Inventario</p>
        </div>
        <div><span style="background: #10b981; color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold;">SISTEMA ACTIVO</span></div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # Cálculo de KPIs
  total_sku = len(df_resultados)
  sku_con_stock = int((df_resultados["Stock_Promedio"] > 0).sum())
  total_pallets = int(df_resultados["Pallets_Requeridos"].sum())
  revisar = int(
      (
          df_resultados["Estado_Calculo"].str.contains(
              "REVISAR|PELIGRO", na=False
          )
      ).sum()
  )

  st.markdown(
      f"""
    <div class="kpi-container">
        <div class="kpi-card" style="border-left: 4px solid #3b82f6;"><div class="kpi-title">Total SKU</div><div class="kpi-value">{total_sku:,}</div></div>
        <div class="kpi-card" style="border-left: 4px solid #10b981;"><div class="kpi-title">Con Stock</div><div class="kpi-value">{sku_con_stock:,}</div></div>
        <div class="kpi-card" style="border-left: 4px solid #6366f1;"><div class="kpi-title">Pallets Req.</div><div class="kpi-value" style="color: #4f46e5;">{total_pallets:,}</div></div>
        <div class="kpi-card" style="border-left: 4px solid #8b5cf6;"><div class="kpi-title">Posiciones</div><div class="kpi-value" style="color: #7c3aed;">{total_pallets:,}</div></div>
        <div class="kpi-card" style="border-left: 4px solid #ef4444; background: #fef2f2;"><div class="kpi-title" style="color: #dc2626;">Alertas Críticas</div><div class="kpi-value" style="color: #dc2626;">{revisar:,}</div></div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  st.subheader("📋 Resumen de Inventario General")
  st.dataframe(df_resultados, use_container_width=True)

# ------------------------------------------------------------
# VISTA 2: BUSCADOR DE SKUS Y ALERTAS
# ------------------------------------------------------------
elif st.session_state.menu_seleccion == "🔍 Buscador y Alertas":
  st.subheader("🔍 Buscador de Planos y Estado de Palletizado")

  col1, col2 = st.columns([3, 1])
  with col1:
    texto_busqueda = st.text_area(
        "Ingresa los códigos SKU a consultar (separados por enter o comas):",
        placeholder="Ejemplo:\nP-1\nH-1\nAD-3",
        height=100,
    )
  with col2:
    st.write(" ")
    st.write(" ")
    btn_buscar = st.button(
        "🔍 Buscar SKUs", use_container_width=True, type="primary"
    )
    btn_alertas = st.button("🚨 Ver Alertas", use_container_width=True)
    btn_limpiar = st.button("🧹 Limpiar", use_container_width=True)

  if btn_alertas:
    mask = df_resultados["Estado_Calculo"].str.contains(
        "REVISAR|PELIGRO", na=False
    )
    filas = [row for _, row in df_resultados[mask].iterrows()]
    st.warning(f"🚨 Mostrando {len(filas)} Alertas Críticas encontradas:")
    for f in filas:
      st.markdown(generar_tarjeta_sku(f), unsafe_allow_html=True)

  elif btn_buscar and texto_busqueda.strip():
    codigos = [
        c.strip().upper()
        for c in re.split(r"[\n,;\t]+", texto_busqueda)
        if c.strip()
    ]
    serie_sku = (
        df_resultados["Codigo_Producto"].astype(str).str.strip().str.upper()
    )
    filas = [
        df_resultados[serie_sku == c].iloc[0]
        for c in codigos
        if not df_resultados[serie_sku == c].empty
    ]
    no_encontrados = [
        c for c in codigos if df_resultados[serie_sku == c].empty
    ]

    if filas:
      st.success(f"🔍 Mostrando {len(filas)} SKU encontrados:")
      for f in filas:
        st.markdown(generar_tarjeta_sku(f), unsafe_allow_html=True)
    if no_encontrados:
      st.error(
          "⚠️ SKU no encontrados en la base de datos:"
          f" {', '.join(no_encontrados)}"
      )

# ------------------------------------------------------------
# VISTA 3: PESTAÑA DEDICADA MODELO 3D SKETCHUP
# ------------------------------------------------------------
elif st.session_state.menu_seleccion == "📦 Modelo 3D SketchUp":
  st.title("📦 Visor 3D Interactivo - Modelo SketchUp")
  st.markdown(
      "Visualiza e interactúa en 360° con el diseño del modelo 3D exportado"
      " desde SketchUp."
  )

  # URL RAW de GitHub (rama desarrollo con %20 para los espacios)
  URL_MODELO_3D = "https://raw.githubusercontent.com/oldgamerpablo-prog/gestor-pallets/desarrollo/Alexander%20-%201.glb"

  html_visor_3d = f"""
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>

    <div style="text-align: center; font-family: system-ui, -apple-system, sans-serif; margin-top: 10px;">
        <model-viewer 
            src="{URL_MODELO_3D}" 
            alt="Modelo 3D de SketchUp" 
            auto-rotate 
            camera-controls 
            shadow-intensity="1"
            style="width: 100%; height: 550px; background-color: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
        </model-viewer>
        <div style="background: #f1f5f9; padding: 12px; border-radius: 8px; margin-top: 12px; color: #475569; font-size: 13px;">
            💡 <b>Instrucciones de Navegación 3D:</b><br>
            • <b>Rotación:</b> Haz clic izquierdo y arrastra el ratón.<br>
            • <b>Zoom:</b> Usa la rueda del ratón (scroll).<br>
            • <b>Desplazamiento (Pan):</b> Haz clic derecho y arrastra.
        </div>
    </div>
    """

  components.html(html_visor_3d, height=640)

# ------------------------------------------------------------
# VISTA 4: CONFIGURACIÓN Y LAYOUT
# ------------------------------------------------------------
elif st.session_state.menu_seleccion == "📐 Configuración y Layout":
  st.title("📐 Configuración de Almacén y Layout")
  st.info(
      "Parámetros físicos y reglas de paletizado del centro de distribución."
  )
  col_a, col_b = st.columns(2)
  with col_a:
    st.number_input("Peso Máximo por Pallet (kg):", value=MAX_PESO_PALLET)
    st.number_input("Peso Base Pallet Madera (kg):", value=PESO_MADERA_PALLET)
  with col_b:
    st.selectbox(
        "Orientación Principal de Racks:", ["Horizontal (X)", "Vertical (Y)"]
    )
    st.number_input("Ancho Pasillo Grúa (m):", value=3.0)
