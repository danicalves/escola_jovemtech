from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from schemas import Curso
from database import get_db
import redis
import os
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cursos_router = APIRouter()

# Conexão com Redis (opcional)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis conectado com sucesso!")
except Exception as e:
    logger.warning(f"Não foi possível conectar ao Redis: {e}")
    redis_client = None


# 🔧 Função auxiliar para serializar Mongo
def serialize(curso):
    curso["_id"] = str(curso["_id"])
    return curso


@cursos_router.get("/cursos", response_model=List[Curso])
def read_cursos(db = Depends(get_db)):
    cache_key = "cursos:lista"

    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("Cache HIT")
                return json.loads(cached)

        cursos = list(db.cursos.find())
        cursos = [serialize(c) for c in cursos]

        if redis_client:
            redis_client.setex(cache_key, 30, json.dumps(cursos))

        return cursos

    except Exception as e:
        logger.error(f"Erro ao buscar cursos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar cursos")


@cursos_router.post("/cursos", response_model=Curso)
def create_curso(curso: Curso = Body(...), db = Depends(get_db)):
    try:
        curso_dict = curso.dict(exclude={"id"})
        result = db.cursos.insert_one(curso_dict)

        created = db.cursos.find_one({"_id": result.inserted_id})
        created = serialize(created)

        # limpa cache
        if redis_client:
            redis_client.delete("cursos:lista")

        return created

    except Exception as e:
        logger.error(f"Erro ao criar curso: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar curso")


@cursos_router.put("/cursos/{codigo_curso}", response_model=Curso)
def update_curso(codigo_curso: str, curso: Curso = Body(...), db = Depends(get_db)):
    db_curso = db.cursos.find_one({"codigo": codigo_curso})

    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    update_data = {k: v for k, v in curso.dict(exclude_unset=True).items() if k != "id"}

    if update_data:
        db.cursos.update_one({"codigo": codigo_curso}, {"$set": update_data})

    updated = db.cursos.find_one({"codigo": codigo_curso})
    updated = serialize(updated)

    if redis_client:
        redis_client.delete("cursos:lista")

    return updated


@cursos_router.get("/cursos/{codigo_curso}", response_model=Curso)
def read_curso_por_codigo(codigo_curso: str, db = Depends(get_db)):
    cache_key = f"curso:{codigo_curso}"

    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        curso = db.cursos.find_one({"codigo": codigo_curso})

        if not curso:
            raise HTTPException(status_code=404, detail="Curso não encontrado")

        curso = serialize(curso)

        if redis_client:
            redis_client.setex(cache_key, 30, json.dumps(curso))

        return curso

    except Exception as e:
        logger.error(f"Erro ao buscar curso: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar curso")