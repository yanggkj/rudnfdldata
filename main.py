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
    fig1 = px.pie(
        genre_counts,
        names='장르',
        values='편수',
        hole=0.4,
        title="장르별 영화 편수 비중 (도넛 차트)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig1.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>장르: %{label}</b><br>편수: %{value}편<br>비율: %{percent}'
    )
    
    fig1.update_layout(
        legend_title="장르 목록",
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig1, use_container_width=True)
    
    # 그래프 하단 Insight
    stream_lit.info("💡 **이 그래프로 알 수 있는 것:** 박스오피스 상위권 영화 중 특정 주요 장르가 대부분의 비중을 차지하고 있음을 알 수 있습니다.")
    
    stream_lit.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------
    # 섹션 2: 장르 및 영화별 총 관객 수 (트리맵)
    # -------------------------------------------------------------
    stream_lit.header("2. 장르 및 영화별 총 관객 수 분포 (트리맵)")
    
    # Plotly 트리맵 그래프 생성 (계층 구조: genre -> movieNm)
    fig2 = px.treemap(
        df,
        path=[px.Constant("전체 영화"), 'genre', 'movieNm'],
        values='total_audi',
        title="장르 및 영화별 총 관객 수 트리맵",
        color='genre',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig2.update_traces(
        hovertemplate='<b>영화명: %{label}</b><br>총 관객 수: %{value:,}명'
    )
    
    fig2.update_layout(
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig2, use_container_width=True)
    
    # 그래프 하단 Insight
    stream_lit.info("💡 **이 그래프로 알 수 있는 것:** 각 장르 내에서 어떤 영화가 가장 많은 총 관객 수를 기록했는지 직관적으로 비교할 수 있습니다.")

    stream_lit.markdown("<br><hr><br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 섹션 3: 총 관객 수 분포 (히스토그램)
    # -------------------------------------------------------------
    stream_lit.header("3. 총 관객 수(total_audi) 분포 히스토그램")
    
    # 히스토그램 동적 데이터 계산
    max_audi_movie = df.loc[df['total_audi'].idxmax()]
    top_movie_name = max_audi_movie['movieNm']
    top_movie_audi = max_audi_movie['total_audi']
    
    fig3 = px.histogram(
        df,
        x='total_audi',
        nbins=20,
        title="총 관객 수 분포 히스토그램",
        labels={'total_audi': '총 관객 수 (명)', 'count': '영화 수'},
        color_discrete_sequence=['#636EFA']
    )
    
    fig3.update_layout(
        xaxis_title="총 관객 수 (명)",
        yaxis_title="영화 수 (편)",
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig3, use_container_width=True)
    
    # 그래프 하단 Insight 문구 동적 생성
    stream_lit.info(
        f"💡 **이 그래프로 알 수 있는 것:** 대다수의 영화가 상대적으로 적은 관객 수 구간(하위 구간)에 집중되어 있는 오른쪽으로 긴 꼬리를 가진 분포 형태를 보이며, "
        f"가장 관객이 많은 영화는 **'{top_movie_name}'**(총 {top_movie_audi:,}명)입니다."
    )

    stream_lit.markdown("<br><hr><br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 섹션 4: 개봉일 스크린 수 vs 총 관객 수 (산점도)
    # -------------------------------------------------------------
    stream_lit.header("4. 개봉일 스크린 수 vs 총 관객 수 관계 (산점도)")
    
    fig4 = px.scatter(
        df,
        x='first_scrn',
        y='total_audi',
        color='genre',
        hover_name='movieNm',
        hover_data={'movieNm': False, 'first_scrn': ':,', 'total_audi': ':,'},
        labels={
            'first_scrn': '개봉일 스크린 수',
            'total_audi': '총 관객 수 (명)',
            'genre': '장르'
        },
        title="개봉일 스크린 수(first_scrn)와 총 관객 수(total_audi) 산점도"
    )
    
    fig4.update_traces(marker=dict(size=9, opacity=0.8))
    fig4.update_layout(
        xaxis_title="개봉일 스크린 수 (개)",
        yaxis_title="총 관객 수 (명)",
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig4, use_container_width=True)
    
    # 그래프 하단 Insight
    stream_lit.info("💡 **이 그래프로 알 수 있는 것:** 개봉일 스크린 수가 많을수록 대체로 총 관객 수도 증가하는 양의 상관관계를 보이며, 장르별로 초기 스크린 확보 수준과 상응하는 관객 동원력의 차이를 확인할 수 있습니다.")

except Exception as e:
    stream_lit.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
