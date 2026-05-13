import streamlit as st
from engine.decision_tree import (
    QUESTION_TREE,
    is_result,
    is_info_page,
    is_multi_select,
    get_strategies,
    get_strategies_from_multiselect,
)
from knowledge.strategies import STRATEGIES

st.set_page_config(
    page_title="台灣節稅專家系統",
    page_icon="💰",
    layout="centered",
)

TAG_COLORS = {
    "green":  ("#d4edda", "#155724"),
    "orange": ("#fff3cd", "#856404"),
    "red":    ("#f8d7da", "#721c24"),
}

MAX_STEPS = 4


def init_state():
    if "current_key" not in st.session_state:
        st.session_state.current_key = "Q1"
    if "history" not in st.session_state:
        st.session_state.history = []
    if "result_strategies" not in st.session_state:
        st.session_state.result_strategies = []


def reset_state():
    st.session_state.current_key = "Q0"
    st.session_state.history = []
    st.session_state.result_strategies = []


def go_back():
    if st.session_state.history:
        st.session_state.current_key = st.session_state.history.pop()
        st.session_state.result_strategies = []


def render_progress():
    depth = len(st.session_state.history)
    progress = min(depth / MAX_STEPS, 1.0)
    st.progress(progress)
    st.caption(f"第 {depth + 1} 步，共約 {MAX_STEPS} 步")


def render_back_button():
    if st.session_state.history:
        if st.button("← 上一題", key="back_btn"):
            go_back()
            st.rerun()


def render_question_page(key):
    q = QUESTION_TREE[key]
    render_progress()
    st.markdown(f"## {q['text']}")
    if q.get("subtitle"):
        st.caption(q["subtitle"])
    st.markdown("---")
    for option, next_key in q["options"].items():
        if st.button(option, use_container_width=True, key=f"opt_{option}"):
            st.session_state.history.append(key)
            if is_result(next_key):
                st.session_state.result_strategies = get_strategies(next_key)
                st.session_state.current_key = next_key
            else:
                st.session_state.current_key = next_key
            st.rerun()
    st.markdown("")
    render_back_button()


def render_info_page(key):
    q = QUESTION_TREE[key]
    render_progress()
    st.markdown(f"## {q['text']}")
    if q.get("subtitle"):
        st.caption(q["subtitle"])
    st.markdown("---")
    info_text = "\n\n".join(line if line else "&nbsp;" for line in q["content"])
    st.info(info_text)
    st.markdown("")
    if st.button("了解了，開始評估我的節稅方案 →", use_container_width=True, key="info_next"):
        st.session_state.history.append(key)
        st.session_state.current_key = q["next"]
        st.rerun()
    st.markdown("")
    render_back_button()


def render_multiselect_page(key):
    q = QUESTION_TREE[key]
    render_progress()
    st.markdown(f"## {q['text']}")
    if q.get("subtitle"):
        st.caption(q["subtitle"])
    st.markdown("---")
    selected = []
    for option in q["options"]:
        if st.checkbox(option, key=f"chk_{option}"):
            selected.append(option)
    st.markdown("")
    if st.button("✅ 確認，看我的節稅方案", use_container_width=True, key="multi_confirm"):
        strategies = get_strategies_from_multiselect(key, selected)
        st.session_state.history.append(key)
        st.session_state.result_strategies = strategies
        st.session_state.current_key = "RESULT_MULTI"
        st.rerun()
    st.markdown("")
    render_back_button()


def render_strategy_card(strategy_id):
    s = STRATEGIES.get(strategy_id)
    if not s:
        return

    tag_color_key = s.get("tag_color", "green")
    bg, fg = TAG_COLORS.get(tag_color_key, TAG_COLORS["green"])

    with st.container(border=True):
        tag_html = (
            f'<span style="background:{bg};color:{fg};padding:2px 10px;'
            f'border-radius:12px;font-size:0.82em;font-weight:600;">'
            f'{s["tag"]}</span>'
        )
        st.markdown(
            f"### {s['title']} &nbsp; {tag_html}",
            unsafe_allow_html=True,
        )
        st.markdown(f"**節稅潛力：** {s['節稅潛力']}")
        st.markdown("**白話說明**")
        st.markdown(s["白話說明"])

        case = s.get("真實案例", {})
        if case:
            st.success(f"**📖 {case['標題']}**\n\n{case['內容']}")

        st.markdown("**具體步驟**")
        for step in s["具體步驟"]:
            st.markdown(f"- {step}")

        st.warning(f"⚠️ **注意事項：** {s['注意事項']}")

        with st.expander("📋 法規依據", expanded=False):
            st.markdown(s["法規依據"])


def build_path_label():
    labels = []
    for key in st.session_state.history:
        if key in QUESTION_TREE:
            labels.append(QUESTION_TREE[key]["text"])
    return " → ".join(labels) if labels else ""


def render_result_page():
    st.markdown("# 🎯 你的節稅方案")
    st.markdown("以下是根據你的狀況，最值得優先執行的建議")
    path_label = build_path_label()
    if path_label:
        st.caption(f"你的狀況：{path_label}")
    st.markdown("---")

    strategy_ids = st.session_state.result_strategies
    if not strategy_ids:
        st.info("目前沒有找到符合的策略，請重新評估。")
    else:
        display_ids = strategy_ids[:3]
        extra = len(strategy_ids) - len(display_ids)
        for sid in display_ids:
            render_strategy_card(sid)
            st.markdown("")
        if extra > 0:
            st.markdown(
                f'<p style="color:gray;font-size:0.85em;">還有 {extra} 個相關策略，建議諮詢專業會計師了解更多</p>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    if st.button("🔄 重新評估", use_container_width=True, key="restart_btn"):
        reset_state()
        st.rerun()


def main():
    init_state()
    st.title("💰 台灣節稅專家系統")
    st.markdown("*依你的狀況，找出最適合的合法節稅策略*")
    st.markdown("---")

    key = st.session_state.current_key

    if key == "RESULT_MULTI" or is_result(key):
        render_result_page()
    elif is_info_page(key):
        render_info_page(key)
    elif is_multi_select(key):
        render_multiselect_page(key)
    elif key in QUESTION_TREE:
        render_question_page(key)
    else:
        st.error(f"找不到問題：{key}")
        if st.button("回到首頁"):
            reset_state()
            st.rerun()


if __name__ == "__main__":
    main()
