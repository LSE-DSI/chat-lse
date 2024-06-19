# hash:sha256:54d8a87d88a1c9bb14f5e3e01540e223b03f20516abf34f3a295e51dc17ac646
FROM registry.codeocean.dascl.lse.ac.uk/codeocean/tensorflow:2.11-python3.10-cuda11.7.0-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

ADD "https://github.com/coder/code-server/releases/download/v4.9.0/code-server-4.9.0-linux-amd64.tar.gz" /.code-server/code-server.tar.gz


RUN cd /.code-server \
	&& tar -xvf code-server.tar.gz \
	&& rm code-server.tar.gz \
	&& ln -s /.code-server/code-server-4.9.0-linux-amd64/bin/code-server  /usr/bin/code-server

RUN pip install https://download.pytorch.org/whl/cu117/torch-2.0.0%2Bcu117-cp310-cp310-linux_x86_64.whl

RUN pip3 install -U --no-cache-dir \
    scrapy \
    pandas>=2 \
    aiohttp==3.9.5 \ 
    aiosignal==1.3.1 \
    annotated-types==0.6.0 \
    anyio==4.3.0 \ 
    async-timeout==4.0.3 \ 
    asyncpg==0.29.0 \
    attrs==23.2.0 \
    certifi==2024.2.2 \
    cffi==1.16.0 \ 
    charset-normalizer==3.3.2 \
    click==8.1.7 \
    cryptography==42.0.6 \
    distro==1.9.0 \
    environs==11.0.0 \ 
    fastapi==0.110.3 \ 
    frozenlist==1.4.1 \ 
    greenlet==3.0.3 \ 
    gunicorn==20.1.0 \ 
    h11==0.14.0 \
    httpcore==1.0.5 \ 
    httptools==0.6.1 \ 
    httpx==0.27.0 \
    idna==3.7 \
    markdown-it-py==3.0.0 \
    marshmallow==3.21.2 \
    mdurl==0.1.2 \
    multidict==6.0.5 \
    numpy==1.26.4 \ 
    openai==1.25.2 \
    openai-messages-token-helper==0.1.3 \
    packaging==24.0 \
    pgvector==0.2.5 \
    pillow==10.3.0 \
    pycparser==2.22 \ 
    pydantic==2.7.1 \
    pydantic-core==2.18.2 \
    pygments==2.18.0 \
    pyjwt[crypto]==2.8.0 \
    python-dotenv==1.0.1 \ 
    pyyaml==6.0.1 \
    regex==2024.4.28 \
    requests==2.31.0 \
    rich==13.7.1 \
    sniffio==1.3.1 \
    sqlalchemy[asyncio]==2.0.30 \
    starlette==0.37.2 \
    tiktoken==0.6.0 \
    tqdm==4.66.4 \
    typing-extensions==4.11.0 \
    urllib3==2.2.1 \
    uvicorn[standard]==0.23.2 \
    watchfiles==0.21.0 \
    websockets==12.0 \
    yarl==1.9.4

# https://code.visualstudio.com/docs/setup/linux#_visual-studio-code-is-unable-to-watch-for-file-changes-in-this-large-workspace-error-enospc
RUN echo "fs.inotify.max_user_watches=524288" >> /etc/sysctl.conf

COPY postInstall /
RUN /postInstall