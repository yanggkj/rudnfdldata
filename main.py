# -------------------------------------------------------------
    # 섹션 3: 총 관객 수 분포 (히스토그램)
    # -------------------------------------------------------------
    stream_lit.header("3. 총 관객 수(total_audi) 분포 히스토그램")
    
    # 히스토그램 동적 데이터 계산 (최대 관객 영화 탐색)
    max_audi_movie = df.loc[df['total_audi'].idxmax()]
    top_movie_name = max_audi_movie['movieNm']
    top_movie_audi = max_audi_movie['total_audi']
    
    fig3 = px.histogram(
        df,
        x='total_audi',
        nbins=20,
        title="총 관객 수 분포 히스토그램",
        labels={'total_audi': '총 관객 수 (명)', 'count': '영화 수'},
        color_discrete_sequence=['#636EFA']
    )
    
    fig3.update_layout(
        xaxis_title="총 관객 수 (명)",
        yaxis_title="영화 수 (편)",
        margin=dict(t=50, b=30, l=10, r=10)
    )
    
    # 그래프 출력
    stream_lit.plotly_chart(fig3, use_container_width=True)
    
    # 그래프 하단 Insight 문구 출력
    stream_lit.info(
        f"💡 **이 그래프로 알 수 있는 것:** 대다수의 영화가 상대적으로 적은 관객 수 구간(하위 구간)에 집중되어 있는 오른쪽으로 긴 꼬리를 가진 분포 형태를 보이며, "
        f"가장 관객이 많은 영화는 **'{top_movie_name}'**(총 {top_movie_audi:,}명)입니다."
    )
