from pathlib import Path
import hashlib
import json
from datetime import datetime
from io import BytesIO

ALLOWED_EXTENSIONS = {"pdf", "txt", "md"}
# 업로드된 원본 문서를 저장할 위치를 정의한다.
ORIGINALS_DIR = Path("store/originals")
# 문서 metadata 파일을 저장할 위치를 정의한다.
METADATA_PATH = Path("store/metadata/documents.json")
# 이전 로컬 벡터 저장소 인자 호환을 위해 남겨둔 경로를 정의한다.
VECTOR_STORE_DIR = Path("store/vector")

from core.supabase_document_manager import get_all_documents
from core.supabase_document_manager import is_duplicate_document_hash
from core.supabase_document_manager import save_uploaded_document_to_supabase
from core.supabase_document_manager import update_supabase_document_active_status



# 1. 업로드된 파일이 지원 가능한 문서 형식인지 확인한다.
def validate_file_type(file_name):
    file_extension = Path(file_name).suffix.replace(".", "").lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        return False, "올바르지 않은 문서 형식"

    return True, file_extension


# 2. 업로드된 파일 내용을 기준으로 SHA-256 해시값을 생성한다.
#먼저 file을 바이트형식으로 변환된것이 입력으로 와야한다.
def calculate_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


# 3.문서 metadata 파일을 읽어 문서 목록을 가져온다.
def load_document_metadata(metadata_path):
    return get_all_documents()
    
# 4.문서 metadata 목록을 JSON 파일로 저장한다.
def save_document_metadata(metadata_path, documents):
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)

# 5.기존 문서 metadata에서 같은 파일 해시가 있는지 확인한다.
def is_duplicate_file_hash(existing_documents, new_file_hash):
    for document_metadata in existing_documents:
        if document_metadata.get("file_hash") == new_file_hash:
            return True

    return False

# 6.업로드된 원본 파일을 지정한 저장 위치에 저장한다.
#경로를 추후에 내 실제 저장공간으로 바꾼다.
def save_original_file(originals_dir,document_id, file_name, file_bytes,):
    originals_dir.mkdir(parents=True, exist_ok=True)

    saved_file_name = f"{document_id}_{file_name}"
    saved_file_path = originals_dir / saved_file_name

    saved_file_path.write_bytes(file_bytes)

    return saved_file_path


# 7.저장된 문서에 대한 metadata 항목을 생성한다.
def create_document_metadata(
    document_id,
    file_name,
    category,
    file_type,
    file_path,
    file_hash,
):
    return {
        "document_id": document_id,
        "file_name": file_name,
        "category": category,
        "file_type": file_type,
        "file_path": str(file_path),
        "file_hash": file_hash,
        "status": "completed",
        "status_message": "RAG 문서 저장 완료",
        "is_active": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

# 8.문서 metadata 목록에 새 문서 metadata를 추가한다.
def append_document_metadata(metadata_path, document_metadata):
    documents = load_document_metadata(metadata_path)
    documents.append(document_metadata)
    save_document_metadata(metadata_path, documents)

    return documents

# 9.문서 metadata에서 특정 문서의 처리 상태와 메시지를 변경한다.
def update_document_status(metadata_path, document_id, status, status_message):
    documents = load_document_metadata(metadata_path)

    for document in documents:
        if document.get("document_id") == document_id:
            document["status"] = status
            document["status_message"] = status_message
            break

    save_document_metadata(metadata_path, documents)

    return documents

from pypdf import PdfReader


# 9.저장된 원본 문서에서 텍스트를 추출한다.
#벡터화시키기 위한 준비과정 1
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


# Supabase에서 내려받은 원본 파일 bytes에서 텍스트를 추출한다.
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



from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.chroma_vector_store import get_chroma_vector_store


# 10.추출된 문서 텍스트를 청크화하고 Chroma Cloud에 저장한다.
def save_rag_document(extracted_text, document_metadata, vector_store_dir):
    # RAG 저장에 사용할 텍스트가 비어 있는지 확인한다.
    if not extracted_text.strip():
        raise ValueError("저장할 문서 텍스트가 비어 있습니다.")

    # 긴 문서를 검색 가능한 청크 단위로 나눈다.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    # 각 청크에 원본 문서 정보를 metadata로 연결한다.
    document = Document(
        page_content=extracted_text,
        metadata={
            "document_id": document_metadata["document_id"],
            "file_name": document_metadata["file_name"],
            "category": document_metadata["category"],
            "file_path": document_metadata["file_path"],
            "is_active": document_metadata["is_active"],
        },
    )

    # LangChain splitter를 사용해 Document를 청크 Document 목록으로 변환한다.
    split_documents = text_splitter.split_documents([document])

    # Chroma Cloud에 문서 청크를 저장한다.
    vector_store = get_chroma_vector_store()
    vector_ids = [
        f"{document_metadata['document_id']}_{index}"
        for index, document in enumerate(split_documents)
    ]
    vector_store.add_documents(documents=split_documents, ids=vector_ids)

    return len(split_documents)



"""
해당 문서의 전체 파이프라인을 담당하는 함수
"""

# 업로드된 문서를 검증, 저장, metadata 기록, RAG 저장까지 순서대로 처리한다.
def process_uploaded_document(uploaded_file, category, progress_callback=None):

    # 처리 단계가 바뀔 때 외부 UI에 상태를 전달한다.
    def notify(step_name, status, message=""):
        if progress_callback:
            progress_callback(step_name, status, message)

    # 업로드된 파일의 이름과 내용을 가져온다.
    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue()

    # 업로드된 파일이 지원 가능한 문서 형식인지 확인한다.
    notify("문서 형태 파악", "진행중")
    is_valid_file_type, file_type_or_message = validate_file_type(file_name)

    if not is_valid_file_type:
        notify("문서 형태 파악", "실패", file_type_or_message)
        return {
            "success": False,
            "status": "failed",
            "message": file_type_or_message,
        }

    file_type = file_type_or_message
    notify("문서 형태 파악", "완료")

    # 업로드된 파일 내용으로 중복 확인용 해시를 생성한다.
    notify("문서 중복 확인", "진행중")
    file_hash = calculate_file_hash(file_bytes)

    # Supabase documents table에서 중복 문서가 있는지 확인한다.
    if is_duplicate_document_hash(file_hash):
        notify("문서 중복 확인", "실패", "이미 등록된 문서입니다.")
        return {
            "success": False,
            "status": "duplicated",
            "message": "이미 등록된 문서입니다.",
        }

    notify("문서 중복 확인", "완료")

    # 업로드된 원본 파일을 Supabase 원본 저장소에 저장한다.
    notify("문서 원문 저장", "진행중")
    try:
        document_metadata = save_uploaded_document_to_supabase(
            file_name=file_name,
            file_type=file_type,
            category=category,
            file_hash=file_hash,
            file_bytes=file_bytes,
            content_type=getattr(uploaded_file, "type", None),
        )
    except Exception as error:
        notify("문서 원문 저장", "실패", str(error))
        return {
            "success": False,
            "status": "failed",
            "message": f"문서 원문 저장 중 오류가 발생했습니다: {error}",
        }

    notify("문서 원문 저장", "완료")

    # 문서 metadata 저장이 완료되었음을 표시한다.
    notify("상태 업데이트", "진행중")
    notify("상태 업데이트", "완료")

    return {
        "success": True,
        "status": "completed",
        "message": "문서 업로드가 완료되었습니다. RAG 문서 업데이트를 실행하면 AI 검색에 반영됩니다.",
        "document_id": document_metadata["document_id"],
        "file_name": file_name,
        "chunk_count": 0,
    }

# 문서 활성상태 변경
def update_document_active_status(metadata_path, document_id, is_active):
    return update_supabase_document_active_status(document_id, is_active)
