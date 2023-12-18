FROM ubuntu:latest
LABEL maintainer="joshua.ogunyinka@codethink.co.uk"

RUN export DEBIAN_FRONTEND=noninteractive; \
    apt update && \
    apt install -y python3 python-is-python3 python3-pip && \
    pip install black && \
    apt clean

# ENTRYPOINT ["black", "--"]

