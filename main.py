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
    # Plotly 다중 선 그래프 생성
    fig2 = px.line(
        top5_df,
        x='날짜',
        y='일관객',
        color='영화명',
        title="기간 내 일관객 합계 TOP 5 영화의 일별 관객수 변화 비교",
        labels={'날짜': '날짜', '일관객': '일일 관객수(명)', '영화명': '영화 제목'}
    )
    
    # 툴팁 및 범례 설정
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
# 구역 3: 날짜별 TOP 10 일관객 합계 영역 그래프
# ----------------------------------------------------
st.header("3. 날짜별 박스오피스 TOP 10 일관객 합계 추이")

# 날짜별 일관객 합계 계산
daily_total = df.groupby('날짜')['일관객'].sum().reset_index().sort_values('날짜')

if not daily_total.empty:
    # 영역 그래프 (Area chart) 생성
    fig3 = px.area(
        daily_total,
        x='날짜',
        y='일관객',
        title="일별 박스오피스 TOP 10 관객수 총합 추이",
        labels={'날짜': '날짜', '일관객': 'TOP 10 총 관객수(명)'}
    )
    
    # 상위 3일 추출 (관객수 기준)
    top3_days = daily_total.nlargest(3, '일관객')
    
    # 그래프에 상위 3일 주석(Annotation) 추가
    for idx, row in top3_days.iterrows():
        date_str = row['날짜'].strftime('%Y-%m-%d')
        audience_cnt = f"{row['일관객']:,}명"
        
        fig3.add_annotation(
            x=row['날짜'],
            y=row['일관객'],
            text=f"TOP 👑<br>{date_str}<br>({audience_cnt})",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="#EF553B",
            ax=0,
            ay=-45,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#EF553B",
            borderwidth=1,
            borderpad=4
        )
    
    # 툴팁 및 레이아웃 디테일 설정
    fig3.update_traces(
        hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>TOP 10 총 관객수:</b> %{y:,}명<extra></extra>"
    )
    fig3.update_layout(
        xaxis_title="날짜",
        yaxis_title="TOP 10 일관객 합계",
        hovermode="x unified"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # 그래프 설명 문구 자리
    st.info("💡 **이 그래프로 알 수 있는 것:** 전체 영화 시장의 일별 총 관객수 규모 변화와 연휴·명절 등 1년 중 극장가가 가장 붐볐던 최전성기 날짜 3곳을 한눈에 확인할 수 있습니다.")

else:
    st.warning("일별 합계 데이터를 처리할 수 없습니다.")

st.markdown("---")

# ----------------------------------------------------
# 구역 4: 기간 내 관객수 TOP 10 영화 가로 막대그래프
# ----------------------------------------------------
st.header("4. 기간 내 총 관객수 TOP 10 영화")

# 영화별 총 관객수 및 10위권 차트인 날수(집계 행 수) 집계
top10_summary = (
    df.groupby('영화명')
    .agg(
        총관객수=('일관객', 'sum'),
        차트인일수=('날짜', 'count')
    )
    .reset_index()
    .nlargest(10, '총관객수')
    # Plotly 가로 막대는 아래서부터 위로 그려지므로 관객수 오름차순으로 정렬해야 큰 값이 위에 옵니다.
    .sort_values('총관객수', ascending=True)
)

if not top10_summary.empty:
    # Plotly 가로 막대그래프 생성
    fig4 = px.bar(
        top10_summary,
        x='총관객수',
        y='영화명',
        orientation='h',
        title="기간 내 총 관객수 TOP 10 영화",
        labels={'총관객수': '누적 관객수(명)', '영화명': '영화 제목', '차트인일수': '10위권 진입 일수'},
        hover_data=['차트인일수'],
        color='총관객수',
        color_continuous_scale='Blues'
    )
    
    # 툴팁 세부 디자인 설정
    fig4.update_traces(
        hovertemplate="<b>%{y}</b><br>총 관객수: %{x:,}명<br>10위권 진입 일수: %{customdata[0]}일<extra></extra>"
    )
    fig4.update_layout(
        xaxis_title="누적 관객수(명)",
        yaxis_title="영화 제목",
        coloraxis_showscale=False
    )

    st.plotly_chart(fig4, use_container_width=True)

    # 그래프 설명 문구 자리
    st.info("💡 **이 그래프로 알 수 있는 것:** 해당 기간 동안 가장 괄목할 만한 성적을 낸 TOP 10 영화의 종합 관객 수 및 각 영화가 TOP 10 박스오피스에 며칠 동안 머물렀는지 롱런 여부를 파악할 수 있습니다.")

else:
    st.warning("TOP 10 영화 데이터를 처리할 수 없습니다.")

st.markdown("---")

# ----------------------------------------------------
# 구역 5: 추가 그래프 영역 (추후 확장용)
# ----------------------------------------------------
st.header("5. [추가 그래프 영역]")
st.caption("다음 시각화 그래프가 들어갈 공간입니다.")

st.info("💡 **이 그래프로 알 수 있는 것:** (추후 추가될 그래프 분석 결과 문구가 들어갈 자리입니다.)")
