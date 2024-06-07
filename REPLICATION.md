# Rag on Postgres Replication

This repo contains the minimal codes to replicate the Rag on Postgres project. The code has been tested on Windows 11 and Ubuntu 24.04 LTS.

Modifications:

- Removed all Azure components
- Removed all VSCode-related configurations
- Removed fontend router in the fastapi_app

## ⚙️ Setup

### Requirements

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

1. **[IMPORTANT]** Copy `.env.sample` into a `.env` file and replace *YOUR-OPENAI-API-KEY* with your openai api key. Do not change other configs unless you know what you are doing.

```
# Needed for OpenAI.com:
OPENAICOM_KEY=YOUR-OPENAI-API-KEY # Replace this value
...
```

2. Start the Postgres docker container.

```bash
$ docker run -itd --name chatlse-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_PASSWORD=chatlse -e POSTGRES_USER=chatlse -e POSTGRES_DB=chatlse -d pgvector/pgvector:0.7.1-pg16
```

3. Setup the Fastapi app and initialize database by running the setup script:

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/setup.sh
```

4. Setup the frontend app:

```bash
$ cd frontend # Go to chat-lse/frontend folder
$ npm install
```

### Runing the code

1. Start the fastapi app:

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/start_fastapi_app.sh
```

2. Start the frontend. Open a new terminal and run:

```bash
$ cd frontend # Go to chat-lse/frontend folder
$ npm run dev
```
