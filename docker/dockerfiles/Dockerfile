ARG NODE_VERSION=20.17.0
ARG PYTHON_VERSION=3.12.6


FROM node:${NODE_VERSION}-bookworm as frontend

# set up a user and group for bower since it's not working as root
ARG USER=builduser
ARG GROUP=${USER}
ARG UID=10000
ARG GID=10000

RUN groupadd --gid ${GID} --non-unique ${GROUP} && \
    useradd --create-home --shell /bin/bash --uid ${UID} --gid ${GID} --non-unique ${USER}

USER ${USER}


WORKDIR /home/${USER}/redirect/build
ENV PATH /home/${USER}/redirect/build/node_modules/.bin:$PATH

# install the frontend libraries:
COPY ./backend/package.json ./backend/package-lock.json ./backend/bower.json ./backend/.bowerrc ./
RUN npm cache clean --force && npm ci && bower install


FROM python:${PYTHON_VERSION}-bookworm as backend

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    gettext && \
    python3 -m pip install --upgrade pip setuptools cython

# Python virtualenv paths
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /build
COPY ./backend/requirements.txt .

RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install -r ./requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONUNBUFFERED=1

ENV DEBUG=False
ENV ENVIRONMENT=production
ENV LOG_LEVEL=${LOG_LEVEL:-WARNING}

ENV RUN_MIGRATIONS=True
ENV RUN_COMPILE_MESSAGES=True
ENV RUN_COLLECT_STATIC=True
ENV RUN_CREATE_SUPER_USER=True
ENV RUN_SEED_GROUPS=True

ENV IS_CONTAINERIZED=True

ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    nginx gcc xz-utils gettext

# configure process manager
ARG S6_OVERLAY_VERSION=3.2.0.0
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

COPY --from=frontend /home/builduser/redirect/build/bower_components/ /var/www/redirect/backend/bower_components/


ARG VERSION
ARG REVISION
ENV VERSION=${VERSION}
ENV REVISION=${REVISION}

RUN touch /var/www/redirect/.version && \
    echo "$VERSION+$(echo ${REVISION} | cut -c 1-7)" > /var/www/redirect/.version

ENTRYPOINT ["/init"]


WORKDIR /var/www/redirect/

EXPOSE 80
