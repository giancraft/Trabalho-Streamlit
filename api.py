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

@app.post("/kill_process")
def kill_process(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
        return {"status": "Processo terminado com sucesso"}
    except ProcessLookupError:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permissão negada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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