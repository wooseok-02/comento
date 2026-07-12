# 활성 상태이고 처리 완료된 문서만 벡터 DB 재생성 대상으로 가져온다.
from pathlib import Path
from core.document_pipeline import load_document_metadata
from core.document_pipeline import extract_text_from_file
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_active_completed_documents(metadata_path):
    documents = load_document_metadata(metadata_path)

    return [
        document
        for document in documents
        if document.get("is_active") is True
        and document.get("status") == "completed"
    ]

# 활성 문서 목록을 기준으로 FAISS 벡터 DB를 새로 생성한다.
def rebuild_vector_store(metadata_path, vector_store_dir):
    target_documents = get_active_completed_documents(metadata_path)

    if not target_documents:
        return {
            "success": False,
            "message": "벡터 DB 재생성 대상 문서가 없습니다.",
            "document_count": 0,
            "chunk_count": 0,
        }

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    split_documents = []

    for document_metadata in target_documents:
        file_path = Path(document_metadata["file_path"])
        file_type = document_metadata["file_type"]

        extracted_text = extract_text_from_file(file_path, file_type)

        if not extracted_text.strip():
            continue

        document = Document(
            page_content=extracted_text,
            metadata={
                "document_id": document_metadata["document_id"],
                "file_name": document_metadata["file_name"],
                "category": document_metadata["category"],
                "file_path": document_metadata["file_path"],
                "is_active": document_metadata["is_active"],
            },
        )

        split_documents.extend(text_splitter.split_documents([document]))

    if not split_documents:
        return {
            "success": False,
            "message": "벡터 DB에 저장할 문서 내용이 없습니다.",
            "document_count": len(target_documents),
            "chunk_count": 0,
        }

    embeddings = OpenAIEmbeddings()

    vector_store = FAISS.from_documents(
        documents=split_documents,
        embedding=embeddings,
    )

    vector_store.save_local(str(vector_store_dir))

    return {
        "success": True,
        "message": "RAG 문서 업데이트가 완료되었습니다.",
        "document_count": len(target_documents),
        "chunk_count": len(split_documents),
    }