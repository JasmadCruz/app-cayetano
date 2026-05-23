import streamlit as st
import os
from inference_sdk import InferenceHTTPClient

try:
    api_key = st.secrets["ROBOFLOW_API_KEY"]
except:
    api_key = "OCb1UXipZhLKuboj2cMy" 

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=api_key
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
        if usuario == "admin" and clave == "cayetano2024":
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
    
    medicamento_sel = st.selectbox("Seleccione el medicamento a validar:", 
                                   ["Paracetamol 500mg (Genfar)", "Ibuprofeno", "Antibiótico"])
    
    modelos = {
        "Paracetamol 500mg (Genfar)": "cayetano_paracetamol_genfar/1",
        "Ibuprofeno": "tu_modelo_ibuprofeno/1", # Cambia esto cuando entrenes el siguiente
        "Antibiótico": "tu_modelo_antibiotico/1"
    }

    st.write("---")
    img_file = st.camera_input("Tome foto del blíster (Cara de aluminio)")

    if img_file:
        with st.spinner("IA Analizando blíster..."):
            with open("temp.jpg", "wb") as f:
                f.write(img_file.getbuffer())
            
            # Inferencia
            result = CLIENT.infer("temp.jpg", model_id=modelos[medicamento_sel])
            
            # Conteo
            llenas = sum(1 for p in result['predictions'] if p['class'] == 'pastilla_llena')
            vacios = sum(1 for p in result['predictions'] if p['class'] == 'alveolo_vacio')
            
            st.session_state.inventario_escaneado.append({
                "medicamento": medicamento_sel,
                "llenas": llenas,
                "vacios": vacios
            })
            st.success(f"Blíster detectado: {llenas} llenas, {vacios} consumidas.")

    # Resumen
    if st.session_state.inventario_escaneado:
        st.write("### 📋 Resumen de Liquidación Final")
        
        total_llenas = sum(item['llenas'] for item in st.session_state.inventario_escaneado)
        total_vacios = sum(item['vacios'] for item in st.session_state.inventario_escaneado)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Llenas (Devolver)", total_llenas)
        col2.metric("Total Vacíos (Consumo)", total_vacios)

        if st.button("Limpiar y Nuevo Paciente"):
            st.session_state.inventario_escaneado = []
            st.rerun()

# --- NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    dashboard()
