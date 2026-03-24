from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Union
from schemas import Matricula
from database import get_db
from bson import ObjectId

matriculas_router = APIRouter()

@matriculas_router.post("/matriculas", response_model=Matricula, status_code=status.HTTP_201_CREATED)
def create_matricula(matricula: Matricula = Body(...), db = Depends(get_db)):
    
    if not ObjectId.is_valid(matricula.aluno_id) or not ObjectId.is_valid(matricula.curso_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de Aluno ou Curso inválido")

    db_aluno = db.alunos.find_one({"_id": ObjectId(matricula.aluno_id)})
    db_curso = db.cursos.find_one({"_id": ObjectId(matricula.curso_id)})

    if db_aluno is None or db_curso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno ou Curso não encontrado")

    matricula_dict = matricula.dict(exclude={"id"})
    new_matricula = db.matriculas.insert_one(matricula_dict)
    created_matricula = db.matriculas.find_one({"_id": new_matricula.inserted_id})
    return created_matricula

@matriculas_router.get("/matriculas/aluno/{nome_aluno}", response_model=Dict[str, Union[str, List[str]]])
def read_matriculas_por_nome_aluno(nome_aluno: str, db = Depends(get_db)):
    db_aluno = db.alunos.find_one({"nome": {"$regex": nome_aluno, "$options": "i"}})

    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    # Buscar matrículas do aluno
    matriculas = list(db.matriculas.find({"aluno_id": str(db_aluno["_id"])}))
    
    cursos_nomes = []
    for m in matriculas:
        curso = db.cursos.find_one({"_id": ObjectId(m["curso_id"])})
        if curso:
            cursos_nomes.append(curso["nome"])

    if not cursos_nomes:
        raise HTTPException(status_code=404, detail=f"O aluno '{db_aluno['nome']}' não possui matrículas cadastradas.")

    return {"aluno": db_aluno["nome"], "cursos": cursos_nomes}

@matriculas_router.get("/matriculas/curso/{codigo_curso}", response_model=Dict[str, Union[str, List[str]]])
def read_alunos_matriculados_por_codigo_curso(codigo_curso: str, db = Depends(get_db)):
    """Retorna o nome do curso e uma lista com os nomes dos alunos matriculados."""
    db_curso = db.cursos.find_one({"codigo": codigo_curso})

    if not db_curso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado")

    # Buscar matrículas do curso
    matriculas = list(db.matriculas.find({"curso_id": str(db_curso["_id"])}))
    
    alunos_nomes = []
    for m in matriculas:
        aluno = db.alunos.find_one({"_id": ObjectId(m["aluno_id"])})
        if aluno:
            alunos_nomes.append(aluno["nome"])

    if not alunos_nomes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nenhum aluno matriculado no curso '{db_curso['nome']}'.")

    return {"curso": db_curso["nome"], "alunos": alunos_nomes}
