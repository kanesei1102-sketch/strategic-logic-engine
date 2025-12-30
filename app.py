import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Logic Engine", layout="wide")

# Secretsの存在確認
if "OPENAI_API_KEY" not in st.secrets or "TAVILY_API_KEY" not in st.secrets:
    st.error("Secrets (API Keys) が設定されていません。Settings > Secrets を確認してください。")
    st.stop()

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "unlocked_levels" not in st.session_state:
    st.session_state.unlocked_levels = set(["Lv1"]) # Lv1は最初から解禁

st.title("🧠 Strategic Logic Engine")
st.caption("Cognicull-inspired Hierarchical Mapping")

# --- 検索・解析フェーズ ---
query = st.text_input("解体したい専門用語を入力:", placeholder="例: CD45, フォスファターゼ...")

if st.button("ACTIVATE SCAN"):
    with st.spinner("情報を階層化・構造化中..."):
        # Tavily検索
        search_res = tavily.search(query=query, search_depth="advanced", max_results=5)
        context = "\n".join([f"Content: {r['content']}" for r in search_res['results']])

        # OpenAIによる一括生成
        prompt = f"""
        あなたは Seiji の思考を拡張する『Strategic Logic Engine』です。「{query}」を解析せよ。
        
        ### 1. Mermaid
        中心から [Lv1] [Lv3] [Lv5] へのマインドマップ。ノード名は必ず「[レベル] 本質の一文」にせよ。
        
        ### 2. 解説
        - Lv1: 中学生向けの比喩。
        - Lv3: 分子メカニズム。
        - Lv5: 現場/製造のボトルネック。
        
        ### 3. 論理ゲート問題
        - Q_Lv3: Lv1からLv3へ繋がる論理的理由を問え。
        - Q_Lv5: Lv3からLv5へ繋がる論理的理由を問え。
        
        Data: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        st.session_state.analysis_data = response.choices[0].message.content
        st.session_state.unlocked_levels = set(["Lv1"]) # 検索時はリセット

# --- 表示・学習フェーズ ---
if st.session_state.analysis_data:
    # 1. スキャンモード (Mermaid表示)
    st.subheader("🌐 Knowledge Map Scan")
    # ここにMermaidコードを抽出・描画するロジック (簡易的にテキスト表示も可)
    st.info("バブル内の『本質の一文』で全体を把握してください。詳細を学ぶにはゲートを突破せよ。")

    # 2. ドリルダウン (論理ゲート)
    st.divider()
    
    # Lv1は常に表示
    with st.expander("✅ Lv1: 基礎の本質 (解禁済み)"):
        st.write("ここにLv1の解説を表示")

    # Lv3 ゲート
    if "Lv3" not in st.session_state.unlocked_levels:
        with st.expander("🔓 Lv3: 専門メカニズムを解禁する"):
            st.write("【論理テスト】Lv1からLv3への繋がりを説明せよ。")
            logic_input = st.text_input("論理を記述:", key="input_lv3")
            if st.button("論理を検証", key="btn_lv3"):
                # ここでAI判定（今回はデモ的に合格とするが、実際はAI APIで判定）
                st.session_state.unlocked_levels.add("Lv3")
                st.rerun()
    else:
        with st.expander("✅ Lv3: 専門メカニズム (解禁済み)"):
            st.write("ここにLv3の解説を表示")

    # (Lv5も同様のロジックを配置)
