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
    fig1 = px.line(
        movie_df,
        x='날짜',
        y='일관객',
        title=f"[{selected_movie}] 날짜별 일관객수 변화",
        labels={'날짜': '날짜', '일관객': '일일 관객수(명)'},
        markers=True
    )
    
    # 툴팁 및 레이아웃 디테일 설정
    fig1.update_traces(
        hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>관객수:</b> %{y:,}명<extra></extra>"
    )
    fig1.update_layout(
        xaxis_title="날짜",
        yaxis_title="일일 관객수",
        hovermode="x unified"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # 그래프 설명 문구 자리
    st.info("💡 **이 그래프로 알 수 있는 것:** 개별 영화의 상영 기간에 따른 흥행 흐름과 최고 관객수를 기록한 시점을 확인할 수 있습니다.")

else:
    st.warning("선택한 영화의 데이터가 존재하지 않습니다.")

st.markdown("---")

# ----------------------------------------------------
# 구역 2: 기간 내 관객수 TOP 5 영화 추이 비교
# ----------------------------------------------------
st.header("2. 기간 내 일관객 합계 TOP 5 영화 추이 비교")

# 일관객 합계 기준 상위 5개 영화 선정
top5_movies = (
    df.groupby('영화명')['일관객']
    .sum()
    .nlargest(5)
    .index
    .tolist()
)

# 상위 5개 영화 데이터 필터링
top5_df = df[df['영화명'].isin(top5_movies)].sort_values('날짜')

if not top5_df.empty:
    # Plotly 다중 선 그래프 생성 (color='영화명'으로 구분)
    fig2 = px.line(
        top5_df,
        x='날짜',
        y='일관객',
        color='영화명',
        title="기간 내 일관객 합계 TOP 5 영화의 일별 관객수 변화 비교",
        labels={'날짜': '날짜', '일관객': '일일 관객수(명)', '영화명': '영화 제목'}
    )
    
    # 툴팁 및 범례 설정 (범례 클릭 시 켜고 끄기 가능)
    fig2.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>날짜: %{x|%Y-%m-%d}<br>관객수: %{y:,}명<extra></extra>"
    )
    fig2.update_layout(
        xaxis_title="날짜",
        yaxis_title="일일 관객수",
        hovermode="x unified",
        legend_title_text="영화 목록 (클릭하여 켜기/끄기)"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # 그래프 설명 문구 자리
    st.info("💡 **이 그래프로 알 수 있는 것:** 해당 기간 최고 흥행작 5편의 흥행 화력과 흥행 기간을 비교해 어떤 영화가 언제 스크린을 주도했는지 파악할 수 있습니다.")

else:
    st.warning("TOP 5 영화 데이터를 처리할 수 없습니다.")

st.markdown("---")

# ----------------------------------------------------
# 구역 3: 추가 그래프 영역 (추후 확장용)
# ----------------------------------------------------
st.header("3. [추가 그래프 영역]")
st.caption("다음 시각화 그래프가 들어갈 공간입니다.")

st.info("💡 **이 그래프로 알 수 있는 것:** (추후 추가될 그래프 분석 결과 문구가 들어갈 자리입니다.)")
