FROM ubuntu:bionic

# install latest python and nodejs
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      curl \
      software-properties-common \
      gcc g++ make

# Install nodejs and add 'hold' such that it doesn't get upgraded
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs npm

RUN npm install -g elm

VOLUME /bornhack/  # for mounting the whl files into other docker containers

CMD cd /bornhack/schedule && \
    make all
