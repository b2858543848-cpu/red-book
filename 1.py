import streamlit as st
import json
from datetime import datetime
import traceback

# LangChain 核心组件导入
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# ====================== 页面基础配置 ======================
st.set_page_config(
    page_title="小红书爆款文案AI创作助手",
    page_icon="📕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== 会话状态初始化 ======================
def init_session_state():
    """初始化所有会话状态变量"""
    default_states = {
        "chat_history": [],
        "api_key": "",
        "last_generated": "",
        "generate_status": "idle"  # idle / generating / success / error
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ====================== 核心函数：LangChain 驱动的文案生成 ======================
def generate_xiaohongshu_content(api_key, theme, style, length, category):
    """
    使用 LangChain 调用 Kimi API 生成小红书文案
    :param api_key: Kimi API Key
    :param theme: 创作主题
    :param style: 文案风格
    :param length: 文案长度
    :param category: 内容品类
    :return: 生成的文案内容 / 错误信息
    """
    # 长度对应 Token 配置
    length_token_map = {
        "短（100字内）": 300,
        "中（200字）": 500,
        "长（300字）": 800
    }
    max_tokens = length_token_map.get(length, 500)

    try:
        # 1. 初始化 LangChain 封装的 Kimi 聊天模型
        llm = ChatOpenAI(
            model="moonshot-v1-8k",
            openai_api_key=api_key,
            openai_api_base="https://api.moonshot.cn/v1",
            temperature=0.7,  # 创意性控制
            max_tokens=max_tokens,
            timeout=60,  # 超时时间
            max_retries=2  # 重试次数
        )

        # 2. 构建结构化提示模板（LangChain PromptTemplate）
        system_prompt_template = """你是一名小红书爆款文案创作专家，精通各类风格和品类的内容创作，熟悉小红书平台的用户偏好和流行趋势。
请严格按照以下规则生成文案：
1. 标题：生成5个吸引人的标题，每个标题必须包含emoji，字数不超过20字，换行分隔；
2. 正文：根据指定长度撰写，分段清晰（每段不超过2行），使用口语化表达，适当添加emoji增强情感；
3. 流行语：自然融入小红书热门词汇（如"谁懂啊"、"绝绝子"、"亲测有效"、"YYDS"等）；
4. 标签：结尾添加5个高度相关的话题标签，格式为#标签名，标签之间空格分隔；
5. 输出格式：直接输出文案内容，无任何解释、说明或额外文字。"""

        user_prompt_template = """创作主题：{theme}
文案风格：{style}
文案长度：{length}
内容品类：{category}
请按照上述要求创作一篇小红书爆款文案，语气亲切自然，像和朋友分享一样。"""

        # 组合聊天提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template),
            ("human", user_prompt_template)
        ])

        # 3. 创建并调用 LangChain 链（提示模板 + 模型）
        chain = prompt | llm
        response = chain.invoke({
            "theme": theme,
            "style": style,
            "length": length,
            "category": category
        })

        # 返回生成的文案内容
        return response.content, None

    except Exception as e:
        # 详细错误信息（便于调试）
        error_detail = f"错误类型：{type(e).__name__}\n错误信息：{str(e)}\n堆栈信息：{traceback.format_exc()}"
        return None, error_detail

# ====================== 工具函数：文案操作 ======================
def copy_to_clipboard(text):
    """复制文本到剪贴板（Streamlit 实现）"""
    st.code(text, language="markdown")
    st.success("✅ 文案已复制到剪贴板！")

def download_content(text, theme, timestamp):
    """生成下载按钮"""
    filename = f"小红书文案_{theme}_{timestamp.replace(':', '-').replace(' ', '_')}.txt"
    st.download_button(
        label="💾 下载文案",
        data=text,
        file_name=filename,
        mime="text/plain",
        use_container_width=True
    )

# ====================== 侧边栏配置 ======================
with st.sidebar:
    st.title("⚙️ 系统配置")
    st.divider()

    # API Key 输入
    api_key = st.text_input(
        "Kimi API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="请输入你的 Kimi API Key",
        help="API Key 获取地址：https://platform.moonshot.cn/console/api-keys",
        label_visibility="collapsed"
    )

    # 保存 API Key 到会话状态
    if api_key and api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key 已保存！")

    st.divider()

    # 历史记录管理
    st.subheader("📜 历史管理")
    if st.button("🗑️ 清空历史记录", use_container_width=True, type="secondary"):
        st.session_state.chat_history = []
        st.session_state.last_generated = ""
        st.success("✅ 历史记录已清空！")
        st.rerun()

    st.divider()

    # 使用说明
    st.subheader("💡 使用指南")
    st.markdown("""
    ### 操作步骤：
    1. 在上方输入 Kimi API Key
    2. 填写创作主题和参数
    3. 点击「生成爆款文案」按钮
    4. 查看/复制/下载生成的文案
    
    ### 注意事项：
    - API Key 需自行从月之暗面平台获取
    - 创作主题越具体，生成效果越好
    - 生成的文案可直接复制到小红书发布
    """)

    st.divider()
    st.caption("© 2025 小红书文案助手\nPowered by Kimi AI & LangChain")

# ====================== 主界面 ======================
st.title("📕 小红书爆款文案AI创作助手")
st.markdown("### 基于 LangChain + Kimi AI 一键生成高互动文案")
st.divider()

# 检查 API Key 是否配置
if not st.session_state.api_key:
    st.warning("⚠️ 请先在左侧侧边栏输入 Kimi API Key 后再使用！")
    st.info("🔑 API Key 是调用 Kimi AI 的凭证，可从 [月之暗面平台](https://platform.moonshot.cn) 获取")
    st.stop()

# 创作参数配置区
st.subheader("🎯 创作参数配置")
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    theme = st.text_input(
        label="创作主题",
        placeholder="例如：夏日防晒技巧、职场摸鱼神器",
        help="输入核心创作主题，越具体越好",
        value="",
        max_chars=50
    )

with col2:
    style = st.selectbox(
        label="文案风格",
        options=["种草", "干货", "测评", "情感", "搞笑", "治愈", "教程", "探店"],
        index=0,
        help="选择文案的整体风格调性"
    )

with col3:
    length = st.selectbox(
        label="文案长度",
        options=["短（100字内）", "中（200字）", "长（300字）"],
        index=1,
        help="控制文案的字数和详细程度"
    )

with col4:
    category = st.selectbox(
        label="内容品类",
        options=["美妆", "美食", "职场", "旅行", "数码", "教育", "健康", "穿搭", "家居", "其他"],
        index=0,
        help="选择内容所属的品类"
    )

st.divider()

# 生成按钮及结果展示
col_generate, col_empty = st.columns([1, 9])
with col_generate:
    generate_btn = st.button(
        "🚀 生成爆款文案",
        type="primary",
        use_container_width=True,
        disabled=not theme  # 主题为空时禁用按钮
    )

# 生成逻辑处理
if generate_btn:
    st.session_state.generate_status = "generating"
    with st.spinner("🤖 AI 正在创作爆款文案中...请稍候"):
        # 调用生成函数
        content, error = generate_xiaohongshu_content(
            st.session_state.api_key,
            theme,
            style,
            length,
            category
        )

        if content:
            st.session_state.generate_status = "success"
            st.session_state.last_generated = content

            # 保存到历史记录
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.chat_history.append({
                "time": timestamp,
                "theme": theme,
                "style": style,
                "category": category,
                "content": content
            })

            # 展示生成结果
            st.subheader("✨ 生成结果")
            st.markdown("---")
            st.markdown(content)
            st.markdown("---")

            # 操作按钮
            col_copy, col_download = st.columns(2, gap="small")
            with col_copy:
                if st.button("📋 复制文案", use_container_width=True):
                    copy_to_clipboard(content)
            with col_download:
                download_content(content, theme, timestamp)

        else:
            st.session_state.generate_status = "error"
            st.error("❌ 文案生成失败！")
            with st.expander("查看错误详情", expanded=True):
                st.code(error, language="text")

# 历史记录展示区
st.divider()
if st.session_state.chat_history:
    st.subheader("📚 创作历史记录")
    st.markdown(f"共生成 {len(st.session_state.chat_history)} 篇文案")
    st.divider()

    # 倒序展示历史记录
    for idx, record in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(
            label=f"📅 {record['time']} | 主题：{record['theme']} | 风格：{record['style']}",
            expanded=False
        ):
            col_info, col_ops = st.columns([3, 1])
            with col_info:
                st.markdown(f"**品类：** {record['category']}")
                st.markdown("---")
                st.markdown(record['content'])
            with col_ops:
                st.button(
                    "📋 复制",
                    key=f"copy_{idx}",
                    use_container_width=True,
                    on_click=copy_to_clipboard,
                    args=(record['content'],)
                )
                download_content(record['content'], record['theme'], record['time'])
        st.divider()
else:
    if st.session_state.generate_status == "idle":
        st.info("📝 暂无创作历史，填写参数后点击「生成爆款文案」开始创作吧！")
