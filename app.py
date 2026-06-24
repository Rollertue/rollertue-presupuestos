import streamlit as st
from supabase import create_client, Client
import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA Y CONEXIONES
# ==========================================
st.set_page_config(page_title="Cotizador Rollertue", page_icon="🪟", layout="centered")

# Inicializar conexión a Supabase de forma segura usando st.secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Error al conectar con la base de datos de Supabase. Revisa los Secrets.")
    st.stop()

# ==========================================
# INTERFAZ DE USUARIO: PESTAÑAS (TABS)
# ==========================================
st.title("🪟 Sistema Comercial - Rollertue")
st.write("Manufactura de Cortinas Roller | Junín de los Andes")

tab1, tab2, tab3 = st.tabs(["🧮 Nueva Cotización", "📊 Historial", "⚙️ Configuración de Costos"])

# ------------------------------------------
# PESTAÑA 1: NUEVA COTIZACIÓN (PÚBLICA)
# ------------------------------------------
with tab1:
    st.header("Calcular Presupuesto")
    
    with st.form("form_cotizacion"):
        cliente = st.text_input("Nombre del Cliente:")
        telefono = st.text_input("Teléfono / Contacto:")
        
        col1, col2 = st.columns(2)
        with col1:
            ancho = st.number_input("Ancho (metros):", min_value=0.1, max_value=5.0, value=1.2, step=0.1)
            tipo_tela = st.selectbox("Tipo de Tela:", ["Blackout", "Sunscreen 5%", "Sunscreen 1%", "Duo / Eclipse"])
        with col2:
            alto = st.number_input("Alto (metros):", min_value=0.1, max_value=5.0, value=1.5, step=0.1)
            mecanismo = st.selectbox("Lado del Mecanismo:", ["Izquierdo", "Derecho"])
            
        observaciones = st.text_area("Notas / Detalles adicionales:")
        
        btn_calcular = st.form_submit_button("Calcular y Guardar Presupuesto")
        
    if btn_calcular:
        if not cliente:
            st.error("Por favor, ingresá el nombre del cliente.")
        else:
            # Lógica matemática de ejemplo (acá podés adaptarla a tus fórmulas reales)
            metros_cuadrados = ancho * alto
            costo_base = 25000 if "Blackout" in tipo_tela else 28000 # Simulación de costo fijo
            total_estimado = metros_cuadrados * costo_base
            
            # Guardar en Supabase
            datos_presupuesto = {
                "cliente": cliente,
                "telefono": telefono,
                "ancho": ancho,
                "alto": alto,
                "tipo_tela": tipo_tela,
                "mecanismo": mecanismo,
                "total": total_estimado,
                "observaciones": observaciones,
                "fecha": str(datetime.date.today())
            }
            
            try:
                res = supabase.table("presupuestos").insert(datos_presupuesto).execute()
                st.success(f"¡Presupuesto para {cliente} guardado con éxito!")
                st.metric(label="Total a Cobrar", value=f"${total_estimado:,.2f}")
                
                # Acá iría el desencadenador del PDF (ReportLab) que ya tenías programado
                st.info("📥 El PDF se generará automáticamente según tu plantilla de ReportLab.")
                
            except Exception as error:
                st.error(f"No se pudo guardar en la base de datos: {error}")

# ------------------------------------------
# PESTAÑA 2: HISTORIAL DE VENTAS (PÚBLICA)
# ------------------------------------------
with tab2:
    st.header("Últimos Presupuestos Guardados")
    try:
        # Traer los últimos 20 registros desde Supabase
        respuesta = supabase.table("presupuestos").select("*").order("id", desc=True).limit(20).execute()
        datos = respuesta.data
        
        if datos:
            for p in datos:
                with st.expander(f"📋 {p['cliente']} — ${p['total']:,.2f} ({p['fecha']})"):
                    st.write(f"**Medidas:** {p['ancho']}m x {p['alto']}m | **Mecanismo:** {p['mecanismo']}")
                    st.write(f"**Tela:** {p['tipo_tela']}")
                    if p['observaciones']:
                        st.write(f"**Notas:** {p['observaciones']}")
        else:
            st.info("No hay presupuestos registrados todavía.")
    except Exception as e:
        st.warning("Asegúrate de tener creada la tabla 'presupuestos' en Supabase para ver el historial.")

# ------------------------------------------
# PESTAÑA 3: CONFIGURACIÓN DE COSTOS (🔐 PROTEGIDA)
# ------------------------------------------
with tab3:
    st.header("⚙️ Administración del Taller")
    
    # 1. Entrada de texto oculta para la contraseña
    password_ingresada = st.text_input(
        "Introduzca la clave de administrador para modificar los costos de Rollertue:", 
        type="password"
    )
    
    # 2. Validación lógica contra los Secrets de la nube
    if password_ingresada == st.secrets["PASSWORD_COSTOS"]:
        st.success("🔓 Acceso concedido, Maxi.")
        st.subheader("Modificar Lista de Precios de Materiales")
        
        # Todo este bloque de abajo solo existe y se ejecuta si la clave es correcta
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            precio_bo = st.number_input("Precio M2 Blackout ($):", value=15000)
            precio_ss = st.number_input("Precio M2 Sunscreen ($):", value=18000)
        with col_c2:
            costo_mecanismo = st.number_input("Costo Kit Mecanismo ($):", value=8500)
            ganancia_porcentaje = st.number_input("Margen de Ganancia (%):", value=40)
            
        if st.button("Actualizar Costos Globales"):
            # Acá podés agregar la lógica para guardar estos valores en otra tabla de Supabase si querés
            st.toast("¡Valores de costos actualizados en memoria!", icon="💾")
            
    else:
        # Mensajes de advertencia en caso de que la contraseña esté vacía o mal escrita
        if password_ingresada != "":
            st.error("❌ Contraseña incorrecta. Acceso denegado.")
        else:
            st.warning("🔒 Esta sección es privada. Por favor, introducí la clave de administrador para gestionar los costos de insumos.")