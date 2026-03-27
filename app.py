from fastapi import FastAPI
from routers.alunos import alunos_router
from routers.cursos import cursos_router
from routers.matriculas import matriculas_router
from database import db  # 👈 adiciona isso

app = FastAPI(
    title="API de Gestão Escolar",
    description="API para gerenciar alunos, cursos e matrículas",
    version="1.0.0",
)

app.include_router(alunos_router, tags=["alunos"])
app.include_router(cursos_router, tags=["cursos"])
app.include_router(matriculas_router, tags=["matriculas"])

# 👇 rota de teste
@app.get("/debug-db")
def debug_db():
    return {"db": db.name}