import itertools
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

# 5. 사이드바 - 변수 선택
st.sidebar.header("⚙️ 변수 조합 탐색 설정")
st.sidebar.write("조합 비교에 포함할 후보 변수들을 선택하세요:")

possible_features = [
    'first_scrn', 'first_show', 'peak', 
    'first_week_audi', 'days_in_top10'
]

feature_labels = {
    'first_scrn': '첫 관측일 스크린수',
    'first_show': '첫 관측일 상영횟수',
    'peak': '성수기 개봉 여부',
    'first_week_audi': '첫 주 관객수',
    'days_in_top10': '10위권 진입 일수'
}

selected_candidate_features = []
for feat in possible_features:
    if st.sidebar.checkbox(f"{feature_labels[feat]} ({feat})", value=True):
        selected_candidate_features.append(feat)

if not selected_candidate_features:
    st.warning("⚠️ 사이드바에서 최소 하나 이상의 변수를 선택해 주세요.")
else:
    # 6. 모든 가능한 변수 조합 생성 및 평가
    y_train = train_df['total_audi']
    y_test = test_df['total_audi']

    combination_results = []

    # 1개 변수 조합부터 N개 변수 조합까지 생성
    for k in range(1, len(selected_candidate_features) + 1):
        for combo in itertools.combinations(selected_candidate_features, k):
            combo_list = list(combo)
            
            X_tr = train_df[combo_list].fillna(0)
            X_te = test_df[combo_list].fillna(0)
            
            mdl = LinearRegression()
            mdl.fit(X_tr, y_train)
            preds = mdl.predict(X_te)
            
            r2_val = r2_score(y_test, preds)
            rmse_val = np.sqrt(mean_squared_error(y_test, preds))
            
            combo_names = [feature_labels[col] for col in combo_list]
            
            combination_results.append({
                "변수 개수": k,
                "사용 변수 목록": ", ".join(combo_names),
                "변수 코드": ", ".join(combo_list),
                "결정계수 (R²)": r2_val,
                "평균 제곱근 오차 (RMSE)": rmse_val,
                "_raw_combo": combo_list,
                "_model": mdl
            })

    results_df = pd.DataFrame(combination_results)
    # R² 내림차순 정렬
    results_df = results_df.sort_values(by="결정계수 (R²)", ascending=False).reset_index(drop=True)

    # 7. 변수 조합별 점수 비교 표 및 주요 지표 출력
    st.subheader("🏆 변수 조합별 성능 비교 (R² 기준 내림차순)")
    
    best_combo = results_df.iloc[0]
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("최고 결정계수 (Best R²)", f"{best_combo['결정계수 (R²)']:.4f}")
    col_m2.metric("최저 RMSE", f"{best_combo['평균 제곱근 오차 (RMSE)']:,.0f} 명")
    col_m3.metric("최적 변수 조합", f"{best_combo['변수 개수']}개 변수 사용")
    
    st.caption(f"🥇 **최적 조합:** {best_combo['사용 변수 목록']}")

    # 결과 테이블 표시
    st.dataframe(
        results_df[["변수 개수", "사용 변수 목록", "결정계수 (R²)", "평균 제곱근 오차 (RMSE)"]].style.format({
            "결정계수 (R²)": "{:.4f}",
            "평균 제곱근 오차 (RMSE)": "{:,.0f}"
        }),
        use_container_width=True
    )

    # 8. 시각화할 조합 선택 (라디오 버튼)
    st.markdown("---")
    st.subheader("📉 선택한 변수 조합의 예측 산점도 (로그 스케일)")
    
    combo_options = [
        f"[{row['변수 개수']}개 변수] {row['사용 변수 목록']} (R²: {row['결정계수 (R²)']:.4f})" 
        for _, row in results_df.iterrows()
    ]
    
    selected_option_idx = st.selectbox(
        "시각화로 확인할 변수 조합을 선택하세요:", 
        options=range(len(combo_options)),
        format_func=lambda x: combo_options[x]
    )
    
    selected_row = results_df.iloc[selected_option_idx]
    selected_features = selected_row["_raw_combo"]
    
    # 선택된 조합으로 예측 수행
    X_test_selected = test_df[selected_features].fillna(0)
    selected_model = selected_row["_model"]
    y_pred_selected = selected_model.predict(X_test_selected)
    
    eval_df = test_df.copy()
    eval_df['pred_audi'] = y_pred_selected
    
    under_1000_mask = eval_df['pred_audi'] < 1000
    under_1000_count = under_1000_mask.sum()
    
    # 1,000 미만 예측값 처리 (그래프 바닥 1,000으로 고정)
    eval_df['plot_pred_audi'] = eval_df['pred_audi'].apply(lambda x: 1000 if x < 1000 else x)
    
    if under_1000_count > 0:
        st.caption(f"📌 예측 관객 수가 1,000명보다 작은 영화는 총 **{under_1000_count}편**이며, 그래프 바닥(1,000명 선)에 붙여 표시되었습니다.")

    # Plotly 산점도
    fig = px.scatter(
        eval_df,
        x='total_audi',
        y='plot_pred_audi',
        hover_data=['movieNm', 'total_audi', 'pred_audi'],
        labels={
            'total_audi': '실제 총 관객 수 (명)',
            'plot_pred_audi': '예측 총 관객 수 (명)'
        },
        title=f"실제 관객 수 대비 예측 관객 수 분포 ({selected_row['사용 변수 목록']})"
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
