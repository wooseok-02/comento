# Chroma Cloud Vector Store

# 목적
공통 문서를 RAG 검색에 사용할 수 있도록 문서 chunk와 embedding vector를 저장한다.

# collection
```text
worldvision_documents
```

# 저장 단위
Chroma에는 원본 문서 전체가 아니라 검색 가능한 chunk 단위 Document를 저장한다.

각 chunk는 다음 정보를 가진다.

```text
page_content: chunk 본문
metadata: 원본 문서 연결 정보
id: {document_id}_{chunk_index}
```

# metadata 구조

```json
{
  "document_id": "uuid",
  "file_name": "문서명.pdf",
  "category": "규정",
  "file_path": "supabase://uploaded-documents/documents/uuid/file.pdf",
  "storage_bucket": "uploaded-documents",
  "storage_path": "documents/uuid/file.pdf",
  "is_active": true
}
```

# RAG 업데이트 기준
Supabase documents table에서 아래 조건을 만족하는 문서만 Chroma에 저장한다.

```text
is_active = true
status = completed
```

# 재생성 정책
현재 버전에서는 RAG 업데이트 버튼을 누르면 Chroma collection을 비우고 활성 문서 기준으로 다시 생성한다.

이유:
- 비활성 문서를 검색 결과에서 확실히 제외할 수 있다.
- 중복 chunk 저장을 피할 수 있다.
- 초기 운영 단계에서 로직이 단순하고 추적이 쉽다.

# 검색 사용처
- AI 챗봇 내부 RAG 답변
- 보고서 생성 LangGraph 내부 문서 검색
