import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import re
import unicodedata
import io

# ============================================================
# 1. CONFIGURACIÓN INICIAL Y MEMORIA
# ============================================================
# Debe ser la primera instrucción de Streamlit
st.set_page_config(page_title="WMS Analytics Hub", layout="wide", page_icon="🏢")

MAX_PESO_PALLET = 1200
PESO_MADERA_PALLET = 25

# Variables de memoria para la cubicadora
if "skus_activos" not in st.session_state:
    st.session_state.skus_activos = []
if "mostrar_3d" not in st.session_state:
    st.session_state.mostrar_3d = False

# CSS Global para los gráficos 3D HTML
css_styles = """
<style>
    .box-3d { transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: crosshair; }
    .box-3d:hover { transform: scale(1.08) translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.4) !important; z-index: 100 !important; filter: brightness(1.1); }
    .cota-linea { border-left: 1px solid #64748b; border-right: 1px solid #64748b; position: absolute; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #475569; font-weight: bold; background-image: linear-gradient(#64748b, #64748b); background-size: 100% 1px; background-position: center; background-repeat: no-repeat; }
    .cota-linea-v { border-top: 1px solid #64748b; border-bottom: 1px solid #64748b; border-left: none; border-right: none; position: absolute; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #475569; font-weight: bold; background-image: linear-gradient(#64748b, #64748b); background-size: 1px 100%; background-position: center; background-repeat: no-repeat; flex-direction: column; }
    .cota-texto { background: white; padding: 2px 4px; border-radius: 3px; z-index: 2; }
</style>
"""

# ============================================================
# 2. FUNCIONES MATEMÁTICAS Y DE PROCESAMIENTO (Core)
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
# 3. FUNCIONES DE RENDERIZADO VISUAL 2D Y 3D
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
    # Dibujar pallet
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
# 4. DEFINICIÓN DE PÁGINAS (PORTADA, CUBICADORA Y LAYOUT)
# ============================================================

def mostrar_portada():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 80px 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
        <h1 style="font-size: 3.5rem; margin-bottom: 10px; font-weight: 900; color: #ffffff; letter-spacing: -1px;">WMS Analytics Hub</h1>
        <p style="font-size: 1.3rem; color: #cbd5e1; max-width: 800px; margin: 0 auto; line-height: 1.6;">Plataforma integral de ingeniería logística para la optimización de almacenamiento, cubicación geométrica y diseño avanzado de layout de bodegas.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); height: 100%;">
            <div style="font-size: 3rem; margin-bottom: 15px;">📦</div>
            <h2 style="color: #0f172a; margin-top: 0; font-weight: 800;">Cubicadora de Pallets</h2>
            <p style="color: #475569; font-size: 1.1rem; line-height: 1.6;">Herramienta algorítmica para optimizar la estiba de productos. Calcula automáticamente capacidades máximas, alertas de sobrepeso y genera renders en 2D y 3D para tus operarios.</p>
            <br>
            <p style="color: #3b82f6; font-weight: 700; font-size: 1rem;">👉 Accede desde el menú lateral</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); height: 100%; position: relative; overflow: hidden;">
            <div style="font-size: 3rem; margin-bottom: 15px;">🏗️</div>
            <h2 style="color: #0f172a; margin-top: 0; font-weight: 800;">Layout de Bodega</h2>
            <p style="color: #475569; font-size: 1.1rem; line-height: 1.6;">Módulo de diseño visual para mapear tu almacén, asignar ubicaciones de rack, optimizar rutas de picking y conectar zonas de tránsito.</p>
            <br>
            <span style="background: #f59e0b; color: white; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px;">EN DESARROLLO</span>
        </div>
        """, unsafe_allow_html=True)


def mostrar_cubicadora():
    st.markdown(css_styles, unsafe_allow_html=True)
    st.title("📦 Cubicadora de Palletización Masiva")

    archivo_subido = st.file_uploader("📂 Sube tu archivo Excel con la base de datos", type=["xlsx"])

    if archivo_subido is not None:
        with st.spinner("Procesando toda la base de datos..."):
            try: df_original = pd.read_excel(archivo_subido, sheet_name="Data Equipo 7")
            except: df_original = pd.read_excel(archivo_subido, sheet_name=0)
            df_resultados, MAPA = procesar_datos(df_original.dropna(how="all").reset_index(drop=True))

        modo = st.radio("⚙️ Selecciona el modo de cálculo para todo el reporte:", ["EXCEL", "OPTIMO"], horizontal=True)
        tot_p = sum([calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"] for _, row in df_resultados.iterrows()])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total SKU Analizados", len(df_resultados))
        col2.metric("🟢 SKUs con Stock", int((pd.to_numeric(df_resultados[MAPA["stock"]], errors="coerce").fillna(0) > 0).sum()))
        col3.metric("🏗️ Pallets Totales Requeridos", f"{tot_p:,}")

        st.markdown("---")
        
        tab_buscar, tab_descargar, tab_alertas, tab_datos = st.tabs(["🔍 Visualizador de Planos", "📥 Descargar Reporte Completo", "🚨 Ver Alertas", "📊 Ver Base de Datos"])

        with tab_buscar:
            st.subheader("Buscador de SKUs")
            lista_skus_disponibles = df_resultados[MAPA["sku"]].astype(str).unique().tolist()
            
            opcion_seleccion = st.radio(
                "¿Cómo quieres visualizar los planos?", 
                ["Elegir de la lista (Recomendado)", "Ver los primeros 10 SKUs", "Ver TODOS los SKUs de golpe (Cuidado: puede demorar)"],
                horizontal=True
            )

            skus_a_procesar = []
            if opcion_seleccion == "Elegir de la lista (Recomendado)":
                skus_a_procesar = st.multiselect("Selecciona uno o varios SKUs de la lista:", options=lista_skus_disponibles, default=[lista_skus_disponibles[0]] if lista_skus_disponibles else [])
            elif opcion_seleccion == "Ver los primeros 10 SKUs":
                skus_a_procesar = lista_skus_disponibles[:10]
            else:
                skus_a_procesar = lista_skus_disponibles

            if st.button("🚀 Generar Planos", type="primary"):
                st.session_state.skus_activos = skus_a_procesar

            if st.session_state.skus_activos:
                st.markdown(f"**Mostrando planos para {len(st.session_state.skus_activos)} SKUs:**")
                
                for sku in st.session_state.skus_activos:
                    filtro = df_resultados[df_resultados[MAPA["sku"]].astype(str).str.upper() == str(sku).upper()]
                    if not filtro.empty:
                        fila = filtro.iloc[0]
                        m = calcular_metricas_dinamicas(fila, MAPA, modo)
                        st.info(f"**SKU:** {sku} | **Estado:** {m['Estado']} | **Formato:** {fila[MAPA['formato']]}")
                        
                        col_izq, col_der = st.columns([1, 3])
                        
                        with col_izq:
                            st.markdown("### 📋 Datos Base")
                            st.write(f"**Largo:** {fmt(a_float(valor_col(fila, 'largo', MAPA)))} cm")
                            st.write(f"**Ancho:** {fmt(a_float(valor_col(fila, 'ancho', MAPA)))} cm")
                            st.write(f"**Alto:** {fmt(a_float(valor_col(fila, 'alto', MAPA)))} cm")
                            st.write(f"**Peso:** {fmt(a_float(valor_col(fila, 'peso', MAPA)), 2)} kg")
                            st.markdown("### ⚙️ Resultados")
                            st.write(f"**Modo Actual:** {modo}")
                            st.write(f"**Unids Pallet:** {fmt(m['Capacidad_Usada'], 0)} u")
                            st.write(f"**Pallets Requeridos:** {m['Pallets']}")
                            st.write(f"**Últ. Pallet:** {m['Ocupacion_Ultimo']:.1f}%")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            mostrar_3d_sku = st.toggle(f"🧊 Activar Motor 3D", key=f"toggle_3d_{sku}")

                        with col_der:
                            st.markdown(f"#### 📦 PALLET BASE ({m['Capacidad_Usada']} UNIDADES)")
                            c_pb1, c_pb2, c_pb3 = st.columns(3)
                            with c_pb1: components.html(css_styles + html_vista_superior(fila, MAPA), height=300)
                            with c_pb2: components.html(css_styles + html_vista_lateral(fila, MAPA, m['Capacidad_Usada']), height=300)
                            with c_pb3:
                                if mostrar_3d_sku: st.plotly_chart(renderizar_3d_plotly(fila, MAPA, cap_usada=m['Capacidad_Usada']), use_container_width=True, key=f"plot_base_{sku}")
                                else: st.warning("Motor 3D apagado (usa el interruptor)")

                            st.markdown("---")
                            st.markdown(f"#### 🧩 ÚLTIMO PALLET ({m['Unidades_Ultimo']} UNIDADES | {m['Ocupacion_Ultimo']:.1f}%)")
                            c_ps1, c_ps2, c_ps3 = st.columns(3)
                            with c_ps1: components.html(css_styles + html_vista_superior(fila, MAPA, cantidad_unidades=m['Unidades_Ultimo']), height=300)
                            with c_ps2: components.html(css_styles + html_vista_lateral(fila, MAPA, m['Capacidad_Usada'], total_unidades=m['Unidades_Ultimo']), height=300)
                            with c_ps3:
                                if mostrar_3d_sku: st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m['Capacidad_Usada'], total_unidades=m['Unidades_Ultimo']), use_container_width=True, key=f"plot_sob_{sku}")
                                else: st.warning("Motor 3D apagado (usa el interruptor)")
                    else:
                        st.error(f"❌ SKU '{sku}' no encontrado.")
                    st.divider()

        with tab_descargar:
            st.subheader("📥 Generar Reporte Excel Completo")
            st.write("Genera un Excel con 3 hojas (Comparativo, Original, Optimizada) con TODOS los cálculos de los SKUs.")
            excel_data = generar_excel_descarga(df_original, df_resultados, MAPA)
            st.download_button(label="📊 Descargar Reporte Excel", data=excel_data, file_name="Reporte_Paletizacion_Optimizado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with tab_alertas:
            st.subheader("🚨 Control de Alertas")
            alertas = []
            for _, row in df_resultados.iterrows():
                m = calcular_metricas_dinamicas(row, MAPA, modo)
                if "❌" in m["Estado"] or "⚠️" in m["Estado"] or "🚨" in m["Estado"]:
                    alertas.append({"SKU": row[MAPA["sku"]], "Estado": m["Estado"], "Stock": row[MAPA["stock"]], "Pallets": m["Pallets"]})
            if alertas:
                st.warning(f"Se encontraron {len(alertas)} SKUs con alertas.")
                st.dataframe(pd.DataFrame(alertas), use_container_width=True)
            else:
                st.success("🎉 ¡Excelente! No se encontraron problemas de sobrepeso ni falta de datos.")

        with tab_datos:
            st.subheader("📊 Base de Datos Pre-calculada")
            st.dataframe(df_resultados, use_container_width=True)
    else:
        st.info("👆 Sube tu archivo en la parte superior para comenzar a utilizar la cubicadora.")


def mostrar_layout():
    st.title("🏗️ Diseñador de Layout de Bodega")
    st.info("Este módulo está en construcción. Aquí integraremos las herramientas para visualizar y gestionar el mapa físico de la bodega, ubicaciones y rutas de picking.")
    st.image("https://images.unsplash.com/photo-1586528116311-ad8ed7c663e0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", caption="Próximamente", use_column_width=True)

# ============================================================
# 5. MENÚ DE NAVEGACIÓN PRINCIPAL (SIDEBAR)
# ============================================================

# Menú lateral persistente
menu_seleccion = st.sidebar.radio(
    "Menú Principal",
    ["🏠 Portada Principal", "📦 Cubicadora WMS", "🏗️ Layout de Bodega"]
)

st.sidebar.markdown("---")
st.sidebar.caption("WMS Analytics Hub v2.0")
st.sidebar.caption("Desarrollado para la optimización logística.")

# Rutas
if menu_seleccion == "🏠 Portada Principal":
    mostrar_portada()
elif menu_seleccion == "📦 Cubicadora WMS":
    mostrar_cubicadora()
elif menu_seleccion == "🏗️ Layout de Bodega":
    mostrar_layout()
