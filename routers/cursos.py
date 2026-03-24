from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from schemas import Curso
from database import get_db
from bson import ObjectId

cursos_router = APIRouter()

@cursos_router.get("/cursos", response_model=List[Curso])
def read_cursos(db = Depends(get_db)):
    cursos = list(db.cursos.find())
    return cursos

@cursos_router.post("/cursos", response_model=Curso)
def create_curso(curso: Curso = Body(...), db = Depends(get_db)):
    curso_dict = curso.dict(exclude={"id"})
    new_curso = db.cursos.insert_one(curso_dict)
    created_curso = db.cursos.find_one({"_id": new_curso.inserted_id})
    return created_curso

@cursos_router.put("/cursos/{codigo_curso}", response_model=Curso)
def update_curso(codigo_curso: str, curso: Curso = Body(...), db = Depends(get_db)):
    db_curso = db.cursos.find_one({"codigo": codigo_curso})
    if db_curso is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    curso_dict = {k: v for k, v in curso.dict(exclude_unset=True).items() if k != "id"}
    
    if len(curso_dict) >= 1:
        db.cursos.update_one({"codigo": codigo_curso}, {"$set": curso_dict})

    updated_curso = db.cursos.find_one({"codigo": codigo_curso})
    return updated_curso

@cursos_router.get("/cursos/{codigo_curso}", response_model=Curso)
def read_curso_por_codigo(codigo_curso: str, db = Depends(get_db)):
    db_curso = db.cursos.find_one({"codigo": codigo_curso})
    if db_curso is None:
        raise HTTPException(status_code=404, detail="Nenhum curso encontrado com esse código")
    return db_curso
