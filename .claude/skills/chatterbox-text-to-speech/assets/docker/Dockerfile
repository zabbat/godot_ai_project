# Voice tools in Docker (chatterbox-text-to-speech skill, "Chatterbox in Docker").
# One Linux image with the project's two locked uv environments, built from the committed uv.lock
# files, so the versions are the same as a local install:
#   /opt/venv/chatterbox  from <cbx>/settings  (Chatterbox, torch 2.8.0 cu128)  -> cbx-python
#   /opt/venv/kokoro      from <kok>/settings      (faster-whisper, librosa, kokoro) -> kok-python
# Both use the same torch build; uv hard-links the shared files, so torch is stored once.
# Used when Windows (Smart App Control, antivirus, a company policy) blocks Python DLLs locally.
# The project is mounted at /work (compose.yaml); the scripts find <cbx>/ from there.
FROM python:3.11.14-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ffmpeg libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=hardlink \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/local/bin/python3.11

WORKDIR /build
COPY <cbx>/settings/pyproject.toml <cbx>/settings/uv.lock cbx/
COPY <kok>/settings/pyproject.toml <kok>/settings/uv.lock kok/

# One RUN: the uv cache and both environments share a layer, so the hard links hold and the
# cache can be removed afterwards without losing files.
RUN export UV_CACHE_DIR=/opt/uvcache \
 && UV_PROJECT_ENVIRONMENT=/opt/venv/chatterbox uv sync --frozen --no-install-project --project cbx \
 && UV_PROJECT_ENVIRONMENT=/opt/venv/kokoro uv sync --frozen --no-install-project --project kok \
 && rm -rf /opt/uvcache

# Wrapper scripts, not symlinks: a symlink to a venv's python resolves to the base interpreter
# and loses the venv (ModuleNotFoundError).
RUN printf '#!/bin/sh\nexec /opt/venv/chatterbox/bin/python "$@"\n' > /usr/local/bin/cbx-python \
 && printf '#!/bin/sh\nexec /opt/venv/kokoro/bin/python "$@"\n' > /usr/local/bin/kok-python \
 && chmod +x /usr/local/bin/cbx-python /usr/local/bin/kok-python

WORKDIR /work
