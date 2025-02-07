Contains the logic of my project "Memories".
It's basically a server using Flask, that manages the REST petitions of the front, and interacts with the SQL db, and also, has the agentic LangGraph/LangChain component.

This project aims to make a human-in-the-loop iteration based on the retrieving of technical documentation where users will be able to decide wether a retrieved item is useful or not for the making of a technical report. This human-in-the-loop iteration is yet to be developed, as atm only the chat functionalities and user management functions are developed and working.

**Flask:**
- Standard flask, using get and post methods and then calling to methods of other layers to process the petition.
- SQL Component is totally vanilla SQL. It's used to store the users, the Chats and Messages, and perform some querys to retrieve them.

**RAG and Agents:**
- All based in a LangGraph conditional Graph, where the llm decides what tool to use or not. I find it quite unpredictable, and not very deterministic, so I'm seeking for ways to improve the decision making and make it more token-efficient.
- Also, there are always conflicts between the versions of the libraries, so I'm very limited atm on the features.
- There are some cases of users querys that dont work. Next step is to fix that cases with probably a semantic router.
- Using Pinecone atm because of the ease of use. Long term will probably move towards a MongoDB or Chroma for retrieval.

Link to [Front](https://github.com/yaxfer1/Memories.git) Repo.
