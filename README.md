# Company Research Crew

A multi-agent AI system built with CrewAI + Gemini 2.5 Flash + Serper.dev live Google search.

## What It Does

Input a company name → 3 specialized agents collaborate:

1. **Researcher** — Searches Google via Serper API for real company data
2. **Analyst** — Identifies tech stack, pain points, automation opportunities  
3. **Writer** — Generates a personalized cold outreach email

## Architecture

- **Framework:** CrewAI
- **LLM:** Gemini 2.5 Flash (via Google Generative AI)
- **Live Search:** Serper.dev Google Search API
- **Pattern:** Sequential task delegation with context passing
- **Tools:** Custom Serper search + analysis functions

## Example Output

Run: `python crew.py` and enter a company name (e.g., Stripe, Notion, Linear)
See real-time Google search results transformed into structured analysis + personalized outreach.

## Built In

90 minutes. April 2026.
