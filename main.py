import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="시네마 박스오피스 극장",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 극장 스크린 및 시독성 극대화 커스텀 CSS (이미지 스타일 반영)
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 배경: 어두운 극장 내부 및 상단 붉은 조명 효과 */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #3b0a0a 0%, #120303 50%, #050101 100%);
        color: #ffffff;
    }

    /* 메인 타이틀 */
    .cinema-header {
        text-align: center;
        padding: 10px 0;
        margin-bottom: 15px;
    }
    .cinema-title {
        color: #ff3333;
        font-size: 2.5rem;
        font-weight: 900;
        text-shadow: 0 0 15px rgba(255, 51, 51, 0.8), 2px 2px 4px #000;
        margin: 0;
    }
    .cinema-subtitle {
        color: #ffcccc;
        font-size: 1.1rem;
        font-weight: bold;
    }

    /* 🖼️ 이미지 스타일 반영: 붉은 커튼 + 밝은 영사 스크린 */
    .cinema-theater-frame {
        position: relative;
        background-color: #120303;
        border-left: 35px solid #7a0c0c;  /* 좌측 벨벳 커튼 연출 */
        border-right: 35px solid #7a0c0c; /* 우측 벨벳 커튼 연출 */
        border-top: 15px solid #4a0606;   /* 상단 커튼 프레임 */
        border-radius: 12px;
        padding: 30px 25px;
        box-shadow: 0 0 50px rgba(0,0,0,0.9), inset 0 0 30px rgba(0,0,0,0.8);
        margin-bottom: 25px;
    }

    /* 📺 실제 스크린 내부 (글자가 가장 잘 보이는 밝은 영사막 톤) */
    .screen-whiteboard {
        background-color: #f8f9fa !important; /* 밝은 회백색 스크린 */
        color: #111111 !important;            /* 선명한 짙은 글자 */
        border-radius: 8px;
        padding: 25px;
        box-shadow: 0 0 25px rgba(255, 255, 255, 0.6);
    }

    /* 밝은 스크린 내부 요소들의 글자색 고정 */
    .screen-whiteboard h1, .screen-whiteboard h2, .screen-whiteboard h3, 
    .screen-whiteboard h4, .screen-whiteboard p, .screen-whiteboard span,
    .screen-whiteboard label {
        color: #111111 !important;
    }

    /* 티켓 형태 카드 (선명하게 수정) */
    .ticket-card {
        background: #ffffff;
        border: 2px solid #e50914;
        border-left: 8px solid #e50914;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    }
    .ticket-card small {
        color: #555555 !important;
        font-weight: bold;
    }
    .ticket-card h2 {
        color: #b20710 !important;
        font-size: 1.8rem;
        font-weight: 800;
    }

    /* 탭 스타일 (눈에 잘 띄게 변경) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #2b0808;
        padding: 8px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        font-weight: bold;
        font-size: 1rem;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e50914 !important;
        color: #ffffff !important;
    }

    /* 데이터프레임 표 글자 또렷하게 */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 1. KOBIS API 데이터 가져오기 (캐싱 1시간)
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
        
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "알 수 없는 API 오류가 발생했습니다.")
            return None, f"API 오류: {error_message}"
            
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])
        
        if not daily_list:
            return None, "EMPTY_LIST"
            
        return daily_list, None
        
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 오류: {str(e)}"


# -------------------------------------------------------------
# 2. TMDB Open API로 영화 상세 정보 가져오기
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_movie_detail(movie_name):
    try:
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": "15d2ea6d0dc1d476efbca3eba2b9bbf3",
            "query": movie_name,
            "language": "ko-KR"
        }
        res = requests.get(search_url, params=params, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                movie_data = results[0]
                movie_id = movie_data.get("id")
                
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
        "release_date": "정보 없음"
    }


# -------------------------------------------------------------
# 3. 영화 상세 정보 팝업 모달
# -------------------------------------------------------------
@st.dialog("🎬 영화 상세 정보")
def show_movie_dialog(movie_name):
    st.markdown(f"### **{movie_name}**")
    
    with st.spinner("영화 정보를 불러오는 중입니다..."):
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
# 메인 화면 구성
# -------------------------------------------------------------
st.markdown("""
    <div class="cinema-header">
        <h1 class="cinema-title">🍿 CINEMA CINEMATIC THEATER 🍿</h1>
        <p class="cinema-subtitle">대형 스크린으로 관람하는 실시간 박스오피스</p>
    </div>
""", unsafe_allow_html=True)

# Secrets 검증
if "KOBIS_KEY" not in st.secrets:
    st.error("⚠️ 인증키가 설정되지 않았습니다. Streamlit Secrets에 `KOBIS_KEY`를 등록해 주세요.")
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 날짜 설정
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday = (now_kst - datetime.timedelta(days=1)).date()

col_date, col_empty = st.columns([1, 2])
with col_date:
    selected_date = st.date_input(
        "📅 조회할 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 자 데이터는 아직 집계 전이므로 어제 날짜까지 선택할 수 있습니다."
    )

target_dt_str = selected_date.strftime("%Y%m%d")
display_dt_str = selected_date.strftime("%Y년 %m월 %d일")

# API 데이터 불러오기
movie_list, error_msg = fetch_box_office_data(api_key, target_dt_str)

# -------------------------------------------------------------
# 🎭 커튼과 조명이 있는 극장 스크린 레이아웃
# -------------------------------------------------------------
st.markdown('<div class="cinema-theater-frame">', unsafe_allow_html=True)
st.markdown('<div class="screen-whiteboard">', unsafe_allow_html=True)

st.markdown(f"<h3 style='text-align:center; color:#111111;'>🎟️ <b>{display_dt_str}</b> 박스오피스 상영 스크린</h3>", unsafe_allow_html=True)

if error_msg == "EMPTY_LIST":
    st.warning("⚠️ **그날은 아직 집계 전입니다.** (선택하신 날짜의 박스오피스 데이터가 생성되지 않았습니다.)")
elif error_msg:
    st.error("❌ 데이터를 가져오는 데 실패했습니다.")
    st.info(f"💡 **확인 사항:** KOBIS API 키 설정 상태를 확인해 주세요.\n\n({error_msg})")
else:
    # 데이터 전처리
    df = pd.DataFrame(movie_list)
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
    df = df.sort_values("rank").reset_index(drop=True)

    # 순위 증감 화살표
    def format_rank_change(val):
        if val > 0:
            return f"🔴 +{val} ▲"
        elif val < 0:
            return f"🔵 {val} ▼"
        else:
            return "⚪ -"

    df["순위변동"] = df["rankInten"].apply(format_rank_change)

    # 스크린 내 슬라이딩 탭 메뉴
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 1위 영화 하이라이트", 
        "📊 관객수 TOP 5 차트", 
        "📋 전체 순위표", 
        "🔍 영화 상세 검색"
    ])

    # 탭 1: 1위 하이라이트
    with tab1:
        top_1 = df.iloc[0]
        st.markdown(f"<h2 style='color:#111111;'>🥇 1위: <b>{top_1['movieNm']}</b></h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#333333;'>개봉일: {top_1['openDt']} | 전날 대비 순위: {top_1['순위변동']}</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="ticket-card">
                    <small>어제 관객수</small>
                    <h2>{top_1['audiCnt']:,} 명</h2>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="ticket-card">
                    <small>누적 관객수</small>
                    <h2>{top_1['audiAcc']:,} 명</h2>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="ticket-card">
                    <small>상영 스크린수</small>
                    <h2>{top_1['scrnCnt']:,} 개</h2>
                </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        if st.button(f"🎬 '{top_1['movieNm']}' 상세 줄거리 보기", key="top1_btn"):
            show_movie_dialog(top_1["movieNm"])

    # 탭 2: TOP 5 차트
    with tab2:
        st.markdown("<h4 style='color:#111111;'>📊 관객수 TOP 5 영화 차트</h4>", unsafe_allow_html=True)
        top_5_df = df.head(5)
        st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", use_container_width=True)

    # 탭 3: 전체 순위표
    with tab3:
        st.markdown("<h4 style='color:#111111;'>📋 전체 박스오피스 순위 (TOP 10)</h4>", unsafe_allow_html=True)
        display_df = df[["rank", "순위변동", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
        display_df.columns = ["순위", "전날 대비", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

        st.dataframe(
            display_df.style.format({
                "관객수": "{:,}",
                "누적관객": "{:,}",
                "스크린수": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )

    # 탭 4: 상세 검색
    with tab4:
        st.markdown("<h4 style='color:#111111;'>🔍 영화별 상세 줄거리 & 정보</h4>", unsafe_allow_html=True)
        selected_movie = st.selectbox(
            "상세 정보를 확인할 영화를 고르세요:",
            options=df["movieNm"].tolist()
        )
        if st.button("🎬 선택한 영화 상세보기"):
            show_movie_dialog(selected_movie)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
