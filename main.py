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
    /* 버튼 및 대화상자 스타일 */
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
""", unsafe_unsafe_html=True if hasattr(st, "markdown") else False)


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
# 2. TMDB Open API를 이용해 영화 상세 정보(줄거리, 포스터 등) 가져오기
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_movie_detail(movie_name):
    """
    공개된 TMDB 검색 API를 사용해 영화 정보(줄거리, 연령가 등)를 받아옵니다.
    """
    try:
        # TMDB 공용 검색 API 엔드포인트
        search_url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": "15d2ea6d0dc1d476efbca3eba2b9bbf3", # 공용 TMDB 샘플 키
            "query": movie_name,
            "language": "ko-KR"
        }
        res = requests.get(search_url, params=params, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                movie_data = results[0]
                movie_id = movie_data.get("id")
                
                # 연령가(관람등급) 정보 조회를 위한 추가 API
                release_url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates"
                rel_res = requests.get(release_url, params={"api_key": params["api_key"]})
                age_rating = "정보 없음"
                
                if rel_res.status_code == 200:
                    rel_data = rel_res.json().get("results", [])
                    for r in rel_data:
                        if r.get("iso_3166_1") == "KR": # 한국 관람등급 찾기
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
        "release_date": "정보 없음"
    }


# -------------------------------------------------------------
# 3. 영화 상세 정보 모달 창 (Dialog)
# -------------------------------------------------------------
@st.dialog("🎬 영화 상세 정보")
def show_movie_dialog(movie_name):
    st.markdown(f"### **{movie_name}**")
    
    with st.spinner("영화 상세 정보를 불러오는 중입니다..."):
        info = fetch_movie_detail(movie_name)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if info["poster_url"]:
            st.image(info["poster_url"], use_container_width=True)
        else:
            st.info("🖼️ 포스터 없음")
    
    with col2:
        st.write(f"⭐ **TMDB 평점:** {info['rating']} / 10")
        st.write(f"🔞 **관람 등급:** {info['age_rating']}")
        st.write(f"📅 **개봉일:** {info['release_date']}")
    
    st.subheader("📖 줄거리")
    st.write(info["overview"])


# -------------------------------------------------------------
# 메인 UI 구성
# -------------------------------------------------------------

# 헤더 타이틀
st.markdown("""
    <div class="cinema-header">
        <h1 class="cinema-title">🍿 CINEMA BOX OFFICE 🍿</h1>
        <p class="cinema-subtitle">극장 스크린으로 확인하는 실시간 일별 박스오피스</p>
    </div>
""", unsafe_allow_html=True)

# Secrets 키 검증
if "KOBIS_KEY" not in st.secrets:
    st.error("⚠️ 인증키가 설정되지 않았습니다. Streamlit Secrets에 `KOBIS_KEY`를 등록해 주세요.")
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 한국 시간(KST) 기준 날짜 계산
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday = (now_kst - datetime.timedelta(days=1)).date()

# 달력(st.date_input)으로 날짜 선택 (최대 어제까지 선택 가능)
col_date, col_empty = st.columns([1, 2])
with col_date:
    selected_date = st.date_input(
        "📅 조회할 날짜를 선택하세요",
        value=yesterday,
        max_value=yesterday,
        help="오늘 자 데이터는 아직 집계 전이므로 어제 날짜까지 선택할 수 있습니다."
    )

target_dt_str = selected_date.strftime("%Y%m%d")
display_dt_str = selected_date.strftime("%Y년 %m월 %d일")

st.markdown(f"##### 🎟️ **{display_dt_str}** 상영 결과")

# 데이터 불러오기
movie_list, error_msg = fetch_box_office_data(api_key, target_dt_str)

# 데이터가 비어있거나 에러가 발생한 경우 안내
if error_msg == "EMPTY_LIST":
    st.warning("⚠️ **그날은 아직 집계 전입니다.** (선택하신 날짜의 박스오피스 데이터가 생성되지 않았습니다.)")
elif error_msg:
    st.error("❌ 데이터를 가져오는 데 실패했습니다.")
    st.info(f"💡 **확인 사항:** KOBIS API 키 설정 상태 및 하루 호출 제한수를 확인해 주세요.\n\n(오류 메시지: {error_msg})")
else:
    # -------------------------------------------------------------
    # 데이터 전처리 및 순위 변동(rankInten) 화살표 처리
    # -------------------------------------------------------------
    df = pd.DataFrame(movie_list)
    
    # 숫자형 변환
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
    df = df.sort_values("rank").reset_index(drop=True)

    # 순위 증감(rankInten) 텍스트 및 빨간색/파란색 화살표 포맷팅
    def format_rank_change(val):
        if val > 0:
            return f"🔴 +{val} ▲"  # 상승 (빨간 위 화살표)
        elif val < 0:
            return f"🔵 {val} ▼"   # 하강 (파란 아래 화살표)
        else:
            return "⚪ -"        # 변동 없음

    df["순위변동"] = df["rankInten"].apply(format_rank_change)

    # -------------------------------------------------------------
    # 1. 1위 영화 하이라이트 (티켓 전광판 느낌)
    # -------------------------------------------------------------
    top_1 = df.iloc[0]
    st.markdown("---")
    
    st.markdown(f"### 🏆 오늘의 1위 영화: **{top_1['movieNm']}**")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
            <div class="ticket-card">
                <small style="color:#aaa;">일일 관객수</small>
                <h2 style="color:#e50914; margin:0;">{top_1['audiCnt']:,} 명</h2>
            </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
            <div class="ticket-card">
                <small style="color:#aaa;">누적 관객수</small>
                <h2 style="color:#ffffff; margin:0;">{top_1['audiAcc']:,} 명</h2>
            </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
            <div class="ticket-card">
                <small style="color:#aaa;">상영 스크린수</small>
                <h2 style="color:#ffffff; margin:0;">{top_1['scrnCnt']:,} 개</h2>
            </div>
        """, unsafe_allow_html=True)

    # 1위 영화 바로 상세 정보 보는 버튼
    if st.button(f"🔍 '{top_1['movieNm']}' 상세보기 및 줄거리", key="top1_btn"):
        show_movie_dialog(top_1["movieNm"])

    st.markdown("---")

    # -------------------------------------------------------------
    # 2. 관객수 상위 5편 막대그래프
    # -------------------------------------------------------------
    st.subheader("📊 관객수 TOP 5 차트")
    top_5_df = df.head(5)
    st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------
    # 3. 박스오피스 전체 순위 표 및 영화 상세 정보 조회 기능
    # -------------------------------------------------------------
    st.subheader("📋 박스오피스 순위표 (영화 클릭 시 줄거리 보기)")

    # 표 화면 출력을 위한 컬럼 재구성 및 이름 변경
    display_df = df[["rank", "순위변동", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "전날 대비", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

    # 표 출력
    st.dataframe(
        display_df.style.format({
            "관객수": "{:,}",
            "누적관객": "{:,}",
            "스크린수": "{:,}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # 영화 상세 정보를 모달 창으로 조회할 수 있는 셀렉트박스
    st.markdown("##### 💡 관심 있는 영화를 선택하여 상세보기")
    selected_movie = st.selectbox(
        "줄거리 및 상세 정보를 확인할 영화를 고르세요:",
        options=df["movieNm"].tolist()
    )
    
    if st.button("🎬 선택한 영화 상세보기"):
        show_movie_dialog(selected_movie)
