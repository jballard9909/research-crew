# Research Crew

A multi-agent research-and-report generator built with [CrewAI](https://www.crewai.com/).
Give it a topic; it plans research questions, gathers sources, and writes a
structured markdown report with citations.

> **Status:** in development. Day-1 skeleton runs a Planner → Writer crew.
> Web search and citations land in Week 2.

## Architecture

Three agents run in sequence:

| Agent | Owns |
|-------|------|
| **Planner** | Decomposes the topic into 3–5 focused research questions |
| **Researcher** | Runs web searches and gathers sourced findings *(Week 1, Fri)* |
| **Writer** | Synthesizes findings into a structured report with citations |

## Quick start

```bash
git clone https://github.com/jballard9909/research-crew.git
cd research-crew
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY
python -m research_crew.crew "the economic impact of remote work"
```

## What I'd improve

_(fill in Week 3 — note the CrewAI → LangGraph tradeoff for production state
management, and adding an eval/observability layer.)_