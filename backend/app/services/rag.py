
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.services.vector_store import (
    vector_store,
    retrieve_conversation_memories
)



# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0
)

contextualization_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a query contextualization assistant.

        Your job is to rewrite the user's latest question
        into a standalone question that can be understood
        without seeing the previous conversation.

        Use the conversation history to resolve:
        - Pronouns such as it, they, he, she, this and that.
        - References to earlier explanations.
        - References to previously mentioned concepts.
        - Incomplete or ambiguous follow-up questions.

        Rules:
        1. Preserve the original meaning and intent.
        2. Do not answer the question.
        3. Do not introduce information that isn't supported
           by the conversation.
        4. If the question is already standalone, return it
           unchanged.
        5. Return ONLY the rewritten question.
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

contextualization_chain = (
    contextualization_prompt
    | llm
    | StrOutputParser()
)

def rewrite_question(question: str, chat_history: list = None) -> str:

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

    # Generate a standalone question
    standalone_question = contextualization_chain.invoke({
        "chat_history": formatted_history,
        "question": question
    })

    return standalone_question.strip()

# Create prompt template


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a helpful YouTube video assistant.

        You will receive four types of context:

        1. Transcript Context:
           Relevant information retrieved from the YouTube video.

        2. Older Conversation Memories:
           Relevant exchanges retrieved from ChromaDB.

        3. Recent Conversation History:
           The latest messages in the current conversation.

        4. Rolling Conversation Summary:
           A compressed summary of older conversation exchanges.

        Instructions:

        - Use transcript context as the primary source
          for factual information about the video.
        - Use older memories and the rolling summary
          to understand previous discussions.
        - Use recent history to understand the current
          discussion and references.
        - Do not invent facts.
        - Do not claim something was mentioned in the
          transcript if it wasn't.
        - If video information is unavailable in the
          transcript, say so.
        - Keep answers clear and informative.

        Transcript Context:
        {context}

        Older Conversation Memories:
        {memory_context}

        Rolling Conversation Summary:
        {summary}
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])



summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a conversation memory summarization assistant.

        Your job is to maintain a concise, accurate,
        continuously updated summary of a conversation.

        You will receive:
        1. The previous conversation summary.
        2. New completed conversation turns.

        Instructions:
        - Preserve important facts and explanations.
        - Preserve user preferences and corrections.
        - Preserve decisions and conclusions.
        - Preserve unresolved questions.
        - Retain important technical terms and names.
        - Remove repetition and irrelevant details.
        - Never invent information.
        - Do not answer the user's questions.
        - Produce a self-contained updated summary.

        Previous summary:
        {previous_summary}
        """
    ),
    ("human", "New conversation turns:\n{new_turns}")
])


# Create the RAG chain
rag_chain = prompt | llm | StrOutputParser()

summary_chain = summary_prompt | llm | StrOutputParser()

def generate_conversation_summary(
    previous_summary: str,
    new_turns: str
) -> str:

    updated_summary = summary_chain.invoke({
        "previous_summary": previous_summary or "No previous summary.",
        "new_turns": new_turns
    })

    return updated_summary.strip()


def log_token_count(label: str, text: str):
    token_count = llm.get_num_tokens(text or "")
    print(f"{label}: {token_count} tokens")


def answer_question(
    video_id: str,
    conversation_id: int,
    question: str,
    chat_history: list = None,
    conversation_summary: str = ""
):
    # 1. Rewrite the question using recent conversation history
    standalone_question = rewrite_question(
        question,
        chat_history
    )

    print(f"Original question: {question}")
    print(f"Standalone question: {standalone_question}")

    print("\n\n")

    print("Rolling summary received:", bool(conversation_summary))

    # 2. Retrieve relevant YouTube transcript chunks
    docs = vector_store.similarity_search(
        query=standalone_question,
        k=4,
        filter={"video_id": video_id}
    )

        # Extract assistant message IDs from recent history.
    recent_document_ids = [
        f"conversation_{conversation_id}_turn_{message['id']}"
        for message in chat_history or []
        if message["role"] == "assistant"
    ]

    memory_docs = retrieve_conversation_memories(
        query=standalone_question,
        conversation_id=conversation_id,
        exclude_document_ids=recent_document_ids,
        k=5
    )

    print("Excluded document IDs:", recent_document_ids)

    print(
        "Retrieved document IDs:",
        [
            f"conversation_{conversation_id}_turn_{doc.metadata['assistant_message_id']}"
            for doc in memory_docs
        ]
    )
    # 4. Combine transcript chunks
    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    if not context:
        context = "No relevant transcript information was retrieved."

    # 5. Combine older conversation memories
    memory_context = "\n\n".join(
        doc.page_content for doc in memory_docs
    )

    if not memory_context:
        memory_context = "No relevant older conversation memories found."

    print(f"Transcript chunks retrieved: {len(docs)}")
    print(f"Conversation memories retrieved: {len(memory_docs)}")

    # 6. Convert recent history into LangChain messages
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
    
    # Token count for each context component
    log_token_count("Transcript context", context)
    log_token_count("Conversation memories", memory_context)
    log_token_count("Rolling summary", conversation_summary)
    log_token_count(
        "Recent chat history",
        "\n".join(
            f"{message['role']}: {message['content']}"
            for message in (chat_history or [])
        )
    )
    log_token_count("Current question", question)
    log_token_count("Standalone question", standalone_question)   
    
    
    # 7. Format the complete RAG prompt
    formatted_prompt = prompt.format_prompt(
        context=context,
        memory_context=memory_context,
        summary=conversation_summary or "No previous summary available.",
        chat_history=formatted_history,
        question=question
    )

    # Convert the complete prompt into text
    prompt_text = formatted_prompt.to_string()

    formated_contextual_prompt=contextualization_prompt.format_prompt(
        chat_history=formatted_history,
        question=question
    )

    contextual_prompt_text= formated_contextual_prompt.to_string()
    log_token_count("contextual prompt text", contextual_prompt_text)

    # Count total prompt tokens
    log_token_count("Complete formatted RAG prompt", prompt_text)     

    # 7. Generate the final answer
    answer = rag_chain.invoke({
        "context": context,
        "memory_context": memory_context,
        "summary": conversation_summary or "No previous summary available.",
        "chat_history": formatted_history,
        "question": question
    })

    return answer

