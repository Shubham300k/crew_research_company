import os
import requests
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

CF_AI_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"

cf_llm = LLM(
    model="openai/@cf/meta/llama-3.1-8b-instruct",
    api_key=CF_API_TOKEN,
    base_url=CF_AI_URL,
    temperature=0.1
)

def cf_generate(prompt: str, max_tokens: int = 400) -> str:
    """Call Cloudflare Workers AI with truncated prompt."""
    MAX_PROMPT_CHARS = 2500
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "... [truncated]"
    
    url = f"{CF_AI_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "@cf/meta/llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a business intelligence assistant. Be extremely concise. Use 3-5 sentences max."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def search_company_info(company_name: str) -> str:
    """
    Search Google for company information. 
    Input must be a single company name string (e.g., "Stripe").
    Returns a brief 3-sentence summary.
    """
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": f"{company_name} company what they do business model", "num": 3}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        results = data.get("organic", [])
        raw = ""
        for i, r in enumerate(results[:2], 1):
            raw += f"{r.get('title')}. {r.get('snippet')} "
        
        prompt = f"In 3 sentences, what does {company_name} do? Context: {raw[:800]}"
        return cf_generate(prompt, max_tokens=200)
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def analyze_tech_stack(company_summary: str) -> str:
    """
    Analyze a company summary for tech stack and pain points.
    Input must be a short company summary string.
    Returns a brief 3-sentence analysis.
    """
    truncated = company_summary[:600]
    prompt = f"What tech stack and 2 pain points does this company likely have? Be brief.\n\nCompany: {truncated}"
    return cf_generate(prompt, max_tokens=200)

# AGENTS: max_iter=2 prevents infinite loops
researcher = Agent(
    role="Company Researcher",
    goal="Find what a company does in 3 sentences",
    backstory="You research companies and return extremely brief summaries. You NEVER call tools multiple times.",
    tools=[search_company_info],
    verbose=True,
    allow_delegation=False,
    llm=cf_llm,
    max_iter=2
)

analyst = Agent(
    role="Business Analyst", 
    goal="Identify 2 pain points in 3 sentences",
    backstory="You analyze companies briefly. You NEVER call tools multiple times.",
    tools=[analyze_tech_stack],
    verbose=True,
    allow_delegation=False,
    llm=cf_llm,
    max_iter=2
)

writer = Agent(
    role="Outreach Writer",
    goal="Write a 3-sentence cold email",
    backstory="You write extremely brief, punchy emails. No fluff.",
    verbose=True,
    allow_delegation=False,
    llm=cf_llm,
    max_iter=2
)

# TASKS: Short expected outputs, 60s timeout
task_research = Task(
    description="Research {company_name}. Find what they do. Use search_company_info ONCE with input: {company_name}",
    expected_output="3 sentences about the company.",
    agent=researcher,
    max_execution_time=60
)

task_analyze = Task(
    description="Analyze the research. Identify 2 pain points. Use analyze_tech_stack ONCE.",
    expected_output="3 sentences: tech stack + 2 pain points.",
    agent=analyst,
    context=[task_research],
    max_execution_time=60
)

task_write = Task(
    description="Write a 3-sentence cold email to {company_name} offering AI automation. Reference pain points.",
    expected_output="3-sentence email.",
    agent=writer,
    context=[task_research, task_analyze],
    max_execution_time=60
)

# CREW: memory=False prevents context buildup
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[task_research, task_analyze, task_write],
    process=Process.sequential,
    verbose=True,
    memory=False,
    max_rpm=10
)

if __name__ == "__main__":
    company = input("Enter company name: ")
    result = crew.kickoff(inputs={"company_name": company})
    print("\n\n=== FINAL OUTPUT ===")
    print(result)
    
    with open(f"output_{company.lower().replace(' ', '_')}.txt", "w", encoding="utf-8") as f:
        f.write(str(result))
    print(f"\nSaved to output_{company.lower().replace(' ', '_')}.txt")