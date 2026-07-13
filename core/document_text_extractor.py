from io import BytesIO

from pypdf import PdfReader


# 저장된 파일 경로에서 문서 텍스트를 추출한다.
def extract_text_from_file(file_path, file_type):
    if file_type == "pdf":
        reader = PdfReader(file_path)
        pages = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)

        return "\n".join(pages)

    if file_type in ["txt", "md"]:
        return file_path.read_text(encoding="utf-8")

    raise ValueError("올바르지 않은 문서 형식")


# 파일 bytes에서 문서 텍스트를 추출한다.
def extract_text_from_file_bytes(file_bytes, file_type):
    if file_type == "pdf":
        reader = PdfReader(BytesIO(file_bytes))
        pages = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)

        return "\n".join(pages)

    if file_type in ["txt", "md"]:
        return file_bytes.decode("utf-8")

    raise ValueError("올바르지 않은 문서 형식")
