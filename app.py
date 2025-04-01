import streamlit as st
import requests
import time

BASE_API_URL = "http://localhost:8000"

st.title("Monitor de Sistema Linux 🖥️")

# Configuração inicial de dados
if 'memory_data' not in st.session_state:
    st.session_state.memory_data = []
    
if 'cpu_data' not in st.session_state:
    st.session_state.cpu_data = []

# Seção de controles
with st.container():
    st.subheader("Controles do Sistema")
    
    # Finalizar Processo
    pid = st.number_input("PID do Processo:", min_value=1, key="pid_input")
    if st.button("Finalizar Processo", key="kill_btn"):
        try:
            response = requests.post(
                f"{BASE_API_URL}/kill_process",
                json={"pid": pid}
            )
            
            if response.status_code == 200:
                st.success(response.json()["status"])
            else:
                error_detail = response.json().get("detail", "Erro desconhecido")
                st.error(f"Erro da API: {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar à API")
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
    
    # Gerenciar Permissões
    path = st.text_input("Caminho do Arquivo/Pasta:", key="path_input")
    permissions = st.text_input("Permissões (ex: 755):", key="perm_input")
    if st.button("Aplicar Permissões", key="perm_btn"):
        if path and permissions:
            try:
                response = requests.post(
                    f"{BASE_API_URL}/set_permissions",
                    json={"path": path, "permissions": permissions}
                )
                if response.status_code == 200:
                    st.success(response.json()["status"])
                else:
                    error_detail = response.json().get("detail", "Erro desconhecido")
                    st.error(f"Erro da API: {error_detail}")
            except requests.exceptions.ConnectionError:
                st.error("Não foi possível conectar à API")
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")
        else:
            st.warning("Preencha todos os campos!")

# Atualização de gráficos
graph_placeholder = st.empty()

while True:
    try:
        memory = requests.get(f"{BASE_API_URL}/memory").json()
        cpu = requests.get(f"{BASE_API_URL}/cpu").json()
        
        st.session_state.memory_data.append(memory)
        st.session_state.cpu_data.append(cpu)
        st.session_state.memory_data = st.session_state.memory_data[-50:]
        st.session_state.cpu_data = st.session_state.cpu_data[-50:]
        
        with graph_placeholder.container():
            st.subheader("Monitoramento em Tempo Real")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Memória (%)")
                st.line_chart(st.session_state.memory_data)
            with col2:
                st.markdown("### CPU (%)")
                st.line_chart(st.session_state.cpu_data)
                
    except Exception as e:
        st.error(f"Erro na coleta de dados: {str(e)}")
    
    time.sleep(1)