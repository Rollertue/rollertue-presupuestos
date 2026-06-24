import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import io
import json  

# CONFIGURACIÓN ESTÉTICA DE LA APP
st.set_page_config(page_title="Rollertue Comercial Cloud", layout="wide")
st.title("📐 Sistema de Cotización y Presupuestos - Rollertue")
st.caption("Módulo Avanzado: Persistencia de Costos en la Nube e Historial Cloud")
st.markdown("---")

# =========================================================
# 1. CONEXIÓN SEGURA A SUPABASE
# =========================================================
@st.cache_resource
def iniciar_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = iniciar_supabase()
except Exception as e:
    st.error(f"Error de conexión Cloud: {e}")

# =========================================================
# 2. CARGA DINÁMICA DE COSTOS DESDE SUPABASE
# =========================================================
def cargar_precios_insumos():
    try:
        res = supabase.table("config_insumos").select("valores").eq("id", "lista_precios").execute()
        if res.data and "valores" in res.data[0]:
            return res.data[0]["valores"]
    except:
        pass
    # Valores de respaldo por si falla la red
    return {
        "BO 520": 5.00, "SS OPTIMA 5%": 5.50, "ECO BOH": 0.00,
        "Caño 32": 3.33, "Caño 38": 4.33, "Caño 32 Ref": 3.33,
        "Zócalo DAVID": 4.10, "Zócalo SS": 4.10,
        "CINTA": 0.30, "FIDEO": 0.30, "Fleje": 0.13,
        "Mecanismo J32": 2.78, "Mecanismo J38": 3.39,
        "Soporte DAVID J32 DOBLE": 5.75, "Soporte J38 DOBLE": 6.19,
        "CONTRAPESO CADENA": 0.30, "CADENA PLÁSTICA": 0.30,     
        "ACCESORIOS CADENA": 0.18, "FLETE": 2.50
    }

# Inicializar precios en el estado de sesión si no existen
if 'precios_insumos' not in st.session_state:
    st.session_state['precios_insumos'] = cargar_precios_insumos()

# Persistencia de variables globales básicas
if 'dolar' not in st.session_state:
    st.session_state['dolar'] = 1570.0  
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = []

# Estados de inputs para recuperador de presupuestos
if 'edit_cliente' not in st.session_state:
    st.session_state['edit_cliente'] = ""
if 'edit_nro' not in st.session_state:
    st.session_state['edit_nro'] = 160
if 'edit_ver' not in st.session_state:
    st.session_state['edit_ver'] = 1

# Márgenes comerciales base
if 'margen_rentabilidad' not in st.session_state:
    st.session_state['margen_rentabilidad'] = 110.0  
if 'componente_financiero' not in st.session_state:
    st.session_state['componente_financiero'] = 85.0  
if 'desc_3_cuotas' not in st.session_state:
    st.session_state['desc_3_cuotas'] = 30.0  
if 'desc_tarjeta' not in st.session_state:
    st.session_state['desc_tarjeta'] = 35.0  
if 'desc_efectivo' not in st.session_state:
    st.session_state['desc_efectivo'] = 40.0  

# Servicios de logística e instalación
if 'toma_medidas' not in st.session_state:
    st.session_state['toma_medidas'] = 25000.0
if 'inst_jdla_1ra' not in st.session_state:
    st.session_state['inst_jdla_1ra'] = 35000.0
if 'inst_sma_1ra' not in st.session_state:
    st.session_state['inst_sma_1ra'] = 50000.0
if 'inst_adicional' not in st.session_state:
    st.session_state['inst_adicional'] = 20000.0

# DISEÑO DE INTERFAZ POR PESTAÑAS
tab_cotizador, tab_config, tab_historial_cloud = st.tabs([
    "🧮 Panel de Cotización", 
    "⚙️ Configuración Financiera y Costos", 
    "🌐 Historial de Presupuestos Cloud"
])

# =========================================================
# PESTAÑA: PANEL DE COTIZACIÓN
# =========================================================
with tab_cotizador:
    st.header("📋 Generador de Presupuestos")
    col_in, col_out = st.columns([1.3, 1.7])
    
    with col_in:
        st.subheader("🛠️ Parámetros de la Orden")
        c_p1, c_p2, c_p3 = st.columns([1.5, 1, 1])
        with c_p1:
            cliente_global = st.text_input("Cliente:", value=st.session_state['edit_cliente'], placeholder="Ej. Juan Pérez")
        with c_p2:
            nro_presupuesto = st.number_input("N° Presupuesto:", min_value=160, value=st.session_state['edit_nro'], step=1)
        with c_p3:
            version_presupuesto = st.number_input("Versión V:", min_value=1, value=st.session_state['edit_ver'], step=1)
            
        st.markdown("**Servicio de Instalación y Medición**")
        c_inst1, c_inst2 = st.columns(2)
        with c_inst1:
            lugar_instalacion = st.selectbox("Lugar de Instalación:", ["Ninguna / Retira de Fábrica", "JDLA (Junín de los Andes)", "SMA (San Martín de los Andes)"])
        with c_inst2:
            aplica_toma_medidas = st.checkbox("¿Descontar Toma de Medidas?", value=False)

        st.markdown("---")
        st.markdown("**Configurar Cortina**")
        ancho_cm = st.number_input("Ancho de la Cortina (en cm)", min_value=10.0, value=150.0, step=1.0)
        alto_cm = st.number_input("Alto de la Cortina (en cm)", min_value=10.0, value=200.0, step=1.0)
        tipo_tela = st.selectbox("Seleccionar Tela:", ["BO 520", "SS OPTIMA 5%", "ECO BOH"])
        tipo_zocalo = st.selectbox("Seleccionar Perfil Zócalo:", ["Zócalo DAVID", "Zócalo SS"])
        es_doble = st.checkbox("¿Es Cortina DOBLE?", value=False)
        cantidad = st.number_input("Cantidad de este ítem:", min_value=1, value=1, step=1)
        
        # --- MOTOR MATEMÁTICO ---
        ancho_m = ancho_cm / 100.0
        alto_m = alto_cm / 100.0
        alto_excedente_m = alto_m + 0.15
        multiplicador = 2 if es_doble else 1
        f_desp = 1.05
        
        if ancho_cm <= 169.0:
            n_cano, n_mec, n_sop_d = "Caño 32", "Mecanismo J32", "Soporte DAVID J32 DOBLE"
        else:
            n_cano, n_mec, n_sop_d = "Caño 38", "Mecanismo J38", "Soporte J38 DOBLE"
            
        p_i = st.session_state['precios_insumos']
        t_c = st.session_state['dolar']
        
        cant_tela_m2 = (ancho_m * alto_excedente_m) * f_desp * multiplicador
        cant_cano_ml = ancho_m * f_desp * multiplicador
        cant_zocalo_ml = ancho_m * f_desp * multiplicador
        
        costo_unitario_usd = (
            (cant_tela_m2 * p_i[tipo_tela]) +  
            (cant_cano_ml * p_i[n_cano]) +                         
            (cant_zocalo_ml * p_i[tipo_zocalo]) +                    
            (((ancho_m * 2) * multiplicador) * p_i["CINTA"]) +                           
            ((ancho_m * multiplicador) * p_i["FIDEO"]) +                                 
            ((ancho_m * f_desp * multiplicador) * p_i["Fleje"]) +                        
            ((1 * multiplicador) * p_i[n_mec]) +                                         
            ((4.0 * multiplicador) * p_i["CADENA PLÁSTICA"]) +                           
            ((1 * multiplicador) * p_i["CONTRAPESO CADENA"]) +  
            ((1 * multiplicador) * p_i["ACCESORIOS CADENA"]) +                           
            ((1 * multiplicador) * p_i["FLETE"])                                         
        )
        if es_doble:
            costo_unitario_usd += (1.0 * p_i[n_sop_d])
            
        costo_unitario_ars = costo_unitario_usd * t_c
        precio_venta_neto = costo_unitario_ars * (1 + (st.session_state['margen_rentabilidad'] / 100))
        precio_lista_bruto = precio_venta_neto * (1 + (st.session_state['componente_financiero'] / 100))
        precio_lista_unitario_fijo = round(precio_lista_bruto / 100) * 100
        precio_lista_total_item = precio_lista_unitario_fijo * float(cantidad)

        st.markdown("#### 🔍 Despiece Unitario de Control")
        desglose_auditoria = [
            {"Componente": f"Tela: {tipo_tela}", "Cantidad": cant_tela_m2, "Subtotal USD": cant_tela_m2 * p_i[tipo_tela]},
            {"Componente": f"Estructura: {n_cano}", "Cantidad": cant_cano_ml, "Subtotal USD": cant_cano_ml * p_i[n_cano]},
            {"Componente": f"Terminación: {tipo_zocalo}", "Cantidad": cant_zocalo_ml, "Subtotal USD": cant_zocalo_ml * p_i[tipo_zocalo]},
            {"Componente": "Cinta Doble Faz", "Cantidad": (ancho_m * 2) * multiplicador, "Subtotal USD": ((ancho_m * 2) * multiplicador) * p_i["CINTA"]},
            {"Componente": "Fideo de Agarre", "Cantidad": ancho_m * multiplicador, "Subtotal USD": (ancho_m * multiplicador) * p_i["FIDEO"]},
            {"Componente": "Fleje de Peso", "Cantidad": ancho_m * f_desp * multiplicador, "Subtotal USD": (ancho_m * f_desp * multiplicador) * p_i["Fleje"]},
            {"Componente": f"Sistema: {n_mec}", "Cantidad": float(1 * multiplicador), "Subtotal USD": float(1 * multiplicador) * p_i[n_mec]},
            {"Componente": "Cadena de Mando", "Cantidad": float(4.0 * multiplicador), "Subtotal USD": float(4.0 * multiplicador) * p_i["CADENA PLÁSTICA"]},
            {"Componente": "Contrapeso Cadena", "Cantidad": float(1 * multiplicador), "Subtotal USD": float(1 * multiplicador) * p_i["CONTRAPESO CADENA"]},
            {"Componente": "Flete Logístico", "Cantidad": float(1 * multiplicador), "Subtotal USD": float(1 * multiplicador) * p_i["FLETE"]}
        ]
        df_vis = pd.DataFrame(desglose_auditoria)
        df_vis["Subtotal ARS"] = df_vis["Subtotal USD"] * t_c
        st.dataframe(df_vis[["Componente", "Cantidad", "Subtotal USD", "Subtotal ARS"]], use_container_width=True, hide_index=True)
        
        if st.button("➕ Agregar Ítem al Presupuesto", type="primary", use_container_width=True):
            detalle_nombre = f"Cortina {tipo_tela} ({'Doble' if es_doble else 'Simple'}) - {ancho_cm:.0f}x{alto_cm:.0f}cm"
            st.session_state['carrito'].append({
                "Detalle Producto": detalle_nombre,
                "Cantidad": int(cantidad),
                "Precio Lista Unit. ($)": precio_lista_unitario_fijo,
                "Precio Lista Total ($)": precio_lista_total_item
            })
            st.rerun()

    with col_out:
        st.subheader("🛒 Estructura del Presupuesto Actual")
        if len(st.session_state['carrito']) > 0:
            for idx, item in enumerate(st.session_state['carrito']):
                c_det, c_cant, c_p_lista, c_btn = st.columns([3, 1, 1.5, 1])
                c_det.write(f"**{item['Detalle Producto']}**")
                c_cant.write(f"Cant: {item['Cantidad']}")
                c_p_lista.write(f"Lista: $ {item['Precio Lista Total ($)']:,.0f}")
                if c_btn.button("🗑️", key=f"del_{idx}"):
                    st.session_state['carrito'].pop(idx)
                    st.rerun()
            
            st.markdown("---")
            df_carrito = pd.DataFrame(st.session_state['carrito'])
            gran_total_lista = df_carrito["Precio Lista Total ($)"].sum()
            total_unidades_cortinas = df_carrito["Cantidad"].sum()
            
            costo_instalacion_final = 0.0
            detalle_instalacion_texto = "Retira de Fábrica"
            if lugar_instalacion == "JDLA (Junín de los Andes)":
                if total_unidades_cortinas > 0:
                    costo_instalacion_final = st.session_state['inst_jdla_1ra'] + ((total_unidades_cortinas - 1) * st.session_state['inst_adicional'])
                    detalle_instalacion_texto = f"Instalación JDLA ({total_unidades_cortinas} u.)"
            elif lugar_instalacion == "SMA (San Martín de los Andes)":
                if total_unidades_cortinas > 0:
                    costo_instalacion_final = st.session_state['inst_sma_1ra'] + ((total_unidades_cortinas - 1) * st.session_state['inst_adicional'])
                    detalle_instalacion_texto = f"Instalación SMA ({total_unidades_cortinas} u.)"
            
            descuento_medicion_final = st.session_state['toma_medidas'] if aplica_toma_medidas else 0.0
            t_base_efectivo_cortinas = gran_total_lista * (1 - (st.session_state['desc_efectivo'] / 100))
            t_efectivo_final_neto = t_base_efectivo_cortinas + costo_instalacion_final - descuento_medicion_final
            
            t_3_cuotas = gran_total_lista * (1 - (st.session_state['desc_3_cuotas'] / 100))
            t_tarjeta = gran_total_lista * (1 - (st.session_state['desc_tarjeta'] / 100))
            
            st.markdown("<p style='margin-bottom:2px; font-size:14px; color:#555; font-weight:bold;'>VALOR TOTAL CONTADO EFECTIVO / TRANSFERENCIA</p>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='color:#1aa845; font-size:48px; margin-top:0px; margin-bottom:2px;'>$ {t_efectivo_final_neto:,.0f}</h1>", unsafe_allow_html=True)
            
            st.markdown(f"<p style='font-size:13px; color:#777; margin-top:5px;'>Precio de Lista Base (Financiado): $ {gran_total_lista:,.0f}</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            c1, c2 = st.columns(2)
            c1.info(f"💳 **3 Cuotas Fijas**\n\nTotal: ${t_3_cuotas:,.0f}\n\n3 de: **${t_3_cuotas/3:,.0f}**")
            c2.success(f"🪪 **Tarjeta 1 Pago**\n\nTotal: ${t_tarjeta:,.0f}")
            
            st.markdown("---")
            
            # ---------------------------------------------------------
            # MÓDULO GENERADOR DE ARCHIVO COMERCIAL DE RESPALDO (PDF / TXT)
            # ---------------------------------------------------------
            st.subheader("📥 Exportación Comercial")
            
            id_compuesto_archivo = f"PR-{nro_presupuesto:05d}-V{version_presupuesto}"
            
            # Construcción de un reporte estructurado en memoria limpia
            buffer_reporte = io.BytesIO()
            lineas_reporte = []
            lineas_reporte.append("==================================================")
            lineas_reporte.append(f"  PRESUPUESTO COMERCIAL - ROLLERTUE CORTINAS")
            lineas_reporte.append("==================================================")
            lineas_reporte.append(f"Referencia: {id_compuesto_archivo}")
            lineas_reporte.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            lineas_reporte.append(f"Cliente: {cliente_global if cliente_global else 'Consumidor Final'}")
            lineas_reporte.append(f"Logística: {detalle_instalacion_texto}")
            lineas_reporte.append("--------------------------------------------------\n")
            lineas_reporte.append("DETALLE DE LAS UNIDADES:")
            
            for sub_item in st.session_state['carrito']:
                lineas_reporte.append(f"- {sub_item['Cantidad']} u. x {sub_item['Detalle Producto']} -> Lista Total: ${sub_item['Precio Lista Total ($)']:,.0f}")
            
            lineas_reporte.append("\n--------------------------------------------------")
            lineas_reporte.append(f"PRECIO BASE LISTA FINANCIADO: $ {gran_total_lista:,.0f}")
            lineas_reporte.append(f"VALOR TOTAL EFECTIVO/TRANSFERENCIA: $ {t_efectivo_final_neto:,.0f}")
            lineas_reporte.append(f"OPCIÓN 3 CUOTAS FIJAS: 3 de ${t_3_cuotas/3:,.0f} (Total: ${t_3_cuotas:,.0f})")
            lineas_reporte.append(f"OPCIÓN TARJETA 1 PAGO: $ {t_tarjeta:,.0f}")
            lineas_reporte.append("==================================================")
            lineas_reporte.append(" Validez del presupuesto: 5 días debido a volatilidad.")
            
            texto_final_reporte = "\n".join(lineas_reporte)
            buffer_reporte.write(texto_final_reporte.encode('utf-8'))
            buffer_reporte.seek(0)
            
            # Botón nativo de descarga directo al almacenamiento local
            st.download_button(
                label="📄 GENERAR Y DESCARGAR COMPROBANTE",
                data=buffer_reporte,
                file_name=f"Presupuesto_{id_compuesto_archivo}_{cliente_global.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.markdown("---")
            if st.button("🚀 SYNC INTERNET: GUARDAR EN LA NUBE", use_container_width=True, type="primary"):
                if cliente_global.strip() == "":
                    st.error("Falta ingresar el nombre del cliente.")
                else:
                    try:
                        id_compuesto = f"PR-{nro_presupuesto:05d}-V{version_presupuesto}"
                        carrito_serializado = json.dumps(st.session_state['carrito']) 
                        
                        supabase.table("presupuestos").insert({
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "cliente": f"{cliente_global} ({id_compuesto})",
                            "items_cantidad": len(df_carrito),
                            "total_lista": int(gran_total_lista),
                            "total_efectivo": int(t_efectivo_final_neto),
                            "detalle_items": carrito_serializado  
                        }).execute()
                        
                        st.success(f"¡Orden {id_compuesto} fijada online!")
                        st.session_state['carrito'] = []
                        st.session_state['edit_cliente'] = ""
                        st.session_state['edit_nro'] = 160
                        st.session_state['edit_ver'] = 1
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al sincronizar con Supabase Cloud: {err}")
        else:
            st.info("Presupuesto vacío. Agregue cortinas desde el panel izquierdo.")

# =========================================================
# PESTAÑA: CONFIGURACIÓN FINANCIERA Y PRECIOS (🔐 CANDADO REUBICADO)
# =========================================================
with tab_config:
    st.header("⚙️ Configuración Global e Insumos del Taller")
    st.markdown("---")
    
    # 1. El candado ahora opera estrictamente encapsulado dentro de su pestaña
    password_ingresada = st.text_input("🔐 Introduzca la clave de administrador para modificar los costos:", type="password")
    
    if password_ingresada == st.secrets["PASSWORD_COSTOS"]:
        st.success("¡Acceso concedido, Maxi!")
        
        # Botón principal para fijar costos en Supabase
        if st.button("💾 GUARDAR PRECIOS PERMANENTES EN LA NUBE", type="primary", use_container_width=True):
            try:
                supabase.table("config_insumos").upsert({
                    "id": "lista_precios",
                    "valores": st.session_state['precios_insumos']
                }).execute()
                st.success("¡Costos de insumos sincronizados de forma permanente! No tendrás que reconfigurarlos al reiniciar.")
            except Exception as ex:
                st.error(f"Error al guardar costos en Supabase: {ex}")

        st.markdown("---")
        col_d, _ = st.columns([1, 2])
        with col_d:
            st.session_state['dolar'] = st.number_input("Cotización del Dólar (ARS):", min_value=1.0, value=st.session_state['dolar'], step=10.0)
        
        st.markdown("---")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.subheader("📊 Módulo de Márgenes Financieros")
            st.session_state['margen_rentabilidad'] = st.number_input("Rentabilidad sobre Costo (%)", min_value=0.0, value=st.session_state['margen_rentabilidad'])
            st.session_state['componente_financiero'] = st.number_input("Componente Financiero para Lista (%)", min_value=0.0, value=st.session_state['componente_financiero'])
            st.session_state['desc_3_cuotas'] = st.number_input("Descuento en 3 Cuotas Fijas (%)", min_value=0.0, value=st.session_state['desc_3_cuotas'])
            st.session_state['desc_tarjeta'] = st.number_input("Descuento 1 pago Tarjeta (%)", min_value=0.0, value=st.session_state['desc_tarjeta'])
            st.session_state['desc_efectivo'] = st.number_input("Descuento Efectivo (%)", min_value=0.0, value=st.session_state['desc_efectivo'])
        with col_f2:
            st.subheader("🚚 Módulo de Servicios e Instalaciones ($ ARS)")
            st.session_state['toma_medidas'] = st.number_input("Servicio Toma de Medidas ($)", min_value=0.0, value=st.session_state['toma_medidas'], step=1000.0)
            st.session_state['inst_jdla_1ra'] = st.number_input("JDLA - Instalación 1ra Cortina ($)", min_value=0.0, value=st.session_value['inst_jdla_1ra'], step=1000.0) if 'inst_jdla_1ra' in st.session_state else st.number_input("JDLA - Instalación 1ra Cortina ($)", min_value=0.0, value=35000.0, step=1000.0)
            st.session_state['inst_sma_1ra'] = st.number_input("SMA - Instalación 1ra Cortina ($)", min_value=0.0, value=st.session_state['inst_sma_1ra'], step=1000.0)
            st.session_state['inst_adicional'] = st.number_input("Valor Cortina Adicional ($)", min_value=0.0, value=st.session_state['inst_adicional'], step=1000.0)

        st.markdown("---")
        st.subheader("🛠️ Costo Base de Componentes (Valores en USD)")
        insumos = st.session_state['precios_insumos']
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown("### 🔹 Telas y Caños")
            insumos["BO 520"] = st.number_input("Tela BO 520 (USD/m²)", value=float(insumos["BO 520"]), format="%.2f")
            insumos["SS OPTIMA 5%"] = st.number_input("Tela SS OPTIMA 5% (USD/m²)", value=float(insumos["SS OPTIMA 5%"]), format="%.2f")
            insumos["ECO BOH"] = st.number_input("Tela ECO BOH (USD/m²)", value=float(insumos["ECO BOH"]), format="%.2f")
            insumos["Caño 32"] = st.number_input("Caño 32 (USD/ML)", value=float(insumos["Caño 32"]), format="%.2f")
            insumos["Caño 38"] = st.number_input("Caño 38 (USD/ML)", value=float(insumos["Caño 38"]), format="%.2f")
        with col_c2:
            st.markdown("### 🔹 Zócalos y Lineales")
            insumos["Zócalo DAVID"] = st.number_input("Zócalo DAVID (USD/ML)", value=float(insumos["Zócalo DAVID"]), format="%.2f")
            insumos["Zócalo SS"] = st.number_input("Zócalo SS (USD/ML)", value=float(insumos["Zócalo SS"]), format="%.2f")
            insumos["CINTA"] = st.number_input("Cinta Doble Faz (USD/ML)", value=float(insumos["CINTA"]), format="%.2f")
            insumos["FIDEO"] = st.number_input("Fideo (USD/ML)", value=float(insumos["FIDEO"]), format="%.2f")
            insumos["Fleje"] = st.number_input("Fleje (USD/ML)", value=float(insumos["Fleje"]), format="%.2f")
        with col_c3:
            st.markdown("### 🔹 Sistemas y Logística")
            insumos["Mecanismo J32"] = st.number_input("Mecanismo J32 (USD)", value=float(insumos["Mecanismo J32"]), format="%.2f")
            insumos["Mecanismo J38"] = st.number_input("Mecanismo J38 (USD)", value=float(insumos["Mecanismo J38"]), format="%.2f")
            insumos["Soporte DAVID J32 DOBLE"] = st.number_input("Soporte J32 DOBLE (USD)", value=float(insumos["Soporte DAVID J32 DOBLE"]), format="%.2f")
            insumos["Soporte J38 DOBLE"] = st.number_input("Soporte J38 DOBLE (USD)", value=float(insumos["Soporte J38 DOBLE"]), format="%.2f")
            insumos["CONTRAPESO CADENA"] = st.number_input("Contrapeso (USD)", value=float(insumos["CONTRAPESO CADENA"]), format="%.2f")
            insumos["CADENA PLÁSTICA"] = st.number_input("Cadena Plástica (USD/ML)", value=float(insumos["CADENA PLÁSTICA"]), format="%.2f")
            insumos["FLETE"] = st.number_input("Flete por Unidad (USD)", value=float(insumos["FLETE"]), format="%.2f")
    else:
        if password_ingresada != "":
            st.error("❌ Contraseña incorrecta. Acceso denegado.")
        else:
            st.warning("🔒 Esta pestaña contiene información financiera crítica. Ingrese la clave de administrador de Rollertue para desplegar los controles.")

# =========================================================
# PESTAÑA: HISTORIAL CLOUD 
# =========================================================
with tab_historial_cloud:
    st.header("🌐 Historial de Órdenes Guardadas en Internet")
    try:
        respuesta = supabase.table("presupuestos").select("*").order("id", desc=True).execute()
        if respuesta.data:
            for row in respuesta.data:
                c_info, c_recup = st.columns([5, 1.2])
                c_info.write(f"📅 **{row['fecha']}** | 👤 {row['cliente']} | 📦 Cortinas: {row['items_cantidad']} | Total Contado: **$ {row['total_efectivo']:,}**")
                
                if c_recup.button("📂 Cargar en Editor", key=f"rec_{row['id']}"):
                    texto_cliente = row['cliente']
                    try:
                        partes = texto_cliente.split(" (PR-")
                        nombre_limpio = partes[0]
                        codigo_bloque = partes[1].replace(")", "")
                        nro_extraido = int(codigo_bloque.split("-V")[0])
                        ver_extraida = int(codigo_bloque.split("-V")[1])
                    except:
                        nombre_limpio = texto_cliente
                        nro_extraido = 160
                        ver_extraida = 1
                    
                    st.session_state.edit_cliente = str(nombre_limpio)
                    st.session_state.edit_nro = int(nro_extraido)
                    st.session_state.edit_ver = int(ver_extraida)
                    
                    if 'detalle_items' in row and row['detalle_items']:
                        st.session_state.carrito = json.loads(row['detalle_items'])
                    st.rerun()
                st.markdown("<hr style='margin: 4px 0px;'>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Error al leer desde Supabase: {e}")