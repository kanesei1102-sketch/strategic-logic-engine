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

# --- 凡例（レジェンド）の表示 ---
st.markdown("""
<div style="display: flex; gap: 20px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #1f78b4; border-radius: 50%; margin-right: 5px;"></span><b>前提・基礎 (PRE)</b>: 中心へ向かう矢印</div>
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #2ca25f; border-radius: 50%; margin-right: 5px;"></span><b>応用・実務 (POST)</b>: 外へ広がる矢印</div>
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #e6550d; border-radius: 50%; margin-right: 5px;"></span><b>課題・壁 (ISSUE)</b>: オレンジ・点線</div>
</div>
""", unsafe_allow_html=True)

query = st.text_input("解体したい概念:", placeholder="例: CD3, T細胞, Cellares...")

if st.button("GENERATE STAKEHOLDER MAP"):
    with st.spinner("知識の宇宙を構築中..."):
        search_res = tavily.search(query=f"{query} mechanism importance future", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        prompt = f"""
        「{query}」を中心としたステークホルダー図を作るために、以下のデータを生成せよ。
        
        ### SECTION 1: NODES
        計8個〜10個出力せよ。
        TYPE:単語:短い役割
        
        TYPEの分類（厳守）:
        - PRE: 理解に必要な前提知識（基礎・原理）
        - POST: 応用・実務・メリット（出口）
        - ISSUE: 課題・ボトルネック（現場の壁）
        
        ### SECTION 2: DETAIL
        「{query}」についての詳細な学術・実務解説（マークダウン形式）。

        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        full_res = response.choices[0].message.content

        parts = full_res.split("### SECTION 2: DETAIL")
        st.session_state.map_data = parts[0].replace("### SECTION 1: NODES", "").strip()
        st.session_state.detail_data = parts[1].strip() if len(parts) > 1 else "解説生成エラー"

# --- 描画ロジック ---
if st.session_state.map_data:
    st.subheader(f"🌐 Stakeholder Map: {query}")
    
    dot = graphviz.Digraph(engine='twopi') 
    dot.attr(bgcolor='#0e1117', overlap='false', splines='true', ranksep='3.5')
    dot.attr('node', fontname='IPAGothic', fontcolor='white', style='filled', fixedsize='true')
    dot.attr('edge', color='white', len='3.0', penwidth='1.5') # エッジを太く

    # 中心ノード
    dot.node('root', f"{query}\n(中心)", shape='doublecircle', fillcolor='#d53e4f', width='2.8', fontsize='16')

    lines = st.session_state.map_data.split('\n')
    for line in lines:
        if ':' in line:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 3:
                kind, label, desc = parts[0], parts[1], parts[2]
                
                # 色と矢印のロジック
                if kind == 'PRE':
                    color = '#1f78b4' # 青
                    # PREは「中心に向かう」矢印 (Label -> Root)
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    dot.edge(label, 'root') 
                    
                elif kind == 'POST':
                    color = '#2ca25f' # 緑
                    # POSTは「中心から出る」矢印 (Root -> Label)
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    dot.edge('root', label)
                    
                else: # ISSUE
                    color = '#e6550d' # オレンジ
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    # 課題は点線で繋ぐ
                    dot.edge('root', label, style='dashed', color='#e6550d')

    st.graphviz_chart(dot)

    st.divider()
    st.subheader("📖 Deep Intelligence Report")
    st.markdown(st.session_state.detail_data)
