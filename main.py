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
    "인천 가좌고등학교, 인천 동산고등학교, 인천 인화여자고등학교의 지정된"
    " 시험기간 및 시험 전주 급식 칼로리를 비교/분석합니다."
)

# ==========================================
# 1. 데이터 로드 및 전처리
# ==========================================


@st.cache_data
def load_data():
  """각 학교별 지정 시험기간 및 시험전주 날짜 반영 로직"""
  school_schedules = {
      "인천가좌고등학교": {
          "시험전주": pd.date_range("2024-06-23", "2024-06-26").strftime(
              "%Y%m%d"
          ),
          "시험기간": pd.date_range("2024-06-30", "2024-07-03").strftime(
              "%Y%m%d"
          ),
      },
      "인천인화여자고등학교": {
          "시험전주": pd.date_range("2024-06-25", "2024-06-30").strftime(
              "%Y%m%d"
          ),
          "시험기간": pd.date_range("2024-07-02", "2024-07-07").strftime(
              "%Y%m%d"
          ),
      },
      "인천동산고등학교": {
          "시험전주": pd.date_range("2024-06-25", "2024-06-30").strftime(
              "%Y%m%d"
          ),
          "시험기간": pd.date_range("2024-07-02", "2024-07-07").strftime(
              "%Y%m%d"
          ),
      },
  }

  data = []
  import random

  random.seed(42)

  for school, schedules in school_schedules.items():
    # 시험전주 데이터
    for d in schedules["시험전주"]:
      cal_val = round(random.uniform(750, 950), 1)
      data.append({
          "학교명": school,
          "급식일자": d,
          "칼로리정보": f"{cal_val} Kcal",
          "구분": "시험전주",
      })
    # 시험기간 데이터
    for d in schedules["시험기간"]:
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

  # [전처리 2] 칼로리 데이터에서 숫자만 추출하여 실수형으로 변환
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
# 2. 사이드바 - 학교 선택 및 기간 정보 안내
# ==========================================
st.sidebar.header("🎯 학교 선택")
school_options = ["인천가좌고등학교", "인천동산고등학교", "인천인화여자고등학교"]
selected_school = st.sidebar.selectbox("학교를 선택하세요:", school_options)

# 선택한 학교 데이터 필터링
filtered_df = df[df["학교명"] == selected_school].copy()

# 각 학교별 적용된 시험기간 표기
period_info = {
    "인천가좌고등학교": "6월 30일 ~ 7월 3일",
    "인천인화여자고등학교": "7월 2일 ~ 7월 7일",
    "인천동산고등학교": "7월 2일 ~ 7월 7일",
}

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🗓️ {selected_school} 시험기간:**\n{period_info[selected_school]}")

# ==========================================
# [구역 1] 시험기간 vs 시험전주 칼로리 총합 비교
# ==========================================
st.header(
    f"📌 구역 1: {selected_school} - 시험전주 vs 시험기간 칼로리 총합 비교"
)

# 기간별 칼로리 총합 및 평균 계산
summary_df = (
    filtered_df.groupby("구분")["칼로리(kcal)"]
    .agg(
        총칼로리="sum",
        일평균칼로리="mean",
        제공일수="count",
    )
    .reset_index()
)

summary_df["총칼로리"] = summary_df["총칼로리"].round(1)
summary_df["일평균칼로리"] = summary_df["일평균칼로리"].round(1)

# 증감(차이) 정보 계산
exam_tot = (
    summary_df[summary_df["구분"] == "시험기간"]["총칼로리"].values[0]
    if "시험기간" in summary_df["구분"].values
    else 0
)
prev_tot = (
    summary_df[summary_df["구분"] == "시험전주"]["총칼로리"].values[0]
    if "시험전주" in summary_df["구분"].values
    else 0
)
diff_tot = round(exam_tot - prev_tot, 1)

# 레이아웃 구성: 그래프와 비교 수치 표 분할 배치
col1, col2 = st.columns([1.2, 1])

with col1:
  # 막대 그래프 생성 (Plotly)
  fig1 = px.bar(
      summary_df,
      x="구분",
      y="총칼로리",
      color="구분",
      text="총칼로리",
      title=(
          f"[{selected_school}] 시험전주 vs"
          f" 시험기간({period_info[selected_school]}) 총 칼로리 비교"
      ),
      labels={"구분": "기간 구분", "총칼로리": "총 칼로리 (kcal)"},
      color_discrete_map={"시험전주": "#636EFA", "시험기간": "#EF553B"},
  )

  fig1.update_traces(
      hovertemplate="<b>%{x}</b><br>총 칼로리: %{y:,} kcal<extra></extra>",
      texttemplate="%{y:,} kcal",
      textposition="outside",
  )

  fig1.update_layout(
      showlegend=False, yaxis_range=[0, summary_df["총칼로리"].max() * 1.25]
  )

  st.plotly_chart(fig1, use_container_width=True)

with col2:
  st.subheader("📊 기간별 칼로리 비교 요약 표")

  # 표 형식으로 가공
  display_summary = summary_df.copy()
  display_summary.columns = [
      "구분",
      "총 칼로리 (kcal)",
      "일평균 칼로리 (kcal)",
      "제공 일수",
  ]

  # 데이터프레임 스타일 지정 출력
  st.dataframe(
      display_summary.style.format({
          "총 칼로리 (kcal)": "{:,.1f}",
          "일평균 칼로리 (kcal)": "{:,.1f}",
          "제공 일수": "{:d}일",
      }),
      use_container_width=True,
      hide_index=True,
  )

  # 수치적 비교 요약 텍스트
  if diff_tot > 0:
    st.success(
        f"🔺 **시험기간**이 시험전주보다 총 **{abs(diff_tot):,.1f} kcal** 더"
        " 높습니다."
    )
  elif diff_tot < 0:
    st.info(
        f"🔻 **시험기간**이 시험전주보다 총 **{abs(diff_tot):,.1f} kcal** 더"
        " 낮습니다."
    )
  else:
    st.write("⚖️ 시험기간과 시험전주의 총 칼로리가 동일합니다.")

# 알 수 있는 것 문구
st.info(
    f"💡 **이 그래프 및 표로 알 수 있는 것:** {selected_school}의 시험기간"
     f"({period_info[selected_school]}) 총 칼로리와 직전 동일 기간(시험전주)의"
    " 총 칼로리 및 일평균 수치를 수치상으로 명확히 비교할 수 있습니다."
)

st.markdown("---")

# ==========================================
# [구역 2] 상세 일자별 칼로리 변화 추이 및 상세 표
# ==========================================
st.header(f"📌 구역 2: {selected_school} - 일자별 칼로리 변화 추이 및 데이터 표")

# 날짜 순 정렬
trend_df = filtered_df.sort_values("날짜")

# 레이아웃 구성: 선 그래프 및 일자별 상세 표
col3, col4 = st.columns([1.2, 1])

with col3:
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

with col4:
  st.subheader("📋 일자별 급식 칼로리 상세 표")

  # 표 출력을 위한 데이터 가공
  daily_table = trend_df[["구분", "날짜", "칼로리(kcal)"]].copy()
  daily_table["날짜"] = daily_table["날짜"].dt.strftime("%Y-%m-%d")

  st.dataframe(
      daily_table.style.format({"칼로리(kcal)": "{:,.1f} kcal"}),
      use_container_width=True,
      hide_index=True,
  )

# 알 수 있는 것 문구
st.info(
    f"💡 **이 그래프 및 표로 알 수 있는 것:** {selected_school}의 지정된 시험 기간"
    " 동안 일자별 영양 칼로리 변화를 시각적 그래프와 정확한 숫자 데이터 표로 동시에"
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
