import streamlit as st
from inference_sdk import InferenceHTTPClient

# --- CONFIGURACIÓN ---
api_key = st.secrets.get("ROBOFLOW_API_KEY", "OCb1UXipZhLKuboj2cMy")
CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)

LISTA_MAESTRA = {
    "Paracetamol 500mg": "cayetano_paracetamol_genfar/1",
    "Ibuprofeno 400mg": "MODELO_ID_IBUPROFENO"
}

# --- INICIALIZACIÓN DE ESTADO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pacientes' not in st.session_state: st.session_state.pacientes = {}

# --- LÓGICA DE LOGIN ---
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

# --- LÓGICA DE LA APP ---
def mostrar_app():
    st.title("🏥 Admisión Cayetano")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    dni = st.text_input("DNI del Paciente:")
    if dni:
        if dni not in st.session_state.pacientes:
            st.session_state.pacientes[dni] = {med: [] for med in LISTA_MAESTRA.keys()}
        
        med = st.selectbox("Medicamento:", list(LISTA_MAESTRA.keys()))
        
        if st.button("Añadir nuevo blíster"):
            st.session_state.pacientes[dni][med].append({"id": len(st.session_state.pacientes[dni][med]) + 1, "vacios": 0})
            st.rerun()

        for idx, b in enumerate(st.session_state.pacientes[dni][med]):
            with st.expander(f"Blíster #{b['id']} (Código: BLI-{dni[:3]}-{b['id']})", expanded=True):
                archivo = st.file_uploader(f"Foto Blíster {b['id']}", key=f"up_{dni}_{med}_{idx}")
                if archivo:
                    with open("temp.jpg", "wb") as f: f.write(archivo.getbuffer())
                    res = CLIENT.infer("temp.jpg", model_id=LISTA_MAESTRA[med])
                    vacios = sum(1 for p in res['predictions'] if p['class'] == 'alveolo_vacio')
                    st.session_state.pacientes[dni][med][idx]['vacios'] = vacios
                    st.success(f"Detectado: {vacios} consumidas.")

        st.metric(f"Total consumido {med}", sum(b['vacios'] for b in st.session_state.pacientes[dni][med]))

# --- FLUJO PRINCIPAL ---
if not st.session_state.autenticado:
    mostrar_login()
else:
    mostrar_app()
