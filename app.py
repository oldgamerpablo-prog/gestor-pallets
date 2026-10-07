import base64
import io
import json
import math
import re
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
# ============================================================
# 1. CONFIGURACIÓN INICIAL Y MEMORIA
# ============================================================
st.set_page_config(page_title=&quot;WMS Analytics Hub&quot;, layout=&quot;wide&quot;,
page_icon=&quot;��&quot;)
MAX_PESO_PALLET = 1200
PESO_MADERA_PALLET = 25
if &quot;menu_seleccion&quot; not in st.session_state:
st.session_state.menu_seleccion = &quot;�� Portada Principal&quot;
if &quot;tipo_stock&quot; not in st.session_state: st.session_state.tipo_stock =
&quot;Stock Promedio&quot;
if &quot;bodegas_sel&quot; not in st.session_state: st.session_state.bodegas_sel = []
if &quot;skus_activos&quot; not in st.session_state: st.session_state.skus_activos =
[]
if &quot;skus_invalidos&quot; not in st.session_state:
st.session_state.skus_invalidos = []
if &quot;df_original&quot; not in st.session_state: st.session_state.df_original =
None
if &quot;df_resultados&quot; not in st.session_state: st.session_state.df_resultados
= None
if &quot;mapa_columnas&quot; not in st.session_state: st.session_state.mapa_columnas
= None
if &quot;historial_inbound&quot; not in st.session_state:
st.session_state.historial_inbound = pd.DataFrame(columns=[&quot;Fecha&quot;,
&quot;Proveedor&quot;, &quot;SKU&quot;, &quot;Unidades&quot;, &quot;Pallets_Generados&quot;, &quot;Ubicacion_Sugerida&quot;,
&quot;Estado&quot;])
if &quot;ordenes_picking&quot; not in st.session_state:
st.session_state.ordenes_picking = []
if &quot;tareas_movimiento&quot; not in st.session_state:
st.session_state.tareas_movimiento = []

if &quot;ultima_animacion&quot; not in st.session_state:
st.session_state.ultima_animacion = {&quot;activa&quot;: False}
parametros_layout = {
&quot;l_bod&quot;: 50.0, &quot;a_bod&quot;: 40.0, &quot;alt_bod&quot;: 7.0, &quot;cant_pilares_x&quot;: 4,
&quot;cant_pilares_y&quot;: 1,
&quot;dist_pilares_x&quot;: 20.0, &quot;dist_pilares_y&quot;: 15.0, &quot;ofi_pos_x&quot;: 0.0,
&quot;ofi_pos_y&quot;: 0.0,
&quot;ofi_largo&quot;: 10.0, &quot;ofi_ancho&quot;: 5.0, &quot;ofi_alto&quot;: 3.5, &quot;pallets_viga&quot;:
2,
&quot;peso_max_pallet&quot;: 2000.0, &quot;tipo_flujo&quot;: &quot;Flujo en I (Línea Recta)&quot;,
&quot;ancho_porton&quot;: 6.0,
&quot;orientacion_rack&quot;: &quot;Horizontal (X)&quot;, &quot;pasillo&quot;: 3.0, &quot;cant_pas_trans&quot;:
0, &quot;ancho_pas_trans&quot;: 3.0,
&quot;alt_grua&quot;: 10.5, &quot;peso_max_grua&quot;: 1500.0, &quot;cant_ptas_norte&quot;: 0,
&quot;w_ptas_norte&quot;: 6.0,
&quot;cant_ptas_sur&quot;: 0, &quot;w_ptas_sur&quot;: 6.0, &quot;cant_ptas_este&quot;: 0,
&quot;w_ptas_este&quot;: 6.0,
&quot;cant_ptas_oeste&quot;: 0, &quot;w_ptas_oeste&quot;: 6.0, &quot;fuente_datos&quot;: &quot;Data
Original&quot;,
&quot;filtro_sublayout&quot;: &quot;TODOS&quot;, &quot;chk_a&quot;: True, &quot;chk_b&quot;: True, &quot;chk_c&quot;:
True,
&quot;consolidar_saldos&quot;: False, &quot;modo_vista_color&quot;: &quot;3 Zonas (ABC)&quot;,
&quot;racks_en_pared&quot;: False,
&quot;forma_pilar&quot;: &quot;Cuadrado / Rectangular&quot;, &quot;pilar_largo&quot;: 0.5,
&quot;pilar_ancho&quot;: 0.5
}
for k, v in parametros_layout.items():
if k not in st.session_state: st.session_state[k] = v
if &quot;layout_generado&quot; not in st.session_state:
st.session_state.layout_generado = False
if &quot;res_layout_actual&quot; not in st.session_state:
st.session_state.res_layout_actual = None
if &quot;kpi_layout_capacidad&quot; not in st.session_state:
st.session_state.kpi_layout_capacidad = 0
if &quot;kpi_layout_ubicados&quot; not in st.session_state:
st.session_state.kpi_layout_ubicados = 0
css_styles = &quot;&lt;style&gt;.box-3d{transition:all 0.25s cubic-
bezier(0.25,0.8,0.25,1);cursor:crosshair;}.box-
3d:hover{transform:scale(1.08) translateY(-3px);box-shadow:0 10px 20px
rgba(0,0,0,0.4)!important;z-
index:100!important;filter:brightness(1.1);}.cota-linea,.cota-linea-
v{position:absolute;display:flex;align-items:center;justify-
content:center;font-size:10px;color:#475569;font-weight:bold;background-
repeat:no-repeat;}.cota-linea{border-left:1px solid #64748b;border-
right:1px solid #64748b;background-image:linear-
gradient(#64748b,#64748b);background-size:100% 1px;background-
position:center;}.cota-linea-v{border-top:1px solid #64748b;border-
bottom:1px solid #64748b;background-image:linear-
gradient(#64748b,#64748b);background-size:1px 100%;background-

position:center;flex-direction:column;}.cota-
texto{background:white;padding:2px 4px;border-radius:3px;z-index:2;}.kpi-
box{background:#ffffff;border:1px solid #e2e8f0;padding:15px;border-
radius:8px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.1);}.kpi-
title{font-size:11px;color:#64748b;font-weight:600;text-
transform:uppercase;letter-spacing:0.5px;margin-bottom:5px;}.kpi-
value{font-size:24px;font-weight:700;color:#0f172a;}.kpi-box-
danger{background:#fef2f2!important;border:1px solid
#fecaca!important;}.kpi-value-danger{color:#dc2626!important;}&lt;/style&gt;&quot;
color_styles = &quot;&lt;style&gt;.hero-container-color{background:linear-
gradient(135deg,#0f172a 0%,#1e3a8a 50%,#0369a1 100%);border-
radius:16px;padding:50px 30px;text-align:center;box-shadow:0 12px 30px
rgba(15,23,42,0.25);margin-bottom:35px;}.hero-title-color{font-
size:3.6rem;font-weight:900;color:#ffffff;letter-spacing:-1px;margin-
bottom:14px;text-align:center;}.hero-subtitle-color{color:#e2e8f0;font-
size:1.25rem;font-weight:400;max-width:850px;margin:0 auto;line-
height:1.6;text-align:center;}.color-card{background:#ffffff;border-
radius:14px;padding:25px;height:230px;display:flex;flex-
direction:column;justify-content:space-between;box-shadow:0 6px 18px
rgba(0,0,0,0.05);transition:all 0.3s ease;margin-bottom:15px;border-top:5px
solid #2563eb;}.color-card-green{border-top-color:#059669;}.color-card-
purple{border-top-color:#7c3aed;}.color-card-amber{border-top-
color:#d97706;}.color-card-rose{border-top-color:#e11d48;}.color-
card:hover{box-shadow:0 12px 28px rgba(0,0,0,0.12);transform:translateY(-
4px);}.card-icon-header{display:flex;align-items:center;justify-
content:space-between;}.card-icon{font-size:2rem;}.card-tag-color{font-
size:0.72rem;font-weight:800;padding:4px 12px;border-radius:20px;letter-
spacing:0.5px;}.tag-blue{background:#dbeafe;color:#1e40af;}.tag-
green{background:#d1fae5;color:#065f46;}.tag-
purple{background:#ede9fe;color:#5b21b6;}.tag-
soon{background:#f1f5f9;color:#64748b;}.color-card-
title{color:#0f172a;font-size:1.25rem;font-weight:800;margin:10px 0 6px
0;}.color-card-desc{color:#475569;font-size:0.9rem;line-
height:1.45;margin:0;}&lt;/style&gt;&quot;
def clean_html(html_str):
return &quot;\n&quot;.join(line.strip() for line in html_str.split(&quot;\n&quot;))
# ============================================================
# 2. FUNCIONES CORE INTELIGENTES
# ============================================================
def norm_txt(valor):
t = &quot;&quot; if valor is None else str(valor)
return re.sub(r&quot;\s+&quot;, &quot; &quot;, re.sub(r&quot;[^a-z0-9]+&quot;, &quot; &quot;,
unicodedata.normalize(&quot;NFKD&quot;, t).encode(&quot;ascii&quot;,
&quot;ignore&quot;).decode(&quot;ascii&quot;).lower())).strip()
def es_numero(valor):
try: return pd.notna(valor) and math.isfinite(float(valor))
except: return False
def a_float(valor, default=np.nan):

try: return float(valor) if pd.notna(valor) else default
except: return default
def fmt(valor, dec=1): return f&quot;{float(valor):,.{dec}f}&quot; if
es_numero(valor) else &quot;N/D&quot;
def encontrar_columna(columnas, incluir, excluir=()):
for col in columnas:
n = norm_txt(col)
if all(p in n for p in incluir) and not any(p in n for p in
excluir): return col
return None
@st.cache_data
def procesar_datos(df_original):
cols = list(df_original.columns)
normalizados = {c: norm_txt(c) for c in cols}
mapa = {}
mapa[&quot;sku&quot;] = encontrar_columna(cols, [&quot;codigo&quot;, &quot;producto&quot;]) or
encontrar_columna(cols, [&quot;sku&quot;]) or encontrar_columna(cols, [&quot;codigo&quot;])
mapa[&quot;stock_promedio&quot;] = encontrar_columna(cols, [&quot;stock&quot;, &quot;promedio&quot;])
or encontrar_columna(cols, [&quot;promedio&quot;]) or encontrar_columna(cols,
[&quot;stock&quot;])
mapa[&quot;stock_maximo&quot;] = encontrar_columna(cols, [&quot;stock&quot;, &quot;maximo&quot;]) or
encontrar_columna(cols, [&quot;maximo&quot;]) or mapa[&quot;stock_promedio&quot;]
mapa[&quot;stock&quot;] = mapa[&quot;stock_promedio&quot;]
mapa[&quot;peso&quot;] = encontrar_columna(cols, [&quot;peso&quot;], [&quot;total&quot;, &quot;pallet&quot;])
mapa[&quot;formato&quot;] = encontrar_columna(cols, [&quot;formato&quot;, &quot;principal&quot;])
largos = [c for c in cols if &quot;largo&quot; in normalizados[c] and &quot;pallet&quot;
not in normalizados[c]]
anchos = [c for c in cols if &quot;ancho&quot; in normalizados[c] and &quot;pallet&quot;
not in normalizados[c]]
altos = [c for c in cols if &quot;alto&quot; in normalizados[c] and &quot;pallet&quot; not
in normalizados[c] and &quot;altura&quot; not in normalizados[c]]
mapa[&quot;largo&quot;] = largos[0] if largos else None
mapa[&quot;ancho&quot;] = anchos[0] if anchos else None
if mapa[&quot;ancho&quot;] is None and len(largos) &gt;= 2: mapa[&quot;ancho&quot;] =
largos[1]
mapa[&quot;alto&quot;] = altos[0] if altos else None
mapa[&quot;largo_pallet&quot;] = me_lp = encontrar_columna(cols, [&quot;largo&quot;,
&quot;pallet&quot;])
mapa[&quot;ancho_pallet&quot;] = me_ap = encontrar_columna(cols, [&quot;ancho&quot;,
&quot;pallet&quot;])
mapa[&quot;altura_pallet&quot;] = encontrar_columna(cols, [&quot;altura&quot;, &quot;pallet&quot;],
[&quot;total&quot;, &quot;paletizada&quot;]) or me_lp or me_ap
mapa[&quot;unidades_pallet&quot;] = encontrar_columna(cols, [&quot;unidades&quot;,
&quot;pallet&quot;])
mapa[&quot;altura_total&quot;] = encontrar_columna(cols, [&quot;altura&quot;, &quot;total&quot;,
&quot;pallet&quot;]) or me_lp or encontrar_columna(cols, [&quot;altura&quot;, &quot;paletizada&quot;])

mapa[&quot;abc&quot;] = encontrar_columna(cols, [&quot;abc&quot;], [&quot;xyz&quot;])
mapa[&quot;xyz&quot;] = encontrar_columna(cols, [&quot;xyz&quot;], [&quot;abc&quot;])
mapa[&quot;abc_xyz&quot;] = encontrar_columna(cols, [&quot;abc&quot;, &quot;xyz&quot;])
mapa[&quot;familia&quot;] = encontrar_columna(cols, [&quot;familia&quot;])
mapa[&quot;bodega&quot;] = encontrar_columna(cols, [&quot;bodega&quot;])
mapa[&quot;ranking&quot;] = encontrar_columna(cols, [&quot;ranking&quot;])
df_trabajo = df_original.copy()
if &quot;Pallets_Totales_Optimo&quot; in df_trabajo.columns:
mapa[&quot;is_opt_report&quot;] = True
mapa[&quot;stock&quot;] = &quot;Stock&quot; if &quot;Stock&quot; in df_trabajo.columns else
mapa.get(&quot;stock&quot;)
mapa[&quot;stock_promedio&quot;] = &quot;Stock_Promedio&quot; if &quot;Stock_Promedio&quot; in
df_trabajo.columns else mapa.get(&quot;stock&quot;)
mapa[&quot;stock_maximo&quot;] = &quot;Stock_Maximo&quot; if &quot;Stock_Maximo&quot; in
df_trabajo.columns else mapa.get(&quot;stock&quot;)
mapa[&quot;formato&quot;] = &quot;Formato&quot; if &quot;Formato&quot; in df_trabajo.columns else
mapa.get(&quot;formato&quot;)
mapa[&quot;abc&quot;] = &quot;Clasificacion_ABC&quot; if &quot;Clasificacion_ABC&quot; in
df_trabajo.columns else mapa.get(&quot;abc&quot;)
mapa[&quot;xyz&quot;] = &quot;Clasificacion_XYZ&quot; if &quot;Clasificacion_XYZ&quot; in
df_trabajo.columns else mapa.get(&quot;xyz&quot;)
mapa[&quot;abc_xyz&quot;] = &quot;Matriz_ABC_XYZ&quot; if &quot;Matriz_ABC_XYZ&quot; in
df_trabajo.columns else mapa.get(&quot;abc_xyz&quot;)
mapa[&quot;familia&quot;] = &quot;Familia&quot; if &quot;Familia&quot; in df_trabajo.columns else
mapa.get(&quot;familia&quot;)
mapa[&quot;bodega&quot;] = &quot;Bodega&quot; if &quot;Bodega&quot; in df_trabajo.columns else
mapa.get(&quot;bodega&quot;)
mapa[&quot;ranking&quot;] = &quot;Ranking&quot; if &quot;Ranking&quot; in df_trabajo.columns else
mapa.get(&quot;ranking&quot;)
df_trabajo[mapa[&quot;sku&quot;]] =
df_trabajo[mapa[&quot;sku&quot;]].astype(str).str.strip()
if mapa.get(&quot;abc&quot;): df_trabajo[mapa[&quot;abc&quot;]] =
df_trabajo[mapa[&quot;abc&quot;]].fillna(&quot;C&quot;).astype(str).str.strip().str.upper()
if mapa.get(&quot;xyz&quot;): df_trabajo[mapa[&quot;xyz&quot;]] =
df_trabajo[mapa[&quot;xyz&quot;]].fillna(&quot;Z&quot;).astype(str).str.strip().str.upper()
return df_trabajo, mapa
else:
mapa[&quot;is_opt_report&quot;] = False
df_trabajo[mapa[&quot;sku&quot;]] =
df_trabajo[mapa[&quot;sku&quot;]].astype(str).str.strip()
if mapa.get(&quot;abc&quot;): df_trabajo[mapa[&quot;abc&quot;]] =
df_trabajo[mapa[&quot;abc&quot;]].fillna(&quot;C&quot;).astype(str).str.strip().str.upper()
if mapa.get(&quot;xyz&quot;): df_trabajo[mapa[&quot;xyz&quot;]] =
df_trabajo[mapa[&quot;xyz&quot;]].fillna(&quot;Z&quot;).astype(str).str.strip().str.upper()
return pd.concat([df_trabajo, df_trabajo.apply(lambda fila:
precalcular_fila(fila, mapa), axis=1)], axis=1), mapa
def mejor_distribucion_filas(largo, ancho, largo_pallet, ancho_pallet):
if not all(es_numero(v) and float(v) &gt; 0 for v in [largo, ancho,

largo_pallet, ancho_pallet]): return {&quot;cantidad&quot;: 0, &quot;cajas&quot;: [], &quot;filas&quot;:
[]}
largo, ancho, largo_pallet, ancho_pallet = map(float, [largo, ancho,
largo_pallet, ancho_pallet])
opciones, mejor = [{&quot;tipo&quot;: &quot;Normal&quot;, &quot;largo&quot;: largo, &quot;ancho&quot;: ancho},
{&quot;tipo&quot;: &quot;Cruzada&quot;, &quot;largo&quot;: ancho, &quot;ancho&quot;: largo}], {&quot;cantidad&quot;: 0,
&quot;filas&quot;: []}
max_n, max_c = int(math.floor(ancho_pallet / opciones[0][&quot;ancho&quot;])),
int(math.floor(ancho_pallet / opciones[1][&quot;ancho&quot;]))
p_f_n, p_f_c = int(math.floor(largo_pallet / opciones[0][&quot;largo&quot;])),
int(math.floor(largo_pallet / opciones[1][&quot;largo&quot;]))
for n_n in range(max_n + 1):
for n_c in range(max_c + 1):
if (n_n * opciones[0][&quot;ancho&quot;] + n_c * opciones[1][&quot;ancho&quot;]) &lt;=
ancho_pallet + 1e-9:
tot = (n_n * p_f_n + n_c * p_f_c)
if tot &gt; mejor[&quot;cantidad&quot;]: mejor = {&quot;cantidad&quot;: tot,
&quot;filas&quot;: ([opciones[0]] * n_n) + ([opciones[1]] * n_c)}
cajas, y = [], 0.0
for fila in mejor[&quot;filas&quot;]:
for i in range(int(math.floor(largo_pallet / fila[&quot;largo&quot;]))):
cajas.append({&quot;x&quot;: i * fila[&quot;largo&quot;], &quot;y&quot;: y, &quot;largo&quot;: fila[&quot;largo&quot;],
&quot;ancho&quot;: fila[&quot;ancho&quot;]})
y += fila[&quot;ancho&quot;]
return {&quot;cantidad&quot;: mejor[&quot;cantidad&quot;], &quot;cajas&quot;: cajas}
def valor_col(fila, key, mapa):
col = mapa.get(key)
return fila[col] if col is not None and col in fila.index else np.nan
def precalcular_fila(fila, mapa):
cap_base, largo, ancho, alto, peso_u = a_float(valor_col(fila,
&quot;unidades_pallet&quot;, mapa)), a_float(valor_col(fila, &quot;largo&quot;, mapa)),
a_float(valor_col(fila, &quot;ancho&quot;, mapa)), a_float(valor_col(fila, &quot;alto&quot;,
mapa)), a_float(valor_col(fila, &quot;peso&quot;, mapa))
l_p, a_p, alt_p, alt_t = a_float(valor_col(fila, &quot;largo_pallet&quot;, mapa),
120), a_float(valor_col(fila, &quot;ancho_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;altura_pallet&quot;, mapa), 15),
a_float(valor_col(fila, &quot;altura_total&quot;, mapa))
layout = mejor_distribucion_filas(largo, ancho, l_p, a_p)
u_niv, n_alt, n_peso = layout[&quot;cantidad&quot;], float(&#39;inf&#39;), float(&#39;inf&#39;)
if all(es_numero(v) and v &gt; 0 for v in [alt_t, alt_p, alto]) and alt_t
&gt; alt_p: n_alt = math.floor((alt_t - alt_p) / alto)
if es_numero(peso_u) and peso_u &gt; 0 and u_niv &gt; 0: n_peso =
math.floor((MAX_PESO_PALLET - PESO_MADERA_PALLET) / (u_niv * peso_u))
niv_opt = min(n_alt, n_peso)
if math.isinf(niv_opt) or niv_opt &lt;= 0: niv_opt = max(1,
int(round(cap_base / u_niv))) if (es_numero(cap_base) and u_niv &gt; 0) else 1
return pd.Series({&quot;Capacidad_Excel&quot;: cap_base, &quot;Capacidad_Optima&quot;:
int(u_niv * niv_opt), &quot;Unidades_Por_Nivel&quot;: u_niv, &quot;Niveles_Optimos&quot;:
niv_opt})

def calcular_metricas_dinamicas(fila, mapa, modo=&quot;EXCEL&quot;):
escenario_stock = st.session_state.get(&quot;tipo_stock&quot;, &quot;Stock Promedio&quot;)
key_stock = &quot;stock_maximo&quot; if escenario_stock == &quot;Stock Máximo&quot; else
&quot;stock_promedio&quot;
if mapa.get(&quot;is_opt_report&quot;):
col_stock = mapa.get(key_stock, mapa.get(&quot;stock&quot;, &quot;Stock&quot;))
if col_stock not in fila.index: col_stock = mapa.get(&quot;stock&quot;,
&quot;Stock&quot;)
stock = a_float(fila.get(col_stock), 0)
if modo == &quot;OPTIMO&quot;:
cap_usada, pallets_comp, efi_vol, estado =
a_float(fila.get(&quot;Capacidad_Optima&quot;), 0),
a_float(fila.get(&quot;Pallets_Completos_Optimo&quot;), 0),
a_float(fila.get(&quot;Eficiencia_Vol_Optimo_%&quot;), np.nan),
str(fila.get(&quot;Estado_Optimo&quot;, &quot;OK&quot;))
else:
cap_usada, pallets_comp, efi_vol, estado =
a_float(fila.get(&quot;Capacidad_Excel&quot;), 0),
a_float(fila.get(&quot;Pallets_Completos_Excel&quot;), 0),
a_float(fila.get(&quot;Eficiencia_Vol_Excel_%&quot;), np.nan),
str(fila.get(&quot;Estado_Excel&quot;, &quot;OK&quot;))
pallets = int(math.ceil(stock / cap_usada)) if stock &gt; 0 and
cap_usada &gt; 0 else 0
ult_unids = (stock - (pallets - 1) * cap_usada) if pallets &gt; 0 else
0
if ult_unids == 0 and stock &gt; 0: ult_unids = cap_usada
pallets_comp = pallets - 1 if pallets &gt; 0 and ult_unids &lt; cap_usada
else pallets
u_sob = 0 if ult_unids == cap_usada else ult_unids
ult_pct = (ult_unids / cap_usada * 100) if cap_usada &gt; 0 else 0
peso_u = a_float(valor_col(fila, &quot;peso&quot;, mapa))
peso_pal = (cap_usada * peso_u) + PESO_MADERA_PALLET if
es_numero(peso_u) else np.nan
return {&quot;Capacidad_Usada&quot;: cap_usada, &quot;Pallets&quot;: int(pallets),
&quot;Unidades_Ultimo&quot;: ult_unids, &quot;Ocupacion_Ultimo&quot;: ult_pct, &quot;Peso_Pallet&quot;:
peso_pal, &quot;Estado&quot;: estado, &quot;Cap_Excel&quot;:
a_float(fila.get(&quot;Capacidad_Excel&quot;), 0), &quot;Cap_Optima&quot;:
a_float(fila.get(&quot;Capacidad_Optima&quot;), 0), &quot;Eficiencia_Volumen&quot;: efi_vol,
&quot;Pallets_Completos&quot;: int(pallets_comp), &quot;Unidades_Sobrante&quot;: u_sob,
&quot;Stock&quot;: stock}
stock = a_float(valor_col(fila, key_stock, mapa), 0)
cap_ex, cap_op = a_float(fila.get(&quot;Capacidad_Excel&quot;), 0),
int(fila.get(&quot;Capacidad_Optima&quot;, 0))
peso_u, largo, ancho, alto = a_float(valor_col(fila, &quot;peso&quot;, mapa)),
a_float(valor_col(fila, &quot;largo&quot;, mapa)), a_float(valor_col(fila, &quot;ancho&quot;,
mapa)), a_float(valor_col(fila, &quot;alto&quot;, mapa))
l_p, a_p, alt_p, alt_t = a_float(valor_col(fila, &quot;largo_pallet&quot;, mapa),

120), a_float(valor_col(fila, &quot;ancho_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;altura_pallet&quot;, mapa), 15),
a_float(valor_col(fila, &quot;altura_total&quot;, mapa))
cap_usada = cap_op if (modo == &quot;OPTIMO&quot; and cap_op &gt; 0) else
int(round(cap_ex)) if (modo == &quot;EXCEL&quot; and es_numero(cap_ex) and cap_ex &gt;
0) else cap_op
pallets = int(math.ceil(stock / cap_usada)) if stock &gt; 0 and cap_usada
&gt; 0 else 0
ult_unids = (stock - (pallets - 1) * cap_usada) if pallets &gt; 0 else 0
if ult_unids == 0 and stock &gt; 0: ult_unids = cap_usada
pallets_comp = pallets - 1 if pallets &gt; 0 and ult_unids &lt; cap_usada
else pallets
u_sob = 0 if ult_unids == cap_usada else ult_unids
peso_pal = (cap_usada * peso_u) + PESO_MADERA_PALLET if
es_numero(peso_u) else np.nan
vol_prod = (largo * ancho * alto * cap_usada) if all(es_numero(v) for v
in [largo, ancho, alto]) else np.nan
vol_pallet = (l_p * a_p * (alt_t - alt_p)) if all(es_numero(v) for v in
[l_p, a_p, alt_t, alt_p]) else np.nan
efi_vol = (vol_prod / vol_pallet * 100) if es_numero(vol_prod) and
es_numero(vol_pallet) and vol_pallet &gt; 0 else np.nan
estado = &quot;OK&quot;
if stock &lt;= 0: estado = &quot;SIN STOCK&quot;
elif cap_usada &lt;= 0: estado = &quot;REVISAR DATOS&quot;
elif es_numero(peso_pal) and peso_pal &gt; MAX_PESO_PALLET: estado = &quot;⚠️
PELIGRO: SOBREPESO (&gt;1200kg)&quot;
elif modo == &quot;EXCEL&quot; and abs((cap_op - cap_ex) if es_numero(cap_ex)
else 0) &gt; 0: estado = f&quot;⚠️ EXCEL: {int(cap_ex)}u | ÓPTIMO: {cap_op}u&quot;
return {&quot;Capacidad_Usada&quot;: cap_usada, &quot;Pallets&quot;: pallets,
&quot;Unidades_Ultimo&quot;: ult_unids, &quot;Ocupacion_Ultimo&quot;: (ult_unids / cap_usada *
100) if cap_usada &gt; 0 else 0, &quot;Peso_Pallet&quot;: peso_pal, &quot;Estado&quot;: estado,
&quot;Cap_Excel&quot;: cap_ex, &quot;Cap_Optima&quot;: cap_op, &quot;Eficiencia_Volumen&quot;: efi_vol,
&quot;Pallets_Completos&quot;: pallets_comp, &quot;Unidades_Sobrante&quot;: u_sob, &quot;Stock&quot;:
stock}
# REPORTE DE 3 HOJAS EN CUBICADORA
def generar_excel_descarga(df_original, df_resultados, mapa):
output = io.BytesIO()
comparativo_rows = []
for _, row in df_resultados.iterrows():
m_ex, m_op = calcular_metricas_dinamicas(row, mapa, &quot;EXCEL&quot;),
calcular_metricas_dinamicas(row, mapa, &quot;OPTIMO&quot;)
dif = m_op[&quot;Cap_Optima&quot;] - m_ex[&quot;Cap_Excel&quot;] if
es_numero(m_ex[&quot;Cap_Excel&quot;]) else m_op[&quot;Cap_Optima&quot;]
comparativo_rows.append({
&quot;SKU&quot;: row[mapa[&quot;sku&quot;]] if mapa.get(&quot;sku&quot;) else &quot;N/D&quot;,

&quot;Familia&quot;: row.get(mapa.get(&quot;familia&quot;), &quot;N/D&quot;), &quot;Ranking&quot;:
row.get(mapa.get(&quot;ranking&quot;), &quot;N/D&quot;),
&quot;Clasificacion_ABC&quot;: row.get(mapa.get(&quot;abc&quot;), &quot;N/D&quot;),
&quot;Clasificacion_XYZ&quot;: row.get(mapa.get(&quot;xyz&quot;), &quot;N/D&quot;), &quot;Matriz_ABC_XYZ&quot;:
row.get(mapa.get(&quot;abc_xyz&quot;), &quot;N/D&quot;),
&quot;Bodega&quot;: row.get(mapa.get(&quot;bodega&quot;), &quot;N/D&quot;), &quot;Formato&quot;:
row.get(mapa.get(&quot;formato&quot;), &quot;N/D&quot;), &quot;Stock&quot;: m_ex[&quot;Stock&quot;],
&quot;Capacidad_Excel&quot;: m_ex[&quot;Cap_Excel&quot;],
&quot;Capacidad_Optima&quot;: m_op[&quot;Cap_Optima&quot;], &quot;Diferencia_Unidades&quot;:
dif, &quot;Pallets_Totales_Excel&quot;: m_ex[&quot;Pallets&quot;], &quot;Pallets_Completos_Excel&quot;:
m_ex[&quot;Pallets_Completos&quot;],
&quot;Unidades_Sobrante_Excel&quot;: m_ex[&quot;Unidades_Sobrante&quot;],
&quot;Pallets_Totales_Optimo&quot;: m_op[&quot;Pallets&quot;], &quot;Pallets_Completos_Optimo&quot;:
m_op[&quot;Pallets_Completos&quot;],
&quot;Unidades_Sobrante_Optimo&quot;: m_op[&quot;Unidades_Sobrante&quot;],
&quot;Peso_Pallet_Excel_kg&quot;: m_ex[&quot;Peso_Pallet&quot;], &quot;Peso_Pallet_Optimo_kg&quot;:
m_op[&quot;Peso_Pallet&quot;],
&quot;Eficiencia_Vol_Excel_%&quot;: m_ex[&quot;Eficiencia_Volumen&quot;],
&quot;Eficiencia_Vol_Optimo_%&quot;: m_op[&quot;Eficiencia_Volumen&quot;], &quot;Estado_Excel&quot;:
m_ex[&quot;Estado&quot;], &quot;Estado_Optimo&quot;: m_op[&quot;Estado&quot;]
})
with pd.ExcelWriter(output, engine=&#39;openpyxl&#39;) as writer:
pd.DataFrame(comparativo_rows).to_excel(writer,
sheet_name=&quot;1_Analisis_Comparativo&quot;, index=False)
df_original.loc[df_resultados.index].copy().to_excel(writer,
sheet_name=&quot;2_Data_Original_Filtr&quot;, index=False)
df_resultados.to_excel(writer,
sheet_name=&quot;3_Data_Optimizada_Filtr&quot;, index=False)
output.seek(0)
return output
# REPORTE DE 3 HOJAS EN LAYOUT WMS
def generar_wms_excel(df_base, almacen, mapa):
pos = {}
slots_rows = []
for s in almacen:
if s[&#39;ocupado&#39;]:
pos.setdefault(str(s[&#39;sku&#39;]).upper(),
[]).append(s[&#39;id_posicion&#39;])
slots_rows.append({
&quot;ID_Posicion&quot;: s[&#39;id_posicion&#39;], &quot;Pasillo&quot;: s[&#39;letra_pasillo&#39;],
&quot;Modulo&quot;: s[&#39;modulo&#39;],
&quot;Nivel&quot;: s[&#39;nivel&#39;], &quot;Slot&quot;: s[&#39;slot&#39;], &quot;SKU&quot;: s.get(&#39;sku&#39;,
&#39;VACIO&#39;),
&quot;Unidades_Actuales&quot;: s.get(&#39;unidades&#39;, 0), &quot;Capacidad_Maxima&quot;:
s.get(&#39;cap_maxima&#39;, 0),
&quot;Estado&quot;: &quot;Ocupado&quot; if s[&#39;ocupado&#39;] else &quot;Vacío&quot;, &quot;Zona_ABC&quot;:
s.get(&#39;abc&#39;, &#39;N/D&#39;),
&quot;Es_Mixto&quot;: &quot;SI&quot; if s.get(&#39;es_mixto&#39;) else &quot;NO&quot;
})
df_exp = df_base.copy()

col_sku = mapa.get(&quot;sku&quot;, df_exp.columns[0])
df_exp[&#39;Posiciones_Layout_WMS&#39;] = df_exp[col_sku].apply(lambda x: &quot;,
&quot;.join(pos.get(str(x).strip().upper(), [&quot;Sin Ubicar&quot;])))
resumen_data = [{
&quot;Total_Slots_Racks&quot;: len(almacen),
&quot;Total_Slots_Ocupados&quot;: sum(1 for s in almacen if s[&#39;ocupado&#39;]),
&quot;Total_Slots_Vacios&quot;: sum(1 for s in almacen if not s[&#39;ocupado&#39;]),
&quot;Porcentaje_Ocupacion&quot;: f&quot;{(sum(1 for s in almacen if
s[&#39;ocupado&#39;])/len(almacen)*100):.1f}%&quot; if almacen else &quot;0%&quot;
}]
output = io.BytesIO()
with pd.ExcelWriter(output, engine=&#39;openpyxl&#39;) as w:
df_exp.to_excel(w, sheet_name=&quot;1_Asignacion_WMS&quot;, index=False)
pd.DataFrame(slots_rows).to_excel(w,
sheet_name=&quot;2_Mapa_Malla_Slots&quot;, index=False)
pd.DataFrame(resumen_data).to_excel(w,
sheet_name=&quot;3_Resumen_Capacidad&quot;, index=False)
output.seek(0)
return output
def es_formato_circular(formato): return any(k in norm_txt(formato) for k
in [&quot;tambor&quot;, &quot;balde&quot;, &quot;bidon&quot;, &quot;cunete&quot;, &quot;barril&quot;, &quot;tarro&quot;, &quot;lata&quot;,
&quot;cilindro&quot;]) if not pd.isna(formato) else False
def get_material_css(f):
n = norm_txt(f)
if any(k in n for k in [&quot;tambor&quot;, &quot;balde&quot;, &quot;bidon&quot;, &quot;lata&quot;,
&quot;cilindro&quot;]): return {&quot;bg_top&quot;: &quot;radial-gradient(circle at 35% 35%,
#93c5fd, #1d4ed8)&quot;, &quot;bg_side&quot;: &quot;linear-gradient(to right, #1e3a8a, #60a5fa
30%, #3b82f6 60%, #1e3a8a)&quot;, &quot;border&quot;: &quot;#1e3a8a&quot;, &quot;radius&quot;: &quot;50%&quot;,
&quot;shadow&quot;: &quot;inset -3px -3px 6px rgba(0,0,0,0.4), 2px 3px 5px
rgba(0,0,0,0.25)&quot;}
if &quot;bin&quot; in n or &quot;cubeta&quot; in n: return {&quot;bg_top&quot;: &quot;linear-
gradient(135deg, #34d399, #059669)&quot;, &quot;bg_side&quot;: &quot;linear-gradient(to bottom,
#34d399, #059669)&quot;, &quot;border&quot;: &quot;#064e3b&quot;, &quot;radius&quot;: &quot;6px&quot;, &quot;shadow&quot;: &quot;inset
-2px -2px 5px rgba(0,0,0,0.3), inset 2px 2px 3px rgba(255,255,255,0.4), 2px
3px 4px rgba(0,0,0,0.2)&quot;}
return {&quot;bg_top&quot;: &quot;linear-gradient(135deg, #e5c07b, #c6893f)&quot;,
&quot;bg_side&quot;: &quot;linear-gradient(to bottom, #d4a373, #a67232)&quot;, &quot;border&quot;:
&quot;#8b5a2b&quot;, &quot;radius&quot;: &quot;2px&quot;, &quot;shadow&quot;: &quot;inset -2px -2px 4px rgba(0,0,0,0.2),
inset 1px 1px 2px rgba(255,255,255,0.3), 2px 3px 5px rgba(0,0,0,0.2)&quot;}
def html_vista_superior(fila, mapa, cantidad_unidades=None):
if cantidad_unidades is not None and int(cantidad_unidades) &lt;= 0:
return &quot;&lt;div style=&#39;text-align:center; padding:30px; font-weight:bold;
color:#cbd5e1;&#39;&gt;Pallet Vacío&lt;/div&gt;&quot;
lp, ap = a_float(valor_col(fila, &quot;largo_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;ancho_pallet&quot;, mapa), 120)
layout = mejor_distribucion_filas(a_float(valor_col(fila, &quot;largo&quot;,
mapa)), a_float(valor_col(fila, &quot;ancho&quot;, mapa)), lp, ap)

if layout[&quot;cantidad&quot;] &lt;= 0: return &quot;&lt;div style=&#39;text-align:center;
padding:30px;&#39;&gt;Faltan dimensiones.&lt;/div&gt;&quot;
escala, mat = min(220 / lp, 220 / ap, 2.0),
get_material_css(valor_col(fila, &quot;formato&quot;, mapa))
cajas = layout[&quot;cajas&quot;][:int(cantidad_unidades) % layout[&quot;cantidad&quot;] or
layout[&quot;cantidad&quot;]] if cantidad_unidades is not None and cantidad_unidades
&gt; 0 else layout[&quot;cajas&quot;]
objs = [f&quot;&lt;div class=&#39;box-3d&#39; style=&#39;position:absolute;
left:{c[&#39;x&#39;]*escala:.2f}px; top:{c[&#39;y&#39;]*escala:.2f}px;
width:{c[&#39;largo&#39;]*escala:.2f}px; height:{c[&#39;ancho&#39;]*escala:.2f}px; box-
sizing:border-box; background:{mat[&#39;bg_top&#39;]}; border:1px solid
{mat[&#39;border&#39;]}; border-radius:{mat[&#39;radius&#39;]}; box-shadow:{mat[&#39;shadow&#39;]};
color:white; font-size:10px; font-weight:700; display:flex; align-
items:center; justify-content:center; z-index: 10;&#39;&gt;{i+1}&lt;/div&gt;&quot; for i, c
in enumerate(cajas)]
return f&quot;&lt;div style=&#39;position:relative; width:{lp*escala + 30:.2f}px;
height:{ap*escala + 30:.2f}px; margin: 10px auto;&#39;&gt;&lt;div class=&#39;cota-linea&#39;
style=&#39;top: 0; left: 0; width: {lp*escala}px; height: 10px;&#39;&gt;&lt;span
class=&#39;cota-texto&#39;&gt;{fmt(lp,0)} cm&lt;/span&gt;&lt;/div&gt;&lt;div class=&#39;cota-linea-v&#39;
style=&#39;top: 15px; right: 0; width: 10px; height: {ap*escala}px;&#39;&gt;&lt;span
class=&#39;cota-texto&#39; style=&#39;transform: rotate(90deg); white-
space:nowrap;&#39;&gt;{fmt(ap,0)} cm&lt;/span&gt;&lt;/div&gt;&lt;div style=&#39;position:absolute;
top:15px; left:0; width:{lp*escala:.2f}px; height:{ap*escala:.2f}px;
background-color:#d39e66; background-image:repeating-linear-
gradient(90deg,transparent,transparent 15%,rgba(100,50,0,0.15)
15%,rgba(100,50,0,0.15) 17%); box-shadow:4px 6px 12px rgba(0,0,0,0.25);
border:2px solid #8b5a2b; border-radius:4px;&#39;&gt;{&#39;&#39;.join(objs)}&lt;/div&gt;&lt;/div&gt;&quot;
def html_vista_lateral(fila, mapa, cap_usada, total_unidades=None):
if total_unidades is not None and int(total_unidades) &lt;= 0: return
&quot;&lt;div style=&#39;text-align:center; padding:30px; font-weight:bold;
color:#cbd5e1;&#39;&gt;Pallet Vacío&lt;/div&gt;&quot;
lp, hp, ap = a_float(valor_col(fila, &quot;largo_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;altura_pallet&quot;, mapa), 15),
a_float(valor_col(fila, &quot;ancho_pallet&quot;, mapa), 120)
alto, alt_t, largo, ancho = a_float(valor_col(fila, &quot;alto&quot;, mapa)),
a_float(valor_col(fila, &quot;altura_total&quot;, mapa)), a_float(valor_col(fila,
&quot;largo&quot;, mapa)), a_float(valor_col(fila, &quot;ancho&quot;, mapa))
if not all([es_numero(x) and x &gt; 0 for x in [lp, hp, alto]]): return
&quot;&lt;div style=&#39;text-align:center; padding:30px;&#39;&gt;Faltan datos.&lt;/div&gt;&quot;
lay = mejor_distribucion_filas(largo, ancho, lp, ap)
if lay[&quot;cantidad&quot;] &lt;= 0: return &quot;&quot;
t_units = int(cap_usada) if total_unidades is None else
int(total_unidades)
cols = len([c for c in lay[&quot;cajas&quot;] if abs(c[&quot;y&quot;]) &lt; 1e-5]) or 1
niv_c, u_sob = t_units // lay[&quot;cantidad&quot;], t_units % lay[&quot;cantidad&quot;]
alto_v = alt_t if es_numero(alt_t) and alt_t &gt; hp else (hp + max(niv_c
+ (1 if u_sob &gt; 0 else 0), 1) * alto)
ex, ey = min(220 / lp, 2.0), min(180 / alto_v, 2.0)
cw, ch, mat = (lp * ex) / cols, alto * ey,
get_material_css(valor_col(fila, &quot;formato&quot;, mapa))
bloques = [f&quot;&lt;div class=&#39;box-3d&#39; style=&#39;position:absolute;

left:{i*cw:.2f}px; bottom:{hp*ey + n*ch:.2f}px; width:{cw-1:.2f}px;
height:{ch-1:.2f}px; box-sizing:border-box; background:{mat[&#39;bg_side&#39;]};
border:1px solid {mat[&#39;border&#39;]}; border-radius:{mat[&#39;radius&#39;]}; box-
shadow:inset 1px 1px 2px rgba(255,255,255,0.2), 2px 2px 4px
rgba(0,0,0,0.3);&#39;&gt;&lt;/div&gt;&quot; for n in range(niv_c) for i in range(cols)]
c_top = len([c for c in lay[&quot;cajas&quot;][:u_sob] if abs(c[&quot;y&quot;]) &lt; 1e-5]) if
u_sob &gt; 0 else 0
bloques += [f&quot;&lt;div class=&#39;box-3d&#39; style=&#39;position:absolute;
left:{i*cw:.2f}px; bottom:{hp*ey + niv_c*ch:.2f}px; width:{cw-1:.2f}px;
height:{ch-1:.2f}px; box-sizing:border-box; background:{mat[&#39;bg_side&#39;]};
border:1px solid {mat[&#39;border&#39;]}; border-radius:{mat[&#39;radius&#39;]}; box-
shadow:inset 1px 1px 2px rgba(255,255,255,0.2), 2px 2px 4px
rgba(0,0,0,0.3);&#39;&gt;&lt;/div&gt;&quot; for i in range(c_top if c_top &gt; 0 else (1 if
u_sob &gt; 0 else 0))]
return f&quot;&lt;div style=&#39;position:relative; width:{lp*ex + 40:.2f}px;
height:{alto_v*ey + 30:.2f}px; margin: 10px auto;&#39;&gt;&lt;div class=&#39;cota-linea-
v&#39; style=&#39;bottom: 0; left: 0; width: 10px; height: {alto_v*ey}px;&#39;&gt;&lt;span
class=&#39;cota-texto&#39; style=&#39;transform: rotate(-90deg); white-
space:nowrap;&#39;&gt;{fmt(alto_v,0)} cm&lt;/span&gt;&lt;/div&gt;&lt;div
style=&#39;position:absolute; left:25px; bottom:0; width:{lp*ex:.2f}px;
height:{alto_v*ey:.2f}px;&#39;&gt;&lt;div style=&#39;position:absolute; left:0; bottom:0;
width:{lp*ex:.2f}px; height:{hp*ey:.2f}px; background:#b88252; border:1px
solid #754b28; border-radius:2px; box-shadow: 2px 2px 4px
rgba(0,0,0,0.3);&#39;&gt;&lt;div style=&#39;position:absolute; left:18%; bottom:15%;
width:22%; height:70%; background:#2c1b12; border-radius:2px;&#39;&gt;&lt;/div&gt;&lt;div
style=&#39;position:absolute; right:18%; bottom:15%; width:22%; height:70%;
background:#2c1b12; border-radius:2px;&#39;&gt;&lt;/div&gt;&lt;/div&gt;{&#39;&#39;.join(bloques)}&lt;div
style=&#39;position:absolute; left:0; bottom:{alto_v*ey:.2f}px; width:110%;
border-top:2px dashed #ef4444; z-index:20;&#39;&gt;&lt;/div&gt;&lt;div
style=&#39;position:absolute; right:-25px; bottom:{alto_v*ey-10:.2f}px; font-
size:10px; color:#ef4444; font-weight:700;&#39;&gt;MÁX&lt;/div&gt;&lt;/div&gt;&lt;/div&gt;&quot;
class MallaAgrupada:
def __init__(self, color, nombre, opacidad=1.0):
self.color, self.nombre, self.opacidad = color, nombre, opacidad
self.x, self.y, self.z, self.i, self.j, self.k, self.text = [], [],
[], [], [], [], []
self.contador = 0
def agregar_cubo(self, x0, y0, z0, dx, dy, dz, hover_txt=None):
off = len(self.x)
self.x.extend([x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0]);
self.y.extend([y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy]);
self.z.extend([z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz])
self.i.extend([idx + off for idx in [7,0,0,0,4,4,6,6,4,0,3,2]]);
self.j.extend([idx + off for idx in [3,4,1,2,5,6,5,2,0,1,6,3]]);
self.k.extend([idx + off for idx in [0,7,2,3,6,7,1,1,5,5,7,6]])
if hover_txt: self.text.extend([hover_txt] * 8)
self.contador += 1
def agregar_cilindro(self, xc, yc, zb, r, h, hover_txt=None):
l = 8; off = len(self.x)
for i in range(l):
ang = 2 * math.pi * i / l

self.x.extend([xc + r * math.cos(ang)]*2); self.y.extend([yc +
r * math.sin(ang)]*2); self.z.extend([zb, zb + h])
if hover_txt: self.text.extend([hover_txt]*2)
self.x.extend([xc]*2); self.y.extend([yc]*2); self.z.extend([zb, zb
+ h])
if hover_txt: self.text.extend([hover_txt]*2)
cb, ct = off + l*2, off + l*2 + 1
for i in range(l):
nxt = (i+1)%l
b1, t1, b2, t2 = off + i*2, off + i*2 + 1, off + nxt*2, off +
nxt*2 + 1
self.i.extend([b1, t1, cb, ct]); self.j.extend([b2, b2, b2,
t1]); self.k.extend([t1, t2, b1, t2])
self.contador += 1
def obtener_trazo(self):
if not self.x: return None
return go.Mesh3d(x=self.x, y=self.y, z=self.z, i=self.i, j=self.j,
k=self.k, color=self.color, opacity=self.opacidad, name=self.nombre,
text=self.text if self.text else None, hoverinfo=&quot;text&quot; if self.text else
&quot;name&quot;, showscale=False, flatshading=True)
def renderizar_3d_plotly(fila, mapa, cap_usada, total_unidades=None):
lp, ap, hp = a_float(valor_col(fila, &quot;largo_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;ancho_pallet&quot;, mapa), 120),
a_float(valor_col(fila, &quot;altura_pallet&quot;, mapa), 15)
largo, ancho, alto = a_float(valor_col(fila, &quot;largo&quot;, mapa)),
a_float(valor_col(fila, &quot;ancho&quot;, mapa)), a_float(valor_col(fila, &quot;alto&quot;,
mapa))
target = int(cap_usada) if total_unidades is None else
int(total_unidades)
lay = mejor_distribucion_filas(largo, ancho, lp, ap)
if lay[&quot;cantidad&quot;] &lt;= 0 or target &lt;= 0: return go.Figure()
m_base = MallaAgrupada(&#39;#c18c5d&#39;, &#39;Madera&#39;)
m_base.agregar_cubo(0, 0, hp*0.8, lp, ap, hp*0.2)
m_base.agregar_cubo(0, 0, 0, lp*0.1, ap, hp*0.8);
m_base.agregar_cubo((lp-lp*0.1)/2, 0, 0, lp*0.1, ap, hp*0.8);
m_base.agregar_cubo(lp-lp*0.1, 0, 0, lp*0.1, ap, hp*0.8)
m_carga = MallaAgrupada(&#39;#2563eb&#39; if
es_formato_circular(valor_col(fila, &quot;formato&quot;, mapa)) else &#39;#d4a373&#39;,
&#39;Carga&#39;)
u_p, niv = 0, 0
while u_p &lt; target:
for c in lay[&quot;cajas&quot;]:
if u_p &gt;= target: break
if es_formato_circular(valor_col(fila, &quot;formato&quot;, mapa)):
m_carga.agregar_cilindro(c[&#39;x&#39;]+c[&#39;largo&#39;]/2, c[&#39;y&#39;]+c[&#39;ancho&#39;]/2, hp +
niv*alto, min(c[&#39;largo&#39;], c[&#39;ancho&#39;])/2 - 0.2, alto - 0.5)
else: m_carga.agregar_cubo(c[&#39;x&#39;]+0.25, c[&#39;y&#39;]+0.25, hp +
niv*alto, c[&#39;largo&#39;]-0.5, c[&#39;ancho&#39;]-0.5, alto-0.25)
u_p += 1
niv += 1
fig = go.Figure(data=[m_base.obtener_trazo(), m_carga.obtener_trazo()])

sku_name = valor_col(fila, &quot;sku&quot;, mapa)
_ = fig.update_layout(title=dict(text=f&quot;&lt;b&gt;�� Pallet Unitari
({sku_name})&lt;/b&gt;&quot;, x=0.5, font=dict(size=11, color=&quot;#475569&quot;)),
scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False),
zaxis=dict(visible=False), aspectmode=&#39;data&#39;),
margin=dict(r=0,l=0,b=0,t=25), height=300)
return fig
# ============================================================
# 3. MOTOR DE CÁLCULO LAYOUT 3D (CON CONSOLIDACIÓN DE SALDOS)
# ============================================================
def preparar_df_layout(df_base, mapa, modo):
df_l = pd.DataFrame({&#39;SKU&#39;: df_base[mapa[&#39;sku&#39;]]})
metrics = [calcular_metricas_dinamicas(row, mapa, modo) for _, row in
df_base.iterrows()]
df_l[&#39;Cantidad_Pallets&#39;], df_l[&#39;Peso_Pallet_kg&#39;] = [m[&#39;Pallets&#39;] for m
in metrics], [m[&#39;Peso_Pallet&#39;] for m in metrics]
df_l[&#39;Pallets_Completos_Optimo&#39;], df_l[&#39;Unidades_Sobrante_Optimo&#39;],
df_l[&#39;Capacidad_Optima&#39;] = [m[&#39;Pallets_Completos&#39;] for m in metrics],
[m[&#39;Unidades_Sobrante&#39;] for m in metrics], [m[&#39;Cap_Optima&#39;] for m in
metrics]
col_alto = mapa.get(&#39;altura_total&#39;) if mapa.get(&#39;altura_total&#39;) in
df_base.columns else mapa.get(&#39;alto&#39;)
df_l[&#39;Alto_m&#39;] = pd.to_numeric(df_base[col_alto],
errors=&#39;coerce&#39;).fillna(120) / 100.0 if col_alto and col_alto in
df_base.columns else 1.2
df_l[&#39;Bodega&#39;] = df_base[mapa[&#39;bodega&#39;]].astype(str) if
mapa.get(&#39;bodega&#39;) and mapa[&#39;bodega&#39;] in df_base.columns else &#39;N/D&#39;
abc =
df_base[mapa.get(&#39;abc&#39;)].fillna(&#39;C&#39;).astype(str).str.strip().str.upper() if
mapa.get(&#39;abc&#39;) and mapa.get(&#39;abc&#39;) in df_base.columns else pd.Series(&#39;C&#39;,
index=df_base.index)
xyz =
df_base[mapa.get(&#39;xyz&#39;)].fillna(&#39;Z&#39;).astype(str).str.strip().str.upper() if
mapa.get(&#39;xyz&#39;) and mapa.get(&#39;xyz&#39;) in df_base.columns else pd.Series(&#39;Z&#39;,
index=df_base.index)
df_l[&#39;ABC_XYZ&#39;] = df_base[mapa.get(&#39;abc_xyz&#39;)].fillna(abc +
xyz).astype(str).str.strip().str.upper() if mapa.get(&#39;abc_xyz&#39;) and
mapa.get(&#39;abc_xyz&#39;) in df_base.columns else abc + xyz
df_l[&#39;ABC_XYZ&#39;] = df_l[&#39;ABC_XYZ&#39;].replace({&#39;N/D&#39;: &#39;CZ&#39;, &#39;N/DN/D&#39;: &#39;CZ&#39;,
&#39;NAN&#39;: &#39;CZ&#39;})
df_l[&#39;ABC_XYZ&#39;] =
df_l[&#39;ABC_XYZ&#39;].astype(pd.CategoricalDtype(categories=[&#39;AX&#39;,&#39;AY&#39;,&#39;AZ&#39;,&#39;BX&#39;,
&#39;BY&#39;,&#39;BZ&#39;,&#39;CX&#39;,&#39;CY&#39;,&#39;CZ&#39;], ordered=True))
df_l[&#39;Formato&#39;], df_l[&#39;ABC&#39;] = df_base[mapa.get(&#39;formato&#39;)] if
mapa.get(&#39;formato&#39;) and mapa.get(&#39;formato&#39;) in df_base.columns else &#39;N/D&#39;,
abc.replace({&#39;N/D&#39;: &#39;C&#39;, &#39;NAN&#39;: &#39;C&#39;})
return df_l[df_l[&#39;Cantidad_Pallets&#39;] &gt;
0].sort_values(by=&#39;ABC_XYZ&#39;).reset_index(drop=True)

def motor_calculo_layout(df_activa, is_vertical, pal_v, conf):
l_m, a_m, alt_m, w_p, flujo = conf[&#39;l_bod&#39;], conf[&#39;a_bod&#39;],
conf[&#39;alt_bod&#39;], conf[&#39;ancho_porton&#39;], conf[&#39;tipo_flujo&#39;]
sz = []
if w_p &gt; 0 and flujo != &#39;Ninguno&#39;:
if &#39;Flujo en U&#39; in flujo: sz.extend([{&#39;x1&#39;: l_m*0.25 - w_p/2, &#39;y1&#39;:
0, &#39;x2&#39;: l_m*0.25 + w_p/2, &#39;y2&#39;: 6}, {&#39;x1&#39;: l_m*0.75 - w_p/2, &#39;y1&#39;: 0,
&#39;x2&#39;: l_m*0.75 + w_p/2, &#39;y2&#39;: 6}])
elif &#39;Flujo en I&#39; in flujo: sz.extend([{&#39;x1&#39;: l_m/2 - w_p/2, &#39;y1&#39;:
0, &#39;x2&#39;: l_m/2 + w_p/2, &#39;y2&#39;: 6}, {&#39;x1&#39;: l_m/2 - w_p/2, &#39;y1&#39;: a_m-6, &#39;x2&#39;:
l_m/2 + w_p/2, &#39;y2&#39;: a_m}])
elif &#39;Flujo en L&#39; in flujo: sz.extend([{&#39;x1&#39;: max(1, l_m*0.15 -
w_p/2), &#39;y1&#39;: 0, &#39;x2&#39;: max(1, l_m*0.15 - w_p/2)+w_p, &#39;y2&#39;: 6}, {&#39;x1&#39;: l_m-
6, &#39;y1&#39;: max(1, a_m*0.85 - w_p/2), &#39;x2&#39;: l_m, &#39;y2&#39;: max(1, a_m*0.85 -
w_p/2)+w_p}])
ap_w, pp_d, ap_h = 1.2, 1.2, float(df_activa[&#39;Alto_m&#39;].max()) if not
df_activa.empty else 1.2
v_l, v_a = (a_m, l_m) if is_vertical else (l_m, a_m)
t_m, a_n_v = 0.10, ap_h + 0.27
niv = max(1, sum(1 for n in range(50) if n*a_n_v+ap_h+0.15 &lt;= alt_m and
n*a_n_v &lt;= conf[&#39;alt_grua&#39;]))
l_mod = (ap_w * pal_v) + (0.10 * (pal_v + 1)) + t_m
pegar_pared = conf.get(&#39;racks_en_pared&#39;, False)
offset_y = 0.0 if pegar_pared else 2.0
offset_x = 0.0 if pegar_pared else 2.0
a_b = (pp_d * 2) + conf[&#39;pasillo&#39;]
s_c = conf[&#39;cant_pas_trans&#39;] + 1
espacio_x_disp = v_l - offset_x - (2.0 if not pegar_pared else 0.5)
m_x_s = math.floor(((espacio_x_disp - ((s_c-1) *
(conf[&#39;ancho_pas_trans&#39;] if conf[&#39;cant_pas_trans&#39;]&gt;0 else 0))) / s_c) /
l_mod) if s_c &gt; 0 else 0
dp_x, dp_y, cx, cy = conf[&#39;dist_pilares_x&#39;], conf[&#39;dist_pilares_y&#39;],
conf[&#39;cant_pilares_x&#39;], conf[&#39;cant_pilares_y&#39;]
dxr, nx = (l_m / (cx + 1), cx) if cx &gt; 0 else (dp_x, math.floor(l_m /
dp_x) if dp_x &gt; 0 else 0)
dyr, ny = (a_m / (cy + 1), cy) if cy &gt; 0 else (dp_y, math.floor(a_m /
dp_y) if dp_y &gt; 0 else 0)
pil_r = [(px * dxr, py * dyr) for px in range(1, nx + 1) for py in
range(1, ny + 1)]
v_pil = [(py, px) for px, py in pil_r] if is_vertical else pil_r
y_cursor = offset_y
filas_y = []
if pegar_pared:
filas_y.append([(y_cursor, &#39;A&#39;)])
y_cursor += pp_d + conf[&#39;pasillo&#39;]

while y_cursor + (pp_d * 2) &lt;= v_a - (0.0 if pegar_pared else 2.0):
filas_y.append([(y_cursor, &#39;A&#39;), (y_cursor + pp_d, &#39;B&#39;)])
y_cursor += (pp_d * 2) + conf[&#39;pasillo&#39;]
if pegar_pared and (y_cursor + pp_d &lt;= v_a):
filas_y.append([(y_cursor, &#39;A&#39;)])
p_l = conf.get(&#39;pilar_largo&#39;, 0.5)
p_a = conf.get(&#39;pilar_ancho&#39;, 0.5)
m_v, m_l, alm = 0, [] , []
for f, lados in enumerate(filas_y):
l_pas = chr(64 + f + 1) if f+1 &lt;= 26 else f&quot;P{f+1}&quot;
for s in range(s_c):
x_ini = offset_x + s * (m_x_s * l_mod +
(conf[&#39;ancho_pas_trans&#39;] if conf[&#39;cant_pas_trans&#39;]&gt;0 else 0))
for m in range(m_x_s):
xp = x_ini + (m * l_mod)
n_m = (s * m_x_s) + m + 1
for yr, lado in lados:
rx1, ry1, rx2, ry2 = (yr, xp, yr+pp_d, xp+l_mod) if
is_vertical else (xp, yr, xp+l_mod, yr+pp_d)
if any(not (rx2+1.5&lt;o[&#39;x&#39;] or rx1-1.5&gt;o[&#39;x&#39;]+o[&#39;w&#39;] or
ry2+1.5&lt;o[&#39;y&#39;] or ry1-1.5&gt;o[&#39;y&#39;]+o[&#39;d&#39;]) for o in conf.get(&#39;oficinas&#39;, []))
or any(not (rx2&lt;z[&#39;x1&#39;] or rx1&gt;z[&#39;x2&#39;] or ry2&lt;z[&#39;y1&#39;] or ry1&gt;z[&#39;y2&#39;]) for z
in sz): continue
b_p = any(xp - p_l/2 &lt;= px &lt;= xp + l_mod + p_l/2 and yr
- p_a/2 &lt;= py &lt;= yr + pp_d + p_a/2 for px, py in v_pil)
m_l.append({&#39;x&#39;: xp, &#39;y&#39;: yr, &#39;bloqueado&#39;: b_p})
if not b_p:
m_v += 1
for n in range(niv):
for p_i in range(pal_v):
alm.append({&#39;id_posicion&#39;: f&quot;{l_pas}-
{n_m:02d}-{n+1}{lado}-{p_i+1}&quot;, &#39;letra_pasillo&#39;: l_pas, &#39;pasillo&#39;: f+1,
&#39;lado&#39;: lado, &#39;modulo&#39;: n_m, &#39;nivel&#39;: n+1, &#39;slot&#39;: p_i+1, &#39;x&#39;: xp, &#39;y&#39;: yr,
&#39;x_pal&#39;: xp + t_m + 0.10 + (p_i * 1.3), &#39;z&#39;: n * a_n_v, &#39;ocupado&#39;: False})
alm.sort(key=lambda x: (x[&#39;letra_pasillo&#39;], x[&#39;nivel&#39;], x[&#39;x&#39;],
x[&#39;y&#39;]))
pallets_a_ubicar = []
saldos_pendientes = []
for _, row in df_activa.iterrows():
c = int(row.get(&quot;Cantidad_Pallets&quot;, 0))
if c &lt;= 0: continue
p_c = int(row.get(&quot;Pallets_Completos_Optimo&quot;, c)) if
pd.notna(row.get(&quot;Pallets_Completos_Optimo&quot;)) else c
sku = str(row[&quot;SKU&quot;]).strip().upper()
abc = str(row.get(&quot;ABC&quot;, &quot;C&quot;))
abc_xyz = str(row.get(&quot;ABC_XYZ&quot;, &quot;CZ&quot;))
es_cilindro = es_formato_circular(row.get(&quot;Formato&quot;, &quot;&quot;))

alt_full = float(row.get(&quot;Alto_m&quot;, ap_h))
peso_kg = float(row.get(&quot;Peso_Pallet_kg&quot;, 500))
cap_opt = max(row.get(&quot;Capacidad_Optima&quot;, 1), 1)
for _ in range(p_c):
pallets_a_ubicar.append({&quot;sku&quot;: sku, &quot;abc&quot;: abc, &quot;abc_xyz&quot;:
abc_xyz, &quot;es_cilindro&quot;: es_cilindro, &quot;alt_p&quot;: alt_full, &quot;es_saldo&quot;: False,
&quot;es_mixto&quot;: False, &quot;peso&quot;: peso_kg, &quot;unidades&quot;: cap_opt, &quot;cap_maxima&quot;:
cap_opt})
if c &gt; p_c:
u_sob = row.get(&quot;Unidades_Sobrante_Optimo&quot;, cap_opt)
pct = u_sob / cap_opt if cap_opt &gt; 0 else 1.0
saldos_pendientes.append({&quot;sku&quot;: sku, &quot;abc&quot;: abc, &quot;abc_xyz&quot;:
abc_xyz, &quot;es_cilindro&quot;: es_cilindro, &quot;alt_p_full&quot;: alt_full, &quot;pct&quot;: pct,
&quot;peso&quot;: peso_kg * pct, &quot;unidades&quot;: u_sob, &quot;cap_maxima&quot;: cap_opt})
if conf.get(&quot;consolidar_saldos&quot;, False):
saldos_pendientes.sort(key=lambda x: (x[&quot;es_cilindro&quot;], x[&quot;abc&quot;]))
bin_actual = []
vol_actual = 0.0
peso_actual = 0.0
for s in saldos_pendientes:
if (vol_actual + s[&quot;pct&quot;] &lt;= 1.05) and (peso_actual + s[&quot;peso&quot;]
&lt;= conf.get(&quot;peso_max_grua&quot;, 1500.0)):
bin_actual.append(s); vol_actual += s[&quot;pct&quot;]; peso_actual
+= s[&quot;peso&quot;]
else:
if bin_actual:
skus_mix = [b[&quot;sku&quot;] for b in bin_actual]
txt_sku = &quot;MIXTO: &quot; + &quot;, &quot;.join(skus_mix[:3]) + (&quot;...&quot;
if len(skus_mix)&gt;3 else &quot;&quot;)
pallets_a_ubicar.append({&quot;sku&quot;: txt_sku, &quot;abc&quot;:
bin_actual[0][&quot;abc&quot;], &quot;abc_xyz&quot;: bin_actual[0][&quot;abc_xyz&quot;], &quot;es_cilindro&quot;:
bin_actual[0][&quot;es_cilindro&quot;], &quot;alt_p&quot;: max([b[&quot;alt_p_full&quot;] for b in
bin_actual]) * min(1.0, vol_actual), &quot;es_saldo&quot;: False, &quot;es_mixto&quot;: True,
&quot;peso&quot;: peso_actual, &quot;unidades&quot;: len(bin_actual), &quot;cap_maxima&quot;:
len(bin_actual)})
bin_actual = [s]; vol_actual = s[&quot;pct&quot;]; peso_actual =
s[&quot;peso&quot;]
if bin_actual:
skus_mix = [b[&quot;sku&quot;] for b in bin_actual]
txt_sku = &quot;MIXTO: &quot; + &quot;, &quot;.join(skus_mix[:3]) + (&quot;...&quot; if
len(skus_mix)&gt;3 else &quot;&quot;)
pallets_a_ubicar.append({&quot;sku&quot;: txt_sku, &quot;abc&quot;:
bin_actual[0][&quot;abc&quot;], &quot;abc_xyz&quot;: bin_actual[0][&quot;abc_xyz&quot;], &quot;es_cilindro&quot;:
bin_actual[0][&quot;es_cilindro&quot;], &quot;alt_p&quot;: max([b[&quot;alt_p_full&quot;] for b in
bin_actual]) * min(1.0, vol_actual), &quot;es_saldo&quot;: False, &quot;es_mixto&quot;: True,
&quot;peso&quot;: peso_actual, &quot;unidades&quot;: len(bin_actual), &quot;cap_maxima&quot;:
len(bin_actual)})

else:
for s in saldos_pendientes:
pallets_a_ubicar.append({&quot;sku&quot;: s[&quot;sku&quot;], &quot;abc&quot;: s[&quot;abc&quot;],
&quot;abc_xyz&quot;: s[&quot;abc_xyz&quot;], &quot;es_cilindro&quot;: s[&quot;es_cilindro&quot;], &quot;alt_p&quot;: max(0.3,
s[&quot;alt_p_full&quot;] * s[&quot;pct&quot;]), &quot;es_saldo&quot;: True, &quot;es_mixto&quot;: False, &quot;peso&quot;:
s[&quot;peso&quot;], &quot;unidades&quot;: s[&quot;unidades&quot;], &quot;cap_maxima&quot;: s[&quot;cap_maxima&quot;]})
u = 0
for p in pallets_a_ubicar:
for s in alm:
if not s[&quot;ocupado&quot;] and not (p[&quot;peso&quot;] &gt;
conf.get(&quot;peso_max_grua&quot;, 1500.0) and s[&quot;nivel&quot;] &gt; 1):
s.update({&quot;ocupado&quot;: True, &quot;sku&quot;: p[&quot;sku&quot;], &quot;abc&quot;:
p[&quot;abc&quot;], &quot;abc_xyz&quot;: p[&quot;abc_xyz&quot;], &quot;alt_p&quot;: p[&quot;alt_p&quot;], &quot;es_cilindro&quot;:
p[&quot;es_cilindro&quot;], &quot;es_saldo&quot;: p[&quot;es_saldo&quot;], &quot;es_mixto&quot;: p[&quot;es_mixto&quot;],
&quot;unidades&quot;: p[&quot;unidades&quot;], &quot;cap_maxima&quot;: p[&quot;cap_maxima&quot;]})
u += 1
break
demanda_total = int(df_activa[&quot;Cantidad_Pallets&quot;].sum()) if not
conf.get(&quot;consolidar_saldos&quot;, False) else len(pallets_a_ubicar)
return {&quot;modulos&quot;: m_v, &quot;niveles&quot;: niv, &quot;capacidad&quot;: len(alm),
&quot;demanda&quot;: demanda_total, &quot;diferencia&quot;: len(alm) - demanda_total,
&quot;staging&quot;: sz, &quot;oficinas&quot;: conf.get(&quot;oficinas&quot;, []), &quot;modulos_list&quot;: m_l,
&quot;almacen&quot;: alm, &quot;pilares_reales&quot;: pil_r, &quot;pallets_ubicados_totales&quot;: u,
&quot;alt_nivel_viga&quot;: a_n_v, &quot;l_modulo&quot;: l_mod, &quot;t_marco&quot;: t_m, &quot;pp_d&quot;: pp_d,
&quot;ap_w&quot;: ap_w, &quot;viga_h&quot;: 0.12, &quot;is_vertical&quot;: is_vertical, &quot;forma_pilar&quot;:
conf.get(&quot;forma_pilar&quot;, &quot;Cuadrado / Rectangular&quot;), &quot;pilar_largo&quot;: p_l,
&quot;pilar_ancho&quot;: p_a}
# ============================================================
# 5. PÁGINAS Y NAVEGACIÓN
# ============================================================
def cambiar_menu(pagina):
st.session_state.menu_seleccion = pagina
def mostrar_portada():
st.markdown(color_styles, unsafe_allow_html=True)
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;hero-container-color&quot;&gt;&lt;div class=&quot;hero-
title-color&quot;&gt;WMS Analytics Hub&lt;/div&gt;&lt;div class=&quot;hero-subtitle-
color&quot;&gt;Plataforma integral de ingeniería logística para la optimización de
almacenamiento, cubicación geométrica y diseño avanzado de layout de
bodegas.&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.markdown(&quot;&lt;h3 style=&#39;color:#0f172a; font-weight:800; margin-bottom:
20px;&#39;&gt;MÓDULOS DE CONTROL&lt;/h3&gt;&quot;, unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card&quot;&gt;&lt;div&gt;&lt;div class=&quot;card-icon-
header&quot;&gt;&lt;span class=&quot;card-icon&quot;&gt;��&lt;/span&gt;&lt;span class=&quot;card-tag-color tag-
blue&quot;&gt;DISPONIBLE&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-card-title&quot;&gt;Cubicadora de
Pallets&lt;/div&gt;&lt;p class=&quot;color-card-desc&quot;&gt;Cálculo algorítmico de volumen,

estiba optimizada de productos y previsualización 2D/3D con filtros
ABC.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.button(&quot;⚙️ Abrir Cubicadora&quot;, key=&quot;btn_cub&quot;, type=&quot;primary&quot;,
use_container_width=True, on_click=cambiar_menu, args=(&quot;�� Cubicador
WMS&quot;,))
with c2:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card color-card-green&quot;&gt;&lt;div&gt;&lt;div
class=&quot;card-icon-header&quot;&gt;&lt;span class=&quot;card-icon&quot;&gt;��️&lt;/span&gt;&lt;spa
class=&quot;card-tag-color tag-green&quot;&gt;DISPONIBLE&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-
card-title&quot;&gt;Layout de Bodega&lt;/div&gt;&lt;p class=&quot;color-card-desc&quot;&gt;Diseñador
espacial de CD, optimización IA, Gemelo Digital 3D y Exportador de
posiciones WMS.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.button(&quot;⚙️ Abrir Diseñador Layout&quot;, key=&quot;btn_lay&quot;,
type=&quot;primary&quot;, use_container_width=True, on_click=cambiar_menu, args=(&quot;��
Layout de Bodega&quot;,))
with c3:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card color-card-purple&quot;&gt;&lt;div&gt;&lt;div
class=&quot;card-icon-header&quot;&gt;&lt;span class=&quot;card-icon&quot;&gt;��&lt;/span&gt;&lt;spa
class=&quot;card-tag-color tag-purple&quot;&gt;DISPONIBLE&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-
card-title&quot;&gt;Analytics &amp; Reportería&lt;/div&gt;&lt;p class=&quot;color-card-
desc&quot;&gt;Dashboard de indicadores clave (KPIs), volumetría total, ocupación
física y análisis gerencial.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.button(&quot;�� Abrir Dashboard Analytics&quot;, key=&quot;btn_an&quot;
type=&quot;primary&quot;, use_container_width=True, on_click=cambiar_menu, args=(&quot;�
Analytics &amp; Reportería&quot;,))
c4, c5, c6 = st.columns(3)
with c4:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card color-card-amber&quot;&gt;&lt;div&gt;&lt;div
class=&quot;card-icon-header&quot;&gt;&lt;span class=&quot;card-icon&quot;&gt;��&lt;/span&gt;&lt;spa
class=&quot;card-tag-color tag-amber&quot; style=&quot;background:#fef3c7;
color:#b45309;&quot;&gt;NUEVO&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-card-title&quot;&gt;Entrada
(Inbound)&lt;/div&gt;&lt;p class=&quot;color-card-desc&quot;&gt;Registro de ASN, paletizado
inteligente en andén y sugerencias de Put-Away en el
Layout.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.button(&quot;�� Abrir Inbound&quot;, key=&quot;btn_in&quot;, type=&quot;primary&quot;
use_container_width=True, on_click=cambiar_menu, args=(&quot;�� Entrad
Mercadería&quot;,))
with c5:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card color-card-rose&quot;&gt;&lt;div&gt;&lt;div
class=&quot;card-icon-header&quot;&gt;&lt;span class=&quot;card-icon&quot;&gt;��&lt;/span&gt;&lt;spa
class=&quot;card-tag-color tag-rose&quot; style=&quot;background:#ffe4e6;
color:#e11d48;&quot;&gt;NUEVO&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-card-title&quot;&gt;Salida
(Outbound)&lt;/div&gt;&lt;p class=&quot;color-card-desc&quot;&gt;Olas de picking, trazado de
rutas cortas y simulación de despacho hacia andenes de
salida.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;, unsafe_allow_html=True)
st.button(&quot;�� Abrir Outbound&quot;, key=&quot;btn_out&quot;, type=&quot;primary&quot;
use_container_width=True, on_click=cambiar_menu, args=(&quot;�� Salid
Mercadería&quot;,))
with c6:
st.markdown(&quot;&quot;&quot;&lt;div class=&quot;color-card&quot; style=&quot;border-top-
color:#0ea5e9;&quot;&gt;&lt;div&gt;&lt;div class=&quot;card-icon-header&quot;&gt;&lt;span class=&quot;card-
icon&quot;&gt;��&lt;/span&gt;&lt;span class=&quot;card-tag-color&quot; style=&quot;background:#e0f2fe

color:#0369a1;&quot;&gt;NUEVO&lt;/span&gt;&lt;/div&gt;&lt;div class=&quot;color-card-title&quot;&gt;Movimientos
Internos&lt;/div&gt;&lt;p class=&quot;color-card-desc&quot;&gt;Consolidación de saldos por SKU
(Prevención Efecto Panal) y optimización del Racking.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;&quot;&quot;,
unsafe_allow_html=True)
st.button(&quot;�� Abrir Movimientos&quot;, key=&quot;btn_mov&quot;, type=&quot;primary&quot;
use_container_width=True, on_click=cambiar_menu, args=(&quot;�� Movimiento
Internos&quot;,))
def mostrar_cubicadora():
st.markdown(css_styles, unsafe_allow_html=True)
st.title(&quot;�� Cubicadora de Palletización Masiva&quot;)
archivo_subido = st.file_uploader(&quot;�� Sube tu archivo Excel con la bas
de datos&quot;, type=[&quot;xlsx&quot;])
if archivo_subido is not None:
with st.spinner(&quot;Procesando base de datos...&quot;):
try: df_original = pd.read_excel(archivo_subido,
sheet_name=&quot;Data Equipo 7&quot;)
except: df_original = pd.read_excel(archivo_subido,
sheet_name=0)
df_res, MAPA =
procesar_datos(df_original.dropna(how=&quot;all&quot;).reset_index(drop=True))
st.session_state.df_original, st.session_state.df_resultados,
st.session_state.mapa_columnas = df_original, df_res, MAPA
if st.session_state.df_resultados is not None:
df_f = st.session_state.df_resultados.copy()
MAPA = st.session_state.mapa_columnas
# FILTRO GLOBAL DE BODEGA
if getattr(st.session_state, &#39;bodegas_sel&#39;, []):
df_f =
df_f[df_f[MAPA[&#39;bodega&#39;]].isin(st.session_state.bodegas_sel)]
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
modo = st.radio(&quot;⚙️ Modo de cálculo:&quot;, [&quot;EXCEL&quot;, &quot;OPTIMO&quot;])
with col_m2:
if MAPA.get(&#39;abc&#39;):
opc_abc = sorted([str(x) for x in
df_f[MAPA[&#39;abc&#39;]].unique() if str(x) != &#39;nan&#39;])
if opc_abc: df_f =
df_f[df_f[MAPA[&#39;abc&#39;]].isin(st.multiselect(&quot;�� Filtro ABC:&quot;, opc_abc
default=opc_abc))]
with col_m3:
if MAPA.get(&#39;xyz&#39;):
opc_xyz = sorted([str(x) for x in
df_f[MAPA[&#39;xyz&#39;]].unique() if str(x) != &#39;nan&#39;])
if opc_xyz: df_f =
df_f[df_f[MAPA[&#39;xyz&#39;]].isin(st.multiselect(&quot;�� Filtro XYZ:&quot;, opc_xyz
default=opc_xyz))]
with col_m4:
if MAPA.get(&#39;bodega&#39;) and MAPA[&#39;bodega&#39;] in df_f.columns:

opc_bod_cub = sorted([str(x) for x in
df_f[MAPA[&#39;bodega&#39;]].unique() if pd.notna(x) and str(x) != &#39;nan&#39; and str(x)
!= &#39;N/D&#39;])
if opc_bod_cub:
bod_def = [b for b in
st.session_state.get(&quot;bodegas_sel&quot;, opc_bod_cub) if b in opc_bod_cub] or
opc_bod_cub
bod_cub_sel = st.multiselect(&quot;�� Filtro Bodega:&quot;
opc_bod_cub, default=bod_def, key=&quot;ms_bodega_cub_page&quot;)
df_f = df_f[df_f[MAPA[&#39;bodega&#39;]].isin(bod_cub_sel)]
st.session_state.bodegas_sel = bod_cub_sel
st.markdown(&quot;&lt;h3 style=&#39;color:#0f172a; font-weight:800; font-
size:18px; margin-top:20px;&#39;&gt;�� Buscador Masivo y Panel de Cálculo&lt;/h3&gt;&quot;
unsafe_allow_html=True)
lista_skus_all =
df_f[MAPA[&quot;sku&quot;]].astype(str).str.upper().unique().tolist()
opcion_vis = st.radio(&quot;Método de Visualización:&quot;, [&quot;Elegir de la
lista&quot;, &quot;Pegar lista (Excel)&quot;, &quot;Ver primeros 10&quot;, &quot;Ver TODOS&quot;],
horizontal=True)
skus_a_procesar = []
if opcion_vis == &quot;Elegir de la lista&quot;:
def_sel = [lista_skus_all[0]] if (lista_skus_all and not
st.session_state.skus_activos) else [s for s in
st.session_state.skus_activos if s in lista_skus_all]
if not def_sel and lista_skus_all: def_sel =
[lista_skus_all[0]]
skus_a_procesar = st.multiselect(&quot;Seleccionar SKUs
individualmente:&quot;, options=lista_skus_all, default=def_sel)
elif opcion_vis == &quot;Pegar lista (Excel)&quot;:
txt_list = st.text_area(&quot;Pega aquí la columna copiada de
Excel:&quot;, height=80)
if txt_list:
ext = [s.strip().upper() for s in re.split(r&#39;[,\s;\n]+&#39;,
txt_list) if s.strip()]
skus_a_procesar = [s for s in ext if s in lista_skus_all]
inv = [s for s in ext if s not in lista_skus_all]
if inv: st.warning(f&quot;⚠️ SKUs no encontrados: {&#39;,
&#39;.join(inv)}&quot;)
elif opcion_vis == &quot;Ver primeros 10&quot;: skus_a_procesar =
lista_skus_all[:10]
elif opcion_vis == &quot;Ver TODOS&quot;: skus_a_procesar = lista_skus_all
st.session_state.skus_activos = skus_a_procesar
st.markdown(&quot;&lt;br&gt;&quot;, unsafe_allow_html=True)
mostrar_graf = st.toggle(&quot;��️ Mostrar Planos 2D / 3D&quot;, value=True)
if st.session_state.skus_activos: df_kpi =
df_f[df_f[MAPA[&#39;sku&#39;]].astype(str).str.upper().isin(st.session_state.skus_a
ctivos)]
else: df_kpi = df_f

escenario_stock = st.session_state.get(&quot;tipo_stock&quot;, &quot;Stock
Promedio&quot;)
key_stock_eval = &quot;stock_maximo&quot; if escenario_stock == &quot;Stock
Máximo&quot; else &quot;stock_promedio&quot;
col_stock_val = MAPA.get(key_stock_eval, MAPA.get(&quot;stock&quot;,
df_kpi.columns[0]))
if col_stock_val not in df_kpi.columns: col_stock_val =
MAPA.get(&quot;stock&quot;, df_kpi.columns[0])
tot_sku_kpi = len(df_kpi)
con_stock_kpi = int((pd.to_numeric(df_kpi[col_stock_val],
errors=&quot;coerce&quot;).fillna(0) &gt; 0).sum())
tot_pallets_kpi = sum([calcular_metricas_dinamicas(row, MAPA,
modo)[&quot;Pallets&quot;] for _, row in df_kpi.iterrows()])
alertas_activas_kpi = sum(1 for _, row in df_kpi.iterrows() if
&quot;EXCEL&quot; in calcular_metricas_dinamicas(row, MAPA, modo)[&quot;Estado&quot;] or
&quot;PELIGRO&quot; in calcular_metricas_dinamicas(row, MAPA, modo)[&quot;Estado&quot;] or
&quot;REVISAR&quot; in calcular_metricas_dinamicas(row, MAPA, modo)[&quot;Estado&quot;])
modo_txt = &quot;MODO EXCEL (VALORES MANUALES)&quot; if modo == &quot;EXCEL&quot; else
&quot;MODO OPTIMIZADO (MÁXIMA FÍSICA)&quot;
color_modo = &quot;#3b82f6&quot; if modo == &quot;EXCEL&quot; else &quot;#f59e0b&quot;
st.markdown(f&quot;&quot;&quot;
&lt;div style=&quot;font-family: &#39;Segoe UI&#39;, system-ui, sans-serif;
background: #0f172a; border-radius: 12px 12px 0 0; padding: 18px 25px;
display: flex; justify-content: space-between; align-items: center; margin-
top: 15px;&quot;&gt;
&lt;div&gt;&lt;h3 style=&quot;color: #ffffff; margin: 0; font-size: 20px;
font-weight: 800; letter-spacing: -0.5px;&quot;&gt;WMS Analytics: Dashboard
Paletizado&lt;/h3&gt;&lt;p style=&quot;color: #94a3b8; margin: 3px 0 0 0; font-size:
12px;&quot;&gt;Estado: &lt;b style=&quot;color:{color_modo};&quot;&gt;{modo_txt}&lt;/b&gt;&lt;/p&gt;&lt;/div&gt;
&lt;div&gt;&lt;span style=&quot;background: {color_modo}; color: white;
padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 800;
letter-spacing: 0.5px;&quot;&gt;{modo}&lt;/span&gt;&lt;/div&gt;
&lt;/div&gt;
&quot;&quot;&quot;, unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.markdown(f&quot;&lt;div style=&#39;background:#ffffff;border:1px
solid #e2e8f0;border-left:4px solid #3b82f6;border-radius:0 0 0
8px;padding:14px 16px;margin-bottom:20px;&#39;&gt;&lt;div style=&#39;font-size:10px;font-
weight:800;color:#64748b;letter-spacing:0.5px;margin-bottom:4px;&#39;&gt;TOTAL SKU
(FILTRADO)&lt;/div&gt;&lt;div style=&#39;font-size:22px;font-
weight:800;color:#0f172a;&#39;&gt;{tot_sku_kpi:,}&lt;/div&gt;&lt;/div&gt;&quot;,
unsafe_allow_html=True)
with k2: st.markdown(f&quot;&lt;div style=&#39;background:#ffffff;border:1px
solid #e2e8f0;border-left:4px solid #10b981;padding:14px 16px;margin-
bottom:20px;&#39;&gt;&lt;div style=&#39;font-size:10px;font-
weight:800;color:#64748b;letter-spacing:0.5px;margin-bottom:4px;&#39;&gt;SKUs CON
{escenario_stock.upper()}&lt;/div&gt;&lt;div style=&#39;font-size:22px;font-
weight:800;color:#0f172a;&#39;&gt;{con_stock_kpi:,}&lt;/div&gt;&lt;/div&gt;&quot;,
unsafe_allow_html=True)

with k3: st.markdown(f&quot;&lt;div style=&#39;background:#f5f3ff;border:1px
solid #ddd6fe;border-left:4px solid #6366f1;padding:14px 16px;margin-
bottom:20px;&#39;&gt;&lt;div style=&#39;font-size:10px;font-
weight:800;color:#4338ca;letter-spacing:0.5px;margin-bottom:4px;&#39;&gt;PALLETS
REQ.&lt;/div&gt;&lt;div style=&#39;font-size:22px;font-
weight:800;color:#4f46e5;&#39;&gt;{tot_pallets_kpi:,}&lt;/div&gt;&lt;/div&gt;&quot;,
unsafe_allow_html=True)
with k4: st.markdown(f&quot;&lt;div style=&#39;background:#f5f3ff;border:1px
solid #ddd6fe;border-left:4px solid #8b5cf6;padding:14px 16px;margin-
bottom:20px;&#39;&gt;&lt;div style=&#39;font-size:10px;font-
weight:800;color:#5b21b6;letter-spacing:0.5px;margin-
bottom:4px;&#39;&gt;POSICIONES&lt;/div&gt;&lt;div style=&#39;font-size:22px;font-
weight:800;color:#7c3aed;&#39;&gt;{tot_pallets_kpi:,}&lt;/div&gt;&lt;/div&gt;&quot;,
unsafe_allow_html=True)
with k5: st.markdown(f&quot;&lt;div style=&#39;background:#fef2f2;border:1px
solid #fecaca;border-left:4px solid #ef4444;border-radius:0 0 8px
0;padding:14px 16px;margin-bottom:20px;&#39;&gt;&lt;div style=&#39;font-size:10px;font-
weight:800;color:#991b1b;letter-spacing:0.5px;margin-bottom:4px;&#39;&gt;ALERTAS
ACTIVAS&lt;/div&gt;&lt;div style=&#39;font-size:22px;font-weight:800;color:{&#39;#dc2626&#39; if
alertas_activas_kpi &gt; 0 else
&#39;#10b981&#39;};&#39;&gt;{alertas_activas_kpi:,}&lt;/div&gt;&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;---&quot;)
tab_buscar, tab_descargar, tab_alertas, tab_datos = st.tabs([&quot;�
Resultados Detallados&quot;, &quot;�� Descargar Reporte&quot;, &quot;�� Ver Alertas&quot;, &quot;�� B
de Datos&quot;])
with tab_buscar:
if not st.session_state.skus_activos: st.markdown(&quot;&lt;div
style=&#39;text-align:center; padding: 30px; color:#64748b;&#39;&gt;&lt;h4&gt;No hay SKUs
seleccionados.&lt;/h4&gt;&lt;/div&gt;&quot;, unsafe_allow_html=True)
else:
for sku in st.session_state.skus_activos:
filtro =
df_kpi[df_kpi[MAPA[&quot;sku&quot;]].astype(str).str.upper() == sku]
if not filtro.empty:
fila = filtro.iloc[0]
m = calcular_metricas_dinamicas(fila, MAPA, modo)
formato = fila.get(MAPA.get(&#39;formato&#39;, &#39;Formato&#39;),
&#39;N/D&#39;)
fam = fila.get(MAPA.get(&#39;familia&#39;, &#39;Familia&#39;),
&#39;N/D&#39;)
bodega = fila.get(MAPA.get(&#39;bodega&#39;, &#39;Bodega&#39;),
&#39;N/D&#39;)
rank = fila.get(MAPA.get(&#39;ranking&#39;, &#39;Ranking&#39;),
&#39;N/D&#39;)
abc_xyz = fila.get(MAPA.get(&#39;abc_xyz&#39;,
&#39;Matriz_ABC_XYZ&#39;), &#39;N/D&#39;)
if pd.isna(formato): formato = &#39;N/D&#39;
if pd.isna(fam): fam = &#39;N/D&#39;
if pd.isna(bodega): bodega = &#39;N/D&#39;
if pd.isna(rank): rank = &#39;N/D&#39;

if pd.isna(abc_xyz): abc_xyz = &#39;N/D&#39;
cap, cap_excel, cap_optima, pallets, peso_est,
efi_vol, ult_unids, ult_pct, estado = m[&#39;Capacidad_Usada&#39;], m[&#39;Cap_Excel&#39;],
m[&#39;Cap_Optima&#39;], m[&#39;Pallets&#39;], m[&#39;Peso_Pallet&#39;], m[&#39;Eficiencia_Volumen&#39;],
m[&#39;Unidades_Ultimo&#39;], m[&#39;Ocupacion_Ultimo&#39;], m[&#39;Estado&#39;]
color_estado = &quot;#ef4444&quot; if &quot;PELIGRO&quot; in estado or
&quot;EXCEL&quot; in estado else &quot;#f59e0b&quot; if &quot;REVISAR&quot; in estado else &quot;#10b981&quot;
bg_estado = &quot;#fef2f2&quot; if &quot;PELIGRO&quot; in estado or
&quot;EXCEL&quot; in estado else &quot;#fffbeb&quot; if &quot;REVISAR&quot; in estado else &quot;#ecfdf5&quot;
border_estado = &quot;#fecaca&quot; if &quot;PELIGRO&quot; in estado or
&quot;EXCEL&quot; in estado else &quot;#fde68a&quot; if &quot;REVISAR&quot; in estado else &quot;#a7f3d0&quot;
html_header = clean_html(f&quot;&quot;&quot;&lt;div style=&quot;font-
family: &#39;Segoe UI&#39;, system-ui, sans-serif; width: 100%; background:
#ffffff; border: 1px solid #e2e8f0; border-bottom:none; border-radius: 12px
12px 0 0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow: hidden; box-
sizing: border-box;&quot;&gt;
&lt;div style=&quot;background: #0f172a; padding: 20px 25px; display: flex;
justify-content: space-between; align-items: center; border-bottom: 4px
solid {color_estado};&quot;&gt;
&lt;div&gt;&lt;div style=&quot;color: #94a3b8; font-size: 11px; font-weight: 800; letter-
spacing: 1px;&quot;&gt;ANÁLISIS DE ESTIBA&lt;/div&gt;&lt;div style=&quot;color: #ffffff; font-
size: 26px; font-weight: 900; margin: 4px 0;&quot;&gt;{sku}&lt;/div&gt;&lt;div style=&quot;color:
#cbd5e1; font-size: 13px;&quot;&gt;Formato: &lt;span style=&quot;color: #fff; font-
weight:600;&quot;&gt;{formato}&lt;/span&gt; &amp;nbsp;|&amp;nbsp; Familia: &lt;span style=&quot;color:
#fff; font-weight:600;&quot;&gt;{fam}&lt;/span&gt; &amp;nbsp;|&amp;nbsp; Bodega: &lt;span
style=&quot;color: #38bdf8; font-weight:700;&quot;&gt;{bodega}&lt;/span&gt;&lt;/div&gt;&lt;/div&gt;
&lt;div style=&quot;background: {bg_estado}; border: 1px solid {border_estado};
padding: 10px 18px; border-radius: 6px; text-align: right;&quot;&gt;&lt;div
style=&quot;color: {color_estado}; font-size: 10px; font-weight:
900;&quot;&gt;DIAGNÓSTICO&lt;/div&gt;&lt;div style=&quot;color: {color_estado}; font-size: 15px;
font-weight: 900;&quot;&gt;{estado}&lt;/div&gt;&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;padding: 20px 25px 5px 25px;&quot;&gt;
&lt;div style=&quot;display: grid; grid-template-columns: repeat(5, 1fr); gap:
15px; margin-bottom: 15px;&quot;&gt;
&lt;div class=&quot;kpi-box&quot;&gt;&lt;div class=&quot;kpi-title&quot;&gt;{escenario_stock}&lt;/div&gt;&lt;div
class=&quot;kpi-value&quot;&gt;{fmt(m[&#39;Stock&#39;], 1)}&lt;/div&gt;&lt;/div&gt;
&lt;div class=&quot;kpi-box&quot; style=&quot;background:#f0f9ff; border:1px solid
#bae6fd;&quot;&gt;&lt;div class=&quot;kpi-title&quot;&gt;Unid. Pallet&lt;/div&gt;&lt;div class=&quot;kpi-value&quot;
style=&quot;color:#0284c7;&quot;&gt;{fmt(cap, 0)}&lt;/div&gt;&lt;/div&gt;
&lt;div class=&quot;kpi-box&quot; style=&quot;background:#f0f9ff; border:1px solid
#bae6fd;&quot;&gt;&lt;div class=&quot;kpi-title&quot;&gt;Pallets Req.&lt;/div&gt;&lt;div class=&quot;kpi-value&quot;
style=&quot;color:#0284c7;&quot;&gt;{pallets}&lt;/div&gt;&lt;/div&gt;
&lt;div class=&quot;kpi-box {&#39;kpi-box-danger&#39; if es_numero(peso_est) and peso_est &gt;
MAX_PESO_PALLET else &#39;&#39;}&quot;&gt;&lt;div class=&quot;kpi-title&quot;&gt;Peso (Kg)&lt;/div&gt;&lt;div
class=&quot;kpi-value {&#39;kpi-value-danger&#39; if es_numero(peso_est) and peso_est &gt;
MAX_PESO_PALLET else &#39;&#39;}&quot;&gt;{fmt(peso_est, 1)}&lt;/div&gt;&lt;/div&gt;
&lt;div class=&quot;kpi-box&quot;&gt;&lt;div class=&quot;kpi-title&quot;&gt;Volumen %&lt;/div&gt;&lt;div class=&quot;kpi-
value&quot;&gt;{fmt(efi_vol, 1)}%&lt;/div&gt;&lt;/div&gt;
&lt;/div&gt;

&lt;/div&gt;
&lt;/div&gt;&quot;&quot;&quot;)
html_datos_base = clean_html(f&quot;&quot;&quot;&lt;div
style=&quot;background: #f8fafc; border: 1px solid #e2e8f0; border-top: none;
border-radius: 0 0 0 12px; padding: 20px; font-family: system-ui; height:
100%; box-sizing: border-box;&quot;&gt;
&lt;h4 style=&quot;margin:0 0 10px 0; font-size:13px; color:#334155; border-
bottom:2px solid #e2e8f0; padding-bottom:5px;&quot;&gt;�� Datos Base&lt;/h4&gt;
&lt;div style=&quot;display: grid; grid-template-columns: auto 1fr; gap: 8px 12px;
font-size: 12px; color: #475569;&quot;&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Largo:&lt;/span&gt;&lt;span&gt;{fmt(a_float(valor_col(fila, &#39;largo&#39;,
MAPA)),1)} cm&lt;/span&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Ancho:&lt;/span&gt;&lt;span&gt;{fmt(a_float(valor_col(fila, &#39;ancho&#39;,
MAPA)),1)} cm&lt;/span&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Alto:&lt;/span&gt;&lt;span&gt;{fmt(a_float(valor_col(fila, &#39;alto&#39;,
MAPA)),1)} cm&lt;/span&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Peso:&lt;/span&gt;&lt;span&gt;{fmt(a_float(valor_col(fila, &#39;peso&#39;,
MAPA)),2)} kg&lt;/span&gt;&lt;/div&gt;
&lt;h4 style=&quot;margin:16px 0 8px 0; font-size:13px; color:#334155; border-
bottom:2px solid #e2e8f0; padding-bottom:5px;&quot;&gt;��️ Perfil Logístico&lt;/h4&gt;
&lt;div style=&quot;display: grid; grid-template-columns: auto 1fr; gap: 8px 12px;
font-size: 12px; color: #475569;&quot;&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Ranking:&lt;/span&gt;&lt;span&gt;#{fmt(rank,0) if es_numero(rank) else
rank}&lt;/span&gt;&lt;span style=&quot;font-weight:600;&quot;&gt;Matriz ABC-XYZ:&lt;/span&gt;&lt;span
style=&quot;font-weight:bold; color:#0284c7;&quot;&gt;{abc_xyz}&lt;/span&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Zonificación:&lt;/span&gt;&lt;span style=&quot;font-weight:bold;
color:#0f766e;&quot;&gt;{bodega}&lt;/span&gt;&lt;/div&gt;
&lt;h4 style=&quot;margin:16px 0 8px 0; font-size:13px; color:#334155; border-
bottom:2px solid #e2e8f0; padding-bottom:5px;&quot;&gt;⚙️ Resultados&lt;/h4&gt;
&lt;div style=&quot;display: grid; grid-template-columns: auto 1fr; gap: 8px 12px;
font-size: 12px; color: #475569;&quot;&gt;&lt;span style=&quot;color:#ef4444; font-
weight:bold;&quot;&gt;Excel (Manual):&lt;/span&gt;&lt;span style=&quot;color:#ef4444; font-
weight:bold;&quot;&gt;{fmt(cap_excel,0)} u&lt;/span&gt;&lt;span style=&quot;color:#10b981; font-
weight:bold;&quot;&gt;Óptimo Física:&lt;/span&gt;&lt;span style=&quot;color:#10b981; font-
weight:bold;&quot;&gt;{fmt(cap_optima,0)} u&lt;/span&gt;&lt;span style=&quot;font-
weight:600;&quot;&gt;Últ. Pallet:&lt;/span&gt;&lt;span&gt;{fmt(ult_pct,1)}%
({fmt(ult_unids,1)}u)&lt;/span&gt;&lt;/div&gt;
&lt;/div&gt;&quot;&quot;&quot;)
st.markdown(html_header, unsafe_allow_html=True)
col_izq, col_der = st.columns([1, 3])
with col_izq:
st.markdown(html_datos_base,
unsafe_allow_html=True)
with col_der:
if mostrar_graf and not
MAPA.get(&#39;is_opt_report&#39;):
st.markdown(&quot;&lt;div style=&#39;border: 1px solid
#e2e8f0; border-top: none; border-radius: 0 0 12px 0; padding: 20px;
background: #ffffff; height: 100%;&#39;&gt;&quot;, unsafe_allow_html=True)

mostrar_3d_sku = st.toggle(f&quot;�� Levanta
Maqueta 3D&quot;, key=f&quot;t_{sku}&quot;)
c_pb1, c_pb2, c_pb3 = st.columns(3)
with c_pb1:
st.markdown(f&quot;&lt;div style=&#39;font-
size:10px; text-align:center; font-weight:800; color:#334155; margin-
bottom:5px;&#39;&gt;PLANO PLANTA (N1)&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(html_vista_superior(fila,
MAPA), unsafe_allow_html=True)
with c_pb2:
st.markdown(f&quot;&lt;div style=&#39;font-
size:10px; text-align:center; font-weight:800; color:#334155; margin-
bottom:5px;&#39;&gt;PLANO ALZADO&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(html_vista_lateral(fila,
MAPA, m[&#39;Capacidad_Usada&#39;]), unsafe_allow_html=True)
with c_pb3:
if mostrar_3d_sku:
st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m[&#39;Capacidad_Usada&#39;]),
use_container_width=True, key=f&quot;pb_{sku}&quot;)
else:
st.markdown(&quot;&lt;div
style=&#39;height:200px; display:flex; align-items:center; justify-
content:center; background:#f8fafc; border:1px dashed #cbd5e1; border-
radius:8px; color:#94a3b8; font-size:11px; font-weight:bold;&#39;&gt;Activa el
botón &#39;Levantar Maqueta 3D&#39; para renderizar.&lt;/div&gt;&quot;,
unsafe_allow_html=True)
if m[&#39;Unidades_Sobrante&#39;] &gt; 0:
st.markdown(&quot;&lt;hr style=&#39;margin:10px
0;&#39;&gt;&quot;, unsafe_allow_html=True)
c_ps1, c_ps2, c_ps3 = st.columns(3)
with c_ps1:
st.markdown(f&quot;&lt;div style=&#39;font-
size:10px; text-align:center; font-weight:800; color:#0284c7; margin-
bottom:5px;&#39;&gt;PLANTA PALLET SOBRANTE&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(html_vista_superior(fila, MAPA, m[&#39;Unidades_Sobrante&#39;]),
unsafe_allow_html=True)
with c_ps2:
st.markdown(f&quot;&lt;div style=&#39;font-
size:10px; text-align:center; font-weight:800; color:#0284c7; margin-
bottom:5px;&#39;&gt;ALZADO PALLET SOBRANTE&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(html_vista_lateral(fila, MAPA, m[&#39;Capacidad_Usada&#39;],
m[&#39;Unidades_Sobrante&#39;]), unsafe_allow_html=True)
with c_ps3:
if mostrar_3d_sku:
st.plotly_chart(renderizar_3d_plotly(fila, MAPA, m[&#39;Capacidad_Usada&#39;],
m[&#39;Unidades_Sobrante&#39;]), use_container_width=True, key=f&quot;ps_{sku}&quot;)
else:
st.markdown(&quot;&lt;hr style=&#39;margin:10px
0;&#39;&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;&lt;div style=&#39;text-

align:center; padding: 15px; background: #f0fdf4; border: 1px dashed
#bbf7d0; border-radius: 8px; color: #166534; font-size: 13px; font-weight:
bold;&#39;&gt;✅ Todos los pallets están 100% completos.&lt;/div&gt;&quot;,
unsafe_allow_html=True)
st.markdown(&quot;&lt;/div&gt;&quot;,
unsafe_allow_html=True)
else:
st.markdown(&quot;&lt;div style=&#39;border: 1px solid
#e2e8f0; border-top: none; border-radius: 0 0 12px 0; padding: 20px;
background: #ffffff; height: 100%; display:flex; align-items:center;
justify-content:center;&#39;&gt;&lt;div style=&#39;text-align:center; color:#64748b;&#39;&gt;&lt;h4
style=&#39;margin:0;&#39;&gt;⚠️ Carga desde Reporte Optimizado&lt;/h4&gt;&lt;p style=&#39;font-
size:12px;&#39;&gt;El reporte optimizado no contiene las dimensiones crudas
(Largo, Ancho, Alto) necesarias para dibujar el plano individual del
producto.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;&lt;br&gt;&quot;, unsafe_allow_html=True)
with tab_descargar:
st.write(f&quot;Genera un Excel completo con las **24 columnas WMS**
de los **{len(df_f)} SKUs** actuales.&quot;)
st.download_button(&quot;�� Descargar Reporte WMS Completo (Excel
Hojas)&quot;, data=generar_excel_descarga(st.session_state.df_original, df_f,
MAPA), file_name=&quot;Reporte_Paletizacion_Optimizado.xlsx&quot;,
mime=&quot;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&quot;)
with tab_alertas:
alertas = [{&quot;SKU&quot;: row[MAPA[&quot;sku&quot;]], &quot;Estado&quot;:
calcular_metricas_dinamicas(row, MAPA, modo)[&quot;Estado&quot;], &quot;Pallets&quot;:
calcular_metricas_dinamicas(row, MAPA, modo)[&quot;Pallets&quot;]} for _, row in
df_f.iterrows() if &quot;EXCEL&quot; in calcular_metricas_dinamicas(row, MAPA,
modo)[&quot;Estado&quot;] or &quot;PELIGRO&quot; in calcular_metricas_dinamicas(row, MAPA,
modo)[&quot;Estado&quot;] or &quot;REVISAR&quot; in calcular_metricas_dinamicas(row, MAPA,
modo)[&quot;Estado&quot;]]
if alertas: st.warning(f&quot;Se encontraron {len(alertas)} SKUs con
alertas.&quot;); st.dataframe(pd.DataFrame(alertas), use_container_width=True)
else: st.success(&quot;�� ¡Excelente! No hay alertas.&quot;)
with tab_datos: st.dataframe(df_f, use_container_width=True)
else: st.info(&quot;�� Sube tu archivo Excel para comenzar.&quot;)
def mostrar_layout():
st.title(&quot;��️ Diseñador de Layout de Bodega&quot;)
if st.session_state.df_resultados is None:
st.error(&quot;⚠️ Para usar el Layout, primero debes cargar el Excel en
el módulo &#39;Cubicadora WMS&#39;.&quot;)
return
MAPA = st.session_state.mapa_columnas
df_layout_orig =
preparar_df_layout(st.session_state.df_resultados.copy(), MAPA, &quot;EXCEL&quot;)
df_layout_opt =
preparar_df_layout(st.session_state.df_resultados.copy(), MAPA, &quot;OPTIMO&quot;)

dict_demanda = {&#39;Data Original&#39;: df_layout_orig, &#39;Data Optimizada&#39;:
df_layout_opt}
with st.expander(&quot;�� 1. Filtros de Demanda, Slotting y Racks&quot;
expanded=True):
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
st.session_state.fuente_datos = st.selectbox(&#39;�� Fuente d
Datos:&#39;, [&#39;Data Original&#39;, &#39;Data Optimizada&#39;], index=[&#39;Data Original&#39;,
&#39;Data Optimizada&#39;].index(st.session_state.fuente_datos))
df_fuente_curr = dict_demanda[st.session_state.fuente_datos]
if &#39;Bodega&#39; in df_fuente_curr.columns:
opc_bod_lay = sorted([str(x) for x in
df_fuente_curr[&#39;Bodega&#39;].unique() if pd.notna(x) and str(x) != &#39;nan&#39; and
str(x) != &#39;N/D&#39;])
if opc_bod_lay:
bod_default_lay = [b for b in
st.session_state.get(&#39;bodegas_sel&#39;, opc_bod_lay) if b in opc_bod_lay] or
opc_bod_lay
bod_lay_sel = st.multiselect(&quot;�� Filtrar por Bodega:&quot;
opc_bod_lay, default=bod_default_lay, key=&quot;ms_bodega_layout_page&quot;)
st.session_state.bodegas_sel = bod_lay_sel
with col_f2:
st.markdown(&quot;&lt;b style=&#39;font-size:12px; color:#34495e;&#39;&gt;�� Zona
ABC a procesar:&lt;/b&gt;&quot;, unsafe_allow_html=True)
cb_a, cb_b, cb_c = st.columns(3)
with cb_a: st.session_state.chk_a = st.checkbox(&#39;Zona A&#39;,
value=st.session_state.chk_a)
with cb_b: st.session_state.chk_b = st.checkbox(&#39;Zona B&#39;,
value=st.session_state.chk_b)
with cb_c: st.session_state.chk_c = st.checkbox(&#39;Zona C&#39;,
value=st.session_state.chk_c)
st.session_state.filtro_sublayout = st.text_input(&quot;�� Buscado
Masivo de SKUs (separar por comas, o &#39;TODOS&#39;):&quot;,
value=st.session_state.filtro_sublayout)
with col_f3:
st.session_state.pallets_viga = st.selectbox(&#39;Config. Viga
(Pallets por nivel):&#39;, [1, 2, 3],
index=[1,2,3].index(st.session_state.pallets_viga))
st.session_state.peso_max_pallet = st.number_input(&#39;Peso Máx.
Viga (kg):&#39;, value=st.session_state.peso_max_pallet)
with st.expander(&quot;�� 2. Infraestructura (Bodega, Pilares y Oficinas)&quot;
expanded=False):
c_inf1, c_inf2, c_inf3 = st.columns(3)
with c_inf1:
st.markdown(&quot;&lt;b style=&#39;font-size:12px;
color:#34495e;&#39;&gt;DIMENSIONES BODEGA&lt;/b&gt;&quot;, unsafe_allow_html=True)
st.session_state.l_bod = st.number_input(&#39;Largo Bodega (m):&#39;,
value=st.session_state.l_bod)
st.session_state.a_bod = st.number_input(&#39;Ancho Bodega (m):&#39;,
value=st.session_state.a_bod)

st.session_state.alt_bod = st.number_input(&#39;Alto Útil (m):&#39;,
value=st.session_state.alt_bod)
with c_inf2:
st.markdown(&quot;&lt;b style=&#39;font-size:12px; color:#34495e;&#39;&gt;MALLA DE
PILARES&lt;/b&gt;&quot;, unsafe_allow_html=True)
st.session_state.cant_pilares_x = st.number_input(&#39;Cant.
Pilares X (0=Auto):&#39;, value=st.session_state.cant_pilares_x)
st.session_state.cant_pilares_y = st.number_input(&#39;Cant.
Pilares Y (0=Auto):&#39;, value=st.session_state.cant_pilares_y)
st.session_state.dist_pilares_x = st.number_input(&#39;Dist.
Pilares X (m):&#39;, value=st.session_state.dist_pilares_x)
st.session_state.dist_pilares_y = st.number_input(&#39;Dist.
Pilares Y (m):&#39;, value=st.session_state.dist_pilares_y)
st.markdown(&quot;&lt;b style=&#39;font-size:11px; color:#7f8c8d; margin-
top:10px; display:block;&#39;&gt;DIMENSIONES DE PILARES&lt;/b&gt;&quot;,
unsafe_allow_html=True)
st.session_state.forma_pilar = st.selectbox(&#39;Formato Pilar:&#39;,
[&#39;Cuadrado / Rectangular&#39;, &#39;Circular&#39;], index=[&#39;Cuadrado / Rectangular&#39;,
&#39;Circular&#39;].index(st.session_state.forma_pilar))
if st.session_state.forma_pilar == &#39;Circular&#39;:
st.session_state.pilar_largo = st.number_input(&#39;Diámetro
Pilar (m):&#39;, value=st.session_state.pilar_largo)
st.session_state.pilar_ancho = st.session_state.pilar_largo
else:
cp1, cp2 = st.columns(2)
with cp1: st.session_state.pilar_largo =
st.number_input(&#39;Largo X (m):&#39;, value=st.session_state.pilar_largo)
with cp2: st.session_state.pilar_ancho =
st.number_input(&#39;Ancho Y (m):&#39;, value=st.session_state.pilar_ancho)
with c_inf3:
st.markdown(&quot;&lt;b style=&#39;font-size:12px; color:#34495e;&#39;&gt;ZONA DE
OFICINAS&lt;/b&gt;&quot;, unsafe_allow_html=True)
st.session_state.ofi_pos_x = st.number_input(&#39;Pos. Inicio X
(m):&#39;, value=st.session_state.ofi_pos_x)
st.session_state.ofi_pos_y = st.number_input(&#39;Pos. Inicio Y
(m):&#39;, value=st.session_state.ofi_pos_y)
st.session_state.ofi_largo = st.number_input(&#39;Largo X (m):&#39;,
value=st.session_state.ofi_largo)
st.session_state.ofi_ancho = st.number_input(&#39;Ancho Y (m):&#39;,
value=st.session_state.ofi_ancho)
st.session_state.ofi_alto = st.number_input(&#39;Alto Z (m):&#39;,
value=st.session_state.ofi_alto)
with st.expander(&quot;�� 3. Diseño de Tránsito y Operación&quot;
expanded=False):
c_op1, c_op2, c_op3 = st.columns(3)
with c_op1:
st.session_state.tipo_flujo = st.selectbox(&#39;Flujo:&#39;,
[&#39;Ninguno&#39;, &#39;Flujo en U&#39;, &#39;Flujo en I (Línea Recta)&#39;, &#39;Flujo en L&#39;],
index=[&#39;Ninguno&#39;, &#39;Flujo en U&#39;, &#39;Flujo en I (Línea Recta)&#39;, &#39;Flujo en
L&#39;].index(st.session_state.tipo_flujo))

st.session_state.ancho_porton = st.number_input(&#39;Ancho P. Auto
(m):&#39;, value=st.session_state.ancho_porton)
st.session_state.orientacion_rack =
st.selectbox(&#39;Orientación:&#39;, [&#39;Automática&#39;, &#39;Horizontal (X)&#39;, &#39;Vertical
(Y)&#39;], index=[&#39;Automática&#39;, &#39;Horizontal (X)&#39;, &#39;Vertical
(Y)&#39;].index(st.session_state.orientacion_rack))
st.session_state.alt_grua = st.number_input(&#39;Alt. Máx. Grúa
(m):&#39;, value=st.session_state.alt_grua)
with c_op2:
st.session_state.pasillo = st.number_input(&#39;Ancho Pasillo
(m):&#39;, value=st.session_state.pasillo)
st.session_state.cant_pas_trans = st.number_input(&#39;Pasillos
Trans.:&#39;, value=st.session_state.cant_pas_trans)
st.session_state.ancho_pas_trans = st.number_input(&#39;Ancho P.
Trans. (m):&#39;, value=st.session_state.ancho_pas_trans)
st.session_state.peso_max_grua = st.number_input(&#39;Cap. Grúa
(kg):&#39;, value=st.session_state.peso_max_grua)
with c_op3:
st.markdown(&quot;&lt;b style=&#39;font-size:12px; color:#34495e;&#39;&gt;ACCESOS
EXTRA&lt;/b&gt;&quot;, unsafe_allow_html=True)
p1, p2 = st.columns(2)
with p1:
st.session_state.cant_ptas_norte = st.number_input(&#39;Ptas
Norte:&#39;, value=st.session_state.cant_ptas_norte)
st.session_state.cant_ptas_sur = st.number_input(&#39;Ptas
Sur:&#39;, value=st.session_state.cant_ptas_sur)
st.session_state.cant_ptas_este = st.number_input(&#39;Ptas
Este:&#39;, value=st.session_state.cant_ptas_este)
st.session_state.cant_ptas_oeste = st.number_input(&#39;Ptas
Oeste:&#39;, value=st.session_state.cant_ptas_oeste)
with p2:
st.session_state.w_ptas_norte = st.number_input(&#39;Ancho N:&#39;,
value=st.session_state.w_ptas_norte)
st.session_state.w_ptas_sur = st.number_input(&#39;Ancho S:&#39;,
value=st.session_state.w_ptas_sur)
st.session_state.w_ptas_este = st.number_input(&#39;Ancho E:&#39;,
value=st.session_state.w_ptas_este)
st.session_state.w_ptas_oeste = st.number_input(&#39;Ancho O:&#39;,
value=st.session_state.w_ptas_oeste)
st.markdown(&quot;&lt;br&gt;&quot;, unsafe_allow_html=True)
c_btn1, c_btn2, c_btn3 = st.columns(3)
with c_btn1:
st.session_state.racks_en_pared = st.toggle(&quot;�� ¿Primer rack pegad
a la pared?&quot;, value=st.session_state.get(&#39;racks_en_pared&#39;, False))
st.session_state.consolidar_saldos = st.toggle(&quot;�� Consolida
Saldos (Pallets Mixtos)&quot;, value=st.session_state.get(&#39;consolidar_saldos&#39;,
False))
with c_btn2:
btn_crear_sel = st.button(&quot;�� Buscar / Crear Layout&quot;
type=&quot;primary&quot;, use_container_width=True)

btn_crear_gen = st.button(&quot;�� Mostrar Toda la Bodega&quot;
use_container_width=True)
with c_btn3:
btn_propuesta = st.button(&quot;�� Propuesta Espacial IA&quot;
use_container_width=True)
st.session_state.oficinas = [{&#39;x&#39;: st.session_state.ofi_pos_x, &#39;y&#39;:
st.session_state.ofi_pos_y, &#39;w&#39;: st.session_state.ofi_largo, &#39;d&#39;:
st.session_state.ofi_ancho, &#39;h&#39;: st.session_state.ofi_alto}] if
st.session_state.ofi_largo &gt; 0 else []
if btn_crear_sel:
raw = st.session_state.filtro_sublayout.strip()
skus_f = set(s.strip().upper() for s in re.split(r&#39;[,\s;]+&#39;, raw)
if s.strip())
if not skus_f or raw.upper() == &#39;TODOS&#39;:
st.session_state.modo_layout_eval = &#39;todos&#39;
st.warning(&quot;⚠️ No ingresaste ningún SKU específico. Se cargará
la bodega completa.&quot;)
else: st.session_state.modo_layout_eval = &#39;filtro&#39;
st.session_state.layout_generado = True
if btn_crear_gen:
st.session_state.filtro_sublayout = &quot;TODOS&quot;
st.session_state.layout_generado = True
st.session_state.modo_layout_eval = &#39;todos&#39;
if btn_propuesta:
with st.spinner(&quot;⏳ Calculando propuesta óptima con IA...&quot;):
clases_sel = []
if st.session_state.chk_a: clases_sel.append(&#39;A&#39;)
if st.session_state.chk_b: clases_sel.append(&#39;B&#39;)
if st.session_state.chk_c: clases_sel.append(&#39;C&#39;)
df_test_base = dict_demanda[st.session_state.fuente_datos]
df_test_base =
df_test_base[df_test_base[&#39;ABC&#39;].isin(clases_sel)]
if getattr(st.session_state, &#39;bodegas_sel&#39;, []):
df_test_base =
df_test_base[df_test_base[&#39;Bodega&#39;].isin(st.session_state.bodegas_sel)]
raw_f = st.session_state.filtro_sublayout.strip()
skus_f = set(s.strip().upper() for s in re.split(r&#39;[,\s;]+&#39;,
raw_f) if s.strip())
if skus_f and raw_f.upper() != &#39;TODOS&#39;: df_test_base =
df_test_base[df_test_base[&#39;SKU&#39;].astype(str).str.upper().isin(skus_f)]
if not df_test_base.empty:
escenarios = []
for o in [True, False]:
for v in [2, 3]:
res_ia = motor_calculo_layout(df_test_base, o, v,
st.session_state)
res_ia.update({&#39;is_vertical&#39;: o, &#39;pal_v&#39;: v})
escenarios.append(res_ia)
if escenarios:

mejor = max(escenarios, key=lambda x: x[&#39;diferencia&#39;])
st.session_state.orientacion_rack = &#39;Vertical (Y)&#39; if
mejor[&#39;is_vertical&#39;] else &#39;Horizontal (X)&#39;
st.session_state.pallets_viga = mejor[&#39;pal_v&#39;]
st.session_state.layout_generado = True
st.session_state.modo_layout_eval = &#39;todos&#39;
st.success(f&quot;�� IA Aplicada: Orientación {&#39;Vertical&#39; i
mejor[&#39;is_vertical&#39;] else &#39;Horizontal&#39;}, {mejor[&#39;pal_v&#39;]} vigas.&quot;)
st.rerun()
if st.session_state.layout_generado:
clases_sel = []
if st.session_state.chk_a: clases_sel.append(&#39;A&#39;)
if st.session_state.chk_b: clases_sel.append(&#39;B&#39;)
if st.session_state.chk_c: clases_sel.append(&#39;C&#39;)
df_activa = dict_demanda[st.session_state.fuente_datos]
df_activa = df_activa[df_activa[&#39;ABC&#39;].isin(clases_sel)]
if getattr(st.session_state, &#39;bodegas_sel&#39;, []):
df_activa =
df_activa[df_activa[&#39;Bodega&#39;].isin(st.session_state.bodegas_sel)]
raw = st.session_state.filtro_sublayout.strip()
if getattr(st.session_state, &#39;modo_layout_eval&#39;, &#39;todos&#39;) ==
&#39;filtro&#39;:
skus_buscados = set(s.strip().upper() for s in
re.split(r&#39;[,\s;]+&#39;, raw) if s.strip())
if skus_buscados and raw.upper() != &#39;TODOS&#39;: df_activa =
df_activa[df_activa[&#39;SKU&#39;].astype(str).str.upper().isin(skus_buscados)]
is_vert = (&#39;Vertical&#39; in st.session_state.orientacion_rack) if
&#39;Automática&#39; not in st.session_state.orientacion_rack else
(st.session_state.tipo_flujo in [&#39;Flujo en U&#39;, &#39;Flujo en I (Línea Recta)&#39;])
res_box = motor_calculo_layout(df_activa, is_vert,
st.session_state.pallets_viga, st.session_state)
# APLICAR MOVIMIENTOS INTERNOS GUARDADOS
for tarea in st.session_state.get(&#39;tareas_movimiento&#39;, []):
ori_id = tarea[&quot;Origen&quot;]
des_id = tarea[&quot;Destino&quot;]
ori_slot = next((s for s in res_box[&#39;almacen&#39;] if
s[&#39;id_posicion&#39;] == ori_id), None)
des_slot = next((s for s in res_box[&#39;almacen&#39;] if
s[&#39;id_posicion&#39;] == des_id), None)
if ori_slot and des_slot and ori_slot[&#39;ocupado&#39;] and
des_slot[&#39;ocupado&#39;] and ori_slot[&#39;sku&#39;] == des_slot[&#39;sku&#39;]:
des_slot[&#39;unidades&#39;] += tarea[&#39;Unidades Movidas&#39;]
des_slot[&#39;pct&#39;] = des_slot[&#39;unidades&#39;] /
des_slot[&#39;cap_maxima&#39;]
des_slot[&#39;es_saldo&#39;] = des_slot[&#39;unidades&#39;] &lt;
des_slot[&#39;cap_maxima&#39;]

ori_slot[&#39;ocupado&#39;] = False
ori_slot[&#39;sku&#39;] = &quot;&quot;
ori_slot[&#39;unidades&#39;] = 0
ori_slot[&#39;es_saldo&#39;] = False
st.session_state.res_layout_actual = res_box
dif = res_box[&#39;diferencia&#39;]
s_bg = &quot;#0f172a&quot;
s_color = &quot;#10b981&quot; if dif &gt;= 0 else &quot;#ef4444&quot;
msg_txt = f&quot;✔️ ¡ÉXITO! Caben todos y sobran {dif:,}.&quot; if dif &gt;= 0
else f&quot;⚠️ ¡ALERTA! Te faltan {abs(dif):,} posiciones.&quot;
html_eval = clean_html(f&quot;&quot;&quot;
&lt;div style=&quot;font-family: &#39;Segoe UI&#39;, system-ui, sans-serif;
background: #0f172a; border-radius: 12px 12px 0 0; padding: 18px 25px;
display: flex; justify-content: space-between; align-items: center; margin-
top: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);&quot;&gt;
&lt;div&gt;&lt;h3 style=&quot;color: #ffffff; margin: 0; font-size: 20px;
font-weight: 800; letter-spacing: -0.5px;&quot;&gt;��️ Evaluación de Capacidad de
Layout&lt;/h3&gt;&lt;p style=&quot;color: #94a3b8; margin: 3px 0 0 0; font-size:
12px;&quot;&gt;Zonas Evaluadas: &lt;b
style=&quot;color:#38bdf8;&quot;&gt;{&#39;,&#39;.join(clases_sel)}&lt;/b&gt;&lt;/p&gt;&lt;/div&gt;
&lt;div&gt;&lt;span style=&quot;background: {&#39;#ecfdf5&#39; if dif &gt;= 0 else
&#39;#fef2f2&#39;}; color: {&#39;#065f46&#39; if dif &gt;= 0 else &#39;#991b1b&#39;}; padding: 6px
14px; border-radius: 20px; font-size: 11px; font-weight: 800; border: 1px
solid {&#39;#10b981&#39; if dif &gt;= 0 else &#39;#ef4444&#39;};&quot;&gt;{msg_txt}&lt;/span&gt;&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;background: #f8fafc; border: 1px solid #e2e8f0; border-
top: none; border-radius: 0 0 12px 12px; padding: 20px 25px; margin-bottom:
20px;&quot;&gt;
&lt;div style=&quot;display: grid; grid-template-columns: repeat(5,
1fr); gap: 15px;&quot;&gt;
&lt;div style=&quot;background:#ffffff; border:1px solid #e2e8f0;
border-left:4px solid #3b82f6; border-radius:8px; padding:15px; text-
align:center;&quot;&gt;
&lt;div style=&quot;font-size:10px; font-weight:800;
color:#64748b; letter-spacing:0.5px; margin-bottom:4px;&quot;&gt;RACKS EN
PLANTA&lt;/div&gt;
&lt;div style=&quot;font-size:24px; font-weight:800;
color:#0f172a;&quot;&gt;{res_box[&#39;modulos&#39;]:,}&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;background:#ffffff; border:1px solid #e2e8f0;
border-left:4px solid #10b981; border-radius:8px; padding:15px; text-
align:center;&quot;&gt;
&lt;div style=&quot;font-size:10px; font-weight:800;
color:#64748b; letter-spacing:0.5px; margin-bottom:4px;&quot;&gt;NIVELES EN
ALTURA&lt;/div&gt;
&lt;div style=&quot;font-size:24px; font-weight:800;
color:#0f172a;&quot;&gt;{res_box[&#39;niveles&#39;]}&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;background:#f5f3ff; border:1px solid #ddd6fe;

border-left:4px solid #6366f1; border-radius:8px; padding:15px; text-
align:center;&quot;&gt;
&lt;div style=&quot;font-size:10px; font-weight:800;
color:#4338ca; letter-spacing:0.5px; margin-bottom:4px;&quot;&gt;CAPACIDAD
TOTAL&lt;/div&gt;
&lt;div style=&quot;font-size:24px; font-weight:800;
color:#4f46e5;&quot;&gt;{res_box[&#39;capacidad&#39;]:,}&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;background:#f5f3ff; border:1px solid #ddd6fe;
border-left:4px solid #8b5cf6; border-radius:8px; padding:15px; text-
align:center;&quot;&gt;
&lt;div style=&quot;font-size:10px; font-weight:800;
color:#5b21b6; letter-spacing:0.5px; margin-bottom:4px;&quot;&gt;ALMACENADOS
3D&lt;/div&gt;
&lt;div style=&quot;font-size:24px; font-weight:800;
color:#7c3aed;&quot;&gt;{res_box[&#39;pallets_ubicados_totales&#39;]:,}&lt;/div&gt;
&lt;/div&gt;
&lt;div style=&quot;background:{&#39;#fef2f2&#39; if dif &lt; 0 else
&#39;#ffffff&#39;}; border:1px solid {&#39;#fecaca&#39; if dif &lt; 0 else &#39;#e2e8f0&#39;}; border-
left:4px solid {&#39;#ef4444&#39; if dif &lt; 0 else &#39;#f59e0b&#39;}; border-radius:8px;
padding:15px; text-align:center;&quot;&gt;
&lt;div style=&quot;font-size:10px; font-weight:800;
color:{&#39;#991b1b&#39; if dif &lt; 0 else &#39;#b45309&#39;}; letter-spacing:0.5px; margin-
bottom:4px;&quot;&gt;DEMANDA EVALUADA&lt;/div&gt;
&lt;div style=&quot;font-size:24px; font-weight:800;
color:{&#39;#dc2626&#39; if dif &lt; 0 else &#39;#d97706&#39;};&quot;&gt;{res_box[&#39;demanda&#39;]:,}&lt;/div&gt;
&lt;/div&gt;
&lt;/div&gt;
&lt;/div&gt;
&quot;&quot;&quot;)
st.markdown(html_eval, unsafe_allow_html=True)
if st.session_state.layout_generado and
st.session_state.res_layout_actual is not None:
res = st.session_state.res_layout_actual
anim_info = st.session_state.get(&#39;ultima_animacion&#39;, {&quot;activa&quot;:
False})
if anim_info.get(&quot;activa&quot;):
st.success(f&quot;�� Animación 3D Pendiente: Se moverán cajas de
SKU **{anim_info.get(&#39;sku&#39;)}** para consolidar. Activa el Gemelo Digital
abajo para visualizar.&quot;)
if st.button(&quot;Limpiar Animación (Detener)&quot;,
use_container_width=True):
st.session_state.ultima_animacion = {&quot;activa&quot;: False}
st.rerun()
col_exp1, col_exp2 = st.columns([1, 1])
with col_exp1: st.session_state.modo_vista_color = st.selectbox(&quot;�
Zonificación de Colores Racks:&quot;, [&#39;3 Zonas (ABC)&#39;, &#39;9 Zonas (ABC-XYZ)&#39;],
index=[&#39;3 Zonas (ABC)&#39;, &#39;9 Zonas (ABC-
XYZ)&#39;].index(st.session_state.modo_vista_color))

with col_exp2:
st.markdown(&quot;&lt;div style=&#39;height:28px;&#39;&gt;&lt;/div&gt;&quot;,
unsafe_allow_html=True)
st.download_button(&quot;�� Exportar Ubicaciones WMS (Excel
Hojas)&quot;, data=generar_wms_excel(st.session_state.df_resultados,
res[&#39;almacen&#39;], st.session_state.mapa_columnas),
file_name=&quot;WMS_Ubicaciones_Bodega.xlsx&quot;,
mime=&quot;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&quot;,
use_container_width=True)
l_m, a_m, w_puerta, flujo = st.session_state.l_bod,
st.session_state.a_bod, st.session_state.ancho_porton,
st.session_state.tipo_flujo
fig_2d = go.Figure()
fig_2d.add_shape(type=&quot;rect&quot;, x0=0, y0=0, x1=l_m, y1=a_m,
line=dict(color=&quot;#2c3e50&quot;, width=4), fillcolor=&quot;#fafafa&quot;)
pp_d, l_modulo = 1.2, (1.2 * st.session_state.pallets_viga) + (0.10
* (st.session_state.pallets_viga + 1)) + 0.10
dict_color_abc = {&#39;A&#39;: &#39;#e74c3c&#39;, &#39;B&#39;: &#39;#f39c12&#39;, &#39;C&#39;: &#39;#3498db&#39;}
dict_color_abcxyz = {&#39;AX&#39;: &#39;#900C3F&#39;, &#39;AY&#39;: &#39;#C70039&#39;, &#39;AZ&#39;:
&#39;#FF5733&#39;, &#39;BX&#39;: &#39;#E67E22&#39;, &#39;BY&#39;: &#39;#F39C12&#39;, &#39;BZ&#39;: &#39;#F1C40F&#39;, &#39;CX&#39;:
&#39;#2E86C1&#39;, &#39;CY&#39;: &#39;#3498DB&#39;, &#39;CZ&#39;: &#39;#85C1E9&#39;}
skus_b = set(s.strip().upper() for s in re.split(r&#39;[,\s;]+&#39;,
st.session_state.filtro_sublayout.strip()) if s.strip()) if
getattr(st.session_state, &#39;modo_layout_eval&#39;, &#39;todos&#39;) == &#39;filtro&#39; else
set()
if skus_b and &#39;TODOS&#39; in skus_b: skus_b = set()
path_free, path_block, path_pil, path_destacado, path_apagado,
path_mixto = [], [], [], [], [], []
p_racks = {k: [] for k in list(dict_color_abc.keys()) +
list(dict_color_abcxyz.keys())}
modulos_ocupados = set((s[&#39;x&#39;], s[&#39;y&#39;]) for s in res[&#39;almacen&#39;] if
s[&#39;ocupado&#39;])
modulos_destacados = set((s[&#39;x&#39;], s[&#39;y&#39;]) for s in res[&#39;almacen&#39;]
if s[&#39;ocupado&#39;] and s[&#39;sku&#39;] in skus_b)
modulos_mixtos = set((s[&#39;x&#39;], s[&#39;y&#39;]) for s in res[&#39;almacen&#39;] if
s[&#39;ocupado&#39;] and s.get(&#39;es_mixto&#39;, False))
for mod in res[&#39;modulos_list&#39;]:
x_pos, y_rack = mod[&#39;x&#39;], mod[&#39;y&#39;]
rx0, ry0, rx1, ry1 = (y_rack, x_pos, y_rack+pp_d,
x_pos+l_modulo) if res[&#39;is_vertical&#39;] else (x_pos, y_rack, x_pos+l_modulo,
y_rack+pp_d)
path = f&quot;M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1} L {rx0}
{ry1} Z&quot;
if mod[&#39;bloqueado&#39;]: path_block.append(path)
elif (x_pos, y_rack) in modulos_ocupados:

if skus_b:
if (x_pos, y_rack) in modulos_destacados:
path_destacado.append(path)
else: path_apagado.append(path)
elif (x_pos, y_rack) in modulos_mixtos:
path_mixto.append(path)
else:
abcs_aqui = [s[&#39;abc_xyz&#39;] if &#39;9 Zonas&#39; in
st.session_state.modo_vista_color else s[&#39;abc&#39;] for s in res[&#39;almacen&#39;] if
s[&#39;x&#39;]==x_pos and s[&#39;y&#39;]==y_rack and s[&#39;ocupado&#39;]]
clase = min(abcs_aqui) if abcs_aqui else None
if clase and clase in p_racks:
p_racks[clase].append(path)
else: path_free.append(path)
else: path_free.append(path)
for px, py in res[&#39;pilares_reales&#39;]:
if res.get(&#39;forma_pilar&#39;) == &#39;Circular&#39;:
r_p = res[&#39;pilar_largo&#39;] / 2.0
fig_2d.add_shape(type=&quot;circle&quot;, x0=px-r_p, y0=py-r_p,
x1=px+r_p, y1=py+r_p, fillcolor=&quot;#e74c3c&quot;, line=dict(color=&quot;#c0392b&quot;,
width=1.5))
else:
lx = res.get(&#39;pilar_largo&#39;, 0.5) / 2.0
ly = res.get(&#39;pilar_ancho&#39;, 0.5) / 2.0
rx0, ry0, rx1, ry1 = px-lx, py-ly, px+lx, py+ly
path_pil.append(f&quot;M {rx0} {ry0} L {rx1} {ry0} L {rx1} {ry1}
L {rx0} {ry1} Z&quot;)
if path_free: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(path_free), fillcolor=&quot;#ecf0f1&quot;, line=dict(color=&quot;#bdc3c7&quot;,
width=1))
if path_block: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(path_block), fillcolor=&quot;#95a5a6&quot;, line=dict(color=&quot;#7f8c8d&quot;,
width=1))
if path_apagado: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(path_apagado), fillcolor=&quot;#ecf0f1&quot;, line=dict(color=&quot;#bdc3c7&quot;,
width=1))
if path_destacado: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(path_destacado), fillcolor=&quot;#2ecc71&quot;, line=dict(color=&quot;#27ae60&quot;,
width=2))
if path_mixto: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(path_mixto), fillcolor=&quot;#8b5cf6&quot;, line=dict(color=&quot;#6d28d9&quot;,
width=1))
if not skus_b:
for c_k, color in (dict_color_abcxyz.items() if &#39;9 Zonas&#39; in
st.session_state.modo_vista_color else dict_color_abc.items()):
if p_racks[c_k]: fig_2d.add_shape(type=&quot;path&quot;, path=&quot;
&quot;.join(p_racks[c_k]), fillcolor=color, line=dict(color=&quot;#2c3e50&quot;, width=1))

if path_pil: fig_2d.add_shape(type=&quot;path&quot;, path=&quot; &quot;.join(path_pil),
fillcolor=&quot;#e74c3c&quot;, line=dict(color=&quot;#c0392b&quot;, width=1.5))
for st_z in res[&#39;staging&#39;]: fig_2d.add_shape(type=&quot;rect&quot;,
x0=st_z[&#39;x1&#39;], y0=st_z[&#39;y1&#39;], x1=st_z[&#39;x2&#39;], y1=st_z[&#39;y2&#39;],
fillcolor=&quot;rgba(241, 196, 15, 0.4)&quot;, line=dict(color=&quot;#f39c12&quot;, width=2))
for ofi in res[&#39;oficinas&#39;]: fig_2d.add_shape(type=&quot;rect&quot;,
x0=ofi[&#39;x&#39;], y0=ofi[&#39;y&#39;], x1=ofi[&#39;x&#39;]+ofi[&#39;w&#39;], y1=ofi[&#39;y&#39;]+ofi[&#39;d&#39;],
fillcolor=&quot;#bdc3c7&quot;, line=dict(color=&quot;#7f8c8d&quot;, width=2))
puertas = []
if w_puerta &gt; 0 and flujo != &#39;Ninguno&#39;:
if &#39;Flujo en U&#39; in flujo: puertas.extend([{&#39;pared&#39;: &#39;S&#39;, &#39;pos&#39;:
(l_m*0.25)-(w_puerta/2), &#39;w&#39;: w_puerta, &#39;label&#39;: &#39;IN&#39;}, {&#39;pared&#39;: &#39;S&#39;,
&#39;pos&#39;: (l_m*0.75)-(w_puerta/2), &#39;w&#39;: w_puerta, &#39;label&#39;: &#39;OUT&#39;}])
elif &#39;Flujo en I&#39; in flujo: puertas.extend([{&#39;pared&#39;: &#39;S&#39;,
&#39;pos&#39;: (l_m/2)-(w_puerta/2), &#39;w&#39;: w_puerta, &#39;label&#39;: &#39;IN&#39;}, {&#39;pared&#39;: &#39;N&#39;,
&#39;pos&#39;: (l_m/2)-(w_puerta/2), &#39;w&#39;: w_puerta, &#39;label&#39;: &#39;OUT&#39;}])
elif &#39;Flujo en L&#39; in flujo: puertas.extend([{&#39;pared&#39;: &#39;S&#39;,
&#39;pos&#39;: max(1, (l_m*0.15)-(w_puerta/2)), &#39;w&#39;: w_puerta, &#39;label&#39;: &#39;IN&#39;},
{&#39;pared&#39;: &#39;E&#39;, &#39;pos&#39;: max(1, (a_m*0.85)-(w_puerta/2)), &#39;w&#39;: w_puerta,
&#39;label&#39;: &#39;OUT&#39;}])
for p in puertas:
pared, pos, w, label = p[&#39;pared&#39;], p[&#39;pos&#39;], p[&#39;w&#39;], p[&#39;label&#39;]
if pared == &#39;S&#39;: x0, y0, x1, y1, ax, ay = pos, 0, pos+w, 1.5,
pos+w/2, 0.75
elif pared == &#39;N&#39;: x0, y0, x1, y1, ax, ay = pos, a_m-1.5,
pos+w, a_m, pos+w/2, a_m-0.75
elif pared == &#39;E&#39;: x0, y0, x1, y1, ax, ay = l_m-1.5, pos, l_m,
pos+w, l_m-0.75, pos+w/2
elif pared == &#39;O&#39;: x0, y0, x1, y1, ax, ay = 0, pos, 1.5, pos+w,
0.75, pos+w/2
fig_2d.add_shape(type=&quot;rect&quot;, x0=x0, y0=y0, x1=x1, y1=y1,
fillcolor=&quot;#f1c40f&quot;, line=dict(color=&quot;#f39c12&quot;, width=2))
fig_2d.add_annotation(x=ax, y=ay, text=f&quot;&lt;b&gt;{label}&lt;/b&gt;&quot;,
showarrow=False, font=dict(size=11, color=&quot;black&quot;))
fig_2d.update_layout(title=&quot;Plano CAD 2D del Centro de Distribución
(Zonificación Racks)&quot;, xaxis=dict(title=&quot;Largo (m)&quot;, range=[-3, l_m + 3],
zeroline=False), yaxis=dict(title=&quot;Ancho (m)&quot;, range=[-3, a_m + 3],
zeroline=False, scaleanchor=&quot;x&quot;, scaleratio=1), height=650,
margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor=&quot;#ffffff&quot;)
st.plotly_chart(fig_2d, use_container_width=True)
st.markdown(&quot;&lt;hr&gt;&quot;, unsafe_allow_html=True)
mostrar_3d_layout = st.toggle(&quot;�� Cargar Gemelo Digital 3D H
(Three.js WebGL)&quot;)
if mostrar_3d_layout:
with st.spinner(&quot;Construyendo Mallas 3D de la Bodega...&quot;):
datos_bodega = {

&quot;largo&quot;: l_m, &quot;ancho&quot;: a_m, &quot;alto&quot;:
st.session_state.alt_bod, &quot;is_vertical&quot;: res[&#39;is_vertical&#39;],
&quot;l_modulo&quot;: res[&quot;l_modulo&quot;], &quot;pp_d&quot;: res[&quot;pp_d&quot;],
&quot;t_marco&quot;: res[&quot;t_marco&quot;],
&quot;niveles&quot;: res[&quot;niveles&quot;], &quot;alt_nivel_viga&quot;:
res[&quot;alt_nivel_viga&quot;], &quot;viga_h&quot;: res[&quot;viga_h&quot;], &quot;ap_w&quot;: res[&quot;ap_w&quot;],
&quot;slots&quot;: [{&quot;id&quot;: s[&quot;id_posicion&quot;], &quot;x&quot;: s[&quot;x_pal&quot;],
&quot;y&quot;: s[&quot;y&quot;], &quot;z&quot;: s[&quot;z&quot;], &quot;sku&quot;: s.get(&quot;sku&quot;, &quot;&quot;), &quot;abc&quot;: s.get(&quot;abc&quot;,
&quot;C&quot;), &quot;abc_xyz&quot;: s.get(&quot;abc_xyz&quot;, &quot;CZ&quot;), &quot;ocupado&quot;: s[&quot;ocupado&quot;],
&quot;es_cilindro&quot;: s.get(&quot;es_cilindro&quot;, False), &quot;es_saldo&quot;: s.get(&quot;es_saldo&quot;,
False), &quot;es_mixto&quot;: s.get(&quot;es_mixto&quot;, False), &quot;alt_p&quot;: s.get(&quot;alt_p&quot;, 1.2),
&quot;destacado&quot;: True if not skus_b else (s.get(&quot;sku&quot;, &quot;&quot;).upper() in skus_b),
&quot;letra&quot;: s[&quot;letra_pasillo&quot;], &quot;modulo&quot;: s[&quot;modulo&quot;], &quot;nivel&quot;: s[&quot;nivel&quot;],
&quot;unidades&quot;: s.get(&quot;unidades&quot;, 0), &quot;cap_maxima&quot;: s.get(&quot;cap_maxima&quot;, 0)} for
s in res[&quot;almacen&quot;]],
&quot;racks&quot;: [{&quot;x&quot;: m[&quot;x&quot;], &quot;y&quot;: m[&quot;y&quot;], &quot;bloqueado&quot;:
m[&quot;bloqueado&quot;]} for m in res[&quot;modulos_list&quot;]],
&quot;pilares&quot;: res[&quot;pilares_reales&quot;], &quot;oficinas&quot;:
res[&quot;oficinas&quot;], &quot;staging&quot;: res[&quot;staging&quot;], &quot;puertas&quot;: puertas,
&quot;hay_filtro&quot;: len(skus_b) &gt; 0 if skus_b else False,
&quot;forma_pilar&quot;: res.get(&quot;forma_pilar&quot;, &quot;Cuadrado /
Rectangular&quot;),
&quot;pilar_largo&quot;: res.get(&quot;pilar_largo&quot;, 0.5),
&quot;pilar_ancho&quot;: res.get(&quot;pilar_ancho&quot;, 0.5),
&quot;animacion&quot;: anim_info
}
json_data = json.dumps(datos_bodega)
html_template = &quot;&quot;&quot;
&lt;!DOCTYPE html&gt;
&lt;html&gt;
&lt;head&gt;
&lt;style&gt;
body { margin: 0; overflow: hidden; background-
color: #0f172a; font-family: system-ui, -apple-system, sans-serif; }
#canvas-container { width: 100vw; height: 100vh;
position: relative; }
#info-overlay { position: absolute; top: 15px;
left: 15px; color: white; background: rgba(15, 23, 42, 0.88); padding: 12px
18px; border-radius: 8px; border: 1px solid #334155; font-size: 13px;
pointer-events: none; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
#tooltip { position: absolute; background: rgba(15,
23, 42, 0.95); color: #fff; padding: 12px; border-radius: 6px; pointer-
events: none; display: none; z-index: 1000; font-size: 13px; border: 1px
solid #38bdf8; box-shadow: 0 6px 12px rgba(0,0,0,0.4); line-height: 1.5;
min-width: 180px; }
&lt;/style&gt;
&lt;script
src=&quot;https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js&quot;&gt;&lt;/s
cript&gt;
&lt;script

src=&quot;https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitC
ontrols.js&quot;&gt;&lt;/script&gt;
&lt;/head&gt;
&lt;body&gt;
&lt;div id=&quot;info-overlay&quot;&gt;
✨ &lt;b&gt;Gemelo Digital HD Completo (WebGL)&lt;/b&gt;&lt;br&gt;
�� &lt;i&gt;Mueve el ratón sobre un pallet para ver su
datos.&lt;/i&gt;&lt;br&gt;
�� &lt;i&gt;Clic Izq: Rotar 360° | Clic Der: Desplazar
Rueda: Zoom&lt;/i&gt;
&lt;/div&gt;
&lt;div id=&quot;canvas-container&quot;&gt;
&lt;div id=&quot;tooltip&quot;&gt;&lt;/div&gt;
&lt;/div&gt;
&lt;script&gt;
const data = __DATOS_JSON__;
const modoVista = &quot;__MODO_VISTA__&quot;;
const container = document.getElementById(&#39;canvas-
container&#39;);
const tooltip = document.getElementById(&#39;tooltip&#39;);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f172a);
scene.fog = new THREE.FogExp2(0x0f172a, 0.008);
const camera = new THREE.PerspectiveCamera(45,
window.innerWidth / 850, 0.5, 1000);
const maxDim = Math.max(data.largo, data.ancho);
camera.position.set(data.largo / 2, maxDim * 0.9,
data.ancho * 0.8);
const renderer = new THREE.WebGLRenderer({
antialias: true });
renderer.setSize(window.innerWidth, 850);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
container.appendChild(renderer.domElement);
const controls = new THREE.OrbitControls(camera,
renderer.domElement);
controls.target.set(data.largo / 2, 0, -data.ancho
/ 2);
controls.update();
window.addEventListener(&#39;resize&#39;, () =&gt; {
camera.aspect = window.innerWidth /
window.innerHeight;
camera.updateProjectionMatrix();
renderer.setSize(window.innerWidth,
window.innerHeight);
});

const ambientLight = new
THREE.AmbientLight(0xffffff, 0.65);
scene.add(ambientLight);
const dirLight = new
THREE.DirectionalLight(0xffffff, 0.85);
dirLight.position.set(data.largo / 2, 40, -
data.ancho / 2);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);
const floorGeo = new THREE.PlaneGeometry(data.largo
+ 20, data.ancho + 20);
const floorMat = new THREE.MeshStandardMaterial({
color: 0x1e293b, roughness: 0.4, metalness: 0.2 });
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI / 2;
floor.position.set(data.largo / 2, -0.02, -
data.ancho / 2);
floor.receiveShadow = true;
scene.add(floor);
const grid = new
THREE.GridHelper(Math.max(data.largo, data.ancho) + 20, 50, 0x38bdf8,
0x334155);
grid.position.set(data.largo / 2, 0, -data.ancho /
2);
scene.add(grid);
const linePoints = [
new THREE.Vector3(0, 0.05, 0), new
THREE.Vector3(data.largo, 0.05, 0),
new THREE.Vector3(data.largo, 0.05, -
data.ancho), new THREE.Vector3(0, 0.05, -data.ancho),
new THREE.Vector3(0, 0.05, 0)
];
const lineGeo = new
THREE.BufferGeometry().setFromPoints(linePoints);
const lineMat = new THREE.LineBasicMaterial({
color: 0xeab308, linewidth: 3 });
scene.add(new THREE.Line(lineGeo, lineMat));
const pilMat = new THREE.MeshStandardMaterial({
color: 0xdc2626, roughness: 0.3 });
data.pilares.forEach(p =&gt; {
if (p[0] &lt;= data.largo &amp;&amp; p[1] &lt;= data.ancho) {
let mesh;
if (data.forma_pilar === &#39;Circular&#39;) {
mesh = new THREE.Mesh(new

THREE.CylinderGeometry(data.pilar_largo/2, data.pilar_largo/2, data.alto,
16), pilMat);
} else {
mesh = new THREE.Mesh(new
THREE.BoxGeometry(data.pilar_largo, data.alto, data.pilar_ancho), pilMat);
}
mesh.position.set(p[0], data.alto/2, -
p[1]);
mesh.castShadow = true;
scene.add(mesh);
}
});
function createFloorLabel(text, w, d, textColor) {
const canvas =
document.createElement(&#39;canvas&#39;);
canvas.width = 512; canvas.height = 128;
const ctx = canvas.getContext(&#39;2d&#39;);
ctx.font = &#39;900 65px &quot;Segoe UI&quot;, system-ui,
sans-serif&#39;;
ctx.fillStyle = textColor;
ctx.textAlign = &#39;center&#39;;
ctx.textBaseline = &#39;middle&#39;;
ctx.fillText(text, canvas.width / 2,
canvas.height / 2);
const tex = new THREE.CanvasTexture(canvas);
const mat = new THREE.MeshBasicMaterial({ map:
tex, transparent: true, depthWrite: false });
let planeW = w * 0.9; let planeH = planeW / 4;
if (planeH &gt; d * 0.9) { planeH = d * 0.9;
planeW = planeH * 4; }
const mesh = new THREE.Mesh(new
THREE.PlaneGeometry(planeW, planeH), mat);
mesh.rotation.x = -Math.PI / 2;
return mesh;
}
const offMat = new THREE.MeshStandardMaterial({
color: 0x64748b, transparent: true, opacity: 0.75, roughness: 0.1,
metalness: 0.5 });
data.oficinas.forEach(o =&gt; {
const h = o.h || 3.5;
const mesh = new THREE.Mesh(new
THREE.BoxGeometry(o.w, h, o.d), offMat);
mesh.position.set(o.x + o.w/2, h/2, -(o.y +
o.d/2));
mesh.castShadow = true;
scene.add(mesh);
const lbl = createFloorLabel(&quot;OFICINA&quot;, o.w,
o.d, &quot;#ffffff&quot;);
lbl.position.set(o.x + o.w/2, h + 0.05, -(o.y +
o.d/2));

scene.add(lbl);
});
const stMat = new THREE.MeshBasicMaterial({ color:
0xf59e0b, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
data.staging.forEach(s =&gt; {
const w = s.x2 - s.x1; const d = s.y2 - s.y1;
const mesh = new THREE.Mesh(new
THREE.PlaneGeometry(w, d), stMat);
mesh.rotation.x = -Math.PI / 2;
mesh.position.set(s.x1 + w/2, 0.03, -(s.y1 +
d/2));
scene.add(mesh);
const lbl = createFloorLabel(&quot;STAGING&quot;, w, d,
&quot;#b45309&quot;);
lbl.position.set(s.x1 + w/2, 0.05, -(s.y1 +
d/2));
scene.add(lbl);
});
const doorMat = new THREE.MeshStandardMaterial({
color: 0xf59e0b, roughness: 0.2 });
data.puertas.forEach(p =&gt; {
const w = p.w; const h = 4.5; let x0=0, y0=0,
dx=0.3, dy=0.3;
if (p.pared === &#39;S&#39;) { x0 = p.pos + w/2; y0 =
0.15; dx = w; dy = 0.3; }
else if (p.pared === &#39;N&#39;) { x0 = p.pos + w/2;
y0 = data.ancho - 0.15; dx = w; dy = 0.3; }
else if (p.pared === &#39;E&#39;) { x0 = data.largo -
0.15; y0 = p.pos + w/2; dx = 0.3; dy = w; }
else if (p.pared === &#39;O&#39;) { x0 = 0.15; y0 =
p.pos + w/2; dx = 0.3; dy = w; }
const frameMesh = new THREE.Mesh(new
THREE.BoxGeometry(dx, h, dy), doorMat);
frameMesh.position.set(x0, h/2, -y0);
scene.add(frameMesh);
});
const rackPostMat = new
THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3, metalness:
0.8 });
const beamMat = new THREE.MeshStandardMaterial({
color: 0xe67e22, roughness: 0.4, metalness: 0.6 });
const lm = data.l_modulo; const pd = data.pp_d;
const hr = Math.max(data.niveles * data.alt_nivel_viga,
data.alt_nivel_viga);
data.racks.forEach(r =&gt; {
const rx = r.x; const ry = r.y; const isV =
data.is_vertical;

const postGeo = new THREE.BoxGeometry(0.08, hr,
0.08);
const coords = isV ? [
[ry, rx], [ry + pd - 0.08, rx],
[ry, rx + lm - 0.08], [ry + pd - 0.08, rx +
lm - 0.08]
] : [
[rx, ry], [rx + lm - 0.08, ry],
[rx, ry + pd - 0.08], [rx + lm - 0.08, ry +
pd - 0.08]
];
coords.forEach(pt =&gt; {
const post = new THREE.Mesh(postGeo,
rackPostMat);
post.position.set(pt[0] + 0.04, hr / 2, -
(pt[1] + 0.04));
post.castShadow = true;
scene.add(post);
});
for (let n = 1; n &lt;= data.niveles; n++) {
const zv = n * data.alt_nivel_viga -
data.viga_h;
if (!isV) {
const b1 = new THREE.Mesh(new
THREE.BoxGeometry(lm - 0.16, data.viga_h, 0.05), beamMat);
b1.position.set(rx + lm / 2, zv, -(ry +
0.025));
scene.add(b1);
const b2 = new THREE.Mesh(new
THREE.BoxGeometry(lm - 0.16, data.viga_h, 0.05), beamMat);
b2.position.set(rx + lm / 2, zv, -(ry +
pd - 0.025));
scene.add(b2);
} else {
const b1 = new THREE.Mesh(new
THREE.BoxGeometry(0.05, data.viga_h, lm - 0.16), beamMat);
b1.position.set(ry + 0.025, zv, -(rx +
lm / 2));
scene.add(b1);
const b2 = new THREE.Mesh(new
THREE.BoxGeometry(0.05, data.viga_h, lm - 0.16), beamMat);
b2.position.set(ry + pd - 0.025, zv, -
(rx + lm / 2));
scene.add(b2);
}
}
});
let meshesInteractivos = [];

const colMapABC = { &#39;A&#39;: 0xef4444, &#39;B&#39;: 0xf59e0b,
&#39;C&#39;: 0x3b82f6 };
const colMapXYZ = {
&#39;AX&#39;: 0x900C3F, &#39;AY&#39;: 0xC70039, &#39;AZ&#39;: 0xFF5733,
&#39;BX&#39;: 0xE67E22, &#39;BY&#39;: 0xF39C12, &#39;BZ&#39;: 0xF1C40F,
&#39;CX&#39;: 0x2E86C1, &#39;CY&#39;: 0x3498DB, &#39;CZ&#39;: 0x85C1E9
};
data.slots.forEach(s =&gt; {
if (s.ocupado) {
let colHex = colMapABC[s.abc] || 0x3b82f6;
if (modoVista === &#39;9 Zonas (ABC-XYZ)&#39;) {
colHex = colMapXYZ[s.abc_xyz] ||
colHex;
}
let opacidad = 1.0;
let colorFinal = colHex;
if (s.es_mixto) {
colorFinal = 0x8b5cf6; // Morado para
Pallets Mixtos
}
if (data.hay_filtro &amp;&amp; !s.destacado) {
opacidad = 0.10;
colorFinal = 0x94a3b8;
} else if (data.hay_filtro &amp;&amp; s.destacado)
{
colHex = 0x22c55e;
colorFinal = colHex;
}
const isV = data.is_vertical;
const px = isV ? s.y + 0.05 : s.x;
const py = isV ? s.x + 0.05 : s.y + 0.05;
const pW = isV ? data.pp_d - 0.1 :
data.ap_w;
const pD = isV ? data.ap_w : data.pp_d -
0.1;
const pbMat = new
THREE.MeshStandardMaterial({ color: 0xb88252, roughness: 0.8, transparent:
opacidad &lt; 1, opacity: opacidad });
const pBaseMesh = new THREE.Mesh(new
THREE.BoxGeometry(pW, 0.12, pD), pbMat);
pBaseMesh.position.set(px + pW/2, s.z +
0.06, -(py + pD/2));
if (opacidad === 1) { pBaseMesh.castShadow
= true; pBaseMesh.receiveShadow = true; }
scene.add(pBaseMesh);

const h = Math.max(0.3, s.alt_p - 0.12);
const cargoMat = new
THREE.MeshStandardMaterial({ color: colorFinal, roughness: 0.5,
transparent: opacidad &lt; 1, opacity: opacidad });
let cargoMesh;
if (s.es_cilindro) {
const radius = Math.min(pW, pD) / 2.2;
cargoMesh = new THREE.Mesh(new
THREE.CylinderGeometry(radius, radius, h, 16), cargoMat);
cargoMesh.position.set(px + pW/2, s.z +
0.12 + h/2, -(py + pD/2));
} else {
cargoMesh = new THREE.Mesh(new
THREE.BoxGeometry(pW - 0.05, h, pD - 0.05), cargoMat);
cargoMesh.position.set(px + pW/2, s.z +
0.12 + h/2, -(py + pD/2));
}
if (opacidad === 1) { cargoMesh.castShadow
= true; cargoMesh.receiveShadow = true; }
cargoMesh.userData = { id: s.id, sku:
s.sku, letra: s.letra, modulo: s.modulo, nivel: s.nivel, zona: modoVista
=== &#39;9 Zonas (ABC-XYZ)&#39; ? s.abc_xyz : s.abc, alt: s.alt_p, es_mixto:
s.es_mixto, unidades: s.unidades, cap_maxima: s.cap_maxima };
meshesInteractivos.push(cargoMesh);
scene.add(cargoMesh);
}
});
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
container.addEventListener(&#39;mousemove&#39;, (event) =&gt;
{
const rect = container.getBoundingClientRect();
mouse.x = ((event.clientX - rect.left) /
rect.width) * 2 - 1;
mouse.y = -((event.clientY - rect.top) /
rect.height) * 2 + 1;
raycaster.setFromCamera(mouse, camera);
const intersects =
raycaster.intersectObjects(meshesInteractivos);
if (intersects.length &gt; 0) {
const d = intersects[0].object.userData;
tooltip.style.display = &#39;block&#39;;
tooltip.style.left = (event.clientX + 15) +
&#39;px&#39;;

tooltip.style.top = (event.clientY + 15) +
&#39;px&#39;;
const mixBadge = d.es_mixto ? &#39;&lt;span
style=&quot;background:#8b5cf6; color:white; padding:2px 6px; border-radius:4px;
font-size:10px;&quot;&gt;PALLET MIXTO&lt;/span&gt;&lt;br&gt;&#39; : &#39;&#39;;
tooltip.innerHTML = `&lt;span
style=&quot;color:#38bdf8; font-weight:bold;&quot;&gt;�� POSICIÓN: ${d.id}&lt;/span&gt;&lt;h
style=&quot;margin:5px 0; border-color:#334155;&quot;&gt;${mixBadge}&lt;b
style=&quot;color:#cbd5e1;&quot;&gt;�� SKU:&lt;/b&gt; &lt;spa
style=&quot;color:#fff&quot;&gt;${d.sku}&lt;/span&gt;&lt;br&gt;&lt;b style=&quot;color:#cbd5e1;&quot;&gt;��
Pasillo:&lt;/b&gt; ${d.letra} | &lt;b style=&quot;color:#cbd5e1;&quot;&gt;Módulo:&lt;/b&gt; ${d.modulo}
| &lt;b style=&quot;color:#cbd5e1;&quot;&gt;Nivel:&lt;/b&gt; ${d.nivel}&lt;br&gt;&lt;b
style=&quot;color:#cbd5e1;&quot;&gt;�� Zona:&lt;/b&gt; ${d.zona}&lt;br&gt;&lt;
style=&quot;color:#cbd5e1;&quot;&gt;�� Alto Carga:&lt;/b&gt; ${d.alt.toFixed(2)} m&lt;br&gt;&lt;
style=&quot;color:#cbd5e1;&quot;&gt;�� Carga:&lt;/b&gt; ${d.unidades} / ${d.cap_maxima} u.`;
document.body.style.cursor = &#39;pointer&#39;;
} else {
tooltip.style.display = &#39;none&#39;;
document.body.style.cursor = &#39;default&#39;;
}
});
// LÓGICA DE ANIMACIÓN (MONTACARGAS Y
CONSOLIDACIÓN)
let updateAnimation = () =&gt; {};
const animData = data.animacion;
if (animData &amp;&amp; animData.activa) {
const isV = data.is_vertical;
function getPPos(p) {
const px = isV ? p.y + 0.05 : p.x_pal;
const py = isV ? p.x_pal + 0.05 : p.y +
0.05;
const pW = isV ? data.pp_d - 0.1 :
data.ap_w;
const pD = isV ? data.ap_w : data.pp_d -
0.1;
return { x: px + pW/2, y: p.z + 0.06, z: -
(py + pD/2) };
}
const startP = getPPos(animData.origen);
const endP = getPPos(animData.destino);
const forkGroup = new THREE.Group();
const fBody = new THREE.Mesh(new
THREE.BoxGeometry(1.0, 0.8, 1.8), new THREE.MeshStandardMaterial({color:
0xf39c12}));
fBody.position.y = 0.4;
forkGroup.add(fBody);
const fMast = new THREE.Mesh(new
THREE.BoxGeometry(1.0, 2.5, 0.2), new THREE.MeshStandardMaterial({color:
0x34495e}));
fMast.position.set(0, 1.25, -1.0);
forkGroup.add(fMast);

const wGeo = new THREE.CylinderGeometry(0.3,
0.3, 1.2, 16);
const wMat = new
THREE.MeshStandardMaterial({color: 0x111111});
const w1 = new THREE.Mesh(wGeo, wMat);
w1.rotation.z = Math.PI/2; w1.position.set(0, 0.3, 0.6); forkGroup.add(w1);
const w2 = new THREE.Mesh(wGeo, wMat);
w2.rotation.z = Math.PI/2; w2.position.set(0, 0.3, -0.6);
forkGroup.add(w2);
scene.add(forkGroup);
const movingPallet = new THREE.Mesh(new
THREE.BoxGeometry(0.9, Math.max(0.3, animData.origen.alt_p - 0.12), 0.9),
new THREE.MeshStandardMaterial({ color: 0x8b5cf6 }));
scene.add(movingPallet);
movingPallet.position.set(startP.x, startP.y +
0.5, startP.z);
forkGroup.position.set(startP.x, 0, startP.z +
2.0);
let state = 0;
updateAnimation = () =&gt; {
const speed = 0.04;
const moveSpeed = 0.15;
if(state === 0) {
movingPallet.position.y -= speed;
if(movingPallet.position.y &lt;= 0.8) {
movingPallet.position.y = 0.8;
state = 1;
}
} else if(state === 1) {
const dx = endP.x -
forkGroup.position.x;
const dz = (endP.z + 2.0) -
forkGroup.position.z;
const dist = Math.sqrt(dx*dx + dz*dz);
if(dist &lt; 0.2) {
forkGroup.position.x = endP.x;
forkGroup.position.z = endP.z +
2.0;
movingPallet.position.x = endP.x;
movingPallet.position.z = endP.z;
forkGroup.rotation.y = 0;
state = 2;
} else {
forkGroup.position.x += (dx/dist) *
moveSpeed;
forkGroup.position.z += (dz/dist) *
moveSpeed;
const angle = Math.atan2(dx, dz);
forkGroup.rotation.y = angle;
movingPallet.position.x =
forkGroup.position.x + Math.sin(angle) * 1.5;

movingPallet.position.z =
forkGroup.position.z + Math.cos(angle) * 1.5;
}
} else if(state === 2) {
movingPallet.position.y += speed;
if(movingPallet.position.y &gt;= endP.y +
0.5) {
movingPallet.position.y = endP.y +
0.5;
state = 3;
}
} else if(state === 3) {
forkGroup.position.z += moveSpeed;
if(forkGroup.position.z &gt; data.ancho +
5) scene.remove(forkGroup);
}
};
}
function animate() {
requestAnimationFrame(animate);
updateAnimation();
controls.update();
renderer.render(scene, camera);
}
animate();
&lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;
&quot;&quot;&quot;
html_template = html_template.replace(&quot;map: map,&quot;, &quot;map:
tex,&quot;)
html_final = html_template.replace(&quot;__DATOS_JSON__&quot;,
json_data).replace(&quot;__MODO_VISTA__&quot;, st.session_state.modo_vista_color)
components.html(html_final, height=860)
def mostrar_analytics():
st.title(&quot;�� Analytics &amp; Reportería Ejecutivo&quot;)
if st.session_state.df_resultados is None:
st.error(&quot;⚠️ Para visualizar el Dashboard de Analytics, primero
debes cargar tu base de datos en el módulo &#39;Cubicadora WMS&#39;.&quot;)
return
df_res, MAPA = st.session_state.df_resultados.copy(),
st.session_state.mapa_columnas
# Aplicar Filtro de Bodega Global
if getattr(st.session_state, &#39;bodegas_sel&#39;, []):
df_res =
df_res[df_res[MAPA[&#39;bodega&#39;]].isin(st.session_state.bodegas_sel)]

escenario_stock = st.session_state.get(&quot;tipo_stock&quot;, &quot;Stock Promedio&quot;)
key_stock_eval = &quot;stock_maximo&quot; if escenario_stock == &quot;Stock Máximo&quot;
else &quot;stock_promedio&quot;
col_stock_val = MAPA.get(key_stock_eval, MAPA.get(&quot;stock&quot;,
df_res.columns[0]))
if col_stock_val not in df_res.columns: col_stock_val =
MAPA.get(&quot;stock&quot;, df_res.columns[0])
df_res[&#39;Stock_Num&#39;] = pd.to_numeric(df_res[col_stock_val],
errors=&#39;coerce&#39;).fillna(0)
metrics_excel = [calcular_metricas_dinamicas(row, MAPA, &quot;EXCEL&quot;) for _,
row in df_res.iterrows()]
metrics_opt = [calcular_metricas_dinamicas(row, MAPA, &quot;OPTIMO&quot;) for _,
row in df_res.iterrows()]
df_res[&#39;Pallets_Req_Excel&#39;], df_res[&#39;Pallets_Req_Optimo&#39;] =
[m[&#39;Pallets&#39;] for m in metrics_excel], [m[&#39;Pallets&#39;] for m in metrics_opt]
df_res[&#39;Ocupacion_Ult_Pct&#39;], df_res[&#39;Estado_Sku&#39;] =
[m[&#39;Ocupacion_Ultimo&#39;] for m in metrics_excel], [m[&#39;Estado&#39;] for m in
metrics_excel]
if MAPA.get(&#39;is_opt_report&#39;): df_res[&#39;Volumen_Total_M3&#39;] = 0
else: df_res[&#39;Volumen_Total_M3&#39;] =
(pd.to_numeric(df_res[MAPA[&#39;largo&#39;]], errors=&#39;coerce&#39;).fillna(0)/100) *
(pd.to_numeric(df_res[MAPA[&#39;ancho&#39;]], errors=&#39;coerce&#39;).fillna(0)/100) *
(pd.to_numeric(df_res[MAPA[&#39;alto&#39;]], errors=&#39;coerce&#39;).fillna(0)/100) *
df_res[&#39;Stock_Num&#39;]
tot_pal_ex, tot_pal_op = df_res[&#39;Pallets_Req_Excel&#39;].sum(),
df_res[&#39;Pallets_Req_Optimo&#39;].sum()
ahorro = tot_pal_ex - tot_pal_op
pct_ahorro = (ahorro / tot_pal_ex * 100) if tot_pal_ex &gt; 0 else 0
vol_tot = df_res[&#39;Volumen_Total_M3&#39;].sum()
num_alertas = sum(1 for m in metrics_excel if &quot;EXCEL&quot; in m[&quot;Estado&quot;] or
&quot;PELIGRO&quot; in m[&quot;Estado&quot;] or &quot;REVISAR&quot; in m[&quot;Estado&quot;])
cap_bod = st.session_state.kpi_layout_capacidad
pal_ub = st.session_state.kpi_layout_ubicados
pct_oc = (pal_ub / cap_bod * 100) if cap_bod &gt; 0 else 0.0
st.markdown(f&quot;### �� Indicadores Macro de Almacenamient
({escenario_stock})&quot;)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(&quot;�� Volumen Carga&quot;, f&quot;{vol_tot:,.1f} m³&quot; if vol_tot &gt; 0 els
&quot;N/D&quot;)
m2.metric(&quot;��️ Pallets Excel&quot;, f&quot;{tot_pal_ex:,} pal&quot;)
m3.metric(&quot;�� Pallets Óptimo&quot;, f&quot;{tot_pal_op:,} pal&quot;, delta=f&quot;{-
ahorro:,} pal ({pct_ahorro:.1f}%)&quot;, delta_color=&quot;inverse&quot;)
m4.metric(&quot;��️ Ocupación Bodega&quot;, f&quot;{pct_oc:.1f}%&quot; if cap_bod &gt; 0 els
&quot;N/D&quot;, delta=f&quot;{pal_ub:,}/{cap_bod:,} Slots&quot; if cap_bod &gt; 0 else &quot;Generar
Layout&quot;)

m5.metric(&quot;�� SKUs Alertas&quot;, f&quot;{num_alertas} SKUs&quot;, delta=&quot;Atenció
Requerida&quot; if num_alertas &gt; 0 else &quot;Todo OK&quot;, delta_color=&quot;off&quot;)
st.markdown(&quot;---&quot;)
g1, g2 = st.columns(2)
with g1:
st.markdown(&quot;#### �� Distribución de SKUs por Formato&quot;)
formato_col = MAPA[&#39;formato&#39;] if not MAPA.get(&#39;is_opt_report&#39;) else
&#39;Formato&#39;
if formato_col in df_res.columns:
df_f = df_res[formato_col].value_counts().reset_index()
df_f.columns = [&#39;Formato&#39;, &#39;Cantidad&#39;]
st.plotly_chart(px.pie(df_f, values=&#39;Cantidad&#39;,
names=&#39;Formato&#39;, hole=0.4,
color_discrete_sequence=px.colors.qualitative.Bold).update_layout(margin=di
ct(l=20, r=20, t=30, b=20), height=350), use_container_width=True)
with g2:
st.markdown(&quot;#### �� Top 10 SKUs por Pallets Requeridos&quot;)
st.plotly_chart(px.bar(df_res.sort_values(by=&#39;Pallets_Req_Excel&#39;,
ascending=False).head(10), x=&#39;Pallets_Req_Excel&#39;, y=MAPA[&#39;sku&#39;],
orientation=&#39;h&#39;, text=&#39;Pallets_Req_Excel&#39;, color=&#39;Pallets_Req_Excel&#39;,
color_continuous_scale=&#39;Blues&#39;).update_layout(yaxis=dict(autorange=&quot;reverse
d&quot;), margin=dict(l=20, r=20, t=30, b=20), height=350, showlegend=False),
use_container_width=True)
st.markdown(&quot;---&quot;)
g3, g4 = st.columns(2)
with g3:
st.markdown(&quot;#### �� Comparativa de Pallets: Excel vs. Óptimo (To
15)&quot;)
df_comp = df_res.head(15)
fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(x=df_comp[MAPA[&#39;sku&#39;]],
y=df_comp[&#39;Pallets_Req_Excel&#39;], name=&#39;Excel (Manual)&#39;,
marker_color=&#39;#3b82f6&#39;))
fig_comp.add_trace(go.Bar(x=df_comp[MAPA[&#39;sku&#39;]],
y=df_comp[&#39;Pallets_Req_Optimo&#39;], name=&#39;Óptimo Algorítmico&#39;,
marker_color=&#39;#10b981&#39;))
fig_comp.update_layout(barmode=&#39;group&#39;, margin=dict(l=20, r=20,
t=30, b=20), height=350, legend=dict(orientation=&quot;h&quot;, yanchor=&quot;bottom&quot;,
y=1.02, xanchor=&quot;right&quot;, x=1))
st.plotly_chart(fig_comp, use_container_width=True)
with g4:
st.markdown(&quot;#### ⚖️ Matriz Peso por Pallet vs. Ocupación&quot;)
df_res[&#39;Peso_Pallet_Kg&#39;] = [m[&#39;Peso_Pallet&#39;] for m in
metrics_excel]
fig_scatter = px.scatter(df_res, x=&#39;Ocupacion_Ult_Pct&#39;,
y=&#39;Peso_Pallet_Kg&#39;, size=&#39;Stock_Num&#39;, color=&#39;Estado_Sku&#39;,
hover_name=MAPA[&#39;sku&#39;], labels={&#39;Ocupacion_Ult_Pct&#39;: &#39;% Ocupación Último
Pallet&#39;, &#39;Peso_Pallet_Kg&#39;: &#39;Peso Total Pallet (kg)&#39;},
color_discrete_map={&quot;✅ OK&quot;: &quot;#10b981&quot;, &quot;❌ SIN STOCK&quot;: &quot;#64748b&quot;, &quot;⚠️
REVISAR DATOS&quot;: &quot;#f59e0b&quot;, &quot;�� SOBREPESO (&gt;1200kg)&quot;: &quot;#ef4444&quot;})

fig_scatter.add_hline(y=MAX_PESO_PALLET, line_dash=&quot;dash&quot;,
line_color=&quot;red&quot;, annotation_text=&quot;Límite Peso (1200kg)&quot;)
fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20),
height=350)
st.plotly_chart(fig_scatter, use_container_width=True)
def mostrar_inbound():
st.title(&quot;�� Entrada de Mercadería (Inbound)&quot;)
st.info(&quot;Módulo táctico para la gestión inteligente de andenes,
asignación de recepción y priorización de descarga.&quot;)
if st.session_state.df_resultados is None:
st.warning(&quot;⚠️ Debes cargar la base de datos en la Cubicadora para
operar este módulo.&quot;)
return
df_res = st.session_state.df_resultados
mapa = st.session_state.mapa_columnas
if getattr(st.session_state, &#39;bodegas_sel&#39;, []):
df_res =
df_res[df_res[mapa[&#39;bodega&#39;]].isin(st.session_state.bodegas_sel)]
skus_disponibles = df_res[mapa[&#39;sku&#39;]].astype(str).unique().tolist()
col1, col2 = st.columns([1, 2])
with col1:
st.markdown(&quot;&lt;div style=&#39;background:white; padding:20px; border-
radius:10px; border:1px solid #e2e8f0;&#39;&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;#### �� Registro de ASN (Advanced Shipping Notice)&quot;)
sku_in = st.selectbox(&quot;1. Seleccionar SKU recibido:&quot;,
skus_disponibles)
prov_in = st.text_input(&quot;2. Proveedor / Origen:&quot;, value=&quot;Proveedor
Genérico&quot;)
cant_in = st.number_input(&quot;3. Unidades Totales Recibidas:&quot;,
min_value=1, value=100)
fila_sku = df_res[df_res[mapa[&#39;sku&#39;]].astype(str) ==
sku_in].iloc[0]
cap_optima = int(fila_sku.get(&quot;Capacidad_Optima&quot;, 1)) if
mapa.get(&quot;is_opt_report&quot;) else precalcular_fila(fila_sku,
mapa)[&quot;Capacidad_Optima&quot;]
cap_optima = max(cap_optima, 1)
pallets_gen = int(math.ceil(cant_in / cap_optima))
es_crossdock = False
escenario = st.session_state.get(&quot;tipo_stock&quot;, &quot;Stock Promedio&quot;)
key_stock = &quot;stock_maximo&quot; if escenario == &quot;Stock Máximo&quot; else
&quot;stock_promedio&quot;
col_stock = mapa.get(key_stock, mapa.get(&quot;stock&quot;, &quot;Stock&quot;))

stock_actual = float(fila_sku.get(col_stock, 0))
if stock_actual &lt;= 0: es_crossdock = True
st.markdown(&quot;---&quot;)
st.markdown(f&quot;**�� Pallets a generar:** `{pallets_gen}` pallet
físicos.&quot;)
if es_crossdock:
st.error(&quot;�� ALERTA CROSS-DOCKING: Este SKU no tiene stock e
bodega. Priorizar envío directo a Staging de Salida.&quot;)
if st.button(&quot;�� Confirmar Ingreso&quot;, type=&quot;primary&quot;
use_container_width=True):
nueva_entrada = pd.DataFrame([{
&quot;Fecha&quot;: pd.Timestamp.now().strftime(&quot;%Y-%m-%d %H:%M&quot;),
&quot;Proveedor&quot;: prov_in,
&quot;SKU&quot;: sku_in,
&quot;Unidades&quot;: cant_in,
&quot;Pallets_Generados&quot;: pallets_gen,
&quot;Ubicacion_Sugerida&quot;: &quot;STAGING OUT&quot; if es_crossdock else
&quot;RACK PENDIENTE&quot;,
&quot;Estado&quot;: &quot;Recibido&quot;
}])
st.session_state.historial_inbound =
pd.concat([st.session_state.historial_inbound, nueva_entrada],
ignore_index=True)
st.success(&quot;✅ Mercadería registrada correctamente en andén.&quot;)
st.markdown(&quot;&lt;/div&gt;&quot;, unsafe_allow_html=True)
with col2:
st.markdown(&quot;#### �� Historial de Entradas Recientes (Andén)&quot;)
if not st.session_state.historial_inbound.empty:
st.dataframe(st.session_state.historial_inbound,
use_container_width=True)
st.markdown(&quot;#### �� Asignador Automático (Put-Away)&quot;)
if st.session_state.res_layout_actual is not None:
if st.button(&quot;�� Escanear Layout y Sugerir Ubicaciones&quot;
use_container_width=True):
st.info(&quot;Buscando posiciones vacías según rotación ABC
en el Gemelo Digital...&quot;)
alm = st.session_state.res_layout_actual[&#39;almacen&#39;]
vacios = [s for s in alm if not s[&#39;ocupado&#39;]]
if vacios:
st.success(f&quot;Se encontraron {len(vacios)}
posiciones vacías. Sugiriendo ubicación óptima:
**{vacios[0][&#39;id_posicion&#39;]}**&quot;)
else:
st.error(&quot;Bodega al 100% de capacidad. No hay
posiciones disponibles.&quot;)
else:

st.warning(&quot;⚠️ Debes generar el Layout de Bodega primero
para habilitar el algoritmo de Put-Away.&quot;)
else:
st.info(&quot;No hay recepciones registradas el día de hoy.&quot;)
def mostrar_outbound():
st.title(&quot;�� Salida de Mercadería (Outbound)&quot;)
st.info(&quot;Planificación de despacho, consolidación de pedidos por ruta y
generación de Olas de Picking.&quot;)
if st.session_state.df_resultados is None or
st.session_state.res_layout_actual is None:
st.warning(&quot;⚠️ Debes cargar la base de datos y generar el Layout 3D
para operar este módulo.&quot;)
return
df_res = st.session_state.df_resultados
mapa = st.session_state.mapa_columnas
alm = st.session_state.res_layout_actual[&#39;almacen&#39;]
skus_en_bodega = list(set([s[&#39;sku&#39;] for s in alm if s[&#39;ocupado&#39;]]))
col1, col2 = st.columns([1, 2])
with col1:
st.markdown(&quot;&lt;div style=&#39;background:white; padding:20px; border-
radius:10px; border:1px solid #e2e8f0;&#39;&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;#### �� Crear Orden de Salida&quot;)
if not skus_en_bodega:
st.error(&quot;No hay SKUs ubicados en el layout.&quot;)
else:
sku_out = st.selectbox(&quot;1. Seleccionar SKU a despachar:&quot;,
skus_en_bodega)
posiciones_sku = [s for s in alm if s[&#39;ocupado&#39;] and s[&#39;sku&#39;]
== sku_out]
max_pallets = len(posiciones_sku)
cant_pallets_out = st.number_input(f&quot;2. Pallets a extraer (Máx
disponible: {max_pallets}):&quot;, min_value=1, max_value=max_pallets if
max_pallets &gt; 0 else 1, value=1)
cliente_out = st.text_input(&quot;3. Cliente / Ruta:&quot;,
value=&quot;Cliente A - Ruta Centro&quot;)
if st.button(&quot;�� Generar Ola de Picking&quot;, type=&quot;primary&quot;
use_container_width=True):
rutas = [p[&#39;id_posicion&#39;] for p in
posiciones_sku[:cant_pallets_out]]
nueva_orden = {
&quot;Orden&quot;: f&quot;ORD-
{len(st.session_state.ordenes_picking)+1:04d}&quot;,
&quot;Cliente&quot;: cliente_out,

&quot;SKU&quot;: sku_out,
&quot;Pallets&quot;: cant_pallets_out,
&quot;Ruta_Picking&quot;: &quot; -&gt; &quot;.join(rutas),
&quot;Estado&quot;: &quot;Pendiente de Extracción&quot;
}
st.session_state.ordenes_picking.append(nueva_orden)
st.success(&quot;✅ Orden enviada a los montacargas.&quot;)
st.markdown(&quot;&lt;/div&gt;&quot;, unsafe_allow_html=True)
with col2:
st.markdown(&quot;#### ��️ Secuencia de Picking Optimizada&quot;)
if st.session_state.ordenes_picking:
df_ordenes = pd.DataFrame(st.session_state.ordenes_picking)
st.dataframe(df_ordenes, use_container_width=True)
st.markdown(&quot;�� **Nota Operativa:** Al confirmar el Picking, e
sistema asume que los montacargas movieron la carga desde los Racks hasta
la zona amarilla de STAGING, liberando las posiciones en el Gemelo Digital
3D.&quot;)
else:
st.info(&quot;No hay órdenes de salida pendientes.&quot;)
def mostrar_movimientos():
st.title(&quot;�� Consolidación y Movimientos Internos&quot;)
st.info(&quot;Módulo de Reabastecimiento Activo (Active Replenishment) para
optimizar saldos parciales y evitar el &#39;Efecto Panal&#39; (Honeycombing) en los
racks.&quot;)
if st.session_state.res_layout_actual is None:
st.warning(&quot;⚠️ Debes generar el Layout 3D de la bodega primero para
analizar los saldos.&quot;)
return
alm = st.session_state.res_layout_actual[&#39;almacen&#39;]
with st.expander(&quot;�� Modo Pruebas (Simulador de Desorden)&quot;
expanded=False):
st.write(&quot;Usa este botón si generaste un layout perfecto y quieres
crear saldos artificialmente para probar la animación 3D del montacargas.&quot;)
if st.button(&quot;�� Simular Efecto Panal (Vaciar 2 pallets a medias)&quot;
use_container_width=True):
skus_multiples = {}
for s in alm:
if s[&#39;ocupado&#39;] and not s.get(&#39;es_mixto&#39;, False):
skus_multiples[s[&#39;sku&#39;]] = skus_multiples.get(s[&#39;sku&#39;],
0) + 1
candidatos = [sku for sku, cant in skus_multiples.items() if
cant &gt;= 2]
if candidatos:
sku_test = candidatos[0]
pals_test = [s for s in alm if s[&#39;ocupado&#39;] and s[&#39;sku&#39;] ==
sku_test][:2]

pals_test[0][&#39;unidades&#39;] = int(pals_test[0][&#39;cap_maxima&#39;] *
0.4) or 1
pals_test[0][&#39;es_saldo&#39;] = True
pals_test[1][&#39;unidades&#39;] = int(pals_test[1][&#39;cap_maxima&#39;] *
0.3) or 1
pals_test[1][&#39;es_saldo&#39;] = True
st.session_state.res_layout_actual[&#39;almacen&#39;] = alm
st.success(f&quot;¡Magia hecha! Se generaron 2 saldos del SKU
{sku_test}. Cierra este panel y mira abajo.&quot;)
st.rerun()
else:
st.error(&quot;No hay SKUs con suficientes pallets para
simular.&quot;)
parciales = [s for s in alm if s[&#39;ocupado&#39;] and not s.get(&#39;es_mixto&#39;,
False) and s.get(&#39;unidades&#39;, 0) &lt; s.get(&#39;cap_maxima&#39;, 1)]
from collections import defaultdict
sku_partials = defaultdict(list)
for p in parciales:
sku_partials[p[&#39;sku&#39;]].append(p)
skus_candidatos = {sku: pos for sku, pos in sku_partials.items() if
len(pos) &gt; 1}
col1, col2 = st.columns([1, 2])
with col1:
st.markdown(&quot;&lt;div style=&#39;background:white; padding:20px; border-
radius:10px; border:1px solid #e2e8f0;&#39;&gt;&quot;, unsafe_allow_html=True)
st.markdown(&quot;#### �� Algoritmo Buscador de Tareas&quot;)
if not skus_candidatos:
st.success(&quot;✅ Excelente. No hay &#39;Efecto Panal&#39; detectado. Todos
los saldos están optimizados o no existen múltiples pallets parciales del
mismo SKU.&quot;)
else:
st.warning(f&quot;⚠️ Se detectaron {len(skus_candidatos)} SKUs
ocupando múltiples espacios innecesariamente.&quot;)
sku_sel = st.selectbox(&quot;1. Seleccionar SKU a Consolidar:&quot;,
list(skus_candidatos.keys()))
posiciones = sorted(skus_candidatos[sku_sel], key=lambda x:
x[&#39;unidades&#39;])
origen = posiciones[0]
destino = posiciones[-1]
u_ori = origen.get(&#39;unidades&#39;, 0)
u_des = destino.get(&#39;unidades&#39;, 0)
cap_max = destino.get(&#39;cap_maxima&#39;, 1)
pueden_fusionarse = (u_ori + u_des) &lt;= cap_max

st.markdown(&quot;---&quot;)
st.markdown(&quot;#### �� Propuesta de Movimiento:&quot;)
st.markdown(f&quot;**�� Origen (Bajar):** Posició
`{origen[&#39;id_posicion&#39;]}` — **{u_ori:.0f} u.**&quot;)
st.markdown(f&quot;**�� Destino (Rellenar):** Posició
`{destino[&#39;id_posicion&#39;]}` — **{u_des:.0f} u.**&quot;)
if pueden_fusionarse:
st.success(f&quot;✅ El pallet destino quedará con **{u_ori +
u_des:.0f} / {cap_max:.0f} unidades**.&quot;)
if st.button(&quot;�� Confirmar Tarea de Grúa (Fusión)&quot;
type=&quot;primary&quot;, use_container_width=True):
# Guardar info de animación
st.session_state.ultima_animacion = {
&quot;activa&quot;: True,
&quot;origen&quot;: {&quot;x_pal&quot;: origen[&quot;x_pal&quot;], &quot;y&quot;:
origen[&quot;y&quot;], &quot;z&quot;: origen[&quot;z&quot;], &quot;alt_p&quot;: origen.get(&quot;alt_p&quot;, 1.2)},
&quot;destino&quot;: {&quot;x_pal&quot;: destino[&quot;x_pal&quot;], &quot;y&quot;:
destino[&quot;y&quot;], &quot;z&quot;: destino[&quot;z&quot;], &quot;alt_p&quot;: destino.get(&quot;alt_p&quot;, 1.2)},
&quot;sku&quot;: sku_sel
}
# EJECUTAR EL MOVIMIENTO LÓGICO
destino[&#39;unidades&#39;] += origen[&#39;unidades&#39;]
destino[&#39;pct&#39;] = destino[&#39;unidades&#39;] /
destino[&#39;cap_maxima&#39;]
destino[&#39;es_saldo&#39;] = destino[&#39;unidades&#39;] &lt;
destino[&#39;cap_maxima&#39;]
# VACIAR ORIGEN
origen[&#39;ocupado&#39;] = False
origen[&#39;sku&#39;] = &quot;&quot;
origen[&#39;unidades&#39;] = 0
origen[&#39;es_saldo&#39;] = False
# Guardar tarea
st.session_state.tareas_movimiento.append({
&quot;Fecha&quot;: pd.Timestamp.now().strftime(&quot;%Y-%m-%d
%H:%M&quot;),
&quot;SKU&quot;: sku_sel,
&quot;Origen&quot;: origen[&#39;id_posicion&#39;],
&quot;Destino&quot;: destino[&#39;id_posicion&#39;],
&quot;Unidades Movidas&quot;: u_ori,
&quot;Estado&quot;: &quot;Completado&quot;
})
st.rerun()
else:
st.error(f&quot;❌ Sobrecarga. La suma ({u_ori + u_des:.0f} u.)
supera la capacidad del pallet ({cap_max:.0f} u.). Revisa la configuración
de apilamiento.&quot;)

st.markdown(&quot;&lt;/div&gt;&quot;, unsafe_allow_html=True)
with col2:
st.markdown(&quot;#### �� Historial de Movimientos Internos&quot;)
if st.session_state.get(&#39;tareas_movimiento&#39;):
st.dataframe(pd.DataFrame(st.session_state.tareas_movimiento),
use_container_width=True)
st.markdown(&quot;�� **Tip Operativo:** Cuando un movimiento s
confirma, la Maqueta 3D del Layout actualiza la posición original dejándola
vacía para su próximo uso, incrementando la ocupación cúbica global de tu
bodega.&quot;)
else:
st.info(&quot;No hay tareas de consolidación registradas.&quot;)
menu_opciones = [
&quot;�� Portada Principal&quot;,
&quot;�� Cubicadora WMS&quot;,
&quot;��️ Layout de Bodega&quot;,
&quot;�� Analytics &amp; Reportería&quot;,
&quot;�� Entrada Mercadería&quot;,
&quot;�� Salida Mercadería&quot;,
&quot;�� Movimientos Internos&quot;,
]
if st.session_state.menu_seleccion not in menu_opciones:
st.session_state.menu_seleccion = menu_opciones[0]
# ============================================================
# SIDEBAR GLOBAL (Aplica a todas las pestañas)
# ============================================================
st.session_state.menu_seleccion = st.sidebar.radio(&quot;Navegación&quot;,
menu_opciones, index=menu_opciones.index(st.session_state.menu_seleccion))
st.sidebar.markdown(&quot;---&quot;)
st.session_state.tipo_stock = st.sidebar.radio(
&quot;�� Escenario de Stock a evaluar:&quot;,
[&quot;Stock Promedio&quot;, &quot;Stock Máximo&quot;],
index=[&quot;Stock Promedio&quot;, &quot;Stock
Máximo&quot;].index(st.session_state.get(&quot;tipo_stock&quot;, &quot;Stock Promedio&quot;))
)
st.sidebar.markdown(&quot;---&quot;)
# FILTRO GLOBAL BODEGA EN SIDEBAR
if st.session_state.df_resultados is not None:
mapa = st.session_state.mapa_columnas
df_all = st.session_state.df_resultados
col_bod = mapa.get(&#39;bodega&#39;) if mapa and mapa.get(&#39;bodega&#39;) else
&#39;Bodega&#39;
if col_bod in df_all.columns:
opciones_bodega = sorted([str(x) for x in df_all[col_bod].unique()
if pd.notna(x) and str(x) != &#39;nan&#39; and str(x) != &#39;N/D&#39;])
if opciones_bodega:

valid_sel = [b for b in st.session_state.get(&#39;bodegas_sel&#39;, [])
if b in opciones_bodega]
if not st.session_state.get(&#39;bodegas_sel&#39;) and not valid_sel:
st.session_state.bodegas_sel = opciones_bodega
st.session_state.bodegas_sel = st.sidebar.multiselect(
&quot;�� Filtrar por Bodega:&quot;,
options=opciones_bodega,
default=st.session_state.bodegas_sel
)
st.sidebar.markdown(&quot;---&quot;)
st.sidebar.caption(&quot;WMS Analytics Hub v8.9 • Dev Branch&quot;)
if st.session_state.menu_seleccion == &quot;�� Portada Principal&quot;
mostrar_portada()
elif st.session_state.menu_seleccion == &quot;�� Cubicadora WMS&quot;
mostrar_cubicadora()
elif st.session_state.menu_seleccion == &quot;��️ Layout de Bodega&quot;
mostrar_layout()
elif st.session_state.menu_seleccion == &quot;�� Analytics &amp; Reportería&quot;
mostrar_analytics()
elif st.session_state.menu_seleccion == &quot;�� Entrada Mercadería&quot;
mostrar_inbound()
elif st.session_state.menu_seleccion == &quot;�� Salida Mercadería&quot;
mostrar_outbound()
elif st.session_state.menu_seleccion == &quot;�� Movimientos Internos&quot;
mostrar_movimientos()
