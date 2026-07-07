# Santa Fe Half Marathon MCP server — container image.
# Serves the MCP endpoint (/mcp) and the results widget (/leaderboard) over HTTP.
FROM python:3.12-slim

# Don't buffer stdout/stderr so logs show up promptly in `docker logs`.
ENV PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (see .dockerignore for what's excluded).
COPY . .

EXPOSE 8000

# Simple healthcheck against the widget route.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/leaderboard', timeout=4).status==200 else 1)" || exit 1

CMD ["python", "server.py", "http"]
