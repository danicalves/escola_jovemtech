from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from schemas import Curso
from database import get_db
from bson import ObjectId
import redis
import os
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cursos_router = APIRouter()

# Conexão com Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    # Testa a conexão
    redis_client.ping()
    logger.info("Redis conectado com sucesso!")
except Exception as e:
    logger.warning(f"Não foi possível conectar ao Redis: {e}")
    redis_client = None

@cursos_router.get("/cursos", response_model=List[Curso])
def read_cursos(db = Depends(get_db)):
    cache_key = "cursos:lista"
    
    # Tenta buscar do Redis se ele estiver disponível
    if redis_client:
        try:
            cached_cursos = redis_client.get(cache_key)
            
            if cached_cursos:
                # Cache HIT - retorna do Redis
                logger.info("Cache HIT - Retornando cursos do Redis")
                cursos_data = json.loads(cached_cursos)
                return cursos_data
            else:
                # Cache MISS - busca no MongoDB
                logger.info("Cache MISS - Buscando cursos do MongoDB")
                cursos = list(db.cursos.find())
                
                # Converte ObjectId para string para poder serializar em JSON
                cursos_serializable = []
                for curso in cursos:
                    curso["_id"] = str(curso["_id"])
                    cursos_serializable.append(curso)
                
                # Salva no Redis com TTL de 30 segundos
                redis_client.setex(
                    cache_key,
                    30,  # TTL de 30 segundos
                    json.dumps(cursos_serializable)
                )
                logger.info(f"Cache atualizado com {len(cursos_serializable)} cursos")
                
                return cursos
                
        except Exception as e:
            # Se o Redis falhar, loga o erro e continua com MongoDB
            logger.error(f"Erro ao acessar Redis: {e}")
            cursos = list(db.cursos.find())
            return cursos
    else:
        # Redis não está disponível, busca direto do MongoDB
        logger.warning("Redis indisponível - Buscando diretamente do MongoDB")
        cursos = list(db.cursos.find())
        return cursos

@cursos_router.post("/cursos", response_model=Curso)
def create_curso(curso: Curso = Body(...), db = Depends(get_db)):
    curso_dict = curso.dict(exclude={"id"})
    new_curso = db.cursos.insert_one(curso_dict)
    created_curso = db.cursos.find_one({"_id": new_curso.inserted_id})
    
    # Invalida o cache após criar um novo curso
    if redis_client:
        try:
            redis_client.delete("cursos:lista")
            logger.info("Cache invalidado após criação de novo curso")
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {e}")
    
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
    
    # Invalida o cache após atualizar um curso
    if redis_client:
        try:
            redis_client.delete("cursos:lista")
            logger.info("Cache invalidado após atualização de curso")
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {e}")
    
    return updated_curso

@cursos_router.get("/cursos/{codigo_curso}", response_model=Curso)
def read_curso_por_codigo(codigo_curso: str, db = Depends(get_db)):
    # Cache separado para cursos individuais
    cache_key = f"curso:{codigo_curso}"
    
    # Tenta buscar do Redis
    if redis_client:
        try:
            cached_curso = redis_client.get(cache_key)
            
            if cached_curso:
                logger.info(f"Cache HIT - Retornando curso {codigo_curso} do Redis")
                curso_data = json.loads(cached_curso)
                return curso_data
            else:
                logger.info(f"Cache MISS - Buscando curso {codigo_curso} do MongoDB")
                db_curso = db.cursos.find_one({"codigo": codigo_curso})
                
                if db_curso is None:
                    raise HTTPException(status_code=404, detail="Nenhum curso encontrado com esse código")
                
                # Converte ObjectId para string
                db_curso["_id"] = str(db_curso["_id"])
                
                # Salva no Redis com TTL de 30 segundos
                redis_client.setex(
                    cache_key,
                    30,
                    json.dumps(db_curso)
                )
                logger.info(f"Cache atualizado para o curso {codigo_curso}")
                
                return db_curso
                
        except Exception as e:
            logger.error(f"Erro ao acessar Redis: {e}")
            db_curso = db.cursos.find_one({"codigo": codigo_curso})
            if db_curso is None:
                raise HTTPException(status_code=404, detail="Nenhum curso encontrado com esse código")
            return db_curso
    else:
        # Redis não disponível
        db_curso = db.cursos.find_one({"codigo": codigo_curso})
        if db_curso is None:
            raise HTTPException(status_code=404, detail="Nenhum curso encontrado com esse código")
        return db_curso