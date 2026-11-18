FROM python:3.12-slim
WORKDIR /workspace
COPY app/ ./app/
RUN mkdir -p /data && useradd -r -u 10001 runner && chown runner:runner /data
USER runner
ENV APP_DB=/data/app.db PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "app/server.py"]
