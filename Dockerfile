FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Unprivileged user. uid 1000 matches a typical host user so the bind-mounted
# ./data directory stays writable (the UI saves uploads there).
RUN useradd --create-home --uid 1000 app
COPY --chown=app:app app.py rag.py services.py eval.py ./
COPY --chown=app:app data/ data/
USER app

EXPOSE 8000

# python is always present; curl is not in the slim image.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
