import os

from supabase import create_client


# Supabase 접속에 필요한 환경변수가 설정되어 있는지 확인한다.
def is_supabase_configured():
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


# 환경변수를 사용해 Supabase client를 생성한다.
def get_supabase_client():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase 환경변수가 설정되지 않았습니다.")

    return create_client(supabase_url, supabase_key)
