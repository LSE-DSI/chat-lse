from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def read_json():
    file_path = "data/ingested_data.json"
    data = []
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = [json.loads(line.strip()) for line in file]

    # Generate HTML table
    table_html = """
    <html>
    <head>
        <title>Ingested Data</title>
    </head>
    <body>
        <h1>Ingested Data</h1>
        <table border="1">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Type</th>
                    <th>URL</th>
                    <th>Title</th>
                    <th>Date Scraped</th>
                </tr>
            </thead>
            <tbody>
    """

    for item in data:
        table_html += f"""
                <tr>
                    <td>{item['id']}</td>
                    <td>{item['type']}</td>
                    <td><a href="{item['url']}">{item['url']}</a></td>
                    <td>{item['title']}</td>
                    <td>{item['date_scraped']}</td>
                </tr>
        """

    table_html += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=table_html)
