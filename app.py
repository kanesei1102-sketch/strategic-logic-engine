import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import streamlit.components.v1 as components
import re

# --- 1. 初期設定 ---
st.set_page_config(page_title="Strategic Logic Engine", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "analysis_raw" not in st.session_state:
    st.session_state.analysis_raw = None
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

st.title("🧠 Strategic Logic Engine")
st.caption("Cognicull-inspired Learning System")

# --- 2. 検索・解析実行 ---
query = st.text_input("解体したい専門用語を入力:", placeholder="例: T細胞, CD45, ZAP-70...")

if st.button("ACTIVATE SCAN"):
    with st.spinner("AI参謀が構造化データを構築中..."):
        # Tavily検索 (生データの取得)
        search_res = tavily.search(query=query, search_depth="advanced", max_results=5)
        context = "\n".join([r['content'] for r in search_res['results']])

        # OpenAI解析 (構造を厳密に指定)
        prompt = f"""
        「{query}」を解析し、以下の4つのブロックのみを出力せよ。余計な挨拶や説明は一切不要。
        
        @@@MAP
        mindmap
          root(({query}))
            Lv1_Basic
              Lv3_Mechanism
                Lv5_Industrial_Issue
        
        @@@LV1
        (中学生向けの比喩での一文解説)
        
        @@@LV3
        (専門的な分子メカニズムの解説)
        
        @@@LV5
        (Cellares等の製造現場での実戦的課題)
        
        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        st.session_state.analysis_raw = response.choices[0].message.content
        st.session_state.unlocked = False

# --- 3. 描画とロジック ---
if st.session_state.analysis_raw:
    raw = st.session_state.analysis_raw
    
    try:
        # 文字列を分割
        map_code = raw.split("@@@MAP")[1].split("@@@LV1")[0].strip()
        lv1_detail = raw.split("@@@LV1")[1].split("@@@LV3")[0].strip()
        lv3_detail = raw.split("@@@LV3")[1].split("@@@LV5")[0].strip()
        lv5_detail = raw.split("@@@LV5")[1].strip()

        # マインドマップ描画
        st.subheader("🌐 Strategic Map Scan")
        m_html = f"""
        <div class="mermaid" style="background-color: #0e1117;">
        {map_code}
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
        </script>
        """
        components.html(m_html, height=450)

        st.divider()
        with st.expander("✅ Lv1: 基礎の本質 (開示中)"):
            st.info(lv1_detail)

        # 論理ゲート
        if not st.session_state.unlocked:
            st.warning("🔒 専門メカニズム(Lv3)を解禁するには、この概念の繋がりを自力で説明してください。")
            if st.button("自分の言葉で理解した（解禁する）"):
                st.session_state.unlocked = True
                st.rerun()
        else:
            with st.expander("✅ Lv3: 専門メカニズム (解禁済み)"):
                st.write(lv3_detail)
            with st.expander("🚀 Lv5: 製造現場・企業の課題"):
                st.write(lv5_detail)
    
    except Exception as e:
        st.error(f"解析フォーマットエラーが発生しました。再度スキャンしてください。")
        st.write("Debug info:", raw) # 万が一のためにAIの回答をそのまま出す
