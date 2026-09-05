import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 기온 종합 분석 대시보드",
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
    df['월'] = df[date_col].dt.month
    
    # 수치형 변환
    for col in [avg_col, min_col, max_col]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 필수 데이터 결측치 제거
    df = df.dropna(subset=[min_col, max_col])
    
    # 일교차 계산
    df['일교차'] = df[max_col] - df[min_col]
    
    return df, avg_col, min_col, max_col, date_col

# 타이틀
st.title("🌡️ 서울 기온 분석 대시보드")

try:
    df, avg_col, min_col, max_col, date_col = load_data()
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 데이터 필터링")
    
    min_year = int(df['연도'].min())
    max_year = int(df['연도'].max())
    
    year_range = st.sidebar.slider(
        "분석 연도 범위",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    # 연도 필터링
    filtered_df = df[(df['연도'] >= year_range[0]) & (df['연도'] <= year_range[1])].copy()
    
    # 3개 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "🔵 최저 vs 최고기온 (산점도)", 
        "📊 일별 기온 분포 (히스토그램)", 
        "📈 100년 기온 변화 추이"
    ])
    
    # ==========================================
    # TAB 1: 최저기온 vs 최고기온 산점도
    # ==========================================
    with tab1:
        st.subheader("🔵 일별 최저기온과 최고기온의 상관관계")
        st.markdown("X축은 **최저기온**, Y축은 **최고기온**을 나타내며 점들이 대각선에 가까울수록 두 기온이 비례 관계임을 의미합니다.")
        
        # 컨트롤 영역
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            color_by_month = st.checkbox("월별(계절별) 색상 구분하기", value=True)
        with col_ctrl2:
            sample_size = st.select_slider(
                "표시할 데이터 수 (속도 최적화)",
                options=[1000, 3000, 5000, 10000, "전체"],
                value=5000
            )
        
        # 데이터 샘플링
        if sample_size != "전체" and len(filtered_df) > sample_size:
            plot_df = filtered_df.sample(n=sample_size, random_state=42).copy()
        else:
            plot_df = filtered_df.copy()
            
        # 통계값 계산 (전체 필터링 데이터 기준)
        corr = filtered_df[min_col].corr(filtered_df[max_col])
        avg_diff = filtered_df['일교차'].mean()
        max_diff_row = filtered_df.loc[filtered_df['일교차'].idxmax()]
        
        # 요약 메트릭
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("상관계수 (r)", f"{corr:.3f}", help="1에 가까울수록 강한 양의 상관관계")
        s2.metric("평균 일교차", f"{avg_diff:.1f} ℃")
        s3.metric("최대 일교차", f"{max_diff_row['일교차']:.1f} ℃", f"{max_diff_row[date_col].strftime('%Y-%m-%d')}")
        s4.metric("표시된 데이터 수", f"{len(plot_df):,} 개")
        
        # Plotly 산점도 생성
        if color_by_month:
            plot_df['월_label'] = plot_df['월'].astype(str) + "월"
            fig_scatter = px.scatter(
                plot_df,
                x=min_col,
                y=max_col,
                color='월',
                color_continuous_scale='Turbo',
                hover_data=[date_col, '일교차'],
                labels={min_col: '최저기온 (℃)', max_col: '최고기온 (℃)', '월': '월'},
                title=f"서울 일별 최저 vs 최고기온 산점도 ({year_range[0]}년 ~ {year_range[1]}년)",
                opacity=0.6
            )
        else:
            fig_scatter = px.scatter(
                plot_df,
                x=min_col,
                y=max_col,
                hover_data=[date_col, '일교차'],
                labels={min_col: '최저기온 (℃)', max_col: '최고기온 (℃)'},
                title=f"서울 일별 최저 vs 최고기온 산점도 ({year_range[0]}년 ~ {year_range[1]}년)",
                color_discrete_sequence=['#2B5C8F'],
                opacity=0.5
            )
            
        # 선형 회귀 추세선(OLS Trendline) 추가
        x = plot_df[min_col].values
        y = plot_df[max_col].values
        mask = ~np.isnan(x) & ~np.isnan(y)
        m, b = np.polyfit(x[mask], y[mask], 1)
        
        x_range = np.array([x.min(), x.max()])
        fig_scatter.add_trace(go.Scatter(
            x=x_range,
            y=m * x_range + b,
            mode='lines',
            name=f'추세선 (y = {m:.2f}x + {b:.2f})',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig_scatter.update_layout(
            template="plotly_white",
            height=600,
            xaxis_title="일 최저기온 (℃)",
            yaxis_title="일 최고기온 (℃)"
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ==========================================
    # TAB 2: 일별 기온 히스토그램
    # ==========================================
    with tab2:
        st.subheader("📊 일별 평균기온 구간별 빈도 분포")
        
        bin_size = st.slider("기온 구간 간격 (℃)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
        
        mean_temp = filtered_df[avg_col].mean()
        median_temp = filtered_df[avg_col].median()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 분석 일수", f"{len(filtered_df):,} 일")
        m2.metric("전체 일평균기온 평균", f"{mean_temp:.1f} ℃")
        m3.metric("일평균기온 중앙값", f"{median_temp:.1f} ℃")
        m4.metric("역대 최저 / 최고 일평균", f"{filtered_df[avg_col].min():.1f} ℃ / {filtered_df[avg_col].max():.1f} ℃")
        
        fig_hist = px.histogram(
            filtered_df,
            x=avg_col,
            nbins=int((filtered_df[avg_col].max() - filtered_df[avg_col].min()) / bin_size),
            title=f"서울 일별 평균기온 분포 ({year_range[0]}년 ~ {year_range[1]}년)",
            labels={avg_col: '일별 평균기온 (℃)'},
            color_discrete_sequence=['#42A5F5']
        )
        
        fig_hist.add_vline(x=mean_temp, line_dash="dash", line_color="red", annotation_text=f"평균: {mean_temp:.1f}℃")
        fig_hist.add_vline(x=median_temp, line_dash="dot", line_color="green", annotation_text=f"중앙값: {median_temp:.1f}℃")
        
        fig_hist.update_layout(
            bargap=0.05,
            template="plotly_white",
            xaxis_title="일별 평균기온 (℃)",
            yaxis_title="날짜 수(일)"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ==========================================
    # TAB 3: 연도별 추이
    # ==========================================
    with tab3:
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
