import re
import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="인천 지역 고등학교 시험기간 급식 칼로리 비교 분석",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 인천 지역 고등학교 시험기간 급식 칼로리 비교 분석")
st.write(
    "인천 가좌고등학교, 인천 동산고등학교, 인천 인화여자고등학교의 시험기간 및 시험 전주 급식 칼로리를 비교/분석합니다."
)

# ==========================================
# 1. 데이터 로드 및 전처리
# ==========================================


@st.cache_data
def load_data():
  """나이스 Open API / CSV 데이터 전처리 및 로드 함수"""
  # 나이스 오픈포털 또는 수집된 CSV 데이터 링크 사용
  # 기본 열 구조: 학교명(SCHUL_NM), 급식일자(MLSV_YMD), 칼로리정보(CAL_INFO) 등

  # [샘플 데이터 구축 - 나이스 데이터 표준 규격 반영]
  schools = ["인천가좌고등학교", "인천동산고등학교", "인천인화여자고등학교"]
  dates_prev = ["20240415", "20240416", "20240417", "20240418", "20240419"]  # 시험전주
  dates_exam = ["20240422", "20240423", "20240424", "20240425", "20240426"]  # 시험기간

  data = []
  import random

  random.seed(42)

  for school in schools:
    for d in dates_prev:
      cal_val = round(random.uniform(750, 950), 1)
      data.append({
          "학교명": school,
          "급식일자": d,
          "칼로리정보": f"{cal_val} Kcal",
          "구분": "시험전주",
      })
    for d in dates_exam:
      cal_val = round(random.uniform(800, 1050), 1)
      data.append({
          "학교명": school,
          "급식일자": d,
          "칼로리정보": f"{cal_val} Kcal",
          "구분": "시험기간",
      })

  df = pd.DataFrame(data)

  # [전처리 1] 날짜 열을 실제 Datetime 객체로 변환
  df["날짜"] = pd.to_datetime(df["급식일자"], format="%Y%m%d")

  # [전처리 2] 칼로리 데이터에서 숫자만 추출하여 정수/실수형 변환 (예: "852.4 Kcal" -> 852.4)
  def extract_calorie(text):
    if pd.isna(text):
      return 0.0
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(text))
    if match:
      return float(match.group(1))
    return 0.0

  df["칼로리(kcal)"] = df["칼로리정보"].apply(extract_calorie)

  return df


df = load_data()

# ==========================================
# 2. 사이드바 - 학교 선택
# ==========================================
st.sidebar.header("🎯 학교 선택")
school_options = ["인천가좌고등학교", "인천동산고등학교", "인천인화여자고등학교"]
selected_school = st.sidebar.selectbox("학교를 선택하세요:", school_options)

# 선택한 학교 데이터 필터링
filtered_df = df[df["학교명"] == selected_school].copy()

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **안내:** 나이스(NEIS) Open API 급식데이터 연동에 맞추어 전처리 알고리즘이"
    " 적용되었습니다."
)

# ==========================================
# [구역 1] 시험기간 vs 시험전주 칼로리 총합 비교
# ==========================================
st.header(
    f"📌 구역 1: {selected_school} - 시험전주 vs 시험기간 칼로리 총합 비교"
)

# 기간별 칼로리 총합 계산
summary_df = filtered_df.groupby("구분")["칼로리(kcal)"].sum().reset_index()
summary_df["칼로리(kcal)"] = summary_df["칼로리(kcal)"].round(1)

# 막대 그래프 생성 (Plotly)
fig1 = px.bar(
    summary_df,
    x="구분",
    y="칼로리(kcal)",
    color="구분",
    text="칼로리(kcal)",
    title=f"[{selected_school}] 시험전주 vs 시험기간 총 칼로리 비교",
    labels={"구분": "기간 구분", "칼로리(kcal)": "총 칼로리 (kcal)"},
    color_discrete_map={"시험전주": "#636EFA", "시험기간": "#EF553B"},
)

fig1.update_traces(
    hovertemplate="<b>%{x}</b><br>총 칼로리: %{y:,} kcal<extra></extra>",
    texttemplate="%{y:,} kcal",
    textposition="outside",
)

fig1.update_layout(
    showlegend=False, yaxis_range=[0, summary_df["칼로리(kcal)"].max() * 1.2]
)

st.plotly_chart(fig1, use_container_width=True)

# 해석 문구
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** {selected_school}의 시험기간 일주일 동안 제공된"
    " 급식 칼로리 총합과 시험 전주 일주일 총합을 비교하여, 시험 기간 특식이나 열량"
    " 제공 변화 패턴을 한눈에 확인할 수 있습니다."
)

st.markdown("---")

# ==========================================
# [구역 2] 상세 일자별 칼로리 변화 추이
# ==========================================
st.header(f"📌 구역 2: {selected_school} - 일자별 칼로리 변화 추이")

# 날짜 순으로 정렬
trend_df = filtered_df.sort_values("날짜")

# 선 그래프 생성 (Plotly)
fig2 = px.line(
    trend_df,
    x="날짜",
    y="칼로리(kcal)",
    color="구분",
    markers=True,
    title=f"[{selected_school}] 날짜별 급식 칼로리 추이",
    labels={
        "날짜": "급식 제공일자",
        "칼로리(kcal)": "일일 칼로리 (kcal)",
        "구분": "구분",
    },
    color_discrete_map={"시험전주": "#636EFA", "시험기간": "#EF553B"},
)

fig2.update_traces(
    hovertemplate=(
        "<b>날짜:</b> %{x|%Y-%m-%d}<br><b>칼로리:</b> %{y} kcal<extra></extra>"
    )
)

fig2.update_xaxes(dtick="86400000.0", tickformat="%Y-%m-%d")

st.plotly_chart(fig2, use_container_width=True)

# 해석 문구
st.info(
    "💡 **이 그래프로 알 수 있는 것:** 시험전주와 시험기간 동안의 일별 급식 칼로리"
    " 변동 추이를 확인하여 특정 날짜에 고칼로리 또는 저칼로리 급식이 집중되었는지"
    " 상세히 분석할 수 있습니다."
)

st.markdown("---")

# ==========================================
# [구역 3] 추후 영양소 및 타 학교 비교 추가 구역
# ==========================================
st.header("📌 구역 3: (추가 예정) 기타 영양소 분석 및 학교 간 비교")
st.caption(
    "※ 탄수화물, 단백질, 지방 등 추가 영양소 분석 및 3개 학교 동시 비교 그래프가"
    " 들어갈 확장용 구역입니다."
)
