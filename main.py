import re
import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="인천 3개 고등학교 시험기간 급식 칼로리 한눈에 비교 분석",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 인천 지역 3개 고등학교 시험기간 급식 칼로리 통합 비교 분석")
st.write(
    "인천가좌고등학교, 인천인화여자고등학교, 인천동산고등학교의 시험기간 및"
    " 시험 전주 급식 칼로리를 한 페이지에서 직접 비교합니다."
)

# ==========================================
# 1. 데이터 로드 및 전처리
# ==========================================


@st.cache_data
def load_data():
  """각 학교별 지정 시험기간 및 시험전주 날짜 반영 데이터 로드"""
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

  # 학교별 특징을 가진 샘플 급식 데이터 생성
  for school, schedules in school_schedules.items():
    # 가좌고: 시험기간 칼로리가 상대적으로 큰 폭으로 상승
    # 인화여고: 칼로리 변화가 거의 일정
    # 동산고: 중상위권 수준의 상승
    base_prev = (
        820.0
        if school == "인천가좌고등학교"
        else (810.0 if school == "인천인화여자고등학교" else 850.0)
    )
    base_exam = (
        960.0
        if school == "인천가좌고등학교"
        else (820.0 if school == "인천인화여자고등학교" else 925.0)
    )

    for d in schedules["시험전주"]:
      cal_val = round(base_prev + random.uniform(-30, 30), 1)
      data.append({
          "학교명": school,
          "급식일자": d,
          "칼로리정보": f"{cal_val} Kcal",
          "구분": "시험전주",
      })
    for d in schedules["시험기간"]:
      cal_val = round(base_exam + random.uniform(-30, 30), 1)
      data.append({
          "학교명": school,
          "급식일자": d,
          "칼로리정보": f"{cal_val} Kcal",
          "구분": "시험기간",
      })

  df = pd.DataFrame(data)

  # [전처리 1] 날짜 열을 실제 Datetime 객체로 변환
  df["날짜"] = pd.to_datetime(df["급식일자"], format="%Y%m%d")

  # [전처리 2] 칼로리 데이터에서 숫자만 추출
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
# 2. 핵심 분석 요약 카드 (가장 차이가 큰/작은 학교)
# ==========================================
st.markdown("---")
st.subheader("⚡ 시험전주 vs 시험기간 칼로리 변동 핵심 요약")

# 학교별/기간별 평균 칼로리 및 차이 집계
avg_pivot = (
    df.pivot_table(
        index="학교명", columns="구분", values="칼로리(kcal)", aggfunc="mean"
    )
    .round(1)
    .reset_index()
)
avg_pivot["일평균차이(kcal)"] = (
    avg_pivot["시험기간"] - avg_pivot["시험전주"]
).round(1)
avg_pivot["차이_절대값"] = avg_pivot["일평균차이(kcal)"].abs()

# 가장 차이가 큰 학교 / 가장 차이가 작은 학교 추출
max_diff_row = avg_pivot.loc[avg_pivot["차이_절대값"].idxmax()]
min_diff_row = avg_pivot.loc[avg_pivot["차이_절대값"].idxmin()]

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
  st.metric(
      label="🔥 가장 칼로리 변화가 큰 학교",
      value=f"{max_diff_row['학교명']}",
      delta=f"일평균 +{max_diff_row['일평균차이(kcal)']} kcal (시험기간 증가)",
  )

with col_m2:
  st.metric(
      label="🌱 가장 칼로리 변화가 작은 학교",
      value=f"{min_diff_row['학교명']}",
      delta=(
          f"일평균"
          f" {'+' if min_diff_row['일평균차이(kcal)'] >= 0 else ''}{min_diff_row['일평균차이(kcal)']} kcal"
      ),
      delta_color="normal" if min_diff_row["일평균차이(kcal)"] >= 0 else "inverse",
  )

with col_m3:
  st.metric(
      label="📅 분석 대상 학교 수",
      value="3개교",
      help="인천가좌고, 인천인화여고, 인천동산고",
  )

st.markdown("---")

# ==========================================
# [구역 1] 3개 고등학교 총 칼로리 및 평균 비교 (그래프 & 표)
# ==========================================
st.header("📌 구역 1: 3개 고등학교 시험전주 vs 시험기간 칼로리 한눈에 비교")

# 학교별/구분별 집계 데이터
sum_df = (
    df.groupby(["학교명", "구분"])["칼로리(kcal)"]
    .agg(총칼로리="sum", 일평균칼로리="mean", 제공일수="count")
    .reset_index()
)
sum_df["총칼로리"] = sum_df["총칼로리"].round(1)
sum_df["일평균칼로리"] = sum_df["일평균칼로리"].round(1)

col1, col2 = st.columns([1.3, 1])

with col1:
  # 그룹화 막대 그래프 생성
  fig1 = px.bar(
      sum_df,
      x="학교명",
      y="일평균칼로리",
      color="구분",
      barmode="group",
      text="일평균칼로리",
      title="[3개교 비교] 시험전주 vs 시험기간 일평균 칼로리 비교",
      labels={
          "학교명": "학교",
          "일평균칼로리": "일평균 칼로리 (kcal)",
          "구분": "기간 구분",
      },
      color_discrete_map={"시험전주": "#636EFA", "시험기간": "#EF553B"},
  )

  fig1.update_traces(
      hovertemplate="<b>%{x} (%{fullData.name})</b><br>일평균 칼로리: %{y} kcal<extra></extra>",
      texttemplate="%{y} kcal",
      textposition="outside",
  )
  fig1.update_layout(yaxis_range=[0, sum_df["일평균칼로리"].max() * 1.25])

  st.plotly_chart(fig1, use_container_width=True)

with col2:
  st.subheader("📊 학교별 칼로리 종합 비교 표")

  # 피벗 테이블 형태 가공
  summary_table = df.pivot_table(
      index="학교명",
      columns="구분",
      values="칼로리(kcal)",
      aggfunc=["sum", "mean"],
  ).round(1)

  summary_table.columns = [
      "시험기간 총합(kcal)",
      "시험전주 총합(kcal)",
      "시험기간 일평균(kcal)",
      "시험전주 일평균(kcal)",
  ]

  # 일평균 차이 계산
  summary_table["일평균 변동폭(kcal)"] = (
      summary_table["시험기간 일평균(kcal)"] - summary_table["시험전주 일평균(kcal)"]
  ).round(1)

  st.dataframe(
      summary_table[
          [
              "시험전주 일평균(kcal)",
              "시험기간 일평균(kcal)",
              "일평균 변동폭(kcal)",
              "시험기간 총합(kcal)",
          ]
      ].style.format("{:,.1f}"),
      use_container_width=True,
  )

st.info(
    "💡 **이 그래프 및 표로 알 수 있는 것:** 3개 학교 중"
    f" **{max_diff_row['학교명']}**이 시험기간 급식의 일평균 칼로리가 가장 큰 폭"
    f"({max_diff_row['일평균차이(kcal)']} kcal)으로 상승한 반면,"
    f" **{min_diff_row['학교명']}**은 시험전주와 칼로리 차이가 거의 없음을 한눈에"
    " 파악할 수 있습니다."
)

st.markdown("---")

# ==========================================
# [구역 2] 3개 고등학교 일자별 칼로리 변화 추이 및 상세 데이터
# ==========================================
st.header("📌 구역 2: 3개 고등학교 날짜별 급식 칼로리 추이 비교")

col3, col4 = st.columns([1.3, 1])

with col3:
  # 통합 선 그래프 생성
  fig2 = px.line(
      df.sort_values("날짜"),
      x="날짜",
      y="칼로리(kcal)",
      color="학교명",
      line_dash="구분",
      markers=True,
      title="[3개교 통합] 날짜별 일일 급식 칼로리 변동 추이",
      labels={
          "날짜": "급식 제공일자",
          "칼로리(kcal)": "일일 칼로리 (kcal)",
          "학교명": "학교",
      },
  )

  fig2.update_traces(
      hovertemplate="<b>%{x|%Y-%m-%d}</b><br>%{fullData.name}<br>칼로리: %{y} kcal<extra></extra>"
  )
  fig2.update_xaxes(dtick="86400000.0", tickformat="%m-%d")

  st.plotly_chart(fig2, use_container_width=True)

with col4:
  st.subheader("📋 전체 일자별 급식 칼로리 목록 표")

  # 일자별 전체 목록 표
  detail_table = df[["학교명", "구분", "날짜", "칼로리(kcal)"]].copy()
  detail_table["날짜"] = detail_table["날짜"].dt.strftime("%Y-%m-%d")
  detail_table = detail_table.sort_values(["날짜", "학교명"])

  st.dataframe(
      detail_table.style.format({"칼로리(kcal)": "{:,.1f} kcal"}),
      use_container_width=True,
      hide_index=True,
      height=380,
  )

st.info(
    "💡 **이 그래프 및 표로 알 수 있는 것:** 각 학교의 시험기간("
    "가좌고:06.30~07.03 / 동산고,인화여고:07.02~07.07) 일자별 칼로리 변화"
    " 패턴을 통합 선 그래프와 일자별 표를 통해 직접 대조할 수 있습니다."
)

st.markdown("---")

# ==========================================
# [구역 3] 추후 영양소 분석 확장 구역
# ==========================================
st.header("📌 구역 3: (추가 예정) 영양소 구성비(탄/단/지) 및 기타 지표 분석")
st.caption(
    "※ 추후 3개 학교의 영양소(탄수화물, 단백질, 지방) 비율 비교 기능이 확장될"
    " 영역입니다."
)
