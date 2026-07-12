from datetime import datetime
import re

from core.supabase_resource_manager import save_generated_resource_file


# 회의 제목을 파일명으로 사용할 수 있는 문자열로 변환한다.
def create_meeting_note_file_name(meeting_title):
    safe_title = re.sub(r'[\\/:*?"<>|]', "", meeting_title).strip()
    safe_title = safe_title.replace(" ", "_")

    if not safe_title:
        safe_title = "meeting_note"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{safe_title}_{timestamp}.md"


# 생성된 회의록 정보를 markdown 파일 내용으로 변환한다.
def build_meeting_note_markdown(meeting_note):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# {meeting_note.get("meeting_title", "회의록")}

생성일: {created_at}

## 회의 정보

- 회의 목적: {meeting_note.get("meeting_purpose", "-")}
- 회의 설명: {meeting_note.get("meeting_description", "-")}
- 저장 위치: {meeting_note.get("owner_type", "-")}

---

{meeting_note.get("content", "")}
"""


# 생성된 회의록을 파일로 저장하고 자료관리 metadata에 등록한다.
def save_generated_meeting_note(meeting_note):
    try:
        file_name = create_meeting_note_file_name(
            meeting_note.get("meeting_title", "회의록")
        )
        markdown_content = build_meeting_note_markdown(meeting_note)
        resource = save_generated_resource_file(
            owner_type=meeting_note.get("owner_type"),
            resource_type="meeting_note",
            source_type="generated_meeting_note",
            title=meeting_note.get("meeting_title", "회의록"),
            file_name=file_name,
            markdown_content=markdown_content,
        )

        return {
            "success": True,
            "message": "회의록이 저장되었습니다.",
            "file_name": resource.get("file_name"),
            "file_path": resource.get("file_path"),
            "resource": resource,
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"회의록 저장 중 오류가 발생했습니다: {str(error)}",
            "file_name": None,
            "file_path": None,
            "resource": None,
        }
