# 1. Usar uma imagem oficial do Python como imagem base.
# A variante 'slim' oferece um bom equilíbrio entre tamanho e compatibilidade.
# O readme menciona Python 3.10+, então a versão 3.11 é uma escolha segura e moderna.
FROM python:3.11-slim

# 2. Definir o diretório de trabalho dentro do contêiner.
# É uma boa prática para manter a organização.
WORKDIR /app

# 3. Copiar o arquivo de dependências primeiro para aproveitar o cache de camadas do Docker.
# Se o requirements.txt não mudar, esta camada não será reconstruída.
COPY requirements.txt .
# 4. Instalar as dependências do Python.
# --no-cache-dir: Reduz o tamanho da imagem final ao não armazenar o cache do pip.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante do código-fonte da aplicação para o contêiner.
COPY . .

# 6. Expor a porta em que a aplicação será executada.
# O Uvicorn usa a porta 8000 por padrão.
EXPOSE 8000

# 7. Definir o comando para executar a aplicação quando o contêiner iniciar.
# --host 0.0.0.0 é crucial para tornar o servidor acessível de fora do contêiner.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]