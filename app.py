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
            st.session_state.filtro_sublayout = st.text_area('✂️ Filtrar SKU (Dejar TODOS para bodega completa):', value=st.session_state.filtro_sublayout, height=50)
            
            st.markdown("<b style='font-size:11px; color:#34495e;'>🔠 Zonas ABC a procesar:</b>", unsafe_allow_html=True)
            cb_a, cb_b, cb_c = st.columns(3)
            with cb_a: st.session_state.chk_a = st.checkbox('Zona A', value=st.session_state.chk_a)
            with cb_b: st.session_state.chk_b = st.checkbox('Zona B', value=st.session_state.chk_b)
            with cb_c: st.session_state.chk_c = st.checkbox('Zona C', value=st.session_state.chk_c)

            st.markdown("<b style='font-size:10px; color:#34495e; margin-top:5px; display:block;'>CONTROLES DE EVALUACIÓN:</b>", unsafe_allow_html=True)
            
            if st.button("🎯 Crear Layout (SKUs Seleccionados)", type="primary", use_container_width=True):
                raw = st.session_state.filtro_sublayout.strip()
                skus_f = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw) if s.strip())
                if not skus_f or raw.upper() == 'TODOS':
                    st.session_state.modo_layout_eval = 'todos'
                    st.warning("⚠️ No ingresaste ningún SKU específico. Se cargará la bodega completa.")
                else:
                    st.session_state.modo_layout_eval = 'filtro'
                st.session_state.layout_generado = True
                
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
st.sidebar.caption("WMS Analytics Hub v8.2 • Visual Fixes")

if st.session_state.menu_seleccion == "🏠 Portada Principal": mostrar_portada()
elif st.session_state.menu_seleccion == "📦 Cubicadora WMS": mostrar_cubicadora()
elif st.session_state.menu_seleccion == "🏗️ Layout de Bodega": mostrar_layout()
elif st.session_state.menu_seleccion == "📊 Analytics & Reportería": mostrar_analytics()
elif st.session_state.menu_seleccion == "📥 Entrada Mercadería": mostrar_inbound()
elif st.session_state.menu_seleccion == "📤 Salida Mercadería": mostrar_outbound()
