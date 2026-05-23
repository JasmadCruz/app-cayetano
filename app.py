import streamlit as st
from inference_sdk import InferenceHTTPClient
from fpdf import FPDF

# --- CONFIGURACIÓN ---
api_key = st.secrets["ROBOFLOW_API_KEY"] if "ROBOFLOW_API_KEY" in st.secrets else "OCb1UXipZhLKuboj2cMy"
CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=api_key)

LISTA_MAESTRA = {
    "Paracetamol 500mg": "cayetano_paracetamol_genfar/1",
    "Ibuprofeno 400mg": "MODELO_ID_IBUPROFENO"
}

# --- INICIALIZACIÓN ---
if 'pacientes' not in st.session_state: st.session_state.pacientes = {}

st.title("🏥 Admisión Cayetano - Sistema por Blíster")

dni = st.text_input("DNI Paciente:")
if dni:
    if dni not in st.session_state.pacientes:
        st.session_state.pacientes[dni] = {med: [] for med in LISTA_MAESTRA.keys()}
    
    med = st.selectbox("Medicamento:", list(LISTA_MAESTRA.keys()))
    
    # --- SISTEMA DE BLÍSTERES INDEPENDIENTES ---
    st.subheader(f"Gestión de {med}")
    
    # Botón para añadir un nuevo blíster (Slot)
    if st.button("Añadir nuevo blíster a este paciente"):
        st.session_state.pacientes[dni][med].append({"id": len(st.session_state.pacientes[dni][med]) + 1, "foto": None, "vacios": 0})
        st.rerun()

    # Mostrar todos los blísteres registrados de este medicamento
    blisteres = st.session_state.pacientes[dni][med]
    for idx, b in enumerate(blisteres):
        with st.expander(f"Blíster #{b['id']} (Código: BLI-{dni[:3]}-{b['id']})", expanded=True):
            archivo = st.file_uploader(f"Foto Blíster {b['id']}", key=f"uploader_{dni}_{med}_{idx}")
            
            if archivo:
                # Procesar IA
                with open("temp.jpg", "wb") as f: f.write(archivo.getbuffer())
                res = CLIENT.infer("temp.jpg", model_id=LISTA_MAESTRA[med])
                vacios = sum(1 for p in res['predictions'] if p['class'] == 'alveolo_vacio')
                
                # Guardar resultado en el slot específico
                st.session_state.pacientes[dni][med][idx]['vacios'] = vacios
                st.success(f"Detectado: {vacios} consumidas.")
                st.image(archivo, use_container_width=True)

    # Resumen Total por Paciente
    st.write("---")
    total_consumo = sum(b['vacios'] for b in blisteres)
    st.metric(f"Total {med} consumido por el paciente", total_consumo)
