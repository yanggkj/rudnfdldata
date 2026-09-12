import streamlit as stream_lit
import pandas as pd
import plotly.express as px

# Streamlit 페이지 설정
stream_lit.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

stream_lit.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
stream_lit.markdown("---")

# 데이터 로드 및 전처리
@stream_lit.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # 장르: 결측치(NaN/float) 예방 및 세로막대 기호(|)로 여러 개 적힌 영화는 첫 번째 장르만 추출
    if 'genre' in df.columns:
        def extract_first_genre(val):
            if pd.isna(val):
                return '기타'
            return str(val).split('|')[0].strip()
            
        df['genre'] = df['genre'].apply(extract_first_genre)
        
    return df

try:
    df = load_data()
    
    # Sidebar: 데이터 요약 및 사이드바 옵션
    stream_lit.sidebar.header("📊 데이터 요약")
    stream_lit.sidebar.metric(label="총 수집 영화 수", value=f"{len(df)} 편")
    stream_lit.sidebar.markdown("---")
    stream_lit.sidebar.write("데이터 출처: KOBIS (박스오피스 요약 216편)")
    
    if stream_lit.sidebar.checkbox("원본 데이터 보기"):
        stream_lit.subheader("📄 Raw Data")
        stream_lit.dataframe(df)

    # -------------------------------------------------------------
    # 섹션 1: 장르별 영화 편수 (도넛 그래프)
    # -------------------------------------------------------------
    stream_lit.header("1. 장르별 영화 편수 분포")
    
    # 장르별 빈도 계산
    genre_counts = df['genre'].value_counts().reset_index()
    genre_counts.columns = ['장르', '편수']
    
    # Plotly 도넛 그래프 생성
    fig = px.pie(
        genre_counts,
        names='장르',
        values='편수',
        hole=0.4,
        title="장르별 영화 편수 비중 (도넛 차트)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>장르: %{label}</b><br>편수: %{value}편<br>비율: %{percent}'
    )
    
    fig.update_layout(
        legend_title="장르 목록",
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig, use_container_width=True)
    
    # 그래프 하단 Insight 및 구역 구분을 위한 설정
    stream_lit.info("💡 **이 그래프로 알 수 있는 것:** 박스오피스 상위권 영화 중 특정 주요 장르가 대부분의 비중을 차지하고 있음을 알 수 있습니다.")
    
    stream_lit.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------
    # 섹션 2: 개봉일 스크린 수와 총 관객 수의 관계
    # -------------------------------------------------------------
    stream_lit.header("2. 개봉일 스크린 수 vs 총 관객 수 관계")
    
    fig2 = px.scatter(
        df,
        x='first_scrn',
        y='total_audi',
        color='genre',
        hover_data=['movieNm', 'days_in_top10'],
        labels={
            'first_scrn': '개봉일 스크린 수',
            'total_audi': '총 관객 수 (명)',
            'genre': '장르',
            'movieNm': '영화명',
            'days_in_top10': 'Top10 머문 날수'
        },
        title="개봉일 스크린 수에 따른 총 관객 수 산점도"
    )
    
    fig2.update_traces(marker=dict(size=8, opacity=0.8))
    fig2.update_layout(margin=dict(t=50, b=30, l=10, r=10))
    
    stream_lit.plotly_chart(fig2, use_container_width=True)
    
    stream_lit.info("💡 **이 그래프로 알 수 있는 것:** 초기 스크린 수가 확보될수록 총 관객 수가 늘어나는 양의 상관관계를 관찰할 수 있습니다.")

except Exception as e:
    stream_lit.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
