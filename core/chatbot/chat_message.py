from pathlib import Path
import json
from datetime import datetime
import uuid

from core.supabase_client import get_supabase_client
from core.supabase_client import is_supabase_configured

# 대화 메시지 목록을 저장할 위치를 정의한다.
CHAT_MESSAGES_PATH = Path("store/chat/chat_messages.json")
SUPABASE_CHAT_MESSAGES_TABLE = "chat_messages"


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# 대화 메시지 저장 파일을 읽어 전체 메시지 목록을 가져온다.
def load_chat_messages(chat_messages_path=CHAT_MESSAGES_PATH):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_MESSAGES_TABLE)
        .select("*")
        .order("created_at")
        .execute()
    )

    return response.data or []


# 전체 대화 메시지 목록을 JSON 파일로 저장한다.
def save_chat_messages(messages, chat_messages_path=CHAT_MESSAGES_PATH):
    return messages


# 특정 대화방에 속한 메시지를 생성 시간순으로 가져온다.
def get_messages_by_room(chat_room_id, chat_messages_path=CHAT_MESSAGES_PATH):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_MESSAGES_TABLE)
        .select("*")
        .eq("chat_room_id", chat_room_id)
        .order("created_at")
        .execute()
    )

    return response.data or []


# 대화 메시지 metadata를 생성한다.
def create_chat_message(
    chat_room_id,
    role,
    content,
    sources=None,
    model_name=None,
    retrieval_mode=None,
):
    if sources is None:
        sources = []

    message = {
        "message_id": str(uuid.uuid4()),
        "chat_room_id": chat_room_id,
        "role": role,
        "content": content,
        "sources": sources,
        "created_at": get_current_datetime(),
    }

    if model_name is not None:
        message["model_name"] = model_name

    if retrieval_mode is not None:
        message["retrieval_mode"] = retrieval_mode

    return message


# 대화 메시지를 생성하고 저장소에 추가한다.
def append_chat_message(
    chat_room_id,
    role,
    content,
    sources=None,
    model_name=None,
    retrieval_mode=None,
    chat_messages_path=CHAT_MESSAGES_PATH,
):
    message = create_chat_message(
        chat_room_id=chat_room_id,
        role=role,
        content=content,
        sources=sources,
        model_name=model_name,
        retrieval_mode=retrieval_mode,
    )

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_MESSAGES_TABLE)
        .insert(message)
        .execute()
    )

    if response.data:
        return response.data[0]

    return message


# 사용자 질문 메시지를 저장한다.
def append_user_message(chat_room_id, content, chat_messages_path=CHAT_MESSAGES_PATH):
    return append_chat_message(
        chat_room_id=chat_room_id,
        role="user",
        content=content,
        sources=[],
        chat_messages_path=chat_messages_path,
    )


# AI 답변 메시지를 출처와 함께 저장한다.
def append_assistant_message(
    chat_room_id,
    content,
    sources,
    model_name,
    retrieval_mode,
    chat_messages_path=CHAT_MESSAGES_PATH,
):
    return append_chat_message(
        chat_room_id=chat_room_id,
        role="assistant",
        content=content,
        sources=sources,
        model_name=model_name,
        retrieval_mode=retrieval_mode,
        chat_messages_path=chat_messages_path,
    )
