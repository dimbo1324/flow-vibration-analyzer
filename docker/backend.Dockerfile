FROM python:3.12-slim
WORKDIR /app
ENV QT_QPA_PLATFORM=offscreen
ENV QT_OPENGL=software
ENV MPLBACKEND=Agg
COPY requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-web.txt
COPY . .
RUN pip install --no-cache-dir -e .
RUN useradd -m -u 1000 iva && mkdir -p /app/out && chown -R iva:iva /app/out
USER iva
CMD ["python", "-m", "uvicorn", "iva.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
