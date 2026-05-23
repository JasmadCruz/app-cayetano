import streamlit as st
from inference_sdk import InferenceHTTPClient

# --- CONFIGURACIÓN DE IA ---
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="OCb1UXipZhLKuboj2cMy" # Recuerda cambiarla por seguridad después
)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'inventario_escaneado' not in st.session_state:
    st.session_state.inventario_escaneado = []

# --- PANTALLA DE LOGIN ---
def login():
    st.title("🏥 Admisión Hospitalaria - Cayetano")
    st.subheader("Acceso al Sistema de Liquidación")
    
    usuario = st.text_input("Documento de Identidad (DNI)")
    clave = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if usuario == "admin" and clave == "cayetano2024": # Configura tu clave aquí
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# --- PANTALLA PRINCIPAL (DASHBOARD) ---
def dashboard():
    st.sidebar.title(f"Usuario: Operador 01")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    st.title("Liquidación de Medicamentos")
    
    # 1. Selección de Medicamento (Escalable)
    medicamento_sel = st.selectbox("Seleccione el medicamento a validar:", 
                                   ["Paracetamol 500mg (Genfar)", "Ibuprofeno (Próximamente)", "Antibiótico (Próximamente)"])
    
    # Mapeo de modelos (Aquí agregarás los nuevos IDs de Roboflow)
    modelos = {
        "Paracetamol 500mg (Genfar)": "cayetano_paracetamol_genfar/1"
    }

    # 2. Captura de Blísteres (Permite múltiples fotos)
    st.write("---")
    img_file = st.camera_input("Tome foto del blíster (Cara de aluminio)") # Esto abre la cámara en el cel

    if img_file:
        with st.spinner("IA Analizando blíster..."):
            with open("temp.jpg", "wb") as f:
                f.write(img_file.getbuffer())
            
            # Inferencia
            result = CLIENT.infer("temp.jpg", model_id=modelos[medicamento_sel])
            
            # Conteo
            llenas = sum(1 for p in result['predictions'] if p['class'] == 'pastilla_llena')
            vacios = sum(1 for p in result['predictions'] if p['class'] == 'alveolo_vacio')
            
            # Guardar en sesión
            st.session_state.inventario_escaneado.append({
                "medicamento": medicamento_sel,
                "llenas": llenas,
                "vacios": vacios
            })
            st.success(f"Blíster detectado: {llenas} llenas, {vacios} consumidas.")

    # 3. Resumen de Liquidación Acumulada
    if st.session_state.inventario_escaneado:
        st.write("### 📋 Resumen de Liquidación Final")
        
        total_llenas = sum(item['llenas'] for item in st.session_state.inventario_escaneado)
        total_vacios = sum(item['vacios'] for item in st.session_state.inventario_escaneado)
        num_blisteres = len(st.session_state.inventario_escaneado)

        col1, col2, col3 = st.columns(3)
        col1.metric("Blísteres", num_blisteres)
        col2.metric("Total Llenas (Devolver)", total_llenas)
        col3.metric("Total Vacíos (Consumo)", total_vacios)

        if st.button("Limpiar y Nuevo Paciente"):
            st.session_state.inventario_escaneado = []
            st.rerun()

# --- LÓGICA DE NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    dashboard()