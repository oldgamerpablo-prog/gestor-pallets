import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import re
import unicodedata
import io

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(page_title="WMS Analytics: Paletizado", layout="wide", page_icon="📦")

MAX_PESO_PALLET = 1200
PESO_MADERA_PALLET = 25

# ============================================================
# UTILIDADES Y DETECCIÓN
# ============================================================
def norm_txt(valor):
    texto = "" if valor is None else str(valor)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().strip()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto)).strip()

def es_numero(valor):
    try: return pd.notna(valor) and math.isfinite(float(valor))
    except Exception: return False

def a_float(valor, default=np.nan):
    try: return float(valor) if pd.notna(valor) else default
    except Exception: return default

def encontrar_columna(columnas, incluir, excluir=()):
    for col in columnas:
        n = norm_txt(col)
        if all(p in n for p in incluir) and not any(p in n for p in excluir): return col
    return None

def detectar_columnas(df):
    cols = list(df.columns)
    normalizados = {c: norm_txt(c) for c in cols}
    mapa = {}
    mapa["sku"] = encontrar_columna(cols, ["codigo", "producto"]) or encontrar_columna(cols, ["sku"]) or encontrar_columna(cols, ["codigo"])
    mapa["stock"] = encontrar_columna(cols, ["stock", "promedio"])
    mapa["peso"] = me = encontrar_columna(cols, ["peso"], ["total", "pallet"])
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
    mapa["altura_total"] = encontrar_columna(cols, ["altura", "total", "pallet"]) or me or encontrar_columna(cols, ["altura", "paletizada"])
    return mapa

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
                if total > mejor["cantidad"]:
                    mejor = {"cantidad": total, "filas": ([opciones[0]] * n_normal) + ([opciones[1]] * n_cruzada)}
    cajas = []
    y = 0.0
    for fila in mejor["filas"]:
        cantidad = int(math.floor(largo_pallet / fila["largo"]))
        for i in range(cantidad):
            cajas.append({"x": i * fila["largo"], "y": y, "largo": fila["largo"], "ancho": fila["ancho"]})
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

    capacidad_optima = int(unidades_nivel * niveles_optimos)

    return pd.Series({
        "Capacidad_Excel": capacidad_base,
        "Capacidad_Optima": capacidad_optima,
        "Unidades_Por_Nivel": unidades_nivel,
        "Niveles_Optimos": niveles_optimos
    })

def calcular_metricas_dinamicas(fila, mapa, modo="EXCEL"):
    stock = a_float(valor_col(fila, "stock", mapa), 0)
    cap_excel = a_float(fila.get("Capacidad_Excel"), 0)
    cap_optima = int(fila.get("Capacidad_Optima", 0))
    peso_unitario = a_float(valor_col(fila, "peso", mapa))
    largo, ancho, alto = a_float(valor_col(fila, "largo", mapa)), a_float(valor_col(fila, "ancho", mapa)), a_float(valor_col(fila, "alto", mapa))
    largo_pallet, ancho_pallet, altura_pallet = a_float(valor_col(fila, "largo_pallet", mapa), 120), a_float(valor_col(fila, "ancho_pallet", mapa), 120), a_float(valor_col(fila, "altura_pallet", mapa), 15)
    altura_total = a_float(valor_col(fila, "altura_total", mapa))

    if modo == "OPTIMO":
        cap_usada = cap_optima if cap_optima > 0 else int(round(cap_excel)) if es_numero(cap_excel) else 0
        metodo = "MOTOR ÓPTIMO"
    else:
        cap_usada = int(round(cap_excel)) if (es_numero(cap_excel) and cap_excel > 0) else cap_optima
        metodo = "BASE EXCEL"

    pallets = int(math.ceil(stock / cap_usada)) if stock > 0 and cap_usada > 0 else 0
    ult_unids = (stock - (pallets - 1) * cap_usada) if pallets > 0 else 0
    if ult_unids == 0 and stock > 0: ult_unids = cap_usada
    ult_pct = (ult_unids / cap_usada * 100) if cap_usada > 0 else 0

    peso_pallet = (cap_usada * peso_unitario) + PESO_MADERA_PALLET if es_numero(peso_unitario) else np.nan
    vol_prod = (largo * ancho * alto * cap_usada) if all(es_numero(v) for v in [largo, ancho, alto]) else np.nan
    vol_pallet = (largo_pallet * ancho_pallet * (altura_total - altura_pallet)) if all(es_numero(v) for v in [largo_pallet, ancho_pallet, altura_total, altura_pallet]) else np.nan
    efi_vol = (vol_prod / vol_pallet * 100) if es_numero(vol_prod) and es_numero(vol_pallet) and vol_pallet > 0 else np.nan

    estado = "OK"
    if stock <= 0: estado = "SIN STOCK"
    elif cap_usada <= 0: estado = "SIN CAPACIDAD"
    elif es_numero(peso_pallet) and peso_pallet > MAX_PESO_PALLET: estado = "SOBREPESO (>1200kg)"
    
    return {
        "Capacidad_Usada": cap_usada, "Metodo": metodo, "Pallets": pallets,
        "Unidades_Ultimo": ult_unids, "Ocupacion_Ultimo": ult_pct,
        "Peso_Pallet": peso_pallet, "Eficiencia_Volumen": efi_vol,
        "Estado": estado, "Cap_Excel": cap_excel, "Cap_Optima": cap_optima
    }

def generar_excel_descarga(df_original, df_resultados, mapa):
    output = io.BytesIO()
    comparativo_rows = []
    
    for _, row in df_resultados.iterrows():
        m_excel = calcular_metricas_dinamicas(row, mapa, modo="EXCEL")
        m_opt = calcular_metricas_dinamicas(row, mapa, modo="OPTIMO")
        comparativo_rows.append({
            "SKU": row[mapa["sku"]],
            "Stock": row[mapa["stock"]],
            "Capacidad_Excel": m_excel["Cap_Excel"],
            "Capacidad_Optima": m_opt["Cap_Optima"],
            "Pallets_Req_Excel": m_excel["Pallets"],
            "Pallets_Req_Optimo": m_opt["Pallets"]
        })
        
    df_sheet1 = pd.DataFrame(comparativo_rows)
    df_sheet2 = df_original.copy()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sheet1.to_excel(writer, sheet_name="1_Analisis_Comparativo", index=False)
        df_sheet2.to_excel(writer, sheet_name="2_Data_Original", index=False)
        df_resultados.to_excel(writer, sheet_name="3_Data_Optimizada", index=False)
        
    output.seek(0)
    return output

# ============================================================
# INTERFAZ DE USUARIO (STREAMLIT)
# ============================================================
st.title("📊 WMS Analytics: Dashboard de Paletización Masiva")

# 1. Cargar el archivo
archivo_subido = st.file_uploader("📂 Sube tu archivo Excel con la base de datos (Ej: cubicadora pablo.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # Leer datos
    with st.spinner("Procesando base de datos..."):
        try:
            df_original = pd.read_excel(archivo_subido, sheet_name="Data Equipo 7")
        except:
            df_original = pd.read_excel(archivo_subido, sheet_name=0)
            
        df_original = df_original.dropna(how="all").reset_index(drop=True)
        MAPA = detectar_columnas(df_original)
        
        df_trabajo = df_original.copy()
        df_trabajo[MAPA["sku"]] = df_trabajo[MAPA["sku"]].astype(str).str.strip()

        precalculos = df_trabajo.apply(lambda fila: precalcular_fila(fila, MAPA), axis=1)
        df_resultados = pd.concat([df_trabajo, precalculos], axis=1)

    st.success("✅ Base de datos procesada con éxito.")

    # Estado del sistema
    modo = st.radio("⚙️ Selecciona el modo de cálculo:", ["EXCEL", "OPTIMO"], horizontal=True)
    
    tot_p = sum([calcular_metricas_dinamicas(row, MAPA, modo)["Pallets"] for _, row in df_resultados.iterrows()])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total SKU Analizados", len(df_resultados))
    col2.metric("🟢 SKUs con Stock", int((pd.to_numeric(df_resultados[MAPA["stock"]], errors="coerce").fillna(0) > 0).sum()))
    col3.metric("🏗️ Pallets Totales Requeridos", f"{tot_p:,}")

    st.markdown("---")

    col_busq, col_rep = st.columns([2, 1])
    
    with col_busq:
        st.subheader("🔍 Buscar SKU Específico")
        sku_buscado = st.text_input("Ingresa un código SKU para ver su detalle:")
        if st.button("Buscar") and sku_buscado:
            filtro = df_resultados[df_resultados[MAPA["sku"]].astype(str).str.upper() == sku_buscado.upper()]
            if not filtro.empty:
                fila = filtro.iloc[0]
                m = calcular_metricas_dinamicas(fila, MAPA, modo)
                st.info(f"**Estado:** {m['Estado']} | **Capacidad Pallet:** {m['Capacidad_Usada']} u. | **Último Pallet:** {m['Ocupacion_Ultimo']:.1f}%")
                st.dataframe(pd.DataFrame([m]))
            else:
                st.error("SKU no encontrado.")
                
    with col_rep:
        st.subheader("📥 Descargar Reporte")
        st.write("Genera el Excel completo con 3 hojas.")
        excel_data = generar_excel_descarga(df_original, df_resultados, MAPA)
        st.download_button(
            label="📊 Descargar Reporte Excel",
            data=excel_data,
            file_name="Reporte_Paletizacion_Optimizado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("👆 Por favor, sube tu archivo Excel en la parte superior para comenzar.")
