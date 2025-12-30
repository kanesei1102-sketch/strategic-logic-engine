import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import graphviz

# --- 初期設定 ---
st.set_page_config(page_title="Strategic Knowledge Map", layout="wide")

# Secretsチェック
if "TAVILY_API_KEY" not in st.secrets or "OPENAI_API_KEY" not in st.secrets:
    st.error("SecretsにAPIキーが設定されていません。")
    st.stop()

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "map_data" not in st.session_state:
    st.session_state.map_data = ""
if "detail_data" not in st.session_state:
    st.session_state.detail_data = ""

st.title("🧠 Strategic Knowledge Map")
st.caption("『絶対不可欠』な知識のみを抽出・可視化する")

# --- 凡例 ---
st.markdown("""
<div style="display: flex; gap: 20px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #1f78b4; border-radius: 50%; margin-right: 5px;"></span><b>前提 (PRE)</b>: これを知らないと始まらない基礎</div>
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #2ca25f; border-radius: 50%; margin-right: 5px;"></span><b>応用 (POST)</b>: 技術がもたらす最大の価値</div>
    <div style="display: flex; align-items: center;"><span style="display: inline-block; width: 15px; height: 15px; background-color: #e6550d; border-radius: 50%; margin-right: 5px;"></span><b>課題 (ISSUE)</b>: 現場で直面する最大の壁</div>
</div>
""", unsafe_allow_html=True)

query = st.text_input("解体したい概念:", placeholder="例: CD3, T細胞, Cellares...")

if st.button("GENERATE STAKEHOLDER MAP"):
    with st.spinner("情報を厳選・構造化中..."):
        search_res = tavily.search(query=f"{query} mechanism importance future bottleneck", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        # プロンプト：3x3x3の厳選構成を指示
        prompt = f"""
        「{query}」を中心としたステークホルダー図を作るために、以下のデータを生成せよ。
        各カテゴリ【厳選して3つずつ】、合計9個の要素を出力すること。
        
        ### SECTION 1: NODES
        形式: TYPE:単語:短い役割
        
        TYPEの分類（以下の3種のみ）:
        1. PRE: これを知らないと理解不能になる「絶対不可欠な前提知識」×3つ
        2. POST: この技術がもたらす「最も重要な実務価値・応用先」×3つ
        3. ISSUE: 実用化を阻む「最大のボトルネック・課題」×3つ
        
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
    dot.attr('edge', color='white', len='3.0', penwidth='2.0')

    # 中心ノード
    dot.node('root', f"{query}\n(中心)", shape='doublecircle', fillcolor='#d53e4f', width='2.8', fontsize='16')

    lines = st.session_state.map_data.split('\n')
    for line in lines:
        if ':' in line:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 3:
                kind, label, desc = parts[0].upper(), parts[1], parts[2] # kindを大文字に統一
                
                # 分類ロジックの強化（部分一致で判定）
                if 'PRE' in kind:
                    color = '#1f78b4' # 青
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    dot.edge(label, 'root') # 矢印：自分 -> 中心
                    
                elif 'POST' in kind:
                    color = '#2ca25f' # 緑
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    dot.edge('root', label) # 矢印：中心 -> 自分
                    
                elif 'ISSUE' in kind:
                    color = '#e6550d' # オレンジ
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.2', fontsize='10')
                    dot.edge('root', label, style='dashed', color='#e6550d') # 点線
                
                # 万が一どれにも当てはまらない場合（エラー回避）
                else:
                    color = '#555555' # グレー
                    dot.node(label, f"{label}\n\n{desc}", shape='circle', fillcolor=color, width='2.0', fontsize='10')
                    dot.edge('root', label, style='dotted')

    st.graphviz_chart(dot)

    st.divider()
    st.subheader("📖 Deep Intelligence Report")
    st.markdown(st.session_state.detail_data)
