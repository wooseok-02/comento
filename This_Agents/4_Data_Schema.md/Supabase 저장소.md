# Supabase Storage

## bucket
```text
uploaded-documents
generated-files
```

## uploaded-documents 저장 경로
```text
documents/{document_id}/{file_name}
```

## generated-files 저장 경로
```text
reports/{file_name}
meeting_notes/{file_name}
files/{file_name}
```

# documents table

공통 문서 metadata를 저장한다.

```sql
create table documents (
  document_id text primary key,
  file_name text not null,
  category text not null,
  file_type text not null,
  file_hash text not null unique,
  file_path text,
  storage_bucket text not null,
  storage_path text not null,
  status text not null default 'completed',
  status_message text,
  is_active boolean not null default true,
  created_at timestamp with time zone default now()
);
```

# resources table

개인/Teams 자료 metadata를 저장한다.

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

# chat_rooms table

AI 챗봇 대화방 metadata를 저장한다.

```sql
create table chat_rooms (
  chat_room_id text primary key,
  title text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);
```

# chat_messages table

AI 챗봇 대화 메시지를 저장한다.

```sql
create table chat_messages (
  message_id text primary key,
  chat_room_id text not null references chat_rooms(chat_room_id) on delete cascade,
  role text not null,
  content text not null,
  sources jsonb default '[]'::jsonb,
  model_name text,
  retrieval_mode text,
  created_at timestamp with time zone default now()
);
```

# 주요 컬럼 설명

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

## source_type
자료 생성 출처이다.

허용값:
- generated_meeting_note
- generated_report
- common_document
- uploaded_file

## storage_bucket
파일이 저장된 Supabase Storage bucket 이름이다.

## storage_path
Supabase Storage 내부 파일 경로이다.

## source_document_id
공통 문서에서 파생된 자료일 경우 원본 document_id를 저장한다.

# ERD

```text
documents
---------
document_id PK
file_name
category
file_type
file_hash
file_path
storage_bucket
storage_path
status
status_message
is_active
created_at

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

chat_rooms
----------
chat_room_id PK
title
created_at
updated_at

chat_messages
-------------
message_id PK
chat_room_id FK
role
content
sources
model_name
retrieval_mode
created_at
```
