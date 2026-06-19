# 1. Usamos una computadora virtual pequeña con Python ya instalado
FROM python:3.10-slim

# 2. Le decimos que trabaje dentro de una carpeta llamada /app
WORKDIR /app

# 3. Copiamos la lista de requisitos y los instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos todo tu código (main.py, ai_model.py, etc.) a la caja
COPY . .

# 5. Le decimos qué comando ejecutar al encender la caja
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]