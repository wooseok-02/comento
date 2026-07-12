import os
import uuid
from datetime import datetime

from core.supabase_client import get_supabase_client
from core.supabase_client import is_supabase_configured


SUPABASE_DOCUMENTS_TABLE = "documents"
DEFAULT_SUPABASE_DOCUMENT_BUCKET = "uploaded-documents"


# Supabase 문서 Storage bucket 이름을 환경변수에서 가져온다.
def get_supabase_document_bucket():
    return os.getenv("SUPABASE_DOCUMENT_BUCKET", DEFAULT_SUPABASE_DOCUMENT_BUCKET)


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# Supabase Storage에 저장할 문서 경로를 생성한다.
def create_document_storage_path(document_id, file_name):
    return f"documents/{document_id}/{file_name}"


# 업로드 문서 원본 파일을 Supabase Storage에 저장한다.
def upload_document_file_to_storage(document_id, file_name, file_bytes, content_type=None):
    supabase = get_supabase_client()
    storage_bucket = get_supabase_document_bucket()
    storage_path = create_document_storage_path(document_id, file_name)

    supabase.storage.from_(storage_bucket).upload(
        storage_path,
        file_bytes,
        {
            "content-type": content_type or "application/octet-stream",
            "upsert": "true",
        },
    )

    return {
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
    }


# Supabase documents table에 저장할 문서 metadata를 생성한다.
def create_supabase_document_metadata(
    document_id,
    file_name,
    category,
    file_type,
    file_hash,
    storage_bucket,
    storage_path,
):
    return {
        "document_id": document_id,
        "file_name": file_name,
        "category": category,
        "file_type": file_type,
        "file_hash": file_hash,
        "file_path": f"supabase://{storage_bucket}/{storage_path}",
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "status": "completed",
        "status_message": "문서 원본 저장 완료",
        "is_active": True,
        "created_at": get_current_datetime(),
    }


# Supabase documents table에 문서 metadata를 등록한다.
def insert_document_metadata(document_metadata):
    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .insert(document_metadata)
        .execute()
    )

    if response.data:
        return response.data[0]

    return document_metadata


# Supabase documents table에서 전체 문서 metadata를 최신순으로 가져온다.
def get_all_documents():
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# Supabase documents table에서 카테고리에 해당하는 문서 metadata를 가져온다.
def get_documents_by_category(category):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .select("*")
        .eq("category", category)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# Supabase documents table에서 활성화된 완료 문서만 가져온다.
def get_active_completed_documents():
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .select("*")
        .eq("is_active", True)
        .eq("status", "completed")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# Supabase documents table에서 같은 파일 해시가 존재하는지 확인한다.
def is_duplicate_document_hash(file_hash):
    if not is_supabase_configured():
        return False

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .select("document_id")
        .eq("file_hash", file_hash)
        .limit(1)
        .execute()
    )

    return bool(response.data)


# Supabase documents table에서 특정 문서의 활성 상태를 변경한다.
def update_supabase_document_active_status(document_id, is_active):
    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_DOCUMENTS_TABLE)
        .update({"is_active": is_active})
        .eq("document_id", document_id)
        .execute()
    )

    return response.data or []


# Supabase Storage에서 문서 원본 파일 bytes를 내려받는다.
def download_document_file_bytes(document_metadata):
    storage_bucket = document_metadata.get("storage_bucket") or get_supabase_document_bucket()
    storage_path = document_metadata.get("storage_path")

    if not storage_path:
        raise ValueError("문서 Storage 경로가 없습니다.")

    supabase = get_supabase_client()
    return supabase.storage.from_(storage_bucket).download(storage_path)


# Supabase Storage 문서를 내려받을 수 있는 signed URL을 생성한다.
def create_document_signed_url(document_metadata, expires_in=3600):
    storage_bucket = document_metadata.get("storage_bucket") or get_supabase_document_bucket()
    storage_path = document_metadata.get("storage_path")

    if not storage_path:
        return {
            "success": False,
            "url": None,
            "message": "문서 Storage 경로가 없습니다.",
        }

    try:
        supabase = get_supabase_client()
        response = (
            supabase.storage.from_(storage_bucket)
            .create_signed_url(storage_path, expires_in)
        )
        signed_url = response.get("signedURL") or response.get("signedUrl")

        return {
            "success": bool(signed_url),
            "url": signed_url,
            "message": None if signed_url else "다운로드 URL을 생성하지 못했습니다.",
        }

    except Exception as error:
        return {
            "success": False,
            "url": None,
            "message": str(error),
        }


# 업로드된 문서를 Supabase Storage와 documents table에 함께 저장한다.
def save_uploaded_document_to_supabase(file_name, file_type, category, file_hash, file_bytes, content_type=None):
    document_id = str(uuid.uuid4())

    storage_result = upload_document_file_to_storage(
        document_id=document_id,
        file_name=file_name,
        file_bytes=file_bytes,
        content_type=content_type,
    )

    document_metadata = create_supabase_document_metadata(
        document_id=document_id,
        file_name=file_name,
        category=category,
        file_type=file_type,
        file_hash=file_hash,
        storage_bucket=storage_result["storage_bucket"],
        storage_path=storage_result["storage_path"],
    )

    return insert_document_metadata(document_metadata)
