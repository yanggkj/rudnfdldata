import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # CP949 또는 UTF-8 인코딩 처리
    try:
        df = pd.read_csv(url, encoding='cp949')
    except Exception:
        df = pd.read_csv(url, encoding='utf-8')
    
    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()
    
    # 핵심 컬럼 자동 탐색 (열 이름 변형 대비)
    date_col = [c for c in df.columns if '날짜' in c][0]
    avg_col = [c for c in df.columns if '평균' in c][0]
    min_col = [c for c in df.columns if '최저' in c][0]
    max_col = [c for c in df.columns if '최고' in c][0]
    
    # 날짜 처리 및 연도 추출
    df[date_col] = pd.to_datetime(df[date_col])
    df['연도'] = df[date_col].dt.year
    
    # 수치형 변환 및 결측치 처리
    for col in [avg_col, min_col, max_col]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=[avg_col])
    
    return df, avg_col, min_col, max_col

# 앱 헤더
st.title("🌡️ 지난 100년간 서울의 기온 변화")
st.markdown("기상청 서울 관측 데이터(seoul.csv)를 바탕으로 연도별 기온 변화 추이를 시각화한 웹 앱입니다.")

try:
    df, avg_col, min_col, max_col = load_data()
    
    # 연도별 평균 집계
    annual_df = df.groupby('연도').agg(
        연평균기온=(avg_col, 'mean'),
        연평균최저기온=(min_col, 'mean'),
        연평균최고기온=(max_col, 'mean')
    ).reset_index()
    
    # 사이드바 제어 요소
    st.sidebar.header("⚙️ 검색 및 분석 옵션")
    
    min_year = int(annual_df['연도'].min())
    max_year = int(annual_df['연도'].max())
    
    year_range = st.sidebar.slider(
        "조회 연도 범위",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    ma_window = st.sidebar.slider("이동평균 구간(년)", min_value=3, max_value=20, value=10)
    
    # 데이터 필터링 및 이동평균 계산
    filtered_df = annual_df[(annual_df['연도'] >= year_range[0]) & (annual_df['연도'] <= year_range[1])].copy()
    filtered_df['이동평균'] = filtered_df['연평균기온'].rolling(window=ma_window, min_periods=1).mean()
    
    # 요약 지표 (Metric Cards)
    c1, c2, c3, c4 = st.columns(4)
    
    start_temp = filtered_df['연평균기온'].iloc[0]
    end_temp = filtered_df['연평균기온'].iloc[-1]
    diff = end_temp - start_temp
    
    max_row = filtered_df.loc[filtered_df['연평균기온'].idxmax()]
    min_row = filtered_df.loc[filtered_df['연평균기온'].idxmin()]
    
    c1.metric("분석 기간", f"{year_range[0]} ~ {year_range[1]}년")
    c2.metric("최근 연평균 기온", f"{end_temp:.1f} ℃", delta=f"{diff:+.1f} ℃ (시작 대비)")
    c3.metric("가장 따뜻했던 해", f"{int(max_row['연도'])}년", f"{max_row['연평균기온']:.1f} ℃")
    c4.metric("가장 춥던 해", f"{int(min_row['연도'])}년", f"{min_row['연평균기온']:.1f} ℃")
    
    st.markdown("---")
    
    # 그래프 시각화 (Plotly)
    st.subheader("📈 연도별 연평균 기온 및 추세선")
    
    fig = go.Figure()
    
    # 연평균 기온 라인
    fig.add_trace(go.Scatter(
        x=filtered_df['연도'],
        y=filtered_df['연평균기온'],
        mode='lines+markers',
        name='연평균 기온',
        line=dict(color='#E53935', width=1.5),
        marker=dict(size=4),
        hovertemplate='%{x}년 연평균: %{y:.2f}℃<extra></extra>'
    ))
    
    # 이동평균 라인
    fig.add_trace(go.Scatter(
        x=filtered_df['연도'],
        y=filtered_df['이동평균'],
        mode='lines',
        name=f'{ma_window}년 이동평균',
        line=dict(color='#1E88E5', width=3, dash='dash'),
        hovertemplate=f'%{{x}}년 {ma_window}년 이동평균: %{{y:.2f}}℃<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=f"서울 연평균 기온 추이 ({year_range[0]}년 ~ {year_range[1]}년)"),
        xaxis_title="연도",
        yaxis_title="기온 (℃)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 데이터표 및 다운로드
    with st.expander("📄 연도별 요약 데이터 보기"):
        st.dataframe(filtered_df.style.format({
            '연평균기온': '{:.2f} ℃',
            '연평균최저기온': '{:.2f} ℃',
            '연평균최고기온': '{:.2f} ℃',
            '이동평균': '{:.2f} ℃'
        }), use_container_width=True)
        
        csv_bytes = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 CSV 데이터 다운로드",
            data=csv_bytes,
            file_name=f"seoul_temp_{year_range[0]}_{year_range[1]}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 동안 오류가 발생했습니다: {e}")
