import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="시네마 박스오피스 극장",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 극장(영화관) 분위기의 커스텀 CSS 스타일 적용
# -------------------------------------------------------------
# unsafe_allow_html=True 로 오타 수정 완료
st.markdown("""
    <style>
    /* 전체 배경을 아늑하고 어두운 영화관 스크린 느낌으로 설정 */
    .stApp {
        background-color: #0f0f14;
        color: #e0e0e0;
    }
    /* 타이틀 헤더 디자인 (붉은 네온 및 스크린 느낌) */
    .cinema-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(180deg, #2b0000 0%, #0f0f14 100%);
        border-bottom: 2px solid #e50914;
        margin-bottom: 25px;
        border-radius: 10px;
    }
    .cinema-title {
        color: #e50914;
        font-size: 2.3rem;
        font-weight: 800;
        text-shadow: 0 0 10px rgba(229, 9, 20, 0.7);
        margin: 0;
    }
    .cinema-subtitle {
        color: #aaaaaa;
        font-size: 1rem;
        margin-top: 5px;
    }
    /* 티켓 형태의 지표 카드 스타일 */
    .ticket-card {
        background: linear-gradient(135deg, #1f1f2e 0%, #161622 100%);
        border: 1px solid #33334d;
        border-left: 5px solid #e50914;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    /* 버튼 스타일 */
    .stButton > button {
        background-color: #e50914;
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #b20710;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 1. KOBIS API 박스오피스 데이터 호출 (캐싱 1시간)
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, target_date):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, f"서버 응답 에러 (상태 코드: {response.status_code})"
        
        data = response.json()
        
        # 인증키 오류 등 faultInfo 상자가 온 경우
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "알 수 없는 API 오류가 발생했습니다.")
            return None, f"API 오류: {error_message}"
            
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])
        
        # 영화 목록이 비어있는 경우
        if not daily_list:
            return None, "EMPTY_LIST"
            
        return daily_list, None
        
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 오류: {str(e)}"


# -------------------------------------------------------------
# 2. TMDB Open API를 이용해 영화 상세 정보 가져오기
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_movie_detail(movie_name):
    try:
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": "15d2ea6d0dc1d476efbca3eba2b9bbf3", # 샘플 TMDB 키
            "query": movie_name,
            "language": "ko-KR"
        }
        res = requests.get(search_url, params=params, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                movie_data = results[0]
                movie_id = movie_data.get("id")
                
                # 연령가 정보 조회
                release_url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates"
                rel_res = requests.get(release_url, params={"api_key": params["api_key"]})
                age_rating = "정보 없음"
                
                if rel_res.status_code == 200:
                    rel_data = rel_res.json().get("results", [])
                    for r in rel_data:
                        if r.get("iso_3166_1") == "KR":
                            for dates in r.get("release_dates", []):
                                if dates.get("certification"):
                                    age_rating = dates.get("certification")
                                    break
                
                poster_path = movie_data.get("poster_path")
                poster_url = f"https://image.tmdb.org/t5/p/w500{poster_path}" if poster_path else None
                
                return {
                    "overview": movie_data.get("overview") or "줄거리 정보가 제공되지 않는 영화입니다.",
                    "rating": movie_data.get("vote_average", 0.0),
                    "poster_url": poster_url,
                    "age_rating": age_rating,
                    "release_date": movie_data.get("release_date", "정보 없음")
                }
    except Exception:
        pass
    
    return {
        "overview": "영화 상세 정보를 불러올 수 없습니다.",
        "rating": 0.0,
        "poster_url": None,
        "age_rating": "정보 없음",
        "release_date": "
