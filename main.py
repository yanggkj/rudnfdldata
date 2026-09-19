# app.py
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px

# 1. 페이지 설정 (탭 제목 및 아이콘 설정)
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

# 2. 메인 타이틀 및 아이콘
st.title("🎬 영화 유형 나누기")
st.markdown("KOBIS 영화 데이터를 활용하여 비지도 학습(K-Means) 방식으로 영화를 유형별로 그룹화합니다.")

# 3. 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url, encoding="utf-8")
    
    # 롱런 지수 계산: 누적 관객 / 첫 주 관객
    # first_week_audi가 0인 경우 및 결측치 처리를 위해 먼저 제외 조건 확인
    df = df.dropna(subset=['first_scrn', 'total_audi', 'days_in_top10', 'first_week_audi']).copy()
    df = df[df['first_week_audi'] > 0].copy()
    
    # 파생 변수 및 변환 변수 생성
    df['long_run'] = df['total_audi'] / df['first_week_audi']
    df['long_run'] = df['long_run'].clip(upper=20)  # 20을 넘으면 20으로 클리핑
    
    df['log_first_scrn'] = np.log10(df['first_scrn'] + 1e-5) # 로그 취하기
    df['log_total_audi'] = np.log10(df['total_audi'] + 1e-5)
    
    return df

# 데이터 불러오기
try:
    raw_df = load_and_preprocess_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 전체 편수 및 묶은 편수 한 줄로 표시
total_count = 3737  # 원본 데이터 기준 전체 수
used_count = len(raw_df)
st.info(f"📊 **전체 영화 수:** {total_count}편 | **분석에 사용된 묶은 영화 수:** {used_count}편")

st.markdown("---")

# 4. 묶는 데 사용할 속성 선택
feature_map = {
    "스크린 수 (상용로그)": "log_first_scrn",
    "누적 관객 수 (상용로그)": "log_total_audi",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "long_run"
}

selected_feature_labels = st.multiselect(
    "클러스터링(유형 나누기)에 사용할 속성을 선택하세요 (2개 이상 선택):",
    options=list(feature_map.keys()),
    default=list(feature_map.keys())
)

if len(selected_feature_labels) < 2:
    st.warning("⚠️ 속성을 최소 2개 이상 선택해 주세요.")
    st.stop()

selected_features = [feature_map[label] for label in selected_feature_labels]

# 5. K-Means 클러스터링 실행
X = raw_df[selected_features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(X_scaled)

raw_df['cluster_raw'] = clusters

# 묶음 번호 재정의 (누적 관객 평균이 큰 묶음부터 ㉮, ㉯, ㉰)
cluster_audi_mean = raw_df.groupby('cluster_raw')['total_audi'].mean().sort_values(ascending=False)
label_mapping = {}
labels = ['㉮', '㉯', '㉰']
for i, orig_cluster in enumerate(cluster_audi_mean.index):
    label_mapping[orig_cluster] = labels[i]

raw_df['cluster'] = raw_df['cluster_raw'].map(label_mapping)

st.markdown("---")

# 6. 2차원 산점도
st.subheader("📌 2차원 산점도")
col1, col2 = st.columns(2)
with col1:
    x_axis_2d_label = st.selectbox("2차원 가로축(X축) 속성:", options=selected_feature_labels, index=0)
with col2:
    y_axis_2d_label = st.selectbox("2차원 세로축(Y축) 속성:", options=selected_feature_labels, index=min(1, len(selected_feature_labels)-1))

fig_2d = px.scatter(
    raw_df,
    x=feature_map[x_axis_2d_label],
    y=feature_map[y_axis_2d_label],
    color='cluster',
    hover_name='movieNm',
    title=f"2차원 산점도 ({x_axis_2d_label} vs {y_axis_2d_label})",
    category_orders={'cluster': ['㉮', '㉯', '㉰']},
    labels={feature_map[x_axis_2d_label]: x_axis_2d_label, feature_map[y_axis_2d_label]: y_axis_2d_label, 'cluster': '영화 유형'}
)
st.plotly_chart(fig_2d, use_container_width=True)

# 7. 3차원 산점도
st.subheader("📌 3차원 산점도")
if len(selected_feature_labels) < 3:
    st.info("💡 3차원 산점도를 출력하려면 묶는 데 사용할 속성을 3개 이상 선택해 주세요.")
else:
    col3, col4, col5 = st.columns(3)
    with col3:
        x_axis_3d_label = st.selectbox("3차원 X축 속성:", options=selected_feature_labels, index=0, key="3d_x")
    with col4:
        y_axis_3d_label = st.selectbox("3차원 Y축 속성:", options=selected_feature_labels, index=1, key="3d_y")
    with col5:
        z_axis_3d_label = st.selectbox("3차원 Z축 속성:", options=selected_feature_labels, index=2, key="3d_z")

    fig_3d = px.scatter_3d(
        raw_df,
        x=feature_map[x_axis_3d_label],
        y=feature_map[y_axis_3d_label],
        z=feature_map[z_axis_3d_label],
        color='cluster',
        hover_name='movieNm',
        title="3차원 산점도",
        category_orders={'cluster': ['㉮', '㉯', '㉰']},
        labels={
            feature_map[x_axis_3d_label]: x_axis_3d_label,
            feature_map[y_axis_3d_label]: y_axis_3d_label,
            feature_map[z_axis_3d_label]: z_axis_3d_label,
            'cluster': '영화 유형'
        }
    )
    # 점 크기 조절
    fig_3d.update_traces(marker=dict(size=3))
    st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("---")

# 8. 묶음별 요약 표 (원래 단위 평균)
st.subheader("📊 묶음별 영화 수 및 주요 속성 평균 (원래 단위)")

summary_df = raw_df.groupby('cluster').agg(
    편수=('movieCd', 'count'),
    스크린_수_평균=('first_scrn', 'mean'),
    누적_관객_평균=('total_audi', 'mean'),
    상위10위권_일수_평균=('days_in_top10', 'mean'),
    롱런_지수_평균=('long_run', 'mean')
).reindex(['㉮', '㉯', '㉰'])

# 컬럼명 정리
summary_df.columns = ['편수', '스크린 수 평균', '누적 관객 평균', '10위권 일수 평균', '롱런 지수 평균']

# 소수점 둘째 자리 정리
summary_df = summary_df.round(2)
st.dataframe(summary_df, use_container_width=True)

# 9. 묶음별 누적 관객 수 상위 5개 영화
st.subheader("🏆 묶음별 누적 관객 수 TOP 5 영화")
col_a, col_b, col_c = st.columns(3)

for col, cluster_name in zip([col_a, col_b, col_c], ['㉮', '㉯', '㉰']):
    with col:
        st.markdown(f"### 묶음 **{cluster_name}**")
        top5 = raw_df[raw_df['cluster'] == cluster_name].sort_values(by='total_audi', ascending=False).head(5)
        for idx, row in top5.iterrows():
            st.write(f"- **{row['movieNm']}** ({row['total_audi']:,}명)")
