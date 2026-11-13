
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.services.rag import (
    answer_question,
    generate_conversation_summary
)
from app.database import get_db
from app.models import Conversation, Message
from app.services.vector_store import store_conversation_turn

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)

def update_rolling_summary(db: Session, conversation: Conversation):

    # Get messages that haven't been included in the summary
    unsummarized_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.id > (conversation.summary_through_message_id or 0)
    ).order_by(Message.id.asc()).all()

    # Group messages into complete user-assistant turns
    turns = []
    current_user_message = None

    for message in unsummarized_messages:

        if message.role == "user":

            # Start a new turn only if no unanswered question exists
            if current_user_message is None:
                current_user_message = message

        elif message.role == "assistant" and current_user_message:

            turns.append([
                current_user_message,
                message
            ])

            current_user_message = None

    # We need at least 10 complete turns
    if len(turns) < 10:
        return

    # Process the first 10 unsummarized turns
    turns_to_summarize = turns[:10]

    # Convert turns into readable text
    new_turns = "\n\n".join(
        f"User: {turn[0].content}\nAssistant: {turn[1].content}"
        for turn in turns_to_summarize
    )

    # Generate updated summary
    updated_summary = generate_conversation_summary(
        previous_summary=conversation.summary or "",
        new_turns=new_turns
    )

    # Save summary and checkpoint
    conversation.summary = updated_summary
    conversation.summary_through_message_id = (
        turns_to_summarize[-1][-1].id
    )

    db.commit()

@router.post("/ask")
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # 1. Find an existing conversation or create a new one
        if request.conversation_id is not None:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id
            ).first()

            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )

            if conversation.video_id != request.video_id:
                raise HTTPException(
                    status_code=400,
                    detail="This conversation belongs to a different video"
                )

        else:
            conversation = Conversation(
                title=request.question[:50],
                video_id=request.video_id
            )

            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Retrieve previous messages BEFORE saving current question
        previous_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.id.desc()).limit(10).all()

        # Reverse the messages to restore chronological order
        previous_messages.reverse()

        # 3. Convert database messages into dictionaries
        chat_history = [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content
            }
            for message in previous_messages
        ]

        # 4. Save the current user's question
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.question
        )

        db.add(user_message)
        db.commit()

        print("\n========== CHAT DEBUG ==========")

        print("Conversation ID:", conversation.id)
        print("Video ID:", request.video_id)
        print("Current Question:", request.question)

        # print("\nPrevious Conversation History:")

        # for message in chat_history:
        #     print(f"{message['role']}: {message['content']}")

        # print(f"number of convo in chat history:{len(chat_history)}")     

        # print("================================\n")

        
        
        # 5. Generate answer using RAG + conversation history
        answer = answer_question(
            video_id=request.video_id,
            conversation_id=conversation.id,
            question=request.question,
            chat_history=chat_history,
            conversation_summary=conversation.summary or ""
        )

        # 6. Save Gemini's response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )

        db.add(assistant_message)
        db.commit()

        db.refresh(assistant_message)

        # Store the completed Q&A turn in ChromaDB
        try:
            store_conversation_turn(
                conversation_id=conversation.id,
                video_id=request.video_id,
                user_message_id=user_message.id,
                assistant_message_id=assistant_message.id,
                question=request.question,
                answer=answer
            )

            print("Conversation memory stored successfully!")

        except Exception as memory_error:
            print(f"Conversation memory storage failed: {memory_error}")

        try:
            update_rolling_summary(
                db=db,
                conversation=conversation
            )

        except Exception as summary_error:
                db.rollback()
                print(f"Rolling summary update failed: {summary_error}")

        # 7. Return response
        return {
            "conversation_id": conversation.id,
            "video_id": request.video_id,
            "question": request.question,
            "answer": answer
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(error)}"
        )


@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):
    try:
        conversations = (
            db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

        return [
            {
                "id": conversation.id,
                "title": conversation.title,
                "video_id": conversation.video_id,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at
            }
            for conversation in conversations
        ]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching conversations: {str(error)}"
        )
@router.get("/conversations/{conversation_id}")
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.id.asc()).all()

        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "video_id": conversation.video_id,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at
                }
                for message in messages
            ]
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching conversation: {str(error)}"
        )