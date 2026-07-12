from pathlib import Path
import json
from datetime import datetime
import uuid


# 개인/팀 자료 metadata를 저장할 위치를 정의한다.
RESOURCES_PATH = Path("store/resources/resources.json")


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# 자료 metadata 저장 파일을 읽어 전체 자료 목록을 가져온다.
def load_resources(resources_path=RESOURCES_PATH):
    if not resources_path.exists():
        return []

    if resources_path.stat().st_size == 0:
        return []

    with resources_path.open("r", encoding="utf-8") as file:
        return json.load(file)


# 전체 자료 metadata 목록을 JSON 파일로 저장한다.
def save_resources(resources, resources_path=RESOURCES_PATH):
    resources_path.parent.mkdir(parents=True, exist_ok=True)

    with resources_path.open("w", encoding="utf-8") as file:
        json.dump(resources, file, ensure_ascii=False, indent=2)


# 개인/팀 자료 metadata 항목을 생성한다.
def create_resource_metadata(
    owner_type,
    resource_type,
    source_type,
    title,
    file_name,
    file_path,
    source_document_id=None,
):
    return {
        "resource_id": str(uuid.uuid4()),
        "owner_type": owner_type,
        "resource_type": resource_type,
        "source_type": source_type,
        "title": title,
        "file_name": file_name,
        "file_path": file_path,
        "source_document_id": source_document_id,
        "created_at": get_current_datetime(),
    }


# 새 자료 metadata를 저장소에 추가한다.
def append_resource(resource_metadata, resources_path=RESOURCES_PATH):
    resources = load_resources(resources_path)
    resources.append(resource_metadata)
    save_resources(resources, resources_path)

    return resource_metadata


# 저장 범위와 자료 유형에 해당하는 자료 목록을 최신순으로 가져온다.
def get_resources_by_owner_and_type(
    owner_type,
    resource_type,
    resources_path=RESOURCES_PATH,
):
    resources = load_resources(resources_path)

    filtered_resources = [
        resource
        for resource in resources
        if resource.get("owner_type") == owner_type
        and resource.get("resource_type") == resource_type
    ]

    return sorted(
        filtered_resources,
        key=lambda resource: resource.get("created_at", ""),
        reverse=True,
    )


# 저장 범위에 해당하는 전체 자료 목록을 최신순으로 가져온다.
def get_resources_by_owner(
    owner_type,
    resources_path=RESOURCES_PATH,
):
    resources = load_resources(resources_path)

    filtered_resources = [
        resource
        for resource in resources
        if resource.get("owner_type") == owner_type
    ]

    return sorted(
        filtered_resources,
        key=lambda resource: resource.get("created_at", ""),
        reverse=True,
    )


# 공통 문서가 이미 같은 저장 범위의 자료로 저장되어 있는지 확인한다.
def is_duplicate_common_document_resource(
    owner_type,
    source_document_id,
    resources_path=RESOURCES_PATH,
):
    resources = load_resources(resources_path)

    for resource in resources:
        if (
            resource.get("owner_type") == owner_type
            and resource.get("source_type") == "common_document"
            and resource.get("source_document_id") == source_document_id
        ):
            return True

    return False


# 공통 RAG 문서 metadata를 개인 자료 metadata로 변환해 저장한다.
def add_common_document_to_personal_resources(
    document_metadata,
    resources_path=RESOURCES_PATH,
):
    document_id = document_metadata.get("document_id")

    if is_duplicate_common_document_resource(
        owner_type="personal",
        source_document_id=document_id,
        resources_path=resources_path,
    ):
        return {
            "success": False,
            "status": "duplicated",
            "message": "이미 내 자료에 저장된 문서입니다.",
            "resource": None,
        }

    resource_metadata = create_resource_metadata(
        owner_type="personal",
        resource_type="file",
        source_type="common_document",
        title=document_metadata.get("file_name", "알 수 없는 문서"),
        file_name=document_metadata.get("file_name", "알 수 없는 문서"),
        file_path=document_metadata.get("file_path"),
        source_document_id=document_id,
    )

    append_resource(resource_metadata, resources_path)

    return {
        "success": True,
        "status": "completed",
        "message": "내 자료에 저장되었습니다.",
        "resource": resource_metadata,
    }
