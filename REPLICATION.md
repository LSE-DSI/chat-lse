# Rag on Postgres Replication

This repo contains the minimal codes to replicate the Rag on Postgres project. The code has been tested on Windows 11, Ubuntu 24.04 LTS, and MacOS (M2). 

Modifications:

- Removed all Azure components
- Removed all VSCode-related configurations
- Removed fontend router in the fastapi_app
- Removed dependency on close-sourced OpenAI chat and embedding models 

## ⚙️ Setup

### Requirements

Make sure the following are properly installed on your OS: 

- [VSCode](https://code.visualstudio.com/)
- [Docker](https://docs.docker.com/engine/install/)
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

### VS Code setup

1. Git clone the repository to your `~/Workspace` folder

2. Open a fresh new VSCode window (to avoid conflicts with other projects). You can do this by clicking on 'File' -> 'New Window'.

3. Now click on 'File' -> 'Add Folder to Workspace' and select the folder you just cloned.

4. Open the terminal in VSCode by clicking on 'Terminal' -> 'New Terminal' and create a virtual environment. 

```bash
# Use venv as an example. Can also use other virtual environments like conda

$ cd chat-lse # Make sure in the project root directory
$ python3 -m venv .venv
$ source .venv/bin/activate
```

### Setup the environments

1. Start the Postgres docker container and verify the container is running. The STATUS of the container shoule be something like "Up 2 seconds".

```bash
$ docker run -itd --name chatlse-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_PASSWORD=chatlse -e POSTGRES_USER=chatlse -e POSTGRES_DB=chatlse -d pgvector/pgvector:0.7.1-pg16

# To verify the container is up and running:
$ docker ps -a

CONTAINER ID   IMAGE                          COMMAND                  CREATED         STATUS         PORTS                                       NAMES
45d7301f5ef8   pgvector/pgvector:0.7.1-pg16   "docker-entrypoint.s…"   2 seconds ago   Up 2 seconds   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp   chatlse-postgres
```

2. Download [Ollama](https://ollama.com/download) or pull its docker image using: 

CPU only: 
```bash
$ docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

Nvidia GPU 
```bash
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

3. Generate sample LSE seed data by running: 

```bash
$ python fastapi_app/setup_seeddata_lse.py 
```
(use python or python3 depend on your set up)

4. Setup the Fastapi app and initialize database by running the setup script:

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/setup.sh
```

5. Setup the frontend app:

```bash
$ cd frontend # Go to chat-lse/frontend folder
$ npm install
```

You might see the following warning. We can ignore it for now.

```bash
1 moderate severity vulnerability

To address all issues, run:
  npm audit fix

Run `npm audit` for details.
```

### Runing the code

1. Start the fastapi app:

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/start_fastapi_app.sh
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

2. Start the frontend. Open a new terminal and run:

```bash
$ cd frontend # Go to chat-lse/frontend folder
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

3. Open http://localhost:5173/ in your web browser to try the app.