FROM alpine:latest

ARG GHIDRA_VERSION=latest
ARG JDK_VERSION=openjdk11

RUN apk --update add \
    ${JDK_VERSION} \
    bash \
    gradle \
    unzip \
    python3 \
    py3-pip

# Install requests for ghidra-grabber.py
RUN python3 -m pip install requests
COPY --chmod=0755 bin/ghidra-grabber.py /usr/local/bin

# Set up environment
ENV GHIDRA_INSTALL_DIR=/ghidra

# Install Ghidra
RUN /usr/local/bin/ghidra-grabber.py --version=${GHIDRA_VERSION} /${GHIDRA_INSTALL_DIR}

# Set up entrypoint
ENTRYPOINT [ "/bin/bash", "-c" ]
