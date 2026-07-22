import streamlit as st

from core.meeting_pipeline import generate_meeting_note_preview
from core.meeting_pipeline import MAX_AUDIO_FILE_SIZE_BYTES, MAX_AUDIO_FILE_SIZE_MB
from core.meeting_storage import save_generated_meeting_note


# 회의 생성 페이지에서 사용할 세션 상태를 초기화한다.
def initialize_meeting_create_state():
    if "generated_meeting_note_preview" not in st.session_state:
        st.session_state["generated_meeting_note_preview"] = None

    if "meeting_note_editor" not in st.session_state:
        st.session_state["meeting_note_editor"] = ""


# 회의록 생성 과정의 단계별 상태 메시지를 화면에 표시한다.
def render_progress_message(message):
    st.session_state["meeting_create_progress"].append(message)


# 생성된 transcript 원문을 접힌 영역으로 표시한다.
def render_transcript_area(transcript):
    with st.expander("원문 보기"):
        st.write(transcript)


# 생성된 회의록 markdown을 사용자가 직접 수정할 수 있게 표시한다.
def render_meeting_note_editor():
    return st.text_area(
        "회의록 편집",
        key="meeting_note_editor",
        height=600,
    )


# 업로드된 음성 파일 크기가 STT 처리 한도 안에 있는지 확인한다.
def is_audio_file_size_valid(uploaded_audio_file):
    if uploaded_audio_file is None:
        return True

    file_size = getattr(uploaded_audio_file, "size", None)

    if file_size is None:
        file_size = len(uploaded_audio_file.getbuffer())

    return file_size <= MAX_AUDIO_FILE_SIZE_BYTES


# 회의 생성 페이지의 전체 화면을 구성한다.
def render_meeting_create_page():
    initialize_meeting_create_state()

    st.title("회의 생성")

    meeting_title = st.text_input(
        "회의 제목",
        placeholder="회의 제목을 입력하세요.",
    )

    meeting_purpose = st.text_input(
        "회의 목적",
        placeholder="회의 목적을 입력하세요.",
    )

    meeting_description = st.text_area(
        "회의 설명",
        placeholder="회의 배경, 참석자, 주요 안건 등을 입력하세요.",
    )

    uploaded_audio_file = st.file_uploader(
        "회의 음성 파일",
        type=["mp3", "wav", "m4a"],
        help=f"OpenAI Whisper API 제한에 따라 {MAX_AUDIO_FILE_SIZE_MB}MB 이하 파일만 처리할 수 있습니다.",
    )

    st.caption(f"원본 음성 파일은 회의록 생성 후 저장하지 않습니다. {MAX_AUDIO_FILE_SIZE_MB}MB 이하 파일만 업로드하세요.")

    is_valid_audio_size = is_audio_file_size_valid(uploaded_audio_file)

    if not is_valid_audio_size:
        st.warning(f"회의 음성 파일은 {MAX_AUDIO_FILE_SIZE_MB}MB 이하만 업로드할 수 있습니다.")

    owner_label = st.radio(
        "저장 위치",
        ["개인", "Teams"],
        horizontal=True,
    )

    owner_type = "personal" if owner_label == "개인" else "teams"

    generate_button = st.button(
        "회의록 생성",
        type="primary",
        use_container_width=True,
        disabled=not is_valid_audio_size,
    )

    if generate_button:
        st.session_state["meeting_create_progress"] = []

        with st.spinner("회의록을 생성하는 중입니다."):
            result = generate_meeting_note_preview(
                meeting_title=meeting_title,
                meeting_purpose=meeting_purpose,
                meeting_description=meeting_description,
                uploaded_audio_file=uploaded_audio_file,
                owner_type=owner_type,
                progress_callback=render_progress_message,
            )

        if st.session_state["meeting_create_progress"]:
            with st.expander("처리 단계", expanded=True):
                for message in st.session_state["meeting_create_progress"]:
                    st.write(f"- {message}")

        if result["success"]:
            st.session_state["generated_meeting_note_preview"] = result["meeting_note"]
            st.session_state["meeting_note_editor"] = result["meeting_note"]["content"]
            st.success(result["message"])
        else:
            st.session_state["generated_meeting_note_preview"] = None
            st.session_state["meeting_note_editor"] = ""
            st.warning(result["message"])

    meeting_note_preview = st.session_state.get("generated_meeting_note_preview")

    if meeting_note_preview:
        st.divider()

        st.subheader("회의록 편집")
        edited_content = render_meeting_note_editor()

        render_transcript_area(meeting_note_preview.get("transcript", ""))

        save_button = st.button(
            "회의록 저장",
            use_container_width=True,
        )

        if save_button:
            meeting_note_to_save = {
                **meeting_note_preview,
                "content": edited_content,
            }

            save_result = save_generated_meeting_note(meeting_note_to_save)

            if save_result["success"]:
                st.success(save_result["message"])
            else:
                st.warning(save_result["message"])
