"""
QLD 투자 일지 - Streamlit 앱

실행 방법:
  1) pip install streamlit plotly
  2) streamlit run qld_journal_app.py

데이터는 이 파일과 같은 폴더의 data.json 에 저장됩니다.
로컬에서 계속 같은 폴더로 실행하면 기록이 영구적으로 유지됩니다.
다른 기기에서도 쓰고 싶다면, 이 앱을 서버(Streamlit Community Cloud 등)에 올려서
같은 주소로 접속하면 됩니다. (Streamlit Community Cloud 무료 플랜은 재배포 시
파일이 초기화될 수 있으니, 정말 여러 기기에서 오래 쓰실 거면 별도 DB 연결을 권장드려요.)
"""

import json
import os
from datetime import date, datetime
import calendar as cal

import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

REASONS = {
    "regular": {"label": "정기 적립",   "color": "#7C9473", "bg": "#E7EEE2"},
    "ma50":    {"label": "50일선",      "color": "#D08A52", "bg": "#F5E4D3"},
    "ma120":   {"label": "120일선",     "color": "#B8763A", "bg": "#F0DCC4"},
    "ma200":   {"label": "200일선",     "color": "#8C5A2B", "bg": "#E8D2BA"},
    "golden":  {"label": "골든크로스",   "color": "#B8930F", "bg": "#F3E9C4"},
    "other":   {"label": "기타",        "color": "#8A8375", "bg": "#EFECE5"},
}

# ---------- 데이터 저장/불러오기 ----------

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "entries": {},          # { "YYYY-MM-DD": {reason, shares, price, note} }
        "base_shares": 0.0,
        "base_avg_price": 0.0,
        "current_price": 0.0,
        "fx_rate": 0.0,
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ---------- 페이지 설정 ----------

st.set_page_config(page_title="QLD 투자 일지", page_icon="📓", layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&family=Noto+Sans+KR:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #F6F4EE;
  --panel: #FFFFFF;
  --ink: #1F2A24;
  --ink-soft: #5B6B60;
  --line: #E5E1D5;
}
html, body, [data-testid="stAppViewContainer"] {
  background-color: var(--bg) !important;
  font-family: 'Noto Sans KR', -apple-system, sans-serif;
}
[data-testid="stHeader"] { background-color: transparent; }
.block-container { max-width: 1020px; padding-top: 2.2rem; padding-bottom: 3rem; }

h1 {
  font-family: 'Noto Serif KR', Georgia, serif !important;
  font-weight: 700 !important;
  font-size: 30px !important;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 12px;
  margin-bottom: 4px !important;
  letter-spacing: -0.01em;
  color: var(--ink);
}
h3 {
  font-family: 'Noto Serif KR', Georgia, serif !important;
  font-size: 15px !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-soft) !important;
  margin-top: 6px !important;
}
[data-testid="stCaptionContainer"] { color: var(--ink-soft) !important; }
hr { border-color: var(--line) !important; margin: 1.6rem 0 !important; }

.stat-box {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(31,42,36,0.04);
  transition: box-shadow .15s ease;
}
.stat-box:hover { box-shadow: 0 3px 10px rgba(31,42,36,0.08); }
.stat-label { font-size: 11px; color: var(--ink-soft); letter-spacing: 0.03em; margin-bottom: 4px; }
.stat-value { font-family: 'Noto Serif KR', Georgia, serif; font-size: 21px; color: var(--ink); }

.cal-cell-box {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px;
  height: 60px;
  margin-bottom: -6px;
  box-shadow: 0 1px 2px rgba(31,42,36,0.03);
}

div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {
  border-radius: 8px !important;
  border-color: var(--line) !important;
}

.stButton button {
  border-radius: 8px !important;
  border: 1px solid var(--line) !important;
  color: var(--ink-soft) !important;
  font-size: 12px !important;
  padding: 2px 0 !important;
}
.stButton button:hover {
  border-color: var(--ink) !important;
  color: var(--ink) !important;
}
.stButton button[kind="primary"] {
  background: var(--ink) !important;
  border-color: var(--ink) !important;
  color: #fff !important;
}

[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 10px !important;
  background: var(--panel) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("QLD 투자 일지")
st.caption("DISCIPLINE OVER IMPULSE · 데이터는 data.json 파일에 영구 저장됩니다")

# ---------- 보유 현황 ----------

st.subheader("보유 현황 (캘린더 자동 연동)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    base_shares = st.number_input("일지 시작 전 기존 보유 수량", value=float(data.get("base_shares", 0.0)), step=0.0001, format="%.4f")
with col2:
    base_avg = st.number_input("기존 보유 평단가 (USD)", value=float(data.get("base_avg_price", 0.0)), step=0.01, format="%.2f")
with col3:
    current_price = st.number_input("QLD 현재가 (USD, 수동 입력)", value=float(data.get("current_price", 0.0)), step=0.01, format="%.2f")
with col4:
    fx_rate = st.number_input("환율 USD→KRW (수동 입력)", value=float(data.get("fx_rate", 0.0)), step=0.01, format="%.2f")

# 값이 바뀌면 즉시 저장
if (base_shares != data.get("base_shares") or base_avg != data.get("base_avg_price")
        or current_price != data.get("current_price") or fx_rate != data.get("fx_rate")):
    data["base_shares"] = base_shares
    data["base_avg_price"] = base_avg
    data["current_price"] = current_price
    data["fx_rate"] = fx_rate
    save_data(data)

st.caption("※ 외부 시세·환율 API 없이 수동 입력 방식입니다. 매일 한 번씩 현재가·환율만 갱신해주시면 나머지는 자동 계산됩니다.")

entries = data.get("entries", {})
entry_shares_sum = sum(float(e.get("shares") or 0) for e in entries.values())
entry_cost_sum = sum(float(e.get("shares") or 0) * float(e.get("price") or 0) for e in entries.values())
total_shares = base_shares + entry_shares_sum
total_cost = base_shares * base_avg + entry_cost_sum
avg_price = (total_cost / total_shares) if total_shares > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(f'<div class="stat-box"><div class="stat-label">총 보유 수량</div><div class="stat-value">{total_shares:.4f}주</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat-box"><div class="stat-label">평단가</div><div class="stat-value">${avg_price:,.2f}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat-box"><div class="stat-label">총 매입원가</div><div class="stat-value">${total_cost:,.2f}</div></div>', unsafe_allow_html=True)

if current_price > 0 and total_shares > 0:
    value_usd = total_shares * current_price
    value_krw = value_usd * fx_rate if fx_rate > 0 else None
    c4.markdown(f'<div class="stat-box"><div class="stat-label">평가금액 (USD)</div><div class="stat-value">${value_usd:,.2f}</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="stat-box"><div class="stat-label">평가금액 (KRW)</div><div class="stat-value">{f"{value_krw:,.0f}원" if value_krw else "환율 입력 필요"}</div></div>', unsafe_allow_html=True)
else:
    c4.markdown('<div class="stat-box"><div class="stat-label">평가금액 (USD)</div><div class="stat-value">현재가 입력 필요</div></div>', unsafe_allow_html=True)
    c5.markdown('<div class="stat-box"><div class="stat-label">평가금액 (KRW)</div><div class="stat-value">-</div></div>', unsafe_allow_html=True)

st.divider()

# ---------- 캘린더 ----------

st.subheader("매수 캘린더")

legend_html = " &nbsp; ".join(
    f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;color:#5B6B60;">'
    f'<span style="width:9px;height:9px;border-radius:50%;background:{v["color"]};display:inline-block;"></span>{v["label"]}</span>'
    for v in REASONS.values()
)
st.markdown(legend_html, unsafe_allow_html=True)
st.write("")

if "cal_year" not in st.session_state:
    today = date.today()
    st.session_state.cal_year = today.year
    st.session_state.cal_month = today.month

nav1, nav2, nav3 = st.columns([1, 3, 1])
with nav1:
    if st.button("‹ 이전달"):
        m = st.session_state.cal_month - 1
        y = st.session_state.cal_year
        if m == 0:
            m = 12
            y -= 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
with nav3:
    if st.button("다음달 ›"):
        m = st.session_state.cal_month + 1
        y = st.session_state.cal_year
        if m == 13:
            m = 1
            y += 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
with nav2:
    st.markdown(f"<div style='text-align:center;font-family:Georgia,serif;font-size:18px;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</div>", unsafe_allow_html=True)

year, month = st.session_state.cal_year, st.session_state.cal_month
month_days = cal.monthcalendar(year, month)  # weeks, Mon=0 ... Sun=6 by default; we'll relabel

dow_labels = ["월", "화", "수", "목", "금", "토", "일"]
dcols = st.columns(7)
for i, d in enumerate(dow_labels):
    dcols[i].markdown(f"<div style='text-align:center;font-size:11px;color:#5B6B60;'>{d}</div>", unsafe_allow_html=True)

if "open_date" not in st.session_state:
    st.session_state.open_date = None

for week in month_days:
    wcols = st.columns(7)
    for i, day in enumerate(week):
        with wcols[i]:
            if day == 0:
                st.write("")
                continue
            key = f"{year}-{month:02d}-{day:02d}"
            entry = entries.get(key)
            bg = REASONS[entry["reason"]]["bg"] if entry else "#FFFFFF"
            shares_label = f"{entry['shares']}주" if entry and entry.get("shares") else ""
            st.markdown(
                f"<div class='cal-cell-box' style='background:{bg};'>"
                f"<div style='font-size:11px;color:#5B6B60;'>{day}</div>"
                f"<div style='font-size:11px;font-weight:600;'>{shares_label}</div></div>",
                unsafe_allow_html=True,
            )
            if st.button("기록", key=f"btn_{key}", use_container_width=True):
                st.session_state.open_date = key

# ---------- 매수 기록 입력 패널 ----------

if st.session_state.open_date:
    key = st.session_state.open_date
    entry = entries.get(key, {})
    with st.expander(f"📝 {key} 매수 기록", expanded=True):
        reason_keys = list(REASONS.keys())
        reason_labels = [REASONS[k]["label"] for k in reason_keys]
        default_idx = reason_keys.index(entry.get("reason", "regular")) if entry.get("reason") in reason_keys else 0
        reason_choice = st.radio("매수 이유", reason_labels, index=default_idx, horizontal=True, key=f"reason_{key}")
        shares_val = st.number_input("매수 수량 (주)", value=float(entry.get("shares") or 0), step=0.0001, format="%.4f", key=f"shares_{key}")
        price_val = st.number_input("매수 가격 (USD)", value=float(entry.get("price") or 0), step=0.01, format="%.2f", key=f"price_{key}")
        note_val = st.text_area("메모 (판단 이유, 그때 감정 등)", value=entry.get("note", ""), key=f"note_{key}")

        bsave, bdelete, bclose = st.columns(3)
        with bsave:
            if st.button("저장", type="primary", use_container_width=True):
                reason_key = reason_keys[reason_labels.index(reason_choice)]
                entries[key] = {"reason": reason_key, "shares": shares_val, "price": price_val, "note": note_val}
                data["entries"] = entries
                save_data(data)
                st.session_state.open_date = None
                st.rerun()
        with bdelete:
            if entry and st.button("삭제", use_container_width=True):
                entries.pop(key, None)
                data["entries"] = entries
                save_data(data)
                st.session_state.open_date = None
                st.rerun()
        with bclose:
            if st.button("닫기", use_container_width=True):
                st.session_state.open_date = None
                st.rerun()

st.divider()

# ---------- 매수 이력 타임라인 ----------

st.subheader("매수 이력 타임라인")
st.caption("TradingView 차트에 직접 마커를 겹치는 기능은 무료 임베드에서 지원되지 않아, 기록된 매수 시점만 따로 표시합니다.")

priced = sorted(
    [(k, v) for k, v in entries.items() if v.get("price")],
    key=lambda kv: kv[0],
)
if priced:
    xs = [k for k, v in priced]
    ys = [float(v["price"]) for k, v in priced]
    colors = [REASONS[v.get("reason", "other")]["color"] for k, v in priced]
    hover = [
        f"{k}<br>{REASONS[v.get('reason','other')]['label']}<br>${float(v['price']):.2f} × {v.get('shares','')}주<br>{v.get('note','')[:60]}"
        for k, v in priced
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#B7ADA0", dash="dot"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(color=colors, size=10, line=dict(color="white", width=1.5)), hovertext=hover, hoverinfo="text"))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 가격이 기록된 매수 이력이 없어요.")

st.divider()

# ---------- TradingView 차트 ----------

st.subheader("QLD 차트 (TradingView)")
st.caption("차트 상단 툴바의 '지표' 버튼으로 20/50/120/200일 이동평균선을 직접 추가할 수 있어요.")
components.html(
    """
    <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tvchart1&symbol=AMEX%3AQLD&interval=D&hidesidetoolbar=0&hidetoptoolbar=0&symboledit=0&saveimage=0&toolbarbg=F6F4EE&theme=light&style=1&timezone=Asia%2FSeoul&withdateranges=1&locale=kr"
    style="width:100%;height:460px;border:none;border-radius:8px;"></iframe>
    """,
    height=470,
)

st.divider()

# ---------- 이번 달 요약 ----------

st.subheader("이번 달 요약")
month_prefix = f"{year}-{month:02d}-"
month_entries = [v for k, v in entries.items() if k.startswith(month_prefix)]
month_shares = sum(float(v.get("shares") or 0) for v in month_entries)
reason_count = {k: 0 for k in REASONS}
for v in month_entries:
    reason_count[v.get("reason", "other")] = reason_count.get(v.get("reason", "other"), 0) + 1

st.markdown(f"이번 달 매수 횟수: **{len(month_entries)}회**  \n"
            f"이번 달 매수 총 수량: **{month_shares:.4f}주**  \n"
            + " · ".join(f"{REASONS[k]['label']} {v}회" for k, v in reason_count.items()))
