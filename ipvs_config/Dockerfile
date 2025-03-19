FROM ubuntu:latest

RUN apt-get update \
    && apt-get install -y iproute2 curl ipvsadm

COPY setup-ipvs.sh /usr/local/bin/setup-ipvs.sh

RUN chmod +x /usr/local/bin/setup-ipvs.sh

CMD ["/usr/local/bin/setup-ipvs.sh"]