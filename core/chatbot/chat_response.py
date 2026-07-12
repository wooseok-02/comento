# 질문을 받아서 내부 RAG 기반 답변 생성 모듈
"""파이프라인 구조 요약
question
↓
retriever
↓
context 생성
↓
prompt
↓
ChatOpenAI
↓
StrOutputParser
"""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

# LangChain FAISS 벡터 저장소 위치를 정의한다.
VECTOR_STORE_DIR = Path("store/vector")

# 챗봇 답변 생성에 사용할 모델명을 정의한다.
CHAT_MODEL_NAME = "gpt-4o-mini"

# 챗봇 답변 생성에 사용할 온도를 정의한다.
CHAT_TEMPERATURE = 0

# 내부 문서 기반 RAG 검색 방식을 정의한다.
RETRIEVAL_MODE = "internal_rag"

# 검색할 내부 문서 청크 개수를 정의한다.
RETRIEVAL_TOP_K = 4

# 검색 결과로 사용할 최대 거리 점수를 정의한다.
MAX_DISTANCE_SCORE = 1.0

# 관련 내부 문서가 없을 때 사용자에게 보여줄 답변을 정의한다.
NO_RELEVANT_DOCUMENT_ANSWER = (
    "등록된 내부 문서에서 질문과 관련된 근거를 찾지 못했습니다. "
    "질문을 더 구체적으로 입력하거나 관련 문서를 먼저 등록해 주세요."
)

# 답변 생성 중 오류가 발생했을 때 사용자에게 보여줄 답변을 정의한다.
DEFAULT_ERROR_ANSWER = "답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."


# 저장된 FAISS 벡터 DB를 불러온다.
def load_vector_store(vector_store_dir=VECTOR_STORE_DIR):
    index_file_path = vector_store_dir / "index.faiss"
    metadata_file_path = vector_store_dir / "index.pkl"

    if not index_file_path.exists() or not metadata_file_path.exists():
        raise FileNotFoundError("저장된 벡터 DB가 없습니다. RAG 문서 업데이트를 먼저 실행하세요.")

    embeddings = OpenAIEmbeddings()

    return FAISS.load_local(
        folder_path=str(vector_store_dir),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )


# 사용자 질문과 유사한 내부 문서 청크를 점수와 함께 검색한다.
def retrieve_documents_with_score(question, top_k=RETRIEVAL_TOP_K):
    vector_store = load_vector_store()

    return vector_store.similarity_search_with_score(
        query=question,
        k=top_k,
    )


# 거리 점수 기준을 통과한 문서만 반환한다.
def filter_documents_by_score(documents_with_score, max_distance_score=MAX_DISTANCE_SCORE):
    filtered_documents = []

    for document, distance_score in documents_with_score:
        if distance_score <= max_distance_score:
            filtered_documents.append(document)

    return filtered_documents


# 검색된 문서 청크를 LLM 프롬프트에 넣을 context 문자열로 변환한다.
def format_retrieved_documents(documents):
    if not documents:
        return "검색된 내부 문서가 없습니다."

    formatted_documents = []

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        file_name = metadata.get("file_name", "알 수 없는 문서")
        category = metadata.get("category", "미분류")
        page_content = document.page_content

        formatted_documents.append(
            f"[문서 {index}]\n"
            f"문서명: {file_name}\n"
            f"카테고리: {category}\n"
            f"내용:\n{page_content}"
        )

    return "\n\n".join(formatted_documents)


# 검색된 문서 metadata를 답변 출처 목록으로 변환한다.
def build_sources(documents):
    sources = []
    document_ids = set()

    for document in documents:
        metadata = document.metadata
        document_id = metadata.get("document_id")

        if document_id in document_ids:
            continue

        source = {
            "source_type": "document",
            "title": metadata.get("file_name", "알 수 없는 문서"),
            "document_id": document_id,
            "file_path": metadata.get("file_path"),
            "category": metadata.get("category"),
        }

        sources.append(source)
        document_ids.add(document_id)

    return sources


# 내부 문서 context를 기반으로 LLM 답변을 생성한다.
def generate_rag_answer(question, context):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "너는 내부 문서를 기반으로 답변하는 AI 챗봇이다. "
                "반드시 제공된 내부 문서 내용에 근거해서 답변한다. "
                "문서에 없는 내용은 추측하지 말고, 문서에서 확인할 수 없다고 답한다. "
                "답변은 한국어로 작성한다. "
                "답변은 반드시 '### 답변', '### 근거', '### 확인 필요' 세 섹션으로 작성한다. "
                "'### 답변'에는 핵심 답변을 먼저 작성한다. "
                "'### 근거'에는 내부 문서에서 확인한 근거를 bullet로 정리한다. "
                "'### 확인 필요'에는 문서에서 확인할 수 없는 내용이나 추가 확인이 필요한 점을 적는다.",
            ),
            (
                "human",
                "사용자 질문:\n{question}\n\n"
                "내부 문서 내용:\n{context}",
            ),
        ]
    )

    llm = ChatOpenAI(
        model=CHAT_MODEL_NAME,
        temperature=CHAT_TEMPERATURE,
    )

    output_parser = StrOutputParser()

    answer_chain = prompt | llm | output_parser

    return answer_chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )


# 챗봇 응답 반환 형식을 생성한다.
def create_chat_response_result(success, answer, sources=None, error_message=None):
    if sources is None:
        sources = []

    return {
        "success": success,
        "answer": answer,
        "sources": sources,
        "model_name": CHAT_MODEL_NAME,
        "retrieval_mode": RETRIEVAL_MODE,
        "error_message": error_message,
    }


# 사용자 질문을 받아 내부 RAG 기반 답변, 출처, 모델 정보를 반환한다.
def generate_chat_response(question):
    try:
        documents_with_score = retrieve_documents_with_score(question)
        documents = filter_documents_by_score(documents_with_score)

        if not documents:
            return create_chat_response_result(
                success=True,
                answer=NO_RELEVANT_DOCUMENT_ANSWER,
                sources=[],
            )

        context = format_retrieved_documents(documents)
        sources = build_sources(documents)

        answer = generate_rag_answer(
            question=question,
            context=context,
        )

        return create_chat_response_result(
            success=True,
            answer=answer,
            sources=sources,
        )

    except Exception as error:
        return create_chat_response_result(
            success=False,
            answer=DEFAULT_ERROR_ANSWER,
            sources=[],
            error_message=str(error),
        )
