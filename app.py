import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import graphviz

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Knowledge Architecture", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化
if "res_map" not in st.session_state:
    st.session_state.res_map = ""
if "res_detail" not in st.session_state:
    st.session_state.res_detail = ""

st.title("🔗 Strategic Knowledge Architecture")
st.caption("理解の『急所』を特定する、高密度・依存関係マップ")

query = st.text_input("整理・解体したい概念:", placeholder="例: CD45のフォスファターゼ活性...")

if st.button("VISUALIZE ARCHITECTURE"):
    with st.spinner("知識の全系譜をスキャン中..."):
        search_res = tavily.search(query=f"{query} mechanism biological basis dependency", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        prompt = f"""
        「{query}」を理解するための知識の系譜を、以下の【厳格なルール】で出力せよ。
        
        ### SECTION 1: MAP
        以下の形式のみで出力せよ。
        PRE:単語:短い役割説明
        POST:単語:実務上の意義
        （PREは最低5つ、POSTは最低3つ出力すること）

        ### SECTION 2: DETAIL
        「{query}」そのものについて、以下の項目を含め、正確かつ詳細に解説せよ。
        1. 根本的な定義と生物学的役割
        2. 信号伝達における具体的なメカニズム
        3. 実務（製造・臨床）における重要性とボトルネック
        4. 今後の課題や議論されている点

        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        full_res = response.choices[0].message.content

        # データの切り分け
        parts = full_res.split("### SECTION 2: DETAIL")
        st.session_state.res_map = parts[0].replace("### SECTION 1: MAP", "").strip()
        st.session_state.res_detail = parts[1].strip() if len(parts) > 1 else "解説の生成に失敗しました。"

# --- 画面描画 ---
if st.session_state.res_map:
    # 1. 図の描画
    st.subheader(f"🌐 Knowledge Genealogy: {query}")
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR', bgcolor='#0e1117', splines='ortho')
    dot.attr('node', fontname='IPAGothic', fontcolor='white', style='filled', shape='record')

    # 中央ターゲット
    dot.node('center', f"{{ 主題 | {query} }}", fillcolor='#d53e4f', fontsize='18', penwidth='3')

    lines = st.session_state.res_map.split('\n')
    for line in lines:
        # 表記ゆれ対策（トリミングと分割）
        if ':' in line:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 3:
                direction, label, desc = parts[0], parts[1], parts[2]
                color = '#1f78b4' if 'PRE' in direction else '#2ca25f'
                
                dot.node(label, f"{{ {label} | {desc} }}", fillcolor=color)
                
                if 'PRE' in direction:
                    dot.edge(label, 'center', color='white', penwidth='1.5')
                else:
                    dot.edge('center', label, color='white', penwidth='1.5')

    st.graphviz_chart(dot)

    # 2. 詳細解説の表示
    st.divider()
    st.subheader(f"📖 Deep Intelligence: {query}")
    st.markdown(st.session_state.res_detail)
