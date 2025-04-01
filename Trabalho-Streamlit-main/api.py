import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
import os
import signal
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PermissionRequest(BaseModel):
    path: str
    permissions: str

@app.get("/memory")
def get_memory_usage():
    return psutil.virtual_memory().percent

@app.get("/cpu")
def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

# Adicione este novo modelo
class KillRequest(BaseModel):
    pid: int

# Atualize o endpoint
import logging
from fastapi import HTTPException

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/kill_process")
def kill_process(request: KillRequest):
    pid = request.pid
    
    # Verificação imediata via sistema operacional
    try:
        os.kill(pid, 0)  # Sinal 0 verifica se o processo existe
    except ProcessLookupError:
        logger.error(f"Erro imediato: PID {pid} não encontrado.")
        raise HTTPException(
            status_code=404,
            detail=f"Processo {pid} não existe ou já foi encerrado."
        )
    except PermissionError:
        logger.error(f"Permissão negada para PID {pid}.")
        raise HTTPException(
            status_code=403,
            detail="Permissão insuficiente. Execute a API como superusuário."
        )
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Tentar finalizar o processo com SIGTERM e SIGKILL
    try:
        # Primeiro tenta SIGTERM (término suave)
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Sinal SIGTERM enviado para PID {pid}.")
        
        # Verifica se o processo ainda existe após SIGTERM
        time.sleep(0.5)  # Aguarda 500ms
        os.kill(pid, 0)  # Se falhar, o processo foi encerrado
        
        # Se chegou aqui, o processo ainda existe (SIGTERM falhou)
        logger.warning(f"SIGTERM falhou. Enviando SIGKILL para PID {pid}.")
        os.kill(pid, signal.SIGKILL)
        
        return {"status": f"Processo {pid} finalizado com SIGKILL"}
        
    except ProcessLookupError:
        logger.info(f"Processo {pid} encerrado com SIGTERM.")
        return {"status": f"Processo {pid} finalizado com sucesso"}
        
    except Exception as e:
        logger.error(f"Erro crítico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Adicione este endpoint em api.py
@app.get("/processes")
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        # Filtrar processos do kernel e PIDs críticos
        if (
            proc.info['pid'] > 1000 and  # Ignorar PIDs baixos (geralmente do kernel)
            "kworker" not in proc.info['name'] and
            proc.info['name'] not in ["systemd", "kthreadd", "rcu_preempt"]
        ):
            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "cpu": proc.info['cpu_percent'],
                "memory": proc.info['memory_percent'],
                "status": proc.info['status']
            })
    return processes

@app.post("/set_permissions")
def set_permissions(request: PermissionRequest):
    try:
        permissions_int = int(request.permissions, 8)  # Converte de octal para inteiro
        os.chmod(request.path, permissions_int)
        return {"status": "Permissões atualizadas com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Permissões inválidas. Use formato octal (ex: 755)")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo/pasta não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)