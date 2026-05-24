import streamlit as st
from inference_sdk import InferenceHTTPClient
from fpdf import FPDF

# --- CONFIGURACIÓN ---
api_key = st.secrets.get("ROBOFLOW_API_KEY", "OCb1UXipZhLKuboj2cMy")
CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)
MODELO_ID = "cayetano_paracetamol_genfar-2/3" 

LISTA_MEDICAMENTOS = ["Paracetamol 500mg", "Ibuprofeno 400mg", "Amoxicilina 500mg"]

# --- INICIALIZACIÓN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pacientes' not in st.session_state: st.session_state.pacientes = {}

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(dni, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Reporte Clinico: Paciente {dni}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for med, lista_blisteres in data.items():
        total = sum(b['vacios'] for b in lista_blisteres)
        if total > 0:
            pdf.cell(200, 10, txt=f"- {med}: {total} dosis consumidas", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA LOGIN ---
def mostrar_login():
    st.title("🏥 Acceso Médico - Cayetano")
    usuario = st.text_input("Usuario Médico")
    contraseña = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario == "medico" and contraseña == "cayetano2024":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# --- LÓGICA APP ---
def mostrar_app():
    st.title("🏥 Admisión Cayetano")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    dni = st.text_input("DNI del Paciente:")
    if dni:
        if dni not in st.session_state.pacientes:
            st.session_state.pacientes[dni] = {med: [] for med in LISTA_MEDICAMENTOS}
        
        med = st.selectbox("Seleccione Medicamento:", LISTA_MEDICAMENTOS)
        
        if st.button("Añadir nuevo blíster"):
            nueva_id = len(st.session_state.pacientes[dni][med]) + 1
            st.session_state.pacientes[dni][med].append({"id": nueva_id, "vacios": 0})
            st.rerun()

        for idx, b in enumerate(st.session_state.pacientes[dni][med]):
            with st.expander(f"Blíster #{b['id']} (Código: BLI-{dni[:3]}-{b['id']})", expanded=True):
                # Selector Dual
                metodo = st.radio(f"¿Cómo desea cargar la foto #{b['id']}?", ["Cámara en vivo", "Subir desde almacenamiento"])
                
                archivo = None
                if metodo == "Cámara en vivo":
                    archivo = st.camera_input("Tomar foto", key=f"cam_{dni}_{med}_{idx}")
                else:
                    archivo = st.file_uploader("Subir foto", type=["jpg", "png", "jpeg"], key=f"up_{dni}_{med}_{idx}")
                
                if archivo:
                    with open("temp.jpg", "wb") as f: f.write(archivo.getbuffer())
                    res = CLIENT.infer("temp.jpg", model_id=MODELO_ID)
                    vacios = sum(1 for p in res['predictions'] if p['class'] == 'alveolo_vacio')
                    st.session_state.pacientes[dni][med][idx]['vacios'] = vacios
                    st.success(f"IA detectó: {vacios} dosis consumidas.")
                    st.image("temp.jpg", use_container_width=True)

        st.metric("Total dosis paciente", sum(sum(b['vacios'] for b in lista) for lista in st.session_state.pacientes[dni].values()))
        
        st.download_button("📄 Descargar Reporte PDF", data=generar_pdf(dni, st.session_state.pacientes[dni]), 
                           file_name=f"Reporte_{dni}.pdf", mime="application/pdf")

if not st.session_state.autenticado: mostrar_login()
else: mostrar_app()
