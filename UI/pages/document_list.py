import streamlit as st
from datetime import datetime
from core.document_pipeline import update_document_active_status
from core.document_pipeline import METADATA_PATH, VECTOR_STORE_DIR
from core.rag_update import rebuild_vector_store
from core.resource_manager import add_common_document_to_personal_resources
from core.supabase_document_manager import create_document_signed_url
from core.supabase_document_manager import get_documents_by_category as get_supabase_documents_by_category

CATEGORIES = ["규정", "내규", "법령", "판례", "보도자료"]


# 선택한 카테고리의 문서만 최신순으로 정렬한다.
def get_documents_by_category(selected_category):
    return get_supabase_documents_by_category(selected_category)


# ISO 형식의 생성일을 화면 표시용 날짜로 변환한다.
def format_created_at(created_at):
    if not created_at:
        return "-"

    return created_at.split("T")[0]


# 문서 목록의 다운로드 버튼을 표시한다.
def render_document_download_button(document):
    signed_url_result = create_document_signed_url(document)

    if not signed_url_result["success"]:
        st.warning(signed_url_result["message"])
        return

    st.link_button(
        "다운로드",
        signed_url_result["url"],
        use_container_width=True,
    )


# RAG 문서 업데이트 버튼과 마지막 업데이트 시간을 표시한다.
def render_rag_update_area():
    if "rag_updated_at" not in st.session_state:
        st.session_state["rag_updated_at"] = "아직 업데이트 기록이 없습니다."

    left_col, right_col = st.columns([1, 3])

    with left_col:
        update_button = st.button(
            "RAG 문서 업데이트",
            type="primary",
            use_container_width=True,
        )

    with right_col:
        st.caption(f"업데이트 날짜(시간): {st.session_state['rag_updated_at']}")

    if update_button:
        result = rebuild_vector_store(
            METADATA_PATH,
            VECTOR_STORE_DIR,
        )

        if result["success"]:
            st.session_state["rag_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(
                f"{result['message']} "
                f"대상 문서 {result['document_count']}개, "
                f"청크 {result['chunk_count']}개"
            )
            st.rerun()
        else:
            st.warning(result["message"])

# 문서 조회에 사용할 카테고리 탭을 표시한다.
def render_category_tabs():
    selected_category = st.radio(
        "카테고리 선택",
        CATEGORIES,
        horizontal=True,
        label_visibility="collapsed",
    )

    return selected_category


# 선택한 카테고리에 해당하는 문서 목록을 표시한다.
def render_document_table(selected_category):
    documents = get_documents_by_category(selected_category)

    if not documents:
        st.info("선택한 카테고리에 등록된 문서가 없습니다.")
        return

    header_cols = st.columns([4, 2, 2, 2, 2])

    with header_cols[0]:
        st.markdown("**문서 제목**")

    with header_cols[1]:
        st.markdown("**업로드일**")

    with header_cols[2]:
        st.markdown("**상태**")

    with header_cols[3]:
        st.markdown("**다운로드**")

    with header_cols[4]:
        st.markdown("**내 자료**")

    st.divider()

    for index, document in enumerate(documents):
        document_id = document["document_id"]
        row_cols = st.columns([4, 2, 2, 2, 2])

        with row_cols[0]:
            st.button(
                document["file_name"],
                key=f"document_title_{selected_category}_{index}",
                use_container_width=True,
            )

        with row_cols[1]:
            st.write(document["created_at"])

        with row_cols[2]:
            current_is_active = document.get("is_active", False)

            new_is_active = st.toggle(
                "활성",
                value=current_is_active,
                key=f"document_active_{document_id}",
            )

            if new_is_active != current_is_active:
                update_document_active_status(
                    METADATA_PATH,
                    document_id,
                    new_is_active,
                )
                st.rerun()

        with row_cols[3]:
            render_document_download_button(document)

        with row_cols[4]:
            save_button = st.button(
                "내 자료에 저장",
                key=f"save_personal_resource_{document_id}",
                use_container_width=True,
            )

            if save_button:
                result = add_common_document_to_personal_resources(document)

                if result["success"]:
                    st.success(result["message"])
                else:
                    st.warning(result["message"])


# 공통 자료 조회 페이지의 전체 화면을 구성한다.
def render_document_list_page():
    st.title("공통 자료 조회")

    render_rag_update_area()

    st.divider()

    selected_category = render_category_tabs()

    st.divider()

    render_document_table(selected_category)
