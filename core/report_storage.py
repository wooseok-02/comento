from datetime import datetime
import re

from core.supabase_resource_manager import save_generated_resource_file


# 보고서 제목을 파일명으로 사용할 수 있는 문자열로 변환한다.
def create_report_file_name(title):
    safe_title = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    safe_title = safe_title.replace(" ", "_")

    if not safe_title:
        safe_title = "report"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{safe_title}_{timestamp}.md"


# 생성된 보고서 정보를 markdown 파일 내용으로 변환한다.
def build_report_markdown(report):
    sources = report.get("sources", [])

    source_lines = []

    for index, source in enumerate(sources, start=1):
        source_type = source.get("source_type")

        if source_type == "internal_document":
            title = source.get("title", "알 수 없는 문서")
            file_name = source.get("file_name", "")
            category = source.get("category", "")

            source_lines.append(
                f"{index}. [내부 문서] {title} / 파일명: {file_name} / 카테고리: {category}"
            )

        elif source_type == "web":
            title = source.get("title", "제목 없음")
            url = source.get("url", "")

            source_lines.append(
                f"{index}. [웹] {title} / URL: {url}"
            )

    if not source_lines:
        source_lines.append("참고 출처가 없습니다.")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# {report.get("title", "보고서")}

생성일: {created_at}

## 보고서 정보

- 주제: {report.get("topic", "-")}
- 목적: {report.get("purpose", "-")}
- 저장 위치: {report.get("owner_type", "-")}

---

{report.get("content", "")}

---

## 참고 출처

{chr(10).join(source_lines)}
"""


# 생성된 보고서를 파일로 저장하고 자료관리 metadata에 등록한다.
def save_generated_report(report):
    try:
        file_name = create_report_file_name(report.get("title", "보고서"))
        markdown_content = build_report_markdown(report)
        resource = save_generated_resource_file(
            owner_type=report.get("owner_type"),
            resource_type="report",
            source_type="generated_report",
            title=report.get("title", "보고서"),
            file_name=file_name,
            markdown_content=markdown_content,
        )

        return {
            "success": True,
            "message": "보고서가 저장되었습니다.",
            "file_name": resource.get("file_name"),
            "file_path": resource.get("file_path"),
            "resource": resource,
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"보고서 저장 중 오류가 발생했습니다: {str(error)}",
            "file_name": None,
            "file_path": None,
            "resource": None,
        }
