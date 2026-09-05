import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 및 분포 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    try:
        df = pd.read_csv(url, encoding='cp949')
    except Exception:
        df = pd.read_csv(url, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    date_col = [c for c in df.columns if '날짜' in c][0]
    avg_col = [c for c in df.columns if '평균' in c][0]
    min_col = [c for c in df.columns if '최저' in c][0]
    max_col = [c for c in df.columns if '최고' in c][0]
    
    df[date_col] = pd.to_datetime(df[date_col])
    df['연도'] = df[date_col].dt.year
    
    for col in [avg_col, min_col, max_col]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=[avg_col])
    
    return df, avg_col, min_col, max_col, date_col

# 대시보드 타이틀
st.title("🌡️ 서울 일별 평균기온 분포 및 연도별 추이 분석")

try:
    df, avg_col, min_col, max_col, date_col = load_data()
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 데이터 필터링")
    
    min_year = int(df['연도'].min())
    max_year = int(df['연도'].max())
    
    year_range = st.sidebar.slider(
        "분석 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    # 선택된 연도 범위로 필터링
    filtered_df = df[(df['연도'] >= year_range[0]) & (df['연도'] <= year_range[1])].copy()
    
    # 탭 구성 (히스토그램 / 연도별 추이)
    tab1, tab2 = st.tabs(["📊 일별 기온 분포 (히스토그램)", "📈 100년 기온 변화 추이"])
    
    # --- TAB 1: 일별 기온 히스토그램 ---
    with tab1:
        st.subheader("📊 일별 평균기온 구간별 빈도 분포")
        
        # 히스토그램 간격(Bin size) 설정
        bin_size = st.slider("기온 구간 간격 (℃)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
        
        # 주요 통계 수치
        mean_temp = filtered_df[avg_col].mean()
        median_temp = filtered_df[avg_col].median()
        total_days = len(filtered_df)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 분석 일수", f"{total_days:,} 일")
        m2.metric("전체 일평균기온 평균", f"{mean_temp:.1f} ℃")
        m3.metric("일평균기온 중앙값", f"{median_temp:.1f} ℃")
        m4.metric("역대 최저 / 최고 일평균", f"{filtered_df[avg_col].min():.1f} ℃ / {filtered_df[avg_col].max():.1f} ℃")
        
        # Plotly 히스토그램 생성
        fig_hist = px.histogram(
            filtered_df,
            x=avg_col,
            nbins=int((filtered_df[avg_col].max() - filtered_df[avg_col].min()) / bin_size),
            title=f"서울 일별 평균기온 분포 ({year_range[0]}년 ~ {year_range[1]}년)",
            labels={avg_col: '일별 평균기온 (℃)', 'count': '일수 (빈도)'},
            color_discrete_sequence=['#42A5F5']
        )
        
        # 평균선 및 중앙값선 표시
        fig_hist.add_vline(x=mean_temp, line_dash="dash", line_color="red", annotation_text=f"평균: {mean_temp:.1f}℃")
        fig_hist.add_vline(x=median_temp, line_dash="dot", line_color="green", annotation_text=f"중앙값: {median_temp:.1f}℃")
        
        fig_hist.update_layout(
            bargap=0.05,
            template="plotly_white",
            xaxis_title="일별 평균기온 (℃)",
            yaxis_title="날짜 수(일)",
            hovermode="x"
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- TAB 2: 연도별 추이 ---
    with tab2:
        st.subheader("📈 연도별 연평균 기온 변화")
        
        ma_window = st.slider("이동평균 구간(년)", min_value=3, max_value=20, value=10)
        
        annual_df = filtered_df.groupby('연도').agg(
            연평균기온=(avg_col, 'mean')
        ).reset_index()
        
        annual_df['이동평균'] = annual_df['연평균기온'].rolling(window=ma_window, min_periods=1).mean()
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=annual_df['연도'], y=annual_df['연평균기온'],
            mode='lines+markers', name='연평균 기온', line=dict(color='#E53935', width=1.5)
        ))
        fig_line.add_trace(go.Scatter(
            x=annual_df['연도'], y=annual_df['이동평균'],
            mode='lines', name=f'{ma_window}년 이동평균', line=dict(color='#1E88E5', width=3, dash='dash')
        ))
        
        fig_line.update_layout(
            xaxis_title="연도",
            yaxis_title="기온 (℃)",
            template="plotly_white",
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
