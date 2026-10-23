# main.py — 급식 규칙 찾기: 같은 날 함께 나온 메뉴 쌍을 센다
import re
from collections import Counter
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st

URL = "https://raw.githubusercontent.com/teacher188-netizen/2026-datascience/refs/heads/main/gajwa_meals.csv"

st.title("🍚 급식 규칙 찾기")


@st.cache_data(ttl=3600)
def load_baskets(url):
    table = pd.read_csv(url, encoding="utf-8")
    baskets = []
    for line in table["메뉴"]:
        names = set()
        for dish in str(line).split("|"):
            name = re.sub(r"\([^)]*\)", "", dish).strip()   # 괄호와 그 안의 내용은 제외한다
            if name:
                names.add(name)
        if names:
            baskets.append(sorted(names))
    return baskets


baskets = load_baskets(URL)
n = len(baskets)
single = Counter(item for basket in baskets for item in basket)           # 메뉴가 나온 날 수
pair = Counter(c for basket in baskets for c in combinations(basket, 2))  # 두 메뉴가 함께 나온 날 수

rows = []
for (a, b), together in pair.items():
    for x, y in [(a, b), (b, a)]:              # 한 쌍에서 두 방향의 규칙이 나온다
        rows.append({"조건": x, "결과": y, "동시": together,
                     "지지도": round(together / n, 3),
                     "신뢰도": round(together / single[x], 3),
                     "향상도": round((together / single[x]) / (single[y] / n), 2)})
규칙 = pd.DataFrame(rows, columns=["조건", "결과", "동시", "지지도", "신뢰도", "향상도"])

st.caption(f"급식 {n}일 · 메뉴 {len(single)}종 · 함께 나온 적이 있는 메뉴 쌍 {len(pair):,}개 · "
           f"규칙 {len(규칙):,}개")

기준 = st.radio("정렬", ["향상도 순", "신뢰도 순", "동시 순"], horizontal=True)
메뉴 = st.selectbox("메뉴로 좁혀 보기", ["(전체)"] + sorted(single))
최소동시 = st.slider("최소 동시 일수", 1, 10, 1)
걸러낸규칙 = 규칙[규칙["동시"] >= 최소동시]
st.write(f"동시에 나온 날이 {최소동시}일 이상인 규칙은 {len(걸러낸규칙):,}개입니다.")

보기 = 걸러낸규칙 if 메뉴 == "(전체)" else 걸러낸규칙[(걸러낸규칙["조건"] == 메뉴) | (걸러낸규칙["결과"] == 메뉴)]
보기 = 보기.sort_values({"향상도 순": "향상도", "신뢰도 순": "신뢰도", "동시 순": "동시"}[기준],
                    ascending=False, ignore_index=True)
if 보기.empty:
    st.info("조건에 맞는 규칙이 없습니다. 최소 동시 일수를 낮춰 봅니다.")
else:
    st.dataframe(보기, width="stretch", hide_index=True)
    top = 보기.sort_values("향상도", ascending=False).head(10).copy()
    top["규칙"] = top["조건"] + " → " + top["결과"]
    fig = px.bar(top, x="향상도", y="규칙", orientation="h", text="향상도")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)
    st.plotly_chart(fig, width="stretch")

st.subheader("함께 나온 적 없는 짝")
고른메뉴 = st.selectbox("메뉴 고르기", sorted(single), key="없는짝")
같이나온메뉴 = {y for (a, b) in pair for x, y in [(a, b), (b, a)] if x == 고른메뉴}
없는짝 = [{"메뉴": 이름, "나온 날": 날수} for 이름, 날수 in single.items()
        if 이름 != 고른메뉴 and 이름 not in 같이나온메뉴 and 날수 >= 10]   # 혼자서는 열흘 이상 나온 메뉴만

st.write(f"{고른메뉴} · 나온 날 {single[고른메뉴]}일 · 함께 나온 적 없는 메뉴 {len(없는짝)}종")
if not 없는짝:
    st.info("열흘 이상 나오면서 한 번도 함께 나오지 않은 메뉴가 없습니다.")
else:
    표 = pd.DataFrame(없는짝).sort_values("나온 날", ascending=False)
    st.dataframe(표, width="stretch", hide_index=True)
