FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -r nutrisense

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run pytest (allow failure with || true as requested)
RUN pytest tests/ -v || true

# Change ownership
RUN chown -R nutrisense:nutrisense /app

# Switch to non-root user
USER nutrisense

# Environment variables
ENV PORT=8080
EXPOSE 8080

# Command to run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
