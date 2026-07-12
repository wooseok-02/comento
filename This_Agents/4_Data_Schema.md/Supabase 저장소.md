# Supabase Storage

## bucket
```text
generated-files
```

## 저장 경로
```text
reports/{file_name}
meeting_notes/{file_name}
```

## 저장 대상
- 보고서 markdown 파일
- 회의록 markdown 파일

# resources table

Supabase Database에 생성할 table이다.

```sql
create table resources (
  resource_id text primary key,
  owner_type text not null,
  resource_type text not null,
  source_type text not null,
  title text not null,
  file_name text not null,
  file_path text,
  storage_bucket text,
  storage_path text,
  source_document_id text,
  created_at timestamp with time zone default now()
);
```

# 컬럼 설명

## resource_id
자료 metadata의 고유 ID이다.
Python 코드에서 uuid 문자열로 생성한다.

## owner_type
자료 저장 범위이다.

허용값:
- personal
- teams

## resource_type
자료 유형이다.

허용값:
- meeting_note
- report
- file

현재 Supabase 전환 대상:
- meeting_note
- report

## source_type
자료 생성 출처이다.

허용값:
- generated_meeting_note
- generated_report
- common_document
- uploaded_file

현재 Supabase 전환 대상:
- generated_meeting_note
- generated_report

## title
자료관리 화면에 표시할 제목이다.

## file_name
Storage에 저장한 파일명이다.

예:
- 아동보호_정책_보고서_20260712_120000.md
- 주간회의_20260712_130000.md

## file_path
파일 위치를 표현하는 문자열이다.

Supabase 산출물은 다음 형식을 사용한다.
```text
supabase://generated-files/reports/file.md
```

## storage_bucket
Supabase Storage bucket 이름이다.

기본값:
```text
generated-files
```

## storage_path
Supabase Storage 내부 파일 경로이다.

예:
```text
reports/file.md
meeting_notes/file.md
```

## source_document_id
공통 문서에서 파생된 자료일 경우 원본 문서 ID를 저장한다.
보고서와 회의록 생성 산출물에서는 null로 둔다.

## created_at
자료 등록 시각이다.

# 자료관리 조회 기준

개인 자료 조회:
```sql
select * from resources
where owner_type = 'personal'
order by created_at desc;
```

Teams 자료 조회:
```sql
select * from resources
where owner_type = 'teams'
order by created_at desc;
```

보고서 필터:
```sql
select * from resources
where owner_type = 'personal'
and resource_type = 'report'
order by created_at desc;
```

회의록 필터:
```sql
select * from resources
where owner_type = 'personal'
and resource_type = 'meeting_note'
order by created_at desc;
```

# ERD

```text
resources
---------
resource_id PK
owner_type
resource_type
source_type
title
file_name
file_path
storage_bucket
storage_path
source_document_id
created_at
```

현재 버전에서는 단일 table로 자료관리 metadata를 관리한다.
향후 사용자 인증이 추가되면 users table과 owner_id 관계를 추가한다.
