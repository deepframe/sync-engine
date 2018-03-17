FROM ubuntu:16.04

MAINTAINER viktor@deepframe.io
RUN apt-get update && apt-get -y install python-software-properties\
       git \
       liblua5.2-dev \
       lua5.2 \
       unzip \
       build-essential \
       curl \
       g++ \
       gcc \
       language-pack-en \
       lib32z1-dev \
       libffi-dev \
       libmysqlclient-dev \
       libssl-dev \
       libxml2-dev \
       libxslt-dev \
       libzmq-dev \
       mercurial \
       mysql-client \
       pkg-config \
       python \
       python-dev \
       python-lxml \
       python-pip \
       python-setuptools \
       stow \
       sudo \
       supervisor \
       tmux \
       tnef \
       vim \
       wget


RUN mkdir -p /tmp/build
WORKDIR /tmp/build
ENV LIBSODIUM_VER=1.0.0

RUN curl -L -O https://github.com/jedisct1/libsodium/releases/download/${LIBSODIUM_VER}/libsodium-${LIBSODIUM_VER}.tar.gz
RUN echo 'ced1fe3d2066953fea94f307a92f8ae41bf0643739a44309cbe43aa881dbc9a5 *libsodium-1.0.0.tar.gz' | sha256sum -c || exit 1
RUN tar -xzf libsodium-${LIBSODIUM_VER}.tar.gz

WORKDIR /tmp/build/libsodium-1.0.0
RUN ./configure --prefix=/usr/local/stow/libsodium-${LIBSODIUM_VER} &&\
                  make -j4 &&\
                  rm -rf /usr/local/stow/libsodium-${LIBSODIUM_VER} &&\
                  mkdir -p /usr/local/stow/libsodium-${LIBSODIUM_VER} &&\
                  make install &&\
                  stow -d /usr/local/stow -R libsodium-${LIBSODIUM_VER} &&\
                  ldconfig

WORKDIR /tmp/build
RUN rm -rf libsodium-${LIBSODIUM_VER} libsodium-${LIBSODIUM_VER}.tar.gz

WORKDIR /opt
ENV LC_ALL=en_US.UTF-8
ENV LANF=en_US.UTF-8


## Usage of our extension of nylas-sync

RUN mkdir -p /var/lib/inboxapp/parts

RUN mkdir -p /var/log/inboxapp

RUN mkdir -p /etc/inboxapp

ENV PYTHONPATH=/opt/sync-engine

RUN mkdir /opt/sync-engine

WORKDIR /opt/sync-engine

COPY ./requirements.txt /opt/sync-engine/

#Update pip version
RUN pip install 'pyparsing==2.2.0'
# If python-setuptools is actually the old 'distribute' fork of setuptools,
# then the first 'pip install setuptools' will be a no-op.
RUN pip install 'pip==9.0.1' 'setuptools==34.3.1'
RUN hash pip        # /usr/bin/pip might now be /usr/local/bin/pip
RUN pip install 'pip==9.0.1' 'setuptools==34.3.1'

# Doing pip upgrade setuptools leaves behind this problematic symlink
RUN rm -rf /usr/lib/python2.7/dist-packages/setuptools.egg-info

RUN pip uninstall -y chardet

RUN pip install -r requirements.txt

COPY ./build-files/config.json /etc/inboxapp/config.json
COPY ./build-files/secrets.json /etc/inboxapp/secrets.json

COPY ./ /opt/sync-engine

RUN pip install -e .

VOLUME /var/lib/inboxapp

EXPOSE 5555

CMD ["python", "/opt/sync-engine/bin/inbox-api"]
