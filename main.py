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

# 1. 기준 기간 확인 및 표시
df_daily['date_str'] = df_daily['날짜'].astype(str)
start_date = df_daily['date_str'].min()
end_date = df_daily['date_str'].max()

# YYYY-MM-DD 형식 변환
start_date_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
end_date_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

st.info(f"**기준 기간:** {start_date_fmt} ~ {end_date_fmt}")

# 2. 영화별 표 상위 10개 행 출력
st.subheader("📋 영화별 데이터 (상위 10개 행)")
st.dataframe(df_movies.head(10), use_container_width=True)

# 3. 데이터 전처리 및 Train/Test 분할
# 영화코드(movieCd) 순 정렬 (모든 영화 사용)
df_sorted = df_movies.sort_values(by="movieCd").reset_index(drop=True)

# 열 편마다 앞의 세 편(인덱스 % 10 < 3)을 테스트용으로 분리
test_mask = (df_sorted.index % 10) < 3
train_df = df_sorted[~test_mask].copy()
test_df = df_sorted[test_mask].copy()

# 데이터 분할 현황 안내
st.markdown("---")
st.markdown(f"**학습용 영화 수:** `{len(train_df)}`편 | **평가용(테스트) 영화 수:** `{len(test_df)}`편")

# 4. 피처 선택 (사용자가 체크박스로 지정)
st.sidebar.header("⚙️ 모델 설정")
st.sidebar.write("학습에 사용할 변수를 선택하세요:")

possible_features = [
    'first_scrn', 'first_show', 'peak', 
    'first_week_audi', 'days_in_top10'
]

# 한글 라벨 제공
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
    st.warning("⚠️ 최소 하나의 변수를 선택해야 모델 학습이 진행됩니다.")
else:
    # 5. 다중 회귀 모델 학습
    X_train = train_df[selected_features]
    y_train = train_df['total_audi']
    
    X_test = test_df[selected_features]
    y_test = test_df['total_audi']
    
    # 결측치 처리 (0으로 채움)
    X_train = X_train.fillna(0)
    X_test = X_test.fillna(0)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # 6. 평가 예측
    y_pred = model.predict(X_test)
    
    # 평가 지표 산출
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # 평가 결과 출력
    st.subheader("📊 모델 평가 결과")
    col1, col2 = st.columns(2)
    col1.metric("결정계수 (R² Score)", f"{r2:.4f}")
    col2.metric("평균 제곱근 오차 (RMSE)", f"{rmse:,.0f} 명")
    
    # 7. plotly 산점도 시각화 준비
    eval_df = test_df.copy()
    eval_df['pred_audi'] = y_pred
    
    # 1,000명 미만 예측값 처리
    under_1000_mask = eval_df['pred_audi'] < 1000
    under_1000_count = under_1000_mask.sum()
    
    # 그래프 표현을 위해 1,000 미만 예측값은 1,000으로 보정 (로그 스케일 바닥 표시)
    eval_df['plot_pred_audi'] = eval_df['pred_audi'].apply(lambda x: 1000 if x < 1000 else x)
    
    st.markdown("---")
    st.subheader("📉 실제 관객 수 vs 예측 관객 수 (로그 스케일)")
    if under_1000_count > 0:
        st.caption(f"📌 예측 관객 수가 1,000명보다 작은 영화는 총 **{under_1000_count}편**이며, 그래프 바닥(1,000명 선)에 붙여 표시되었습니다.")

    # 산점도 생성
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

    # 실젯값과 예측값이 같은 대각선 추가 (1:1 선)
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

    # 양 축 로그 스케일 설정
    fig.update_xaxes(type="log", title="실제 총 관객 수 (로그 스케일)")
    fig.update_yaxes(type="log", title="예측 총 관객 수 (로그 스케일)")
    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True)
