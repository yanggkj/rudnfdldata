import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="모바일 티켓 박스오피스",
    page_icon="🎟️",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 2번 구현: 화이트 배경 + 실물 모바일 티켓(Ticket) UI/UX CSS
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 메인 배경: 눈이 편안한 소프트 화이트 */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* 상단 타이틀 바 */
    .ticket-header {
        text-align: center;
        padding: 10px 0 25px 0;
        border-bottom: 2px dashed #cbd5e1;
        margin-bottom: 30px;
    }
    .ticket-header-title {
        color: #0f172a;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -1px;
        margin: 0;
    }
    .ticket-header-sub {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 6px;
    }

    /* 🎟️ 실물 티켓 카드 스타일 디자인 */
    .ticket-box {
        position: relative;
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        overflow: hidden;
    }
    
    /* 마우스 호버 시 티켓이 살짝 들리는 인터랙션 */
    .ticket-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
        border-color: #e50914;
    }

    /* 티켓 좌우 절취 홈 (펀칭 홀) 효과 */
    .ticket-box::before, .ticket-box::after {
        content: "";
        position: absolute;
        top: 50%;
        width: 20px;
        height: 20px;
        background-color: #f8fafc; /* 배경색과 동일하게 맞춰 홈처럼 보임 */
        border: 2px solid #e2e8f0;
        border-radius: 50%;
        transform: translateY(-50%);
    }
    .ticket-box::before { left: -12px; }
    .ticket-box::after { right: -12px; }

    /* 티켓 순위 뱃지 */
    .ticket-rank-badge {
        display: inline-block;
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 12px;
    }
    .ticket-rank-badge.top1 {
        background-color: #e50914; /* 1위는 넷플릭스 레드 로 포인트 */
    }

    /* 티켓 내부 텍스트 스타일 */
    .ticket-movie-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 6px;
    }
    .ticket-meta {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 16px;
    }

    /* 티켓 지표(수치) 영역 */
    .ticket-data-grid {
        display: flex;
        gap: 15px;
        background-color: #f1f5f9;
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 4px solid #e50914;
    }
    .ticket-data-item {
        flex: 1;
    }
    .ticket-data-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 700;
    }
    .ticket-data-value {
        font-size: 1.1rem;
        color: #0f172a;
        font-weight: 800;
    }

    /* 티켓 하단 바코드 연출 디자인 */
    .ticket-stub-barcode {
        margin-top: 18px;
        padding-top: 12px;
        border-top: 2px dashed #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #94a3b8;
        font-family: monospace;
        font-size: 0.8rem;
        letter-spacing: 2px;
    }

    /* 탭 메뉴 스타일 정돈 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 700;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #e50914 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 1. KOBIS API 데이터 불러오기 (캐싱)
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
# 2. TMDB API 영화 상세 정보 불러오기
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
# 3. 영화 상세 정보 모달
# -------------------------------------------------------------
@st.dialog("🎬 모바일 티켓 상세보기")
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
# 헤더 레이아웃
# -------------------------------------------------------------
st.markdown("""
    <div class="ticket-header">
        <h1 class="ticket-header-title">🎟️ DAILY MOVIE TICKET</h1>
        <div class="ticket-header-sub">실물 모바일 티켓 형태로 확인하는 실시간 일별 박스오피스</div>
    </div>
""", unsafe_allow_html=True)

# Secrets 키 확인
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

# 데이터 불러오기
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
    # 탭 구성
    # -------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎟️ 모바일 티켓 랭킹", 
        "📊 관객수 TOP 5 차트", 
        "📋 전체 순위표", 
        "🔍 상세 검색"
    ])

    # TAB 1: 실물 모바일 티켓 형태 카드 리스트
    with tab1:
        st.markdown(f"##### 📢 **{display_dt_str}** 관객 발권 현황")
        st.write("")

        # TOP 3 영화를 3열의 티켓 카드로 배치
        top3_cols = st.columns(3)
        for i in range(min(3, len(df))):
            item = df.iloc[i]
            rank_badge_class = "top1" if item['rank'] == 1 else ""
            
            with top3_cols[i]:
                st.markdown(f"""
                    <div class="ticket-box">
                        <span class="ticket-rank-badge {rank_badge_class}">NO. {item['rank']} TICKET</span>
                        <div class="ticket-movie-title">{item['movieNm']}</div>
                        <div class="ticket-meta">개봉일: {item['openDt']} | 변동: {item['순위변동']}</div>
                        <div class="ticket-data-grid">
                            <div class="ticket-data-item">
                                <div class="ticket-data-label">어제 관객</div>
                                <div class="ticket-data-value">{item['audiCnt']:,}명</div>
                            </div>
                            <div class="ticket-data-item">
                                <div class="ticket-data-label">누적 관객</div>
                                <div class="ticket-data-value">{item['audiAcc']:,}명</div>
                            </div>
                        </div>
                        <div class="ticket-stub-barcode">
                            <span>||||||| | |||| | |||||</span>
                            <span>#2026-BOX-{item['rank']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🎟️ '{item['movieNm']}' 티켓 정보", key=f"tkt_btn_{i}"):
                    show_movie_dialog(item["movieNm"])

        st.divider()

        # 4위~10위 영화는 가로 스태킹 티켓 형태로 표시
        st.markdown("##### 🎟️ NEXT RANKINGS")
        for i in range(3, min(10, len(df))):
            item = df.iloc[i]
            col_tkt, col_act = st.columns([4, 1])
            with col_tkt:
                st.markdown(f"""
                    <div class="ticket-box" style="padding: 16px 24px; margin-bottom: 10px;">
                        <span class="ticket-rank-badge">NO. {item['rank']}</span>
                        <strong style="font-size: 1.1rem; margin-left: 10px; color: #0f172a;">{item['movieNm']}</strong>
                        <span style="color: #64748b; font-size:0.85rem; margin-left: 15px;">개봉: {item['openDt']} | 관객수: <b>{item['audiCnt']:,}명</b> (누적 {item['audiAcc']:,}명)</span>
                    </div>
                """, unsafe_allow_html=True)
            with col_act:
                st.write("")
                if st.button(f"상세보기", key=f"tkt_btn_{i}"):
                    show_movie_dialog(item["movieNm"])

    # TAB 2: 차트
    with tab2:
        st.markdown("#### 📊 TOP 5 관객수 비교")
        top_5_df = df.head(5)
        st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", use_container_width=True)

    # TAB 3: 전체 순위표
    with tab3:
        st.markdown("#### 📋 전체 박스오피스 순위표")
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
        st.markdown("#### 🔍 영화 선택 상세 검색")
        selected_movie = st.selectbox(
            "줄거리 및 상세 정보를 확인할 영화를 고르세요:",
            options=df["movieNm"].tolist()
        )
        if st.button("🎬 선택한 영화 상세보기"):
            show_movie_dialog(selected_movie)
