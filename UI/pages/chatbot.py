import streamlit as st
from core.chatbot.chat_response import generate_chat_response
from core.supabase_resource_manager import create_resource_signed_url

from core.chatbot.chat_room import (
    create_chat_room,
    get_chat_room_by_id,
    get_chat_rooms_latest_first,
    update_chat_room_updated_at
)

from core.chatbot.chat_message import (
    append_assistant_message,
    append_user_message,
    get_messages_by_room,
)


# 챗봇 페이지에서 사용할 세션 상태를 초기화한다.
def initialize_chatbot_state():
    if "selected_chat_room_id" not in st.session_state:
        st.session_state["selected_chat_room_id"] = None


# 새 대화방 생성 영역을 화면에 표시한다.
def render_chat_room_create_area():
    st.subheader("새 대화방 생성")

    chat_room_title = st.text_input(
        "대화방 제목",
        placeholder="대화방 제목을 입력하세요.",
    )

    create_button = st.button(
        "대화방 생성",
        type="primary",
        use_container_width=True,
    )

    if create_button:
        if not chat_room_title.strip():
            st.warning("대화방 제목을 입력하세요.")
            return

        chat_room = create_chat_room(chat_room_title.strip())
        st.session_state["selected_chat_room_id"] = chat_room["chat_room_id"]
        st.success("대화방이 생성되었습니다.")
        st.rerun()


# 기존 대화방 목록을 화면에 표시한다.
def render_chat_room_list_area():
    st.subheader("대화방 목록")

    chat_rooms = get_chat_rooms_latest_first()

    if not chat_rooms:
        st.info("생성된 대화방이 없습니다.")
        return

    for chat_room in chat_rooms:
        chat_room_id = chat_room["chat_room_id"]
        title = chat_room["title"]
        updated_at = chat_room.get("updated_at", "-")

        button_label = f"{title} ({updated_at})"

        if st.button(
            button_label,
            key=f"chat_room_{chat_room_id}",
            use_container_width=True,
        ):
            st.session_state["selected_chat_room_id"] = chat_room_id
            st.rerun()


# 현재 선택된 대화방 정보를 화면에 표시한다.
def render_selected_chat_room_area():
    selected_chat_room_id = st.session_state.get("selected_chat_room_id")

    if selected_chat_room_id is None:
        st.info("대화방을 생성하거나 선택하세요.")
        return

    chat_room = get_chat_room_by_id(selected_chat_room_id)

    if chat_room is None:
        st.warning("선택한 대화방을 찾을 수 없습니다.")
        st.session_state["selected_chat_room_id"] = None
        return

    st.subheader(chat_room["title"])
    st.caption(f"마지막 대화 시간: {chat_room.get('updated_at', '-')}")
    
    st.divider()

    render_chat_messages_area(selected_chat_room_id)

    render_chat_input_area(selected_chat_room_id)


# AI 챗봇 페이지의 전체 화면을 구성한다.
def render_chatbot_page():
    initialize_chatbot_state()

    st.title("AI 챗봇")

    left_col, right_col = st.columns([1, 2])

    with left_col:
        render_chat_room_create_area()
        st.divider()
        render_chat_room_list_area()

    with right_col:
        render_selected_chat_room_area()

# 선택된 대화방의 메시지 목록을 화면에 표시한다.
def render_chat_messages_area(chat_room_id):
    messages = get_messages_by_room(chat_room_id)

    if not messages:
        st.info("아직 대화 내용이 없습니다.")
        return

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            with st.chat_message("user"):
                st.write(content)

        elif role == "assistant":
            with st.chat_message("assistant"):
                st.write(content)

                sources = message.get("sources", [])
                if sources:
                    with st.expander("출처 자세히 보기"):
                        for source in sources:
                            source_type = source.get("source_type")
                            title = source.get("title", "알 수 없는 문서")
                            category = source.get("category")
                            signed_url_result = create_resource_signed_url(source)

                            st.caption(f"source_type: {source_type}")
                            st.caption(f"category: {category}")

                            if signed_url_result["success"]:
                                st.link_button(title, signed_url_result["url"])
                            else:
                                st.warning(signed_url_result["message"])


# 선택된 대화방에 새 메시지를 입력하고 저장한다.
def render_chat_input_area(chat_room_id):
    user_input = st.chat_input("질문을 입력하세요.")

    if user_input:
        append_user_message(
            chat_room_id=chat_room_id,
            content=user_input,
        )

        response = generate_chat_response(user_input)

        if not response["success"]:
            st.error(response["error_message"])
            return 

        append_assistant_message(
            chat_room_id=chat_room_id,
            content=response["answer"],
            sources=response["sources"],
            model_name=response["model_name"],
            retrieval_mode=response["retrieval_mode"],
        )

        update_chat_room_updated_at(chat_room_id)

        st.rerun()
