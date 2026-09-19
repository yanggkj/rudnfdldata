# main.py
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import plotly.express as px
import plotly.graph_objects as go

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

# 4. 묶는 데 사용할 속성 선택 및 묶음 수 선택
col_feat, col_k = st.columns([3, 1])

feature_map = {
    "스크린 수 (상용로그)": "log_first_scrn",
    "누적 관객 수 (상용로그)": "log_total_audi",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "long_run"
}

with col_feat:
    selected_feature_labels = st.multiselect(
        "클러스터링(유형 나누기)에 사용할 속성을 선택하세요 (2개 이상 선택):",
        options=list(feature_map.keys()),
        default=list(feature_map.keys())
    )

with col_k:
    n_clusters = st.slider(
        "묶음 수(K) 선택:",
        min_value=2,
        max_value=7,
        value=3,
        step=1
    )

if len(selected_feature_labels) < 2:
    st.warning("⚠️ 속성을 최소 2개 이상 선택해 주세요.")
    st.stop()

selected_features = [feature_map[label] for label in selected_feature_labels]

# 5. K-Means 클러스터링 실행
X = raw_df[selected_features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(X_scaled)

raw_df['cluster_raw'] = clusters

# 묶음 번호 기호 정의 (㉮ ~ ㉴)
circle_labels = ['㉮', '㉯', '㉰', '㉱', '㉲', '㉳', '㉴']
current_labels = circle_labels[:n_clusters]

# 누적 관객 평균이 큰 묶음부터 기호 부여
cluster_audi_mean = raw_df.groupby('cluster_raw')['total_audi'].mean().sort_values(ascending=False)
label_mapping = {}
for i, orig_cluster in enumerate(cluster_audi_mean.index):
    label_mapping[orig_cluster] = current_labels[i]

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
    category_orders={'cluster': current_labels},
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
        category_orders={'cluster': current_labels},
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
).reindex(current_labels)

# 컬럼명 정리
summary_df.columns = ['편수', '스크린 수 평균', '누적 관객 평균', '10위권 일수 평균', '롱런 지수 평균']

# 소수점 둘째 자리 정리
summary_df = summary_df.round(2)
st.dataframe(summary_df, use_container_width=True)

# 9. 묶음별 누적 관객 수 상위 5개 영화
st.subheader("🏆 묶음별 누적 관객 수 TOP 5 영화")
cols = st.columns(n_clusters)

for i, cluster_name in enumerate(current_labels):
    with cols[i]:
        st.markdown(f"### 묶음 **{cluster_name}**")
        top5 = raw_df[raw_df['cluster'] == cluster_name].sort_values(by='total_audi', ascending=False).head(5)
        for idx, row in top5.iterrows():
            st.write(f"- **{row['movieNm']}** ({row['total_audi']:,}명)")

st.markdown("---")

# 10. 엘보우 기법(Elbow Method) 및 실루엣 점수 평가
st.subheader("📈 적정 묶음 수(K) 진단 및 평가")

# K=1~7 군집 내 오차제곱합(Inertia) 계산
k_range = range(1, 8)
inertias = []

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

# 꺾은선 그래프 생성 및 선택된 K 세로선 표시
fig_elbow = go.Figure()
fig_elbow.add_trace(go.Scatter(
    x=list(k_range),
    y=inertias,
    mode='lines+markers',
    name='군집 내 오차제곱합(Inertia)',
    line=dict(color='royalblue', width=2),
    marker=dict(size=8)
))

# 선택된 K에 세로선 그리기
fig_elbow.add_vline(
    x=n_clusters,
    line_width=2,
    line_dash="dash",
    line_color="red",
    annotation_text=f"선택한 묶음 수 (K={n_clusters})",
    annotation_position="top right"
)

fig_elbow.update_layout(
    title="묶음 수(K)에 따른 군집 내 오차제곱합(Inertia) 변화",
    xaxis_title="묶음 수 (K)",
    yaxis_title="군집 내 오차제곱합",
    xaxis=dict(tickmode='linear', tick0=1, dtick=1)
)

st.plotly_chart(fig_elbow, use_container_width=True)

# 묶음 수별 Inertia 및 감솟값 표 작성
reduction_list = [""]  # K=1일 때는 비교 대상이 없으므로 빈칸
for i in range(1, len(inertias)):
    diff = inertias[i-1] - inertias[i]
    reduction_list.append(f"{diff:,.2f}")

elbow_df = pd.DataFrame({
    '묶음 수 (K)': list(k_range),
    '군집 내 오차제곱합 (Inertia)': [f"{val:,.2f}" for val in inertias],
    '이전 값 대비 감소량': reduction_list
})

st.dataframe(elbow_df, use_container_width=True)

# 실루엣 점수 계산 및 출력
score = silhouette_score(X_scaled, clusters)
st.success(f"💡 현재 선택한 **묶음 수({n_clusters})**의 실루엣 점수: **{score:.4f}** (점수는 -1에서 1 사이이며, 1에 가까울수록 묶음이 뚜렷합니다.)")
