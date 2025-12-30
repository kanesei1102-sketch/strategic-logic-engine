import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import graphviz

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Knowledge Architecture", layout="wide")

# Secretsの確認
if "OPENAI_API_KEY" not in st.secrets or "TAVILY_API_KEY" not in st.secrets:
    st.error("Streamlit CloudのSettings > Secretsでキーを設定してください。")
    st.stop()

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

st.title("🔗 Strategic Knowledge Architecture")
st.caption("理解の依存関係を可視化し、知識の『系譜』をスキャンする")

# --- 解析実行 ---
query = st.text_input("整理・解体したい概念を入力:", placeholder="例: CD45のフォスファターゼ活性, ZAP-70のリン酸化...")

if st.button("VISUALIZE GENEALOGY"):
    with st.spinner("AI参謀が深層解析を実行中..."):
        # 検索の深化
        search_res = tavily.search(query=f"{query} biological mechanism prerequisite basis detail", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        # プロンプトの最適化
        prompt = f"""
        「{query}」について、以下の2つのセクションで構成されるレポートを生成せよ。

        ### SECTION 1: MAP_DATA
        以下の形式のみで出力せよ。
        PRE:単語:一言役割
        POST:単語:一言メリット

        ### SECTION 2: DEEP_DETAIL
        「{query}」そのものについて、正確かつ詳細に解説せよ。
        1. 根本的な定義と生物学的役割
        2. 信号伝達における具体的なメカニズム
        3. 実務（製造・臨床）における重要性とボトルネック
        4. 今後の課題や議論されている点

        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        st.session_state.analysis_result = response.choices[0].message.content

# --- 画面表示 ---
if st.session_state.analysis_result:
    res = st.session_state.analysis_result
    
    try:
        # データの分割
        parts = res.split("### SECTION 2: DEEP_DETAIL")
        map_lines = parts[0].replace("### SECTION 1: MAP_DATA", "").strip().split('\n')
        detail_text = parts[1].strip()

        # --- A. 知識系譜図 (Graphviz) ---
        st.subheader(f"🌐 Knowledge Genealogy: {query}")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='#0e1117')
        dot.attr('node', fontname='IPAGothic', fontcolor='white', style='filled', shape='record')

        # ターゲットノード
        dot.node('root', f"{{ TARGET | {query} }}", fillcolor='#d53e4f', fontsize='16')

        for line in map_lines:
            if ':' in line:
                elements = line.split(':')
                if len(elements) >= 3:
                    direction, label, desc = elements[0].strip(), elements[1].strip(), elements[2].strip()
                    color = '#1f78b4' if 'PRE' in direction else '#2ca25f'
                    
                    dot.node(label, f"{{ {label} | {desc} }}", fillcolor=color)
                    
                    if 'PRE' in direction:
                        dot.edge(label, 'root', color='white')
                    else:
                        dot.edge('root', label, color='white')

        st.graphviz_chart(dot)

        # --- B. 詳細解説セクション ---
        st.divider()
        st.subheader(f"📖 Deep Intelligence: {query}")
        st.markdown(detail_text)
        
    except Exception as e:
        st.error(f"解析データの表示に失敗しました。: {e}")
