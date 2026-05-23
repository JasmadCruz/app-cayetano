import streamlit as st
from inference_sdk import InferenceHTTPClient
from fpdf import FPDF

# --- CONFIGURACIÓN ---
api_key = st.secrets.get("ROBOFLOW_API_KEY", "OCb1UXipZhLKuboj2cMy")
CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)

LISTA_MAESTRA = {
    "Paracetamol 500mg": "cayetano_paracetamol_genfar/1",
    "Ibuprofeno 400mg": "MODELO_ID_IBUPROFENO"
}

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
        pdf.cell(200, 10, txt=f"- {med}: Total {total} dosis consumidas", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA LOGIN ---
def mostrar_login():
    st.title("🏥 Acceso al Sistema")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario == "admin" and contraseña == "cayetano2024":
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
            st.session_state.pacientes[dni] = {med: [] for med in LISTA_MAESTRA.keys()}
        
        med = st.selectbox("Seleccione Medicamento:", list(LISTA_MAESTRA.keys()))
        
        if st.button("Añadir nuevo blíster"):
            nueva_id = len(st.session_state.pacientes[dni][med]) + 1
            st.session_state.pacientes[dni][med].append({"id": nueva_id, "vacios": 0})
            st.rerun()

        # Visualización y Registro
        for idx, b in enumerate(st.session_state.pacientes[dni][med]):
            with st.expander(f"Blíster #{b['id']} (Código: BLI-{dni[:3]}-{b['id']})", expanded=True):
                archivo = st.file_uploader(f"Foto Blíster {b['id']}", key=f"up_{dni}_{med}_{idx}")
                if archivo:
                    with open("temp.jpg", "wb") as f: f.write(archivo.getbuffer())
                    res = CLIENT.infer("temp.jpg", model_id=LISTA_MAESTRA[med])
                    vacios = sum(1 for p in res['predictions'] if p['class'] == 'alveolo_vacio')
                    st.session_state.pacientes[dni][med][idx]['vacios'] = vacios
                    st.success(f"Analizado: {vacios} consumidas.")

        st.metric(f"Total consumido {med}", sum(b['vacios'] for b in st.session_state.pacientes[dni][med]))
        
        # BOTÓN PDF
        st.download_button(
            label="📄 Descargar Reporte PDF",
            data=generar_pdf(dni, st.session_state.pacientes[dni]),
            file_name=f"Reporte_Paciente_{dni}.pdf",
            mime="application/pdf"
        )

# --- FLUJO ---
if not st.session_state.autenticado: mostrar_login()
else: mostrar_app()
