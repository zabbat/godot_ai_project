# Sandboxed Blender MCP server: headless Blender 5.1 + the official Blender Lab MCP server.
#
# Build (PowerShell; the MCP server source is a clone of https://projects.blender.org/lab/blender_mcp):
#   docker build -t blender-mcp-sandbox --build-context mcpsrc="$HOME\blender_mcp\mcp" <this folder>
#
# Claude Code runs it with --network none and sees only the folders mounted with -v.
# To change Blender: set BLENDER_VERSION and BLENDER_SHA256 from
# https://download.blender.org/release/Blender<major.minor>/blender-<version>.sha256 (the linux-x64 line).
FROM debian:bookworm-slim

ARG BLENDER_VERSION=5.1.2
ARG BLENDER_SERIES=5.1
ARG BLENDER_SHA256=aaccb355f50183979b698bcce7467103a76261b5fa59f4972295842662a285fb

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils python3 python3-venv \
        libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libxkbcommon-x11-0 \
        libsm6 libice6 libgl1 libegl1 libglu1-mesa libvulkan1 \
        libwayland-client0 libwayland-cursor0 libwayland-egl1 libdecor-0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/blender.tar.xz \
        "https://download.blender.org/release/Blender${BLENDER_SERIES}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && echo "${BLENDER_SHA256}  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir /opt/blender \
    && tar -xJf /tmp/blender.tar.xz -C /opt/blender --strip-components=1 \
    && rm /tmp/blender.tar.xz \
    && ln -s /opt/blender/blender /usr/local/bin/blender

# Empty scene to start new files from (the _for_cli tools need an existing .blend to open).
RUN blender --background --factory-startup --python-expr \
        "import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.save_as_mainfile(filepath='/opt/empty.blend')" \
    && test -f /opt/empty.blend

COPY --from=mcpsrc . /opt/blmcp-src
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir /opt/blmcp-src

RUN useradd -m -u 1000 blender && mkdir /work && chown blender:blender /work
USER blender
WORKDIR /work

ENV BLENDER_PATH=/usr/local/bin/blender \
    BLENDER_MCP_HOST=127.0.0.1

ENTRYPOINT ["/opt/venv/bin/blender-mcp"]
