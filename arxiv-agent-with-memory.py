"""
This module integrates LangChain, a Python framework for large language models (LLMs), and arXiv, a repository for e-prints of scientific papers, to create a question answering program. The goal is to demonstrate how to use LangChain and related libraries in building LLM-powered applications.

Here's the plan:

1. Ask the user for a query.
2. Expand the query by adding related words.
3. Use the expanded query to search arXiv for papers.
5. Create embeddings from the papers' abstracts.
6. Create embeddings from the orginal query.
6. Find the most relevant papers to the orginal query.
7. Feed the retrieved abstracts and the query to GPT-3.
8. Display the response.
9. Repeat steps 1-8 until the user quits.
"""

import streamlit as st

from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.utilities import WikipediaAPIWrapper
from langchain.utilities import PythonREPL
from langchain.tools import DuckDuckGoSearchRun
from langchain.agents import Tool

st.set_page_config(page_title="arXiv Assistant", page_icon="📖")
st.title("📖 arXiv Assistant")

# Set up memory
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs,
    return_messages=True,
    memory_key="chat_history",
    output_key="output",
)

# Add a default message if there are no messages in memory
if len(msgs.messages) == 0:
    msgs.add_ai_message(
        "As a helpful research assistant, I can answer questions using "
        "research papers available on arXiv. I also have access to a few "
        "other tools that can help me answer your questions. **Try asking me "
        "something!**"
    )

# Render current messages from StreamlitChatMessageHistory
view_messages = st.expander("View the message contents in session state")

# Create tools for the agent
wikipedia = WikipediaAPIWrapper()
python_repl = PythonREPL()
search = DuckDuckGoSearchRun()

tools = [
    Tool(
        name="Wikipedia Search",
        func=wikipedia.run,
        description="Useful for when you need to look up a definition or a short description of something. Be specific with your input.",
    ),
    Tool(
        name="Python REPL",
        func=python_repl.run,
        description="useful for when you need to use Python to answer a question. You should input Python code.",
    ),
    Tool(
        name="DuckDuckGo Search",
        func=search.run,
        description="Useful for when you need to do a search on the internet to find information that another tool can't find. Be specific with your input.",
    ),
]

tools.extend(load_tools(["arxiv"]))

# Set up the ComversationalAgent, passing in memory and tools
agent_executor = initialize_agent(
    llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k"),
    tools=tools,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    return_intermediate_steps=True,
    handle_parsing_errors=True,
    verbose=True,
)

# Render current messages from StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# If user inputs a new prompt, generate and draw a new response
if prompt := st.chat_input():
    st.chat_message("human").write(prompt)
    st_callback = StreamlitCallbackHandler(st.container())

    with st.chat_message("assistant"):
        response = agent_executor(prompt, callbacks=[st_callback])
        st.write(response["output"])

# Draw the messages at the end, so newly generated ones show up immediately
with view_messages:
    """
    Memory initialized with:
    ```python
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    memory = ConversationBufferMemory(chat_memory=msgs)
    ```

    Contents of `st.session_state.langchain_messages`:
    """
    view_messages.json(st.session_state.langchain_messages)
