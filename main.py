import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="NETFLIX LIGHT - 박스오피스",
    page_icon="🍿",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 넷플릭스 스타일 라이트 모드 (화이트 배경 + 넷플릭스 레드)
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 메인 배경: 눈이 편안한 밝은 화이트/일렉트릭 백그라운드 */
    .stApp {
        background-color: #ffffff;
        color: #141414;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 넷플릭스 헤더 바 */
    .netflix-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0 20px 0;
        border-bottom: 2px solid #f2f2f2;
        margin-bottom: 25px;
    }
    .netflix-logo {
        color: #E50914;
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: -1.5px;
        margin: 0;
    }
    .netflix-badge {
        background-color: #E50914;
        color: #ffffff;
        padding: 4px 12px;
        font-size: 0.85rem;
        font-weight: 700;
        border-radius: 4px;
        text-transform: uppercase;
    }

    /* 넷플릭스 스타일 메인 히어로 배너 (화이트 모드 전용) */
    .hero-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }
    .hero-title-badge {
        color: #E50914;
        font-weight: 800;
        font-size: 0.9rem;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .hero-title {
        color: #111111;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .hero-sub {
        color: #666666;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }

    /* 지표 카드 (메트릭) */
    .net-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #E50914;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        text-align: left;
    }
    .net-card-label {
        color: #718096;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .net-card-value {
        color: #1a202c;
        font-size: 1.6rem;
        font-weight: 800;
        margin-top: 4px;
    }

    /* 탭 메뉴 (넷플릭스 레드 포인트) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #f1f5f9;
        padding: 6px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 700;
        border-radius: 6px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E50914 !important;
        color: #ffffff !important;
    }

    /* 테이블 스타일 모던화 */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 1. KOBIS API 박스오피스 데이터 가져오기
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
# 2. TMDB Open API 영화 상세 정보 가져오기
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
# 3. 영화 상세 정보 다이얼로그 (모달)
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
# 헤더 영역
# -------------------------------------------------------------
st.markdown("""
    <div class="netflix-header">
        <h1 class="netflix-logo">NETFLIX <span style="font-size:1.2rem; font-weight:400; color:#333;">BOXOFFICE</span></h1>
        <span class="netflix-badge">TOP 10 TODAY</span>
    </div>
""", unsafe_allow_html=True)

# Secrets 인증키 확인
if "KOBIS_KEY" not in st.secrets:
    st.error("⚠️ 인증키가 설정되지 않았습니다. Streamlit Secrets에 `KOBIS_KEY`를 등록해 주세요.")
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 날짜 계산
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday = (now_kst - datetime.timedelta(days=1)).date()

col_date, col_space = st.columns([1, 3])
with col_date:
    selected_date = st.date_input(
        "📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 자 데이터는 아직 집계 전이므로 어제 날짜까지 선택 가능합니다."
    )

target_dt_str = selected_date.strftime("%Y%m%d")
display_dt_str = selected_date.strftime("%Y년 %m월 %d일")

# 데이터 호출
movie_list, error_msg = fetch_box_office_data(api_key, target_dt_str)

if error_msg == "EMPTY_LIST":
    st.warning("⚠️ **그날은 아직 집계 전입니다.** (선택하신 날짜의 박스오피스 데이터가 생성되지 않았습니다.)")
elif error_msg:
    st.error("❌ 데이터를 가져오는 데 실패했습니다.")
    st.info(f"💡 **확인 사항:** KOBIS API 키 설정 상태를 확인해 주세요.\n\n({error_msg})")
else:
    # 데이터 가공
    df = pd.DataFrame(movie_list)
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
    df = df.sort_values("rank").reset_index(drop=True)

    def format_rank_change(val):
        if val > 0:
            return f"🔴 +{val} ▲"
        elif val < 0:
            return f"🔵 {val} ▼"
        else:
            return "⚪ -"

    df["순위변동"] = df["rankInten"].apply(format_rank_change)

    # -------------------------------------------------------------
    # 탭 구성 (라이트 넷플릭스)
    # -------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 오늘 일등 추천", 
        "📈 관객수 랭킹 차트", 
        "📋 전체 랭킹 리스트", 
        "🔍 상세 검색"
    ])

    # TAB 1: 넷플릭스 메인 히어로 스타일 (1위 영화)
    with tab1:
        top_1 = df.iloc[0]
        
        st.markdown(f"""
            <div class="hero-container">
                <div class="hero-title-badge">#1 TODAY'S FEATURED</div>
                <div class="hero-title">{top_1['movieNm']}</div>
                <div class="hero-sub">개봉일: {top_1['openDt']} &nbsp;|&nbsp; 순위 변동: {top_1['순위변동']}</div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="net-card">
                    <div class="net-card-label">일일 관객수</div>
                    <div class="net-card-value">{top_1['audiCnt']:,} 명</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="net-card">
                    <div class="net-card-label">누적 관객수</div>
                    <div class="net-card-value">{top_1['audiAcc']:,} 명</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="net-card">
                    <div class="net-card-label">스크린수</div>
                    <div class="net-card-value">{top_1['scrnCnt']:,} 개</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button(f"▶ '{top_1['movieNm']}' 상세 정보 열기", key="hero_btn"):
            show_movie_dialog(top_1["movieNm"])

    # TAB 2: 차트
    with tab2:
        st.markdown("<h4 style='color:#111;'>📈 TOP 5 관객수 차트</h4>", unsafe_allow_html=True)
        top_5_df = df.head(5)
        st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", use_container_width=True)

    # TAB 3: 전체 순위표
    with tab3:
        st.markdown("<h4 style='color:#111;'>📋 오늘 박스오피스 순위표</h4>", unsafe_allow_html=True)
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

    # TAB 4: 상세 검색
    with tab4:
        st.markdown("<h4 style='color:#111;'>🔍 영화 줄거리 검색</h4>", unsafe_allow_html=True)
        selected_movie = st.selectbox(
            "목록에서 영화를 선택하세요:",
            options=df["movieNm"].tolist()
        )
        if st.button("🎬 선택한 영화 상세보기"):
            show_movie_dialog(selected_movie)
