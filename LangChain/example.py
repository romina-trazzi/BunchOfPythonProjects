from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Inizializza il modello
llm = ChatAnthropic(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"), 
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    temperature=0.5
)

# Test base
response = llm.invoke([HumanMessage(content="Ciao, come stai?")])
print(response.content)
