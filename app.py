import streamlit as st
from inference_sdk import InferenceHTTPClient
from fpdf import FPDF

# --- CONFIGURACIÓN ---
if "ROBOFLOW_API_KEY" in st.secrets:
    api_key = st.secrets["ROBOFLOW_API_KEY"]
else:
    api_key = "OCb1UXipZhLKuboj2cMy"

CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)

LISTA_MAESTRA = {
    "Paracetamol 500mg": "cayetano_paracetamol_genfar/1",
    "Ibuprofeno 400mg": "MODELO_ID_IBUPROFENO",
    "Amoxicilina 500mg": "MODELO_ID_AMOXICILINA"
}

# --- INICIALIZACIÓN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pacientes' not in st.session_state: st.session_state.pacientes = {}

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(dni, datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Reporte de Liquidacion: DNI {dni}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    for med, total in datos.items():
        pdf.cell(200, 10, txt=f"{med}: {total} dosis consumidas", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE INTERFAZ ---
if not st.session_state.autenticado:
    st.title("🏥 Login Cayetano")
    usuario = st.text_input("DNI Operador")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario == "admin" and clave == "cayetano2024":
            st.session_state.autenticado = True
            st.rerun()
else:
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({'autenticado': False}))
    st.title("🏥 Gestión de Pacientes")
    
    dni_paciente = st.text_input("DNI del Paciente a registrar:")
    
    if dni_paciente:
        if dni_paciente not in st.session_state.pacientes:
            st.session_state.pacientes[dni_paciente] = {med: 0 for med in LISTA_MAESTRA.keys()}
        
        med_sel = st.selectbox("Medicamento:", list(LISTA_MAESTRA.keys()))
        archivo = st.file_uploader("Subir foto blíster", type=["jpg", "png"])
        
        if archivo:
            # Procesamiento IA...
            with open("temp.jpg", "wb") as f: f.write(archivo.getbuffer())
            res = CLIENT.infer("temp.jpg", model_id=LISTA_MAESTRA[med_sel])
            vacios = sum(1 for p in res['predictions'] if p['class'] == 'alveolo_vacio')
            st.session_state.pacientes[dni_paciente][med_sel] += vacios
            st.success(f"Registrado: {vacios} dosis de {med_sel}")

        # Resumen y PDF
        st.write(f"### Resumen para {dni_paciente}")
        data = st.session_state.pacientes[dni_paciente]
        st.write(data)
        
        st.download_button(
            label="Descargar Reporte en PDF",
            data=generar_pdf(dni_paciente, data),
            file_name=f"Reporte_{dni_paciente}.pdf",
            mime="application/pdf"
        )
