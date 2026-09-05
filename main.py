import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정 (모던한 다크 모드 레이아웃)
st.set_page_config(
    page_title="일별 박스오피스 대시보드",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 깔끔하고 모던한 UI 커스텀 스타일
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 메인 배경 및 가독성 좋은 폰트 설정 */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* 상단 타이틀 영역 */
    .header-container {
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .header-title {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
    }
    .header-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 5px;
    }

    /* 카드 형태의 지표 스타일 */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }

    /* 모던 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e293b;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
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
        
        # faultInfo 예외 처리
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
                
                # 관람 등급 가져오기
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
# 메인 헤더 레이아웃
# -------------------------------------------------------------
st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🎬 Daily Box Office Dashboard</h1>
        <p class="header-subtitle">영화진흥위원회(KOBIS) 데이터 기반의 일별 박스오피스 분석</p>
    </div>
""", unsafe_allow_html=True)

# Secrets 키 확인
if "KOBIS_KEY" not in st.secrets:
    st.error("⚠️ 인증키가 설정되지 않았습니다. Streamlit Secrets에 `KOBIS_KEY`를 등록해 주세요.")
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 날짜 계산 (한국 시간 기준어제까지 선택 가능)
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday = (now_kst - datetime.timedelta(days=1)).date()

# 컨트롤 패널 (날짜 선택)
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

st.markdown(f"##### 📊 **{display_dt_str}** 박스오피스 결과")

# API 호출
movie_list, error_msg = fetch_box_office_data(api_key, target_dt_str)

# 데이터 예외 및 집계 전 처리
if error_msg == "EMPTY_LIST":
    st.warning("⚠️ **그날은 아직 집계 전입니다.** (선택하신 날짜의 박스오피스 데이터가 생성되지 않았습니다.)")
elif error_msg:
    st.error("❌ 데이터를 가져오는 데 실패했습니다.")
    st.info(f"💡 **확인 사항:** KOBIS API 키 설정 상태 및 호출 한도를 확인해 주세요.\n\n({error_msg})")
else:
    # 데이터 전처리
    df = pd.DataFrame(movie_list)
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
    df = df.sort_values("rank").reset_index(drop=True)

    # 순위 증감 화살표 표시
    def format_rank_change(val):
        if val > 0:
            return f"🔴 +{val} ▲"
        elif val < 0:
            return f"🔵 {val} ▼"
        else:
            return "⚪ -"

    df["순위변동"] = df["rankInten"].apply(format_rank_change)

    # -------------------------------------------------------------
    # 깔끔한 탭 넘김 레이아웃
    # -------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 1위 영화 하이라이트", 
        "📊 관객수 TOP 5 차트", 
        "📋 전체 순위표", 
        "🔍 영화 상세 검색"
    ])

    # 탭 1: 1위 하이라이트
    with tab1:
        top_1 = df.iloc[0]
        st.markdown(f"### 🥇 1위 영화: **{top_1['movieNm']}**")
        st.caption(f"개봉일: {top_1['openDt']} | 전날 대비 순위: {top_1['순위변동']}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">어제 관객수</div>
                    <div class="metric-value">{top_1['audiCnt']:,} 명</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">누적 관객수</div>
                    <div class="metric-value" style="color:#f8fafc;">{top_1['audiAcc']:,} 명</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">상영 스크린수</div>
                    <div class="metric-value" style="color:#f8fafc;">{top_1['scrnCnt']:,} 개</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        if st.button(f"🎬 '{top_1['movieNm']}' 줄거리 및 상세보기"):
            show_movie_dialog(top_1["movieNm"])

    # 탭 2: TOP 5 차트
    with tab2:
        st.markdown("#### 📊 관객수 TOP 5 영화")
        top_5_df = df.head(5)
        st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", use_container_width=True)

    # 탭 3: 전체 순위표
    with tab3:
        st.markdown("#### 📋 전체 박스오피스 순위 (TOP 10)")
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
        st.markdown("#### 🔍 영화 선택 상세 검색")
        selected_movie = st.selectbox(
            "줄거리 및 상세 정보를 확인할 영화를 고르세요:",
            options=df["movieNm"].tolist()
        )
        if st.button("🎬 선택한 영화 상세보기"):
            show_movie_dialog(selected_movie)
