# Why: standardizes the run-time environment using python 3.12-slim to optimize container footprint.
FROM python:3.12-slim

# Why: Prevents Python from writing pyc files to disk and ensures stdout/stderr are flushed immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Why: Creates container directories for code execution and database mounting.
# Connectivity: /app/data will host the mounted DuckDB storage volume linked in docker-compose.
RUN mkdir -p /app/data

# Why: Copies dependencies first to leverage Docker's build cache layers.
COPY requirements.txt /app/

# Why: Installs libraries needed for DuckDB operations and OpenAI LangChain wrappers.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Why: Copies source package directories.
# Connectivity: Includes main.py and the local rag_engine modules.
COPY . /app/

# Why: Exposes the API endpoint inside the Docker network.
# Connectivity: Mapped to Port 8000 in docker-compose for incoming n8n trigger calls.
EXPOSE 8000

# Why: Launches the ASGI web server to handle HTTP POST/GET requests.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
