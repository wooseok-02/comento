import os
import uuid
from datetime import datetime

from core.supabase_client import get_supabase_client
from core.supabase_client import is_supabase_configured


SUPABASE_RESOURCES_TABLE = "resources"
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "generated-files")


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# Supabase Storage에 저장할 산출물 경로를 생성한다.
def create_storage_path(resource_type, file_name):
    if resource_type == "report":
        return f"reports/{file_name}"

    if resource_type == "meeting_note":
        return f"meeting_notes/{file_name}"

    return f"files/{file_name}"


# markdown 문자열을 Supabase Storage에 업로드한다.
def upload_markdown_to_storage(storage_path, markdown_content):
    supabase = get_supabase_client()

    supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
        storage_path,
        markdown_content.encode("utf-8"),
        {
            "content-type": "text/markdown; charset=utf-8",
            "upsert": "true",
        },
    )

    return {
        "storage_bucket": SUPABASE_STORAGE_BUCKET,
        "storage_path": storage_path,
    }


# Supabase resources table에 저장할 metadata를 생성한다.
def create_supabase_resource_metadata(
    owner_type,
    resource_type,
    source_type,
    title,
    file_name,
    storage_bucket,
    storage_path,
    source_document_id=None,
):
    return {
        "resource_id": str(uuid.uuid4()),
        "owner_type": owner_type,
        "resource_type": resource_type,
        "source_type": source_type,
        "title": title,
        "file_name": file_name,
        "file_path": f"supabase://{storage_bucket}/{storage_path}",
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "source_document_id": source_document_id,
        "created_at": get_current_datetime(),
    }


# Supabase resources table에 자료 metadata를 등록한다.
def insert_resource_metadata(resource_metadata):
    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_RESOURCES_TABLE)
        .insert(resource_metadata)
        .execute()
    )

    if response.data:
        return response.data[0]

    return resource_metadata


# 생성 산출물 파일을 Storage에 저장하고 resources table에 등록한다.
def save_generated_resource_file(
    owner_type,
    resource_type,
    source_type,
    title,
    file_name,
    markdown_content,
):
    if not is_supabase_configured():
        raise ValueError("Supabase 환경변수가 설정되지 않았습니다.")

    storage_path = create_storage_path(resource_type, file_name)
    storage_result = upload_markdown_to_storage(storage_path, markdown_content)

    resource_metadata = create_supabase_resource_metadata(
        owner_type=owner_type,
        resource_type=resource_type,
        source_type=source_type,
        title=title,
        file_name=file_name,
        storage_bucket=storage_result["storage_bucket"],
        storage_path=storage_result["storage_path"],
    )

    return insert_resource_metadata(resource_metadata)


# Supabase에서 저장 범위에 해당하는 전체 자료 목록을 최신순으로 가져온다.
def get_supabase_resources_by_owner(owner_type):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_RESOURCES_TABLE)
        .select("*")
        .eq("owner_type", owner_type)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# Supabase에서 저장 범위와 자료 유형에 해당하는 자료 목록을 최신순으로 가져온다.
def get_supabase_resources_by_owner_and_type(owner_type, resource_type):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_RESOURCES_TABLE)
        .select("*")
        .eq("owner_type", owner_type)
        .eq("resource_type", resource_type)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# Supabase Storage 파일을 내려받을 수 있는 signed URL을 생성한다.
def create_resource_signed_url(resource, expires_in=3600):
    storage_bucket = resource.get("storage_bucket") or SUPABASE_STORAGE_BUCKET
    storage_path = resource.get("storage_path")

    if not storage_path:
        return {
            "success": False,
            "url": None,
            "message": "Supabase Storage 경로가 없습니다.",
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
