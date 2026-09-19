import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# 웹 앱 기본 설정
st.set_page_config(page_title="영화 흥행 예측기", layout="wide")
st.title("🎬 영화 흥행 예측기")

# 데이터 URL
DAILY_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
MOVIES_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

# 데이터 로드 함수
@st.cache_data
def load_data():
    df_daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    df_movies = pd.read_csv(MOVIES_URL, encoding="utf-8")
    return df_daily, df_movies

df_daily, df_movies = load_data()

# 1. 데이터 안내 경고 메시지 (사후 집계값 관련)
st.warning(
    "⚠️ **데이터 관련 주의사항**\n\n"
    "본 데이터셋에 포함된 '첫 주 관객 수(first_week_audi)' 및 '10위권 진입 일수(days_in_top10)' 등은 **영화 개봉 이후 상영 과정에서 수집된 사후 집계값(Ex-post data)**입니다. "
    "따라서 해당 변수들을 포함한 모델 예측 결과는 **실제 영화 개봉 전(Pre-release) 시점의 순수 예측 성능을 의미하지 않음**을 유의하시기 바랍니다."
)

# 2. 기준 기간 확인 및 표시
df_daily['date_str'] = df_daily['날짜'].astype(str)
start_date = df_daily['date_str'].min()
end_date = df_daily['date_str'].max()

start_date_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
end_date_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

st.info(f"📅 **기준 기간:** {start_date_fmt} ~ {end_date_fmt}")

# 3. 영화별 표 상위 10개 행 출력
st.subheader("📋 영화별 데이터 (상위 10개 행)")
st.dataframe(df_movies.head(10), use_container_width=True)

# 4. 데이터 전처리 및 Train/Test 분할
df_sorted = df_movies.sort_values(by="movieCd").reset_index(drop=True)

test_mask = (df_sorted.index % 10) < 3
train_df = df_sorted[~test_mask].copy()
test_df = df_sorted[test_mask].copy()

st.markdown("---")
st.markdown(f"**학습용 영화 수:** `{len(train_df)}`편 | **평가용(테스트) 영화 수:** `{len(test_df)}`편")

# 5. 기본 3개 변수 vs 첫 주 관객 수 추가 모델 비교
st.subheader("📊 기본 변수 vs 첫 주 관객 수 추가 비교")

base_features = ['first_scrn', 'first_show', 'peak']
added_features = base_features + ['first_week_audi']

# 모델 1: 기본 3개 변수
X_train_base = train_df[base_features].fillna(0)
X_test_base = test_df[base_features].fillna(0)
y_train = train_df['total_audi']
y_test = test_df['total_audi']

model_base = LinearRegression()
model_base.fit(X_train_base, y_train)
y_pred_base = model_base.predict(X_test_base)

r2_base = r2_score(y_test, y_pred_base)
rmse_base = np.sqrt(mean_squared_error(y_test, y_pred_base))

# 모델 2: 기본 3개 변수 + 첫 주 관객 수
X_train_added = train_df[added_features].fillna(0)
X_test_added = test_df[added_features].fillna(0)

model_added = LinearRegression()
model_added.fit(X_train_added, y_train)
y_pred_added = model_added.predict(X_test_added)

r2_added = r2_score(y_test, y_pred_added)
rmse_added = np.sqrt(mean_squared_error(y_test, y_pred_added))

# 점수 나란히 표시
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 1️⃣ 기본 변수 (3개)")
    st.caption("사용 변수: `첫 관측일 스크린수`, `첫 관측일 상영횟수`, `성수기 개봉 여부`")
    st.metric("결정계수 (R²)", f"{r2_base:.4f}")
    st.metric("평균 제곱근 오차 (RMSE)", f"{rmse_base:,.0f} 명")

with col2:
    st.markdown("#### 2️⃣ + 첫 주 관객 수 추가 (4개)")
    st.caption("사용 변수: 기본 3개 + `첫 주 관객 수`")
    st.metric("결정계수 (R²)", f"{r2_added:.4f}", delta=f"{r2_added - r2_base:+.4f}")
    st.metric("평균 제곱근 오차 (RMSE)", f"{rmse_added:,.0f} 명", delta=f"{rmse_added - rmse_base:,.0f} 명", delta_color="inverse")

# 6. 사용자 선택 커스텀 모델 시각화
st.sidebar.header("⚙️ 커스텀 모델 변수 선택")

possible_features = [
    'first_scrn', 'first_show', 'peak', 
    'first_week_audi', 'days_in_top10'
]

feature_labels = {
    'first_scrn': '첫 관측일 스크린수 (first_scrn)',
    'first_show': '첫 관측일 상영횟수 (first_show)',
    'peak': '성수기 개봉 여부 (peak)',
    'first_week_audi': '첫 주 관객수 (first_week_audi)',
    'days_in_top10': '10위권 진입 일수 (days_in_top10)'
}

selected_features = []
for feat in possible_features:
    if st.sidebar.checkbox(feature_labels[feat], value=True):
        selected_features.append(feat)

if not selected_features:
    st.warning("⚠️ 사이드바에서 최소 하나의 변수를 선택해야 아래 산점도가 출력됩니다.")
else:
    X_train_custom = train_df[selected_features].fillna(0)
    X_test_custom = test_df[selected_features].fillna(0)
    
    model_custom = LinearRegression()
    model_custom.fit(X_train_custom, y_train)
    y_pred_custom = model_custom.predict(X_test_custom)
    
    eval_df = test_df.copy()
    eval_df['pred_audi'] = y_pred_custom
    
    under_1000_mask = eval_df['pred_audi'] < 1000
    under_1000_count = under_1000_mask.sum()
    
    eval_df['plot_pred_audi'] = eval_df['pred_audi'].apply(lambda x: 1000 if x < 1000 else x)
    
    st.markdown("---")
    st.subheader("📉 실제 관객 수 vs 선택 변수 모델 예측 관객 수 (로그 스케일)")
    if under_1000_count > 0:
        st.caption(f"📌 예측 관객 수가 1,000명보다 작은 영화는 총 **{under_1000_count}편**이며, 그래프 바닥(1,000명 선)에 붙여 표시되었습니다.")

    fig = px.scatter(
        eval_df,
        x='total_audi',
        y='plot_pred_audi',
        hover_data=['movieNm', 'total_audi', 'pred_audi'],
        labels={
            'total_audi': '실제 총 관객 수 (명)',
            'plot_pred_audi': '예측 총 관객 수 (명)'
        },
        title="실제 관객 수 대비 예측 관객 수 분포"
    )

    min_val = min(eval_df['total_audi'].min(), eval_df['plot_pred_audi'].min())
    max_val = max(eval_df['total_audi'].max(), eval_df['plot_pred_audi'].max())
    
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='기준선 (실제 = 예측)',
            line=dict(color='red', dash='dash')
        )
    )

    fig.update_xaxes(type="log", title="실제 총 관객 수 (로그 스케일)")
    fig.update_yaxes(type="log", title="예측 총 관객 수 (로그 스케일)")
    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True)
