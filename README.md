# 💬 ChatLSE

In this project, we will gather all public LSE documents and webpages into a database (LSE Crawler) and then develop a chat interface using an LLM mediated by the [langchain](https://python.langchain.com/v0.2/docs/introduction/) package. Think of it as a ChatGPT meant to be particularly knowledgeable of LSE documents.

Since we intend to release this product to LSE staff and possibly students, we will treat this as a software development project, setting deadlines for an alpha and a beta launch. We will initially target a small group of early adopters and later expand to a larger audience. In addition to developing the ChatLSE server and UI, we will also create a database structure to track user engagement with the tool, with the potential for performing Reinforcement Learning from Human Feedback (I doubt we’ll have the time, but one can hope…).

## Benefits of this project

By the end of Summer 2024, we want to be proud to say:

1) we have created a valuable service to the LSE staff community,
2) we have written a short report (2-3 pages) to demonstrate our methodology of an open-source RAG solution, and
3) we have tested the capabilities of DSI's new on-premises cloud infrastructure.

## 🔗 Links

- 🗂️ [Sharepoint folder](https://lsecloud.sharepoint.com/:f:/r/sites/TEAM_DSI-Executive/Shared%20Documents/Computing/ChatLSE?csf=1&web=1&e=pRgfW9): for interactive documents (MS Word documents) or academic papers (PDFs).
- ☁️ [CodeOcean](#): Where we will keep the data


## ⚙️ Setup

### Requirements

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- [VSCode](https://code.visualstudio.com/)
- [Git](https://git-scm.com/)
- [Jupyter Extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) extension for VSCode
- [GitHub Pull Requests and Issues](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github) extension for VSCode

### VS Code setup

1. Git clone the repository to your `~/Workspace` folder

2. Open a fresh new VSCode window (to avoid conflicts with other projects). You can do this by clicking on 'File' -> 'New Window'.

3. Now click on 'File' -> 'Add Folder to Workspace' and select the folder you just cloned.

4. Open the terminal in VSCode by clicking on 'Terminal' -> 'New Terminal' and run the following commands to create a conda environment:

```bash
conda create -n chat-lse python=3.11 ipython
conda activate chat-lse # or the equivalent for your OS
```

5. (Important) Ensure that `pip` refers to the pip inside the conda environment we just created:

```bash
which pip
```

 this should output something like `/home/your-username/miniconda3/envs/chat-lse/bin/pip`

6. Assuming you've fixed the `pip` path, install the required packages:

```bash
pip install -r requirements.txt
```

## Running the crawler

1. First, ensure you have activated the `chat-lse` conda environment.

2. Run the following command from the root of the project to save the scraped data to a JSON file:

```bash
scrapy crawl lse_crawler
```

Note: with the current configuration, the crawler will save the data to `data/output.jl`(JSON Lines format). Read about scrapy's [item exporters](https://docs.scrapy.org/en/latest/topics/exporters.html#using-item-exporters) for more information.
