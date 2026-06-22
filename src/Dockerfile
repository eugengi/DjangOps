# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

# This build-specific ARG is named `TARGET`
# to avoid conflict with Django's ENV `ENVIRONMENT`,
# which determines app settings to use.
ARG TARGET=production
ARG UV_VERSION="0.11.14@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97"
ARG PYTHON_VERSION="3.12.13"
ARG ALPINE_VERSION="3.23"

# ======================================================================================
# Phase 0: Provision the standalone uv binary
# ======================================================================================
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-binary

# ======================================================================================
# Phase 1: Build Environments
# ======================================================================================
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS builder-base

ENV BASE=/usr/src/app
WORKDIR $BASE

# set pkg-manger specific env variables.
# install all deps into a dedicated venv as a portable cross-stage artifact.
ENV UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON_PREFERENCE=only-system \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_CACHE_DIR="/root/.cache/uv"

# provision package manager
COPY --from=uv-binary /uv /usr/local/bin/uv

# install app's base runtime dependencies.
ENV UV_INSTALL="uv sync --locked"
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL}

# ======================================================================================
# Builder Environment: testing (inherits from builder-base)
# ======================================================================================

FROM builder-base AS builder-testing

RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group test

# ======================================================================================
# Builder Environment: development (inherits from builder-base)
# ======================================================================================

FROM builder-base AS builder-develop

ENV UV_NO_DEV=0
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group dev

# ======================================================================================
# Builder Environment: production (inherits from builder-base)
# ======================================================================================

FROM builder-base AS builder-production

RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group prod

# ======================================================================================
# Bridge Target Environment: (inherits from builder-<testing|development|production>)
# ======================================================================================

# hadolint ignore=DL3006
FROM builder-${TARGET} AS target-builder

# ======================================================================================
# Phase 2: Runtime Environments
# ======================================================================================
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS runtime-base

LABEL \
    author="Eugene Mwangi" \
    contact="mwangi.em37@gmail.com" \
    version="0.7.2" \
    license="MIT"

ENV BASE=/usr/src/app
ENV APP=$BASE/src
WORKDIR "${APP}"
EXPOSE 8000

# set python-specific env variables.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=${TARGET}

# pull isolated virtual environment from the bridge stage.
COPY --from=target-builder /opt/venv /opt/venv

COPY ./src/ "${APP}"

# set shareable user arguments across final stages.
ARG UID=1000 APPUSER=appuser
ENV UID=${UID} APPUSER=${APPUSER}

# ======================================================================================
# Least-privilege user mode (inherits from runtime-base)
# ======================================================================================

FROM runtime-base AS local-rootless

ENV APPUSER_HOME="/home/${APPUSER}"
# hadolint ignore=SC3028
RUN adduser \
    --gecos "" \
    --home "${APPUSER_HOME}" \
    --shell "/bin/sh" \
    --system \
    --uid "${UID}" \
    "${APPUSER}"

FROM runtime-base AS rootless

# hadolint ignore=SC3028
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --system \
    --no-create-home \
    --uid "${UID}" \
    "${APPUSER}"

# ======================================================================================
# Runtime: target execution (inherits from least-privilege user mode)
# ======================================================================================

FROM local-rootless AS local-runtime

# set user-writeable, pytest cache dir for local target stages.
ENV PYTEST_ADDOPTS="-o cache_dir=${APPUSER_HOME}/.cache/pytest/.pytest_cache"

# change ownership of src directory to non-root user for local targets.
# hadolint ignore=SC3028
RUN chown -R ${UID} "${APP}"

USER ${APPUSER}
ENTRYPOINT ["python3", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

FROM rootless AS prod-runtime

USER ${APPUSER}
ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
