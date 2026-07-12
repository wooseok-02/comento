import os

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


DEFAULT_CHROMA_COLLECTION_NAME = "worldvision_documents"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


# Chroma collection 이름을 환경변수에서 가져온다.
def get_chroma_collection_name():
    return os.getenv("CHROMA_COLLECTION_NAME", DEFAULT_CHROMA_COLLECTION_NAME)


# OpenAI embedding 모델을 생성한다.
def get_embedding_function():
    return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))


# Chroma Cloud 연결에 필요한 환경변수가 있는지 확인한다.
def is_chroma_cloud_configured():
    return bool(
        os.getenv("CHROMA_API_KEY")
        and os.getenv("CHROMA_TENANT")
        and os.getenv("CHROMA_DATABASE")
    )


# Chroma Cloud client를 생성한다.
def get_chroma_client():
    if not is_chroma_cloud_configured():
        raise ValueError("Chroma Cloud 환경변수가 설정되지 않았습니다.")

    return chromadb.CloudClient()


# LangChain Chroma vector store를 생성한다.
def get_chroma_vector_store():
    return Chroma(
        client=get_chroma_client(),
        collection_name=get_chroma_collection_name(),
        embedding_function=get_embedding_function(),
    )


# Chroma collection을 비우고 새 vector store를 반환한다.
def reset_chroma_collection():
    client = get_chroma_client()
    collection_name = get_chroma_collection_name()

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_embedding_function(),
    )
