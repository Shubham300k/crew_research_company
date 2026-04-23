import os
import requests
from dotenv import load_dotenv

load_dotenv()

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

CF_AI_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct"

def cf_generate(prompt: str) -> str:
    """Call Cloudflare Workers AI."""
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "system", "content": "You are a business intelligence assistant. Be concise."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(CF_AI_URL, headers=headers, json=data, timeout=30)
        result = response.json()
        return result["result"]["response"]
    except Exception as e:
        return f"Error: {str(e)}"

def search_company(company_name: str) -> str:
    """Search Google via Serper."""
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": f"{company_name} company what they do", "num": 3}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    results = data.get("organic", [])
    raw = ""
    for i, r in enumerate(results[:2], 1):
        raw += f"{r.get('title')}. {r.get('snippet')} "
    
    prompt = f"Summarize what {company_name} does in 2 sentences: {raw[:800]}"
    return cf_generate(prompt)

def analyze_company(summary: str) -> str:
    """Analyze pain points."""
    prompt = f"What tech stack and pain points does this company likely have? Be brief: {summary[:600]}"
    return cf_generate(prompt)

def write_email(company: str, analysis: str) -> str:
    """Generate email."""
    prompt = f"Write a 3-sentence cold email to {company} offering AI automation. Mention: {analysis[:400]}"
    return cf_generate(prompt)

# RUN
if __name__ == "__main__":
    company = input("Company: ")
    
    print("\nResearching...")
    research = search_company(company)
    print(research)
    
    print("\nAnalyzing...")
    analysis = analyze_company(research)
    print(analysis)
    
    print("\nWriting email...")
    email = write_email(company, analysis)
    print(email)
    
    # Save
    output = f"RESEARCH: {research}\n\nANALYSIS: {analysis}\n\nEMAIL: {email}"
    with open(f"output_{company.lower()}.txt", "w") as f:
        f.write(output)
    print(f"\nSaved!")