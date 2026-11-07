
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.services.rag import answer_question
from app.database import get_db
from app.models import Conversation, Message

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


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
        ).order_by(Message.id.asc()).all()

        # 3. Convert database messages into dictionaries
        chat_history = [
            {
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

        # 5. Generate answer using RAG + conversation history
        answer = answer_question(
            video_id=request.video_id,
            question=request.question,
            chat_history=chat_history
        )

        # 6. Save Gemini's response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )

        db.add(assistant_message)
        db.commit()

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