import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import math
import re
import unicodedata
import io

# ============================================================
# 1. CONFIGURACIÓN INICIAL Y MEMORIA
# ============================================================
st.set_page_config(page_title="WMS Analytics Hub", layout="wide", page_icon="🏢")

MAX_PESO_PALLET = 1200
PESO_MADERA_PALLET = 25

if "menu_seleccion" not in st.session_state: st.session_state.menu_seleccion = "🏠 Portada Principal"
if "skus_activos" not in st.session_state: st.session_state.skus_activos = []
if "skus_invalidos" not in st.session_state: st.session_state.skus_invalidos = []
if "df_original" not in st.session_state: st.session_state.df_original = None
if "df_resultados" not in st.session_state: st.session_state.df_resultados = None
if "mapa_columnas" not in st.session_state: st.session_state.mapa_columnas = None

parametros_layout = {
    'l_bod': 50.0, 'a_bod': 40.0, 'alt_bod': 7.0,
    'cant_pilares_x': 4, 'cant_pilares_y': 1, 'dist_pilares_x': 20.0, 'dist_pilares_y': 15.0,
    'ofi_pos_x': 0.0, 'ofi_pos_y': 0.0, 'ofi_largo': 10.0, 'ofi_ancho': 5.0, 'ofi_alto': 3.5,
    'pallets_viga': 2, 'peso_max_pallet': 2000.0,
    'tipo_flujo': 'Flujo en I (Línea Recta)', 'ancho_porton': 6.0, 'orientacion_rack': 'Horizontal (X)',
    'pasillo': 3.0, 'cant_pas_trans': 0, 'ancho_pas_trans': 3.0,
    'alt_grua': 10.5, 'peso_max_grua': 1500.0,
    'cant_ptas_norte': 0, 'w_ptas_norte': 6.0, 'cant_ptas_sur': 0, 'w_ptas_sur': 6.0,
    'cant_ptas_este': 0, 'w_ptas_este': 6.0, 'cant_ptas_oeste': 0, 'w_ptas_oeste': 6.0,
    'fuente_datos': 'Data Original', 'filtro_sublayout': 'TODOS',
    'chk_a': True, 'chk_b': True, 'chk_c': True, 'modo_vista_color': '3 Zonas (ABC)'
}
for k, v in parametros_layout.items():
    if k not in st.session_state: st.session_state[k] = v

if "layout_generado" not in st.session_state: st.session_state.layout_generado = False
if "res_layout_actual" not in st.session_state: st.session_state.res_layout_actual = None
if "mostrar_3d_layout" not in st.session_state: st.session_state.mostrar_3d_layout = False
if "kpi_layout_capacidad" not in st.session_state: st.session_state.kpi_layout_capacidad = 0
if "kpi_layout_ubicados" not in st.session_state: st.session_state.kpi_layout_ubicados = 0

css_styles = """
<style>
    .box-3d { transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: crosshair; }
    .box-3d:hover { transform: scale(1.08) translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.4) !important; z-index: 100 !important; filter: brightness(1.1); }
    .cota-linea, .cota-linea-v { position: absolute; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #475569; font-weight: bold; background-repeat: no-repeat; }
    .cota-linea { border-left: 1px solid #64748b; border-right: 1px solid #64748b; background-image: linear-gradient(#64748b, #64748b); background-size: 100% 1px; background-position: center; }
    .cota-linea-v { border-top: 1px solid #64748b; border-bottom: 1px solid #64748b; background-image: linear-gradient(#64748b, #64748b); background-size: 1px 100%; background-position: center; flex-direction: column; }
    .cota-texto { background: white; padding: 2px 4px; border-radius: 3px; z-index: 2; }
    .kpi-box { background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #0f172a; }
    .kpi-box-danger { background: #fef2f2 !important; border: 1px solid #fecaca !important; }
    .kpi-value-danger { color: #dc2626 !important; }
</style>
"""

color_styles = """
<style>
    .hero-container-color { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0369a1 100%); border-radius: 16px; padding: 50px 30px; text-align: center; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25); margin-bottom: 35px; }
    .hero-title-color { font-size: 3.6rem; font-weight: 900; color: #ffffff; letter-spacing: -1px; margin-bottom: 14px; text-align: center; }
    .hero-subtitle-color { color: #e2e8f0; font-size: 1.25rem; font-weight: 400; max-width: 850px; margin: 0 auto; line-height: 1.6; text-align: center; }
    .color-card { background: #ffffff; border-radius: 14px; padding: 25px; height: 230px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05); transition: all 0.3s ease; margin-bottom: 15px; border-top: 5px solid #2563eb; }
    .color-card-green { border-top-color: #059669; }
    .color-card-purple { border-top-color: #7c3aed; }
    .color-card-amber { border-top-color: #d97706; }
    .color-card-rose { border-top-color: #e11d48; }
    .color-card:hover { box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12); transform: translateY(-4px); }
    .card-icon-header { display: flex; align-items: center; justify-content: space-between; }
    .card-icon { font-size: 2rem; }
    .card-tag-color { font-size: 0.72rem; font-weight: 800; padding: 4px 12px; border-radius: 20px; letter-spacing: 0.5px; }
    .tag-blue { background: #dbeafe; color: #1e40af; }
    .tag-green { background: #d1fae5; color: #065f46; }
    .tag-purple { background: #ede9fe; color: #5b21b6; }
    .tag-soon { background: #f1f5f9; color: #64748b; }
    .color-card-title { color: #0f172a; font-size: 1.25rem; font-weight: 800; margin: 10px 0 6px 0; }
    .color-card-desc { color: #475569; font-size: 0.9rem; line-height: 1.45; margin: 0; }
</style>
"""

# ============================================================
# 2. FUNCIONES CORE
# ============================================================
def norm_txt(valor):
    texto = "" if valor is None else str(valor)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto.lower().strip())).strip()

def es_numero(valor):
    try: return pd.notna(valor) and math.isfinite(float(valor))
    except: return False

def a_float(valor, default=np.nan):
    try: return float(valor) if pd.notna(valor) else default
    except: return default

def fmt(valor, dec=1): return f"{float(valor):,.{dec}f}" if es_numero(valor) else "N/D"

def encontrar_columna(columnas, incluir, excluir=()):
    for col in columnas:
        n = norm_txt(col)
        if all(p in n for p in incluir) and not any(p in n for p in excluir): return col
    return None

@st.cache_data
def procesar_datos(df_original):
    cols = list(df_original.columns)
    normalizados = {c: norm_txt(c) for c in cols}
    mapa = {}
    mapa["sku"] = encontrar_columna(cols, ["codigo", "producto"]) or encontrar_columna(cols, ["sku"]) or encontrar_columna(cols, ["codigo"])
    mapa["stock"] = encontrar_columna(cols, ["stock", "promedio"])
    mapa["peso"] = encontrar_columna(cols, ["peso"], ["total", "pallet"])
    mapa["formato"] = encontrar_columna(cols, ["formato", "principal"])
    largos = [c for c in cols if "largo" in normalizados[c] and "pallet" not in normalizados[c]]
    anchos = [c for c in cols if "ancho" in normalizados[c] and "pallet" not in normalizados[c]]
    altos = [c for c in cols if "alto" in normalizados[c] and "pallet" not in normalizados[c] and "altura" not in normalizados[c]]
    mapa["largo"] = largos[0] if largos else None
    mapa["ancho"] = anchos[0] if anchos else None
    if mapa["ancho"] is None and len(largos) >= 2: mapa["ancho"] = largos[1]
    mapa["alto"] = altos[0] if altos else None
    mapa["largo_pallet"] = me_lp = encontrar_columna(cols, ["largo", "pallet"])
    mapa["ancho_pallet"] = me_ap = encontrar_columna(cols, ["ancho", "pallet"])
    mapa["altura_pallet"] = encontrar_columna(cols, ["altura", "pallet"], ["total", "paletizada"]) or me_lp or me_ap
    mapa["unidades_pallet"] = encontrar_columna(cols, ["unidades", "pallet"])
    mapa["altura_total"] = encontrar_columna(cols, ["altura", "total", "pallet"]) or me_lp or encontrar_columna(cols, ["altura", "paletizada"])
    
    mapa["abc"] = encontrar_columna(cols, ["abc"], ["xyz"])
    mapa["xyz"] = encontrar_columna(cols, ["xyz"], ["abc"])
    mapa["abc_xyz"] = encontrar_columna(cols, ["abc", "xyz"])
    mapa["familia"] = encontrar_columna(cols, ["familia"])
    mapa["bodega"] = encontrar_columna(cols, ["bodega"])
    mapa["ranking"] = encontrar_columna(cols, ["ranking"])

    df_trabajo = df_original.copy()
    df_trabajo[mapa["sku"]] = df_trabajo[mapa["sku"]].astype(str).str.strip()
    if mapa.get("abc"): df_trabajo[mapa["abc"]] = df_trabajo[mapa["abc"]].fillna("N/D").astype(str).str.strip().str.upper()
    if mapa.get("xyz"): df_trabajo[mapa["xyz"]] = df_trabajo[mapa["xyz"]].fillna("N/D").astype(str).str.strip().str.upper()

    precalculos = df_trabajo.apply(lambda fila: precalcular_fila(fila, mapa), axis=1)
    return pd.concat([df_trabajo, precalculos], axis=1), mapa

def mejor_distribucion_filas(largo, ancho, largo_pallet, ancho_pallet):
    valores = [largo, ancho, largo_pallet, ancho_pallet]
    if not all(es_numero(v) and float(v) > 0 for v in valores): return {"cantidad": 0, "cajas": [], "filas": []}
    largo, ancho, largo_pallet, ancho_pallet = map(float, valores)
    opciones = [{"tipo": "Normal", "largo": largo, "ancho": ancho}, {"tipo": "Cruzada", "largo": ancho, "ancho": largo}]
    mejor = {"cantidad": 0, "filas": []}
    max_normal = int(math.floor(ancho_pallet / opciones[0]["ancho"]))
    max_cruzada = int(math.floor(ancho_pallet / opciones[1]["ancho"]))
    por_fila_normal = int(math.floor(largo_pallet / opciones[0]["largo"]))
    por_fila_cruzada = int(math.floor(largo_pallet / opciones[1]["largo"]))
    for n_normal in range(max_normal + 1):
        for n_cruzada in range(max_cruzada + 1):
            ancho_usado = (n_normal * opciones[0]["ancho"] + n_cruzada * opciones[1]["ancho"])
            if ancho_usado <= ancho_pallet + 1e-9:
                total = (n_normal * por_fila_normal + n_cruzada * por_fila_cruzada)
                if total > mejor["cantidad"]: mejor = {"cantidad": total, "filas": ([opciones[0]] * n_normal) + ([opciones[1]] * n_cruzada)}
    cajas = []
    y = 0.0
    for fila in mejor["filas"]:
        cantidad = int(math.floor(largo_pallet / fila["largo"]))
        for i in range(cantidad): cajas.append({"x": i * fila["largo"], "y": y, "largo": fila["largo"], "ancho": fila["ancho"]})
        y += fila["ancho"]
    return {"cantidad": mejor["cantidad"], "cajas": cajas}

def valor_col(fila, key, mapa):
    col = mapa.get(key)
    return fila[col] if col is not None and col in fila.index else np.nan

def precalcular_fila(fila, mapa):
    capacidad_base = a_float(valor_col(fila, "unidades_pallet", mapa))
    largo, ancho, alto = a_float(valor_col(fila, "largo", mapa)), a_float(valor_col(fila, "ancho", mapa)), a_float(valor_col(fila, "alto", mapa))
    peso_unitario = a_float(valor_col(fila, "peso", mapa))
    largo_pallet, ancho_pallet, altura_pallet = a_float(valor_col(fila, "largo_pallet", mapa), 120), a_float(valor_col(fila, "ancho_pallet", mapa), 120), a_float(valor_col(fila, "altura_pallet", mapa), 15)
    altura_total = a_float(valor_col(fila, "altura_total", mapa))
    layout = mejor_distribucion_filas(largo, ancho, largo_pallet, ancho_pallet)
    unidades_nivel = layout["cantidad"]
    niveles_por_altura = float('inf')
    if all(es_numero(v) and v > 0 for v in [altura_total, altura_pallet, alto]) and altura_total > altura_pallet:
        niveles_por_altura = math.floor((altura_total - altura_pallet) / alto)
    niveles_por_peso = float('inf')
    if es_numero(peso_unitario) and peso_unitario > 0 and unidades_nivel > 0:
        peso_por_nivel = unidades_nivel * peso_unitario
        niveles_por_peso = math.floor((MAX_PESO_PALLET - PESO_MADERA_PALLET) / peso_por_nivel)
    niveles_optimos = min(niveles_por_altura, niveles_por_peso)
    if math.isinf(niveles_optimos) or niveles_optimos <= 0:
        niveles_optimos = max(1, int(round(capacidad_base / unidades_nivel))) if (es_numero(capacidad_base) and unidades_nivel > 0) else 1
    return pd.Series({"Capacidad_Excel": capacidad_base, "Capacidad_Optima": int(unidades_nivel * niveles_optimos), "Unidades_Por_Nivel": unidades_nivel, "Niveles_Optimos": niveles_optimos})

def calcular_metricas_dinamicas(fila, mapa, modo="EXCEL"):
    stock = a_float(valor_col(fila, "stock", mapa), 0)
    cap_excel = a_float(fila.get("Capacidad_Excel"), 0)
    cap_optima = int(fila.get("Capacidad_Optima", 0))
    peso_unitario = a_float(valor_col(fila, "peso", mapa))
    largo = a_float(valor_col(fila, "largo", mapa))
    ancho = a_float(valor_col(fila, "ancho", mapa))
    alto = a_float(valor_col(fila, "alto", mapa))
    largo_pallet = a_float(valor_col(fila, "largo_pallet", mapa), 120)
    ancho_pallet = a_float(valor_col(fila, "ancho_pallet", mapa), 120)
    altura_pallet = a_float(valor_col(fila, "altura_pallet", mapa), 15)
    altura_total = a_float(valor_col(fila, "altura_total", mapa))
    
    if modo == "OPTIMO": cap_usada = cap_optima if cap_optima > 0 else int(round(cap_excel)) if es_numero(cap_excel) else 0
    else: cap_usada = int(round(cap_excel)) if (es_numero(cap_excel) and cap_excel > 0) else cap_optima

    pallets = int(math.ceil(stock / cap_usada)) if stock > 0 and cap_usada > 0 else 0
    ult_unids = (stock - (pallets - 1) * cap_usada) if pallets > 0 else 0
    if ult_unids == 0 and stock > 0: ult_unids = cap_usada
    ult_pct = (ult_unids / cap_usada * 100) if cap_usada > 0 else 0

    pallets_completos = pallets - 1 if pallets > 0 and ult_unids < cap_usada else pallets
    unidades_sobrante = 0 if ult_unids == cap_usada else ult_unids
    peso_pallet = (cap_usada * peso_unitario) + PESO_MADERA_PALLET if es_numero(peso_unitario) else np.nan
    diferencia = (cap_optima - cap_excel) if es_numero(cap_excel) else 0
    vol_prod = (largo * ancho * alto * cap_usada) if all(es_numero(v) for v in [largo, ancho, alto]) else np.nan
    vol_pallet = (largo_pallet * ancho_pallet * (altura_total - altura_pallet)) if all(es_numero(v) for v in [largo_pallet, ancho_pallet, altura_total, altura_pallet]) else np.nan
    efi_vol = (vol_prod / vol_pallet * 100) if es_numero(vol_prod) and es_numero(vol_pallet) and vol_pallet > 0 else np.nan

    estado = "OK"
    if stock <= 0: estado = "SIN STOCK"
    elif cap_usada <= 0: estado = "REVISAR DATOS"
    elif es_numero(peso_pallet) and peso_pallet > MAX_PESO_PALLET: estado = "⚠️ PELIGRO: SOBREPESO (>1200kg)"
    elif modo == "EXCEL" and abs(diferencia) > 0: estado = f"⚠️ EXCEL: {int(cap_excel)}u | ÓPTIMO: {cap_optima}u"

    return {"Capacidad_Usada": cap_usada, "Pallets": pallets, "Unidades_Ultimo": ult_unids, "Ocupacion_Ultimo": ult_pct, "Peso_Pallet": peso_pallet, "Estado": estado, "Cap_Excel": cap_excel, "Cap_Optima": cap_optima, "Eficiencia_Volumen": efi_vol, "Pallets_Completos": pallets_completos, "Unidades_Sobrante": unidades_sobrante, "Stock": stock}

def generar_excel_descarga(df_original, df_resultados, mapa):
    output = io.BytesIO()
    comparativo_rows = []
    for _, row in df_resultados.iterrows():
        m_ex = calcular_metricas_dinamicas(row, mapa, "EXCEL")
        m_op = calcular_metricas_dinamicas(row, mapa, "OPTIMO")
        sku_val = row[mapa["sku"]] if mapa.get("sku") else "N/D"
        fam_val = row.get(mapa.get("familia"), "N/D")
        rank_val = row.get(mapa.get("ranking"), "N/D")
        abc_val = row.get(mapa.get("abc"), "N/D")
        xyz_val = row.get(mapa.get("xyz"), "N/D")
        abc_xyz_val = row.get(mapa.get("abc_xyz"), "N/D")
        bodega_val = row.get(mapa.get("bodega"), "N/D")
        formato_val = row.get(mapa.get("formato"), "N/D")
        dif = m_op["Cap_Optima"] - m_ex["Cap_Excel"] if es_numero(m_ex["Cap_Excel"]) else m_op["Cap_Optima"]
        comparativo_rows.append({
            "SKU": sku_val, "Familia": fam_val, "Ranking": rank_val, "Clasificacion_ABC": abc_val, "Clasificacion_XYZ": xyz_val, "Matriz_ABC_XYZ": abc_xyz_val, "Bodega": bodega_val, "Formato": formato_val, "Stock": m_ex["Stock"], "Capacidad_Excel": m_ex["Cap_Excel"], "Capacidad_Optima": m_op["Cap_Optima"], "Diferencia_Unidades": dif, "Pallets_Totales_Excel": m_ex["Pallets"], "Pallets_Completos_Excel": m_ex["Pallets_Completos"], "Unidades_Sobrante_Excel": m_ex["Unidades_Sobrante"], "Pallets_Totales_Optimo": m_op["Pallets"], "Pallets_Completos_Optimo": m_op["Pallets_Completos"], "Unidades_Sobrante_Optimo": m_op["Unidades_Sobrante"], "Peso_Pallet_Excel_kg": m_ex["Peso_Pallet"], "Peso_Pallet_Optimo_kg": m_op["Peso_Pallet"], "Eficiencia_Vol_Excel_%": m_ex["Eficiencia_Volumen"], "Eficiencia_Vol_Optimo_%": m_op["Eficiencia_Volumen"], "Estado_Excel": m_ex["Estado"], "Estado_Optimo": m_op["Estado"]
        })
    df_sheet1 = pd.DataFrame(comparativo_rows)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sheet1.to_excel(writer, sheet_name="1_Analisis_Comparativo", index=False)
        df_original.loc[df_resultados.index].copy().to_excel(writer, sheet_name="2_Data_Original_Filtr", index=False)
        df_resultados.to_excel(writer, sheet_name="3_Data_Optimizada_Filtr", index=False)
    output.seek(0)
    return output

def generar_wms_excel(df_base, almacen, mapa):
    posiciones_por_sku = {}
    for slot in almacen:
        if slot['ocupado']:
            sku = str(slot['sku']).upper()
            if sku not in posiciones_por_sku: posiciones_por_sku[sku] = []
            posiciones_por_sku[sku].append(slot['id_posicion'])
    df_export = df_base.copy()
    def get_pos(s):
        s = str(s).strip().upper()
        if s in posiciones_por_sku: return ", ".join(posiciones_por_sku[s])
        return "Sin Ubicar (Falta Capacidad / Demanda 0)"
    col_sku = mapa.get("sku", df_export.columns[0])
    df_export['Posiciones_Layout_WMS'] = df_export[col_sku].apply(get_pos)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name="Reporte_WMS", index=False)
    output.seek(0)
    return output

# ============================================================
# 3. FUNCIONES VISUALES 2D / 3D (CUBICADORA)
# ============================================================
def es_formato_circular(formato):
    if pd.isna(formato): return False
    return any(k in norm_txt(formato) for k in ["tambor", "balde", "bidon", "cunete", "barril", "tarro", "lata", "cilindro"])

def get_material_css(formato):
    n = norm_txt(formato)
    if any(k in n for k in ["tambor", "balde", "bidon", "lata", "cilindro"]): return {"bg_top": "radial-gradient(circle at 35% 35%, #93c5fd, #1d4ed8)", "bg_side": "linear-gradient(to right, #1e3a8a, #60a5fa 30%, #3b82f6 60%, #1e3a8a)", "border": "#1e3a8a", "radius": "50%", "shadow": "inset -3px -3px 6px rgba(0,0,0,0.4), 2px 3px 5px rgba(0,0,0,0.25)"}
    if "bin" in n or "cubeta" in n: return {"bg_top": "linear-gradient(135deg, #34d399, #059669)", "bg_side": "linear-gradient(to bottom, #34d399, #059669)", "border": "#064e3b", "radius": "6px", "shadow": "inset -2px -2px 5px rgba(0,0,0,0.3), inset 2px 2px 3px rgba(255,255,255,0.4), 2px 3px 4px rgba(0,0,0,0.2)"}
    return {"bg_top": "linear-gradient(135deg, #e5c07b, #c6893f)", "bg_side": "linear-gradient(to bottom, #d4a373, #a67232)", "border": "#8b5a2b", "radius": "2px", "shadow": "inset -2px -2px 4px rgba(0,0,0,0.2), inset 1px 1px 2px rgba(255,255,255,0.3), 2px 3px 5px rgba(0,0,0,0.2)"}

def html_vista_superior(fila, mapa, cantidad_unidades=None):
    lp, ap = a_float(valor_col(fila, "largo_pallet", mapa), 120), a_float(valor_col(fila, "ancho_pallet", mapa), 120)
    layout = mejor_distribucion_filas(a_float(valor_col(fila, "largo", mapa)), a_float(valor_col(fila, "ancho", mapa)), lp, ap)
    if layout["cantidad"] <= 0: return "<div style='text-align:center; padding:30px;'>Faltan dimensiones.</div>"
    escala = min(220 / lp, 220 / ap, 2.0)
    mat = get_material_css(valor_col(fila, "formato", mapa))
    cajas_a_dibujar = layout["cajas"]
    if cantidad_unidades is not None:
        unids_nivel = layout["cantidad"]
        items_capa = int(cantidad_unidades) % unids_nivel
        if items_capa == 0 and cantidad_unidades > 0: items_capa = unids_nivel
        cajas_a_dibujar = layout["cajas"][:items_capa]
    objetos = [f"<div class='box-3d' style='position:absolute; left:{c['x']*escala:.2f}px; top:{c['y']*escala:.2f}px; width:{c['largo']*escala:.2f}px; height:{c['ancho']*escala:.2f}px; box-sizing:border-box; background:{mat['bg_top']}; border:1px solid {mat['border']}; border-radius:{mat['radius']}; box-shadow:{mat['shadow']}; color:white; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; z-index: 10;'>{i}</div>" for i, c in enumerate(cajas_a_dibujar, 1)]
    pallet_bg = "background-color: #d39e66; background-image: repeating-linear-gradient(90deg, transparent, transparent 15%, rgba(100,50,0,0.15) 15%, rgba(100,50,0,0.15) 17%); box-shadow: 4px 6px 12px rgba(0,0,0,0.25);"
    return f"<div style='position:relative; width:{lp*escala + 30:.2f}px; height:{ap*escala + 30:.2f}px; margin: 10px auto;'><div class='cota-linea' style='top: 0; left: 0; width: {lp*escala}px; height: 10px;'><span class='cota-texto'>{fmt(lp,0)} cm</span></div><div class='cota-linea-v' style='top: 15px; right: 0; width: 10px; height: {ap*escala}px;'><span class='cota-texto' style='transform: rotate(90deg); white-space:nowrap;'>{fmt(ap,0)} cm</span></div><div style='position:absolute; top:15px; left:0; width:{lp*escala:.2f}px; height:{ap*escala:.2f}px; {pallet_bg} border: 2px solid #8b5a2b; border-radius: 4px;'>{''.join(objetos)}</div></div>"

def html_vista_lateral(fila, mapa, cap_usada, total_unidades=None):
    lp, hp, ap = a_float(valor_col(fila, "largo_pallet", mapa), 120), a_float(valor_col(fila, "altura_pallet", mapa), 15), a_float(valor_col(fila, "ancho_pallet", mapa), 120)
    alto, altura_total, largo, ancho = a_float(valor_col(fila, "alto", mapa)), a_float(valor_col(fila, "altura_total", mapa)), a_float(valor_col(fila, "largo", mapa)), a_float(valor_col(fila, "ancho", mapa))
    if not all([es_numero(x) and x > 0 for x in [lp, hp, alto]]): return "<div style='text-align:center; padding:30px;'>Faltan datos.</div>"
    layout = mejor_distribucion_filas(largo, ancho, lp, ap)
    unids_nivel = layout["cantidad"]
    if unids_nivel <= 0: return ""
    target_units = int(cap_usada) if total_unidades is None else int(total_unidades)
    columnas = len([c for c in layout["cajas"] if abs(c["y"]) < 1e-5]) or 1
    niveles_completos = target_units // unids_nivel
    unidades_sobrantes = target_units % unids_nivel
    tot_niveles = niveles_completos + (1 if unidades_sobrantes > 0 else 0)
    cajas_top = len([c for c in layout["cajas"][:unidades_sobrantes] if abs(c["y"]) < 1e-5]) if unidades_sobrantes > 0 else 0
    alto_visual = altura_total if es_numero(altura_total) and altura_total > hp else (hp + max(tot_niveles, 1) * alto)
    escala_x, escala_y = min(220 / lp, 2.0), min(180 / alto_visual, 2.0)
    w, h, caja_w, caja_h = lp * escala_x, alto_visual * escala_y, (lp * escala_x) / columnas, alto * escala_y
    mat = get_material_css(valor_col(fila, "formato", mapa))
    bloques = []
    for nivel in range(niveles_completos):
        for i in range(columnas): bloques.append(f"<div class='box-3d' style='position:absolute; left:{i*caja_w:.2f}px; bottom:{hp*escala_y + nivel*caja_h:.2f}px; width:{caja_w-1:.2f}px; height:{caja_h-1:.2f}px; box-sizing:border-box; background:{mat['bg_side']}; border:1px solid {mat['border']}; border-radius:{mat['radius']}; box-shadow: inset 1px 1px 2px rgba(255,255,255,0.2), 2px 2px 4px rgba(0,0,0,0.3);'></div>")
    for i in range(cajas_top if cajas_top > 0 else (1 if unidades_sobrantes > 0 else 0)): bloques.append(f"<div class='box-3d' style='position:absolute; left:{i*caja_w:.2f}px; bottom:{hp*escala_y + niveles_completos*caja_h:.2f}px; width:{caja_w-1:.2f}px; height:{caja_h-1:.2f}px; box-sizing:border-box; background:{mat['bg_side']}; border:1px solid {mat['border']}; border-radius:{mat['radius']}; box-shadow: inset 1px 1px 2px rgba(255,255,255,0.2), 2px 2px 4px rgba(0,0,0,0.3);'></div>")
    return f"<div style='position:relative; width:{w + 40:.2f}px; height:{h + 30:.2f}px; margin: 10px auto;'><div class='cota-linea-v' style='bottom: 0; left: 0; width: 10px; height: {h}px;'><span class='cota-texto' style='transform: rotate(-90deg); white-space:nowrap;'>{fmt(alto_visual,0)} cm</span></div><div style='position:absolute; left:25px; bottom:0; width:{w:.2f}px; height:{h:.2f}px;'><div style='position:absolute; left:0; bottom:0; width:{w:.2f}px; height:{hp*escala_y:.2f}px; background:#b88252; border:1px solid #754b28; border-radius:2px; box-shadow: 2px 2px 4px rgba(0,0,0,0.3);'><div style='position:absolute; left:18%; bottom:15%; width:22%; height:70%; background:#2c1b12; border-radius:2px;'></div><div style='position:absolute; right:18%; bottom:15%; width:22%; height:70%; background:#2c1b12; border-radius:2px;'></div></div>{''.join(bloques)}<div style='position:absolute; left:0; bottom:{h:.2f}px; width:110%; border-top:2px dashed #ef4444; z-index:20;'></div><div style='position:absolute; right:-25px; bottom:{h-10:.2f}px; font-size:10px; color:#ef4444; font-weight:700;'>MÁX</div></div></div>"

def get_box_cm(x0, y0, z0, dx, dy, dz, color):
    x = [x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0]; y = [y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy]; z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]
    i, j, k = [7,0,0,0,4,4,6,6,4,0,3,2], [3,4,1,2,5,6,5,2,0,1,6,3], [0,7,2,3,6,7,1,1,5,5,7,6]
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=1, showscale=False, hoverinfo='none', flatshading=True)

def crear_cilindro_solido_cm(x0, y0, z0, r, h, color):
    theta = np.linspace(0, 2*np.pi, 24, endpoint=False)
    x, y = x0 + r * np.cos(theta), y0 + r * np.sin(theta)
    x_pts, y_pts = np.concatenate([x, x, [x0, x0]]), np.concatenate([y, y, [y0, y0]])
    z_pts = np.concatenate([np.full(24, z0), np.full(24, z0+h), [z0, z0+h]])
    i, j, k = [], [], []
    for n in range(24):
        nxt = (n+1)%24
        i.extend([n, n]); j.extend([nxt, nxt+24]); k.extend([nxt+24, n+24])
        i.append(48); j.append(nxt); k.append(n); i.append(49); j.append(n+24); k.append(nxt+24)
    return go.Mesh3d(x=x_pts, y=y_pts, z=z_pts, i=i, j=j, k=k, color=color, opacity=1, showscale=False, hoverinfo='none', flatshading=True)

def renderizar_3d_plotly(fila, mapa, cap_usada, total_unidades=None):
    lp, ap, hp = a_float(valor_col(fila, "largo_pallet", mapa), 120), a_float(valor_col(fila, "ancho_pallet", mapa), 120), a_float(valor_col(fila, "altura_pallet", mapa), 15)
    largo, ancho, alto = a_float(valor_col(fila, "largo", mapa)), a_float(valor_col(fila, "ancho", mapa)), a_float(valor_col(fila, "alto", mapa))
    target_units = int(cap_usada) if total_unidades is None else int(total_unidades)
    layout = mejor_distribucion_filas(largo, ancho, lp, ap)
    if layout["cantidad"] <= 0 or target_units <= 0: return go.Figure()
    
    traces = []
    h_deck, h_leg, w_leg = min(3.0, hp * 0.2), hp - min(3.0, hp * 0.2), min(10.0, lp * 0.1)
    traces.extend([get_box_cm(0, 0, h_leg, lp, ap, h_deck, '#c18c5d'), get_box_cm(0, 0, 0, w_leg, ap, h_leg, '#966336'), get_box_cm((lp - w_leg)/2, 0, 0, w_leg, ap, h_leg, '#966336'), get_box_cm(lp - w_leg, 0, 0, w_leg, ap, h_leg, '#966336')])
    
    es_cilindro = es_formato_circular(valor_col(fila, "formato", mapa))
    color_carga = '#2563eb' if es_cilindro else '#d4a373'
    
    units_placed, nivel = 0, 0
    while units_placed < target_units:
        z_base = hp + (nivel * alto)
        for c in layout["cajas"]:
            if units_placed >= target_units: break
            if es_cilindro:
                radio = min(c['largo'], c['ancho']) / 2
                cx, cy = c['x'] + c['largo']/2, c['y'] + c['ancho']/2
                traces.append(crear_cilindro_solido_cm(cx, cy, z_base, radio - 0.2, alto - 0.5, color_carga))
                theta = np.linspace(0, 2*np.pi, 24)
                traces.append(go.Scatter3d(
                    x=cx + (radio - 0.2) * np.cos(theta), y=cy + (radio - 0.2) * np.sin(theta), z=np.full(24, z_base + alto - 0.5),
                    mode='lines', line=dict(color='#1e3a8a', width=3), showlegend=False, hoverinfo='none'
                ))
            else:
                gap = 0.5
                x_c, y_c = c['x'] + gap/2, c['y'] + gap/2
                l_c, a_c = c['largo'] - gap, c['ancho'] - gap
                alt_c = alto - gap/2
                traces.append(get_box_cm(x_c, y_c, z_base, l_c, a_c, alt_c, color_carga))
                x_e = [x_c, x_c+l_c, x_c+l_c, x_c, x_c, None, x_c, x_c+l_c, x_c+l_c, x_c, x_c, None, x_c, x_c, None, x_c+l_c, x_c+l_c, None, x_c+l_c, x_c+l_c, None, x_c, x_c]
                y_e = [y_c, y_c, y_c+a_c, y_c+a_c, y_c, None, y_c, y_c, y_c+a_c, y_c+a_c, y_c, None, y_c, y_c, None, y_c, y_c, None, y_c+a_c, y_c+a_c, None, y_c+a_c, y_c+a_c]
                z_e = [z_base, z_base, z_base, z_base, z_base, None, z_base+alt_c, z_base+alt_c, z_base+alt_c, z_base+alt_c, z_base+alt_c, None, z_base, z_base+alt_c, None, z_base, z_base+alt_c, None, z_base, z_base+alt_c, None, z_base, z_base+alt_c]
                traces.append(go.Scatter3d(x=x_e, y=y_e, z=z_e, mode='lines', line=dict(color='#8b5a2b', width=2), showlegend=False, hoverinfo='none'))
            units_placed += 1
        nivel += 1
        
    fig = go.Figure(data=traces)
    fig.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), aspectmode='data', camera=dict(eye=dict(x=1.6, y=1.6, z=1.0))), margin=dict(r=0, l=0, b=0, t=0), height=300)
    return fig

# ============================================================
# 4. MOTOR DE CÁLCULO LAYOUT 3D 
# ============================================================
def preparar_df_layout(df_base, mapa, modo):
    df_l = pd.DataFrame()
    df_l['SKU'] = df_base[mapa['sku']]
    
    metrics = [calcular_metricas_dinamicas(row, mapa, modo) for _, row in df_base.iterrows()]
    df_l['Cantidad_Pallets'] = [m['Pallets'] for m in metrics]
    df_l['Peso_Pallet_kg'] = [m['Peso_Pallet'] for m in metrics]
    df_l['Pallets_Completos_Optimo'] = [m['Pallets_Completos'] for m in metrics]
    df_l['Unidades_Sobrante_Optimo'] = [m['Unidades_Sobrante'] for m in metrics]
    df_l['Capacidad_Optima'] = [m['Cap_Optima'] for m in metrics]
    
    col_alto_tot = mapa.get('altura_total')
    if col_alto_tot:
        df_l['Alto_m'] = pd.to_numeric(df_base[col_alto_tot], errors='coerce').fillna(120) / 100.0
    else:
        df_l['Alto_m'] = 1.2
        
    col_abc = mapa.get('abc')
    col_xyz = mapa.get('xyz')
    col_abcxyz = mapa.get('abc_xyz')
    col_formato = mapa.get('formato')
    
    df_l['ABC'] = df_base[col_abc].fillna('C').astype(str).str.strip().str.upper() if col_abc else 'C'
    df_l['XYZ'] = df_base[col_xyz].fillna('Z').astype(str).str.strip().str.upper() if col_xyz else 'Z'
    df_l['ABC'] = df_l['ABC'].replace({'N/D': 'C', 'NAN': 'C', 'NONE': 'C', '': 'C'})
    df_l['XYZ'] = df_l['XYZ'].replace({'N/D': 'Z', 'NAN': 'Z', 'NONE': 'Z', '': 'Z'})
    
    if col_abcxyz and col_abcxyz in df_base.columns:
        df_l['ABC_XYZ'] = df_base[col_abcxyz].fillna(df_l['ABC'] + df_l['XYZ']).astype(str).str.strip().str.upper()
    else:
        df_l['ABC_XYZ'] = df_l['ABC'] + df_l['XYZ']
    
    df_l['ABC_XYZ'] = df_l['ABC_XYZ'].replace({'N/D': 'CZ', 'N/DN/D': 'CZ', 'NAN': 'CZ'})
    
    cat_type = pd.CategoricalDtype(categories=['AX', 'AY', 'AZ', 'BX', 'BY', 'BZ', 'CX', 'CY', 'CZ'], ordered=True)
    df_l['ABC_XYZ'] = df_l['ABC_XYZ'].astype(cat_type)
    
    df_l['Formato'] = df_base[col_formato] if col_formato else 'N/D'
    
    return df_l[df_l['Cantidad_Pallets'] > 0].sort_values(by='ABC_XYZ').reset_index(drop=True)

def motor_calculo_layout(df_activa, is_vertical, pal_v, conf):
    l_m, a_m, alt_m = conf['l_bod'], conf['a_bod'], conf['alt_bod']
    w_p, flujo = conf['ancho_porton'], conf['tipo_flujo']
    limite_peso_grua = conf.get('peso_max_grua', 1500.0)
    
    staging_zones = []
    if w_p > 0 and flujo != 'Ninguno':
        if 'Flujo en U' in flujo: staging_zones.extend([{'x1': l_m*0.25 - w_p/2, 'y1': 0, 'x2': l_m*0.25 + w_p/2, 'y2': 6}, {'x1': l_m*0.75 - w_p/2, 'y1': 0, 'x2': l_m*0.75 + w_p/2, 'y2': 6}])
        elif 'Flujo en I' in flujo: staging_zones.extend([{'x1': l_m/2 - w_p/2, 'y1': 0, 'x2': l_m/2 + w_p/2, 'y2': 6}, {'x1': l_m/2 - w_p/2, 'y1': a_m-6, 'x2': l_m/2 + w_p/2, 'y2': a_m}])
        elif 'Flujo en L' in flujo: staging_zones.extend([{'x1': max(1, l_m*0.15 - w_p/2), 'y1': 0, 'x2': max(1, l_m*0.15 - w_p/2)+w_p, 'y2': 6}, {'x1': l_m-6, 'y1': max(1, a_m*0.85 - w_p/2), 'x2': l_m, 'y2': max(1, a_m*0.85 - w_p/2)+w_p}])
    oficinas_list = [{'x': conf['ofi_pos_x'], 'y': conf['ofi_pos_y'], 'w': conf['ofi_largo'], 'd': conf['ofi_ancho'], 'h': conf['ofi_alto']}] if conf['ofi_largo'] > 0 else []
    ap_w, pp_d = 1.2, 1.2
    ap_h = float(df_activa['Alto_m'].max()) if not df_activa.empty else 1.2
    pas_w, c_ptrans, a_ptrans = conf['pasillo'], conf['cant_pas_trans'], conf['ancho_pas_trans'] if conf['cant_pas_trans'] > 0 else 0.0
    virt_l_m, virt_a_m = (a_m, l_m) if is_vertical else (l_m, a_m)
    t_marco, holgura_viga, holgura_lateral, viga_h = 0.10, 0.15, 0.10, 0.12
    l_modulo = (ap_w * pal_v) + (holgura_lateral * (pal_v + 1)) + t_marco
    alt_nivel_viga = ap_h + holgura_viga + viga_h
    niveles_operativos = max(1, sum(1 for n in range(50) if n*alt_nivel_viga+ap_h+0.15 <= alt_m and n*alt_nivel_viga <= conf['alt_grua']))
    ancho_bloque = (pp_d * 2) + pas_w
    filas = math.floor(virt_a_m / ancho_bloque)
    num_secciones = c_ptrans + 1
    modulos_por_seccion = math.floor(((virt_l_m - 4.0 - (c_ptrans * a_ptrans)) / num_secciones) / l_modulo) if num_secciones > 0 else 0
    cx, cy = conf['cant_pilares_x'], conf['cant_pilares_y']
    dp_x, dp_y = conf['dist_pilares_x'], conf['dist_pilares_y']
    dp_x_real, nx = (l_m / (cx + 1), cx) if cx > 0 else (dp_x, math.floor(l_m / dp_x) if dp_x > 0 else 0)
    dp_y_real, ny = (a_m / (cy + 1), cy) if cy > 0 else (dp_y, math.floor(a_m / dp_y) if dp_y > 0 else 0)
    pilares_reales = [(px * dp_x_real, py * dp_y_real) for px in range(1, nx + 1) for py in range(1, ny + 1)]
    virt_pilares = [(py, px) for px, py in pilares_reales] if is_vertical else pilares_reales

    modulos_validos = 0
    modulos_list = []
    almacen = []
    
    for f in range(filas):
        num_pasillo = f + 1
        letra_pasillo = chr(64 + num_pasillo) if num_pasillo <= 26 else f"P{num_pasillo}"
        y_r1, y_r2 = (f * ancho_bloque) + 2.0, (f * ancho_bloque) + 2.0 + pp_d
        for s in range(num_secciones):
            x_inicio = 2.0 + s * (modulos_por_seccion * l_modulo + a_ptrans)
            for m in range(modulos_por_seccion):
                x_pos = x_inicio + (m * l_modulo)
                num_modulo = (s * modulos_por_seccion) + m + 1
                for y_rack in [y_r1, y_r2]:
                    lado = 'A' if y_rack == y_r1 else 'B'
                    rx1, ry1, rx2, ry2 = (y_rack, x_pos, y_rack+pp_d, x_pos+l_modulo) if is_vertical else (x_pos, y_rack, x_pos+l_modulo, y_rack+pp_d)
                    eliminado = False
                    for ofi in oficinas_list:
                        if not (rx2 + 1.5 < ofi['x'] or rx1 - 1.5 > ofi['x'] + ofi['w'] or ry2 + 1.5 < ofi['y'] or ry1 - 1.5 > ofi['y'] + ofi['d']): eliminado = True; break
                    if not eliminado:
                        for st_z in staging_zones:
                            if not (rx2 < st_z['x1'] or rx1 > st_z['x2'] or ry2 < st_z['y1'] or ry1 > st_z['y2']): eliminado = True; break
                    if eliminado: continue
                    bloqueado_pilar = any((x_pos <= px <= x_pos + l_modulo) and (y_rack - 0.25 <= py <= y_rack + pp_d + 0.25) for px, py in virt_pilares)
                    modulos_list.append({'x': x_pos, 'y': y_rack, 'bloqueado': bloqueado_pilar})
                    
                    if not bloqueado_pilar: 
                        modulos_validos += 1
                        for n in range(niveles_operativos):
                            z_piso = 0 if n == 0 else (n * alt_nivel_viga)
                            for p_idx in range(pal_v):
                                x_pal = x_pos + t_marco + holgura_lateral + (p_idx * (ap_w + holgura_lateral))
                                id_pos = f"{letra_pasillo}-{num_modulo:02d}-{n+1}{lado}-{p_idx+1}"
                                almacen.append({
                                    'id_posicion': id_pos, 'letra_pasillo': letra_pasillo, 'pasillo': num_pasillo, 'lado': lado, 'modulo': num_modulo, 'nivel': n+1, 'slot': p_idx+1,
                                    'x': x_pos, 'y': y_rack, 'x_pal': x_pal, 'z': z_piso, 'ocupado': False, 'sku': None, 'abc': None, 'abc_xyz': None, 'alt_p': 0, 'es_cilindro': False, 'es_saldo': False
                                })

    almacen.sort(key=lambda x: (x['letra_pasillo'], x['nivel'], x['x'], x['y']))
    resumen_ubicacion = []
    
    for _, row in df_activa.iterrows():
        sku, cant = str(row['SKU']).strip().upper(), int(row['Cantidad_Pallets'])
        abc_c = str(row.get('ABC', 'C'))
        abc_xyz_c = str(row.get('ABC_XYZ', abc_c + 'Z'))
        alto_real_sku = float(row['Alto_m']) if 'Alto_m' in row else ap_h
        peso_real_pallet = float(row.get('Peso_Pallet_kg', 0))
        forzar_nivel_1 = (peso_real_pallet > limite_peso_grua)

        es_cilindrico = False
        if 'Formato' in row and pd.notna(row['Formato']):
            f_str = str(row['Formato']).lower()
            if 'tambor' in f_str or 'balde' in f_str or 'cilindro' in f_str:
                es_cilindrico = True

        pallets_completos = cant
        alto_sobrante = alto_real_sku
        
        if 'Pallets_Completos_Optimo' in row and pd.notna(row['Pallets_Completos_Optimo']):
            p_comp = row['Pallets_Completos_Optimo']
            u_sob = row.get('Unidades_Sobrante_Optimo', 0)
            if u_sob > 0:
                pallets_completos = int(p_comp)
                u_pp = row.get('Capacidad_Optima', 0)
                if u_pp > 0: alto_sobrante = max(0.3, alto_real_sku * (u_sob / u_pp))
                else: alto_sobrante = max(0.3, alto_real_sku * 0.5)

        ubicados = 0
        for slot in almacen:
            if ubicados >= cant: break
            if not slot['ocupado']:
                if forzar_nivel_1 and slot['nivel'] > 1:
                    continue
                
                alto_final = alto_real_sku if ubicados < pallets_completos else alto_sobrante
                es_saldo = (ubicados >= pallets_completos and pallets_completos < cant)
                
                slot.update({'ocupado': True, 'sku': sku, 'abc': abc_c, 'abc_xyz': abc_xyz_c, 'alt_p': alto_final, 'es_cilindro': es_cilindrico, 'es_saldo': es_saldo})
                ubicados += 1
        resumen_ubicacion.append({'SKU': sku, 'Pedidas': cant, 'Ubicadas': ubicados})

    total_posiciones = len(almacen)
    demanda_total = int(df_activa['Cantidad_Pallets'].sum())
    pallets_ubicados_totales = sum(r['Ubicadas'] for r in resumen_ubicacion)

    st.session_state.kpi_layout_capacidad = total_posiciones
    st.session_state.kpi_layout_ubicados = pallets_ubicados_totales

    return {
        'modulos': modulos_validos, 'niveles': niveles_operativos,
        'capacidad': total_posiciones, 'demanda': demanda_total,
        'diferencia': total_posiciones - demanda_total,
        'staging': staging_zones, 'oficinas': oficinas_list,
        'modulos_list': modulos_list, 'almacen': almacen, 'pilares_reales': pilares_reales,
        'pallets_ubicados_totales': pallets_ubicados_totales,
        'alt_nivel_viga': alt_nivel_viga, 'l_modulo': l_modulo, 't_marco': t_marco,
        'pp_d': pp_d, 'ap_w': ap_w, 'viga_h': viga_h, 'is_vertical': is_vertical
    }

class MallaAgrupada:
    def __init__(self, color, nombre, opacidad=1.0):
        self.color, self.nombre, self.opacidad = color, nombre, opacidad
        self.x, self.y, self.z, self.i, self.j, self.k, self.text = [], [], [], [], [], [], []
        self.contador = 0

    def agregar_cubo(self, x0, y0, z0, dx, dy, dz, hover_txt=None):
        off = len(self.x)
        self.x.extend([x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0])
        self.y.extend([y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy])
        self.z.extend([z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz])
        self.i.extend([idx + off for idx in [7,0,0,0,4,4,6,6,4,0,3,2]])
        self.j.extend([idx + off for idx in [3,4,1,2,5,6,5,2,0,1,6,3]])
        self.k.extend([idx + off for idx in [0,7,2,3,6,7,1,1,5,5,7,6]])
        if hover_txt: self.text.extend([hover_txt] * 8)
        self.contador += 1
        
    def agregar_cilindro(self, x_center, y_center, z_base, radio, altura, hover_txt=None):
        lados = 8
        off = len(self.x)
        for i in range(lados):
            angulo = 2 * math.pi * i / lados
            cx = x_center + radio * math.cos(angulo)
            cy = y_center + radio * math.sin(angulo)
            self.x.extend([cx, cx])
            self.y.extend([cy, cy])
            self.z.extend([z_base, z_base + altura])
            if hover_txt: self.text.extend([hover_txt, hover_txt])
        
        self.x.extend([x_center, x_center])
        self.y.extend([y_center, y_center])
        self.z.extend([z_base, z_base + altura])
        if hover_txt: self.text.extend([hover_txt, hover_txt])
        
        c_base = off + lados * 2
        c_tope = off + lados * 2 + 1
        
        for i in range(lados):
            nxt = (i + 1) % lados
            b1, t1 = off + i*2, off + i*2 + 1
            b2, t2 = off + nxt*2, off + nxt*2 + 1
            self.i.extend([b1, t1]); self.j.extend([b2, b2]); self.k.extend([t1, t2])
            self.i.extend([c_base, c_tope]); self.j.extend([b2, t1]); self.k.extend([b1, t2])
        self.contador += 1

    def obtener_trazo(self):
        if len(self.x) == 0: return None
        params = dict(
            x=self.x, y=self.y, z=self.z, i=self.i, j=self.j, k=self.k,
            color=self.color, opacity=self.opacidad, name=self.nombre,
            showscale=False, flatshading=True
        )
        if self.text:
            params['text'] = self.text
            params['hoverinfo'] = "text"
        else:
            params['hoverinfo'] = "name"
        return go.Mesh3d(**params)

def add_cube_rotated(capa, x0, y0, z0, dx, dy, dz, is_vertical, hover_txt=None):
    if is_vertical: capa.agregar_cubo(y0, x0, z0, dy, dx, dz, hover_txt)
    else: capa.agregar_cubo(x0, y0, z0, dx, dy, dz, hover_txt)

def generar_layout_3d(res, l_m, a_m, alt_m, is_vertical, skus_buscados, puertas, modo_vista):
    dict_color_abc = {'A': '#e74c3c', 'B': '#f39c12', 'C': '#3498db'}
    dict_color_abcxyz = {
        'AX': '#900C3F', 'AY': '#C70039', 'AZ': '#FF5733',
        'BX': '#E67E22', 'BY': '#F39C12', 'BZ': '#F1C40F',
        'CX': '#2E86C1', 'CY': '#3498DB', 'CZ': '#85C1E9'
    }

    if skus_buscados and 'TODOS' in skus_buscados: skus_buscados = set()

    capa_pilares = MallaAgrupada('#e74c3c', 'Pilares CD')
    capa_oficinas = MallaAgrupada('#bdc3c7', 'Oficinas', 0.9)
    capa_staging = MallaAgrupada('#f39c12', 'Staging', 0.4)
    capa_marcos = MallaAgrupada('#2c3e50', 'Rack', 0.1 if skus_buscados else 1.0)
    capa_marcos_bloqueados = MallaAgrupada('#7f8c8d', 'Rack Inactivo', 0.4)
    capa_vigas = MallaAgrupada('#e67e22', 'Vigas', 0.1 if skus_buscados else 1.0)
    
    capa_maderas = MallaAgrupada('#d35400', 'Pallet Base', 1.0)
    capa_maderas_apagadas = MallaAgrupada('#bdc3c7', 'Pallet Oculto', 0.1)

    cajas_full = {'Destacado': MallaAgrupada('#2ecc71', 'SKU Buscado', 1.0), 'Apagado': MallaAgrupada('#ecf0f1', 'Oculto', 0.1)}
    cajas_saldo = {'Destacado': MallaAgrupada('#27ae60', 'Saldo Buscado', 1.0), 'Apagado': MallaAgrupada('#ecf0f1', 'Oculto', 0.1)}

    if '9 Zonas' in modo_vista:
        for k, color in dict_color_abcxyz.items(): 
            cajas_full[k] = MallaAgrupada(color, f'Clase {k}')
            cajas_saldo[k] = MallaAgrupada(color, f'Saldo {k}')
    else:
        for k, color in dict_color_abc.items(): 
            cajas_full[k] = MallaAgrupada(color, f'Clase {k}')
            cajas_saldo[k] = MallaAgrupada(color, f'Saldo {k}')

    for px, py in res['pilares_reales']:
        if px < l_m and py < a_m: capa_pilares.agregar_cubo(px - 0.25, py - 0.25, 0, 0.5, 0.5, alt_m)
    for ofi in res['oficinas']:
        capa_oficinas.agregar_cubo(ofi['x'], ofi['y'], 0, ofi['w'], ofi['d'], ofi.get('h', 3.5))
    for st_z in res['staging']:
        capa_staging.agregar_cubo(st_z['x1'], st_z['y1'], 0.01, st_z['x2'] - st_z['x1'], st_z['y2'] - st_z['y1'], 0.02)

    t, h_rack = res['t_marco'], max(res['niveles'] * res['alt_nivel_viga'], res['alt_nivel_viga'])
    
    for mod in res['modulos_list']:
        x_pos, y_rack = mod['x'], mod['y']
        c_activa = capa_marcos_bloqueados if mod['bloqueado'] else capa_marcos
        add_cube_rotated(c_activa, x_pos, y_rack, 0, t, res['pp_d'], t, is_vertical)
        add_cube_rotated(c_activa, x_pos, y_rack, 0, t, t, h_rack, is_vertical)
        add_cube_rotated(c_activa, x_pos, y_rack + res['pp_d'] - t, 0, t, t, h_rack, is_vertical)
        add_cube_rotated(c_activa, x_pos + res['l_modulo'] - t, y_rack, 0, t, t, h_rack, is_vertical)
        add_cube_rotated(c_activa, x_pos + res['l_modulo'] - t, y_rack + res['pp_d'] - t, 0, t, t, h_rack, is_vertical)
        add_cube_rotated(c_activa, x_pos, y_rack, h_rack, res['l_modulo'], res['pp_d'], 0.05, is_vertical)

        c_viga = capa_marcos_bloqueados if mod['bloqueado'] else capa_vigas
        for n_v in range(1, res['niveles']):
            z_v = n_v * res['alt_nivel_viga'] - res['viga_h']
            add_cube_rotated(c_viga, x_pos + t, y_rack, z_v, res['l_modulo'] - 2*t, t/2, res['viga_h'], is_vertical)
            add_cube_rotated(c_viga, x_pos + t, y_rack + res['pp_d'] - t/2, z_v, res['l_modulo'] - 2*t, t/2, res['viga_h'], is_vertical)

    for slot in res['almacen']:
        if slot['ocupado']:
            alt_carga = max(0.1, slot['alt_p'] - 0.12)
            es_cilindro = slot.get('es_cilindro', False)
            es_saldo = slot.get('es_saldo', False)
            
            txt_hover = f"<b>[{slot['id_posicion']}]</b><br>SKU: {slot['sku']}<br>Alto Carga: {alt_carga:.2f}m"
            if es_saldo: txt_hover += " <b style='color:#e74c3c;'>(SALDO)</b>"
            
            if skus_buscados:
                if slot['sku'] in skus_buscados:
                    capa_caja = cajas_saldo['Destacado'] if es_saldo else cajas_full['Destacado']
                    capa_madera = capa_maderas
                else:
                    capa_caja = cajas_saldo['Apagado'] if es_saldo else cajas_full['Apagado']
                    capa_madera = capa_maderas_apagadas
            else:
                capa_madera = capa_maderas
                key_color = slot['abc_xyz'] if '9 Zonas' in modo_vista else slot['abc']
                dict_uso = cajas_saldo if es_saldo else cajas_full
                capa_caja = dict_uso.get(key_color, dict_uso.get('C' if '3 Zonas' in modo_vista else 'CZ'))
                
            add_cube_rotated(capa_madera, slot['x_pal'], slot['y'] + 0.05, slot['z'] + 0.02, res['ap_w'], res['pp_d'] - 0.1, 0.12, is_vertical)
            
            rx = slot['y'] + 0.05 if is_vertical else slot['x_pal'] + 0.05
            ry = slot['x_pal'] + 0.05 if is_vertical else slot['y'] + 0.05
            w_c = res['pp_d'] - 0.1 if is_vertical else res['ap_w'] - 0.1
            d_c = res['ap_w'] - 0.1 if is_vertical else res['pp_d'] - 0.2
            z_c = slot['z'] + 0.14
            
            if es_cilindro:
                radio = min(w_c, d_c) / 2
                capa_caja.agregar_cilindro(rx + w_c/2, ry + d_c/2, z_c, radio, alt_carga, txt_hover)
            else:
                capa_caja.agregar_cubo(rx, ry, z_c, w_c, d_c, alt_carga, txt_hover)

    c_puertas_cortina = MallaAgrupada('#f1c40f', 'Cortina', 0.4)
    c_puertas_marcos = MallaAgrupada('#f39c12', 'Marco', 1.0)
    alt_puerta = 4.5
    for p in puertas:
        pared, pos, w = p['pared'], p['pos'], p['w']
        if pared == 'S':
            c_puertas_cortina.agregar_cubo(pos, 0.1, 0, w, 0.1, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos, 0, 0, 0.2, 0.3, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos+w-0.2, 0, 0, 0.2, 0.3, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos, 0, alt_puerta, w, 0.3, 0.4)
        elif pared == 'N':
            c_puertas_cortina.agregar_cubo(pos, a_m-0.2, 0, w, 0.1, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos, a_m-0.3, 0, 0.2, 0.3, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos+w-0.2, a_m-0.3, 0, 0.2, 0.3, alt_puerta)
            c_puertas_marcos.agregar_cubo(pos, a_m-0.3, alt_puerta, w, 0.3, 0.4)
        elif pared == 'E':
            c_puertas_cortina.agregar_cubo(l_m-0.2, pos, 0, 0.1, w, alt_puerta)
            c_puertas_marcos.agregar_cubo(l_m-0.3, pos, 0, 0.3, 0.2, alt_puerta)
            c_puertas_marcos.agregar_cubo(l_m-0.3, pos+w-0.2, 0, 0.3, 0.2, alt_puerta)
            c_puertas_marcos.agregar_cubo(l_m-0.3, pos, alt_puerta, 0.3, w, 0.4)
        elif pared == 'O':
            c_puertas_cortina.agregar_cubo(0.1, pos, 0, 0.1, w, alt_puerta)
            c_puertas_marcos.agregar_cubo(0, pos, 0, 0.3, 0.2, alt_puerta)
            c_puertas_marcos.agregar_cubo(0, pos+w-0.2, 0, 0.3, 0.2, alt_puerta)
            c_puertas_marcos.agregar_cubo(0, pos, alt_puerta, 0.3, w, 0.4)

    fig_3d = go.Figure()
    fig_3d.add_trace(go.Mesh3d(x=[0, l_m, l_m, 0, 0, l_m, l_m, 0], y=[0, 0, a_m, a_m, 0, 0, a_m, a_m], z=[-0.1, -0.1, -0.1, -0.1, 0, 0, 0, 0], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='#ecf0f1', showscale=False, name='Suelo'))

    todas_las_capas = [capa_pilares, capa_oficinas, capa_staging, capa_marcos, capa_marcos_bloqueados, capa_vigas, capa_maderas, capa_maderas_apagadas] + list(cajas_full.values()) + list(cajas_saldo.values()) + [c_puertas_cortina, c_puertas_marcos]
    for c in todas_las_capas:
        trace = c.obtener_trazo()
        if trace: fig_3d.add_trace(trace)

    estado_filtro = "<b style='color:#e67e22;'>[FOCO ACTIVO]</b><br>" if skus_buscados else ""
    fig_3d.update_layout(
        title=dict(text=f"{estado_filtro}<b>Gemelo Digital 3D | Formatos Reales</b><br><sup>Ubicados: {res['pallets_ubicados_totales']} pallets</sup>", x=0.5, font=dict(size=16)),
        scene=dict(xaxis=dict(title='Largo X (m)', range=[-5, l_m + 5], backgroundcolor="white"), yaxis=dict(title='Ancho Y (m)', range=[-5, a_m + 5], backgroundcolor="white"), zaxis=dict(title='Alto Z (m)', range=[0, max(10, alt_m + 1)], backgroundcolor="white"), aspectmode='data', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
        margin=dict(r=0, l=0, b=0, t=80), height=750, paper_bgcolor='white', showlegend=False
    )
    return fig_3d

# ============================================================
# 5. MÓDULOS DE PÁGINAS (UI)
# ============================================================

def cambiar_menu(pagina):
    st.session_state.menu_seleccion = pagina

def mostrar_portada():
    st.markdown(color_styles, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-container-color">
        <div class="hero-title-color">WMS Analytics Hub</div>
        <div class="hero-subtitle-color">Plataforma integral de ingeniería logística para la optimización de almacenamiento, cubicación geométrica y diseño avanzado de layout de bodegas.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='color:#0f172a; font-weight:800; margin-bottom: 20px;'>MÓDULOS DE CONTROL</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="color-card">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📦</span>
                    <span class="card-tag-color tag-blue">DISPONIBLE</span>
                </div>
                <div class="color-card-title">Cubicadora de Pallets</div>
                <p class="color-card-desc">Cálculo algorítmico de volumen, estiba optimizada de productos y previsualización 2D/3D con filtros ABC.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("⚙️ Abrir Cubicadora", key="btn_cub", type="primary", use_container_width=True, on_click=cambiar_menu, args=("📦 Cubicadora WMS",))
        st.markdown("<br>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="color-card color-card-green">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">🏗️</span>
                    <span class="card-tag-color tag-green">DISPONIBLE</span>
                </div>
                <div class="color-card-title">Layout de Bodega</div>
                <p class="color-card-desc">Diseñador espacial de CD, optimización IA, Gemelo Digital 3D y Exportador de posiciones WMS.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("⚙️ Abrir Diseñador Layout", key="btn_lay", type="primary", use_container_width=True, on_click=cambiar_menu, args=("🏗️ Layout de Bodega",))
        st.markdown("<br>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="color-card color-card-purple">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📊</span>
                    <span class="card-tag-color tag-purple">DISPONIBLE</span>
                </div>
                <div class="color-card-title">Analytics & Reportería</div>
                <p class="color-card-desc">Dashboard de indicadores clave (KPIs), volumetría total, ocupación física y análisis gerencial.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("📊 Abrir Dashboard Analytics", key="btn_an", type="primary", use_container_width=True, on_click=cambiar_menu, args=("📊 Analytics & Reportería",))
        st.markdown("<br>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    with col4:
        st.markdown("""
        <div class="color-card color-card-amber" style="opacity: 0.85;">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📥</span>
                    <span class="card-tag-color tag-soon">EN DESARROLLO</span>
                </div>
                <div class="color-card-title">Entrada de Mercadería (Inbound)</div>
                <p class="color-card-desc">Módulo táctico para la gestión inteligente de andenes, asignación de recepción y priorización de descarga.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("🔒 Módulo en Construcción", key="btn_in", disabled=True, use_container_width=True)

    with col5:
        st.markdown("""
        <div class="color-card color-card-rose" style="opacity: 0.85;">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📤</span>
                    <span class="card-tag-color tag-soon">EN DESARROLLO</span>
                </div>
                <div class="color-card-title">Salida de Mercadería (Outbound)</div>
                <p class="color-card-desc">Planificación de despacho, consolidación de pedidos por ruta y cubicaje avanzado de camiones de carga.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("🔒 Módulo en Construcción", key="btn_out", disabled=True, use_container_width=True)


def mostrar_cubicadora():
    st.markdown(css_styles, unsafe_allow_html=True)
    st.title("📦 Cubicadora de Palletización Masiva")

    archivo_subido = st.file_uploader("📂 Sube tu archivo Excel con la base de datos", type=["xlsx"])
    if archivo_subido is not None:
        with st.spinner("Procesando base de datos..."):
            try: df_original = pd.read_excel(archivo_subido, sheet_name="Data Equipo 7")
            except: df_original = pd.read_excel(archivo_subido, sheet_name=0)
            df_res, MAPA = procesar_datos(df_original.dropna(how="all").reset_index(drop=True))
            st.session_state.df_original, st.session_state.df_resultados, st.session_state.mapa_columnas = df_original, df_res, MAPA

    if st.session_state.df_resultados is not None:
        df_f = st.session_state.df_resultados.copy()
        MAPA = st.session_state.mapa_columnas
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            modo = st.radio("⚙️ Modo de cálculo:", ["EXCEL", "OPTIMO"], horizontal=True)
        with col_m2:
            if MAPA.get('abc'):
                opciones_abc = sorted([str(x) for x in df_f[MAPA['abc']].unique() if str(x) != 'nan'])
                if opciones_abc:
                    sel_abc = st.multiselect("🔍 Filtro Rápido (ABC):", opciones_abc, default=opciones_abc)
                    df_f = df_f[df_f[MAPA['abc']].isin(sel_abc)]
            if MAPA.get('xyz'):
                opciones_xyz = sorted([str(x) for x in df_f[MAPA['xyz']].unique() if str(x) != 'nan'])
                if opciones_xyz:
                    sel_xyz = st.multiselect("🔍 Filtro Demanda (XYZ):", opciones_xyz, default=opciones_xyz)
                    df_f = df_f[df_f[MAPA['xyz']].isin(sel_xyz)]

        st.markdown("<h3 style='color:#0f172a; font-weight:800; font-size:18px; margin-top:20px;'>🔍 Buscador Masivo y Panel de Cálculo</h3>", unsafe_allow_html=True)
        
        lista_skus_all = df_f[MAPA["sku"]].astype(str).str.upper().unique().tolist()
        
        opcion_vis = st.radio("Método de Visualización:", ["Elegir de la lista", "Pegar lista (Excel)", "Ver primeros 10", "Ver TODOS"], horizontal=True)
        
        skus_a_procesar = []
        if opcion_vis == "Elegir de la lista":
            default_sel = [lista_skus_all[0]] if (lista_skus_all and not st.session_state.skus_activos) else [s for s in st.session_state.skus_activos if s in lista_skus_all]
            if not default_sel and lista_skus_all: default_sel = [lista_skus_all[0]]
            skus_a_procesar = st.multiselect("Seleccionar SKUs individualmente:", options=lista_skus_all, default=default_sel)
        elif opcion_vis == "Pegar lista (Excel)":
            txt_list = st.text_area("Pega aquí la columna copiada de Excel (SKUs separados por espacio, coma o salto de línea):", height=80)
            if txt_list:
                extraidos = [s.strip().upper() for s in re.split(r'[,\s;\n]+', txt_list) if s.strip()]
                skus_a_procesar = [s for s in extraidos if s in lista_skus_all]
                invalidos = [s for s in extraidos if s not in lista_skus_all]
                if invalidos:
                    st.warning(f"⚠️ Los siguientes SKUs no se encontraron en la base (o están filtrados): {', '.join(invalidos)}")
        elif opcion_vis == "Ver primeros 10":
            skus_a_procesar = lista_skus_all[:10]
        elif opcion_vis == "Ver TODOS":
            skus_a_procesar = lista_skus_all

        st.session_state.skus_activos = skus_a_procesar

        st.markdown("<br>", unsafe_allow_html=True)
        mostrar_graf = st.toggle("🖼️ Mostrar Planos 2D / 3D (Desactiva esta opción para obtener mayor velocidad en búsquedas masivas)", value=True)

        if st.session_state.skus_activos:
            df_kpi = df_f[df_f[MAPA['sku']].astype(str).str.upper().isin(st.session_state.skus_activos)]
        else:
            df_kpi = df_f

        tot_sku_kpi = len(df_f)
        con_stock_kpi = int((pd.to_numeric(df_f[MAPA["stock"]], errors="coerce").fillna(0) > 0).sum())
        tot_pallets_kpi = sum([calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"] for _, row in df_f.iterrows()])
        
        alertas_activas_kpi = 0
        for _, row in df_f.iterrows():
            m_a = calcular_metricas_dinamicas(row, MAPA, modo)
            if "EXCEL" in m_a["Estado"] or "PELIGRO" in m_a["Estado"] or "REVISAR" in m_a["Estado"]:
                alertas_activas_kpi += 1

        modo_txt = "MODO EXCEL (VALORES MANUALES)" if modo == "EXCEL" else "MODO OPTIMIZADO (MÁXIMA FÍSICA)"
        color_modo = "#3b82f6" if modo == "EXCEL" else "#f59e0b"
        
        st.markdown(f"""
        <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; border-radius: 12px 12px 0 0; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
            <div>
                <h3 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.5px;">WMS Analytics: Dashboard Paletizado</h3>
                <p style="color: #94a3b8; margin: 3px 0 0 0; font-size: 12px;">Estado: <b style="color:{color_modo};">{modo_txt}</b></p>
            </div>
            <div><span style="background: {color_modo}; color: white; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">{modo}</span></div>
        </div>
        """, unsafe_allow_html=True)

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; border-radius: 0 0 0 8px; padding: 14px 16px; margin-bottom: 20px;">
                <div style="font-size: 10px; font-weight: 800; color: #64748b; letter-spacing: 0.5px; margin-bottom: 4px;">TOTAL SKU (FILTRADO)</div>
                <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{tot_sku_kpi:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #10b981; padding: 14px 16px; margin-bottom: 20px;">
                <div style="font-size: 10px; font-weight: 800; color: #64748b; letter-spacing: 0.5px; margin-bottom: 4px;">SKUs CON STOCK</div>
                <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{con_stock_kpi:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div style="background: #f5f3ff; border: 1px solid #ddd6fe; border-left: 4px solid #6366f1; padding: 14px 16px; margin-bottom: 20px;">
                <div style="font-size: 10px; font-weight: 800; color: #4338ca; letter-spacing: 0.5px; margin-bottom: 4px;">PALLETS REQ.</div>
                <div style="font-size: 22px; font-weight: 800; color: #4f46e5;">{tot_pallets_kpi:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div style="background: #f5f3ff; border: 1px solid #ddd6fe; border-left: 4px solid #8b5cf6; padding: 14px 16px; margin-bottom: 20px;">
                <div style="font-size: 10px; font-weight: 800; color: #5b21b6; letter-spacing: 0.5px; margin-bottom: 4px;">POSICIONES</div>
                <div style="font-size: 22px; font-weight: 800; color: #7c3aed;">{tot_pallets_kpi:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k5:
            color_alert = "#dc2626" if alertas_activas_kpi > 0 else "#10b981"
            st.markdown(f"""
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #ef4444; border-radius: 0 0 8px 0; padding: 14px 16px; margin-bottom: 20px;">
                <div style="font-size: 10px; font-weight: 800; color: #991b1b; letter-spacing: 0.5px; margin-bottom: 4px;">ALERTAS ACTIVAS</div>
                <div style="font-size: 22px; font-weight: 800; color: {color_alert};">{alertas_activas_kpi:,}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        tab_buscar, tab_descargar, tab_alertas, tab_datos = st.tabs(["🔍 Resultados Detallados", "📥 Descargar Reporte", "🚨 Ver Alertas", "📊 Base de Datos"])

        with tab_buscar:
            if not st.session_state.skus_activos:
                st.markdown("<div style='text-align:center; padding: 30px; color:#64748b;'><h4>No hay SKUs seleccionados. Selecciona opciones en el buscador arriba.</h4></div>", unsafe_allow_html=True)
            else:
                for sku in st.session_state.skus_activos:
                    filtro = df_kpi[df_kpi[MAPA["sku"]].astype(str).str.upper() == sku]
                    if not filtro.empty:
                        fila = filtro.iloc[0]
                        m = calcular_metricas_dinamicas(fila, MAPA, modo)
                        
                        formato = fila[MAPA['formato']] if MAPA.get('formato') and pd.notna(fila[MAPA['formato']]) else 'N/D'
                        fam = fila[MAPA['familia']] if MAPA.get('familia') and pd.notna(fila[MAPA['familia']]) else 'N/D'
                        bodega = fila[MAPA['bodega']] if MAPA.get('bodega') and pd.notna(fila[MAPA['bodega']]) else 'N/D'
                        rank = fila[MAPA['ranking']] if MAPA.get('ranking') and pd.notna(fila[MAPA['ranking']]) else 'N/D'
                        abc_xyz = fila[MAPA['abc_xyz']] if MAPA.get('abc_xyz') and pd.notna(fila[MAPA['abc_xyz']]) else 'N/D'
                        
                        cap = m['Capacidad_Usada']
                        cap_excel = m['Cap_Excel']
                        cap_optima = m['Cap_Optima']
                        pallets = m['Pallets']
                        peso_est = m['Peso_Pallet']
                        efi_vol = m['Eficiencia_Volumen']
                        ult_unids = m['Unidades_Ultimo']
                        ult_pct = m['Ocupacion_Ultimo']
                        estado = m['Estado']
                        
                        color_estado = "#ef4444" if "PELIGRO" in estado or "EXCEL" in estado else "#f59e0b" if "REVISAR" in estado else "#10b981"
                        bg_estado = "#fef2f2" if "PELIGRO" in estado or "EXCEL" in estado else "#fffbeb" if "REVISAR" in estado else "#ecfdf5"
                        border_estado = "#fecaca" if "PELIGRO" in estado or "EXCEL" in estado else "#fde68a" if "REVISAR" in estado else "#a7f3d0"

                        modo_str = 'MODO OPTIMIZADO' if modo == 'OPTIMO' else 'MODO EXCEL'

                        html_header = f"""
                        <div style="font-family: 'Segoe UI', system-ui, sans-serif; width: 100%; background: #ffffff; border: 1px solid #e2e8f0; border-bottom:none; border-radius: 12px 12px 0 0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow: hidden; box-sizing: border-box;">
                            <div style="background: #0f172a; padding: 20px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid {color_estado};">
                                <div>
                                    <div style="color: #94a3b8; font-size: 11px; font-weight: 800; letter-spacing: 1px;">ANÁLISIS DE ESTIBA ({modo_str})</div>
                                    <div style="color: #ffffff; font-size: 26px; font-weight: 900; margin: 4px 0;">{sku}</div>
                                    <div style="color: #cbd5e1; font-size: 13px;">Formato: <span style="color: #fff; font-weight:600;">{formato}</span> &nbsp;|&nbsp; Familia: <span style="color: #fff; font-weight:600;">{fam}</span> &nbsp;|&nbsp; Bodega: <span style="color: #38bdf8; font-weight:700;">{bodega}</span></div>
                                </div>
                                <div style="background: {bg_estado}; border: 1px solid {border_estado}; padding: 10px 18px; border-radius: 6px; text-align: right;">
                                    <div style="color: {color_estado}; font-size: 10px; font-weight: 900;">DIAGNÓSTICO</div>
                                    <div style="color: {color_estado}; font-size: 15px; font-weight: 900;">{estado}</div>
                                </div>
                            </div>
                            <div style="padding: 20px 25px 5px 25px;">
                                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 15px;">
                                    <div class="kpi-box"><div class="kpi-title">Stock Prom.</div><div class="kpi-value">{fmt(m['Stock'], 1)}</div></div>
                                    <div class="kpi-box" style="background:#f0f9ff; border:1px solid #bae6fd;"><div class="kpi-title">Unid. Pallet</div><div class="kpi-value" style="color:#0284c7;">{fmt(cap, 0)}</div></div>
                                    <div class="kpi-box" style="background:#f0f9ff; border:1px solid #bae6fd;"><div class="kpi-title">Pallets Req.</div><div class="kpi-value" style="color:#0284c7;">{pallets}</div></div>
                                    <div class="kpi-box {'kpi-box-danger' if es_numero(peso_est) and peso_est > MAX_PESO_PALLET else ''}"><div class="kpi-title">Peso (Kg)</div><div class="kpi-value {'kpi-value-danger' if es_numero(peso_est) and peso_est > MAX_PESO_PALLET else ''}">{fmt(peso_est, 1)}</div></div>
                                    <div class="kpi-box"><div class="kpi-title">Volumen %</div><div class="kpi-value">{fmt(efi_vol, 1)}%</div></div>
                                </div>
                            </div>
                        </div>
                        """
                        
                        html_datos_base = f"""
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 0 12px; padding: 20px; font-family: system-ui; height: 100%; box-sizing: border-box;">
                            <h4 style="margin:0 0 10px 0; font-size:13px; color:#334155; border-bottom:2px solid #e2e8f0; padding-bottom:5px;">📋 Datos Base</h4>
                            <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 12px; color: #475569;">
                                <span style="font-weight:600;">Largo:</span><span>{fmt(a_float(valor_col(fila, 'largo', MAPA)),1)} cm</span>
                                <span style="font-weight:600;">Ancho:</span><span>{fmt(a_float(valor_col(fila, 'ancho', MAPA)),1)} cm</span>
                                <span style="font-weight:600;">Alto:</span><span>{fmt(a_float(valor_col(fila, 'alto', MAPA)),1)} cm</span>
                                <span style="font-weight:600;">Peso:</span><span>{fmt(a_float(valor_col(fila, 'peso', MAPA)),2)} kg</span>
                            </div>
                            <h4 style="margin:16px 0 8px 0; font-size:13px; color:#334155; border-bottom:2px solid #e2e8f0; padding-bottom:5px;">🏷️ Perfil Logístico</h4>
                            <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 12px; color: #475569;">
                                <span style="font-weight:600;">Ranking:</span><span>#{fmt(rank,0) if es_numero(rank) else rank}</span>
                                <span style="font-weight:600;">Matriz ABC-XYZ:</span><span style="font-weight:bold; color:#0284c7;">{abc_xyz}</span>
                                <span style="font-weight:600;">Zonificación:</span><span style="font-weight:bold; color:#0f766e;">{bodega}</span>
                            </div>
                            <h4 style="margin:16px 0 8px 0; font-size:13px; color:#334155; border-bottom:2px solid #e2e8f0; padding-bottom:5px;">⚙️ Resultados</h4>
                            <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 12px; color: #475569;">
                                <span style="color:#ef4444; font-weight:bold;">Excel (Manual):</span><span style="color:#ef4444; font-weight:bold;">{fmt(cap_excel,0)} u</span>
                                <span style="color:#10b981; font-weight:bold;">Óptimo Física:</span><span style="color:#10b981; font-weight:bold;">{fmt(cap_optima,0)} u</span>
                                <span style="font-weight:600;">Últ. Pallet:</span><span>{fmt(ult_pct,1)}% ({fmt(ult_unids,1)}u)</span>
                            </div>
                        </div>
                        """

                        st.markdown(html_header, unsafe_allow_html=True)
                        
                        if mostrar_graf:
                            col_izq, col_der = st.columns([1, 3])
                            with col_izq:
                                st.markdown(html_datos_base, unsafe_allow_html=True)
                            with col_der:
                                st.markdown("<div style='border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 0; padding: 20px; background: #ffffff; height: 100%;'>", unsafe_allow_html=True)
                                mostrar_3d_sku = st.toggle(f"🧊 Levantar Maqueta 3D", key=f"t_{sku}")
                                c_pb1, c_pb2, c_pb3 = st.columns(3)
                                with c_pb1: 
                                    st.markdown(f"<div style='font-size:10px; text-align:center; font-weight:800; color:#334155; margin-bottom:5px;'>PLANO PLANTA (N1)</div>", unsafe_allow_html=True)
                                    st.markdown(html_vista_superior(fila, MAPA), unsafe_allow_html=True)
                                with c_pb2: 
                                    st.markdown(f"<div style='font-size:10px; text-align:center; font-weight:800; color:#334155; margin-bottom:5px;'>PLANO ALZADO</div>", unsafe_allow_html=True)
                                    st.markdown(html_vista_lateral(fila, MAPA, m['Capacidad_Usada']), unsafe_allow_html=True)
                                with c_pb3: 
                                    if mostrar_3d_sku: 
                                        st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m['Capacidad_Usada']), use_container_width=True, key=f"pb_{sku}")
                                    else:
                                        st.markdown("<div style='height:200px; display:flex; align-items:center; justify-content:center; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; color:#94a3b8; font-size:11px; font-weight:bold;'>Activa el botón 'Levantar Maqueta 3D' para renderizar.</div>", unsafe_allow_html=True)
                                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                                c_ps1, c_ps2, c_ps3 = st.columns(3)
                                with c_ps1: 
                                    st.markdown(f"<div style='font-size:10px; text-align:center; font-weight:800; color:#0284c7; margin-bottom:5px;'>PLANTA PALLET SOBRANTE</div>", unsafe_allow_html=True)
                                    st.markdown(html_vista_superior(fila, MAPA, m['Unidades_Sobrante']), unsafe_allow_html=True)
                                with c_ps2: 
                                    st.markdown(f"<div style='font-size:10px; text-align:center; font-weight:800; color:#0284c7; margin-bottom:5px;'>ALZADO PALLET SOBRANTE</div>", unsafe_allow_html=True)
                                    st.markdown(html_vista_lateral(fila, MAPA, m['Capacidad_Usada'], m['Unidades_Sobrante']), unsafe_allow_html=True)
                                with c_ps3: 
                                    if mostrar_3d_sku: st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m['Capacidad_Usada'], m['Unidades_Sobrante']), use_container_width=True, key=f"ps_{sku}")
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(html_datos_base, unsafe_allow_html=True)
                            
                        st.markdown("<br>", unsafe_allow_html=True)

        with tab_descargar:
            st.write(f"Genera un Excel completo con las **24 columnas WMS** de los **{len(df_f)} SKUs** actuales.")
            excel_data = generar_excel_descarga(st.session_state.df_original, df_f, MAPA)
            st.download_button("📊 Descargar Reporte WMS Completo (Excel)", data=excel_data, file_name="Reporte_Paletizacion_Optimizado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with tab_alertas:
            alertas = [{"SKU": row[MAPA["sku"]], "Estado": calcular_metricas_dinamicas(row, MAPA, modo)["Estado"], "Pallets": calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"]} for _, row in df_f.iterrows() if "EXCEL" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"] or "PELIGRO" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"] or "REVISAR" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"]]
            if alertas: st.warning(f"Se encontraron {len(alertas)} SKUs con alertas."); st.dataframe(pd.DataFrame(alertas), use_container_width=True)
            else: st.success("🎉 ¡Excelente! No hay alertas.")
        with tab_datos: st.dataframe(df_f, use_container_width=True)
    else: st.info("👆 Sube tu archivo Excel para comenzar.")

def preparar_df_layout(df_base, mapa, modo):
    df_l = pd.DataFrame()
    df_l['SKU'] = df_base[mapa['sku']]
    
    metrics = [calcular_metricas_dinamicas(row, mapa, modo) for _, row in df_base.iterrows()]
    df_l['Cantidad_Pallets'] = [m['Pallets'] for m in metrics]
    df_l['Peso_Pallet_kg'] = [m['Peso_Pallet'] for m in metrics]
    df_l['Pallets_Completos_Optimo'] = [m['Pallets_Completos'] for m in metrics]
    df_l['Unidades_Sobrante_Optimo'] = [m['Unidades_Sobrante'] for m in metrics]
    df_l['Capacidad_Optima'] = [m['Cap_Optima'] for m in metrics]
    
    col_alto_tot = mapa.get('altura_total')
    if col_alto_tot:
        df_l['Alto_m'] = pd.to_numeric(df_base[col_alto_tot], errors='coerce').fillna(120) / 100.0
    else:
        df_l['Alto_m'] = 1.2
        
    col_abc = mapa.get('abc')
    col_xyz = mapa.get('xyz')
    col_abcxyz = mapa.get('abc_xyz')
    col_formato = mapa.get('formato')
    
    df_l['ABC'] = df_base[col_abc].fillna('C').astype(str).str.strip().str.upper() if col_abc else 'C'
    df_l['XYZ'] = df_base[col_xyz].fillna('Z').astype(str).str.strip().str.upper() if col_xyz else 'Z'
    df_l['ABC'] = df_l['ABC'].replace({'N/D': 'C', 'NAN': 'C', 'NONE': 'C', '': 'C'})
    df_l['XYZ'] = df_l['XYZ'].replace({'N/D': 'Z', 'NAN': 'Z', 'NONE': 'Z', '': 'Z'})
    
    if col_abcxyz and col_abcxyz in df_base.columns:
        df_l['ABC_XYZ'] = df_base[col_abcxyz].fillna(df_l['ABC'] + df_l['XYZ']).astype(str).str.strip().str.upper()
    else:
        df_l['ABC_XYZ'] = df_l['ABC'] + df_l['XYZ']
    
    df_l['ABC_XYZ'] = df_l['ABC_XYZ'].replace({'N/D': 'CZ', 'N/DN/D': 'CZ', 'NAN': 'CZ'})
    
    cat_type = pd.CategoricalDtype(categories=['AX', 'AY', 'AZ', 'BX', 'BY', 'BZ', 'CX', 'CY', 'CZ'], ordered=True)
    df_l['ABC_XYZ'] = df_l['ABC_XYZ'].astype(cat_type)
    
    df_l['Formato'] = df_base[col_formato] if col_formato else 'N/D'
    
    return df_l[df_l['Cantidad_Pallets'] > 0].sort_values(by='ABC_XYZ').reset_index(drop=True)

def mostrar_layout():
    st.title("🏗️ Diseñador de Layout de Bodega")
    
    if st.session_state.df_resultados is None:
        st.error("⚠️ Para usar el Layout, primero debes cargar el Excel en el módulo 'Cubicadora WMS'.")
        return

    df_orig = st.session_state.df_original.copy()
    df_res = st.session_state.df_resultados.copy()
    MAPA = st.session_state.mapa_columnas
    
    df_layout_orig = preparar_df_layout(df_orig, MAPA, "EXCEL")
    df_layout_opt = preparar_df_layout(df_res, MAPA, "OPTIMO")

    dict_demanda = {'Data Original': df_layout_orig, 'Data Optimizada': df_layout_opt}

    with st.expander("⚙️ PANEL MASTER CD (Configuración Completa de Bodega)", expanded=True):
        col_inf, col_dr, col_op, col_an = st.columns(4)
        
        with col_inf:
            st.markdown("<h4 style='color:#2980b9; margin-top:0;'>🏢 1. Infraestructura</h4>", unsafe_allow_html=True)
            st.session_state.l_bod = st.number_input('Largo Bodega (m):', value=st.session_state.l_bod)
            st.session_state.a_bod = st.number_input('Ancho Bodega (m):', value=st.session_state.a_bod)
            st.session_state.alt_bod = st.number_input('Alto Útil (m):', value=st.session_state.alt_bod)
            
            st.markdown("<b style='color:#7f8c8d; font-size:11px;'>MALLA DE PILARES</b>", unsafe_allow_html=True)
            st.session_state.cant_pilares_x = st.number_input('Cant. Pilares X (0=Auto):', value=st.session_state.cant_pilares_x)
            st.session_state.cant_pilares_y = st.number_input('Cant. Pilares Y (0=Auto):', value=st.session_state.cant_pilares_y)
            st.session_state.dist_pilares_x = st.number_input('Dist. Pilares X (m):', value=st.session_state.dist_pilares_x)
            st.session_state.dist_pilares_y = st.number_input('Dist. Pilares Y (m):', value=st.session_state.dist_pilares_y)
            
            st.markdown("<b style='color:#7f8c8d; font-size:11px;'>🏢 ZONA DE OFICINAS</b>", unsafe_allow_html=True)
            st.session_state.ofi_pos_x = st.number_input('Pos. Inicio X (m):', value=st.session_state.ofi_pos_x)
            st.session_state.ofi_pos_y = st.number_input('Pos. Inicio Y (m):', value=st.session_state.ofi_pos_y)
            st.session_state.ofi_largo = st.number_input('Largo X (m):', value=st.session_state.ofi_largo)
            st.session_state.ofi_ancho = st.number_input('Ancho Y (m):', value=st.session_state.ofi_ancho)
            st.session_state.ofi_alto = st.number_input('Alto Z (m):', value=st.session_state.ofi_alto)

        with col_dr:
            st.markdown("<h4 style='color:#27ae60; margin-top:0;'>📦 2. Slotting y Racks</h4>", unsafe_allow_html=True)
            
            df_fuente_curr = dict_demanda['Data Original'] if st.session_state.fuente_datos == 'Data Original' else dict_demanda['Data Optimizada']
            tot_p_fuente = df_fuente_curr['Cantidad_Pallets'].sum()
            cnt_a = df_fuente_curr[df_fuente_curr['ABC']=='A']['Cantidad_Pallets'].sum()
            cnt_b = df_fuente_curr[df_fuente_curr['ABC']=='B']['Cantidad_Pallets'].sum()
            cnt_c = df_fuente_curr[df_fuente_curr['ABC']=='C']['Cantidad_Pallets'].sum()

            st.markdown(f"""
            <div style='background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px; font-size:12px; font-family:monospace; margin-bottom:12px;'>
                <b style='color:#27ae60;'>✅ REPORTE CUBICADORA OK</b><br>
                <b>Total a Ubicar:</b> {tot_p_fuente:,.0f} Pallets<br>
                <span style='color:#e74c3c;'>🔹 Zona A: {cnt_a:,.0f} pal</span><br>
                <span style='color:#e67e22;'>🔹 Zona B: {cnt_b:,.0f} pal</span><br>
                <span style='color:#3498db;'>🔹 Zona C: {cnt_c:,.0f} pal</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<b style='color:#7f8c8d; font-size:11px;'>ESTRUCTURA RACK</b>", unsafe_allow_html=True)
            st.session_state.pallets_viga = st.selectbox('Config. Viga:', [1, 2, 3], index=[1,2,3].index(st.session_state.pallets_viga))
            st.session_state.peso_max_pallet = st.number_input('Peso Máx. Viga (kg):', value=st.session_state.peso_max_pallet)

        with col_op:
            st.markdown("<h4 style='color:#e67e22; margin-top:0;'>🚜 3. Operación</h4>", unsafe_allow_html=True)
            st.markdown("<b style='color:#7f8c8d; font-size:11px;'>DISEÑO DE TRÁNSITO</b>", unsafe_allow_html=True)
            st.session_state.tipo_flujo = st.selectbox('Flujo:', ['Ninguno', 'Flujo en U', 'Flujo en I (Línea Recta)', 'Flujo en L'], index=['Ninguno', 'Flujo en U', 'Flujo en I (Línea Recta)', 'Flujo en L'].index(st.session_state.tipo_flujo))
            st.session_state.ancho_porton = st.number_input('Ancho P. Auto (m):', value=st.session_state.ancho_porton)
            st.session_state.orientacion_rack = st.selectbox('Orientación:', ['Automática', 'Horizontal (X)', 'Vertical (Y)'], index=['Automática', 'Horizontal (X)', 'Vertical (Y)'].index(st.session_state.orientacion_rack))
            st.session_state.pasillo = st.number_input('Ancho Pasillo (m):', value=st.session_state.pasillo)
            st.session_state.cant_pas_trans = st.number_input('Pasillos Trans.:', value=st.session_state.cant_pas_trans)
            st.session_state.ancho_pas_trans = st.number_input('Ancho P. Trans. (m):', value=st.session_state.ancho_pas_trans)
            
            st.markdown("<b style='color:#d35400; font-size:11px;'>RESTRICCIONES FÍSICAS</b>", unsafe_allow_html=True)
            st.session_state.alt_grua = st.number_input('Alt. Máx. Grúa (m):', value=st.session_state.alt_grua)
            st.session_state.peso_max_grua = st.number_input('Cap. Grúa (kg):', value=st.session_state.peso_max_grua)
            
            st.markdown("<b style='color:#7f8c8d; font-size:11px;'>ACCESOS EXTRA</b>", unsafe_allow_html=True)
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.session_state.cant_ptas_norte = st.number_input('Ptas Norte:', value=st.session_state.cant_ptas_norte)
                st.session_state.cant_ptas_sur = st.number_input('Ptas Sur:', value=st.session_state.cant_ptas_sur)
                st.session_state.cant_ptas_este = st.number_input('Ptas Este:', value=st.session_state.cant_ptas_este)
                st.session_state.cant_ptas_oeste = st.number_input('Ptas Oeste:', value=st.session_state.cant_ptas_oeste)
            with c_p2:
                st.session_state.w_ptas_norte = st.number_input('Ancho N:', value=st.session_state.w_ptas_norte)
                st.session_state.w_ptas_sur = st.number_input('Ancho S:', value=st.session_state.w_ptas_sur)
                st.session_state.w_ptas_este = st.number_input('Ancho E:', value=st.session_state.w_ptas_este)
                st.session_state.w_ptas_oeste = st.number_input('Ancho O:', value=st.session_state.w_ptas_oeste)

        with col_an:
            st.markdown("<h4 style='color:#8e44ad; margin-top:0;'>🔍 4. Análisis y Filtros</h4>", unsafe_allow_html=True)
            st.session_state.fuente_datos = st.selectbox('📂 Fuente:', ['Data Original', 'Data Optimizada'], index=['Data Original', 'Data Optimizada'].index(st.session_state.fuente_datos))
            st.session_state.filtro_sublayout = st.text_area('✂️ Filtrar SKU:', value=st.session_state.filtro_sublayout, height=50)
            
            st.markdown("<b style='font-size:11px; color:#34495e;'>🔠 Zonas ABC a procesar:</b>", unsafe_allow_html=True)
            cb_a, cb_b, cb_c = st.columns(3)
            with cb_a: st.session_state.chk_a = st.checkbox('Zona A', value=st.session_state.chk_a)
            with cb_b: st.session_state.chk_b = st.checkbox('Zona B', value=st.session_state.chk_b)
            with cb_c: st.session_state.chk_c = st.checkbox('Zona C', value=st.session_state.chk_c)

            st.markdown("<b style='font-size:10px; color:#34495e; margin-top:5px; display:block;'>CONTROLES DE EVALUACIÓN:</b>", unsafe_allow_html=True)
            
            if st.button("🎯 Crear Layout (SKUs Seleccionados)", type="primary", use_container_width=True):
                st.session_state.layout_generado = True
                st.session_state.modo_layout_eval = 'filtro'
                
            if st.button("🏢 Crear Layout General", use_container_width=True):
                st.session_state.layout_generado = True
                st.session_state.modo_layout_eval = 'todos'

            if st.button("🧠 Propuesta Espacial de Layout", use_container_width=True):
                with st.spinner("⏳ Calculando propuesta óptima con IA..."):
                    clases_sel = []
                    if st.session_state.chk_a: clases_sel.append('A')
                    if st.session_state.chk_b: clases_sel.append('B')
                    if st.session_state.chk_c: clases_sel.append('C')
                    
                    df_test_base = dict_demanda[st.session_state.fuente_datos]
                    df_test_base = df_test_base[df_test_base['ABC'].isin(clases_sel)]
                    
                    raw_f = st.session_state.filtro_sublayout.strip()
                    skus_f = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw_f) if s.strip())
                    if skus_f and raw_f.upper() != 'TODOS':
                        df_test_base = df_test_base[df_test_base['SKU'].astype(str).str.upper().isin(skus_f)]

                    if not df_test_base.empty:
                        escenarios = []
                        for o in [True, False]:
                            for v in [2, 3]:
                                res_ia = motor_calculo_layout(df_test_base, o, v, st.session_state)
                                res_ia.update({'is_vertical': o, 'pal_v': v})
                                escenarios.append(res_ia)
                        if escenarios:
                            mejor = max(escenarios, key=lambda x: x['diferencia'])
                            st.session_state.orientacion_rack = 'Vertical (Y)' if mejor['is_vertical'] else 'Horizontal (X)'
                            st.session_state.pallets_viga = mejor['pal_v']
                            st.session_state.layout_generado = True
                            st.session_state.modo_layout_eval = 'todos'
                            st.success(f"🧠 IA Aplicada: Orientación {'Vertical' if mejor['is_vertical'] else 'Horizontal'}, {mejor['pal_v']} vigas.")
                            st.rerun()

            if st.session_state.layout_generado:
                clases_sel = []
                if st.session_state.chk_a: clases_sel.append('A')
                if st.session_state.chk_b: clases_sel.append('B')
                if st.session_state.chk_c: clases_sel.append('C')
                
                df_activa = dict_demanda[st.session_state.fuente_datos]
                df_activa = df_activa[df_activa['ABC'].isin(clases_sel)]
                
                raw = st.session_state.filtro_sublayout.strip()
                if getattr(st.session_state, 'modo_layout_eval', 'todos') == 'filtro':
                    skus_buscados = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw) if s.strip())
                    if skus_buscados and raw.upper() != 'TODOS':
                        df_activa = df_activa[df_activa['SKU'].astype(str).str.upper().isin(skus_buscados)]

                is_vert = ('Vertical' in st.session_state.orientacion_rack) if 'Automática' not in st.session_state.orientacion_rack else (st.session_state.tipo_flujo in ['Flujo en U', 'Flujo en I (Línea Recta)'])
                res_box = motor_calculo_layout(df_activa, is_vert, st.session_state.pallets_viga, st.session_state)
                st.session_state.res_layout_actual = res_box

                dif = res_box['diferencia']
                s_bg, s_color = ("#ecfdf5", "#065f46") if dif >= 0 else ("#fef2f2", "#991b1b")
                msg_txt = f"✔️ ¡ÉXITO! Caben todos y sobran {dif:,}." if dif >= 0 else f"⚠️ ¡ALERTA! Te faltan {abs(dif):,} posiciones."

                st.markdown(f"""
                <div style="margin-top:10px; border:1px solid {s_color}; border-radius:6px; background:{s_bg}; padding:8px; font-family:sans-serif;">
                    <div style="color:#2c3e50; font-weight:900; font-size:11px; margin-bottom:2px; text-align:center;">📊 EVALUACIÓN | Zonas: {','.join(clases_sel)}</div>
                    <div style="color:{s_color}; font-weight:bold; font-size:11px; margin-bottom:5px; text-align:center;">{msg_txt}</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2px; font-size:10px; color:#334155;">
                        <div><b>Racks Planta:</b></div><div style="text-align:right;">{res_box['modulos']:,} mód.</div>
                        <div><b>Niveles Alto:</b></div><div style="text-align:right;">{res_box['niveles']} niv.</div>
                        <div style="border-top:1px solid #cbd5e1; padding-top:2px;"><b>Capacidad Racks:</b></div><div style="border-top:1px solid #cbd5e1; padding-top:2px; text-align:right; font-weight:bold;">{res_box['capacidad']:,} pal</div>
                        <div><b>Demanda Eval:</b></div><div style="text-align:right; font-weight:bold;">{res_box['demanda']:,} pal</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if st.session_state.layout_generado and st.session_state.res_layout_actual is not None:
        st.markdown("---")
        res = st.session_state.res_layout_actual
        
        col_exp1, col_exp2 = st.columns([1, 1])
        with col_exp1:
            st.session_state.modo_vista_color = st.selectbox("🎨 Zonificación de Colores Racks:", ['3 Zonas (ABC)', '9 Zonas (ABC-XYZ)'], index=['3 Zonas (ABC)', '9 Zonas (ABC-XYZ)'].index(st.session_state.modo_vista_color))
        with col_exp2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            wms_excel = generar_wms_excel(df_orig if st.session_state.fuente_datos == 'Data Original' else df_res, res['almacen'], MAPA)
            st.download_button("💾 Exportar Ubicaciones WMS (Excel)", data=wms_excel, file_name="WMS_Ubicaciones_Bodega.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        l_m, a_m, w_puerta, flujo = st.session_state.l_bod, st.session_state.a_bod, st.session_state.ancho_porton, st.session_state.tipo_flujo
        fig_2d = go.Figure()
        fig_2d.add_shape(type="rect", x0=0, y0=0, x1=l_m, y1=a_m, line=dict(color="#2c3e50", width=4), fillcolor="#fafafa")
        
        pp_d, l_modulo = 1.2, (1.2 * st.session_state.pallets_viga) + (0.10 * (st.session_state.pallets_viga + 1)) + 0.10
        dict_color_abc = {'A': '#e74c3c', 'B': '#f39c12', 'C': '#3498db'}
        dict_color_abcxyz = {
            'AX': '#900C3F', 'AY': '#C70039', 'AZ': '#FF5733',
            'BX': '#E67E22', 'BY': '#F39C12', 'BZ': '#F1C40F',
            'CX': '#2E86C1', 'CY': '#3498DB', 'CZ': '#85C1E9'
        }

        path_free, path_block, path_pil = [], [], []
        p_racks = {k: [] for k in list(dict_color_abc.keys()) + list(dict_color_abcxyz.keys())}
        
        for mod in res['modulos_list']:
            x_pos, y_rack = mod['x'], mod['y']
            rx0, ry0, rx1, ry1 = (y_rack, x_pos, y_rack+pp_d, x_pos+l_modulo) if res['is_vertical'] else (x_pos, y_rack, x_pos+l_modulo, y_rack+pp_d)
            path = f"M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1} L {rx0} {ry1} Z"
            
            if mod['bloqueado']:
                path_block.append(path)
            else:
                if '9 Zonas' in st.session_state.modo_vista_color:
                    abcs_aqui = [s['abc_xyz'] for s in res['almacen'] if s['x']==x_pos and s['y']==y_rack and s['ocupado']]
                else:
                    abcs_aqui = [s['abc'] for s in res['almacen'] if s['x']==x_pos and s['y']==y_rack and s['ocupado']]
                
                clase = min(abcs_aqui) if abcs_aqui else None
                if clase and clase in p_racks:
                    p_racks[clase].append(path)
                else:
                    path_free.append(path)

        for px, py in res['pilares_reales']:
            rx0, ry0, rx1, ry1 = (py-0.25, px-0.25, py+0.25, px+0.25) if res['is_vertical'] else (px-0.25, py-0.25, px+0.25, py+0.25)
            path_pil.append(f"M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1} L {rx0} {ry1} Z")

        if path_free: fig_2d.add_shape(type="path", path=" ".join(path_free), fillcolor="#ecf0f1", line=dict(color="#bdc3c7", width=1))
        if path_block: fig_2d.add_shape(type="path", path=" ".join(path_block), fillcolor="#95a5a6", line=dict(color="#7f8c8d", width=1))
        
        if '9 Zonas' in st.session_state.modo_vista_color:
            for c_k, color in dict_color_abcxyz.items():
                if p_racks[c_k]: fig_2d.add_shape(type="path", path=" ".join(p_racks[c_k]), fillcolor=color, line=dict(color="#2c3e50", width=1))
        else:
            for c_k, color in dict_color_abc.items():
                if p_racks[c_k]: fig_2d.add_shape(type="path", path=" ".join(p_racks[c_k]), fillcolor=color, line=dict(color="#2c3e50", width=1))

        if path_pil: fig_2d.add_shape(type="path", path=" ".join(path_pil), fillcolor="#e74c3c", line=dict(color="#c0392b", width=1.5))
        
        for st_z in res['staging']: fig_2d.add_shape(type="rect", x0=st_z['x1'], y0=st_z['y1'], x1=st_z['x2'], y1=st_z['y2'], fillcolor="rgba(241, 196, 15, 0.4)", line=dict(color="#f39c12", width=2))
        for ofi in res['oficinas']: fig_2d.add_shape(type="rect", x0=ofi['x'], y0=ofi['y'], x1=ofi['x']+ofi['w'], y1=ofi['y']+ofi['d'], fillcolor="#bdc3c7", line=dict(color="#7f8c8d", width=2))

        puertas = []
        if w_puerta > 0 and flujo != 'Ninguno':
            if 'Flujo en U' in flujo: puertas.extend([{'pared': 'S', 'pos': (l_m*0.25)-(w_puerta/2), 'w': w_puerta, 'label': 'IN'}, {'pared': 'S', 'pos': (l_m*0.75)-(w_puerta/2), 'w': w_puerta, 'label': 'OUT'}])
            elif 'Flujo en I' in flujo: puertas.extend([{'pared': 'S', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta, 'label': 'IN'}, {'pared': 'N', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta, 'label': 'OUT'}])
            elif 'Flujo en L' in flujo: puertas.extend([{'pared': 'S', 'pos': max(1, (l_m*0.15)-(w_puerta/2)), 'w': w_puerta, 'label': 'IN'}, {'pared': 'E', 'pos': max(1, (a_m*0.85)-(w_puerta/2)), 'w': w_puerta, 'label': 'OUT'}])

        for p in puertas:
            pared, pos, w, label = p['pared'], p['pos'], p['w'], p['label']
            if pared == 'S': x0, y0, x1, y1, ax, ay = pos, 0, pos+w, 1.5, pos+w/2, 0.75
            elif pared == 'N': x0, y0, x1, y1, ax, ay = pos, a_m-1.5, pos+w, a_m, pos+w/2, a_m-0.75
            elif pared == 'E': x0, y0, x1, y1, ax, ay = l_m-1.5, pos, l_m, pos+w, l_m-0.75, pos+w/2
            elif pared == 'O': x0, y0, x1, y1, ax, ay = 0, pos, 1.5, pos+w, 0.75, pos+w/2
            fig_2d.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor="#f1c40f", line=dict(color="#f39c12", width=2))
            fig_2d.add_annotation(x=ax, y=ay, text=f"<b>{label}</b>", showarrow=False, font=dict(size=11, color="black"))

        fig_2d.update_layout(
            title="Plano CAD 2D del Centro de Distribución (Zonificación Racks)",
            xaxis=dict(title="Largo (m)", range=[-3, l_m + 3], zeroline=False),
            yaxis=dict(title="Ancho (m)", range=[-3, a_m + 3], zeroline=False, scaleanchor="x", scaleratio=1),
            height=650, margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor="#ffffff"
        )
        st.plotly_chart(fig_2d, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        mostrar_3d_layout = st.toggle("🧊 Cargar Gemelo Digital 3D (Puede tardar unos segundos)")
        
        if mostrar_3d_layout:
            with st.spinner("Construyendo Mallas 3D de la Bodega..."):
                raw_sub = st.session_state.filtro_sublayout.strip()
                skus_b = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw_sub) if s.strip()) if getattr(st.session_state, 'modo_layout_eval', 'todos') == 'filtro' else set()
                fig_3d = generar_layout_3d(res, l_m, a_m, st.session_state.alt_bod, res['is_vertical'], skus_b, puertas, st.session_state.modo_vista_color)
                st.plotly_chart(fig_3d, use_container_width=True)

def mostrar_analytics():
    st.title("📊 Analytics & Reportería Ejecutivo")
    
    if st.session_state.df_resultados is None:
        st.error("⚠️ Para visualizar el Dashboard de Analytics, primero debes cargar tu base de datos en el módulo 'Cubicadora WMS'.")
        return

    df_res = st.session_state.df_resultados.copy()
    MAPA = st.session_state.mapa_columnas

    df_res['Stock_Num'] = pd.to_numeric(df_res[MAPA['stock']], errors='coerce').fillna(0)
    df_res['Peso_Num'] = pd.to_numeric(df_res[MAPA['peso']], errors='coerce').fillna(0)
    
    metrics_excel = [calcular_metricas_dinamicas(row, MAPA, "EXCEL") for _, row in df_res.iterrows()]
    metrics_opt = [calcular_metricas_dinamicas(row, MAPA, "OPTIMO") for _, row in df_res.iterrows()]

    df_res['Pallets_Req_Excel'] = [m['Pallets'] for m in metrics_excel]
    df_res['Pallets_Req_Optimo'] = [m['Pallets'] for m in metrics_opt]
    df_res['Ocupacion_Ult_Pct'] = [m['Ocupacion_Ultimo'] for m in metrics_excel]
    df_res['Estado_Sku'] = [m['Estado'] for m in metrics_excel]

    largo_m = pd.to_numeric(df_res[MAPA['largo']], errors='coerce').fillna(0) / 100.0
    ancho_m = pd.to_numeric(df_res[MAPA['ancho']], errors='coerce').fillna(0) / 100.0
    alto_m = pd.to_numeric(df_res[MAPA['alto']], errors='coerce').fillna(0) / 100.0
    vol_unit_m3 = largo_m * ancho_m * alto_m
    df_res['Volumen_Total_M3'] = vol_unit_m3 * df_res['Stock_Num']

    tot_pallets_excel = df_res['Pallets_Req_Excel'].sum()
    tot_pallets_opt = df_res['Pallets_Req_Optimo'].sum()
    ahorro_pallets = tot_pallets_excel - tot_pallets_opt
    pct_ahorro = (ahorro_pallets / tot_pallets_excel * 100) if tot_pallets_excel > 0 else 0
    vol_total_bodega = df_res['Volumen_Total_M3'].sum()
    num_alertas = sum(1 for m in metrics_excel if "EXCEL" in m["Estado"] or "PELIGRO" in m["Estado"] or "REVISAR" in m["Estado"])

    cap_bodega_slots = st.session_state.kpi_layout_capacidad
    pallets_ubicados = st.session_state.kpi_layout_ubicados
    pct_ocupacion_bodega = (pallets_ubicados / cap_bodega_slots * 100) if cap_bodega_slots > 0 else 0.0

    st.markdown("### 📈 Indicadores Macro de Almacenamiento")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📦 Volumen Carga", f"{vol_total_bodega:,.1f} m³")
    m2.metric("🏗️ Pallets Excel", f"{tot_pallets_excel:,} pal")
    m3.metric("🎯 Pallets Óptimo", f"{tot_pallets_opt:,} pal", delta=f"{-ahorro_pallets:,} pal ({pct_ahorro:.1f}%)", delta_color="inverse")
    m4.metric("🏛️ Ocupación Bodega", f"{pct_ocupacion_bodega:.1f}%" if cap_bodega_slots > 0 else "N/D", delta=f"{pallets_ubicados:,}/{cap_bodega_slots:,} Slots" if cap_bodega_slots > 0 else "Generar Layout")
    m5.metric("🚨 SKUs Alertas", f"{num_alertas} SKUs", delta="Atención Requerida" if num_alertas > 0 else "Todo OK", delta_color="off")

    st.markdown("---")

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### 🍩 Distribución de SKUs por Formato")
        df_formato = df_res[MAPA['formato']].value_counts().reset_index()
        df_formato.columns = ['Formato', 'Cantidad']
        fig_donut = px.pie(df_formato, values='Cantidad', names='Formato', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_donut.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

    with g2:
        st.markdown("#### 📊 Top 10 SKUs por Pallets Requeridos")
        df_top10 = df_res.sort_values(by='Pallets_Req_Excel', ascending=False).head(10)
        fig_top = px.bar(df_top10, x='Pallets_Req_Excel', y=MAPA['sku'], orientation='h', text='Pallets_Req_Excel', color='Pallets_Req_Excel', color_continuous_scale='Blues')
        fig_top.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=30, b=20), height=350, showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("---")

    g3, g4 = st.columns(2)
    with g3:
        st.markdown("#### 📉 Comparativa de Pallets: Excel vs. Óptimo (Top 15)")
        df_comp = df_res.head(15)
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_comp[MAPA['sku']], y=df_comp['Pallets_Req_Excel'], name='Excel (Manual)', marker_color='#3b82f6'))
        fig_comp.add_trace(go.Bar(x=df_comp[MAPA['sku']], y=df_comp['Pallets_Req_Optimo'], name='Óptimo Algorítmico', marker_color='#10b981'))
        fig_comp.update_layout(barmode='group', margin=dict(l=20, r=20, t=30, b=20), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_comp, use_container_width=True)

    with g4:
        st.markdown("#### ⚖️ Matriz Peso por Pallet vs. Ocupación")
        df_res['Peso_Pallet_Kg'] = [m['Peso_Pallet'] for m in metrics_excel]
        fig_scatter = px.scatter(
            df_res, x='Ocupacion_Ult_Pct', y='Peso_Pallet_Kg', size='Stock_Num', color='Estado_Sku',
            hover_name=MAPA['sku'], labels={'Ocupacion_Ult_Pct': '% Ocupación Último Pallet', 'Peso_Pallet_Kg': 'Peso Total Pallet (kg)'},
            color_discrete_map={"✅ OK": "#10b981", "❌ SIN STOCK": "#64748b", "⚠️ REVISAR DATOS": "#f59e0b", "🚨 SOBREPESO (>1200kg)": "#ef4444"}
        )
        fig_scatter.add_hline(y=MAX_PESO_PALLET, line_dash="dash", line_color="red", annotation_text="Límite Peso (1200kg)")
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
        st.plotly_chart(fig_scatter, use_container_width=True)

def mostrar_inbound():
    st.title("📥 Entrada de Mercadería (Inbound)")
    st.info("Módulo táctico para la gestión inteligente de andenes, asignación de recepción y priorización de descarga.")

def mostrar_outbound():
    st.title("📤 Salida de Mercadería (Outbound)")
    st.info("Planificación de despacho, consolidación de pedidos por ruta y cubicaje avanzado de camiones de carga.")

# ============================================================
# 6. MENÚ DE NAVEGACIÓN PRINCIPAL (SIDEBAR)
# ============================================================

menu_opciones = ["🏠 Portada Principal", "📦 Cubicadora WMS", "🏗️ Layout de Bodega", "📊 Analytics & Reportería", "📥 Entrada Mercadería", "📤 Salida Mercadería"]
st.session_state.menu_seleccion = st.sidebar.radio(
    "Navegación", 
    menu_opciones,
    index=menu_opciones.index(st.session_state.menu_seleccion)
)

st.sidebar.markdown("---")
st.sidebar.caption("WMS Analytics Hub v8.1 • Precision Sorting")

if st.session_state.menu_seleccion == "🏠 Portada Principal": mostrar_portada()
elif st.session_state.menu_seleccion == "📦 Cubicadora WMS": mostrar_cubicadora()
elif st.session_state.menu_seleccion == "🏗️ Layout de Bodega": mostrar_layout()
elif st.session_state.menu_seleccion == "📊 Analytics & Reportería": mostrar_analytics()
elif st.session_state.menu_seleccion == "📥 Entrada Mercadería": mostrar_inbound()
elif st.session_state.menu_seleccion == "📤 Salida Mercadería": mostrar_outbound()
