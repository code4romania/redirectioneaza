FROM node:18.17.1-bookworm-slim as frontend

WORKDIR /var/www/redirect/frontend

COPY ./frontend/ .

# install the frontend libraries:
RUN npm ci --no-audit --ignore-scripts && \
    npm run prod

FROM python:3.11.7-slim-bookworm as backend

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gettext git gcc g++ && \
    python3 -m pip install --upgrade pip setuptools cython

# Python virtualenv paths
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /build
COPY ./backend/requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install -r ./requirements.txt

FROM python:3.11.7-slim-bookworm

ENV PYTHONUNBUFFERED=1

ENV DEBUG=False
ENV ENVIRONMENT=production

ENV RUN_MIGRATIONS=True
ENV RUN_COMPILE_MESSAGES=True
ENV RUN_COLLECT_STATIC=True
ENV RUN_CREATE_ADMIN=True
ENV RUN_SEED_GROUPS=True
ENV ENABLE_DJANGO_ADMIN=False

ENV IS_CONTAINERIZED=True

ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    nginx gcc xz-utils gettext

# configure process manager
ARG S6_OVERLAY_VERSION=3.1.2.1
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME 0

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz


COPY ./docker/nginx/nginx.conf /etc/nginx/sites-available/default
COPY ./docker/s6-rc.d /etc/s6-overlay/s6-rc.d


# Python virtualenv paths
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# copy the backend and frontend source code:
COPY --from=backend "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY ./backend/ /var/www/redirect/backend/

COPY --from=frontend /var/www/redirect/frontend/dist/ /var/www/redirect/frontend/dist/

# activate the virtualenv:
RUN . "${VIRTUAL_ENV}/bin/activate"

ARG VERSION
ARG REVISION
ENV VERSION=${VERSION}
ENV REVISION=${REVISION}

RUN touch /var/www/redirect/.version && \
    echo "$VERSION+$(echo ${REVISION} | cut -c 1-7)" > /var/www/redirect/.version

ENTRYPOINT ["/init"]


WORKDIR /var/www/redirect/

EXPOSE 80
