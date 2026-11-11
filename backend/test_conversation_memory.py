
from app.services.vector_store import retrieve_conversation_memories


results = retrieve_conversation_memories(
    query="What did we discuss about Fable's performance?",
    conversation_id=34,
    k=5
)

print("\nRETRIEVED CONVERSATION MEMORIES\n")

for index, doc in enumerate(results, start=1):

    print(f"\nMEMORY {index}")
    print("Content:", doc.page_content)
    print("Metadata:", doc.metadata)
    print("-" * 60)
