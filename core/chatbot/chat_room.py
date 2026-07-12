from pathlib import Path
import json
from datetime import datetime
import uuid

# 대화방 목록을 저장할 위치를 정의한다.
CHAT_ROOMS_PATH = Path("store/chat/chat_rooms.json")


# 현재 시간을 ISO 문자열로 생성한다.
def get_current_datetime():
    return datetime.now().isoformat(timespec="seconds")


# 1.대화방 저장 파일을 읽어 전체 대화방 목록을 가져온다.
#- 대화방 목록 읽기
def load_chat_rooms(chat_rooms_path=CHAT_ROOMS_PATH):
    if not chat_rooms_path.exists():
        return []

    with chat_rooms_path.open("r", encoding="utf-8") as file:
        return json.load(file)


# 2.전체 대화방 목록을 JSON 파일로 저장한다.
#- 대화방 목록 저장
def save_chat_rooms(chat_rooms, chat_rooms_path=CHAT_ROOMS_PATH):
    chat_rooms_path.parent.mkdir(parents=True, exist_ok=True)

    with chat_rooms_path.open("w", encoding="utf-8") as file:
        json.dump(chat_rooms, file, ensure_ascii=False, indent=2)


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
    chat_rooms = load_chat_rooms(chat_rooms_path)
    chat_room = create_chat_room_metadata(title)

    chat_rooms.append(chat_room)
    save_chat_rooms(chat_rooms, chat_rooms_path)

    return chat_room


# 5.대화방 목록을 마지막 대화 시간 기준 최신순으로 가져온다.
#- updated_at 기준 최신순 정렬
def get_chat_rooms_latest_first(chat_rooms_path=CHAT_ROOMS_PATH):
    chat_rooms = load_chat_rooms(chat_rooms_path)

    return sorted(
        chat_rooms,
        key=lambda chat_room: chat_room.get("updated_at", ""),
        reverse=True,
    )


# 6.대화방 고유 ID로 특정 대화방을 찾는다.
#- 특정 대화방 하나 조회
def get_chat_room_by_id(chat_room_id, chat_rooms_path=CHAT_ROOMS_PATH):
    chat_rooms = load_chat_rooms(chat_rooms_path)

    for chat_room in chat_rooms:
        if chat_room.get("chat_room_id") == chat_room_id:
            return chat_room

    return None


# 7.특정 대화방의 마지막 대화 시간을 현재 시간으로 갱신한다.
#- 마지막 대화 시간 갱신
def update_chat_room_updated_at(chat_room_id, chat_rooms_path=CHAT_ROOMS_PATH):
    chat_rooms = load_chat_rooms(chat_rooms_path)
    updated_chat_room = None

    for chat_room in chat_rooms:
        if chat_room.get("chat_room_id") == chat_room_id:
            chat_room["updated_at"] = get_current_datetime()
            updated_chat_room = chat_room
            break

    save_chat_rooms(chat_rooms, chat_rooms_path)

    return updated_chat_room