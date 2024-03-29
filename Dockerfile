FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y \
    fdisk \
    parted \
    wpasupplicant \
    openssl \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
COPY raspios_anvil/ raspios_anvil/

ENTRYPOINT ["python", "-m", "raspios_anvil"]
