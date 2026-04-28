# Usamos una imagen especializada que ya trae Chrome y Selenium preinstalados
FROM joyzoursky/python-chromedriver:3.9-selenium

# Evitamos que Python genere archivos basura (.pyc) y forzamos logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecemos la carpeta de trabajo dentro del servidor
WORKDIR /app

# Copiamos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de tu código (main.py) al servidor
COPY . .

# Comando para ejecutar el bot apenas inicie el contenedor
CMD ["python", "main.py"]