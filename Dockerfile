# check=skip=JSONArgsRecommended
FROM node:22-alpine AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt \
    && useradd --system --no-create-home --shell /usr/sbin/nologin garten
COPY server/ server/
COPY --from=web /app/web/dist web/dist
ENV WEB_DIST=/app/web/dist PORT=8000
USER garten
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/gesundheit' % os.environ.get('PORT', '8000'), timeout=3)"
# Shell-Form, damit $PORT greift; exec ersetzt die Shell → gunicorn bekommt SIGTERM direkt
CMD exec gunicorn -b "0.0.0.0:${PORT}" -w 2 --threads 16 --timeout 60 --chdir server app:app
