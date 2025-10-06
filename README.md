# AI Research Agent

A modular, production-style **AI workflow system** built using **LangGraph**, **LangChain**, and the **Firecrawl API**.
This project demonstrates how to design structured, multi-step AI pipelines capable of autonomous research and analysis — specifically for identifying, evaluating, and comparing **developer tools** across the web.

---

## Overview

The **Advanced AI Research Agent** is designed to automate the process of researching and analyzing technology solutions.
It accepts a user query, conducts web research through the **Firecrawl API**, extracts key entities, analyzes their characteristics, and generates structured insights and comparisons.

For example, given a query such as *“best APIs for stock trading automation,”* the agent:

1. Searches and scrapes relevant sources.
2. Identifies tool or company names using an LLM.
3. Collects and analyzes website content for each tool.
4. Extracts information such as pricing, features, tech stack, and integration support.
5. Produces a structured summary and recommendation output.

---

## Installation & Usage

### Prerequisites

```
Firecrawl API Key (has a free trial)
OpenAI API Key
uv Package Manager (see uv documentation for details; must be installed in the global environment using pip install uv)
(Optional) Langsmith API Key (for tracking project LLM calls)
```

### Launch Application
```
uv run main.py
```

---

## Technologies Used

* **LangGraph** – Workflow orchestration and node graph design.
* **LangChain** – LLM management and structured output handling.
* **OpenAI GPT-4o** – Primary LLM for reasoning and analysis.
* **Firecrawl API** – Web search and scraping service.
* **Pydantic** – Schema validation and data modeling.
* **Python** – Core implementation language.

---

**Built with:** Python, LangGraph, LangChain, Firecrawl API
**Version:** 1.0.0
