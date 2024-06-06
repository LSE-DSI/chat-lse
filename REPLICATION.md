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

### Runing the code

1. Copy `.env.sample` into a `.env` file and replace *YOUR-OPENAI-API-KEY* with your openai api key

2. Run the setup script to install dependencies and start postgres in a docker container

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/setup.sh
```

3. Start the fastapi app

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/start_fastapi_app.sh
```

4. Start the frontend. Open a new terminal and run:

```bash
$ cd chat-lse # Make sure in the project root directory
$ sh ./scripts/start_frontend.sh
```
