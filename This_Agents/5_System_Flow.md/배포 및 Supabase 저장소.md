# 배포 및 외부 저장소 시스템 흐름

## 전체 구조

```text
사용자
→ Streamlit Community Cloud 앱
→ Supabase Database
→ Supabase Storage
→ Chroma Cloud
→ OpenAI / Tavily API
```

# Streamlit Community Cloud 역할

Streamlit Community Cloud는 앱 실행 환경이다.

담당:
- app.py 실행
- UI 렌더링
- Supabase API 호출
- Chroma Cloud API 호출
- OpenAI API 호출
- Tavily 웹 검색 호출

주의:
- Streamlit Cloud 내부 파일 시스템은 영구 저장소로 보장하지 않는다.
- 따라서 운영 데이터는 Supabase와 Chroma Cloud에 저장한다.

# Supabase 역할

Supabase는 서비스 데이터와 파일 원본 저장소이다.

담당:
- 문서 원본 파일 저장
- 문서 metadata 저장
- 자료관리 metadata 저장
- 챗봇 대화방 저장
- 챗봇 메시지 저장
- 보고서/회의록 markdown 파일 저장
- 다운로드 signed URL 생성

# Chroma Cloud 역할

Chroma Cloud는 RAG 검색 저장소이다.

담당:
- 문서 chunk 저장
- embedding vector 저장
- chunk metadata 저장
- similarity search 수행

# 문서 업로드 흐름

```text
문서 업로드
→ 파일 형식 검증
→ 파일 hash 생성
→ Supabase documents table에서 중복 확인
→ Supabase Storage uploaded-documents 업로드
→ Supabase documents table insert
→ 업로드 완료
```

# RAG 업데이트 흐름

```text
RAG 문서 업데이트 클릭
→ Supabase documents table에서 active/completed 문서 조회
→ Supabase Storage에서 원본 파일 다운로드
→ 텍스트 추출
→ chunk 분할
→ Chroma Cloud collection 초기화
→ Chroma Cloud에 chunk documents 저장
→ 업데이트 완료
```

# AI 챗봇 답변 흐름

```text
사용자 질문 입력
→ Supabase chat_messages에 user message 저장
→ Chroma Cloud similarity_search_with_score 실행
→ 검색 결과를 context로 변환
→ ChatOpenAI 답변 생성
→ 출처 metadata 생성
→ Supabase chat_messages에 assistant message 저장
→ 화면 표시
```

# 보고서 생성 흐름

```text
보고서 입력값 제출
→ LangGraph validate_input
→ Chroma Cloud 내부 문서 검색
→ Tavily 웹 검색
→ 내부 문서와 웹 검색 결과 병합
→ ChatOpenAI 보고서 생성
→ 사용자가 저장 클릭
→ Supabase Storage generated-files/reports 업로드
→ Supabase resources table insert
```

# 회의록 저장 흐름

```text
음성 파일 업로드
→ STT
→ 회의록 markdown 생성
→ 사용자가 편집
→ 사용자가 저장 클릭
→ Supabase Storage generated-files/meeting_notes 업로드
→ Supabase resources table insert
```

# 자료관리 조회 흐름

```text
자료관리 페이지 진입
→ owner_type 선택
→ resource_type 필터 선택
→ Supabase resources table 조회
→ 최신순 정렬
→ 화면 표시
```

# 다운로드 흐름

```text
다운로드 클릭
→ metadata의 storage_bucket/storage_path 확인
→ Supabase Storage signed URL 생성
→ Streamlit link_button 표시
→ 사용자가 파일 다운로드
```

# 환경변수 흐름

로컬:
```text
.env
→ load_dotenv()
→ os.environ
```

Streamlit Community Cloud:
```text
App secrets
→ st.secrets
→ app.py에서 os.environ으로 복사
```

필수 secrets:
- OPENAI_API_KEY
- TAVILY_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_STORAGE_BUCKET
- SUPABASE_DOCUMENT_BUCKET
- CHROMA_API_KEY
- CHROMA_TENANT
- CHROMA_DATABASE
- CHROMA_COLLECTION_NAME

# 배포 체크리스트

1. Supabase project 생성
2. Supabase Storage bucket 생성
3. Supabase SQL Editor에서 table 생성
4. Chroma Cloud database 생성
5. Chroma Cloud API key 발급
6. Chroma collection 이름 결정
7. Streamlit Community Cloud App secrets 등록
8. GitHub repository에 코드 반영
9. Streamlit Community Cloud 재배포
10. 문서 업로드 확인
11. RAG 문서 업데이트 확인
12. 챗봇 답변 확인
13. 자료관리 다운로드 확인
