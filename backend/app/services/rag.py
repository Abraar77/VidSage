
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.services.vector_store import vector_store


# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0
)


# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a helpful YouTube video assistant.

        Answer the user's question using ONLY the transcript context
        provided below.

        Use the conversation history to understand follow-up questions
        and references to earlier messages.

        Conversation history is for understanding the user's intent.
        The transcript context is the source of factual answers.

        If the answer is not available in the transcript, say:
        "I couldn't find the answer in this video's transcript."

        Keep your answers clear and informative.

        Transcript Context:
        {context}
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])


# Create the RAG chain
rag_chain = prompt | llm | StrOutputParser()


def answer_question(
    video_id: str,
    question: str,
    chat_history: list = None
):

    # Retrieve relevant chunks from ChromaDB
    docs = vector_store.similarity_search(
        query=question,
        k=4,
        filter={"video_id": video_id}
    )

    if not docs:
        return "No relevant information found in this video."

    # Combine retrieved chunks
    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    # Convert database messages into LangChain messages
    formatted_history = []

    for message in chat_history or []:
        if message["role"] == "user":
            formatted_history.append(
                HumanMessage(content=message["content"])
            )

        elif message["role"] == "assistant":
            formatted_history.append(
                AIMessage(content=message["content"])
            )

    # Generate answer using Gemini
    answer = rag_chain.invoke({
        "context": context,
        "chat_history": formatted_history,
        "question": question
    })

    return answer
