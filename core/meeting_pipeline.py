from pathlib import Path
import tempfile

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI


MEETING_NOTE_MODEL_NAME = "gpt-4o-mini"
STT_MODEL_NAME = "whisper-1"
SUPPORTED_AUDIO_EXTENSIONS = ["mp3", "wav", "m4a"]
MAX_AUDIO_FILE_SIZE_BYTES = 25 * 1024 * 1024
MAX_AUDIO_FILE_SIZE_MB = 25


# 회의 생성에 필요한 입력값과 음성 파일 형식을 검증한다.
def validate_meeting_input(
    meeting_title,
    meeting_purpose,
    meeting_description,
    uploaded_audio_file,
    owner_type,
):
    if not meeting_title.strip():
        return {
            "success": False,
            "message": "회의 제목을 입력하세요.",
        }

    if not meeting_purpose.strip():
        return {
            "success": False,
            "message": "회의 목적을 입력하세요.",
        }

    if not meeting_description.strip():
        return {
            "success": False,
            "message": "회의 설명을 입력하세요.",
        }

    if uploaded_audio_file is None:
        return {
            "success": False,
            "message": "회의 음성 파일을 업로드하세요.",
        }

    if owner_type not in ["personal", "teams"]:
        return {
            "success": False,
            "message": "저장 위치를 선택하세요.",
        }

    file_extension = Path(uploaded_audio_file.name).suffix.replace(".", "").lower()

    if file_extension not in SUPPORTED_AUDIO_EXTENSIONS:
        return {
            "success": False,
            "message": "mp3, wav, m4a 형식의 음성 파일만 업로드할 수 있습니다.",
        }

    file_size = getattr(uploaded_audio_file, "size", None)

    if file_size is None:
        file_size = len(uploaded_audio_file.getbuffer())

    if file_size > MAX_AUDIO_FILE_SIZE_BYTES:
        return {
            "success": False,
            "message": f"회의 음성 파일은 {MAX_AUDIO_FILE_SIZE_MB}MB 이하만 업로드할 수 있습니다.",
        }

    return {
        "success": True,
        "message": "입력값 검증이 완료되었습니다.",
    }


# 업로드된 음성 파일을 STT 처리를 위한 임시 파일로 저장한다.
def save_uploaded_audio_to_temp(uploaded_audio_file):
    file_extension = Path(uploaded_audio_file.name).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_audio_file.getbuffer())
        return temp_file.name


# 임시 음성 파일을 OpenAI STT API로 텍스트 원문으로 변환한다.
def transcribe_audio(temp_audio_path):
    client = OpenAI()

    with open(temp_audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=STT_MODEL_NAME,
            file=audio_file,
        )

    return getattr(transcription, "text", "")


# transcript와 회의 정보를 기반으로 markdown 회의록을 생성한다.
def generate_meeting_note(
    meeting_title,
    meeting_purpose,
    meeting_description,
    transcript,
):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
당신은 회의 내용을 구조화해 실무용 회의록으로 정리하는 AI 문서 작성자입니다.
사용자가 제공한 회의 제목, 목적, 설명, transcript를 바탕으로 한국어 markdown 회의록을 작성하세요.

작성 규칙:
- transcript에 없는 내용을 단정하지 마세요.
- 불명확한 내용은 '확인 필요'로 표시하세요.
- 액션 아이템은 가능한 경우 할 일 중심으로 정리하세요.
- markdown 형식을 사용하세요.

회의록 구조:
# 회의 제목

## 1. 회의 요약
## 2. 주요 논의 내용
## 3. 결정 사항
## 4. 액션 아이템
## 5. 후속 확인 사항
""",
            ),
            (
                "human",
                """
회의 제목:
{meeting_title}

회의 목적:
{meeting_purpose}

회의 설명:
{meeting_description}

transcript:
{transcript}
""",
            ),
        ]
    )

    llm = ChatOpenAI(
        model=MEETING_NOTE_MODEL_NAME,
        temperature=0.2,
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "meeting_title": meeting_title,
            "meeting_purpose": meeting_purpose,
            "meeting_description": meeting_description,
            "transcript": transcript,
        }
    )

    return response.content


# STT 처리에 사용한 임시 음성 파일을 삭제한다.
def delete_temp_audio_file(temp_audio_path):
    if temp_audio_path and Path(temp_audio_path).exists():
        Path(temp_audio_path).unlink()


# 음성 파일을 transcript로 변환하고 회의록 미리보기 결과를 생성한다.
def generate_meeting_note_preview(
    meeting_title,
    meeting_purpose,
    meeting_description,
    uploaded_audio_file,
    owner_type,
    progress_callback=None,
):
    temp_audio_path = None

    try:
        if progress_callback:
            progress_callback("입력값을 검증하는 중입니다.")

        validation_result = validate_meeting_input(
            meeting_title=meeting_title,
            meeting_purpose=meeting_purpose,
            meeting_description=meeting_description,
            uploaded_audio_file=uploaded_audio_file,
            owner_type=owner_type,
        )

        if not validation_result["success"]:
            return {
                "success": False,
                "message": validation_result["message"],
                "meeting_note": None,
            }

        if progress_callback:
            progress_callback("음성 파일을 임시 저장하는 중입니다.")

        temp_audio_path = save_uploaded_audio_to_temp(uploaded_audio_file)

        if progress_callback:
            progress_callback("음성을 텍스트로 변환하는 중입니다.")

        transcript = transcribe_audio(temp_audio_path)

        if not transcript.strip():
            return {
                "success": False,
                "message": "음성에서 텍스트를 추출하지 못했습니다.",
                "meeting_note": None,
            }

        if progress_callback:
            progress_callback("회의록을 생성하는 중입니다.")

        meeting_note_content = generate_meeting_note(
            meeting_title=meeting_title.strip(),
            meeting_purpose=meeting_purpose.strip(),
            meeting_description=meeting_description.strip(),
            transcript=transcript,
        )

        if progress_callback:
            progress_callback("회의록 미리보기를 준비하는 중입니다.")

        return {
            "success": True,
            "message": "회의록이 생성되었습니다.",
            "meeting_note": {
                "meeting_title": meeting_title.strip(),
                "meeting_purpose": meeting_purpose.strip(),
                "meeting_description": meeting_description.strip(),
                "owner_type": owner_type,
                "transcript": transcript,
                "content": meeting_note_content,
            },
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"회의록 생성 중 오류가 발생했습니다: {str(error)}",
            "meeting_note": None,
        }

    finally:
        if progress_callback:
            progress_callback("임시 음성 파일을 정리하는 중입니다.")

        delete_temp_audio_file(temp_audio_path)
