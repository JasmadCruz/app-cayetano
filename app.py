import streamlit as st
from inference_sdk import InferenceHTTPClient

# --- CONFIGURACIÓN DE SEGURIDAD ---
# En Streamlit Cloud, configura esto en Settings > Secrets
if "ROBOFLOW_API_KEY" in st.secrets:
    api_key = st.secrets["ROBOFLOW_API_KEY"]
else:
    api_key = "OCb1UXipZhLKuboj2cMy" # Tu clave local para pruebas

CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)

# --- CONFIGURACIÓN DE MEDICAMENTOS ---
LISTA_MAESTRA = {
    "Paracetamol 500mg": "cayetano_paracetamol_genfar/1",
    "Ibuprofeno 400mg": "MODELO_ID_IBUPROFENO",
    "Amoxicilina 500mg": "MODELO_ID_AMOXICILINA"
}

# --- INICIALIZACIÓN DE ESTADO ---
if 'pacientes' not in st.session_state:
    st.session_state.pacientes = {}

# --- INTERFAZ ---
st.title("🏥 Admisión Cayetano - Gestión Integral")

dni_actual = st.text_input("Ingrese DNI del paciente:")

if dni_actual:
    # Inicializar paciente si es nuevo
    if dni_actual not in st.session_state.pacientes:
        st.session_state.pacientes[dni_actual] = {med: 0 for med in LISTA_MAESTRA.keys()}
    
    st.subheader(f"Paciente: {dni_actual}")
    medicamento = st.selectbox("Seleccione medicamento:", list(LISTA_MAESTRA.keys()))
    
    # Captura Híbrida (Cámara o Archivo)
    archivo_subido = st.file_uploader("Subir foto de blíster (Cámara o Galería)", type=["jpg", "jpeg", "png"])
    
    if archivo_subido:
        with st.spinner("Analizando con IA..."):
            with open("temp.jpg", "wb") as f:
                f.write(archivo_subido.getbuffer())
            
            try:
                result = CLIENT.infer("temp.jpg", model_id=LISTA_MAESTRA[medicamento])
                vacios = sum(1 for p in result['predictions'] if p['class'] == 'alveolo_vacio')
                
                # Actualizar contador del paciente
                st.session_state.pacientes[dni_actual][medicamento] += vacios
                st.success(f"Éxito: {vacios} dosis consumidas registradas en {medicamento}.")
                st.image(archivo_subido, caption="Imagen procesada", use_container_width=True)
            except Exception as e:
                st.error(f"Error de conexión con la IA: {e}")

    # Reporte del paciente
    st.write("---")
    st.write(f"### 📋 Resumen actual de {dni_actual}:")
    resumen = st.session_state.pacientes[dni_actual]
    
    for med, total in resumen.items():
        st.write(f"**{med}:** {total} dosis consumidas")

# --- BARRA LATERAL ---
if st.sidebar.button("Reiniciar Toda la Base de Datos"):
    st.session_state.pacientes = {}
    st.rerun()
