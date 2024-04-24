# Crawler for LSE pages

A proof of concept of a full data pipeline to index data from LSE websites and make /search available as an API endpoint 


## Setup

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
conda create -n poc-lse-search python=3.11 ipython
conda activate poc-lse-search # or the equivalent for your OS
```

5. (Important) Ensure that `pip` refers to the pip inside the conda environment we just created:

```bash
which pip
```

    this should output something like `/home/your-username/miniconda3/envs/poc-lse-search/bin/pip`

6. Assuming you've fixed the `pip` path, install the required packages:

```bash
pip install -r requirements.txt
```

## Running the crawler

1. First, ensure you have activated the `poc-lse-search` conda environment.

2. Run the following command from the root of the project to save the scraped data to a JSON file:

```bash
scrapy crawl dsi_crawler
```

Note: with the current configuration, the crawler will save the data to `data/output.jl`(JSON Lines format). Read about scrapy's [item exporters](https://docs.scrapy.org/en/latest/topics/exporters.html#using-item-exporters) for more information.