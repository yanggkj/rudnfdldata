import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

# 페이지 설정
st.set_page_config(
    page_title="서울 기온 예측기", page_icon="🌡️", layout="wide"
)

st.title("🌡️ 서울 기온 예측기")
st.markdown(
    "서울의 과거 기온 데이터를 분석하여 연도별 평균기온의 추세를 파악하고, 원하는 연도의 평균기온을 예측합니다."
)


# 데이터 로드 및 전처리 캐싱
@st.cache_data
def load_and_preprocess_data():
  url = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
  df = pd.read_csv(url, encoding="utf-8")

  # 날짜를 datetime 형식으로 변환 후 연도 추출
  df["날짜"] = pd.to_datetime(df["날짜"])
  df["연도"] = df["날짜"].dt.year

  # 2025년까지의 데이터만 필터링
  df = df[df["연도"] <= 2025]

  # 결측치 제외 후 연도별 평균기온 및 관측일수 계산
  df_valid = df.dropna(subset=["평균기온"])
  yearly_stats = (
      df_valid.groupby("연도")
      .agg(mean_temp=("평균기온", "mean"), count=("평균기온", "count"))
      .reset_index()
  )

  # 관측일이 300일 미만인 해는 제외
  yearly_filtered = yearly_stats[yearly_stats["count"] >= 300].reset_index(
      drop=True
  )

  return yearly_filtered


try:
  data = load_and_preprocess_data()
except Exception as e:
  st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
  st.stop()

# 회귀 분석 수행 (1908년부터 지난 연수를 독립 변수로 설정)
data["X"] = data["연도"] - 1908
X = data[["X"]]
y = data["mean_temp"]

model = LinearRegression()
model.fit(X, y)

# 상관계수 계산 (연도와 평균기온 간의 상관관계)
correlation = data["연도"].corr(data["mean_temp"])

# --- 화면 상단: 분석 데이터 요약 정보 ---
st.subheader("📊 분석 데이터 요약")
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric("사용한 연도 수", f"{len(data)}년")
with col2:
  st.metric("시작 연도", f"{int(data['연도'].min())}년")
with col3:
  st.metric("끝 연도", f"{int(data['연도'].max())}년")
with col4:
  st.metric("상관계수", f"{correlation:.3f}")

st.markdown("---")

# --- 화면 중단: Plotly 그래프 (산점도 및 회귀 직선) ---
data["회귀예측치"] = model.predict(X)

fig = go.Figure()

# 실제 연평균기온 산점도
fig.add_trace(
    go.Scatter(
        x=data["연도"],
        y=data["mean_temp"],
        mode="markers",
        name="연평균기온 (실제)",
        marker=dict(color="royalblue", size=8),
    )
)

# 회귀 직선
fig.add_trace(
    go.Scatter(
        x=data["연도"],
        y=data["회귀예측치"],
        mode="lines",
        name="회귀 직선",
        line=dict(color="firebrick", width=2),
    )
)

fig.update_layout(
    title="서울 연도별 평균기온 추세 및 회귀선",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    hovermode="x unified",
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 화면 하단: 슬라이더를 통한 연도별 예상 기온 조회 ---
st.subheader("🔮 연도별 예상 기온 조회")
selected_year = st.slider(
    "조회할 연도를 선택하세요", min_value=1900, max_value=2100, value=2026
)

# 선택한 연도 예측값 계산
pred_X = np.array([[selected_year - 1908]])
predicted_temp = model.predict(pred_X)[0]

# 결과를 눈에 띄게 큰 박스로 표시
st.markdown(
    f"""
    <div style="padding: 25px; border-radius: 12px; background-color: #f0f2f6; text-align: center; border: 1px solid #d1d5db;">
        <h3 style="margin: 0; color: #31333F;">{selected_year}년 서울 예상 평균기온</h3>
        <h1 style="margin: 15px 0 0 0; color: #ff4b4b; font-size: 52px;">{predicted_temp:.2f} °C</h1>
    </div>
    """,
    unsafe_allow_html=True,
)
