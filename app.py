import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import graphviz

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Knowledge Map", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "map_data" not in st.session_state:
    st.session_state.map_data = ""
if "detail_data" not in st.session_state:
    st.session_state.detail_data = ""

st.title("🧠 Strategic Knowledge Map")
st.caption("中心概念と、それを取り巻く『前提・応用・課題』を放射状に可視化する")

query = st.text_input("解体したい概念:", placeholder="例: CD3, T細胞, Cellares...")

if st.button("GENERATE STAKEHOLDER MAP"):
    with st.spinner("知識の宇宙を構築中..."):
        # 検索
        search_res = tavily.search(query=f"{query} mechanism importance future", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        # プロンプト：放射状に配置するためのデータを生成
        prompt = f"""
        「{query}」を中心としたステークホルダー図（マインドマップ）を作るために、以下のデータを生成せよ。
        
        ### SECTION 1: NODES
        以下の形式のみで、計8個〜10個出力せよ。
        TYPE:単語:短い役割
        
        TYPEの分類（必ず守ること）:
        - PRE: 理解に必要な前提知識（基礎・原理）
        - POST: 応用・実務・メリット（出口）
        - ISSUE: 課題・ボトルネック（現場の壁）
        
        例:
        PRE:ITAM:信号伝達モチーフ
        POST:CAR-T:細胞製造への応用
        ISSUE:疲弊:持続性の低下
        
        ### SECTION 2: DETAIL
        「{query}」についての詳細な学術・実務解説（マークダウン形式）。

        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        full_res = response.choices[0].message.content

        # データ分割
        parts = full_res.split("### SECTION 2: DETAIL")
        st.session_state.map_data = parts[0].replace("### SECTION 1: NODES", "").strip()
        st.session_state.detail_data = parts[1].strip() if len(parts) > 1 else "解説生成エラー"

# --- 描画ロジック ---
if st.session_state.map_data:
    st.subheader(f"🌐 Stakeholder Map: {query}")
    
    # ★ここがポイント：放射状エンジン 'twopi' を使用★
    dot = graphviz.Digraph(engine='twopi') 
    
    # 全体のスタイル：黒背景、重なり防止
    dot.attr(bgcolor='#0e1117', overlap='false', splines='true', ranksep='3.0')
    dot.attr('node', fontname='IPAGothic', fontcolor='white', style='filled', fixedsize='true')
    dot.attr('edge', color='white', len='2.5') # エッジの長さを指定して広げる

    # 1. 中心ノード（赤色・大きめ）
    dot.node('root', f"{query}\n(中心)", shape='doublecircle', fillcolor='#d53e4f', width='2.5', fontsize='16')

    # 2. 周辺ノードの配置
    lines = st.session_state.map_data.split('\n')
    for line in lines:
        if ':' in line:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 3:
                kind, label, desc = parts[0], parts[1], parts[2]
                
                # タイプごとの色分け
                if kind == 'PRE':
                    color = '#1f78b4' # 青（基礎）
                elif kind == 'POST':
                    color = '#2ca25f' # 緑（応用）
                else:
                    color = '#e6550d' # オレンジ（課題）
                
                # バブルの描画（円形）
                # ラベルに改行を入れて、バブルの中に文字を収める
                node_label = f"{label}\n\n{desc}"
                dot.node(label, node_label, shape='circle', fillcolor=color, width='2.2', fontsize='10')
                
                # 中心と繋ぐ
                dot.edge('root', label)

    st.graphviz_chart(dot)

    # 詳細解説
    st.divider()
    st.subheader("📖 Deep Intelligence Report")
    st.markdown(st.session_state.detail_data)
