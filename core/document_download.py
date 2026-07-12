from pathlib import Path


# 원본 문서 파일을 다운로드할 수 있도록 파일 내용을 읽는다.
def read_document_file_for_download(file_path):
    document_path = Path(file_path)

    if not document_path.exists():
        return {
            "success": False,
            "file_bytes": None,
            "error_message": "원본 파일을 찾을 수 없습니다.",
        }

    return {
        "success": True,
        "file_bytes": document_path.read_bytes(),
        "error_message": None,
    }
