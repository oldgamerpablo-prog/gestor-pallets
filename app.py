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

# Memoria de Navegación
if "menu_seleccion" not in st.session_state:
    st.session_state.menu_seleccion = "🏠 Portada Principal"

# Memoria Cubicadora
if "skus_activos" not in st.session_state: st.session_state.skus_activos = []
if "df_original" not in st.session_state: st.session_state.df_original = None
if "df_resultados" not in st.session_state: st.session_state.df_resultados = None
if "mapa_columnas" not in st.session_state: st.session_state.mapa_columnas = None

# Memoria Layout
parametros_layout = {
    'l_bod': 40.0, 'a_bod': 50.0, 'alt_bod': 7.0, 'cant_pilares_x': 4, 'cant_pilares_y': 1,
    'dist_pilares_x': 20.0, 'dist_pilares_y': 15.0, 'ofi_pos_x': 0.0, 'ofi_pos_y': 0.0,
    'ofi_largo': 10.0, 'ofi_ancho': 5.0, 'ofi_alto': 3.5, 'pallets_viga': 2, 'peso_max_pallet': 2000.0,
    'tipo_flujo': 'Flujo en I (Línea Recta)', 'ancho_porton': 6.0, 'orientacion_rack': 'Horizontal (X)',
    'pasillo': 3.0, 'cant_pas_trans': 0, 'ancho_pas_trans': 3.0, 'alt_grua': 10.5,
    'fuente_datos': 'Data Original', 'filtro_sublayout': 'TODOS'
}
for k, v in parametros_layout.items():
    if k not in st.session_state: st.session_state[k] = v

if "layout_generado" not in st.session_state: st.session_state.layout_generado = False
if "mostrar_3d_layout" not in st.session_state: st.session_state.mostrar_3d_layout = False

css_styles = """
<style>
    .box-3d { transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: crosshair; }
    .box-3d:hover { transform: scale(1.08) translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.4) !important; z-index: 100 !important; filter: brightness(1.1); }
    .cota-linea, .cota-linea-v { position: absolute; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #475569; font-weight: bold; background-repeat: no-repeat; }
    .cota-linea { border-left: 1px solid #64748b; border-right: 1px solid #64748b; background-image: linear-gradient(#64748b, #64748b); background-size: 100% 1px; background-position: center; }
    .cota-linea-v { border-top: 1px solid #64748b; border-bottom: 1px solid #64748b; background-image: linear-gradient(#64748b, #64748b); background-size: 1px 100%; background-position: center; flex-direction: column; }
    .cota-texto { background: white; padding: 2px 4px; border-radius: 3px; z-index: 2; }
</style>
"""

color_styles = """
<style>
    .hero-container-color {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0369a1 100%);
        border-radius: 16px; padding: 50px 30px; text-align: center;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25); margin-bottom: 35px;
    }
    .hero-title-color { font-size: 3.6rem; font-weight: 900; color: #ffffff; letter-spacing: -1px; margin-bottom: 14px; text-align: center; }
    .hero-subtitle-color { color: #e2e8f0; font-size: 1.25rem; font-weight: 400; max-width: 850px; margin: 0 auto; line-height: 1.6; text-align: center; }
    .color-card {
        background: #ffffff; border-radius: 14px; padding: 28px; height: 230px;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05); transition: all 0.3s ease; margin-bottom: 15px; border-top: 5px solid #2563eb;
    }
    .color-card-green { border-top-color: #059669; }
    .color-card-purple { border-top-color: #7c3aed; }
    .color-card-amber { border-top-color: #d97706; }
    .color-card-rose { border-top-color: #e11d48; }
    .color-card:hover { box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12); transform: translateY(-4px); }
    .card-icon-header { display: flex; align-items: center; justify-content: space-between; }
    .card-icon { font-size: 2.2rem; }
    .card-tag-color { font-size: 0.75rem; font-weight: 800; padding: 4px 12px; border-radius: 20px; letter-spacing: 0.5px; }
    .tag-blue { background: #dbeafe; color: #1e40af; }
    .tag-green { background: #d1fae5; color: #065f46; }
    .tag-purple { background: #ede9fe; color: #5b21b6; }
    .tag-soon { background: #f1f5f9; color: #64748b; }
    .color-card-title { color: #0f172a; font-size: 1.35rem; font-weight: 800; margin: 12px 0 6px 0; }
    .color-card-desc { color: #475569; font-size: 0.95rem; line-height: 1.5; margin: 0; }
</style>
"""

# ============================================================
# 2. FUNCIONES CORE (Cubicadora)
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
    mapa["altura_total"] = encontrar_columna(cols, ["altura", "total", "pallet"]) or encontrar_columna(cols, ["peso"], ["total", "pallet"]) or encontrar_columna(cols, ["altura", "paletizada"])
    
    df_trabajo = df_original.copy()
    df_trabajo[mapa["sku"]] = df_trabajo[mapa["sku"]].astype(str).str.strip()
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
    niveles_por_altura, niveles_por_peso = float('inf'), float('inf')
    if all(es_numero(v) and v > 0 for v in [altura_total, altura_pallet, alto]) and altura_total > altura_pallet:
        niveles_por_altura = math.floor((altura_total - altura_pallet) / alto)
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
    if modo == "OPTIMO": cap_usada = cap_optima if cap_optima > 0 else int(round(cap_excel)) if es_numero(cap_excel) else 0
    else: cap_usada = int(round(cap_excel)) if (es_numero(cap_excel) and cap_excel > 0) else cap_optima
    pallets = int(math.ceil(stock / cap_usada)) if stock > 0 and cap_usada > 0 else 0
    ult_unids = (stock - (pallets - 1) * cap_usada) if pallets > 0 else 0
    if ult_unids == 0 and stock > 0: ult_unids = cap_usada
    ult_pct = (ult_unids / cap_usada * 100) if cap_usada > 0 else 0
    peso_pallet = (cap_usada * peso_unitario) + PESO_MADERA_PALLET if es_numero(peso_unitario) else np.nan
    estado = "✅ OK"
    if stock <= 0: estado = "❌ SIN STOCK"
    elif cap_usada <= 0: estado = "⚠️ REVISAR DATOS"
    elif es_numero(peso_pallet) and peso_pallet > MAX_PESO_PALLET: estado = "🚨 SOBREPESO (>1200kg)"
    return {"Capacidad_Usada": cap_usada, "Pallets": pallets, "Unidades_Ultimo": ult_unids, "Ocupacion_Ultimo": ult_pct, "Peso_Pallet": peso_pallet, "Estado": estado, "Cap_Excel": cap_excel, "Cap_Optima": cap_optima}

def generar_excel_descarga(df_original, df_resultados, mapa):
    output = io.BytesIO()
    comparativo_rows = []
    for _, row in df_resultados.iterrows():
        m_excel = calcular_metricas_dinamicas(row, mapa, "EXCEL")
        m_opt = calcular_metricas_dinamicas(row, mapa, "OPTIMO")
        comparativo_rows.append({
            "SKU": row[mapa["sku"]], "Stock": row[mapa["stock"]],
            "Capacidad_Excel": m_excel["Cap_Excel"], "Capacidad_Optima": m_opt["Cap_Optima"],
            "Pallets_Req_Excel": m_excel["Pallets"], "Pallets_Req_Optimo": m_opt["Pallets"]
        })
    df_sheet1 = pd.DataFrame(comparativo_rows)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sheet1.to_excel(writer, sheet_name="1_Analisis_Comparativo", index=False)
        df_original.copy().to_excel(writer, sheet_name="2_Data_Original", index=False)
        df_resultados.to_excel(writer, sheet_name="3_Data_Optimizada", index=False)
    output.seek(0)
    return output

# ============================================================
# 3. FUNCIONES VISUALES 2D / 3D (CUBICADORA)
# ============================================================
def es_formato_circular(formato):
    if pd.isna(formato): return False
    return any(k in norm_txt(formato) for k in ["tambor", "balde", "bidon", "cunete", "barril", "tarro", "lata"])

def get_material_css(formato):
    n = norm_txt(formato)
    if any(k in n for k in ["tambor", "balde", "bidon", "lata"]): return {"bg_top": "radial-gradient(circle at 35% 35%, #93c5fd, #1d4ed8)", "bg_side": "linear-gradient(to right, #1e3a8a, #60a5fa 30%, #3b82f6 60%, #1e3a8a)", "border": "#1e3a8a", "radius": "50%", "shadow": "inset -3px -3px 6px rgba(0,0,0,0.4), 2px 3px 5px rgba(0,0,0,0.25)"}
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
                traces.append(go.Scatter3d(x=cx + (radio - 0.2) * np.cos(theta), y=cy + (radio - 0.2) * np.sin(theta), z=np.full(24, z_base + alto - 0.5), mode='lines', line=dict(color='#1e3a8a', width=3), showlegend=False, hoverinfo='none'))
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
def motor_calculo_layout(df_activa, is_vertical, pal_v, conf):
    l_m, a_m, alt_m = conf['l_bod'], conf['a_bod'], conf['alt_bod']
    w_p, flujo = conf['ancho_porton'], conf['tipo_flujo']
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
    niveles_operativos = sum(1 for n in range(50) if n*alt_nivel_viga+ap_h+0.15 <= alt_m and n*alt_nivel_viga <= conf['alt_grua'])
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
                                almacen.append({
                                    'pasillo': num_pasillo, 'lado': lado, 'modulo': num_modulo, 'nivel': n+1, 'slot': p_idx+1,
                                    'x': x_pos, 'y': y_rack, 'x_pal': x_pal, 'z': z_piso, 'ocupado': False, 'sku': None, 'alt_p': 0
                                })

    almacen.sort(key=lambda x: (x['nivel'], x['pasillo'], x['modulo'], x['lado'], x['slot']))
    resumen_ubicacion = []
    for _, row in df_activa.iterrows():
        sku, cant = str(row['SKU']).strip().upper(), int(row['Cantidad_Pallets'])
        alto_real_sku = float(row['Alto_m']) if 'Alto_m' in row else ap_h
        ubicados = 0
        for slot in almacen:
            if ubicados >= cant: break
            if not slot['ocupado']:
                slot.update({'ocupado': True, 'sku': sku, 'alt_p': alto_real_sku})
                ubicados += 1
        resumen_ubicacion.append({'SKU': sku, 'Pedidas': cant, 'Ubicadas': ubicados})

    total_posiciones = len(almacen)
    demanda_total = int(df_activa['Cantidad_Pallets'].sum())
    pallets_ubicados_totales = sum(r['Ubicadas'] for r in resumen_ubicacion)

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
        self.x, self.y, self.z, self.i, self.j, self.k, self.contador = [], [], [], [], [], [], 0
        self.base_i, self.base_j, self.base_k = [7,0,0,0,4,4,6,6,4,0,3,2], [3,4,1,2,5,6,5,2,0,1,6,3], [0,7,2,3,6,7,1,1,5,5,7,6]
    def agregar_cubo(self, x0, y0, z0, dx, dy, dz):
        off = self.contador * 8
        self.x.extend([x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0])
        self.y.extend([y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy])
        self.z.extend([z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz])
        self.i.extend([idx + off for idx in self.base_i])
        self.j.extend([idx + off for idx in self.base_j])
        self.k.extend([idx + off for idx in self.base_k])
        self.contador += 1
    def obtener_trazo(self):
        if self.contador == 0: return None
        return go.Mesh3d(x=self.x, y=self.y, z=self.z, i=self.i, j=self.j, k=self.k, color=self.color, opacity=self.opacidad, name=self.nombre, hoverinfo="name", showscale=False, flatshading=True)

def add_cube_rotated(capa, x0, y0, z0, dx, dy, dz, is_vertical):
    if is_vertical: capa.agregar_cubo(y0, x0, z0, dy, dx, dz)
    else: capa.agregar_cubo(x0, y0, z0, dx, dy, dz)

def generar_layout_3d(res, l_m, a_m, alt_m, is_vertical, skus_buscados, puertas):
    skus_unicos_ubicados = sorted(list(set(s['sku'] for s in res['almacen'] if s['ocupado'])))
    paleta_colores = ['#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#e74c3c']

    capas_sku = {}
    for idx, s in enumerate(skus_unicos_ubicados):
        if not skus_buscados or s in skus_buscados:
            capas_sku[s] = MallaAgrupada(paleta_colores[idx % len(paleta_colores)], f"SKU: {s}", 1.0)

    capa_pilares = MallaAgrupada('#e74c3c', 'Pilares')
    capa_oficinas = MallaAgrupada('#bdc3c7', 'Oficinas', 0.9)
    capa_staging = MallaAgrupada('#f39c12', 'Staging', 0.4)
    capa_marcos = MallaAgrupada('#2c3e50', 'Rack', 0.1 if skus_buscados else 1.0)
    capa_marcos_bloqueados = MallaAgrupada('#7f8c8d', 'Rack Inactivo', 0.4)
    capa_vigas = MallaAgrupada('#e67e22', 'Vigas', 0.1 if skus_buscados else 1.0)
    capa_maderas = MallaAgrupada('#d35400', 'Base Pallet', 1.0)

    for px, py in res['pilares_reales']:
        if px < l_m and py < a_m: capa_pilares.agregar_cubo(px - 0.25, py - 0.25, 0, 0.5, 0.5, alt_m)
    for ofi in res['oficinas']: capa_oficinas.agregar_cubo(ofi['x'], ofi['y'], 0, ofi['w'], ofi['d'], ofi.get('h', 3.5))
    for st_z in res['staging']: capa_staging.agregar_cubo(st_z['x1'], st_z['y1'], 0.01, st_z['x2'] - st_z['x1'], st_z['y2'] - st_z['y1'], 0.02)

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
        if slot['ocupado'] and ((not skus_buscados) or (slot['sku'] in skus_buscados)):
            add_cube_rotated(capa_maderas, slot['x_pal'], slot['y'] + 0.05, slot['z'] + 0.02, res['ap_w'], res['pp_d'] - 0.1, 0.12, is_vertical)
            alt_carga = slot['alt_p'] - 0.12
            add_cube_rotated(capas_sku[slot['sku']], slot['x_pal'] + 0.05, slot['y'] + 0.1, slot['z'] + 0.14, res['ap_w'] - 0.1, res['pp_d'] - 0.2, alt_carga, is_vertical)

    fig_3d = go.Figure()
    fig_3d.add_trace(go.Mesh3d(x=[0, l_m, l_m, 0, 0, l_m, l_m, 0], y=[0, 0, a_m, a_m, 0, 0, a_m, a_m], z=[-0.1, -0.1, -0.1, -0.1, 0, 0, 0, 0], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='#ecf0f1', showscale=False, name='Suelo'))

    for c in [capa_pilares, capa_oficinas, capa_staging, capa_marcos, capa_marcos_bloqueados, capa_vigas, capa_maderas] + list(capas_sku.values()):
        trace = c.obtener_trazo()
        if trace: fig_3d.add_trace(trace)

    fig_3d.update_layout(
        title=dict(text=f"<b>Gemelo Digital CD 3D</b><br><sup>Ubicados: {res['pallets_ubicados_totales']} pallets</sup>", x=0.5),
        scene=dict(xaxis=dict(range=[-5, l_m + 5]), yaxis=dict(range=[-5, a_m + 5]), zaxis=dict(range=[0, alt_m + 1]), aspectmode='data', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
        margin=dict(r=0, l=0, b=0, t=80), height=750, paper_bgcolor='white'
    )
    return fig_3d

# ============================================================
# 5. MÓDULOS DE PÁGINAS (UI)
# ============================================================

def cambiar_menu(pagina):
    st.session_state.menu_seleccion = pagina

def mostrar_portada():
    st.markdown(color_styles, unsafe_allow_html=True)
    
    # HERO BANNER CENTRADO Y LIMPIO
    st.markdown("""
    <div class="hero-container-color">
        <div class="hero-title-color">WMS Analytics Hub</div>
        <div class="hero-subtitle-color">Plataforma integral de ingeniería logística para la optimización de almacenamiento, cubicación geométrica y diseño avanzado de layout de bodegas.</div>
    </div>
    """, unsafe_allow_html=True)

    # MATRIZ 2X2 CON DETALLES DE COLOR
    st.markdown("<h3 style='color:#0f172a; font-weight:800; margin-bottom: 20px;'>MÓDULOS DE CONTROL</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="color-card">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📦</span>
                    <span class="card-tag-color tag-blue">DISPONIBLE</span>
                </div>
                <div class="color-card-title">Cubicadora de Pallets</div>
                <p class="color-card-desc">Cálculo algorítmico de volumen, estiba optimizada de productos y previsualización gráfica 2D/3D en tiempo real.</p>
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
                <p class="color-card-desc">Diseñador espacial de Centro de Distribución, optimización de flujos de tránsito y Gemelo Digital 3D interactivo.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("⚙️ Abrir Diseñador Layout", key="btn_lay", type="primary", use_container_width=True, on_click=cambiar_menu, args=("🏗️ Layout de Bodega",))
        st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
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

    with col4:
        st.markdown("""
        <div class="color-card color-card-purple" style="opacity: 0.85;">
            <div>
                <div class="card-icon-header">
                    <span class="card-icon">📊</span>
                    <span class="card-tag-color tag-purple">NUEVO</span>
                </div>
                <div class="color-card-title">Analytics & Reportería Ejecutivo</div>
                <p class="color-card-desc">Dashboard de indicadores clave (KPIs), volumetría total, matrices de ocupación y análisis gerencial.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("📊 Abrir Dashboard Analytics", key="btn_an", type="primary", use_container_width=True, on_click=cambiar_menu, args=("📊 Analytics & Reportería",))


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
        df_resultados, MAPA = st.session_state.df_resultados, st.session_state.mapa_columnas
        modo = st.radio("⚙️ Modo de cálculo:", ["EXCEL", "OPTIMO"], horizontal=True)
        tot_p = sum([calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"] for _, row in df_resultados.iterrows()])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 SKU Analizados", len(df_resultados))
        col2.metric("🟢 SKUs con Stock", int((pd.to_numeric(df_resultados[MAPA["stock"]], errors="coerce").fillna(0) > 0).sum()))
        col3.metric("🏗️ Pallets Requeridos", f"{tot_p:,}")

        st.markdown("---")
        tab_buscar, tab_descargar, tab_alertas, tab_datos = st.tabs(["🔍 Visualizador de Planos", "📥 Descargar Reporte", "🚨 Ver Alertas", "📊 Base de Datos"])

        with tab_buscar:
            lista_skus = df_resultados[MAPA["sku"]].astype(str).unique().tolist()
            opcion = st.radio("Visualización:", ["Elegir de la lista", "Ver primeros 10", "Ver TODOS"], horizontal=True)
            if opcion == "Elegir de la lista": skus_a_procesar = st.multiselect("SKUs:", options=lista_skus, default=[lista_skus[0]] if lista_skus else [])
            elif opcion == "Ver primeros 10": skus_a_procesar = lista_skus[:10]
            else: skus_a_procesar = lista_skus

            if st.button("🚀 Generar Planos", type="primary"): st.session_state.skus_activos = skus_a_procesar

            if st.session_state.skus_activos:
                for sku in st.session_state.skus_activos:
                    filtro = df_resultados[df_resultados[MAPA["sku"]].astype(str).str.upper() == str(sku).upper()]
                    if not filtro.empty:
                        fila = filtro.iloc[0]
                        m = calcular_metricas_dinamicas(fila, MAPA, modo)
                        st.info(f"**SKU:** {sku} | **Estado:** {m['Estado']} | **Formato:** {fila[MAPA['formato']]}")
                        col_izq, col_der = st.columns([1, 3])
                        with col_izq:
                            st.write(f"**Dimensiones:** {fmt(a_float(valor_col(fila, 'largo', MAPA)))}x{fmt(a_float(valor_col(fila, 'ancho', MAPA)))}x{fmt(a_float(valor_col(fila, 'alto', MAPA)))} cm")
                            st.write(f"**Peso:** {fmt(a_float(valor_col(fila, 'peso', MAPA)), 2)} kg | **Unidades Pallet:** {fmt(m['Capacidad_Usada'], 0)}")
                            mostrar_3d_sku = st.toggle(f"🧊 Activar Motor 3D", key=f"t_{sku}")
                        with col_der:
                            c_pb1, c_pb2, c_pb3 = st.columns(3)
                            with c_pb1: st.markdown(html_vista_superior(fila, MAPA), unsafe_allow_html=True)
                            with c_pb2: st.markdown(html_vista_lateral(fila, MAPA, m['Capacidad_Usada']), unsafe_allow_html=True)
                            with c_pb3: 
                                if mostrar_3d_sku: st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m['Capacidad_Usada']), use_container_width=True, key=f"pb_{sku}")
                            st.markdown("---")
                            c_ps1, c_ps2, c_ps3 = st.columns(3)
                            with c_ps1: st.markdown(html_vista_superior(fila, MAPA, m['Unidades_Ultimo']), unsafe_allow_html=True)
                            with c_ps2: st.markdown(html_vista_lateral(fila, MAPA, m['Capacidad_Usada'], m['Unidades_Ultimo']), unsafe_allow_html=True)
                            with c_ps3: 
                                if mostrar_3d_sku: st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m['Capacidad_Usada'], m['Unidades_Ultimo']), use_container_width=True, key=f"ps_{sku}")
                    st.divider()

        with tab_descargar:
            st.write("Genera un Excel completo con TODOS los cálculos de los SKUs.")
            excel_data = generar_excel_descarga(st.session_state.df_original, df_resultados, MAPA)
            st.download_button("📊 Descargar Reporte Excel", data=excel_data, file_name="Reporte_Optimizacion.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with tab_alertas:
            alertas = [{"SKU": row[MAPA["sku"]], "Estado": calcular_metricas_dinamicas(row, MAPA, modo)["Estado"], "Pallets": calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"]} for _, row in df_resultados.iterrows() if "❌" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"] or "⚠️" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"] or "🚨" in calcular_metricas_dinamicas(row, MAPA, modo)["Estado"]]
            if alertas: st.warning(f"Se encontraron {len(alertas)} SKUs con alertas."); st.dataframe(pd.DataFrame(alertas), use_container_width=True)
            else: st.success("🎉 ¡Excelente! No hay alertas.")
        with tab_datos: st.dataframe(df_resultados, use_container_width=True)
    else: st.info("👆 Sube tu archivo Excel para comenzar.")

def mostrar_layout():
    st.title("🏗️ Diseñador de Layout de Bodega")
    
    if st.session_state.df_resultados is None:
        st.error("⚠️ Para usar el Layout, primero debes cargar el Excel en el módulo 'Cubicadora WMS'.")
        return

    df_orig, df_res, MAPA = st.session_state.df_original.copy(), st.session_state.df_resultados.copy(), st.session_state.mapa_columnas
    df_layout_orig, df_layout_opt = pd.DataFrame(), pd.DataFrame()
    
    df_layout_orig['SKU'] = df_orig[MAPA['sku']]
    stock_op = pd.to_numeric(df_orig[MAPA['stock']], errors='coerce').fillna(0)
    unid_pal = pd.to_numeric(df_orig[MAPA['unidades_pallet']], errors='coerce').fillna(0).replace(0, np.nan)
    df_layout_orig['Cantidad_Pallets'] = np.ceil(stock_op / unid_pal)
    df_layout_orig['Alto_m'] = pd.to_numeric(df_orig[MAPA['altura_total']], errors='coerce').fillna(120) / 100.0

    df_layout_opt['SKU'] = df_res[MAPA['sku']]
    cap_opt = pd.to_numeric(df_res['Capacidad_Optima'], errors='coerce').fillna(0).replace(0, np.nan)
    df_layout_opt['Cantidad_Pallets'] = np.ceil(stock_op / cap_opt)
    df_layout_opt['Alto_m'] = df_layout_orig['Alto_m']

    dict_demanda = {'Data Original': df_layout_orig[df_layout_orig['Cantidad_Pallets'] > 0], 'Data Optimizada': df_layout_opt[df_layout_opt['Cantidad_Pallets'] > 0]}

    with st.expander("⚙️ PANEL MASTER CD (Configuración de Bodega)", expanded=True):
        col_inf, col_dr, col_op, col_an = st.columns(4)
        with col_inf:
            st.markdown("<h4 style='color:#2980b9;'>🏢 Infraestructura</h4>", unsafe_allow_html=True)
            st.session_state.l_bod = st.number_input('Largo Bodega (m):', value=st.session_state.l_bod)
            st.session_state.a_bod = st.number_input('Ancho Bodega (m):', value=st.session_state.a_bod)
            st.session_state.alt_bod = st.number_input('Alto Útil (m):', value=st.session_state.alt_bod)
            st.session_state.cant_pilares_x = st.number_input('Pilares X:', value=st.session_state.cant_pilares_x)
            st.session_state.dist_pilares_x = st.number_input('Dist. Pilares X (m):', value=st.session_state.dist_pilares_x)
        with col_dr:
            st.markdown("<h4 style='color:#27ae60;'>📦 Estructura</h4>", unsafe_allow_html=True)
            st.session_state.pallets_viga = st.selectbox('Config. Viga (Pallets):', [1, 2, 3], index=[1,2,3].index(st.session_state.pallets_viga))
            st.session_state.alt_grua = st.number_input('Alt. Máx. Grúa (m):', value=st.session_state.alt_grua)
        with col_op:
            st.markdown("<h4 style='color:#e67e22;'>🚜 Operación</h4>", unsafe_allow_html=True)
            st.session_state.tipo_flujo = st.selectbox('Flujo:', ['Ninguno', 'Flujo en U', 'Flujo en I (Línea Recta)', 'Flujo en L'], index=['Ninguno', 'Flujo en U', 'Flujo en I (Línea Recta)', 'Flujo en L'].index(st.session_state.tipo_flujo))
            st.session_state.orientacion_rack = st.selectbox('Orientación:', ['Automática', 'Horizontal (X)', 'Vertical (Y)'], index=['Automática', 'Horizontal (X)', 'Vertical (Y)'].index(st.session_state.orientacion_rack))
            st.session_state.pasillo = st.number_input('Ancho Pasillo (m):', value=st.session_state.pasillo)
        with col_an:
            st.markdown("<h4 style='color:#8e44ad;'>🔍 Análisis</h4>", unsafe_allow_html=True)
            st.session_state.fuente_datos = st.selectbox('Fuente:', ['Data Original', 'Data Optimizada'], index=['Data Original', 'Data Optimizada'].index(st.session_state.fuente_datos))
            st.session_state.filtro_sublayout = st.text_area('✂️ Filtrar SKUs:', value=st.session_state.filtro_sublayout, height=68)
            
            if st.button("🏢 Generar Layout", type="primary", use_container_width=True): st.session_state.layout_generado = True
            if st.button("🧠 IA: Optimizar Layout", use_container_width=True):
                with st.spinner("⏳ Calculando combinaciones..."):
                    raw = st.session_state.filtro_sublayout.strip()
                    skus_busc = set(s.strip().upper() for s in re.split(r'[\n,\t\r;]+', raw) if s.strip())
                    is_filt = bool(skus_busc and raw.upper() != 'TODOS')
                    escenarios = []
                    for f in ['Data Original', 'Data Optimizada']:
                        df_test = dict_demanda[f][dict_demanda[f]['SKU'].astype(str).str.upper().isin(skus_busc)].copy() if is_filt else dict_demanda[f].copy()
                        if df_test.empty: continue
                        for o in [True, False]:
                            for v in [2, 3]:
                                res = motor_calculo_layout(df_test, o, v, st.session_state)
                                res.update({'fuente': f, 'is_vertical': o, 'pal_v': v})
                                escenarios.append(res)
                    if escenarios:
                        mejor = max(escenarios, key=lambda x: x['diferencia'])
                        st.session_state.fuente_datos, st.session_state.orientacion_rack, st.session_state.pallets_viga = mejor['fuente'], 'Vertical (Y)' if mejor['is_vertical'] else 'Horizontal (X)', mejor['pal_v']
                        st.session_state.layout_generado = True
                        st.success(f"🧠 IA Aplicada: {mejor['fuente']}, {'Vertical' if mejor['is_vertical'] else 'Horizontal'}, {mejor['pal_v']} por viga.")
                        st.rerun()

    if st.session_state.layout_generado:
        st.markdown("---")
        raw = st.session_state.filtro_sublayout.strip()
        skus_buscados = set(s.strip().upper() for s in re.split(r'[\n,\t\r;]+', raw) if s.strip())
        is_filtrado = bool(skus_buscados and raw.upper() != 'TODOS')
        
        df_activa = dict_demanda[st.session_state.fuente_datos]
        if is_filtrado: df_activa = df_activa[df_activa['SKU'].astype(str).str.upper().isin(skus_buscados)].copy()
        
        is_vert = ('Vertical' in st.session_state.orientacion_rack) if 'Automática' not in st.session_state.orientacion_rack else (st.session_state.tipo_flujo in ['Flujo en U', 'Flujo en I (Línea Recta)'])
        res = motor_calculo_layout(df_activa, is_vert, st.session_state.pallets_viga, st.session_state)

        dif = res['diferencia']
        if dif >= 0: st.success(f"✔️ ¡ÉXITO! Caben todos y sobran {dif:,} posiciones. (Capacidad: {res['capacidad']:,} | Demanda: {res['demanda']:,})")
        else: st.error(f"⚠️ ¡ALERTA! Faltan {abs(dif):,} posiciones. (Capacidad: {res['capacidad']:,} | Demanda: {res['demanda']:,})")

        # PLOTLY 2D
        l_m, a_m, w_puerta, flujo = st.session_state.l_bod, st.session_state.a_bod, st.session_state.ancho_porton, st.session_state.tipo_flujo
        fig_2d = go.Figure()
        fig_2d.add_shape(type="rect", x0=0, y0=0, x1=l_m, y1=a_m, line=dict(color="#2c3e50", width=4), fillcolor="#fafafa")
        
        pp_d, l_modulo = 1.2, (1.2 * st.session_state.pallets_viga) + (0.10 * (st.session_state.pallets_viga + 1)) + 0.10
        path_free, path_block, path_pil = [], [], []
        
        for mod in res['modulos_list']:
            x_pos, y_rack = mod['x'], mod['y']
            rx0, ry0, rx1, ry1 = (y_rack, x_pos, y_rack+pp_d, x_pos+l_modulo) if is_vert else (x_pos, y_rack, x_pos+l_modulo, y_rack+pp_d)
            path = f"M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1} L {rx0} {ry1} Z"
            if mod['bloqueado']: path_block.append(path)
            else: path_free.append(path)

        for px, py in res['pilares_reales']:
            rx0, ry0, rx1, ry1 = (py-0.25, px-0.25, py+0.25, px+0.25) if is_vert else (px-0.25, py-0.25, px+0.25, py+0.25)
            path_pil.append(f"M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1} L {rx0} {ry1} Z")

        if path_free: fig_2d.add_shape(type="path", path=" ".join(path_free), fillcolor="#3498db", line=dict(color="#2980b9", width=1))
        if path_block: fig_2d.add_shape(type="path", path=" ".join(path_block), fillcolor="#95a5a6", line=dict(color="#7f8c8d", width=1))
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

        fig_2d.update_layout(title="Plano CAD 2D del Centro de Distribución", xaxis=dict(range=[-2, l_m+2]), yaxis=dict(range=[-2, a_m+2], scaleanchor="x", scaleratio=1), height=600, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_2d, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        mostrar_3d_layout = st.toggle("🧊 Cargar Gemelo Digital 3D (Puede tardar unos segundos dependiendo del tamaño de tu bodega)")
        
        if mostrar_3d_layout:
            with st.spinner("Construyendo Mallas 3D de la Bodega..."):
                fig_3d = generar_layout_3d(res, l_m, a_m, st.session_state.alt_bod, is_vert, skus_buscados, puertas)
                st.plotly_chart(fig_3d, use_container_width=True)

# ============================================================
# NUEVO MÓDULO: ANALYTICS & REPORTERÍA EJECUTIVO
# ============================================================
def mostrar_analytics():
    st.title("📊 Analytics & Reportería Ejecutivo")
    
    if st.session_state.df_resultados is None:
        st.error("⚠️ Para visualizar el Dashboard de Analytics, primero debes cargar tu base de datos en el módulo 'Cubicadora WMS'.")
        return

    df_res = st.session_state.df_resultados.copy()
    MAPA = st.session_state.mapa_columnas

    # Cálculos globales
    df_res['Stock_Num'] = pd.to_numeric(df_res[MAPA['stock']], errors='coerce').fillna(0)
    df_res['Peso_Num'] = pd.to_numeric(df_res[MAPA['peso']], errors='coerce').fillna(0)
    
    # Calcular métricas para Excel y Óptimo
    metrics_excel = [calcular_metricas_dinamicas(row, MAPA, "EXCEL") for _, row in df_res.iterrows()]
    metrics_opt = [calcular_metricas_dinamicas(row, MAPA, "OPTIMO") for _, row in df_res.iterrows()]

    df_res['Pallets_Req_Excel'] = [m['Pallets'] for m in metrics_excel]
    df_res['Pallets_Req_Optimo'] = [m['Pallets'] for m in metrics_opt]
    df_res['Cap_Excel_Used'] = [m['Capacidad_Usada'] for m in metrics_excel]
    df_res['Cap_Opt_Used'] = [m['Capacidad_Usada'] for m in metrics_opt]
    df_res['Ocupacion_Ult_Pct'] = [m['Ocupacion_Ultimo'] for m in metrics_excel]
    df_res['Estado_Sku'] = [m['Estado'] for m in metrics_excel]

    # Cálculos Volumétricos
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
    num_alertas = sum(1 for m in metrics_excel if "❌" in m["Estado"] or "⚠️" in m["Estado"] or "🚨" in m["Estado"])

    # 1. MACRO KPIs
    st.markdown("### 📈 Indicadores Macro de Almacenamiento")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Volumen Total Carga", f"{vol_total_bodega:,.1f} m³")
    m2.metric("🏗️ Pallets Requeridos (Excel)", f"{tot_pallets_excel:,} pal")
    m3.metric("🎯 Pallets Requeridos (Óptimo)", f"{tot_pallets_opt:,} pal", delta=f"{-ahorro_pallets:,} pal ({pct_ahorro:.1f}%)", delta_color="inverse")
    m4.metric("🚨 SKUs con Alertas", f"{num_alertas} SKUs", delta="Atención Requerida" if num_alertas > 0 else "Todo OK", delta_color="off")

    st.markdown("---")

    # 2. FILA DE GRÁFICOS 1
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("#### 🍩 Distribución de SKUs por Formato de Envase")
        df_formato = df_res[MAPA['formato']].value_counts().reset_index()
        df_formato.columns = ['Formato', 'Cantidad']
        fig_donut = px.pie(df_formato, values='Cantidad', names='Formato', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_donut.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

    with g2:
        st.markdown("#### 📊 Top 10 SKUs con Mayor Requerimiento de Pallets")
        df_top10 = df_res.sort_values(by='Pallets_Req_Excel', ascending=False).head(10)
        fig_top = px.bar(df_top10, x='Pallets_Req_Excel', y=MAPA['sku'], orientation='h', text='Pallets_Req_Excel', color='Pallets_Req_Excel', color_continuous_scale='Blues')
        fig_top.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=30, b=20), height=350, showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("---")

    # 3. FILA DE GRÁFICOS 2
    g3, g4 = st.columns(2)

    with g3:
        st.markdown("#### 📉 Comparativa de Pallets: Excel vs. Óptimo (Top 15 SKUs)")
        df_comp = df_res.head(15)
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_comp[MAPA['sku']], y=df_comp['Pallets_Req_Excel'], name='Excel (Manual)', marker_color='#3b82f6'))
        fig_comp.add_trace(go.Bar(x=df_comp[MAPA['sku']], y=df_comp['Pallets_Req_Optimo'], name='Óptimo Algorítmico', marker_color='#10b981'))
        fig_comp.update_layout(barmode='group', margin=dict(l=20, r=20, t=30, b=20), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_comp, use_container_width=True)

    with g4:
        st.markdown("#### ⚖️ Matriz Peso por Pallet vs. % Ocupación Último Pallet")
        df_res['Peso_Pallet_Kg'] = [m['Peso_Pallet'] for m in metrics_excel]
        fig_scatter = px.scatter(
            df_res, x='Ocupacion_Ult_Pct', y='Peso_Pallet_Kg', size='Stock_Num', color='Estado_Sku',
            hover_name=MAPA['sku'], labels={'Ocupacion_Ult_Pct': '% Ocupación Último Pallet', 'Peso_Pallet_Kg': 'Peso Total Pallet (kg)'},
            color_discrete_map={"✅ OK": "#10b981", "❌ SIN STOCK": "#64748b", "⚠️ REVISAR DATOS": "#f59e0b", "🚨 SOBREPESO (>1200kg)": "#ef4444"}
        )
        fig_scatter.add_hline(y=MAX_PESO_PALLET, line_dash="dash", line_color="red", annotation_text="Límite Peso (1200kg)")
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
        st.plotly_chart(fig_scatter, use_container_width=True)


# ============================================================
# 6. MENÚ DE NAVEGACIÓN PRINCIPAL (SIDEBAR)
# ============================================================

menu_opciones = ["🏠 Portada Principal", "📦 Cubicadora WMS", "🏗️ Layout de Bodega", "📊 Analytics & Reportería"]
st.session_state.menu_seleccion = st.sidebar.radio(
    "Navegación", 
    menu_opciones,
    index=menu_opciones.index(st.session_state.menu_seleccion)
)

st.sidebar.markdown("---")
st.sidebar.caption("WMS Analytics Hub v5.0 • Executive Suite")

if st.session_state.menu_seleccion == "🏠 Portada Principal": mostrar_portada()
elif st.session_state.menu_seleccion == "📦 Cubicadora WMS": mostrar_cubicadora()
elif st.session_state.menu_seleccion == "🏗️ Layout de Bodega": mostrar_layout()
elif st.session_state.menu_seleccion == "📊 Analytics & Reportería": mostrar_analytics()
