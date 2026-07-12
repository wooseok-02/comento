import streamlit as st

from core.document_download import read_document_file_for_download
from core.resource_manager import get_resources_by_owner
from core.resource_manager import get_resources_by_owner_and_type
from core.supabase_resource_manager import create_resource_signed_url
from core.supabase_resource_manager import get_supabase_resources_by_owner
from core.supabase_resource_manager import get_supabase_resources_by_owner_and_type


OWNER_LABELS = {
    "personal": "개인",
    "teams": "Teams",
}

RESOURCE_TYPE_LABELS = {
    "meeting_note": "회의록",
    "report": "보고서",
    "file": "자료",
}

RESOURCE_FILTER_OPTIONS = {
    "전체": None,
    "회의록": "meeting_note",
    "보고서": "report",
    "자료": "file",
}


# ISO 형식의 생성일을 화면 표시용 날짜로 변환한다.
def format_created_at(created_at):
    if not created_at:
        return "-"

    return created_at.split("T")[0]


# 자료관리 페이지 제목을 생성한다.
def format_resource_page_title(owner_type):
    owner_label = OWNER_LABELS.get(owner_type, owner_type)

    return f"{owner_label} 자료"


# 자료 유형 필터를 화면에 표시하고 선택된 자료 유형을 반환한다.
def render_resource_type_filter(owner_type):
    selected_label = st.radio(
        "자료 유형",
        list(RESOURCE_FILTER_OPTIONS.keys()),
        horizontal=True,
        key=f"resource_type_filter_{owner_type}",
    )

    return RESOURCE_FILTER_OPTIONS[selected_label]


# 선택한 저장 범위와 자료 유형에 맞는 자료 목록을 가져온다.
def get_filtered_resources(owner_type, selected_resource_type):
    if selected_resource_type is None:
        local_resources = get_resources_by_owner(owner_type=owner_type)
        supabase_resources = get_supabase_resources_by_owner(owner_type=owner_type)
    else:
        local_resources = get_resources_by_owner_and_type(
            owner_type=owner_type,
            resource_type=selected_resource_type,
        )
        supabase_resources = get_supabase_resources_by_owner_and_type(
            owner_type=owner_type,
            resource_type=selected_resource_type,
        )

    return sorted(
        local_resources + supabase_resources,
        key=lambda resource: resource.get("created_at", ""),
        reverse=True,
    )


# 자료 목록의 다운로드 버튼을 표시한다.
def render_resource_download_button(resource):
    if resource.get("storage_path"):
        signed_url_result = create_resource_signed_url(resource)

        if not signed_url_result["success"]:
            st.warning(signed_url_result["message"])
            return

        st.link_button(
            "다운로드",
            signed_url_result["url"],
            use_container_width=True,
        )
        return

    file_path = resource.get("file_path")

    if not file_path:
        st.warning("원본 파일 경로가 없습니다.")
        return

    download_result = read_document_file_for_download(file_path)

    if not download_result["success"]:
        st.warning(download_result["error_message"])
        return

    st.download_button(
        "다운로드",
        data=download_result["file_bytes"],
        file_name=resource.get("file_name", "download"),
        mime="application/octet-stream",
        key=f"resource_download_{resource['resource_id']}",
        use_container_width=True,
    )


# 선택한 저장 범위와 자료 유형에 해당하는 자료 목록을 표시한다.
def render_resource_list_page(owner_type):
    st.title(format_resource_page_title(owner_type))

    selected_resource_type = render_resource_type_filter(owner_type)

    st.divider()

    resources = get_filtered_resources(owner_type, selected_resource_type)

    if not resources:
        st.info("등록된 자료가 없습니다.")
        return

    header_cols = st.columns([4, 2, 2, 2, 2])

    with header_cols[0]:
        st.markdown("**제목**")

    with header_cols[1]:
        st.markdown("**자료 유형**")

    with header_cols[2]:
        st.markdown("**저장일**")

    with header_cols[3]:
        st.markdown("**출처 유형**")

    with header_cols[4]:
        st.markdown("**다운로드**")

    st.divider()

    for resource in resources:
        row_cols = st.columns([4, 2, 2, 2, 2])

        with row_cols[0]:
            st.write(resource.get("title", "-"))

        with row_cols[1]:
            resource_type = resource.get("resource_type")
            st.write(RESOURCE_TYPE_LABELS.get(resource_type, resource_type or "-"))

        with row_cols[2]:
            st.write(format_created_at(resource.get("created_at")))

        with row_cols[3]:
            st.write(resource.get("source_type", "-"))

        with row_cols[4]:
            render_resource_download_button(resource)
