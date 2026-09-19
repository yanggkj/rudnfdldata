import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 기온 예측기", page_icon="🌡️", layout="wide"
)


# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_and_process_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

    # UTF-8 인코딩으로 데이터 읽기
    df = pd.read_csv(url, encoding="utf-8")

    # 날짜 데이터 변환 및 연도 추출
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year

    # 1. 2025년 이하 데이터만 필터링
    df = df[df["연도"] <= 2025]

    # 2. 연도별 관측일수 및 평균기온 계산
    yearly_stats = (
        df.groupby("연도")["평균기온"].agg(["count", "mean"]).reset_index()
    )

    # 3. 관측일수가 300일 이상인 해만 필터링
    valid_yearly = yearly_stats[yearly_stats["count"] >= 300].copy()
    valid_yearly.rename(columns={"mean": "연평균기온"}, inplace=True)

    # 4. 전체 기간 독립 변수 X: 1908년부터 지난 연수 (연도 - 1908)
    valid_yearly["X"] = valid_yearly["연도"] - 1908

    # --- 1) 전체 기간 회귀 모델 ---
    slope_full, intercept_full = np.polyfit(
        valid_yearly["X"], valid_yearly["연평균기온"], 1
    )
    correlation_full = valid_yearly["연도"].corr(valid_yearly["연평균기온"])

    # --- 2) 최근 20년 회귀 모델 ---
    recent_start_year = valid_yearly["연도"].max() - 19
    recent_yearly = valid_yearly[
        valid_yearly["연도"] >= recent_start_year
    ].copy()
    slope_recent, intercept_recent = np.polyfit(
        recent_yearly["X"], recent_yearly["연평균기온"], 1
    )
    correlation_recent = recent_yearly["연도"].corr(
        recent_yearly["연평균기온"]
    )

    return (
        valid_yearly,
        recent_yearly,
        slope_full,
        intercept_full,
        correlation_full,
        slope_recent,
        intercept_recent,
        correlation_recent,
    )


# 데이터 및 모델 로드
(
    df_valid,
    df_recent,
    slope_full,
    intercept_full,
    corr_full,
    slope_recent,
    intercept_recent,
    corr_recent,
) = load_and_process_data()

# 주요 통계 정보
num_years = len(df_valid)
start_year = int(df_valid["연도"].min())
end_year = int(df_valid["연도"].max())

# 100년당 기온 상승 폭 (°C/100년)
rate_full_100y = slope_full * 100
rate_recent_100y = slope_recent * 100

# 앱 타이틀
st.title("🌡️ 서울 연평균 기온 예측기")
st.caption(
    "1908년 이후 서울 기온 데이터를 기반으로 한 선형 회귀 및 최근 온난화 가속도 분석"
)

# 데이터 기본 개요
col_a, col_b, col_c = st.columns(3)
col_a.metric("직선을 만든 해의 개수", f"{num_years}개 해")
col_b.metric("시작 연도", f"{start_year}년")
col_c.metric("끝 연도", f"{end_year}년")

st.divider()

# --- 주요 결과 강조: 100년당 기온 상승 폭 비교 ---
st.subheader("🔥 100년당 기온 상승 폭 비교")

col_rate1, col_rate2 = st.columns(2)

with col_rate1:
    st.metric(
        label=f"전체 기간 상승 속도 ({start_year}~{end_year}년)",
        value=f"{rate_full_100y:+.2f} °C / 100년",
        delta=f"상관계수 (r): {corr_full:.4f}",
        delta_color="off",
    )

with col_rate2:
    recent_start_year = int(df_recent["연도"].min())
    recent_end_year = int(df_recent["연도"].max())
    diff_rate = rate_recent_100y - rate_full_100y
    st.metric(
        label=f"최근 20년 상승 속도 ({recent_start_year}~{recent_end_year}년)",
        value=f"{rate_recent_100y:+.2f} °C / 100년",
        delta=f"전체 평균 대비 {diff_rate:+.2f} °C/100년 빠른 속도",
        delta_color="inverse" if diff_rate > 0 else "normal",
    )

st.divider()

# 레이아웃 분할 (왼쪽: 연도 선택 및 예측값, 오른쪽: 그래프)
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("🔮 기온 예측하기")

    # 연도 선택 슬라이더 (1900년 ~ 2100년)
    selected_year = st.slider(
        "예측할 연도를 선택하세요",
        min_value=1900,
        max_value=2100,
        value=2026,
        step=1,
    )

    x_val = selected_year - 1908

    # 두 모델별 예측값
    pred_full = slope_full * x_val + intercept_full
    pred_recent = slope_recent * x_val + intercept_recent

    st.markdown(f"### **{selected_year}년** 예상 연평균 기온")

    pred_col1, pred_col2 = st.columns(2)
    with pred_col1:
        st.metric(
            label="전체 기간 모델 기준",
            value=f"{pred_full:.2f} °C",
        )
    with pred_col2:
        st.metric(
            label="최근 20년 모델 기준",
            value=f"{pred_recent:.2f} °C",
            delta=f"{pred_recent - pred_full:+.2f} °C (전체 모델 대비)",
        )

    st.info(
        f"💡 **회귀 방정식 비교**\n\n"
        f"- **전체 기간:** $y = {slope_full:.4f} \\times (\\text{{연도}} - 1908) + {intercept_full:.2f}$\n"
        f"- **최근 20년:** $y = {slope_recent:.4f} \\times (\\text{{연도}} - 1908) + {intercept_recent:.2f}$"
    )

with right_col:
    st.subheader("📊 산점도 및 회귀 직선 비교")

    # 그래프용 연도 범위 (1900~2100)
    years_range = np.arange(1900, 2101)
    x_range = years_range - 1908

    reg_full_y = slope_full * x_range + intercept_full
    reg_recent_y = slope_recent * x_range + intercept_recent

    fig = go.Figure()

    # 1. 관측 데이터 산점도 (전체)
    fig.add_trace(
        go.Scatter(
            x=df_valid["연도"],
            y=df_valid["연평균기온"],
            mode="markers",
            name="실제 관측값 (전체)",
            marker=dict(color="#1f77b4", size=7, opacity=0.6),
            hovertemplate="%{x}년: %{y:.2f}°C<extra></extra>",
        )
    )

    # 2. 최근 20년 데이터 산점도 강조
    fig.add_trace(
        go.Scatter(
            x=df_recent["연도"],
            y=df_recent["연평균기온"],
            mode="markers",
            name="실제 관측값 (최근 20년)",
            marker=dict(
                color="#d62728", size=9, symbol="circle", opacity=0.9
            ),
            hovertemplate="최근 20년 %{x}년: %{y:.2f}°C<extra></extra>",
        )
    )

    # 3. 전체 기간 회귀선
    fig.add_trace(
        go.Scatter(
            x=years_range,
            y=reg_full_y,
            mode="lines",
            name=f"전체 기간 회귀선 (+{rate_full_100y:.2f}°C/100년)",
            line=dict(color="#ff7f0e", width=2.5, dash="dash"),
            hovertemplate="전체 모델 %{x}년: %{y:.2f}°C<extra></extra>",
        )
    )

    # 4. 최근 20년 회귀선
    fig.add_trace(
        go.Scatter(
            x=years_range,
            y=reg_recent_y,
            mode="lines",
            name=f"최근 20년 회귀선 (+{rate_recent_100y:.2f}°C/100년)",
            line=dict(color="#d62728", width=2.5),
            hovertemplate="최근 20년 모델 %{x}년: %{y:.2f}°C<extra></extra>",
        )
    )

    # 5. 선택 연도 예측점 표시
    fig.add_trace(
        go.Scatter(
            x=[selected_year, selected_year],
            y=[pred_full, pred_recent],
            mode="markers+text",
            name=f"선택 연도({selected_year}년)",
            marker=dict(color=["#ff7f0e", "#d62728"], size=12, symbol="star"),
            text=["전체", "최근20년"],
            textposition="top center",
            hovertemplate=f"선택 연도 ({selected_year}년) 예측<extra></extra>",
        )
    )

    # 그래프 레이아웃 설정
    fig.update_layout(
        xaxis_title="연도 (Year)",
        yaxis_title="연평균 기온 (°C)",
        xaxis=dict(range=[1895, 2105], dtick=20),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=40, r=40, t=30, b=40),
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)
