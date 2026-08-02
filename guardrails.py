# guardrails.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Lightweight model for quick guardrail decision
guard_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

guard_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an input guardrail classifier for a specialized chatbot.
    Your sole task is to classify whether the user query is related to agriculture, farming, crops, livestock, irrigation, rural welfare, or government farmer schemes in Tamil Nadu.

    Respond strictly with "ALLOWED" or "REJECTED".
    
    Examples:
    User: What is the subsidy for drip irrigation in TN? -> ALLOWED
    User: How do I apply for Uzhavar Sandhai card? -> ALLOWED
    User: Who won the cricket match yesterday? -> REJECTED
    User: Write a python program to sort a list. -> REJECTED
    """),
    ("human", "{user_input}")
])

guard_chain = guard_prompt | guard_llm | StrOutputParser()

REJECTION_MESSAGE = (
    "🙏 **Greetings!** I am the Tamil Nadu Farmers Welfare Scheme Assistant. "
    "I am specialized to help you with queries regarding TN government agricultural schemes, "
    "subsidies, crop insurance, and farmer welfare benefits. "
    "\n\nPlease ask a question related to farmer welfare schemes in Tamil Nadu."
)

def check_guardrail(user_input: str) -> tuple[bool, str]:
    """Returns (is_allowed, response_message)"""
    decision = guard_chain.invoke({"user_input": user_input}).strip().upper()
    if "ALLOWED" in decision:
        return True, ""
    return False, REJECTION_MESSAGE