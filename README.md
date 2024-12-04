# 💬 ChatLSE
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-8-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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

3. Run the following command from the root of the project to download all the documents:

```bash
scrapy crawl file_downloader
```

Note: with the current configuration, the crawler will save the data to `data/output.jl`(JSON Lines format). Read about scrapy's [item exporters](https://docs.scrapy.org/en/latest/topics/exporters.html#using-item-exporters) for more information.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tz1211"><img src="https://avatars.githubusercontent.com/u/114442618?v=4?s=500" width="500px;" alt="Terry Zhou"/><br /><sub><b>Terry Zhou</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/issues?q=author%3Atz1211" title="Bug reports">🐛</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=tz1211" title="Code">💻</a> <a href="#data-tz1211" title="Data">🔣</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=tz1211" title="Documentation">📖</a> <a href="#ideas-tz1211" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/pulls?q=is%3Apr+reviewed-by%3Atz1211" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jonjoncardoso"><img src="https://avatars.githubusercontent.com/u/896254?v=4?s=500" width="500px;" alt="Jon Cardoso-Silva"/><br /><sub><b>Jon Cardoso-Silva</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/commits?author=jonjoncardoso" title="Code">💻</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=jonjoncardoso" title="Documentation">📖</a> <a href="#ideas-jonjoncardoso" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/pulls?q=is%3Apr+reviewed-by%3Ajonjoncardoso" title="Reviewed Pull Requests">👀</a> <a href="#mentoring-jonjoncardoso" title="Mentoring">🧑‍🏫</a> <a href="#projectManagement-jonjoncardoso" title="Project Management">📆</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/akshsabherwal"><img src="https://avatars.githubusercontent.com/u/147533587?v=4?s=500" width="500px;" alt="akshsabherwal"/><br /><sub><b>akshsabherwal</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/issues?q=author%3Aakshsabherwal" title="Bug reports">🐛</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=akshsabherwal" title="Code">💻</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=akshsabherwal" title="Documentation">📖</a> <a href="#ideas-akshsabherwal" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/pulls?q=is%3Apr+reviewed-by%3Aakshsabherwal" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/KristinaD1910"><img src="https://avatars.githubusercontent.com/u/145992208?v=4?s=500" width="500px;" alt="KristinaD1910"/><br /><sub><b>KristinaD1910</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/issues?q=author%3AKristinaD1910" title="Bug reports">🐛</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=KristinaD1910" title="Code">💻</a> <a href="#data-KristinaD1910" title="Data">🔣</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=KristinaD1910" title="Documentation">📖</a> <a href="#ideas-KristinaD1910" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/pulls?q=is%3Apr+reviewed-by%3AKristinaD1910" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Mayazure"><img src="https://avatars.githubusercontent.com/u/17568266?v=4?s=500" width="500px;" alt="Jinshuai Ma"/><br /><sub><b>Jinshuai Ma</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/commits?author=Mayazure" title="Code">💻</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=Mayazure" title="Documentation">📖</a> <a href="#example-Mayazure" title="Examples">💡</a> <a href="#infra-Mayazure" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#mentoring-Mayazure" title="Mentoring">🧑‍🏫</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/RiyaChhikara"><img src="https://avatars.githubusercontent.com/u/115228191?v=4?s=500" width="500px;" alt="Riya Chhikara"/><br /><sub><b>Riya Chhikara</b></sub></a><br /><a href="https://github.com/LSE-DSI/chat-lse/commits?author=RiyaChhikara" title="Code">💻</a> <a href="#data-RiyaChhikara" title="Data">🔣</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=RiyaChhikara" title="Documentation">📖</a> <a href="#mentoring-RiyaChhikara" title="Mentoring">🧑‍🏫</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/gaoonline"><img src="https://avatars.githubusercontent.com/u/83190698?v=4?s=500" width="500px;" alt="Kylin Gao"/><br /><sub><b>Kylin Gao</b></sub></a><br /><a href="#ideas-gaoonline" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=gaoonline" title="Tests">⚠️</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/aliceandchains"><img src="https://avatars.githubusercontent.com/u/147733005?v=4?s=500" width="500px;" alt="Alexey Burmistrov"/><br /><sub><b>Alexey Burmistrov</b></sub></a><br /><a href="#ideas-aliceandchains" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/LSE-DSI/chat-lse/commits?author=aliceandchains" title="Tests">⚠️</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
          <a href="https://all-contributors.js.org/docs/en/bot/usage">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!