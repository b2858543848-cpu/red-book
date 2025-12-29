import streamlit as st
import json
from datetime import datetime
# ========== 新增 LangChain 相关导入 ==========
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# ====================== 页面配置/会话状态 保持不变 ======================
st.set_page_config(
    page_title="小红书爆款文案AI创作助手",
    page_icon="📕",
    layout="wide"
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ====================== 改造核心函数：使用 LangChain 调用模型 ======================
def generate_xiaohongshu_content(api_key, theme, style, length, category):
    """使用 LangChain 调用 Kimi API 生成小红书文案"""
    # 1. 初始化 LangChain 封装的 Chat 模型
    llm = ChatOpenAI(
        model="moonshot-v1-8k",
        openai_api_key=api_key,
        openai_api_base="https://api.moonshot.cn/v1",
        temperature=0.7,
        max_tokens={
            "短（100字内）": 300,
            "中（200字）": 500,
            "长（300字）": 800
        }.get(length, 500)
    )

    # 2. 使用 LangChain 提示模板（替代硬编码字符串）
    system_template = """你是一名小红书爆款文案创作专家，精通各种风格和品类的内容创作。请按照以下要求生成文案：
1. 生成5个吸引人的标题，每个标题包含emoji，不超过20字
2. 撰写正文，分段清晰，每段不超过2行，使用口语化表达
3. 正文中适当添加emoji增强情感
4. 在结尾添加5个相关话题标签，格式如：#话题标签
5. 直接输出文案内容，不要有任何解释或说明
"""
    user_template = """请创作一篇关于【{theme}】的小红书文案。

具体要求：
1. 文案风格：{style}
2. 文案长度：{length}
3. 内容品类：{category}
4. 使用小红书流行语：如"谁懂啊"、"绝绝子"、"亲测有效"等
5. 语气亲切自然，像在和朋友分享
"""
    # 封装为 ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", user_template)
    ])

    # 3. 创建链并调用（替代手动构造 HTTP 请求）
    chain = prompt | llm
    try:
        # 传入变量并调用链
        response = chain.invoke({
            "theme": theme,
            "style": style,
            "length": length,
            "category": category
        })
        return response.content  # LangChain 已解析响应，直接取内容
    except Exception as e:
        return f"生成失败: {str(e)}"

# ====================== 侧边栏/主界面/历史记录/页脚 保持不变 ======================
with st.sidebar:
    st.title("⚙️ 配置")
    api_key = st.text_input(
        "Kimi API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="输入您的Kimi API Key",
        help="请从 https://platform.moonshot.cn 获取API Key"
    )
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key已保存")
    st.divider()
    if st.button("🗑️ 清空历史记录", use_container_width=True):
        st.session_state.chat_history = []
        st.success("历史记录已清空")
        st.rerun()
    st.divider()
    st.markdown("### 💡 使用说明")
    st.markdown("""
    1. 输入Kimi API Key
    2. 设置创作参数
    3. 输入主题
    4. 点击生成按钮
    5. 查看历史记录
    """)

st.title("📕 小红书爆款文案AI创作助手")
st.markdown("### 一键生成高互动的小红书爆款文案")
st.divider()

if not st.session_state.api_key:
    st.warning("⚠️ 请先在左侧输入Kimi API Key")
    st.info("API Key获取地址: https://platform.moonshot.cn/console/api-keys")
    st.stop()

st.subheader("🎯 设置创作参数")
col1, col2, col3, col4 = st.columns(4)
with col1:
    theme = st.text_input(
        "创作主题",
        placeholder="例如：大模型应用、职场技能提升、美妆产品测评",
        help="输入你想要创作的核心主题"
    )
with col2:
    style = st.selectbox(
        "文案风格",
        ["种草", "干货", "测评", "情感", "搞笑", "治愈", "教程"],
        help="选择文案的风格调性"
    )
with col3:
    length = st.selectbox(
        "文案长度",
        ["短（100字内）", "中（200字）", "长（300字）"],
        help="控制文案的详细程度"
    )
with col4:
    category = st.selectbox(
        "内容品类",
        ["美妆", "美食", "职场", "旅行", "数码", "教育", "健康", "其他"],
        help="选择内容所属品类"
    )

st.divider()
if st.button("🚀 生成爆款文案", type="primary", use_container_width=True):
    if not theme:
        st.error("❌ 请输入创作主题！")
    else:
        with st.spinner("🤖 AI正在创作中，请稍候..."):
            content = generate_xiaohongshu_content(
                st.session_state.api_key,
                theme,
                style,
                length,
                category
            )
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.chat_history.append({
                "time": timestamp,
                "theme": theme,
                "style": style,
                "category": category,
                "content": content
            })
            st.subheader("✨ 生成结果")
            st.markdown("---")
            st.markdown(content)
            st.markdown("---")
            col_copy, col_download, _ = st.columns([1, 1, 8])
            with col_copy:
                if st.button("📋 复制文案"):
                    st.code(content, language="markdown")
                    st.success("已复制到剪贴板！")
            with col_download:
                filename = f"小红书文案_{theme}_{timestamp.replace(':', '-')}.txt"
                st.download_button(
                    "💾 下载",
                    content,
                    filename,
                    "text/plain"
                )

st.divider()
if st.session_state.chat_history:
    st.subheader("📚 创作历史")
    for idx, record in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"{record['time']} - {record['theme']} ({record['style']}风格)", expanded=False):
            st.markdown(f"**主题:** {record['theme']}")
            st.markdown(f"**风格:** {record['style']} | **品类:** {record['category']}")
            st.markdown("---")
            st.markdown(record['content'])
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📋 复制", key=f"copy_{idx}"):
                    st.code(record['content'], language="markdown")
                    st.success("已复制！")
            with col2:
                download_filename = f"文案_{record['theme']}_{record['time'].replace(':', '-')}.txt"
                st.download_button(
                    "💾 下载",
                    record['content'],
                    download_filename,
                    key=f"download_{idx}"
                )
else:
    st.info("📝 暂无创作历史，开始生成你的第一篇小红书文案吧！")

st.divider()
st.caption("© 2025 小红书爆款文案AI创作助手 | Powered by Kimi AI & LangChain")
