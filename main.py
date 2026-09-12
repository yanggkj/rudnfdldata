import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide"
)

# 제목 설정
st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.markdown("---")

# ----------------------------------------------------
# 데이터 불러오기 및 전처리 (캐싱 적용)
# ----------------------------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
    df = pd.read_csv(url)
    
    # '날짜' 열을 문자열로 변환 후 datetime 타입으로 변경 (YYYYMMDD 형식)
    df['날짜'] = pd.to_datetime(df['날짜'].astype(str), format='%Y%m%d')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ----------------------------------------------------
# 구역 1: 영화별 일관객수 변화 (시간 추이)
# ----------------------------------------------------
st.header("1. 영화별 일별 관객수 추이")

# 영화 목록 추출 및 선택 드롭다운
movie_list = sorted(df['영화명'].unique())
selected_movie = st.selectbox("영화를 선택하세요:", movie_list)

# 선택된 영화 데이터 필터링
movie_df = df[df['영화명'] == selected_movie].sort_values('날짜')

if not movie_df.empty:
    # Plotly 선 그래프 생성
    fig = px.line(
        movie_df,
        x='날짜',
        y='일관객',
        title=f"[{selected_movie}] 날짜별 일관객수 변화",
        labels={'날짜': '날짜', '일관객': '일일 관객수(명)'},
        markers=True,
        hover_data={'날짜': '|%Y-%m-%d', '일관객': ':,d'}
    )
    
    # 툴팁 및 레이아웃 디테일 설정
    fig.update_traces(
        hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>관객수:</b> %{y:,}명<extra></extra>"
    )
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="일일 관객수",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 그래프 설명 문구 자리
    st.info("💡 **이 그래프로 알 수 있는 것:** 영화의 상영 기간에 따른 흥행 관객수 추이와 피크(peak) 시점을 파악할 수 있습니다.")

else:
    st.warning("선택한 영화의 데이터가 존재하지 않습니다.")

st.markdown("---")

# ----------------------------------------------------
# 구역 2: 추가 그래프 영역 (추후 확장용)
# ----------------------------------------------------
st.header("2. [추가 그래프 영역]")
st.caption("다음 시각화 그래프가 들어갈 공간입니다.")

# 예시 설명 자리
st.info("💡 **이 그래프로 알 수 있는 것:** (추후 추가될 그래프 분석 결과 문구가 들어갈 자리입니다.)")
