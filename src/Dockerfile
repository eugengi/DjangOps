# syntax=docker/dockerfile:1

# This build-specific ARG is named `TARGET`
# to avoid conflict with Django's ENV `ENVIRONMENT`,
# which determines app settings to use.
ARG TARGET=production

# ======================================================================================
# Stage 0: Provision the standalone uv binary
# ======================================================================================

ARG UV_VERSION="0.11.19"
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-binary

# ======================================================================================
# Stage 1: Build Environment
# ======================================================================================

ARG PYTHON_VERSION="3.12.13"
ARG ALPINE_VERSION="3.23"
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS build-stage

LABEL \
    author="Eugene Mwangi" \
    contact="mwangi.em37@gmail.com" \
    version="0.7.2" \
    license="MIT"

# set global directories for src to live across all stages.
ENV BASE=/usr/src/app
WORKDIR $BASE
ENV APP=$BASE/src

# set pkg-manger specific env variables.
ENV UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local" \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_CACHE_DIR="/root/.cache/uv"

# provision package manager (changes frequently based on `uv` version in pyproject.toml)
COPY --from=uv-binary /uv /usr/local/bin/uv

# install app's base runtime dependencies.
ENV UV_INSTALL="uv sync --locked"
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL}

# set shareable user and home arguments across stages.
# this comes last so that custom user args don't force a reinstall of base deps.
ARG UID=1000 APPUSER=appuser
ENV UID=${UID} APPUSER=${APPUSER}

# ======================================================================================
# Least-privilege user mode (inherits from build stage)
# ======================================================================================

FROM build-stage AS local-rootless

ENV APPUSER_HOME="/home/${APPUSER}"

# hadolint ignore=SC3028
RUN adduser \
    --gecos "" \
    --home "${APPUSER_HOME}" \
    --shell "/bin/sh" \
    --system \
    --uid "${UID}" \
    "${APPUSER}"

FROM build-stage AS rootless

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
# Environment: testing (inherits from local rootless)
# ======================================================================================

FROM local-rootless AS env-testing

ENV ENVIRONMENT=testing
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group test

# ======================================================================================
# Environment: development (inherits from local rootless)
# ======================================================================================

FROM local-rootless AS env-develop

ENV ENVIRONMENT=develop UV_NO_DEV=0
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group dev

# ======================================================================================
# Environment: production (inherits from rootless)
# ======================================================================================

FROM rootless AS env-production

ENV ENVIRONMENT=production
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    ${UV_INSTALL} --group prod

# ======================================================================================
# Final Stage: use build-arg to decide which environment to “bridge”
# ======================================================================================

# hadolint ignore=DL3006
FROM env-${TARGET} AS final-stage

# set python-specific env variables.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY ./src/ "${APP}"
WORKDIR "${APP}"
EXPOSE 8000

# ======================================================================================
# Runtime: application execution (inherits from Final Stage)
# ======================================================================================

FROM final-stage AS local-runtime

# set user-writeable, pytest cache dir for local target stages.
ENV PYTEST_ADDOPTS="-o cache_dir=${APPUSER_HOME}/.cache/pytest/.pytest_cache"

# change ownership of src directory to non-root user for local targets.
# hadolint ignore=SC3028
RUN chown -R ${UID} "${APP}"

USER ${APPUSER}
ENTRYPOINT ["python3", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

FROM final-stage AS prod-runtime

USER ${APPUSER}
ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
