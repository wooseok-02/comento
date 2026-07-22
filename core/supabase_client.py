import os

import streamlit as st
from supabase import create_client


# Supabase 접속에 필요한 환경변수가 설정되어 있는지 확인한다.
def is_supabase_configured():
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


# 환경변수를 사용해 Supabase client를 생성한다.
@st.cache_resource
def get_supabase_client():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase 환경변수가 설정되지 않았습니다.")

    return create_client(supabase_url, supabase_key)


# Supabase Storage 파일을 내려받을 수 있는 signed URL을 생성한다.
def create_storage_signed_url(
    storage_bucket,
    storage_path,
    expires_in=3600,
    missing_path_message="Supabase Storage 경로가 없습니다.",
):
    if not storage_path:
        return {
            "success": False,
            "url": None,
            "message": missing_path_message,
        }

    try:
        supabase = get_supabase_client()
        response = (
            supabase.storage.from_(storage_bucket)
            .create_signed_url(storage_path, expires_in)
        )
        signed_url = response.get("signedURL") or response.get("signedUrl")

        return {
            "success": bool(signed_url),
            "url": signed_url,
            "message": None if signed_url else "다운로드 URL을 생성하지 못했습니다.",
        }

    except Exception as error:
        return {
            "success": False,
            "url": None,
            "message": str(error),
        }
