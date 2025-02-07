import os

import logging
logging.basicConfig(level=logging.INFO)
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError
import logging
from semantic_router.encoders import OpenAIEncoder
from langchain.globals import set_verbose

set_verbose(True)

os.environ["OPENAI_API_KEY"] = 
encoder = OpenAIEncoder(name="text-embedding-3-small")

from pinecone import Pinecone

# initialize connection to pinecone (get API key at app.pinecone.io)
PINECONE_API_KEY = ""

# configure client
pc = Pinecone(api_key=PINECONE_API_KEY)
pc_o = Pinecone(api_key="")
from pinecone import ServerlessSpec

spec = ServerlessSpec(
    cloud="aws", region="us-west-2"  # us-east-1
)
dims = len(encoder(["some random text"])[0])
print(dims)
import time
index_name = "gpt-4o-research-agent"
index_name_own = "prueba-leyton"

index = pc.Index(index_name)
time.sleep(1)
index_own = pc_o.Index(index_name_own)
time.sleep(1)

from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator



from langgraph.managed.is_last_step import IsLastStep

class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    remaining_steps: IsLastStep
    used_tools: list[str]

import requests
from langchain_core.tools import tool

import requests


import re

# our regex
abstract_pattern = re.compile(
    r'<blockquote class="abstract mathjax">\s*<span class="descriptor">Abstract:</span>\s*(.*?)\s*</blockquote>',
    re.DOTALL
)

@tool("fetch_arxiv")
def fetch_arxiv(arxiv_id: str):
    """Gets the abstract from an ArXiv paper given the arxiv ID. Useful for
    finding high-level context about a specific paper."""
    # get paper page in html
    res = requests.get(
        f"https://export.arxiv.org/abs/{arxiv_id}"
    )
    # search html for abstract
    re_match = abstract_pattern.search(res.text)
    # return abstract text
    return re_match.group(1)


from langchain_core.tools import tool

from serpapi import GoogleSearch

serpapi_params = {
    "engine": "google",
    "api_key": "3e1451b4a09b21039316549bada1f7f57c4702e165c68ca7f52526e11f3e811f"
}

search = GoogleSearch({
    **serpapi_params,
    "q": "coffee"
})

@tool("web_search")
def web_search(query: str):
    """Finds general knowledge information using Google search. Can also be used
    to augment more 'general' knowledge to a previous specialist query. It can also be used to find knowledge about specific businesses."""
    search = GoogleSearch({
        **serpapi_params,
        "q": query,
        "num": 5
    })
    results = search.get_dict()["organic_results"]
    contexts = "\n---\n".join(
        ["\n".join([x["title"], x["snippet"], x["link"]]) for x in results]
    )
    return contexts

def format_rag_contexts(matches: list):
    contexts = []
    for x in matches:
        text = (
            f"Title: {x['metadata']['title']}\n"
            f"Content: {x['metadata']['content']}\n"
            f"ArXiv ID: {x['metadata']['arxiv_id']}\n"
            f"Related Papers: {x['metadata']['references']}\n"
        )
        contexts.append(text)
    context_str = "\n---\n".join(contexts)
    return context_str

@tool("rag_search_filter")
def rag_search_filter(query: str, arxiv_id: str):
    """Finds information from our ArXiv database using a natural language query
    and a specific ArXiv ID. Allows us to learn more details about a specific paper."""
    xq = encoder([query])
    xc = index.query(vector=xq, top_k=6, include_metadata=True, filter={"arxiv_id": arxiv_id})
    context_str = format_rag_contexts(xc["matches"])
    return context_str

@tool("rag_search")
def rag_search(query: str):
    """Finds specialist information on AI using a natural language query. Used to research very technical information(academic papers)"""
    xq = encoder([query])
    xc = index.query(vector=xq, top_k=4, include_metadata=True)
    context_str = format_rag_contexts(xc["matches"])
    return context_str

def format_rag_contexts_own(matches: list):
    contexts = []
    for x in matches:
        text = (
            f"Source: {x['metadata']['source']}\n"
            f"Content: {x['metadata']['text']}\n"
        )
        contexts.append(text)
    context_str = "\n---\n".join(contexts)
    return context_str

@tool("rag_search_pdf")
def rag_search_pdf(query: str):
    """Finds information of persons and business, and confidential data that may not be on the internet"""
    xq = encoder([query])
    xc = index_own.query(vector=xq, top_k=5, include_metadata=True)
    context_str = format_rag_contexts_own(xc["matches"])
    return context_str

@tool("rag_search_filter_pdf")
def rag_search_filter_pdf(query: str, source_id: str):
    """Finds information from our INTERNAL DOCUMENTS of persons, businesses, and more private questions database using a natural language query and a document name. Use when asked about a specific document."""
    xq = encoder([query])
    xc = index.query(vector=xq, top_k=6, include_metadata=True, filter={"source": source_id})
    context_str = format_rag_contexts_own(xc["matches"])
    return context_str

@tool("final_answer")
def final_answer(
        introduction: str,
        research_steps: str,
        main_body: str,
        sources: str
):
    """
    EXECUTE THIS TOOL ALWAYS when received the Message: "final_answer".
    Returns a natural language response to the user in the form of a research
    report. There are several sections to this report, those are:
    - `Introduction`: a short paragraph introducing the user's question and what is the main body being about
    - `main_body`: this is where the bulk of high quality and concise
    information that answers the user's question belongs. The final response HAS TO BE at least **500** words long.
    - `research_steps`: a few bullet points explaining the steps that were taken
    to research your report.
    - `sources`: a bulletpoint list provided detailed sources for all information
    referenced during the research process. Specify the exact name of the metadata and the source.
    """
    if type(research_steps) is list:
        research_steps = "\n".join([f"- {r}" for r in research_steps])
    if type(sources) is list:
        sources = "\n".join([f"- {s}" for s in sources])
    return ""


from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

system_prompt = """
You are the Oracle, the great AI decision-maker specializing in the technical analysis of projects.  
Your purpose is to interpret the description of a specific section from the technical documentation of a GIVEN COMPANY project.  
Based on your interpretation, you must decide the precise information needed to fully address the section's requirements  
and select the appropriate tools to gather the necessary data.  

DO NOT USE ANY TOOL TWICE
DO NOT RE-USE ANY TOOL SHOWN IN THE used_tools list

**Your response MUST ALWAYS be in Spanish.**

---

### **Instructions for Your Decision-Making Process**:
0. WHEN RECEIVED THE MESSAGE: "final_answer", you MUST execute the tool final_answer.
1. **Carefully read the user's query**, which represents a **SECTION STATEMENT** from technical documentation.
2. **Analyze the query** to understand the section's goals, context, and specific technical or business needs.
3. **Identify the key information required** to respond accurately to the paragraph.  
4. Use the available tools from the list of tools that are provided to collect diverse and relevant data points.  
   **IF YOU SEE A TOOL ALREADY USED IN THE used_tools LIST, NEVER USE THE TOOL TWICE**. NEVER USE A TOOL TWICE.  
   - If you’ve already used a tool (indicated in the *used_tools list*), **you must not use it again under any circumstances.**  
   - If you don’t find useful information using one tool, **CHOOSE A DIFFERENT TOOL.**
5. Ask yourself, have I used this tool already? If yes, use another tool or invoke "final_answer". If not, use the tool.
6. **Always finish by using the `final_answer` tool.** When you determine that you’ve collected enough information or cannot gather more, stop your search and provide a complete and detailed response to the user.  
7. **The final response must be at least 500 words long** and should address all relevant aspects of the topic. Organize the response into the following sections:  
8. **Important Criteria**:  
   - DO NOT repeat any tool of the *used_tools list*.  
   - DO NOT use any tool more than once.  
   - Always conclude by executing `final_answer`.  

---

### **List of Tools Available for Your Analysis**:
- `rag_search_filter`  
- `rag_search_filter_pdf`  
- `rag_search`  
- `rag_search_pdf`  
- `fetch_arxiv`  
- `web_search`  
"""


prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}"),
])

from langchain_core.messages import ToolCall, ToolMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.environ["OPENAI_API_KEY"],
    temperature=0,
    max_tokens=10000
)

tools=[
    rag_search_filter,
    rag_search_filter_pdf,
    rag_search,
    rag_search_pdf,
    fetch_arxiv,
    web_search,
    final_answer
]

# define a function to transform intermediate_steps from list
# of AgentAction to scratchpad string
def create_scratchpad(intermediate_steps: list[AgentAction]):
    research_steps = []
    for i, action in enumerate(intermediate_steps):
        if action.log != "TBD":
            # this was the ToolExecution
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\n"
                f"Output: {action.log}"
            )
    return "\n---\n".join(research_steps)

def get_input(x):
    return x["input"]

def get_chat_history(x):
    return x["chat_history"]

def get_scratchpad(x):
    return create_scratchpad(intermediate_steps=x["intermediate_steps"])

def get_used_tools(x):
    return x["used_tools"]

oracle = (
        {
            "input": get_input,
            "chat_history": get_chat_history,
            "scratchpad": get_scratchpad,
            "used_tools": get_used_tools,
        }
        | prompt
        | llm.bind_tools(tools)
)

def run_oracle(state: dict):
    logging.info(f"intermediate_steps: {state.get('intermediate_steps')}")
    logging.info(f"remaining_steps: {state.get('remaining_steps')}")
    logging.info(f"used_tools: {state.get('used_tools')}")

    out = oracle.invoke(state)

    # Verificar si se generaron llamadas a herramientas
    if not out.tool_calls or len(out.tool_calls) == 0:
        logging.warning("No se han generado llamadas a herramientas en la salida del oracle.")
        # Aquí podrías:
        # - Retornar un objeto indicando que no se requiere acción adicional
        # - O generar un final_answer vacío o una respuesta por defecto
        return {"intermediate_steps": []}

    tool_name = out.tool_calls[0]["name"]
    tool_args = out.tool_calls[0]["args"]

    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log="TBD"
    )

    return {
        "intermediate_steps": [action_out]
    }

def router(state: list):
    # return the tool name to use
    if isinstance(state["intermediate_steps"], list):
        if state["remaining_steps"] == True:
            print("DEVOLVER RESPUESTA FINAL")
            #state["intermediate_steps"][-1].tool = "final_answer"
            #return run_tool(state)
            return "final_answer"
        return state["intermediate_steps"][-1].tool
    else:
        # if we output bad format go to final answer
        print("Router invalid format")
        return "final_answer"

tool_str_to_func = {
    "rag_search_filter": rag_search_filter,
    "rag_search_filter_pdf": rag_search_filter_pdf,
    "rag_search": rag_search,
    "rag_search_pdf" : rag_search_pdf,
    "fetch_arxiv": fetch_arxiv,
    "web_search": web_search,
    "final_answer": final_answer
}

def run_tool(state: dict):
    # Obtén el nombre de la herramienta desde intermediate_steps
    tool_name = state["intermediate_steps"][-1].tool
    tool_args = state["intermediate_steps"][-1].tool_input
    print("printear el state")
    print(state)
    # Verifica si la herramienta ya ha sido utilizada
    if tool_name in state["used_tools"]:
        print(f"La herramienta '{tool_name}' ya ha sido utilizada.")

    print(f"{tool_name}.invoke(input={tool_args})")

    # Ejecuta la herramienta
    out = tool_str_to_func[tool_name].invoke(input=tool_args)

    # Registra la herramienta como utilizada
    state["used_tools"].append(tool_name)

    # Crea la acción con el resultado
    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log=str(out)
    )

    return {"intermediate_steps": [action_out]}

from langgraph.graph import StateGraph, END
graph = StateGraph(AgentState)

graph.add_node("oracle", run_oracle)
graph.add_node("rag_search_filter", run_tool)
graph.add_node("rag_search_filter_pdf", run_tool)
graph.add_node("rag_search_pdf", run_tool)
graph.add_node("rag_search", run_tool)
graph.add_node("fetch_arxiv", run_tool)
graph.add_node("web_search", run_tool)
graph.add_node("final_answer", run_tool)

graph.set_entry_point("oracle")

graph.add_conditional_edges(
    source="oracle",  # where in graph to start
    path=router,  # function to determine which node is called
)

# create edges from each tool back to the oracle
for tool_obj in tools:
    if tool_obj.name != "final_answer":
        graph.add_edge(tool_obj.name, "oracle")

# if anything goes to final answer, it must then move to END
graph.add_edge("final_answer", END)
runnable = graph.compile()


def build_report(output: dict):
    research_steps = output["research_steps"]
    if type(research_steps) is list:
        research_steps = "\n".join([f"- {r}" for r in research_steps])
    sources = output["sources"]
    if type(sources) is list:
        sources = "\n".join([f"- {s}" for s in sources])
    return f"""
INTRODUCCION
------------
{output["introduction"]}

TRAZAS DE INVESTIGACION
--------------
{research_steps}

CUERPO DE LA RESPUESTA
------
{output["main_body"]}

FUENTES
-------
{sources}
"""

def research_graph(query: str):
    try:
        print("query:", query)
        out = runnable.invoke({
        "input": query,
        "chat_history": [],
        "used_tools":[],
    }, {"recursion_limit": 30})
    except GraphRecursionError:
        print("Recursion Error")
        return out["intermediate_steps"][-1].tool_input


    return build_report(
        output=out["intermediate_steps"][-1].tool_input
    )
