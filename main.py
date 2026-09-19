import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# 웹 앱 기본 설정
st.set_page_config(page_title="영화 흥행 예측기", layout="wide")
st.title("🎬 영화 흥행 예측기 (첫 관측일 시점 예측)")

# 데이터 URL
DAILY_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
MOVIES_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

# 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_preprocess_data():
    df_daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    df_movies = pd.read_csv(MOVIES_URL, encoding="utf-8")
    
    # 1. 일별 박스오피스 표에서 영화별 10위권 첫 등장일 데이터 추출
    # first_date는 YYYYMMDD 형태의 숫자/문자열
    df_movies['first_date_num'] = pd.to_numeric(df_movies['first_date'], errors='coerce')
    
    # 2. daily 표와 movies 표 병합 (수정된 부분: df_daily의 영화 코드 열은 '영화코드'임)
    df_daily_first = pd.merge(
        df_movies[['movieCd', 'first_date_num']],
        df_daily,
        left_on=['movieCd', 'first_date_num'],
        right_on=['영화코드', '날짜'],  # <-- right_on의 'movieCd'를 '영화코드'로 수정
        how='left'
    )
    
    # 3. '상영당 관객 수' 열 계산 (일관객 / 상영횟수)
    df_daily_first['audi_per_show_first'] = np.where(
        df_daily_first['상영횟수'] > 0,
        df_daily_first['일관객'] / df_daily_first['상영횟수'],
        np.nan
    )
    
    # 4. 계산된 '상영당 관객 수'를 df_movies 표에 결합 (동일 영화코드 기준)
    # df_daily_first의 '영화코드'를 기준으로 병합
    df_movies = pd.merge(
        df_movies,
        df_daily_first[['movieCd', 'audi_per_show_first']],
        on='movieCd',
        how='left'
    )
    
    # 파생 변수 결측치는 중앙값으로 보정
    median_val = df_movies['audi_per_show_first'].median()
    df_movies['audi_per_show_first'] = df_movies['audi_per_show_first'].fillna(median_val)
    
    return df_daily, df_movies

df_daily, df_movies = load_and_preprocess_data()

# 1. 기준 기간 확인 및 표시
df_daily['date_str'] = df_daily['날짜'].astype(str)
start_date = df_daily['date_str'].min()
end_date = df_daily['date_str'].max()

start_date_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
end_date_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

st.info(f"📅 **기준 기간:** {start_date_fmt} ~ {end_date_fmt}")

# 2. 영화별 표 상위 10개 행 출력
st.subheader("📋 영화별 데이터 (상위 10개 행, '상영당 관객 수' 포함)")
st.dataframe(df_movies.head(10), use_container_width=True)

# 3. '상영당 관객 수' 히스토그램
st.markdown("---")
st.subheader("📊 첫 관측일 '상영당 관객 수' 분포 (히스토그램)")
st.caption("10위권에 처음 든 날의 `일관객 ÷ 상영횟수` 값의 분포입니다.")

fig_hist = px.histogram(
    df_movies,
    x='audi_per_show_first',
    nbins=40,
    labels={'audi_per_show_first': '첫 관측일 상영당 관객 수 (명/회)'},
    title="상영당 관객 수 분포",
    color_discrete_sequence=['#1f77b4']
)
fig_hist.update_layout(yaxis_title="영화 수 (편)", height=400)
st.plotly_chart(fig_hist, use_container_width=True)

# 4. 데이터 전처리 및 Train/Test 분할
df_sorted = df_movies.sort_values(by="movieCd").reset_index(drop=True)

test_mask = (df_sorted.index % 10) < 3
train_df = df_sorted[~test_mask].copy()
test_df = df_sorted[test_mask].copy()

st.markdown("---")
st.markdown(f"**학습용 영화 수:** `{len(train_df)}`편 | **평가용(테스트) 영화 수:** `{len(test_df)}`편")

# 5. 모델 평가 비교 (기본 3개 변수 vs + 상영당 관객 수)
st.subheader("⚖️ 모델 성능 비교 (결정계수 R²)")

base_features = ['first_scrn', 'first_show', 'peak']
new_features = base_features + ['audi_per_show_first']

y_train = train_df['total_audi']
y_test = test_df['total_audi']

# 모델 A: 기본 3개 변수
X_train_base = train_df[base_features].fillna(0)
X_test_base = test_df[base_features].fillna(0)

model_base = LinearRegression()
model_base.fit(X_train_base, y_train)
y_pred_base = model_base.predict(X_test_base)

r2_base = r2_score(y_test, y_pred_base)
rmse_base = np.sqrt(mean_squared_error(y_test, y_pred_base))

# 모델 B: 기본 3개 변수 + 상영당 관객 수
X_train_new = train_df[new_features].fillna(0)
X_test_new = test_df[new_features].fillna(0)

model_new = LinearRegression()
model_new.fit(X_train_new, y_train)
y_pred_new = model_new.predict(X_test_new)

r2_new = r2_score(y_test, y_pred_new)
rmse_new = np.sqrt(mean_squared_error(y_test, y_pred_new))

# 성적 나란히 표시
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 1️⃣ 기본 변수 (3개)")
    st.caption("변수: `첫 관측일 스크린수`, `첫 관측일 상영횟수`, `성수기 개봉 여부`")
    st.metric("결정계수 (R²)", f"{r2_base:.4f}")
    st.metric("평균 제곱근 오차 (RMSE)", f"{rmse_base:,.0f} 명")

with col2:
    st.markdown("#### 2️⃣ + 상영당 관객 수 추가 (4개)")
    st.caption("변수: 기본 3개 + `상영당 관객 수 (audi_per_show_first)`")
    st.metric("결정계수 (R²)", f"{r2_new:.4f}", delta=f"{r2_new - r2_base:+.4f}")
    st.metric("평균 제곱근 오차 (RMSE)", f"{rmse_new:,.0f} 명", delta=f"{rmse_new - rmse_base:,.0f} 명", delta_color="inverse")

# 6. 산점도 시각화 (새로운 4개 변수 모델 기준)
st.markdown("---")
st.subheader("📉 실제 관객 수 vs 예측 관객 수 (로그 스케일)")

eval_df = test_df.copy()
eval_df['pred_audi'] = y_pred_new

under_1000_mask = eval_df['pred_audi'] < 1000
under_1000_count = under_1000_mask.sum()

eval_df['plot_pred_audi'] = eval_df['pred_audi'].apply(lambda x: 1000 if x < 1000 else x)

if under_1000_count > 0:
    st.caption(f"📌 예측 관객 수가 1,000명보다 작은 영화는 총 **{under_1000_count}편**이며, 그래프 바닥(1,000명 선)에 붙여 표시되었습니다.")

fig_scatter = px.scatter(
    eval_df,
    x='total_audi',
    y='plot_pred_audi',
    hover_data=['movieNm', 'total_audi', 'pred_audi', 'audi_per_show_first'],
    labels={
        'total_audi': '실제 총 관객 수 (명)',
        'plot_pred_audi': '예측 총 관객 수 (명)'
    },
    title="기본 변수 + 상영당 관객 수 모델 예측 결과"
)

min_val = min(eval_df['total_audi'].min(), eval_df['plot_pred_audi'].min())
max_val = max(eval_df['total_audi'].max(), eval_df['plot_pred_audi'].max())

fig_scatter.add_trace(
    go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        name='기준선 (실제 = 예측)',
        line=dict(color='red', dash='dash')
    )
)

fig_scatter.update_xaxes(type="log", title="실제 총 관객 수 (로그 스케일)")
fig_scatter.update_yaxes(type="log", title="예측 총 관객 수 (로그 스케일)")
fig_scatter.update_layout(height=600)

st.plotly_chart(fig_scatter, use_container_width=True)
