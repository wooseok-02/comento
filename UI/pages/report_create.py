import streamlit as st

from core.report_graph import generate_report_preview
from core.report_storage import save_generated_report


# 보고서 생성 페이지의 전체 화면을 구성한다.
def render_report_create_page():
    st.title("보고서 생성")

    if "generated_report_preview" not in st.session_state:
        st.session_state["generated_report_preview"] = None

    title = st.text_input(
        "보고서 제목",
        placeholder="보고서 제목을 입력하세요.",
    )

    topic = st.text_input(
        "보고서 주제",
        placeholder="보고서 주제를 입력하세요.",
    )

    purpose = st.text_area(
        "보고서 목적",
        placeholder="보고서 목적을 입력하세요.",
    )

    owner_label = st.radio(
        "저장 위치",
        ["개인", "Teams"],
        horizontal=True,
    )

    owner_type = "personal" if owner_label == "개인" else "teams"

    generate_button = st.button(
        "보고서 생성",
        type="primary",
        use_container_width=True,
    )

    if generate_button:
        with st.spinner("보고서를 생성하는 중입니다."):
            result = generate_report_preview(
                title=title,
                topic=topic,
                purpose=purpose,
                owner_type=owner_type,
            )

        if result["success"]:
            st.session_state["generated_report_preview"] = result["report"]
            st.success(result["message"])
        else:
            st.session_state["generated_report_preview"] = None
            st.warning(result["message"])

    report_preview = st.session_state.get("generated_report_preview")

    if report_preview:
        st.divider()

        st.subheader("보고서 미리보기")
        st.markdown(report_preview["content"])

        sources = report_preview.get("sources", [])

        if sources:
            with st.expander("출처 자세히 보기"):
                for source in sources:
                    source_type = source.get("source_type")

                    if source_type == "internal_document":
                        st.write(source.get("title", "알 수 없는 문서"))
                        st.caption(f"category: {source.get('category')}")
                        st.caption(f"file_name: {source.get('file_name')}")

                    elif source_type == "web":
                        title = source.get("title", "제목 없음")
                        url = source.get("url")

                        if url:
                            st.link_button(title, url)
                        else:
                            st.write(title)

        save_button = st.button(
            "보고서 저장",
            use_container_width=True,
        )

        if save_button:
            save_result = save_generated_report(report_preview)

            if save_result["success"]:
                st.success(save_result["message"])
            else:
                st.warning(save_result["message"])