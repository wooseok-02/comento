import streamlit as st
from core.document_pipeline import process_uploaded_document

# 문서 업로드 페이지의 전체 화면을 구성한다.
def render_document_upload_page():
    st.title("문서 업로드")

    # 문서 업로드 UI를 표시하고 사용자가 선택한 값을 받는다.
    uploaded_file, file_type, category, upload_button = render_document_upload_area()

    # 문서 처리 과정 영역을 나중에 다시 그릴 수 있도록 placeholder로 만든다.
    process_area = st.empty()

    # 문서 처리 과정 영역을 현재 상태 기준으로 다시 그린다.
    def refresh_process_area():
        with process_area.container():
            render_document_process_area()

    # 업로드 버튼 클릭 전에도 기존 처리 과정 영역을 표시한다.
    refresh_process_area()

    # 업로드 버튼 클릭 시 문서 저장 파이프라인과 처리 과정 UI를 연결한다.
    if upload_button:
        if uploaded_file is None:
            st.error("업로드할 문서를 선택하세요.")
        else:
            file_name = uploaded_file.name

            # 현재 업로드 문서의 처리 과정 카드를 생성한다.
            add_document_process(file_name)

            # 업로드 버튼 클릭이 정상적으로 들어왔음을 즉시 표시한다.
            update_document_process_step(
                file_name,
                "문서 업로드 버튼",
                "완료",
            )

            refresh_process_area()

            # 파이프라인 단계 변화가 발생할 때 처리 과정 UI를 업데이트한다.
            def update_progress(step_name, status, message=""):
                update_document_process_step(
                    file_name,
                    step_name,
                    status,
                    message,
                )
                refresh_process_area()

            try:
                # 단계별 콜백을 넘겨 문서 처리 파이프라인을 실행한다.
                result = process_uploaded_document(
                    uploaded_file,
                    category,
                    progress_callback=update_progress,
                )

                if result["status"] == "duplicated":
                    # 중복 문서일 때 문서 전체 상태를 중복으로 표시한다.
                    update_document_current_status(file_name, "중복")
                    refresh_process_area()
                    st.warning(result["message"])

                elif result["status"] == "completed":
                    # 문서 처리가 완료되었을 때 문서 전체 상태를 완료로 표시한다.
                    update_document_current_status(file_name, "완료")
                    refresh_process_area()
                    st.success(result["message"])

                else:
                    # 문서 처리가 실패했을 때 문서 전체 상태를 실패로 표시한다.
                    update_document_current_status(file_name, "실패")
                    refresh_process_area()
                    st.error(result["message"])

            except Exception as error:
                # 예외 발생 시 문서 전체 상태를 실패로 표시한다.
                update_document_current_status(file_name, "실패")
                refresh_process_area()
                st.error(f"문서 처리 중 오류가 발생했습니다: {error}")


# 문서 업로드 영역을 화면에 표시한다.
def render_document_upload_area():
    st.subheader("문서 업로드")

    # 관리자가 업로드할 문서 파일을 선택한다.
    uploaded_file = st.file_uploader(
        "업로드할 문서를 선택하세요",
        type=["pdf", "txt", "md"],
    )

    # 시스템이 선택된 파일의 형식을 화면에 표시한다.
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_type = file_name.split(".")[-1].lower()

        st.info(f"선택된 파일: {file_name}")
        st.caption(f"파일 형식: {file_type.upper()}")
    else:
        file_type = None

    # 관리자가 문서 카테고리를 선택한다.
    category = st.selectbox(
        "문서 카테고리를 선택하세요",
        ["규정", "내규", "법령", "판례", "보도자료"],
    )

    # 관리자가 문서 업로드 처리를 시작한다.
    upload_button = st.button(
        "문서 업로드",
        type="primary",
        use_container_width=True,
    )

    return uploaded_file, file_type, category, upload_button


"""
문서 업로드를 통한 처리 영역
"""

PROCESS_STEPS = [
    "문서 업로드 버튼",
    "문서 형태 파악",
    "문서 중복 확인",
    "문서 원문 저장",
    "상태 업데이트",
]


# 문서 처리 과정 상태를 세션에 저장할 기본 공간을 준비한다.
def initialize_process_state():
    if "document_processes" not in st.session_state:
        st.session_state["document_processes"] = []


# 업로드된 문서의 처리 과정 표시 데이터를 생성한다.
def create_document_process(file_name):
    return {
        "file_name": file_name,
        "current_status": "처리중",
        "steps": [
            {"name": step_name, "status": "대기", "message": ""}
            for step_name in PROCESS_STEPS
        ],
    }


# 문서 처리 과정 목록에 새 문서 처리 항목을 추가한다.
def add_document_process(file_name):
    initialize_process_state()
    st.session_state["document_processes"].append(
        create_document_process(file_name)
    )


# 문서 처리 단계의 상태와 메시지를 변경한다.
def update_document_process_step(file_name, step_name, status, message=""):
    initialize_process_state()

    for process in st.session_state["document_processes"]:
        if process["file_name"] == file_name:
            for step in process["steps"]:
                if step["name"] == step_name:
                    step["status"] = status
                    step["message"] = message


# 문서 전체 처리 상태를 변경한다.
def update_document_current_status(file_name, current_status):
    initialize_process_state()

    for process in st.session_state["document_processes"]:
        if process["file_name"] == file_name:
            process["current_status"] = current_status


# 단계 상태에 따라 화면에 표시할 문구를 만든다.
def format_step_status(step):
    if step["message"]:
        return f"{step['name']} - {step['status']} ({step['message']})"

    return f"{step['name']} - {step['status']}"


# 업로드된 문서들의 처리 과정을 expander 형태로 표시한다.
def render_document_process_area():
    initialize_process_state()

    st.subheader("문서 처리 과정")

    if not st.session_state["document_processes"]:
        st.info("아직 처리 중인 문서가 없습니다.")
        return

    for process in st.session_state["document_processes"]:
        left_col, right_col = st.columns([4, 1])

        with left_col:
            st.markdown(f"**{process['file_name']}**")

        with right_col:
            st.markdown(f"**{process['current_status']}**")

        with st.expander("처리 과정 보기"):
            for step in process["steps"]:
                st.write(format_step_status(step))
