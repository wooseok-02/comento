from pathlib import Path
import json
from datetime import datetime
import uuid

from core.supabase_client import get_supabase_client
from core.supabase_client import is_supabase_configured

# 대화방 목록을 저장할 위치를 정의한다.
CHAT_ROOMS_PATH = Path("store/chat/chat_rooms.json")
SUPABASE_CHAT_ROOMS_TABLE = "chat_rooms"


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# 1.대화방 저장 파일을 읽어 전체 대화방 목록을 가져온다.
#- 대화방 목록 읽기
def load_chat_rooms(chat_rooms_path=CHAT_ROOMS_PATH):
    if not is_supabase_configured():
        return []

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_ROOMS_TABLE)
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []


# 2.전체 대화방 목록을 JSON 파일로 저장한다.
#- 대화방 목록 저장
def save_chat_rooms(chat_rooms, chat_rooms_path=CHAT_ROOMS_PATH):
    return chat_rooms


# 3.새 대화방 metadata를 생성한다.
#- 대화방 dict 생성
def create_chat_room_metadata(title):
    current_datetime = get_current_datetime()

    return {
        "chat_room_id": str(uuid.uuid4()),
        "title": title,
        "created_at": current_datetime,
        "updated_at": current_datetime,
    }


# 4.새 대화방을 생성하고 저장소에 추가한다.
#- 새 대화방 생성 후 저장
def create_chat_room(title, chat_rooms_path=CHAT_ROOMS_PATH):
    chat_room = create_chat_room_metadata(title)

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_ROOMS_TABLE)
        .insert(chat_room)
        .execute()
    )

    if response.data:
        return response.data[0]

    return chat_room


# 5.대화방 목록을 마지막 대화 시간 기준 최신순으로 가져온다.
#- updated_at 기준 최신순 정렬
def get_chat_rooms_latest_first(chat_rooms_path=CHAT_ROOMS_PATH):
    return load_chat_rooms(chat_rooms_path)


# 6.대화방 고유 ID로 특정 대화방을 찾는다.
#- 특정 대화방 하나 조회
def get_chat_room_by_id(chat_room_id, chat_rooms_path=CHAT_ROOMS_PATH):
    if not is_supabase_configured():
        return None

    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_ROOMS_TABLE)
        .select("*")
        .eq("chat_room_id", chat_room_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# 7.특정 대화방의 마지막 대화 시간을 현재 시간으로 갱신한다.
#- 마지막 대화 시간 갱신
def update_chat_room_updated_at(chat_room_id, chat_rooms_path=CHAT_ROOMS_PATH):
    supabase = get_supabase_client()
    response = (
        supabase.table(SUPABASE_CHAT_ROOMS_TABLE)
        .update({"updated_at": get_current_datetime()})
        .eq("chat_room_id", chat_room_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None
