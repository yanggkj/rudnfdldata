import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="박스오피스 3D 포디움 & 티켓",
    page_icon="🏆",
    layout="wide"
)

# -------------------------------------------------------------
# 🎨 1번(영사기 빔 & 글로우) + 3번(플로팅 애니메이션) 포인트 적용 CSS
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* 메인 바탕화면: 눈이 편안한 스톤 화이트 라이트 모드 */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* -------------------------------------------------------------
       ✨ 3번 구현: 둥둥 떠다니는 Floating Pulse 애니메이션 Keyframes
       ------------------------------------------------------------- */
    @keyframes floatIcon {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(3deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }

    /* -------------------------------------------------------------
       ✨ 1번 구현: 영사기 라이트 빔(Light Beam) 애니메이션 Keyframes
       ------------------------------------------------------------- */
    @keyframes projectorBeam {
        0% { opacity: 0.35; transform: rotate(-10deg) scaleY(1); }
        50% { opacity: 0.65; transform: rotate(-10deg) scaleY(1.08); }
        100% { opacity: 0.35; transform: rotate(-10deg) scaleY(1); }
    }

    /* 상단 타이틀 헤더 */
    .podium-header {
        text-align: center;
        padding: 10px 0 25px 0;
        border-bottom: 2px dashed #cbd5e1;
        margin-bottom: 35px;
    }
    .podium-title {
        color: #0f172a;
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: -1px;
        margin: 0;
    }
    .podium-sub {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 6px;
    }

    /* 포디움 단상 및 실물 티켓 카드 공통 스타일 */
    .podium-card {
        position: relative;
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
    }

    /* 마우스 호버 시 티켓이 위로 떠오르는 효과 */
    .podium-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.12);
        border-color: #e50914;
    }

    /* 🎟️ 티켓 좌우 절취 펀칭 홀 */
    .podium-card::before, .podium-card::after {
        content: "";
        position: absolute;
        top: 50%;
        width: 18px;
        height: 18px;
        background-color: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 50%;
        transform: translateY(-50%);
        z-index: 5;
    }
    .podium-card::before { left: -11px; }
    .podium-card::after { right: -11px; }

    /* 🥇 1위 포디움: 1번(황금빛 글로우 & 영사기 빔) 적용 */
    .podium-1st {
        flex: 1.15;
        min-height: 390px;
        border: 3px solid #f59e0b;
        background: linear-gradient(180deg, #ffffff 0%, #fffbebe6 100%);
        z-index: 2;
        /* ✨ 1번 포인트: 은은하게 사방으로 번지는 황금빛 네온 글로우 */
        box-shadow: 0 0 25px rgba(245, 158, 11, 0.35), 0 10px 20px rgba(0,0,0,0.05);
    }
    
    /* ✨ 1번 포인트: 1위 카드 우상단 영사기 광선 빔(Light Beam) */
    .podium-1st::before {
        content: "";
        position: absolute;
        top: -60px;
        right: -30px;
        width: 140px;
        height: 250px;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.45) 0%, rgba(255, 255, 255, 0) 70%);
        transform: rotate(-10deg);
        pointer-events: none;
        z-index: 1;
        animation: projectorBeam 3s infinite ease-in-out;
    }

    /* ✨ 3번 포인트: Floating 애니메이션 적용 아이콘 */
    .floating-icon {
        display: inline-block;
        font-size: 2.2rem;
        margin-bottom: 2px;
        animation: floatIcon 2.5s infinite ease-in-out;
    }

    /* 🥈 2위 포디움 */
    .podium-2nd {
        flex: 1;
        min-height: 330px;
        border: 2px solid #94a3b8;
    }
    .podium-2nd .rank-tag {
        background-color: #64748b;
        color: #ffffff;
    }

    /* 🥉 3위 포디움 */
    .podium-3rd {
        flex: 1;
        min-height: 300px;
        border: 2px solid #b45309;
    }
    .podium-3rd .rank-tag {
        background-color: #b45309;
        color: #ffffff;
    }

    /* 랭킹 태그 뱃지 */
    .rank-tag {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 800;
        margin-bottom: 10px;
        position: relative;
        z-index: 2;
    }

    /* 영화 제목 및 정보 */
    .movie-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 6px;
        word-break: keep-all;
        position: relative;
        z-index: 2;
    }
    .movie-meta {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 16px;
        position: relative;
        z-index: 2;
    }

    /* 지표 박스 */
    .data-pill {
        background-color: #f1f5f9;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 12px;
        position: relative;
        z-index: 2;
    }
    .data-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 700;
    }
    .data-val {
        font-size: 1.15rem;
        color: #0f172a;
        font-weight: 800;
    }

    /* 바코드 절취선 */
    .ticket-barcode {
        border-top: 2px dashed #cbd5e1;
        padding-top: 10px;
        margin-top: 10px;
        font-family: monospace;
        letter-spacing: 2px;
        color: #94a3b8;
        font-size: 0.75rem;
        position: relative;
        z-index: 2;
    }

    /* 일반 랭킹 티켓 카드 (4위~10위) */
    .normal-ticket {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        transition: border-color 0.2s ease;
    }
    .normal-ticket:hover {
        border-color: #e50914;
    }

    /* 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #e50914 !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 1. KOBIS API 데이터 불러오기
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
# 2. TMDB Open API 영화 상세 정보
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
@st.dialog("🎬 상세 영화 티켓 정보")
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
# 메인 타이틀
# -------------------------------------------------------------
st.markdown("""
    <div class="podium-header">
        <h1 class="podium-title">🏆 3D PODIUM & TICKET BOX</h1>
        <div class="podium-sub">영사기 라이트와 3D 포디움으로 보는 실시간 박스오피스</div>
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

movie_list, error_msg = fetch_box_office_data(api_key, target_dt_str)

if error_msg == "EMPTY_LIST":
    st.warning("⚠️ **그날은 아직 집계 전입니다.** (선택하신 날짜의 박스오피스 데이터가 생성되지 않았습니다.)")
elif error_msg:
    st.error("❌ 데이터를 가져오는 데 실패했습니다.")
    st.info(f"💡 **확인 사항:** KOBIS API 키 설정 상태를 확인해 주세요.\n\n({error_msg})")
else:
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
    # 탭 메뉴
    # -------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 TOP 3 포디움 시상대", 
        "📊 관객수 TOP 5 차트", 
        "📋 전체 순위표", 
        "🔍 상세 검색"
    ])

    # TAB 1: 3D 입체 포디움 + 1번(빔/글로우) + 3번(플로팅 애니메이션)
    with tab1:
        st.markdown(f"##### 📢 **{display_dt_str}** 박스오피스 TOP 3 영예의 순간")
        st.write("")

        if len(df) >= 3:
            m1 = df.iloc[0] # 1위
            m2 = df.iloc[1] # 2위
            m3 = df.iloc[2] # 3위

            col_p2, col_p1, col_p3 = st.columns([1, 1.15, 1])

            # 🥈 2위 포디움 (🍿 팝콘 플로팅 아이콘)
            with col_p2:
                st.markdown(f"""
                    <div class="podium-card podium-2nd">
                        <div class="floating-icon">🍿</div>
                        <span class="rank-tag">2ND PLACE</span>
                        <div class="movie-title">{m2['movieNm']}</div>
                        <div class="movie-meta">개봉일 {m2['openDt']} | {m2['순위변동']}</div>
                        <div class="data-pill">
                            <div class="data-label">어제 관객수</div>
                            <div class="data-val">{m2['audiCnt']:,} 명</div>
                        </div>
                        <div class="data-pill">
                            <div class="data-label">누적 관객수</div>
                            <div class="data-val">{m2['audiAcc']:,} 명</div>
                        </div>
                        <div class="ticket-barcode">||||||| | ||| #NO-2</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🎟️ 2위 상세 정보", key="pod_btn_2"):
                    show_movie_dialog(m2["movieNm"])

            # 🥇 1위 포디움 (👑 왕관 플로팅 + ✨ 영사기 라이트 빔 + 황금 네온 글로우)
            with col_p1:
                st.markdown(f"""
                    <div class="podium-card podium-1st">
                        <div class="floating-icon" style="font-size: 2.6rem;">👑</div>
                        <br>
                        <span class="rank-tag" style="background-color:#f59e0b; color:#fff;">1ST WINNER</span>
                        <div class="movie-title" style="font-size: 1.55rem; color:#b45309;">{m1['movieNm']}</div>
                        <div class="movie-meta">개봉일 {m1['openDt']} | {m1['순위변동']}</div>
                        <div class="data-pill" style="background-color: #fef3c7;">
                            <div class="data-label" style="color:#b45309;">어제 관객수</div>
                            <div class="data-val" style="color:#78350f;">{m1['audiCnt']:,} 명</div>
                        </div>
                        <div class="data-pill" style="background-color: #fef3c7;">
                            <div class="data-label" style="color:#b45309;">누적 관객수</div>
                            <div class="data-val" style="color:#78350f;">{m1['audiAcc']:,} 명</div>
                        </div>
                        <div class="ticket-barcode" style="color:#d97706;">||||||||||||||| #GOLD-1</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🥇 1위 상세 정보", key="pod_btn_1"):
                    show_movie_dialog(m1["movieNm"])

            # 🥉 3위 포디움 (🎬 슬레이트 플로팅 아이콘)
            with col_p3:
                st.markdown(f"""
                    <div class="podium-card podium-3rd">
                        <div class="floating-icon">🎬</div>
                        <span class="rank-tag">3RD PLACE</span>
                        <div class="movie-title">{m3['movieNm']}</div>
                        <div class="movie-meta">개봉일 {m3['openDt']} | {m3['순위변동']}</div>
                        <div class="data-pill">
                            <div class="data-label">어제 관객수</div>
                            <div class="data-val">{m3['audiCnt']:,} 명</div>
                        </div>
                        <div class="data-pill">
                            <div class="data-label">누적 관객수</div>
                            <div class="data-val">{m3['audiAcc']:,} 명</div>
                        </div>
                        <div class="ticket-barcode">||||||| | ||| #NO-3</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🎟️ 3위 상세 정보", key="pod_btn_3"):
                    show_movie_dialog(m3["movieNm"])

        st.divider()

        # 4위~10위 영화 목록
        st.markdown("##### 🎟️ NEXT RANKINGS (4위~10위)")
        for i in range(3, min(10, len(df))):
            item = df.iloc[i]
            c_info, c_btn = st.columns([4, 1])
            with c_info:
                st.markdown(f"""
                    <div class="normal-ticket">
                        <div>
                            <span style="background-color:#0f172a; color:#fff; font-weight:800; font-size:0.8rem; padding:3px 10px; border-radius:12px;">NO. {item['rank']}</span>
                            <strong style="font-size:1.05rem; margin-left:10px;">{item['movieNm']}</strong>
                            <span style="color:#64748b; font-size:0.85rem; margin-left:12px;">개봉: {item['openDt']} | {item['순위변동']}</span>
                        </div>
                        <div style="font-size:0.95rem; font-weight:700; color:#0f172a;">
                            관객 {item['audiCnt']:,}명 <span style="font-size:0.8rem; color:#64748b; font-weight:normal;">(누적 {item['audiAcc']:,}명)</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with c_btn:
                st.write("")
                if st.button("상세보기", key=f"norm_btn_{i}"):
                    show_movie_dialog(item["movieNm"])

    # TAB 2: 차트
    with tab2:
        st.markdown("#### 📊 TOP 5 관객수 비교 차트")
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
