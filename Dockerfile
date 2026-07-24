FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sql/ sql/
COPY src/ src/
COPY scripts/ scripts/

ENV BI_TOOLKIT_DB_PATH=/app/data/bi_toolkit.db
ENV PYTHONPATH=/app/src

EXPOSE 8501

CMD ["sh", "-c", "python scripts/setup_dados.py && streamlit run src/bi_toolkit/dashboard/app.py --server.address=0.0.0.0"]
