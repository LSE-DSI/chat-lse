# Contributing to _ChatLSE_

## Introduction

The Chat LSE Project is based on the [Rag on Postgres](https://github.com/pamelafox/rag-on-postgres) project with modifictaions to adapt to LSE's development and production environment.

Major modifications are: 

- Removed all Azure components
- Removed all VSCode-related configurations
- Removed dependency on close-sourced OpenAI chat and embedding models

The code has been tested on Windows 11, Ubuntu 20.04 LTS and MacOS(M2).

## Architecture and structure

The overall architecture of the app is shown in the figure:

![arch](img/arch.png "Architecture of the app")

There are 4 main components, the Frontend APP (FluentUI, React JS), the backend APP (FastAPI), PostgreSQL database and Ollama service. 

To run the full app, all four components have to be setup properly either on a local development machine or on a remote server. 

For development purpose, the frontend APP, backend APP should always be setup on a local machine. 

PostgreSQL and Ollama could be setup locally or use a remote setup. 

## Requirements

Make sure the following software are properly installed on your OS: 

- [VSCode](https://code.visualstudio.com/)
- [Docker](https://docs.docker.com/engine/install/)
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

## Table of Content 
  1. [Setup PostgreSQL locally](#1-setup-postgresql-locally)
  2. [(Optionally) Setup Ollama locally](#2-optionally-setup-ollama-locally)
  3. [Setup environment](#3-setup-environment)
    3.1. [Install Python dependencies](#31-install-python-dependencies)
    3.2. [Config environment variables](#32-config-environment-variables)
  4. [Initialise the database](#4-initialise-the-database)
    4.1. [Run crawler to populate database](#41-run-crawler-to-populate-database)
    4.2. [Run the embedding script](#42-run-the-embedding-script)
  5. [Start the FastAPI APP](#5-start-the-fastapi-app)
  6. [Setup and run Frontend APP](#6-setup-and-run-frontend-app)
    6.1. [Install npm dependencies](#61-install-npm-dependencies)
    6.2. [Start the frontend APP](#62-start-the-frontend-app)
    6.3. [Use the APP](#63-use-the-app)

## 1. Setup PostgreSQL locally

Run PostrgeSQL using docker container:

```bash
$ docker run -itd --name chatlse-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_PASSWORD=chatlse -e POSTGRES_USER=chatlse -e POSTGRES_DB=chatlse -d pgvector/pgvector:0.7.1-pg16
```

To verify the container is up and running:

```bash
$ docker ps -a

CONTAINER ID   IMAGE                          COMMAND                  CREATED         STATUS         PORTS                                       NAMES
45d7301f5ef8   pgvector/pgvector:0.7.1-pg16   "docker-entrypoint.s…"   2 seconds ago   Up 2 seconds   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp   chatlse-postgres
```

The STATUS of the container shoule be something like "Up 2 seconds".

## 2. (Optionally) Setup Ollama locally

Download [Ollama](https://ollama.com/download)(recommended) or pull its docker image using: 

CPU only: 
```bash
$ docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

Nvidia GPU 
```bash
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## 3. Setup environment

### 3.1 Install Python dependencies

Open the terminal in VSCode by clicking on 'Terminal' -> 'New Terminal' and create a virtual environment. 

```bash
# Use conda as an example. Can also use other virtual environments like venv

conda create -n chat-lse python=3.11 ipython
conda activate chat-lse # or the equivalent for your OS
```

(Important) Ensure that `pip` refers to the pip inside the conda environment we just created:

```bash
which pip
```

Install dependencies

```bash
pip install -r requirements.txt
```

### 3.2 Config environment variables

Copy **.env.sample** into **.env**.

#### Set Postgres Host

```
# For local setup
POSTGRES_HOST=localhost
```

```
# Remote setup, for testing and deployment only
POSTGRES_HOST=<Host IP address>
```

#### Set Ollama Host

```
# For local setup. Only use this if you have local Ollama running.
OLLAMA_ENDPOINT=http://localhost:11434/v1
```

```
# For Remote setup
OLLAMA_ENDPOINT=http://<Host IP address>:11434/v1
```

## 4. Initialise the database

### 4.1 Run crawler to populate database 

The following script will take a while for the first time you run it as it crawls through all the files and webpages with lse.ac.uk domain name. Subsequent runs of the crawler should be quicker as it only updates the files and webpages that has changed. 

Run the following code to start the crawler :

```bash
sh scripts/start_crawlers.sh 
```

### 4.2 Run the embedding script

Set up embedding type in the **.env** file: 

```
# Select embedding type from ["simple_embeddings", "title_embeddings", "context_embeddings"]
EMBEDDING_TYPE=title_embeddings
```

The default setting is `title_embeddings` as our experiments show that it provides the best results. 

The following script will take a while for the first time you run it as it generates embeddings for all the documents in the database. Subsequent runs of the embedding script should be quicker as it only updates the embeddings for the documents that has changed.

Run the following code to start the embedding script:

```bash
sh scripts/embed_db.sh
```

## 5. Start the FastAPI APP

We need our API to be running in the background, to handle requests from the website to LLAMA and Postgres:

```bash 
sh ./scripts/start_fastapi_app.sh
```

You should see something like:

```bash
INFO:     Will watch for changes in these directories: ['<your-path-to>/chat-lse']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [7609] using WatchFiles
WARNING:  ASGI app factory detected. Using it, but please consider setting the --factory flag explicitly.
INFO:     Started server process [7611]
INFO:     Waiting for application startup.
INFO:ragapp:Authenticating to PostgreSQL using password...
INFO:ragapp:Authenticating to OpenAI using Ollama...
INFO:ragapp:Authenticating to OpenAI using Ollama...
INFO:     Application startup complete.
```

## 6. Setup and run Frontend APP

### 6.1 Install npm dependencies

```bash
# Go to chat-lse/frontend
cd frontend 
npm install
```

You might see the following warning. We can ignore it for now.

```bash
1 moderate severity vulnerability

To address all issues, run:
  npm audit fix

Run `npm audit` for details.
```

### 6.2 Start the frontend APP

Open a new terminal and run:

```bash
# Go to chat-lse/frontend
$ cd frontend 
$ npm run dev
```

You should see something like:

```bash
> frontend@0.0.0 dev
> vite


  VITE v4.5.2  ready in 309 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

## 6.3 Use the APP

Open http://localhost:5173/ in the web browser to try the app.
