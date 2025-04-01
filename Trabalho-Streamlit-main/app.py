import streamlit as st
import requests
import time
from streamlit.components.v1 import html

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

# Placeholders para gráficos e processos
graph_placeholder = st.empty()
process_placeholder = st.empty()

while True:
    try:
        # Coletar dados de monitoramento e processos
        memory = requests.get(f"{BASE_API_URL}/memory").json()
        cpu = requests.get(f"{BASE_API_URL}/cpu").json()
        processes = requests.get(f"{BASE_API_URL}/processes").json()
        
        # Atualizar dados dos gráficos
        st.session_state.memory_data.append(memory)
        st.session_state.cpu_data.append(cpu)
        st.session_state.memory_data = st.session_state.memory_data[-50:]
        st.session_state.cpu_data = st.session_state.cpu_data[-50:]
        
        # Renderizar gráficos
        with graph_placeholder.container():
            st.subheader("Monitoramento em Tempo Real")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Memória (%)")
                st.line_chart(st.session_state.memory_data)
            with col2:
                st.markdown("### CPU (%)")
                st.line_chart(st.session_state.cpu_data)
        
        # Filtrar e ordenar processos
        processes_sorted = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:20]
        
        # Renderizar tabela de processos
        with process_placeholder.container():
            st.subheader("Processos Ativos (Top 20 por CPU)")
        
        # Estilização CSS para a tabela
        st.markdown("""
            <style>
                .compact-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .compact-table th, .compact-table td {
                    padding: 8px;
                    border: 1px solid #ddd;
                    text-align: left;
                }
                .compact-table th {
                    background-color: #f5f5f5;
                }
                .kill-btn {
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    cursor: pointer;
                }
            </style>
        """, unsafe_allow_html=True)

        # Gerar a tabela HTML
        table_html = """
        <table class="compact-table">
            <thead>
                <tr>
                    <th>PID</th>
                    <th>Nome</th>
                    <th>CPU (%)</th>
                    <th>Memória (%)</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
        """

        for proc in processes_sorted:
            table_html += f"""
                <tr>
                    <td>{proc['pid']}</td>
                    <td title="{proc['name']}">{proc['name'][:15]}</td>
                    <td>{proc['cpu']:.1f}</td>
                    <td>{proc['memory']:.1f}</td>
                    <td>
                        <button class="kill-btn" onclick="killProcess({proc['pid']})">Encerrar</button>
                    </td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        # Renderize APENAS UMA VEZ
        html(table_html, height=500)  # Remova o st.markdown() posterior

        # Script para interação com a API
        st.markdown(f"""
            <script>
                function killProcess(pid) {{
                    fetch("{BASE_API_URL}/kill_process", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ pid: pid }})
                    }})
                    .then(response => response.json())
                    .then(data => {{    
                        if (data.status) {{
                            alert("✅ " + data.status);
                        }} else {{
                            alert("❌ Erro: " + (data.detail || "Erro desconhecido"));
                        }}
                    }});
                }}
            </script>
        """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro na coleta de dados: {str(e)}")
    
    time.sleep(2)