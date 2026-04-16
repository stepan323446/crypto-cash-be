FROM python:3.13-slim


# Installing UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
# Use system python version
ENV UV_SYSTEM_PYTHON=1
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

# Set App User
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m appuser

USER appuser

# Create app folder
WORKDIR /app
RUN chown appuser:appuser /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

USER root
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser
ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000

# Guidlines:
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# https://www.docker.com/blog/how-to-dockerize-django-app/