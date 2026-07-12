# 배포 및 Supabase 저장소 시스템 흐름

## 전체 구조

```text
사용자
→ Hugging Face Spaces Streamlit 앱
→ OpenAI / Tavily API
→ Supabase Database
→ Supabase Storage
```

# Hugging Face Spaces 역할

Hugging Face Spaces는 Streamlit 앱 실행 환경이다.

담당:
- app.py 실행
- UI 렌더링
- OpenAI API 호출
- Tavily 웹 검색 호출
- Supabase API 호출

주의:
- Space 내부 파일 시스템은 영구 저장소로 보장하지 않는다.
- 따라서 생성 산출물은 Supabase에 저장한다.

# Supabase 역할

Supabase는 생성 산출물 저장소이다.

담당:
- 보고서 markdown 파일 저장
- 회의록 markdown 파일 저장
- 자료관리 metadata 저장
- 자료관리 목록 조회
- 다운로드 URL 생성

# 저장 흐름: 보고서

```text
보고서 생성
→ 사용자가 보고서 저장 클릭
→ core/report_storage.py
→ markdown content 생성
→ core/supabase_resource_manager.py
→ Supabase Storage generated-files/reports/ 업로드
→ Supabase resources table insert
→ 저장 성공 응답
```

# 저장 흐름: 회의록

```text
회의록 생성
→ 사용자가 회의록 편집
→ 사용자가 회의록 저장 클릭
→ core/meeting_storage.py
→ markdown content 생성
→ core/supabase_resource_manager.py
→ Supabase Storage generated-files/meeting_notes/ 업로드
→ Supabase resources table insert
→ 저장 성공 응답
```

# 자료관리 조회 흐름

```text
자료관리 페이지 진입
→ UI/pages/resource_list.py
→ 로컬 resources.json 조회
→ Supabase resources table 조회
→ 두 목록 병합
→ 최신순 정렬
→ 화면 표시
```

로컬 자료:
- 공통 문서에서 개인 자료로 저장한 파일

Supabase 자료:
- 생성된 보고서
- 생성된 회의록

# 다운로드 흐름

## 로컬 파일 다운로드

```text
자료 metadata에 storage_path 없음
→ file_path를 로컬 파일 경로로 판단
→ read_document_file_for_download 호출
→ st.download_button 표시
```

## Supabase 파일 다운로드

```text
자료 metadata에 storage_path 있음
→ Supabase Storage signed URL 생성
→ st.link_button으로 다운로드 링크 표시
```

# 환경변수 흐름

로컬:
```text
.env
→ load_dotenv()
→ os.environ
```

Hugging Face Spaces:
```text
Repository secrets
→ os.environ
```

필수 secrets:
- OPENAI_API_KEY
- TAVILY_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY

선택 secrets:
- SUPABASE_STORAGE_BUCKET

# 현재 유지하는 로컬 저장소

아래 기능은 현재 버전에서 로컬 파일 기반을 유지한다.

- 공통 문서 업로드
- 공통 문서 metadata
- FAISS vector store
- AI 챗봇 대화방
- AI 챗봇 메시지

이유:
- 오늘 배포 범위에서 전체 저장소 이전은 작업량이 크다.
- 학습 효과가 큰 생성 산출물 저장 흐름부터 클라우드화한다.

# 향후 운영 구조

운영 환경에서는 다음 구조로 확장한다.

```text
문서 원본 파일 → Supabase Storage 또는 S3
문서 metadata → Supabase DB
자료관리 metadata → Supabase DB
채팅방/메시지 → Supabase DB
vector store → pgvector 또는 managed vector DB
생성 산출물 → Supabase Storage 또는 S3
```

# Hugging Face Spaces 배포 체크리스트

1. GitHub 또는 Hugging Face repository에 코드 업로드
2. requirements.txt 확인
3. Space SDK를 Streamlit으로 선택
4. app.py를 진입점으로 설정
5. Repository secrets 등록
6. Supabase resources table 생성
7. Supabase generated-files bucket 생성
8. Space build 완료 확인
9. 배포 URL 접속 확인
