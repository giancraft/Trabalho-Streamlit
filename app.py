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
if 'processes' not in st.session_state:
    st.session_state.processes = []  # Atualizada somente quando o usuário clicar no botão

# Função para atualizar a lista de processos (somente via botão)
def update_processes():
    try:
        response = requests.get(f"{BASE_API_URL}/processes")
        if response.status_code == 200:
            st.session_state.processes = response.json()
        else:
            st.error(f"Erro ao buscar processos: {response.text}")
    except Exception as e:
        st.error(f"Erro na atualização: {str(e)}")

# Layout principal da aplicação
def main():
    # Seção dos Gráficos (atualizados automaticamente)
    with st.container():
        st.header("Monitoramento de Sistema")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Uso de Memória")
            st.line_chart(st.session_state.memory_data)
        with col2:
            st.markdown("### Uso de CPU")
            st.line_chart(st.session_state.cpu_data)
    
    # Seção de Processos (lista atualizada apenas quando o botão for clicado)
    with st.container():
        st.header("Gerenciamento de Processos")
        
        # Opção de digitar um PID para encerrar o processo
        pid_to_kill = st.text_input("Digite o PID do processo a ser finalizado:")
        if st.button("Encerrar PID", key="kill_pid_button"):
            if pid_to_kill:
                try:
                    pid_int = int(pid_to_kill)
                    response = requests.post(
                        f"{BASE_API_URL}/kill_process", 
                        json={"pid": pid_int}
                    )
                    if response.status_code == 200:
                        st.success(f"Processo {pid_int} finalizado com sucesso!")
                        update_processes()  # Atualiza a lista de processos após encerramento
                    else:
                        error_detail = response.json().get("detail", "Erro desconhecido")
                        st.markdown(
                            f"<script>alert('❌ Erro: {error_detail}');</script>", 
                            unsafe_allow_html=True
                        )
                except ValueError:
                    st.error("Por favor, insira um número inteiro válido para o PID.")
                except Exception as e:
                    st.error(f"Erro inesperado: {str(e)}")
            else:
                st.warning("Por favor, insira um PID.")
        
        # Botão para atualizar a lista de processos
        if st.button("🔄 Atualizar Lista de Processos", key="refresh_proc"):
            update_processes()
        
        # Renderiza a tabela de processos com botões "Encerrar" funcionais
        render_process_table()
        
    
    # Seção de Permissões
    with st.container():
        st.header("Gerenciamento de Permissões")
        render_permissions_form()

# Função para renderizar a tabela de processos com a função killProcess incorporada
def render_process_table():
    processes_sorted = sorted(st.session_state.processes, key=lambda x: x['cpu'], reverse=True)[:20]
    
    table_html = f"""
    <style>
        .scrollable-table {{
            max-height: 600px;
            overflow-y: auto;
            margin: 1rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .scrollable-table::-webkit-scrollbar {{
            width: 8px;
        }}
        .scrollable-table::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        .scrollable-table::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 4px;
        }}
        .scrollable-table::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
        .process-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .process-table thead tr {{
            background-color: #2c3e50;
            color: white;
            position: sticky;
            top: 0;
            box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1);
        }}
        .process-table th, 
        .process-table td {{
            padding: 12px 15px;
            white-space: nowrap;
        }}
        .process-table tbody tr {{
            border-bottom: 1px solid #e0e0e0;
        }}
        .process-table tbody tr:nth-of-type(even) {{
            background-color: #f8f9fa;
        }}
        .kill-btn {{
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .kill-btn:hover {{
            background-color: #c0392b;
            transform: scale(1.05);
        }}
        .process-name {{
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
    </style>
    <div class="scrollable-table">
        <table class="process-table">
            <thead>
                <tr>
                    <th>PID</th>
                    <th>Nome</th>
                    <th>CPU (%)</th>
                    <th>Memória (%)</th>
                    <th>Status</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
    """
    for proc in processes_sorted:
        table_html += f"""
                <tr>
                    <td>{proc['pid']}</td>
                    <td class="process-name" title="{proc['name']}">{proc['name']}</td>
                    <td>{proc['cpu']:.1f}</td>
                    <td>{proc['memory']:.1f}</td>
                    <td>{proc['status']}</td>
                    <td>
                        <button class="kill-btn" onclick="killProcess({proc['pid']})">Encerrar</button>
                    </td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    <script>
        function killProcess(pid) {
            fetch("http://localhost:8000/kill_process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pid: pid })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw err; });
                }
                return response.json();
            })
            .then(data => {
                if (data.status) {
                    alert("✅ " + data.status);
                    // Após finalizar, recarrega a página para atualizar a lista de processos
                    window.location.reload();
                } else {
                    alert("❌ Erro: " + (data.detail || "Erro desconhecido"));
                }
            })
            .catch(error => {
                alert("❌ Erro: " + (error.detail || error.message));
            });
        }
    </script>
    """
    # Usamos o componente html para renderizar toda a tabela com o script
    html(table_html, height=600)

# Função para renderizar o formulário de permissões
def render_permissions_form():
    with st.form("permissions_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            path = st.text_input("Caminho absoluto do arquivo/pasta:")
        with col2:
            permissions = st.text_input("Permissões (ex: 755):", max_chars=3)
        if st.form_submit_button("🔒 Aplicar Permissões", use_container_width=True):
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
                        st.error(f"Erro: {error_detail}")
                except requests.exceptions.ConnectionError:
                    st.error("Conexão com a API falhou")
                except Exception as e:
                    st.error(f"Erro inesperado: {str(e)}")
            else:
                st.warning("Preencha todos os campos antes de enviar!")

# Atualiza os dados dos gráficos (memória e CPU) a cada 2 segundos
def update_charts():
    try:
        memory = requests.get(f"{BASE_API_URL}/memory").json()
        cpu = requests.get(f"{BASE_API_URL}/cpu").json()
        st.session_state.memory_data.append(memory)
        st.session_state.cpu_data.append(cpu)
        st.session_state.memory_data = st.session_state.memory_data[-50:]
        st.session_state.cpu_data = st.session_state.cpu_data[-50:]
    except Exception as e:
        st.error(f"Erro na coleta de dados: {str(e)}")

if __name__ == "__main__":
    update_charts()  
    main()
    # Aguarda 2 segundos e reexecuta a aplicação para atualizar os gráficos
    time.sleep(2)
    st.rerun()
