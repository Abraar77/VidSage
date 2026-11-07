from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_transcript(transcript: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    chunks = splitter.create_documents(
        [transcript]
    )

    return chunks