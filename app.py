import streamlit as st
from openai import OpenAI
from tavily import TavilyClient
import graphviz

st.set_page_config(page_title="Strategic Knowledge Architecture", layout="wide")

tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🔗 Strategic Knowledge Architecture")
st.caption("理解の『急所』を特定する、高密度・依存関係マップ")

query = st.text_input("整理・解体したい概念:", placeholder="例: CD45のフォスファターゼ活性...")

if st.button("VISUALIZE ARCHITECTURE"):
    with st.spinner("知識の全系譜をスキャン中..."):
        search_res = tavily.search(query=f"{query} mechanism biological basis dependency", search_depth="advanced", max_results=10)
        context = "\n".join([r['content'] for r in search_res['results']])

        # プロンプトを「密度の強制」に書き換え
        prompt = f"""
        「{query}」を理解するための知識の系譜を、以下の【厳格なルール】で出力せよ。
        
        【ルール】
        1. [PRE]（前提知識）: これを理解するために遡るべき基礎を、分子レベルから原理レベルまで【最低5つ】。
        2. [POST]（応用・実務）: これが実務（製造、治療、戦略）でどう生きるかを【最低3つ】。
        3. 重複は禁止。「TARGET」という単語は含めない。
        
        形式：
        PRE:単語:短い役割説明
        POST:単語:実務上の意義
        
        Context: {context}
        """
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        res_text = response.choices[0].message.content

        # --- Graphviz 描画 (密度重視レイアウト) ---
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='#0e1117', splines='ortho', nodesep='0.5', ranksep='1.5')
        dot.attr('node', fontname='IPAGothic', fontcolor='white', style='filled', shape='record')

        # 中央（ターゲット）を際立たせる
        dot.node('center', f"{{ 主題 | {query} }}", fillcolor='#d53e4f', fontsize='18', penwidth='3')

        for line in res_text.split('\n'):
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 3:
                    direction, label, desc = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    color = '#1f78b4' if 'PRE' in direction else '#2ca25f'
                    
                    dot.node(label, f"{{ {label} | {desc} }}", fillcolor=color)
                    
                    if 'PRE' in direction:
                        dot.edge(label, 'center', color='white', penwidth='1.5')
                    else:
                        dot.edge('center', label, color='white', penwidth='1.5')

        st.graphviz_chart(dot)
        
        # 詳しい解説も独立させて表示
        st.divider()
        st.subheader(f"📖 Deep Intelligence: {query}")
        st.write("AIによる詳細解析がここに表示されます。") # ここにAIの解説を繋げる
