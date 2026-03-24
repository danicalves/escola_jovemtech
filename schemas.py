from pydantic import BaseModel, EmailStr, Field
from typing import List, Annotated, Optional, Any
from pydantic.functional_validators import BeforeValidator

# Representação de um ObjectId como string no Pydantic
PyObjectId = Annotated[str, BeforeValidator(str)]

class Matricula(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    aluno_id: str
    curso_id: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "aluno_id": "ID_DO_ALUNO",
                "curso_id": "ID_DO_CURSO",
            }
        }

class Aluno(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str
    email: EmailStr
    telefone: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nome": "João da Silva",
                "email": "joao@exemplo.com",
                "telefone": "11988887777",
            }
        }

class Curso(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str
    codigo: str
    descricao: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nome": "DevOps",
                "codigo": "DV-01",
                "descricao": "Curso completo de DevOps",
            }
        }

Alunos = List[Aluno]
Cursos = List[Curso]
Matriculas = List[Matricula]
