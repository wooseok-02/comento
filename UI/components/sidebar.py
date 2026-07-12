import streamlit as st


# 사이드바에서 사용할 메뉴 상태를 초기화한다.
def initialize_sidebar_state():
    if "document_menu_open" not in st.session_state:
        st.session_state["document_menu_open"] = False

    if "automation_menu_open" not in st.session_state:
        st.session_state["automation_menu_open"] = False

    if "resource_menu_open" not in st.session_state:
        st.session_state["resource_menu_open"] = False

    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "main"


# 문서관리 메뉴의 열림/닫힘 상태를 전환한다.
def toggle_document_menu():
    st.session_state["document_menu_open"] = not st.session_state["document_menu_open"]
    st.session_state["automation_menu_open"] = False
    st.session_state["resource_menu_open"] = False


# 업무 자동화 메뉴의 열림/닫힘 상태를 전환한다.
def toggle_automation_menu():
    st.session_state["automation_menu_open"] = not st.session_state["automation_menu_open"]
    st.session_state["document_menu_open"] = False
    st.session_state["resource_menu_open"] = False


# 자료 관리 메뉴의 열림/닫힘 상태를 전환한다.
def toggle_resource_menu():
    st.session_state["resource_menu_open"] = not st.session_state["resource_menu_open"]
    st.session_state["document_menu_open"] = False
    st.session_state["automation_menu_open"] = False


# 문서 업로드 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_document_upload():
    st.session_state["selected_page"] = "document_upload"


# 문서 조회 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_document_list():
    st.session_state["selected_page"] = "document_list"


# 회의 생성 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_meeting_create():
    st.session_state["selected_page"] = "meeting_create"


# OCR 문서 분석 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_ocr_analysis():
    st.session_state["selected_page"] = "ocr_analysis"


# 보고서 생성 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_report_create():
    st.session_state["selected_page"] = "report_create"


# Teams 자료관리 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_teams_resources():
    st.session_state["selected_page"] = "teams_resources"


# 개인 자료관리 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_personal_resources():
    st.session_state["selected_page"] = "personal_resources"


# 챗봇 페이지로 이동하도록 선택 상태를 변경한다.
def move_to_chatbot():
    st.session_state["document_menu_open"] = False
    st.session_state["automation_menu_open"] = False
    st.session_state["resource_menu_open"] = False
    st.session_state["selected_page"] = "chatbot"


# 사이드바 메뉴를 화면에 표시하고 현재 선택된 페이지를 반환한다.
def render_sidebar():
    initialize_sidebar_state()

    st.sidebar.title("관리 메뉴")

    st.sidebar.button(
        "문서관리",
        use_container_width=True,
        on_click=toggle_document_menu,
    )

    if st.session_state["document_menu_open"]:
        selected_document_menu = st.sidebar.radio(
            "문서관리 하위 메뉴",
            ["문서 업로드", "문서 조회"],
            label_visibility="collapsed",
            key="selected_document_menu",
        )

        if selected_document_menu == "문서 업로드":
            move_to_document_upload()
        elif selected_document_menu == "문서 조회":
            move_to_document_list()

    st.sidebar.button(
        "업무 자동화",
        use_container_width=True,
        on_click=toggle_automation_menu,
    )

    if st.session_state["automation_menu_open"]:
        selected_automation_menu = st.sidebar.radio(
            "업무 자동화 하위 메뉴",
            ["회의 생성", "OCR 문서 분석", "보고서 생성"],
            label_visibility="collapsed",
            key="selected_automation_menu",
        )

        if selected_automation_menu == "회의 생성":
            move_to_meeting_create()
        elif selected_automation_menu == "OCR 문서 분석":
            move_to_ocr_analysis()
        elif selected_automation_menu == "보고서 생성":
            move_to_report_create()

    st.sidebar.button(
        "자료 관리",
        use_container_width=True,
        on_click=toggle_resource_menu,
    )

    if st.session_state["resource_menu_open"]:
        selected_resource_menu = st.sidebar.radio(
            "자료 관리 하위 메뉴",
            [
                "Teams",
                "개인",
            ],
            label_visibility="collapsed",
            key="selected_resource_menu",
        )

        if selected_resource_menu == "Teams":
            move_to_teams_resources()
        elif selected_resource_menu == "개인":
            move_to_personal_resources()

    st.sidebar.button(
        "챗봇",
        use_container_width=True,
        on_click=move_to_chatbot,
    )

    return st.session_state["selected_page"]
