# @title 📐🧊 CELDA 4: Visor Logístico Ultra-Rápido (Zonificación Profesional Inteligente + Exportador WMS)

try:
    from google.colab import output
    output.enable_custom_widget_manager()
    from google.colab import files
except:
    pass

import plotly.graph_objects as go
import pandas as pd
import math
import re
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import traceback
import os

if 'df_demanda' not in globals() or 'CONFIG_FLUJO' not in globals() or 'df_reporte_base_crudo' not in globals():
    display(HTML("<b style='color:#e74c3c; font-size:14px;'>⚠️ ALERTA: Primero evalúa el Layout en el Panel Master.</b>"))
else:
    try:
        # ==========================================
        # 1. CÁLCULO ESTRUCTURAL MATEMÁTICO
        # ==========================================
        ap_w = float(df_demanda['Ancho_m'].iloc[0]) if not df_demanda.empty else 1.2
        pp_d = float(df_demanda['Fondo_m'].iloc[0]) if not df_demanda.empty else 1.2
        ap_h = float(df_demanda['Alto_m'].max()) if not df_demanda.empty else 1.2
        l_m, a_m, alt_m = float(l_bod.value), float(a_bod.value), float(alt_bod.value)
        
        pal_v, pas_w, c_ptrans = int(pallets_viga.value), float(pasillo.value), int(cant_pas_trans.value)
        a_ptrans = float(ancho_pas_trans.value) if c_ptrans > 0 else 0.0
        alt_max_operativa = float(alt_grua.value)

        conf_flujo = globals()['CONFIG_FLUJO']
        is_vertical, tipo_flujo_str = conf_flujo.get('is_vertical', False), conf_flujo.get('tipo', 'Ninguno')
        w_puerta, oficinas, staging = conf_flujo.get('w_puerta', 0), conf_flujo.get('oficinas', []), conf_flujo.get('staging', [])
        cant_norte, w_norte = conf_flujo.get('cant_norte', 0), conf_flujo.get('w_norte', 0)
        cant_sur, w_sur = conf_flujo.get('cant_sur', 0), conf_flujo.get('w_sur', 0)
        cant_este, w_este = conf_flujo.get('cant_este', 0), conf_flujo.get('w_este', 0)
        cant_oeste, w_oeste = conf_flujo.get('cant_oeste', 0), conf_flujo.get('w_oeste', 0)

        virt_l_m, virt_a_m = (a_m, l_m) if is_vertical else (l_m, a_m)
        t_marco, holgura_viga, holgura_lateral, viga_h = 0.10, 0.15, 0.10, 0.12
        l_modulo = (ap_w * pal_v) + (holgura_lateral * (pal_v + 1)) + t_marco
        alt_nivel_viga = ap_h + holgura_viga + viga_h

        niveles_operativos = max(1, sum(1 for n in range(50) if n*alt_nivel_viga+ap_h+0.15 <= alt_m and n*alt_nivel_viga <= alt_max_operativa))
        ancho_bloque = (pp_d * 2) + pas_w
        filas = math.floor(virt_a_m / ancho_bloque)
        num_secciones = c_ptrans + 1
        modulos_por_seccion = math.floor(((virt_l_m - 4.0 - (c_ptrans * a_ptrans)) / num_secciones) / l_modulo) if num_secciones > 0 else 0

        cx, cy = int(cant_pilares_x.value), int(cant_pilares_y.value)
        dp_x, dp_y = float(dist_pilares_x.value), float(dist_pilares_y.value)
        dp_x_real, nx = (l_m / (cx + 1), cx) if cx > 0 else (dp_x, math.floor(l_m / dp_x) if dp_x > 0 else 0)
        dp_y_real, ny = (a_m / (cy + 1), cy) if cy > 0 else (dp_y, math.floor(a_m / dp_y) if dp_y > 0 else 0)

        pilares_reales = [(px * dp_x_real, py * dp_y_real) for px in range(1, nx + 1) for py in range(1, ny + 1)]
        virt_pilares = [(py, px) for px, py in pilares_reales] if is_vertical else pilares_reales

        modulos, almacen = [], []
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
                        for ofi in oficinas:
                            if not (rx2 + 1.5 < ofi['x'] or rx1 - 1.5 > ofi['x'] + ofi['w'] or ry2 + 1.5 < ofi['y'] or ry1 - 1.5 > ofi['y'] + ofi['d']): eliminado = True; break
                        if not eliminado:
                            for st in staging:
                                if not (rx2 < st['x1'] or rx1 > st['x2'] or ry2 < st['y1'] or ry1 > st['y2']): eliminado = True; break
                        if eliminado: continue

                        bloqueado_pilar = any((x_pos <= px <= x_pos + l_modulo) and (y_rack - 0.25 <= py <= y_rack + pp_d + 0.25) for px, py in virt_pilares)

                        modulos.append({'x': x_pos, 'y': y_rack, 'bloqueado': bloqueado_pilar})
                        if not bloqueado_pilar:
                            for n in range(niveles_operativos):
                                z_piso = 0 if n == 0 else (n * alt_nivel_viga)
                                for p_idx in range(pal_v):
                                    x_pal = x_pos + t_marco + holgura_lateral + (p_idx * (ap_w + holgura_lateral))
                                    id_posicion = f"{letra_pasillo}-{num_modulo:02d}-{n+1}{lado}"
                                    almacen.append({'id_posicion': id_posicion, 'letra_pasillo': letra_pasillo, 'nivel': n+1, 'x': x_pos, 'y': y_rack, 'x_pal': x_pal, 'z': z_piso, 'ocupado': False, 'sku': None, 'abc': None, 'abc_xyz': None, 'alt_p': 0})

        # =========================================================================================
        # 🧠 ALGORITMO DE SLOTTING PROFESIONAL: ZONIFICACIÓN POR PASILLOS (A=Adelante, C=Fondo)
        # =========================================================================================
        almacen.sort(key=lambda x: (x['letra_pasillo'], x['nivel'], x['x'], x['y']))
        df_demanda = df_demanda.sort_values(by='ABC_XYZ')

        # Aplicamos la restricción del peso de la grúa (si la tiene configurada)
        limite_peso_grua = conf_flujo.get('peso_max_grua', 100000)

        for _, row in df_demanda.iterrows():
            sku, cant = str(row['SKU']).strip().upper(), int(row['Cantidad_Pallets'])
            abc_clase = str(row['ABC'])
            abc_xyz_clase = str(row['ABC_XYZ']) if 'ABC_XYZ' in row else abc_clase + 'Z'
            alto_real_sku = float(row['Alto_m']) if 'Alto_m' in row else ap_h
            peso_real_pallet = float(row['Peso_Pallet_kg']) if 'Peso_Pallet_kg' in row else 0
            
            # Regla de oro: si el pallet pesa más de lo que soporta la grúa, se fuerza al Nivel 1
            forzar_nivel_1 = (peso_real_pallet > limite_peso_grua)

            ubicados = 0
            for slot in almacen:
                if ubicados >= cant: break
                if not slot['ocupado']:
                    # Si debe ir a nivel 1 por sobrepeso, saltamos las demás alturas
                    if forzar_nivel_1 and slot['nivel'] > 1:
                        continue
                        
                    slot.update({'ocupado': True, 'sku': sku, 'abc': abc_clase, 'abc_xyz': abc_xyz_clase, 'alt_p': alto_real_sku})
                    ubicados += 1

        pallets_ubicados_totales = sum(1 for s in almacen if s['ocupado'])
        capacidad_total_slots = len(almacen)
        
        dict_color_abc = {'A': '#e74c3c', 'B': '#f39c12', 'C': '#3498db'}
        dict_color_abcxyz = {
            'AX': '#900C3F', 'AY': '#C70039', 'AZ': '#FF5733',
            'BX': '#E67E22', 'BY': '#F39C12', 'BZ': '#F1C40F',
            'CX': '#2E86C1', 'CY': '#3498DB', 'CZ': '#85C1E9'
        }

        # ==========================================
        # 2. INTERFAZ UNIFICADA DE BÚSQUEDA Y EXPORTACIÓN
        # ==========================================
        search_foco = widgets.Text(value="", placeholder='Ej: P-1, H-2...', description='🔍 Foco SKU:', style={'description_width': 'initial'}, layout=widgets.Layout(width='200px'))
        vista_dropdown = widgets.Dropdown(options=['3 Zonas (ABC)', '9 Zonas (ABC-XYZ)'], value='3 Zonas (ABC)', description='🎨 Colores:', layout=widgets.Layout(width='200px'))
        
        btn_2d = widgets.Button(description="🗺️ Actualizar 2D", button_style="warning", layout=widgets.Layout(width='140px', margin='0 5px 0 10px'))
        btn_3d = widgets.Button(description="🧊 Levantar 3D", button_style="info", layout=widgets.Layout(width='140px'))
        
        # NUEVOS BOTONES DE EXPORTACIÓN WMS
        btn_export_drive = widgets.Button(description="💾 Guardar WMS a Drive", button_style="success", icon="cloud-upload", layout=widgets.Layout(width='180px', margin='0 5px 0 10px'))
        btn_export_local = widgets.Button(description="⬇️ Descargar WMS a PC", button_style="primary", icon="download", layout=widgets.Layout(width='180px'))
        
        box_ui = widgets.HBox([search_foco, vista_dropdown, btn_2d, btn_3d], layout=widgets.Layout(margin='10px 0 5px 0', align_items='center'))
        box_export = widgets.HBox([btn_export_drive, btn_export_local], layout=widgets.Layout(margin='0 0 10px 0', align_items='center'))
        
        out_msg = widgets.Output()
        out_2d = widgets.Output()
        out_3d = widgets.Output()

        display(HTML("<h3 style='color:#2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom:5px;'>Visor Logístico Interactivo | Slotting Profesional</h3>"))
        display(box_ui)
        display(box_export)
        display(out_msg)
        display(out_2d)
        display(out_3d)
        
        # ==========================================
        # 3. MOTOR DE EXPORTACIÓN WMS (NUEVO)
        # ==========================================
        def generar_reporte_wms(destino):
            with out_msg:
                clear_output()
                display(HTML("<b style='color:#2980b9;'>⏳ Generando reporte de posiciones, un momento...</b>"))
                
                try:
                    # Traemos la data pura de la cubicadora que guardamos en la Celda 3
                    df_base = globals()['df_reporte_base_crudo'].copy()
                    
                    # Extraer el mapeo de posiciones de nuestro almacén virtual
                    posiciones_por_sku = {}
                    for slot in almacen:
                        if slot['ocupado']:
                            sku = slot['sku']
                            if sku not in posiciones_por_sku:
                                posiciones_por_sku[sku] = []
                            posiciones_por_sku[sku].append(slot['id_posicion'])
                    
                    # Convertir la lista de posiciones a un texto legible por Excel (Ej: "P1-02-1A, P1-02-1B")
                    def get_posiciones_str(sku_code):
                        sku_str = str(sku_code).strip().upper()
                        if sku_str in posiciones_por_sku:
                            return ", ".join(posiciones_por_sku[sku_str])
                        return "Sin Ubicar (Falta Capacidad / Demanda 0)"

                    col_sku = 'Codigo_Producto' if 'Codigo_Producto' in df_base.columns else df_base.columns[0]
                    df_base['Posiciones_Asignadas_Layout'] = df_base[col_sku].apply(get_posiciones_str)
                    
                    # Crear el archivo Excel
                    nombre_archivo = 'WMS_Reporte_Ubicaciones_Layout.xlsx'
                    ruta_drive = f'/content/drive/MyDrive/{nombre_archivo}'
                    
                    df_base.to_excel(ruta_drive, index=False)
                    
                    clear_output()
                    if destino == 'drive':
                        display(HTML(f"<div style='background:#ecfdf5; padding:10px; border-left:4px solid #27ae60; color:#065f46; font-size:12px;'>✔️ <b>¡Reporte guardado con éxito!</b><br>Lo encuentras en 'Mi Unidad' de Google Drive como: <b>{nombre_archivo}</b></div>"))
                    elif destino == 'local':
                        display(HTML(f"<div style='background:#ebf5fb; padding:10px; border-left:4px solid #2980b9; color:#154360; font-size:12px;'>⬇️ <b>¡Descarga iniciada!</b><br>Tu reporte con las ubicaciones ({nombre_archivo}) se está bajando a tu computadora.</div>"))
                        files.download(ruta_drive)
                        
                except Exception as e:
                    clear_output()
                    display(HTML(f"<div style='color:#c0392b; font-size:12px;'>❌ <b>Error al exportar:</b> {str(e)}</div>"))

        btn_export_drive.on_click(lambda b: generar_reporte_wms('drive'))
        btn_export_local.on_click(lambda b: generar_reporte_wms('local'))

        # ==========================================
        # FUNCIONES DE ALERTAS Y VISORES
        # ==========================================
        def comprobar_alertas(skus_buscados):
            with out_msg:
                clear_output()
                if not skus_buscados: return
                
                df_bd_completa = globals().get('df_demanda_full', pd.DataFrame())
                for s in skus_buscados:
                    if s not in df_bd_completa['SKU'].astype(str).str.upper().values:
                        display(HTML(f"<div style='color:#c0392b; font-size:12px; margin-bottom:5px;'>⚠️ <b>{s}</b> no existe en la Base de Datos general.</div>"))
                        continue
                        
                    skus_dibujados = set(slot['sku'] for slot in almacen if slot['ocupado'])
                    if s not in skus_dibujados:
                        stock_fila = df_bd_completa[df_bd_completa['SKU'].astype(str).str.upper() == s]['Cantidad_Pallets'].values[0]
                        if stock_fila <= 0:
                            display(HTML(f"<div style='color:#d35400; font-size:12px; margin-bottom:5px;'>⚠️ <b>{s}</b> no se dibuja porque su stock operativo es 0 (No requiere pallets).</div>"))
                        else:
                            clase_fila = df_bd_completa[df_bd_completa['SKU'].astype(str).str.upper() == s]['ABC_XYZ'].values[0]
                            display(HTML(f"<div style='color:#d35400; font-size:12px; margin-bottom:5px;'>⚠️ <b>{s}</b> es Categoría {clase_fila}, pero desactivaste esa clase madre en el Panel Master.</div>"))

        def render_2d(raw_input, modo_vista):
            with out_2d:
                clear_output(wait=True)
                try:
                    skus_buscados = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw_input) if s.strip())
                    comprobar_alertas(skus_buscados)
                    
                    modulos_ocupados = set((s['x'], s['y']) for s in almacen if s['ocupado'])
                    modulos_destacados = set((s['x'], s['y']) for s in almacen if s['ocupado'] and s['sku'] in skus_buscados)

                    fig = go.Figure()
                    fig.add_shape(type="rect", x0=0, y0=0, x1=l_m, y1=a_m, line=dict(color="#2c3e50", width=4), fillcolor="#fafafa")

                    def add_rect_path(x0, y0, x1, y1, path_list):
                        if is_vertical: path_list.append(f"M {y0} {x0} L {y1} {x0} L {y1} {x1} L {y0} {x1} Z")
                        else: path_list.append(f"M {x0} {y0} L {x1} {y0} L {x1} {y1} L {x0} {y1} Z")

                    p_racks = {k: [] for k in ['Empty', 'Blocked', 'Destacado', 'Apagado'] + list(dict_color_abc.keys()) + list(dict_color_abcxyz.keys())}
                    path_pas_t, path_pas_l, path_pil = [], [], []

                    for s in range(1, num_secciones):
                        x_corte = 2.0 + (s * modulos_por_seccion * l_modulo) + ((s - 1) * a_ptrans)
                        add_rect_path(x_corte, 2.0, x_corte + a_ptrans, virt_a_m - 2.0, path_pas_t)

                    for f in range(filas):
                        y_p = (f * ancho_bloque) + 2.0 + pp_d
                        if f < filas - 1:
                            add_rect_path(2.0, y_p, virt_l_m - 2.0, y_p + pas_w, path_pas_l)
                            letra_pasillo = chr(64 + f + 1) if (f+1) <= 26 else f"P{f+1}"
                            if is_vertical: fig.add_annotation(x=y_p + (pas_w / 2), y=virt_l_m / 2, text=f"<b>PASILLO {letra_pasillo}</b>", showarrow=False, font=dict(size=10, color="#2980b9"), textangle=-90)
                            else: fig.add_annotation(x=virt_l_m / 2, y=y_p + (pas_w / 2), text=f"<b>PASILLO {letra_pasillo}</b>", showarrow=False, font=dict(size=10, color="#2980b9"))

                    for mod in modulos:
                        x_pos, y_rack = mod['x'], mod['y']
                        if mod['bloqueado']: 
                            add_rect_path(x_pos, y_rack, x_pos + l_modulo, y_rack + pp_d, p_racks['Blocked'])
                        elif (x_pos, y_rack) in modulos_ocupados:
                            if skus_buscados:
                                if (x_pos, y_rack) in modulos_destacados: add_rect_path(x_pos, y_rack, x_pos + l_modulo, y_rack + pp_d, p_racks['Destacado'])
                                else: add_rect_path(x_pos, y_rack, x_pos + l_modulo, y_rack + pp_d, p_racks['Apagado'])
                            else:
                                if '9 Zonas' in modo_vista:
                                    abcs_aqui = [s['abc_xyz'] for s in almacen if s['x']==x_pos and s['y']==y_rack and s['ocupado']]
                                else:
                                    abcs_aqui = [s['abc'] for s in almacen if s['x']==x_pos and s['y']==y_rack and s['ocupado']]
                                clase = min(abcs_aqui) if abcs_aqui else 'Empty'
                                add_rect_path(x_pos, y_rack, x_pos + l_modulo, y_rack + pp_d, p_racks.get(clase, p_racks['Empty']))
                        else:
                            add_rect_path(x_pos, y_rack, x_pos + l_modulo, y_rack + pp_d, p_racks['Empty'])

                    for px, py in pilares_reales:
                        if px < l_m and py < a_m:
                            if is_vertical: add_rect_path(py-0.25, px-0.25, py+0.25, px+0.25, path_pil)
                            else: add_rect_path(px-0.25, py-0.25, px+0.25, py+0.25, path_pil)

                    if path_pas_t: fig.add_shape(type="path", path=" ".join(path_pas_t), fillcolor="rgba(52, 152, 219, 0.15)", line=dict(width=0))
                    if path_pas_l: fig.add_shape(type="path", path=" ".join(path_pas_l), fillcolor="rgba(41, 128, 185, 0.08)", line=dict(width=0))
                    
                    if p_racks['Empty']: fig.add_shape(type="path", path=" ".join(p_racks['Empty']), fillcolor="#ecf0f1", line=dict(color="#bdc3c7", width=1))
                    if p_racks['Blocked']: fig.add_shape(type="path", path=" ".join(p_racks['Blocked']), fillcolor="#95a5a6", line=dict(color="#7f8c8d", width=1))
                    if p_racks['Apagado']: fig.add_shape(type="path", path=" ".join(p_racks['Apagado']), fillcolor="#ecf0f1", line=dict(color="#bdc3c7", width=1))
                    if p_racks['Destacado']: fig.add_shape(type="path", path=" ".join(p_racks['Destacado']), fillcolor="#2ecc71", line=dict(color="#27ae60", width=2))
                    
                    if '9 Zonas' in modo_vista:
                        for clase, color in dict_color_abcxyz.items():
                            if p_racks[clase]: fig.add_shape(type="path", path=" ".join(p_racks[clase]), fillcolor=color, line=dict(color="#2c3e50", width=1))
                    else:
                        for clase, color in dict_color_abc.items():
                            if p_racks[clase]: fig.add_shape(type="path", path=" ".join(p_racks[clase]), fillcolor=color, line=dict(color="#2c3e50", width=1))
                            
                    if path_pil: fig.add_shape(type="path", path=" ".join(path_pil), fillcolor="#e74c3c", line=dict(color="#c0392b", width=1.5))

                    hover_data = {}
                    for s in almacen:
                        if s['ocupado']:
                            coord = (s['x'], s['y'])
                            if coord not in hover_data: hover_data[coord] = []
                            hover_data[coord].append(f"[{s['id_posicion']}] {s['sku']} ({s['abc_xyz']})")
                    
                    hx, hy, htxt = [], [], []
                    for (rx, ry), texts in hover_data.items():
                        cx = ry + pp_d/2 if is_vertical else rx + l_modulo/2
                        cy = rx + l_modulo/2 if is_vertical else ry + pp_d/2
                        hx.append(cx); hy.append(cy); htxt.append("<br>".join(texts))
                    
                    if hx:
                        fig.add_trace(go.Scatter(x=hx, y=hy, mode='markers', marker=dict(size=18, color='rgba(0,0,0,0)'), text=htxt, hoverinfo='text', showlegend=False))

                    for st in staging:
                        fig.add_shape(type="rect", x0=st['x1'], y0=st['y1'], x1=st['x2'], y1=st['y2'], fillcolor="rgba(241,196,15,0.25)", line=dict(color="#f39c12", width=1.5, dash="dash"))
                        fig.add_annotation(x=(st['x1']+st['x2'])/2, y=(st['y1']+st['y2'])/2, text="<b>STAGING</b>", showarrow=False, font=dict(size=9, color="#d35400"))

                    for ofi in oficinas:
                        ox, oy, ow, od = ofi['x'], ofi['y'], ofi['w'], ofi['d']
                        fig.add_shape(type="rect", x0=ox, y0=oy, x1=ox+ow, y1=oy+od, fillcolor="#bdc3c7", line=dict(color="#7f8c8d", width=2))
                        fig.add_annotation(x=ox+ow/2, y=oy+od/2, text="<b>🏢 OFICINA</b>", showarrow=False, font=dict(size=12, color="#2c3e50"))

                    puertas = []
                    if w_puerta > 0 and tipo_flujo_str != 'Ninguno':
                        if 'Flujo en U' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': (l_m*0.25)-(w_puerta/2), 'w': w_puerta}, {'pared': 'S', 'pos': (l_m*0.75)-(w_puerta/2), 'w': w_puerta}])
                        elif 'Flujo en I' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta}, {'pared': 'N', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta}])
                        elif 'Flujo en L' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': max(1, (l_m*0.15)-(w_puerta/2)), 'w': w_puerta}, {'pared': 'E', 'pos': max(1, (a_m*0.85)-(w_puerta/2)), 'w': w_puerta}])

                    if cant_norte > 0 and w_norte > 0: puertas.extend([{'pared': 'N', 'pos': (i*(l_m/(cant_norte+1)))-(w_norte/2), 'w': w_norte} for i in range(1, cant_norte+1)])
                    if cant_sur > 0 and w_sur > 0: puertas.extend([{'pared': 'S', 'pos': (i*(l_m/(cant_sur+1)))-(w_sur/2), 'w': w_sur} for i in range(1, cant_sur+1)])
                    if cant_este > 0 and w_este > 0: puertas.extend([{'pared': 'E', 'pos': (i*(a_m/(cant_este+1)))-(w_este/2), 'w': w_este} for i in range(1, cant_este+1)])
                    if cant_oeste > 0 and w_oeste > 0: puertas.extend([{'pared': 'O', 'pos': (i*(a_m/(cant_oeste+1)))-(w_oeste/2), 'w': w_oeste} for i in range(1, cant_oeste+1)])

                    for p in puertas:
                        pared, pos, w = p['pared'], p['pos'], p['w']
                        if pared == 'S': x0, y0, x1, y1 = pos, 0, pos+w, 1.5
                        elif pared == 'N': x0, y0, x1, y1 = pos, a_m-1.5, pos+w, a_m
                        elif pared == 'E': x0, y0, x1, y1 = l_m-1.5, pos, l_m, pos+w
                        elif pared == 'O': x0, y0, x1, y1 = 0, pos, 1.5, pos+w
                        else: continue
                        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor="#f1c40f", line=dict(color="#f39c12", width=2))

                    util = (pallets_ubicados_totales / capacidad_total_slots * 100) if capacidad_total_slots > 0 else 0
                    t_abc = f" | Clases: {','.join(clases_abc)}" if len(clases_abc) < 3 else ""
                    estado_filtro = "<b style='color:#e67e22;'>[FOCO ACTIVO]</b><br>" if skus_buscados else ""
                    tit_text = f"{estado_filtro}<b>Plano 2D Interactivo</b><br><sup>Slots: {capacidad_total_slots} | Ubicados: {pallets_ubicados_totales} ({util:.1f}%) {t_abc}</sup>"
                    
                    fig.update_layout(title=dict(text=tit_text, x=0.5, font=dict(size=16)), xaxis=dict(title="Largo (m)", range=[-3, l_m + 3], zeroline=False, gridcolor='#ecf0f1'), yaxis=dict(title="Ancho (m)", range=[-3, a_m + 3], zeroline=False, scaleanchor="x", scaleratio=1, gridcolor='#ecf0f1'), width=1000, height=700, plot_bgcolor="#ffffff", margin=dict(r=20, l=20, b=40, t=100))
                    
                    if not skus_buscados: 
                        if '9 Zonas' in modo_vista: fig.add_annotation(x=l_m, y=a_m+1.5, text="<b>AX-AZ</b> (Rojos) | <b>BX-BZ</b> (Naranjas) | <b>CX-CZ</b> (Azules)", showarrow=False, font=dict(size=11), xanchor='right')
                        else: fig.add_annotation(x=l_m, y=a_m+1.5, text="<b>A</b> (Rojo) | <b>B</b> (Naranja) | <b>C</b> (Azul)", showarrow=False, font=dict(size=11), xanchor='right')

                    display(go.FigureWidget(fig))

                except Exception as e_2d:
                    print(f"❌ Error dibujando 2D:")
                    traceback.print_exc()

        def render_3d(raw_input, modo_vista):
            with out_3d:
                clear_output(wait=True)
                try:
                    display(HTML("<div style='padding:15px; border-radius:8px; background:#e8f8f5; border:1px solid #1abc9c; color:#16a085; text-align:center;'><b>⏳ Levantando Maqueta 3D... Por favor espera.</b></div>"))
                    
                    skus_buscados = set(s.strip().upper() for s in re.split(r'[,\s;]+', raw_input) if s.strip())

                    class MallaAgrupada:
                        def __init__(self, color, nombre, opacidad=1.0):
                            self.color, self.nombre, self.opacidad = color, nombre, opacidad
                            self.x, self.y, self.z, self.i, self.j, self.k, self.text = [], [], [], [], [], [], []
                            self.contador = 0
                            self.base_i, self.base_j, self.base_k = [7,0,0,0,4,4,6,6,4,0,3,2], [3,4,1,2,5,6,5,2,0,1,6,3], [0,7,2,3,6,7,1,1,5,5,7,6]
                        def agregar_cubo(self, x0, y0, z0, dx, dy, dz, hover_txt=None):
                            off = self.contador * 8
                            self.x.extend([x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0])
                            self.y.extend([y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy])
                            self.z.extend([z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz])
                            self.i.extend([idx + off for idx in self.base_i])
                            self.j.extend([idx + off for idx in self.base_j])
                            self.k.extend([idx + off for idx in self.base_k])
                            if hover_txt: self.text.extend([hover_txt] * 8)
                            self.contador += 1
                        def obtener_trazo(self):
                            if self.contador == 0: return None
                            params = dict(x=self.x, y=self.y, z=self.z, i=self.i, j=self.j, k=self.k, color=self.color, opacity=self.opacidad, name=self.nombre, showscale=False, flatshading=True)
                            if self.text: params['text'], params['hoverinfo'] = self.text, "text"
                            else: params['hoverinfo'] = "name"
                            return go.Mesh3d(**params)

                    def add_cube_rotated(capa, x0, y0, z0, dx, dy, dz, hover_txt=None):
                        if is_vertical: capa.agregar_cubo(y0, x0, z0, dy, dx, dz, hover_txt)
                        else: capa.agregar_cubo(x0, y0, z0, dx, dy, dz, hover_txt)

                    capa_pilares = MallaAgrupada('#e74c3c', 'Pilares CD')
                    capa_oficinas = MallaAgrupada('#bdc3c7', 'Oficinas', 0.9)
                    capa_staging = MallaAgrupada('#f39c12', 'Staging', 0.4)
                    capa_marcos = MallaAgrupada('#2c3e50', 'Estructura Rack', 1.0)
                    capa_marcos_bloqueados = MallaAgrupada('#7f8c8d', 'Rack Inutilizable', 0.4)
                    capa_vigas = MallaAgrupada('#e67e22', 'Vigas', 1.0)
                    
                    capa_maderas = MallaAgrupada('#d35400', 'Pallet Base', 1.0)
                    capa_maderas_apagadas = MallaAgrupada('#bdc3c7', 'Pallet Oculto', 0.1)
                    
                    cajas = {'Destacado': MallaAgrupada('#2ecc71', 'SKU Buscado', 1.0), 'Apagado': MallaAgrupada('#ecf0f1', 'Oculto', 0.1)}
                    
                    if '9 Zonas' in modo_vista:
                        for k, color in dict_color_abcxyz.items(): cajas[k] = MallaAgrupada(color, f'Clase {k}')
                    else:
                        for k, color in dict_color_abc.items(): cajas[k] = MallaAgrupada(color, f'Clase {k}')

                    for px, py in pilares_reales:
                        if px < l_m and py < a_m: capa_pilares.agregar_cubo(px - 0.25, py - 0.25, 0, 0.5, 0.5, alt_m)
                    for ofi in oficinas:
                        capa_oficinas.agregar_cubo(ofi['x'], ofi['y'], 0, ofi['w'], ofi['d'], ofi.get('h', 3.5))
                    for st in staging:
                        capa_staging.agregar_cubo(st['x1'], st['y1'], 0.01, st['x2'] - st['x1'], st['y2'] - st['y1'], 0.02)

                    t = t_marco
                    altura_marcos_total = niveles_operativos * alt_nivel_viga if niveles_operativos > 0 else alt_nivel_viga

                    for mod in modulos:
                        x_pos, y_rack = mod['x'], mod['y']
                        capa_activa = capa_marcos_bloqueados if mod['bloqueado'] else capa_marcos

                        add_cube_rotated(capa_activa, x_pos, y_rack, 0, t, pp_d, t)
                        add_cube_rotated(capa_activa, x_pos, y_rack, 0, t, t, altura_marcos_total)
                        add_cube_rotated(capa_activa, x_pos, y_rack + pp_d - t, 0, t, t, altura_marcos_total)
                        add_cube_rotated(capa_activa, x_pos + l_modulo - t, y_rack, 0, t, t, altura_marcos_total)
                        add_cube_rotated(capa_activa, x_pos + l_modulo - t, y_rack + pp_d - t, 0, t, t, altura_marcos_total)
                        add_cube_rotated(capa_activa, x_pos, y_rack, altura_marcos_total, l_modulo, pp_d, 0.05)

                        viga_activa = capa_marcos_bloqueados if mod['bloqueado'] else capa_vigas
                        for n_viga in range(1, niveles_operativos):
                            z_viga = n_viga * alt_nivel_viga - viga_h
                            add_cube_rotated(viga_activa, x_pos + t, y_rack, z_viga, l_modulo - 2*t, t/2, viga_h)
                            add_cube_rotated(viga_activa, x_pos + t, y_rack + pp_d - t/2, z_viga, l_modulo - 2*t, t/2, viga_h)

                    for slot in almacen:
                        if slot['ocupado']:
                            alt_carga = slot['alt_p'] - 0.12
                            txt_hover = f"Pos: {slot['id_posicion']}<br>SKU: {slot['sku']}<br>ABC-XYZ: {slot['abc_xyz']}"
                            
                            if skus_buscados:
                                if slot['sku'] in skus_buscados:
                                    capa_caja, capa_madera = cajas['Destacado'], capa_maderas
                                else:
                                    capa_caja, capa_madera = cajas['Apagado'], capa_maderas_apagadas
                            else:
                                capa_madera = capa_maderas
                                if '9 Zonas' in modo_vista:
                                    capa_caja = cajas.get(slot['abc_xyz'], cajas.get('CZ'))
                                else:
                                    capa_caja = cajas.get(slot['abc'], cajas.get('C'))
                                
                            add_cube_rotated(capa_madera, slot['x_pal'], slot['y'] + 0.05, slot['z'] + 0.02, ap_w, pp_d - 0.1, 0.12)
                            add_cube_rotated(capa_caja, slot['x_pal'] + 0.05, slot['y'] + 0.1, slot['z'] + 0.14, ap_w - 0.1, pp_d - 0.2, alt_carga, txt_hover)

                    c_puertas_cortina = MallaAgrupada('#f1c40f', 'Cortina', 0.4)
                    c_puertas_marcos = MallaAgrupada('#f39c12', 'Marco', 1.0)
                    alt_puerta = 4.5
                    puertas = []
                    if w_puerta > 0 and tipo_flujo_str != 'Ninguno':
                        if 'Flujo en U' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': (l_m*0.25)-(w_puerta/2), 'w': w_puerta}, {'pared': 'S', 'pos': (l_m*0.75)-(w_puerta/2), 'w': w_puerta}])
                        elif 'Flujo en I' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta}, {'pared': 'N', 'pos': (l_m/2)-(w_puerta/2), 'w': w_puerta}])
                        elif 'Flujo en L' in tipo_flujo_str: puertas.extend([{'pared': 'S', 'pos': max(1, (l_m*0.15)-(w_puerta/2)), 'w': w_puerta}, {'pared': 'E', 'pos': max(1, (a_m*0.85)-(w_puerta/2)), 'w': w_puerta}])

                    if cant_norte > 0 and w_norte > 0: puertas.extend([{'pared': 'N', 'pos': (i*(l_m/(cant_norte+1)))-(w_norte/2), 'w': w_norte} for i in range(1, cant_norte+1)])
                    if cant_sur > 0 and w_sur > 0: puertas.extend([{'pared': 'S', 'pos': (i*(l_m/(cant_sur+1)))-(w_sur/2), 'w': w_sur} for i in range(1, cant_sur+1)])
                    if cant_este > 0 and w_este > 0: puertas.extend([{'pared': 'E', 'pos': (i*(a_m/(cant_este+1)))-(w_este/2), 'w': w_este} for i in range(1, cant_este+1)])
                    if cant_oeste > 0 and w_oeste > 0: puertas.extend([{'pared': 'O', 'pos': (i*(a_m/(cant_oeste+1)))-(w_oeste/2), 'w': w_oeste} for i in range(1, cant_oeste+1)])

                    for p in puertas:
                        pared, pos, w = p['pared'], p['pos'], p['w']
                        if pared == 'S':
                            c_puertas_cortina.agregar_cubo(pos, 0.1, 0, w, 0.1, alt_puerta)
                            c_puertas_marcos.agregar_cubo(pos, 0, 0, 0.2, 0.3, alt_puerta); c_puertas_marcos.agregar_cubo(pos+w-0.2, 0, 0, 0.2, 0.3, alt_puerta); c_puertas_marcos.agregar_cubo(pos, 0, alt_puerta, w, 0.3, 0.4)
                        elif pared == 'N':
                            c_puertas_cortina.agregar_cubo(pos, a_m-0.2, 0, w, 0.1, alt_puerta)
                            c_puertas_marcos.agregar_cubo(pos, a_m-0.3, 0, 0.2, 0.3, alt_puerta); c_puertas_marcos.agregar_cubo(pos+w-0.2, a_m-0.3, 0, 0.2, 0.3, alt_puerta); c_puertas_marcos.agregar_cubo(pos, a_m-0.3, alt_puerta, w, 0.3, 0.4)
                        elif pared == 'E':
                            c_puertas_cortina.agregar_cubo(l_m-0.2, pos, 0, 0.1, w, alt_puerta)
                            c_puertas_marcos.agregar_cubo(l_m-0.3, pos, 0, 0.3, 0.2, alt_puerta); c_puertas_marcos.agregar_cubo(l_m-0.3, pos+w-0.2, 0, 0.3, 0.2, alt_puerta); c_puertas_marcos.agregar_cubo(l_m-0.3, pos, alt_puerta, 0.3, w, 0.4)
                        elif pared == 'O':
                            c_puertas_cortina.agregar_cubo(0.1, pos, 0, 0.1, w, alt_puerta)
                            c_puertas_marcos.agregar_cubo(0, pos, 0, 0.3, 0.2, alt_puerta); c_puertas_marcos.agregar_cubo(0, pos+w-0.2, 0, 0.3, 0.2, alt_puerta); c_puertas_marcos.agregar_cubo(0, pos, alt_puerta, 0.3, w, 0.4)

                    fig_3d = go.Figure()
                    fig_3d.add_trace(go.Mesh3d(x=[0, l_m, l_m, 0, 0, l_m, l_m, 0], y=[0, 0, a_m, a_m, 0, 0, a_m, a_m], z=[-0.1, -0.1, -0.1, -0.1, 0, 0, 0, 0], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='#bdc3c7', showscale=False, name='Suelo'))

                    for c in [capa_pilares, capa_oficinas, capa_staging, capa_marcos, capa_marcos_bloqueados, capa_vigas, capa_maderas, capa_maderas_apagadas] + list(cajas.values()) + [c_puertas_cortina, c_puertas_marcos]:
                        trace = c.obtener_trazo()
                        if trace: fig_3d.add_trace(trace)
                    
                    estado_filtro = "<b style='color:#e67e22;'>[FOCO ACTIVO]</b><br>" if skus_buscados else ""
                    fig_3d.update_layout(title=dict(text=f"{estado_filtro}<b>Gemelo Digital 3D | Hover Interactivo</b><br><sup>Ubicados: {pallets_ubicados_totales}</sup>", x=0.5, font=dict(size=16)), scene=dict(xaxis=dict(title='Largo X (m)', range=[-5, l_m + 5], backgroundcolor="white"), yaxis=dict(title='Ancho Y (m)', range=[-5, a_m + 5], backgroundcolor="white"), zaxis=dict(title='Alto Z (m)', range=[0, max(10, alt_m + 1)], backgroundcolor="white"), aspectmode='data', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))), margin=dict(r=0, l=0, b=0, t=100), height=750, paper_bgcolor='white', showlegend=False)
                    
                    clear_output(wait=True)
                    display(go.FigureWidget(fig_3d))

                except Exception as e_3d:
                    print(f"❌ Error construyendo 3D:")
                    traceback.print_exc()

        btn_2d.on_click(lambda b: render_2d(search_foco.value, vista_dropdown.value))
        btn_3d.on_click(lambda b: render_3d(search_foco.value, vista_dropdown.value))
        vista_dropdown.observe(lambda change: render_2d(search_foco.value, change.new) if change.name == 'value' else None)

        render_2d("", vista_dropdown.value)
        
    except Exception as e:
        display(HTML(f"<div style='background:#fef2f2; padding:15px; border:1px solid #991b1b; border-radius:8px;'><b style='color:#991b1b; font-size:14px;'>❌ Error general en la celda:</b><br><span style='color:#333;'>{str(e)}</span></div>"))
