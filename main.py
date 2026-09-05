import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import timezonefinder # 필요시 타임존 처리를 위한 파이썬 기본 모듈 활용
import pytz
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="어제 박스오피스 순위",
    page_icon="🎬",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 날짜 계산 함수 (한국 시간 KST 기준 '어제')
# -----------------------------------------------------------------------------
def get_yesterday_kst():
    """
    배포 서버(Streamlit Cloud)의 시계가 UTC(세계 표준시)기준이어도 
    한국 표준시(KST, UTC+9)를 기준으로 '어제' 날짜(YYYYMMDD)를 구합니다.
    """
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    yesterday_kst = now_kst - timedelta(days=1)
    return yesterday_kst.strftime("%Y%m%d"), yesterday_kst.strftime("%Y년 %m월 %d일")


# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 호출 함수 (st.cache_data 사용)
# -----------------------------------------------------------------------------
# ttl=3600 초(1시간) 동안 동일한 데이터 요청은 API를 다시 부르지 않고 캐시를 사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, target_date):
    """
    KOBIS API를 호출하여 데이터를 가져옵니다.
    """
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": target_date
    }
    
    # API 요청 (타임아웃 10초 설정)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status() # HTTP 에러 발생 시 예외 발생
    return response.json()


# -----------------------------------------------------------------------------
# 4. 메인 화면 구성 및 데이터 처리
# -----------------------------------------------------------------------------
target_dt_str, display_date_str = get_yesterday_kst()

st.title("🎬 어제 일별 박스오피스 순위")
st.caption(f"📅 기준 일자: {display_date_str} (한국 표준시 기준 어제)")

# Streamlit Secrets에서 인증키 가져오기
api_key = st.secrets.get("KOBIS_KEY", None)

# 인증키가 세팅되어 있지 않은 경우 처리
if not api_key:
    st.error("🚨 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
    st.info(
        "**[해결 방법]**\n"
        "1. Streamlit Cloud의 앱 설정에서 `Secrets` 메뉴로 이동하세요.\n"
        "2. 아래와 같이 KOBIS API 키를 입력하고 저장하세요:\n"
        "```toml\n"
        'KOBIS_KEY = "발급받은_키_문자열"\n'
        "```"
    )
    st.stop()

# API 호출 및 에러 예외 처리
try:
    data = fetch_box_office_data(api_key, target_dt_str)
    
    # 1) 인증키 오류나 서버 오류로 faultInfo 상자가 온 경우
    if "faultInfo" in data:
        st.error("🚨 KOBIS API 오류가 발생했습니다.")
        fault = data["faultInfo"]
        st.warning(f"**오류 메시지:** {fault.get('message', '알 수 없는 오류')}")
        st.info(
            "**[확인할 사항]**\n"
            "- Streamlit Secrets에 입력한 `KOBIS_KEY`가 정확한지 확인하세요.\n"
            "- 영화진흥위원회 통합전산망(KOBIS)에서 API 키가 활성화 상태인지 확인하세요."
        )
        st.stop()
        
    box_office_result = data.get("boxOfficeResult", {})
    daily_list = box_office_result.get("dailyBoxOfficeList", [])
    
    # 2) 영화 목록이 비어 있는 경우
    if not daily_list:
        st.warning("⚠️ 어제 날짜의 박스오피스 데이터가 아직 집계되지 않았거나 비어 있습니다.")
        st.info(
            "**[확인할 사항]**\n"
            "- 보통 오전 일찍 조회할 경우 KOBIS 측 전날 집계가 완료되지 않았을 수 있습니다.\n"
            "- 잠시 후 다시 시도해 보세요."
        )
        st.stop()

    # 데이터프레임 변환
    df = pd.DataFrame(daily_list)
    
    # -------------------------------------------------------------------------
    # 5. 데이터 정제 및 타입 변환 (문자열 -> 숫자)
    # -------------------------------------------------------------------------
    # KOBIS API는 숫자 값도 모두 문자열로 보내주므로 형변환이 필수입니다.
    numeric_columns = ['rank', 'rankInten', 'audiCnt', 'audiAcc', 'scrnCnt', 'showCnt']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
    # 순위 기준으로 정렬
    df = df.sort_values(by='rank').reset_index(drop=True)
    
    # -------------------------------------------------------------------------
    # 6. 1위 영화 지표 카드 (Metric Cards)
    # -------------------------------------------------------------------------
    top_1 = df.iloc[0]
    st.markdown("---")
    st.subheader(f"🥇 어제의 1위 영화: **{top_1['movieNm']}**")
    
    # 증감 표시
    rank_inten = top_1['rankInten']
    if rank_inten > 0:
        delta_str = f"▲ {rank_inten} (순위 상승)"
    elif rank_inten < 0:
        delta_str = f"▼ {abs(rank_inten)} (순위 하락)"
    else:
        delta_str = "변동 없음"
        
    m1, m2, m3 = st.columns(3)
    m1.metric("일일 관객수", f"{top_1['audiCnt']:,} 명", delta=delta_str)
    m2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
    m3.metric("스크린수", f"{top_1['scrnCnt']:,} 개")
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 7. 관객수 상위 5편 막대그래프
    # -------------------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5).copy()
    
    # 그래프 생성을 위한 Plotly 시각화
    fig = px.bar(
        top_5_df,
        x='movieNm',
        y='audiCnt',
        text='audiCnt',
        labels={'movieNm': '영화명', 'audiCnt': '일일 관객수(명)'},
        color='audiCnt',
        color_continuous_scale='Reds'
    )
    
    fig.update_traces(
        texttemplate='%{text:,}명', 
        textposition='outside'
    )
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="관객수 (명)",
        showlegend=False,
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 8. 박스오피스 전체 순위 표
    # -------------------------------------------------------------------------
    st.subheader("📋 전체 박스오피스 순위")
    
    # 화면에 보여줄 컬럼 선택 및 이름을 한국어로 변경
    display_df = df[['rank', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
    display_df.columns = ['순위', '영화명', '개봉일', '관객수', '누적관객', '스크린수']
    
    # 천 단위 콤마(,) 스타일링 및 표 출력
    st.dataframe(
        display_df.style.format({
            '순위': '{:}위',
            '관객수': '{:,} 명',
            '누적관객': '{:,} 명',
            '스크린수': '{:,} 개'
        }),
        use_container_width=True,
        hide_index=True
    )

except requests.exceptions.RequestException as e:
    st.error("🚨 네트워크/서버 요청 실패 오류가 발생했습니다.")
    st.warning(f"**상세 오류:** {e}")
    st.info(
        "**[확인할 사항]**\n"
        "- KOBIS API 서버가 점검 중이거나 응답하지 않는 상태일 수 있습니다.\n"
        "- 잠시 후 페이지를 새로고침해 보세요."
    )
except Exception as e:
    st.error("🚨 앱 실행 중 예상치 못한 오류가 발생했습니다.")
    st.warning(f"**상세 내용:** {e}")
