import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import streamlit.components.v1 as components

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Logic Engine", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "all_data" not in st.session_state:
    st.session_state.all_data = None
if "logic_unlocked" not in st.session_state:
    st.session_state.logic_unlocked = False

st.title("🧠 Strategic Logic Engine")
st.caption("Cognicull-inspired Hierarchical Mapping")

# --- 検索・解析実行 ---
query = st.text_input("解体したい専門用語を入力:", placeholder="例: T細胞, フォスファターゼ...")

if st.button("ACTIVATE SCAN"):
    with st.spinner("知識のネットワークを構築中..."):
        search_res = tavily.search(query=query, search_depth="advanced", max_results=5)
        context = "\n".join([r['content'] for r in search_res['results']])

        # AI解析 (Mermaidの文法を極限までシンプルに指定)
        prompt = f"""
        「{query}」を解析し、以下の形式で出力せよ。
        
        #MERMAID
        mindmap
          root(({query}))
            Lv1_基礎の本質
              Lv3_専門メカニズム
                Lv5_現場の課題
        
        #LV1_DETAIL
        中学生でもわかる比喩での説明
        #LV3_DETAIL
        専門的な分子メカニズムの説明
        #LV5_DETAIL
        実戦的なボトルネックの説明
        
        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        st.session_state.all_data = response.choices[0].message.content
        st.session_state.logic_unlocked = False

# --- 表示ロジック ---
if st.session_state.all_data:
    data = st.session_state.all_data
    
    # データの切り出し
    try:
        mermaid_part = data.split("#MERMAID")[1].split("#LV1_DETAIL")[0].strip()
        lv1_text = data.split("#LV1_DETAIL")[1].split("#LV3_DETAIL")[0].strip()
        lv3_text = data.split("#LV3_DETAIL")[1].split("#LV5_DETAIL")[0].strip()
        
        st.subheader("🌐 Knowledge Map Scan")
        # Mermaidの描画（エラー回避のために初期化コードを強化）
        m_html = f"""
        <div class="mermaid">
        {mermaid_part}
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
            mermaid.contentLoaded();
        </script>
        """
        components.html(m_html, height=500)

        st.divider()
        with st.expander("✅ Lv1: 基礎の本質 (開示済み)"):
            st.write(lv1_text)
        
        if not st.session_state.logic_unlocked:
            st.warning("🔒 次のレベルを解禁するには、論理を説明してください。")
            if st.button("ゲートを解禁 (学習モード)"):
                st.session_state.logic_unlocked = True
                st.rerun()
        else:
            with st.expander("✅ Lv3: 専門メカニズム"):
                st.write(lv3_text)
    except:
        st.error("解析に失敗しました。もう一度スキャンしてください。")
