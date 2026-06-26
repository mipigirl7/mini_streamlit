import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests

st.set_page_config(
    page_title="마케팅 채널 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
.intro-box {
    background: linear-gradient(135deg, #667eea18, #764ba218);
    border-left: 4px solid #667eea;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.intro-box h3 { margin: 0 0 6px 0; font-size: 1.05rem; }
.intro-box p  { margin: 0; font-size: 0.85rem; color: #555; line-height: 1.7; }
.action-card {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-size: 0.87rem;
    line-height: 1.6;
}
.action-high   { background:#fff0f0; border-left: 4px solid #e53e3e; }
.action-medium { background:#fffbeb; border-left: 4px solid #d69e2e; }
.action-low    { background:#f0fff4; border-left: 4px solid #38a169; }
.sim-compare {
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.sim-before { background: #f7f7f7; }
.sim-after  { background: #f0fff4; }
.sim-number { font-size: 1.8rem; font-weight: 800; }
.sim-label  { font-size: 0.8rem; color: #666; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 ──────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/marketing_performance.csv")
    df["month"]  = pd.to_datetime(df["month"])
    df["ROAS"]   = (df["revenue"] / df["spend"]).round(2)
    df["CTR"]    = (df["clicks"] / df["impressions"] * 100).round(2)
    df["CVR"]    = (df["conversions"] / df["clicks"] * 100).round(2)
    df["CAC"]    = (df["spend"] / df["conversions"]).round(0).astype(int)
    return df

@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        res  = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        data = res.json()
        return {"KRW": data["rates"]["KRW"], "updated": data.get("time_last_update_utc",""), "success": True}
    except Exception:
        return {"KRW": 1380.0, "updated": "API 연결 실패", "success": False}

df       = load_data()
exchange = get_exchange_rate()

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 마케팅 채널 분석")
    st.caption("광고 채널 성과를 분석하고\n예산 배분을 최적화하는 의사결정 도구")
    st.divider()

    page = st.radio("페이지", [
        "🏠  KPI 요약",
        "📈  채널 성과",
        "🎛️  예산 시뮬레이터",
        "💡  인사이트",
    ], label_visibility="collapsed")

    st.divider()
    st.markdown("**🔧 필터**")
    all_channels = sorted(df["channel"].unique().tolist())
    selected_channels = st.multiselect("채널", options=all_channels, default=all_channels)

    month_labels = pd.date_range(df["month"].min(), df["month"].max(), freq="MS").strftime("%Y-%m").tolist()
    date_range   = st.select_slider("분석 기간", options=month_labels,
                                    value=(month_labels[0], month_labels[-1]))
    start, end   = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    st.divider()
    icon = "✅" if exchange["success"] else "⚠️"
    st.markdown(f"**🌐 실시간 환율** {icon}")
    st.metric("USD / KRW", f"₩{exchange['KRW']:,.1f}")
    st.caption("출처: Exchange Rate API")

# ── 공통 집계 ────────────────────────────────────────────────
filtered = df[
    df["channel"].isin(selected_channels) &
    (df["month"] >= start) & (df["month"] <= end)
]

total_spend   = filtered["spend"].sum()
total_revenue = filtered["revenue"].sum()
total_conv    = filtered["conversions"].sum()
overall_roas  = round(total_revenue / total_spend, 2) if total_spend else 0
overall_cac   = int(total_spend / total_conv) if total_conv else 0
overall_cvr   = round(total_conv / filtered["clicks"].sum() * 100, 2)

ch_stats = (
    filtered.groupby("channel")
    .agg(spend=("spend","sum"), revenue=("revenue","sum"),
         clicks=("clicks","sum"), conversions=("conversions","sum"))
    .assign(
        ROAS=lambda x: (x["revenue"]/x["spend"]).round(2),
        CVR =lambda x: (x["conversions"]/x["clicks"]*100).round(2),
        CAC =lambda x: (x["spend"]/x["conversions"]).round(0),
    )
    .sort_values("ROAS", ascending=False)
)

# ── 인사이트 생성 함수 ────────────────────────────────────────
def generate_insights(filtered, ch_stats, overall_roas):
    insights = []

    # 1. 숨은 보석: 예산 하위 30% 인데 ROAS 상위 30%
    spend_q30  = ch_stats["spend"].quantile(0.3)
    roas_q70   = ch_stats["ROAS"].quantile(0.7)
    hidden_gems = ch_stats[(ch_stats["spend"] <= spend_q30) & (ch_stats["ROAS"] >= roas_q70)]
    if not hidden_gems.empty:
        ch = hidden_gems.index[0]
        insights.append(("high", "🔮 숨은 보석 발견",
            f"**{ch}** — 예산은 전체의 {int(ch_stats.loc[ch,'spend']/ch_stats['spend'].sum()*100)}%에 불과하지만 "
            f"ROAS {ch_stats.loc[ch,'ROAS']}x로 최상위권입니다. "
            f"예산을 2배 늘리면 약 ₩{int(ch_stats.loc[ch,'spend']*ch_stats.loc[ch,'ROAS']/1e6):.0f}M 추가 매출이 기대됩니다.",
            f"👉 액션: {ch} 월 예산 즉시 상향 검토"))

    # 2. 성과 급락 채널: 최근 3개월 ROAS vs 이전 대비
    monthly = (
        filtered.groupby(["month","channel"])
        .agg(spend=("spend","sum"), revenue=("revenue","sum"))
        .assign(ROAS=lambda x: (x["revenue"]/x["spend"]).round(2))
        .reset_index()
    )
    for ch in ch_stats.index:
        ch_monthly = monthly[monthly["channel"]==ch].sort_values("month")
        if len(ch_monthly) >= 6:
            recent = ch_monthly.tail(3)["ROAS"].mean()
            prev   = ch_monthly.iloc[-6:-3]["ROAS"].mean()
            drop   = (recent - prev) / prev * 100
            if drop < -15:
                insights.append(("high", f"📉 {ch} 성과 급락",
                    f"최근 3개월 ROAS 평균 **{recent:.2f}x** — 직전 3개월({prev:.2f}x) 대비 "
                    f"**{abs(drop):.1f}% 하락**했습니다. 크리에이티브 피로 또는 경쟁 심화가 원인일 수 있습니다.",
                    f"👉 액션: 크리에이티브 소재 교체 및 타깃 오디언스 재설정 필요"))

    # 3. 예산 낭비 채널: ROAS 평균 이하 + 예산 상위 40%
    spend_q60 = ch_stats["spend"].quantile(0.6)
    waste = ch_stats[(ch_stats["ROAS"] < overall_roas) & (ch_stats["spend"] >= spend_q60)]
    if not waste.empty:
        ch = waste.sort_values("spend", ascending=False).index[0]
        wasted = int((ch_stats.loc[ch,"spend"] - ch_stats.loc[ch,"spend"] * ch_stats.loc[ch,"ROAS"] / overall_roas) / 1e6 * 10) / 10
        insights.append(("medium", f"💸 {ch} 예산 효율 저하",
            f"예산은 전체 상위권이지만 ROAS {ch_stats.loc[ch,'ROAS']}x로 평균({overall_roas}x) 미달입니다. "
            f"효율 평균 수준으로만 올려도 약 ₩{wasted}M 추가 매출이 가능합니다.",
            f"👉 액션: 예산 10~20% 감축 후 성과 채널로 이동"))

    # 4. Q4 시즌 기회
    months_in = filtered["month"].dt.month.unique()
    if any(m in months_in for m in [11, 12]):
        q4_roas = monthly[monthly["month"].dt.month.isin([11,12])]["ROAS"].mean()
        avg_roas = monthly["ROAS"].mean()
        if q4_roas > avg_roas * 1.1:
            insights.append(("low", "🎄 Q4 시즌 효과 감지",
                f"11~12월 평균 ROAS **{q4_roas:.2f}x** — 연간 평균({avg_roas:.2f}x) 대비 "
                f"**{(q4_roas/avg_roas-1)*100:.1f}% 높습니다.** 시즌 광고 효율이 확실히 존재합니다.",
                "👉 액션: Q4 예산 사전 증액 및 시즌 크리에이티브 미리 준비"))

    # 기본 인사이트 (항상)
    best_ch  = ch_stats.index[0]
    worst_ch = ch_stats.index[-1]
    insights.append(("low", f"✅ 최고 효율: {best_ch}",
        f"ROAS {ch_stats.loc[best_ch,'ROAS']}x — 전체 평균 대비 "
        f"{round((ch_stats.loc[best_ch,'ROAS']/overall_roas-1)*100,1)}% 초과. 예산 확대 우선 대상입니다.",
        f"👉 액션: 다음 달 예산 배분 시 {best_ch} 비중 우선 증가"))
    insights.append(("medium", f"⚠️ 개선 필요: {worst_ch}",
        f"ROAS {ch_stats.loc[worst_ch,'ROAS']}x, 전환율 {ch_stats.loc[worst_ch,'CVR']}%로 최하위. "
        f"방치 시 예산 낭비 누적됩니다.",
        f"👉 액션: 랜딩 페이지 A/B 테스트 + 오디언스 재타깃 실행"))

    return insights

# ════════════════════════════════════════════════
# PAGE 1 — KPI 요약
# ════════════════════════════════════════════════
if page == "🏠  KPI 요약":
    st.markdown("""
<div class="intro-box">
<h3>📊 마케팅 채널 기여도 분석 & 예산 시뮬레이터</h3>
<p>
Google · Meta · Instagram · Kakao · Naver 5개 광고 채널의 <b>ROAS · 전환율 · CAC</b>를 한눈에 비교하고,<br>
예산을 직접 조정해 <b>예상 매출을 실시간 시뮬레이션</b>하는 마케팅 의사결정 도구입니다.<br>
왼쪽 사이드바에서 채널·기간 필터를 설정하고, 페이지를 선택해 분석을 시작하세요.
</p>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 총 광고비",   f"₩{total_spend/1e6:.1f}M")
    c2.metric("📦 총 매출",     f"₩{total_revenue/1e6:.1f}M")
    c3.metric("📈 전체 ROAS",   f"{overall_roas}x",  help="매출 ÷ 광고비. 1원 투자 시 벌어들인 매출")
    c4.metric("👤 평균 CAC",    f"₩{overall_cac:,}", help="고객 1명 획득에 든 광고비")
    c5.metric("🎯 평균 전환율", f"{overall_cvr}%",   help="클릭 대비 실구매 전환 비율")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("채널별 ROAS 순위")
        fig = px.bar(
            ch_stats.reset_index().sort_values("ROAS", ascending=True),
            x="ROAS", y="channel", orientation="h",
            color="ROAS", color_continuous_scale="Teal", text="ROAS",
        )
        fig.update_traces(texttemplate="%{text}x", textposition="outside")
        fig.add_vline(x=overall_roas, line_dash="dash", line_color="#999",
                      annotation_text=f"평균 {overall_roas}x", annotation_position="top right")
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          yaxis_title="", xaxis_title="ROAS", height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("채널별 광고비 비중")
        spend_df = filtered.groupby("channel")["spend"].sum().reset_index()
        fig2 = px.pie(spend_df, names="channel", values="spend", hole=0.45,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # 추천 액션 TOP 3
    st.divider()
    st.subheader("🚨 지금 당장 해야 할 액션 TOP 3")
    insights = generate_insights(filtered, ch_stats, overall_roas)
    for i, (level, title, body, action) in enumerate(insights[:3]):
        cls = {"high":"action-high","medium":"action-medium","low":"action-low"}[level]
        st.markdown(f"""
<div class="action-card {cls}">
<b>{title}</b><br>
{body}<br>
<span style="font-weight:600">{action}</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# PAGE 2 — 채널 성과
# ════════════════════════════════════════════════
elif page == "📈  채널 성과":
    st.title("채널 성과 분석")
    st.caption("채널별 ROAS · 전환율 · 기여도를 비교해 강약점을 파악합니다.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("월별 ROAS 추이")
        monthly = (
            filtered.groupby(["month","channel"])
            .agg(spend=("spend","sum"), revenue=("revenue","sum"))
            .assign(ROAS=lambda x: (x["revenue"]/x["spend"]).round(2))
            .reset_index()
        )
        fig = px.line(monthly, x="month", y="ROAS", color="channel",
                      markers=True, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=300, xaxis_title="", yaxis_title="ROAS", legend_title="채널")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("광고비 vs 매출")
        agg = ch_stats.reset_index()
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="광고비", x=agg["channel"], y=agg["spend"]/1e6, marker_color="#636EFA"))
        fig2.add_trace(go.Bar(name="매출",   x=agg["channel"], y=agg["revenue"]/1e6, marker_color="#00CC96"))
        fig2.update_layout(barmode="group", height=300, yaxis_title="금액 (백만원)", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("전환율(CVR) 비교")
        fig3 = px.bar(
            ch_stats.reset_index().sort_values("CVR", ascending=True),
            x="CVR", y="channel", orientation="h",
            color="CVR", color_continuous_scale="Blues", text="CVR",
        )
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(showlegend=False, coloraxis_showscale=False,
                           height=280, xaxis_title="CVR (%)", yaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("기여도 비교")
        st.caption("Last Click: 전환 직전 클릭 기준 | Linear: 광고비 비율 기준")
        conv_by_ch  = filtered.groupby("channel")["conversions"].sum()
        spend_by_ch = filtered.groupby("channel")["spend"].sum()
        attr = pd.DataFrame({
            "채널":       conv_by_ch.index,
            "Last Click": (conv_by_ch/conv_by_ch.sum()*100).round(1).values,
            "Linear":     (spend_by_ch/spend_by_ch.sum()*100).round(1).values,
        })
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Last Click", x=attr["채널"], y=attr["Last Click"], marker_color="#EF553B"))
        fig4.add_trace(go.Bar(name="Linear",     x=attr["채널"], y=attr["Linear"],     marker_color="#AB63FA"))
        fig4.update_layout(barmode="group", height=280, yaxis_title="기여도 (%)", xaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════════
# PAGE 3 — 예산 시뮬레이터
# ════════════════════════════════════════════════
elif page == "🎛️  예산 시뮬레이터":
    st.title("예산 시뮬레이터")
    st.caption("슬라이더로 채널 예산 비율을 조정 → 예상 매출·ROAS 실시간 계산. 총 예산은 고정됩니다.")

    total_budget = int(filtered["spend"].sum())

    sliders = {}
    cols = st.columns(len(ch_stats))
    for i, (ch, row) in enumerate(ch_stats.iterrows()):
        default_pct = int(row["spend"] / total_budget * 100)
        sliders[ch] = cols[i].slider(ch, 0, 100, default_pct, key=f"sim_{ch}")

    total_pct = sum(sliders.values())

    if total_pct == 0:
        st.warning("슬라이더를 조정해주세요.")
    else:
        sim_spend   = {ch: int(pct / total_pct * total_budget) for ch, pct in sliders.items()}
        sim_revenue = {ch: int(sim_spend[ch] * ch_stats.loc[ch,"ROAS"]) for ch in sim_spend}
        sim_total_r = sum(sim_revenue.values())
        sim_roas    = round(sim_total_r / total_budget, 2)
        delta_rev   = sim_total_r - total_revenue
        delta_roas  = round(sim_roas - overall_roas, 2)

        st.divider()

        # ── 현재 vs 시뮬레이션 나란히 비교 ──
        left, mid, right = st.columns([5, 1, 5])

        with left:
            st.markdown("""<div class="sim-compare sim-before">""", unsafe_allow_html=True)
            st.markdown("**현재 배분**")
            m1, m2 = st.columns(2)
            m1.metric("총 매출",     f"₩{total_revenue/1e6:.1f}M")
            m2.metric("ROAS",        f"{overall_roas}x")
            cur_df = pd.DataFrame({
                "채널": list(ch_stats.index),
                "예산": [ch_stats.loc[c,"spend"] for c in ch_stats.index],
            })
            fig_cur = px.pie(cur_df, names="채널", values="예산", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_cur.update_layout(height=220, margin=dict(t=5,b=5,l=5,r=5),
                                  showlegend=True, legend=dict(font_size=11))
            st.plotly_chart(fig_cur, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with mid:
            st.markdown("<br><br><br><br><h2 style='text-align:center'>→</h2>", unsafe_allow_html=True)

        with right:
            arrow = "🟢" if delta_rev >= 0 else "🔴"
            st.markdown(f"""<div class="sim-compare sim-after">""", unsafe_allow_html=True)
            st.markdown(f"**시뮬레이션 결과** {arrow}")
            m3, m4 = st.columns(2)
            m3.metric("예상 매출", f"₩{sim_total_r/1e6:.1f}M",
                      delta=f"₩{delta_rev/1e6:+.1f}M")
            m4.metric("예상 ROAS", f"{sim_roas}x",
                      delta=f"{delta_roas:+.2f}x")
            sim_df = pd.DataFrame({
                "채널": list(sim_spend.keys()),
                "예산": list(sim_spend.values()),
            })
            fig_sim = px.pie(sim_df, names="채널", values="예산", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_sim.update_layout(height=220, margin=dict(t=5,b=5,l=5,r=5),
                                  showlegend=True, legend=dict(font_size=11))
            st.plotly_chart(fig_sim, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── 채널별 예상 매출 변화 ──
        st.divider()
        st.subheader("채널별 현재 vs 예상 매출 비교")
        compare_df = pd.DataFrame({
            "채널":   list(ch_stats.index),
            "현재 매출":   [int(ch_stats.loc[c,"revenue"]) for c in ch_stats.index],
            "예상 매출":   [sim_revenue[c] for c in ch_stats.index],
        })
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(name="현재 매출", x=compare_df["채널"],
                                  y=compare_df["현재 매출"]/1e6, marker_color="#a0aec0"))
        fig_comp.add_trace(go.Bar(name="예상 매출", x=compare_df["채널"],
                                  y=compare_df["예상 매출"]/1e6, marker_color="#48bb78"))
        fig_comp.update_layout(barmode="group", height=280,
                               yaxis_title="매출 (백만원)", xaxis_title="")
        st.plotly_chart(fig_comp, use_container_width=True)

        # 추천 액션
        if delta_rev > 0:
            best_gain = max(sim_revenue, key=lambda c: sim_revenue[c]-int(ch_stats.loc[c,"revenue"]))
            st.success(f"💡 이 배분대로 실행하면 **₩{delta_rev/1e6:.1f}M 추가 매출**이 기대됩니다. "
                       f"가장 큰 기여 채널은 **{best_gain}**입니다.")
        else:
            st.warning(f"⚠️ 현재 배분보다 **₩{abs(delta_rev)/1e6:.1f}M 매출 감소**가 예상됩니다. 슬라이더를 조정해보세요.")

# ════════════════════════════════════════════════
# PAGE 4 — 인사이트
# ════════════════════════════════════════════════
elif page == "💡  인사이트":
    st.title("자동 인사이트")
    st.caption("데이터 패턴을 분석해 자동 생성된 진단과 액션 아이템입니다.")
    st.divider()

    insights = generate_insights(filtered, ch_stats, overall_roas)

    high   = [(t,b,a) for lvl,t,b,a in insights if lvl=="high"]
    medium = [(t,b,a) for lvl,t,b,a in insights if lvl=="medium"]
    low    = [(t,b,a) for lvl,t,b,a in insights if lvl=="low"]

    col1, col2 = st.columns(2)
    with col1:
        if high:
            st.markdown("#### 🔴 즉시 조치 필요")
            for t, b, a in high:
                st.markdown(f'<div class="action-card action-high"><b>{t}</b><br>{b}<br><b>{a}</b></div>',
                            unsafe_allow_html=True)
        if low:
            st.markdown("#### 🟢 기회 요인")
            for t, b, a in low:
                st.markdown(f'<div class="action-card action-low"><b>{t}</b><br>{b}<br><b>{a}</b></div>',
                            unsafe_allow_html=True)
    with col2:
        if medium:
            st.markdown("#### 🟡 모니터링 필요")
            for t, b, a in medium:
                st.markdown(f'<div class="action-card action-medium"><b>{t}</b><br>{b}<br><b>{a}</b></div>',
                            unsafe_allow_html=True)

    st.divider()
    st.subheader("채널별 종합 점수")
    st.caption("ROAS 50% + 전환율 30% + CAC 효율 20% 가중 평균")

    def norm(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-9) * 100

    score_df = ch_stats.copy()
    score_df["종합점수"] = (
        norm(score_df["ROAS"]) * 0.5 +
        norm(score_df["CVR"])  * 0.3 +
        norm(-score_df["CAC"]) * 0.2
    ).round(1)

    fig_s = px.bar(
        score_df.reset_index().sort_values("종합점수", ascending=True),
        x="종합점수", y="channel", orientation="h",
        color="종합점수", color_continuous_scale="RdYlGn",
        text="종합점수", range_x=[0, 115],
    )
    fig_s.update_traces(texttemplate="%{text}점", textposition="outside")
    fig_s.update_layout(coloraxis_showscale=False, yaxis_title="",
                        xaxis_title="종합 점수 (/ 100)", height=280, margin=dict(t=10,b=10))
    st.plotly_chart(fig_s, use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("📌 마케팅 캠페인 시뮬레이션 데이터\n🌐 환율: Exchange Rate API\n⚡ Made with Streamlit")
