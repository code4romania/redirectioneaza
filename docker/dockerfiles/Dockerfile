ARG NODE_VERSION=24.11.1
ARG PYTHON_VERSION=3.14.3
ARG S6_OVERLAY_VERSION=3.2.1.0


FROM node:${NODE_VERSION}-alpine AS frontend

WORKDIR /build

COPY ./backend/assets assets
COPY ./backend/templates templates
COPY ./backend/package.json ./backend/package-lock.json ./backend/postcss.config.js ./backend/vite.config.js ./

RUN npm ci --no-audit --ignore-scripts && \
    npm run build


FROM python:${PYTHON_VERSION}-trixie AS backend

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl ca-certificates \
    gettext && \
    apt-get clean

# Make sure scripts in .local are usable:
ENV PATH="/root/.local/bin:${PATH}"

# Download the latest UV installer
ADD ./docker/third-party/uv/installer.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Python virtualenv paths
ENV VIRTUAL_ENV=/opt/venv
RUN uv venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /build

COPY ./backend/pyproject.toml ./backend/uv.lock ./
RUN uv sync --active --locked --compile-bytecode


FROM python:${PYTHON_VERSION}-slim-trixie

ENV PYTHONUNBUFFERED=1

ENV DEBUG=False
ENV ENVIRONMENT=production
ENV LOG_LEVEL=${LOG_LEVEL:-WARNING}

ENV RUN_MIGRATIONS=${RUN_MIGRATIONS:-True}
ENV RUN_COMPILE_MESSAGES=${RUN_COMPILE_MESSAGES:-True}
ENV RUN_COLLECT_STATIC=${RUN_COLLECT_STATIC:-True}
ENV RUN_CREATE_SUPER_USER=${RUN_CREATE_SUPER_USER:-True}
ENV RUN_SEED_GROUPS=${RUN_SEED_GROUPS:-True}

ENV IS_CONTAINERIZED=True

ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    cron nginx gcc xz-utils gettext

# configure process manager
ARG S6_OVERLAY_VERSION
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz


COPY ./docker/nginx/nginx.conf /etc/nginx/sites-available/default
COPY ./docker/s6-rc.d /etc/s6-overlay/s6-rc.d


# Python virtualenv paths
ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

ENV SOURCE_DIR="/var/www/redirect"

# Copy the backend and frontend source code:
COPY --from=backend "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY ./backend/ "${SOURCE_DIR}/backend/"

COPY --from=frontend /build/dist/ "${SOURCE_DIR}/backend/dist/"


ARG VERSION
ARG REVISION
ENV VERSION="${VERSION}"
ENV REVISION="${REVISION}"

RUN touch "${SOURCE_DIR}/.version" && \
    echo "$VERSION+$(echo ${REVISION} | cut -c 1-7)" > "${SOURCE_DIR}/.version"

ENTRYPOINT ["/init"]


WORKDIR "${SOURCE_DIR}/"

EXPOSE 80
