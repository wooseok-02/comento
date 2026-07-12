from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.chroma_vector_store import reset_chroma_collection
from core.document_pipeline import extract_text_from_file_bytes
from core.supabase_document_manager import download_document_file_bytes
from core.supabase_document_manager import get_active_completed_documents as get_supabase_active_completed_documents


# 활성 상태이고 처리 완료된 문서만 Supabase에서 가져온다.
def get_active_completed_documents(metadata_path=None):
    return get_supabase_active_completed_documents()


# 활성 문서 목록을 기준으로 Chroma Cloud 벡터 DB를 새로 생성한다.
def rebuild_vector_store(metadata_path=None, vector_store_dir=None):
    target_documents = get_active_completed_documents()

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
        file_type = document_metadata["file_type"]

        file_bytes = download_document_file_bytes(document_metadata)
        extracted_text = extract_text_from_file_bytes(file_bytes, file_type)

        if not extracted_text.strip():
            continue

        document = Document(
            page_content=extracted_text,
            metadata={
                "document_id": document_metadata["document_id"],
                "file_name": document_metadata["file_name"],
                "category": document_metadata["category"],
                "file_path": document_metadata["file_path"],
                "storage_bucket": document_metadata.get("storage_bucket"),
                "storage_path": document_metadata.get("storage_path"),
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

    vector_store = reset_chroma_collection()
    vector_ids = [
        f"{document.metadata.get('document_id')}_{index}"
        for index, document in enumerate(split_documents)
    ]
    vector_store.add_documents(documents=split_documents, ids=vector_ids)

    return {
        "success": True,
        "message": "RAG 문서 업데이트가 완료되었습니다.",
        "document_count": len(target_documents),
        "chunk_count": len(split_documents),
    }
