# Infrastructure probe only: this image does not contain the MS-Agent WebUI.
# Match the existing Aone toolchain and public dependency sources.
FROM node:22-bookworm-slim AS node-probe
WORKDIR /probe
RUN corepack enable && corepack prepare pnpm@10.17.1 --activate \
 && printf '{"name":"image-preflight","private":true}' > package.json \
 && pnpm add --save-exact is-number@7.0.0 \
 && pnpm install --frozen-lockfile \
 && node -e "require('node:assert')(require('is-number')(42))" \
 && pnpm --version > pnpm-version.txt

FROM python:3.12-slim-bookworm
ARG UV_VERSION=0.12.8
ENV PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    DEBIAN_FRONTEND=noninteractive

RUN pip install --no-cache-dir --only-binary=:all: --timeout 30 --retries 1 \
        -i https://mirrors.aliyun.com/pypi/simple/ "uv==${UV_VERSION}" \
 && uv --version && uvx --version

RUN set -eu; \
    sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    apt-get -o Acquire::Retries=1 -o Acquire::https::Timeout=30 update; \
    apt-get -o Acquire::Retries=1 -o Acquire::https::Timeout=30 install -y --no-install-recommends ca-certificates curl git gnupg tini; \
    curl --connect-timeout 15 --max-time 120 -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/setup-node.sh; \
    bash /tmp/setup-node.sh; \
    apt-get -o Acquire::Retries=1 -o Acquire::https::Timeout=30 install -y --no-install-recommends nodejs; \
    rm -f /tmp/setup-node.sh; \
    rm -rf /var/lib/apt/lists/*

RUN uv pip install --system --index-url https://mirrors.aliyun.com/pypi/simple/ "httpx==0.28.1"

COPY --from=node-probe /probe /opt/probe
COPY server.cjs /opt/probe/server.cjs
WORKDIR /opt/probe
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.cjs"]
