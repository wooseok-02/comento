import os
import streamlit as st
from dotenv import load_dotenv

from UI.components.sidebar import render_sidebar
from UI.pages.document_upload import render_document_upload_page
from UI.pages.document_list import render_document_list_page
from UI.pages.chatbot import render_chatbot_page
from UI.pages.resource_list import render_resource_list_page
from UI.pages.report_create import render_report_create_page
from UI.pages.meeting_create import render_meeting_create_page

# .env 파일에 있는 환경변수를 현재 실행 환경에 로드한다.
load_dotenv()

# Streamlit 앱의 기본 화면 설정을 지정한다.
st.set_page_config(page_title="월드비전 AI 플랫폼", layout="wide")


# Streamlit Cloud secrets를 환경변수로 복사해 외부 SDK들이 읽을 수 있게 한다.
def load_streamlit_secrets_to_environment():
    secret_keys = [
        "OPENAI_API_KEY",
        "TAVILY_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_STORAGE_BUCKET",
        "SUPABASE_DOCUMENT_BUCKET",
        "CHROMA_API_KEY",
        "CHROMA_TENANT",
        "CHROMA_DATABASE",
        "CHROMA_COLLECTION_NAME",
        "OPENAI_EMBEDDING_MODEL",
    ]

    for secret_key in secret_keys:
        if os.getenv(secret_key):
            continue

        try:
            secret_value = st.secrets.get(secret_key)
        except Exception:
            secret_value = None

        if secret_value:
            os.environ[secret_key] = str(secret_value)


load_streamlit_secrets_to_environment()


# 앱의 기본 메인 화면을 표시한다.
def render_main_page():
    st.title("월드비전 AI 플랫폼")
    st.info("왼쪽 사이드바에서 사용할 메뉴를 선택하세요.")


# 사이드바를 항상 표시하고 선택된 페이지 값을 가져온다.
selected_page = render_sidebar()


# 선택된 사이드바 메뉴에 따라 본문 화면을 전환한다.
if selected_page == "document_upload":
    render_document_upload_page()
elif selected_page == "document_list":
    render_document_list_page()
elif selected_page == "chatbot":
    render_chatbot_page()
elif selected_page == "teams_resources":
    render_resource_list_page("teams")
elif selected_page == "personal_resources":
    render_resource_list_page("personal")
elif selected_page == "report_create":
    render_report_create_page()
elif selected_page == "meeting_create":
    render_meeting_create_page()
else:
    render_main_page()
