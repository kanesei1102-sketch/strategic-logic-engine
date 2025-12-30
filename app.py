import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import streamlit.components.v1 as components

# --- 1. 初期設定 ---
st.set_page_config(page_title="Strategic Logic Engine", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 状態管理（解禁フラグなど）
if "logic_unlocked" not in st.session_state:
    st.session_state.logic_unlocked = False

st.title("🧠 Strategic Logic Engine")
st.caption("Cognicull-inspired Hierarchical Mapping")

# --- 2. 検索・解析実行 ---
query = st.text_input("解体したい専門用語を入力:", placeholder="例: T細胞, フォスファターゼ...")

if st.button("ACTIVATE SCAN"):
    with st.spinner("知識のネットワークを構築中..."):
        # Tavily検索
        search_res = tavily.search(query=query, search_depth="advanced", max_results=5)
        context = "\n".join([r['content'] for r in search_res['results']])

        # AI解析 (Mermaidコードとレベル別解説を生成)
        prompt = f"""
        「{query}」を解析し、以下の形式で出力せよ。
        
        #MERMAID
        mindmap
          root(({query}))
            [Lv1] 基礎の本質(一文)
              [Lv3] 専門メカニズム(一文)
                [Lv5] 現場の課題(一文)
        
        #LV1_DETAIL
        中学生でもわかる比喩での説明
        #LV3_DETAIL
        専門的な分子メカニズムの説明
        #LV5_DETAIL
        実戦的なボトルネックの説明
        
        #GATE_QUESTION
        Lv1からLv3へ繋がる論理的な理由を問う問題を1つ。
        
        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        st.session_state.all_data = response.choices[0].message.content
        st.session_state.logic_unlocked = False # 検索ごとにロック

# --- 3. 描画と学習ゲート ---
if "all_data" in st.session_state:
    data = st.session_state.all_data
    
    # データの切り出し (簡易版)
    mermaid_part = data.split("#MERMAID")[1].split("#LV1_DETAIL")[0].strip()
    lv1_text = data.split("#LV1_DETAIL")[1].split("#LV3_DETAIL")[0].strip()
    lv3_text = data.split("#LV3_DETAIL")[1].split("#LV5_DETAIL")[0].strip()
    
    # マインドマップの表示
    st.subheader("🌐 Knowledge Map Scan")
    m_html = f"""
    <pre class="mermaid">{mermaid_part}</pre>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    """
    components.html(m_html, height=400)

    # 階層別ドリルダウン
    st.divider()
    with st.expander("✅ Lv1: 基礎の本質 (開示済み)"):
        st.write(lv1_text)

    # 論理ゲート
    if not st.session_state.logic_unlocked:
        st.warning("🔒 次のレベルを解禁するには、論理の繋がりを説明してください。")
        user_ans = st.text_input("Lv1の概念がなぜLv3に繋がるのか、あなたの論理は？")
        if st.button("ゲートを解禁"):
            # ここでAIに判定させることも可能ですが、まずはボタン押下で解禁
            st.session_state.logic_unlocked = True
            st.rerun()
    else:
        with st.expander("✅ Lv3: 専門メカニズム (解禁！)"):
            st.write(lv3_text)
