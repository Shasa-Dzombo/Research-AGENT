FROM python:3.12-slim

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy requirements and install dependencies using uv (system-wide)
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Set default environment variables for Docker
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RELOAD=False
ENV DEBUG=False

EXPOSE 8000

# Run the application directly with system python
CMD ["python", "main.py"]
