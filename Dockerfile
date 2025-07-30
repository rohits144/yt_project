# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /yt_project

# Copy project files
COPY . .

# Install dependencies via uv (uses pyproject.toml + uv.lock)
RUN uv pip install --system --no-deps

# Expose port
EXPOSE 8000

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
