FROM python:3-slim-bullseye

RUN apt-get update && apt-get install -y \
    parted \
    wpasupplicant \
    zip \
    unzip \
    ssh \
    rsync \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY requirements.yml .
RUN ansible-galaxy collection install --no-cache -r requirements.yml

RUN echo "\
alias ap='ansible-playbook' \n\
alias a='ansible'\n\
" >> ~/.bashrc

WORKDIR /opt/ansible
COPY . .

CMD [ "bash" ]
