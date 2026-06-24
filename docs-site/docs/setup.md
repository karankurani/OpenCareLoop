---
title: Set up your workspace
sidebar_label: Set up your workspace
description: Get OpenCareLoop running on your device in three steps.
---

import useBaseUrl from '@docusaurus/useBaseUrl';

# Set up your workspace

OpenCareLoop runs on your own device through an AI coding agent. You don't need to be technical — once the agent is open, it handles the setup for you. Three steps: get the workspace, open it in an agent, and let the agent set itself up.

:::danger Alpha software: use carefully
OpenCareLoop is an alpha release. Expect rough edges, incomplete workflows, and mistakes. Review important details yourself, and do not rely on it for urgent, time-sensitive, or high-risk decisions.
:::

:::warning Not for emergencies or medical advice
OpenCareLoop helps you organize your health and ask better questions. It is **not** a replacement for a doctor, pharmacist, nurse, or emergency service, and its suggestions are never medical orders. If something is sudden, severe, or dangerous, stop and get medical help. See [When not to use it](./non-urgent-use.md).
:::

## 1. Get the workspace

Download or unzip the `OpenCareLoop` folder and put it somewhere easy to find on your computer. Everything — your dossiers and any records you add — stays inside this folder, on your device.

<a className="button button--primary button--md docsDownloadButton" href="https://github.com/karankurani/OpenCareLoop/releases/latest/download/OpenCareLoop.zip">
  <span className="docsDownloadButtonIcon" aria-hidden="true">
    <svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10 3.5V11.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6.75 8.75L10 12L13.25 8.75" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 15.5H16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </span>
  <span>Download OpenCareLoop Alpha</span>
</a>

:::info The workspace lives on your machine
Your dossiers and records are plain files on your own computer — OpenCareLoop has no servers and never collects your data. Keep it that way: once the folder holds real health information, don't publish, commit, or share it. (The AI agent you choose does send what you discuss to its provider — see the next step.)
:::

## 2. Open it in an AI agent

OpenCareLoop works with an AI coding agent. Either of these is fine:

<div
  style={{
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '12px',
    marginTop: '12px',
    marginBottom: '12px',
  }}>
  <a
    href="https://claude.com/download"
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '12px 14px',
      border: '1px solid var(--ifm-color-emphasis-300)',
      borderRadius: '12px',
      textDecoration: 'none',
      fontWeight: 600,
      backgroundColor: 'var(--ifm-background-surface-color)',
    }}>
    <img
      src={useBaseUrl('/img/claude-app-icon.png')}
      alt="Claude app icon"
      width="28"
      height="28"
      style={{ borderRadius: '7px', flexShrink: 0 }}
    />
    <span>Claude</span>
  </a>
  <a
    href="https://chatgpt.com/codex/"
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '12px 14px',
      border: '1px solid var(--ifm-color-emphasis-300)',
      borderRadius: '12px',
      textDecoration: 'none',
      fontWeight: 600,
      backgroundColor: 'var(--ifm-background-surface-color)',
    }}>
    <img
      src={useBaseUrl('/img/codex-app-icon.png')}
      alt="Codex app icon"
      width="28"
      height="28"
      style={{ borderRadius: '7px', flexShrink: 0 }}
    />
    <span>Codex</span>
  </a>
</div>

Install one, then open the `OpenCareLoop` folder in it.

:::danger Privacy: your data is sent to the agent provider
To do its job, the agent sends what you share — your prompts, dossier text, and records — to its provider (for example, Anthropic for Claude Code or OpenAI for Codex). **What happens to that data depends entirely on the plan and terms you have with that provider.** Some plans use your data to train models or for other purposes; others don't.

It is your responsibility to choose a provider and a plan whose privacy terms you're comfortable with for sensitive health information, and to review those terms before adding real records. OpenCareLoop does not control and is **not responsible** for how any provider processes, stores, or uses the data you send them.
:::

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
