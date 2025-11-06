# langchain_agent.py
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.agents import Tool, AgentExecutor, initialize_agent
from langchain import OpenAI

# herramienta de calendario (implementada en google_calendar_tool.py)
from google_calendar_tool import create_event_tool

def build_agent():
    # modelo conversacional (ajusta temperatura y modelo según tu cuenta)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)  # ejemplo; usa el modelo que tengas disponible
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    tools = [
        create_event_tool(),  # devuelve un Tool que sabe crear eventos
        # aquí puedes añadir más herramientas: lookup cliente, CRM, DB, búsqueda FAQ...
    ]

    agent = initialize_agent(
        tools, llm, agent="conversational-react-description", memory=memory, max_iterations=3
    )
    return agent
