# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and move it to a globally accessible location
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv

# Clone your Django repo
RUN git clone https://github.com/rohits144/yt_project.git /yt_project

# Set working directory
WORKDIR /yt_project

# Install dependencies with uv
RUN uv sync

# Expose the Django development server port
EXPOSE 8000

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh

# Make it executable
RUN chmod +x /entrypoint.sh

# Use the entrypoint script as the container command
CMD ["/entrypoint.sh"]
