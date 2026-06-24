---
title: Set up your workspace
sidebar_label: Set up your workspace
description: Get OpenCareLoop running on your device in three steps.
---

# Set up your workspace

OpenCareLoop runs on your own device through an AI coding agent. You don't need to be technical — once the agent is open, it handles the setup for you. Three steps: get the workspace, open it in an agent, and let the agent set itself up.

:::warning Not for emergencies or medical advice
OpenCareLoop helps you organize your health and ask better questions. It is **not** a replacement for a doctor, pharmacist, nurse, or emergency service, and its suggestions are never medical orders. If something is sudden, severe, or dangerous, stop and get medical help. See [When not to use it](./non-urgent-use.md).
:::

## 1. Get the workspace

Download or unzip the `OpenCareLoop` folder and put it somewhere easy to find on your computer. Everything — your dossiers and any records you add — stays inside this folder, on your device.

:::info Your data stays local
Nothing is uploaded or shared. The workspace lives on your machine, and only you and the agent read it. Once it holds real health information, don't publish or share the folder.
:::

## 2. Open it in an AI agent

OpenCareLoop works with an AI coding agent. Either of these is fine:

- **[Claude Code](https://code.claude.com/docs/en/quickstart)**
- **[Codex](https://developers.openai.com/codex/quickstart)**

Install one, then open the `OpenCareLoop` folder in it.

:::tip Use a capable model
Your results are only as good as the model behind the agent. We recommend running **GPT‑5.5 High** (or an equivalent or better model). Reasoning about scattered health data over time is hard work — a stronger model catches more, guesses less, and asks sharper questions.
:::

## 3. Let the agent set up

In the agent, send this message:

```text
Set up OpenCareLoop and create a new person dossier.
```

The agent prepares the workspace — including a one-time install of the tools it needs to read PDFs and reports — and then starts your first dossier with a few simple questions.

That's it. Next: [start your first dossier](./first-dossier.md).

## Adding records later

When you have a record to add — a lab report, a prescription, a photo of a medicine box — put the file here:

```text
people/<person-slug>/raw-data-dump/
```

The `<person-slug>` is just that person's folder name, like `karan`. Then tell the agent it's there and it will sort and read it for you. More in [Add your records](./adding-records.md).
