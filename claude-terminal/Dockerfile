ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system packages and development tools
RUN apk add --no-cache \
    bash \
    curl \
    nano \
    nodejs \
    npm \
    python3 \
    py3-pip \
    py3-requests \
    py3-aiohttp \
    py3-yaml \
    py3-beautifulsoup4 \
    git \
    vim \
    wget \
    jq \
    tree \
    tmux \
    ttyd \
    yq

# Install Claude Code CLI via npm (avoids musl binary compatibility issues)
RUN npm install -g @anthropic-ai/claude-code@latest \
    && npm cache clean --force

# Install uv for running ha-mcp (Python package manager/runner)
# ha-mcp requires Python 3.13+ (pydantic-core wheels need cp313)
# Alpine ships Python 3.12, so we use uv to fetch Python 3.13 at build time
RUN apk add --no-cache uv \
    && uv python install 3.13

# Create directory for Claude configuration and set working directory
RUN mkdir -p /config/claude-config
WORKDIR /config

# Copy image upload service (uses aiohttp which is already installed via py3-aiohttp)
COPY image-service/ /opt/image-service/

# Copy startup script, modular scripts, and changelog
COPY run.sh /run.sh
COPY scripts/ /opt/scripts/
COPY CHANGELOG.md /opt/scripts/CHANGELOG.md
RUN chmod +x /run.sh \
    && chmod +x /opt/scripts/*.sh

# Use exec form for better signal handling
CMD ["/run.sh"]