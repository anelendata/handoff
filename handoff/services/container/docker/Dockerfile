# Pull base image.
FROM ubuntu:18.04

MAINTAINER Daigo Tanaka <daigo.tanaka@gmail.com>

# upgrade is not recommended by the best practice page
# RUN apt-get -y upgrade

# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive

# Define locale
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8

# Install dependencies via apt-get
# Note: Always combine apt-get update and install
RUN set -ex \
    && buildDeps=' \
        python3-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        build-essential \
        libblas-dev \
        liblapack-dev \
        libpq-dev \
    ' \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        sudo \
        apparmor-utils \
        python3-requests \
        python3-setuptools \
        python3-pip \
        python3-venv \
        apt-utils \
        curl \
        rsync \
        netcat \
        locales \
        wget \
        git \
        openssh-server \
        gdebi-core \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

#######
#  Add tini
ENV TINI_VERSION v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

########
# SSH stuff

RUN mkdir -p /var/run/sshd

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
# Or do this?
# RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

COPY . /app/
RUN chmod 777 -R /app

WORKDIR /app

RUN pip3 install wheel

RUN ./script/install_handoff

# It is recommended to make virtual envs for each process
RUN handoff workspace install -p project -w workspace

# Make sure to delete these directories in case sensitive information was accidentally copied.
RUN rm -fr project
RUN rm -fr workspace/config
RUN rm -fr workspace/files
RUN rm -fr workspace/artifacts

RUN chmod a+x /usr/local/bin/*

ENTRYPOINT [ "/tini", "--" ]
CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"dev"} -a
