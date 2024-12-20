# 💬 ChatLSE

_Total Contributors:_
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-8-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

**Table of Contents:**

  - [About the Project](#-about-the-project)
  - [The Team](#-the-team)
  - [Contributing](#-contributing)
  - [Get in Touch](#%EF%B8%8F-get-in-touch)
  - [Contributors](#-contributors)

## 💡 About the Project
The _ChatLSE_ project is a proof of concept of a full data pipeline to index data from LSE websites. In this project, we gathered all public LSE documents and webpages into a database and then develop a chat interface using an LLM. Think of it as a ChatGPT meant to be particularly knowledgeable of LSE documents. Utilising retrieval augmented generation (RAG), the ChatLSE chatbot is capable of answering queries from staff and students by consulting relevant LSE documents and regulations. 

As all parts of this application are completely open-source, this project also aims to serve as a blueprint for a fully open-source RAG solution. The full workflow of the project is illustrated below: 

![Overall workflow of the project](img/app_workflow.png)

The workflow improves upon vanilla implementations of RAG by adding components of query rewriter and query classifier. They ensure that the chatbot behaves more naturally when interacting with users, being able to handle follow-up questions by referring to previous context and knowing when to deny answering questions that are out of the scope of its intended usage. 

## 🧑‍💻 The Team

_ChatLSE_ was initially created by a small team from the [LSE Data Science Institute](https://www.lse.ac.uk/dsi) over the summer of 2024. 
We now hope to make it open-source and community-driven to allow everyone to contribute to this project. 
Everyone who contributes to this project, no matter how small or big their contributions are, is recognised in this project as a contributor and a community member. 

The project is coordinated and managed by [Jonathan Cardoso-Silva](https://github.com/jonjoncardoso). 

Please see the [Contributors Table](#-contributors) for the GitHub profiles of all our contributors.

## 🔧 Contributing 

_This repository is always a work in progress and **everyone** is encouraged to help us build something that is useful to the many._

Everyone who joins the project should check out our [contributing guidelines](CONTRIBUTING.md) for more information on how to get started.

Community members are provided with opportunities to learn new skills, share their ideas and collaborate with others.

## ✉️ Get in Touch

You can contact the ChatLSE team by emailing [j.cardoso-silva@lse.ac.uk](mailto:j.cardoso-silva@lse.ac.uk?subjet=[ChatLSE]%20-).

## ✨ Contributors

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
