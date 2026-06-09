# GTM Campaign Launch Agent

A multi-agent AI system that turns a campaign brief into a complete, launch-ready GTM package in minutes. Built for B2B SaaS go-to-market workflows.

**Live demo:** https://gtm-campaign-agent.streamlit.app

## What it does

You upload a campaign brief as a Word document. Five AI agents run in sequence to research the market, set strategy, write the copy, and quality-check the result. The output is a full campaign package: email copy with audience variations, channel strategy, market research, and a critic score.

## The five agents

Each agent has one job and hands its output to the next:

1. **Orchestrator** reads the brief and identifies the tasks and target audience
2. **Researcher** runs live web searches for market conditions, competitive landscape, and buyer sentiment
3. **Strategist** defines the target audience, key message, and channel angles
4. **Copywriter** writes the email subject, body, and audience variations
5. **Critic** scores the output and flags strengths and improvements before it ships

Channel angles are generated for Email, Paid Social, Content, and an SDR Sequence.

## Tech stack

- Python
- Anthropic Claude API (claude-sonnet-4-6) for the agents
- Tavily for live web search
- Streamlit for the interface
- GitHub Actions for deployment

## Why it matters

Launching a campaign normally means coordinating research, strategy, and copy across several people and tools. This compresses that into one automated pipeline with a built-in quality check, so a brief becomes a multi-channel campaign in a single run.
