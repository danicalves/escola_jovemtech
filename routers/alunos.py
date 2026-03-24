from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Union
from schemas import Aluno
from database import get_db
from bson import ObjectId

alunos_router = APIRouter()

@alunos_router.get("/alunos", response_model=List[Aluno])
def read_alunos(db = Depends(get_db)):
    """
    Retorna uma lista de todos os alunos cadastrados.
    """
    alunos = list(db.alunos.find())
    return alunos

@alunos_router.get("/alunos/{aluno_id}", response_model=Aluno)
def read_aluno(aluno_id: str, db = Depends(get_db)):
    """
    Retorna os detalhes de um aluno específico com base no ID fornecido.
    """
    if not ObjectId.is_valid(aluno_id):
        raise HTTPException(status_code=400, detail="ID de aluno inválido")
    
    db_aluno = db.alunos.find_one({"_id": ObjectId(aluno_id)})
    if db_aluno is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return db_aluno

@alunos_router.post("/alunos", response_model=Aluno)
def create_aluno(aluno: Aluno = Body(...), db = Depends(get_db)):
    """
    Cria um novo aluno com os dados fornecidos.
    """
    aluno_dict = aluno.dict(exclude={"id"})
    new_aluno = db.alunos.insert_one(aluno_dict)
    created_aluno = db.alunos.find_one({"_id": new_aluno.inserted_id})
    return created_aluno

@alunos_router.put("/alunos/{aluno_id}", response_model=Aluno)
def update_aluno(aluno_id: str, aluno: Aluno = Body(...), db = Depends(get_db)):
    """
    Atualiza os dados de um aluno existente.
    """
    if not ObjectId.is_valid(aluno_id):
        raise HTTPException(status_code=400, detail="ID de aluno inválido")

    aluno_dict = {k: v for k, v in aluno.dict(exclude_unset=True).items() if k != "id"}
    
    if len(aluno_dict) >= 1:
        update_result = db.alunos.update_one({"_id": ObjectId(aluno_id)}, {"$set": aluno_dict})
        if update_result.matched_count == 0:
             raise HTTPException(status_code=404, detail="Aluno não encontrado")

    db_aluno = db.alunos.find_one({"_id": ObjectId(aluno_id)})
    return db_aluno

@alunos_router.delete("/alunos/{aluno_id}", response_model=Aluno)
def delete_aluno(aluno_id: str, db = Depends(get_db)):
    """
    Exclui um aluno.
    """
    if not ObjectId.is_valid(aluno_id):
        raise HTTPException(status_code=400, detail="ID de aluno inválido")

    db_aluno = db.alunos.find_one({"_id": ObjectId(aluno_id)})
    if db_aluno is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    db.alunos.delete_one({"_id": ObjectId(aluno_id)})
    return db_aluno

@alunos_router.get("/alunos/nome/{nome_aluno}", response_model=Union[Aluno, List[Aluno]]) 
def read_aluno_por_nome(nome_aluno: str, db = Depends(get_db)):
    """
    Busca alunos pelo nome (parcial ou completo).
    """
    # Regex para case-insensitive search
    db_alunos = list(db.alunos.find({"nome": {"$regex": nome_aluno, "$options": "i"}}))

    if not db_alunos:
        raise HTTPException(status_code=404, detail="Nenhum aluno encontrado com esse nome")

    if len(db_alunos) == 1:
        return db_alunos[0]

    return db_alunos

@alunos_router.get("/alunos/email/{email_aluno}", response_model=Aluno)
def read_aluno_por_email(email_aluno: str, db = Depends(get_db)):
    """
    Busca um aluno pelo email.
    """
    db_aluno = db.alunos.find_one({"email": email_aluno})

    if db_aluno is None:
        raise HTTPException(status_code=404, detail="Nenhum aluno encontrado com esse email")
    
    return db_aluno
