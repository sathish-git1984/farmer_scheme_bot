# rag_engine.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from guardrails import check_guardrail

load_dotenv()

# 1. Load existing Vector Store
DB_DIR = "./chroma_db"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# 2. Main LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# 3. System Prompt for RAG
system_prompt = (
    "You are an empathetic, clear, and helpful AI assistant specialized in "
    "Tamil Nadu Farmers Welfare Schemes.\n"
    "Use the following pieces of retrieved context to answer the user's question. "
    "If you don't know the answer or if the context doesn't contain it, state politely "
    "that the provided scheme document does not contain those details.\n\n"
    "Retrieved Context:\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

# 4. Helper function to combine document chunks
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 5. In-Memory Session Storage
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# rag_engine.py (Updated Prompting Rules)

def get_detail_instructions(level: str) -> str:
    if level == "Short":
        return (
            "Provide a VERY CRISP response in 3 to 5 lines maximum. "
            "Give only the most critical summary."
        )
    elif level == "Medium":
        return (
            "Provide a balanced response (around 15-20 lines). "
            "Include key eligibility points and main benefits using short bullet points."
        )
    elif level == "Long":
        return (
            "Provide an EXHAUSTIVE and FULLY DETAILED response without length restriction. "
            "Include every piece of information found in the document: scheme background, "
            "target beneficiaries, eligibility criteria, subsidy percentages, exact application steps, "
            "and required documents. Use clear headings and comprehensive lists."
        )
    return "Keep your answer clear and concise."


# 6. Core Query Function with Guardrail
def ask_farmer_bot(query: str, session_id: str = "default_user", detail_level: str = "Short") -> str:
    # 1. Guardrail check
    is_allowed, rejection_msg = check_guardrail(query)
    if not is_allowed:
        return rejection_msg

    # 2. Retrieve Context
    retrieved_docs = retriever.invoke(query)
    context_str = format_docs(retrieved_docs)

    # 3. Dynamic system prompt based on detail level
    detail_instruction = get_detail_instructions(detail_level)
    
    dynamic_system_prompt = (
        "You are an empathetic, clear, and helpful AI assistant specialized in "
        "Tamil Nadu Farmers Welfare Schemes.\n"
        "Use the following pieces of retrieved context to answer the user's question.\n"
        f"FORMATTING RULE: {detail_instruction}\n\n"
        "Retrieved Context:\n{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", dynamic_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    chain = qa_prompt | llm | StrOutputParser()

    conversational_chain = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    response = conversational_chain.invoke(
        {"input": query, "context": context_str},
        config={"configurable": {"session_id": session_id}}
    )
    return response

# rag_engine.py (Add this function alongside your existing code)

def ask_farmer_bot_stream(query: str, session_id: str = "default_user", detail_level: str = "Short"):
    # 1. Retrieve Context
    retrieved_docs = retriever.invoke(query)
    context_str = format_docs(retrieved_docs)

    # 2. Dynamic system prompt based on detail level
    detail_instruction = get_detail_instructions(detail_level)
    
    dynamic_system_prompt = (
        "You are an empathetic, clear, and helpful AI assistant specialized in "
        "Tamil Nadu Farmers Welfare Schemes.\n"
        "Use the following pieces of retrieved context to answer the user's question.\n"
        f"FORMATTING RULE: {detail_instruction}\n\n"
        "Retrieved Context:\n{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", dynamic_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    chain = qa_prompt | llm | StrOutputParser()

    conversational_chain = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    # 3. Stream tokens using .stream()
    for chunk in conversational_chain.stream(
        {"input": query, "context": context_str},
        config={"configurable": {"session_id": session_id}}
    ):
        yield chunk

# Interactive test in terminal
if __name__ == "__main__":
    print("🌾 TN Farmers Welfare Scheme Chatbot Initialized (Type 'exit' to stop)\n")
    session_id = "hackathon_demo_session"
    
    while True:
        user_msg = input("User: ")
        if user_msg.lower() in ["exit", "quit"]:
            break
        
        answer = ask_farmer_bot(user_msg, session_id=session_id)
        print(f"\nBot: {answer}\n" + "-"*50)