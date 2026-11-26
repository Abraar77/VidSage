from app.services.vector_store import vector_store


VIDEO_ID = "1FurWDiK9A4"


def inspect_video_chunks():
    print("Inspecting ChromaDB...")
    print(f"Video ID: {VIDEO_ID}")

    # Retrieve every stored document belonging to this video.
    results = vector_store.get(
        where={"video_id": VIDEO_ID},
        include=["documents", "metadatas"]
    )

    ids = results.get("ids") or []
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []

    print(f"\nTotal chunks found: {len(ids)}")

    if not ids:
        print("No documents found for this video.")
        return

    for index, doc_id in enumerate(ids):

        content = documents[index] if index < len(documents) else ""
        metadata = metadatas[index] if index < len(metadatas) else {}

        print("\n" + "=" * 70)

        print(f"CHUNK NUMBER: {index + 1}")
        print(f"DOCUMENT ID: {doc_id}")

        print("\nMETADATA:")
        print(metadata)

        print("\nDOCUMENT TEXT:")
        print(f"\nDOCUMENT LENGTH: {len(content)} characters")
        print("\nFULL DOCUMENT TEXT:")
        print(content)

    print("\nInspection completed!")


if __name__ == "__main__":
    inspect_video_chunks()