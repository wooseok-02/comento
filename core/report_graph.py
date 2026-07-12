from typing import TypedDict, List, Dict, Any, Optional

from core.chroma_vector_store import get_chroma_vector_store
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

REPORT_MODEL_NAME = "gpt-4o-mini"
INTERNAL_SEARCH_K = 5
WEB_SEARCH_K = 5


class ReportState(TypedDict, total=False):
    title: str
    topic: str
    purpose: str
    owner_type: str

    is_valid: bool
    error_message: Optional[str]

    internal_documents: List[Any]
    internal_sources: List[Dict[str, Any]]

    web_results: List[Dict[str, Any]]
    web_sources: List[Dict[str, Any]]

    merged_context: str
    sources: List[Dict[str, Any]]

    report_content: str


# 보고서 생성에 필요한 입력값이 올바른지 검증한다.
def validate_input_node(state):
    title = state.get("title", "").strip()
    topic = state.get("topic", "").strip()
    purpose = state.get("purpose", "").strip()
    owner_type = state.get("owner_type", "").strip()

    if not title:
        return {
            "is_valid": False,
            "error_message": "보고서 제목을 입력하세요.",
        }

    if not topic:
        return {
            "is_valid": False,
            "error_message": "보고서 주제를 입력하세요.",
        }

    if not purpose:
        return {
            "is_valid": False,
            "error_message": "보고서 목적을 입력하세요.",
        }

    if owner_type not in ["personal", "teams"]:
        return {
            "is_valid": False,
            "error_message": "저장 위치를 선택하세요.",
        }

    return {
        "is_valid": True,
        "error_message": None,
        "title": title,
        "topic": topic,
        "purpose": purpose,
        "owner_type": owner_type,
    }

# 입력값 검증 결과에 따라 다음 실행 흐름을 결정한다.
#공통 엣지 연결 함수
def route_after_validation(state):
    if state.get("is_valid"):
        return "continue"

    return "end"

# 보고서 주제와 목적을 기준으로 내부 RAG 문서를 검색한다.
def retrieve_internal_documents_node(state):
    query = f"{state.get('topic', '')}\n{state.get('purpose', '')}".strip()

    if not query:
        return {
            "internal_documents": [],
            "internal_sources": [],
        }

    try:
        vector_store = get_chroma_vector_store()

        documents = vector_store.similarity_search(
            query,
            k=INTERNAL_SEARCH_K,
        )

        internal_sources = []

        for document in documents:
            metadata = document.metadata or {}

            internal_sources.append(
                {
                    "source_type": "internal_document",
                    "title": metadata.get("title") or metadata.get("file_name", "알 수 없는 문서"),
                    "file_name": metadata.get("file_name"),
                    "file_path": metadata.get("file_path"),
                    "category": metadata.get("category"),
                }
            )

        return {
            "internal_documents": documents,
            "internal_sources": internal_sources,
        }

    except Exception as error:
        return {
            "internal_documents": [],
            "internal_sources": [],
            "internal_search_error": str(error),
        }

# 보고서 주제와 목적을 기준으로 웹 검색 결과를 가져온다.
def search_web_node(state):
    query = f"{state.get('topic', '')}\n{state.get('purpose', '')}".strip()

    if not query:
        return {
            "web_results": [],
            "web_sources": [],
        }

    try:
        search_tool = TavilySearch(
            max_results=WEB_SEARCH_K,
        )

        search_response = search_tool.invoke(query)

        if isinstance(search_response, dict):
            search_results = search_response.get("results", [])
        else:
            search_results = search_response

        web_results = []
        web_sources = []

        for result in search_results:
            title = result.get("title", "제목 없음")
            url = result.get("url")
            content = result.get("content", "")

            web_result = {
                "title": title,
                "url": url,
                "snippet": content,
            }

            web_results.append(web_result)

            web_sources.append(
                {
                    "source_type": "web",
                    "title": title,
                    "url": url,
                    "snippet": content,
                }
            )

        return {
            "web_results": web_results,
            "web_sources": web_sources,
        }

    except Exception as error:
        return {
            "web_results": [],
            "web_sources": [],
            "web_search_error": str(error),
        }

# 내부 RAG 문서와 웹 검색 결과를 보고서 생성용 context와 출처 목록으로 합친다.
def merge_context_node(state):
    internal_documents = state.get("internal_documents", [])
    internal_sources = state.get("internal_sources", [])

    web_results = state.get("web_results", [])
    web_sources = state.get("web_sources", [])

    context_parts = []

    if internal_documents:
        context_parts.append("[내부 문서 참고자료]")

        for index, document in enumerate(internal_documents, start=1):
            metadata = document.metadata or {}
            title = metadata.get("title") or metadata.get("file_name", "알 수 없는 문서")
            content = document.page_content

            context_parts.append(
                f"{index}. 제목: {title}\n내용: {content}"
            )

    if web_results:
        context_parts.append("[웹 검색 참고자료]")

        for index, result in enumerate(web_results, start=1):
            title = result.get("title", "제목 없음")
            url = result.get("url", "")
            snippet = result.get("snippet", "")

            context_parts.append(
                f"{index}. 제목: {title}\nURL: {url}\n내용: {snippet}"
            )

    merged_context = "\n\n".join(context_parts)

    sources = internal_sources + web_sources

    return {
        "merged_context": merged_context,
        "sources": sources,
    }

# 통합 참고자료를 기반으로 markdown 형식의 보고서를 생성한다.
def generate_report_node(state):
    title = state.get("title", "")
    topic = state.get("topic", "")
    purpose = state.get("purpose", "")
    merged_context = state.get("merged_context", "")

    if not merged_context:
        merged_context = "참고자료가 충분하지 않습니다. 사용자가 입력한 주제와 목적을 기준으로 일반적인 보고서 초안을 작성하세요."

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
당신은 NGO/국제개발/정책 문서를 작성하는 AI 보고서 작성 전문가입니다.
사용자가 입력한 보고서 제목, 주제, 목적과 제공된 참고자료를 바탕으로 한국어 markdown 보고서를 작성하세요.

작성 규칙:
- 보고서는 전문적이고 명확한 문체로 작성하세요.
- 참고자료에 없는 내용을 단정하지 마세요.
- 웹 검색 결과와 내부 문서 내용을 구분해서 종합하세요.
- 출처 URL이나 파일명은 본문에 과하게 반복하지 마세요.
- markdown 형식을 사용하세요.
- 보고서 분량은 기본 분량으로 작성하세요.

보고서 구조:
# 보고서 제목

## 1. 요약
## 2. 배경
## 3. 주요 내용
## 4. 시사점
## 5. 실행 제안
## 6. 참고자료 요약
""",
            ),
            (
                "human",
                """
보고서 제목:
{title}

보고서 주제:
{topic}

보고서 목적:
{purpose}

참고자료:
{merged_context}
""",
            ),
        ]
    )

    llm = ChatOpenAI(
        model=REPORT_MODEL_NAME,
        temperature=0.2,
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "title": title,
            "topic": topic,
            "purpose": purpose,
            "merged_context": merged_context,
        }
    )

    return {
        "report_content": response.content,
    }

# 보고서 생성 LangGraph workflow를 구성한다.
def build_report_graph():
    graph_builder = StateGraph(ReportState)

    graph_builder.add_node("validate_input", validate_input_node)
    graph_builder.add_node("retrieve_internal_documents", retrieve_internal_documents_node)
    graph_builder.add_node("search_web", search_web_node)
    graph_builder.add_node("merge_context", merge_context_node)
    graph_builder.add_node("generate_report", generate_report_node)

    # 그래프 시작 노드를 지정
    graph_builder.set_entry_point("validate_input")

    # validate_input 실행 후 어디로 갈지 조건부로 결정
    graph_builder.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "continue": "retrieve_internal_documents",
            "end": END,
        },
    )

    graph_builder.add_edge("retrieve_internal_documents", "search_web")
    graph_builder.add_edge("search_web", "merge_context")
    graph_builder.add_edge("merge_context", "generate_report")
    graph_builder.add_edge("generate_report", END)

    return graph_builder.compile()

# 보고서 생성을 실행하고 UI에서 사용할 미리보기 결과를 반환한다.
def generate_report_preview(title, topic, purpose, owner_type):
    initial_state = {
        "title": title,
        "topic": topic,
        "purpose": purpose,
        "owner_type": owner_type,
    }

    graph = build_report_graph()
    final_state = graph.invoke(initial_state)

    if not final_state.get("is_valid"):
        return {
            "success": False,
            "message": final_state.get("error_message", "입력값이 올바르지 않습니다."),
            "report": None,
        }

    if not final_state.get("report_content"):
        return {
            "success": False,
            "message": "보고서 생성 결과가 없습니다.",
            "report": None,
        }

    return {
        "success": True,
        "message": "보고서가 생성되었습니다.",
        "report": {
            "title": final_state.get("title"),
            "topic": final_state.get("topic"),
            "purpose": final_state.get("purpose"),
            "owner_type": final_state.get("owner_type"),
            "content": final_state.get("report_content"),
            "sources": final_state.get("sources", []),
        },
    }
