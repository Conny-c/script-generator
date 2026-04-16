import streamlit as st
import openai
import pandas as pd
import json
import os
import time
import random
import re
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="BIGO LIVE 脚本生成器",
    page_icon="🎬",
    layout="wide"
)

# ==================== API Key 管理 ====================
def get_client():
    """获取 OpenAI 客户端"""
    api_key = st.session_state.get("api_key", "")
    if not api_key or not api_key.startswith("sk-"):
        return None
    return openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def is_api_ready():
    """检查 API 是否就绪"""
    api_key = st.session_state.get("api_key", "")
    return api_key.startswith("sk-") and len(api_key) > 10

# ==================== 配置管理 ====================
def load_default_config():
    """加载默认配置"""
    return {
        "personas": {
            "甜妹": {
                "vibes": ["撒娇型", "元气型", "委屈型"],
                "templates": {
                    "撒娇型": ["你是一个越南语社交媒体脚本写手，为BIGO LIVE App写15秒口播脚本。\n\n【人设】甜妹，20-22岁，声音软糯\n【语气】撒娇、可爱、带一点点委屈\n\n【脚本结构】\n1. 抱怨竞品\n2. 反转：女生会主动找你\n3. 夸张结果\n4. 身份诱惑\n5. CTA\n\n【要求】\n- 越南语\n- 15秒\n- 语气词：nha, á, cực kỳ\n- 结尾：Tải APP đi nha\n\n只输出脚本正文。"],
                    "元气型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】甜妹，元气满满\n【语气】热情、活泼\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi nè\n\n只输出脚本正文。"],
                    "委屈型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】甜妹，委屈无辜\n【语气】委屈、小抱怨\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi mà\n\n只输出脚本正文。"]
                }
            },
            "御姐": {
                "vibes": ["高冷挑衅型", "温柔知性型", "闺蜜吐槽型"],
                "templates": {
                    "高冷挑衅型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】御姐，高冷\n【语气】干脆、挑衅\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi\n\n只输出脚本正文。"],
                    "温柔知性型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】御姐，温柔知性\n【语气】像姐姐一样分享\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP nha em\n\n只输出脚本正文。"],
                    "闺蜜吐槽型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】御姐，像闺蜜\n【语气】吐槽、真实\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi nghe\n\n只输出脚本正文。"]
                }
            },
            "酷飒": {
                "vibes": ["干脆直接型", "带点不耐烦型"],
                "templates": {
                    "干脆直接型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】酷飒女生\n【语气】干脆、直接\n\n【要求】\n- 越南语，15秒\n- 短句为主\n- 结尾：Tải APP đi\n\n只输出脚本正文。"],
                    "带点不耐烦型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】酷飒女生，有点暴躁\n【语气】带点不耐烦\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi ơi\n\n只输出脚本正文。"]
                }
            },
            "邻家姐姐": {
                "vibes": ["关心型", "分享型"],
                "templates": {
                    "关心型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】邻家姐姐\n【语气】关心、真诚\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP nha, chị đợi em\n\n只输出脚本正文。"],
                    "分享型": ["你是一个越南语社交媒体脚本写手。\n\n【人设】邻家姐姐\n【语气】分享秘密、兴奋\n\n【要求】\n- 越南语，15秒\n- 结尾：Tải APP đi, kể bạn nghe\n\n只输出脚本正文。"]
                }
            }
        },
        "product_hooks": ["女生主动发消息", "成为热门/特权人物", "收礼物/被宠", "不孤单/秒回", "有趣的直播内容"]
    }

def load_config():
    """加载配置（从 session 或默认）"""
    if "config" not in st.session_state:
        st.session_state.config = load_default_config()
    return st.session_state.config

def save_config(config):
    """保存配置到 session"""
    st.session_state.config = config

# ==================== 翻译函数 ====================
def translate_script(script_viet):
    """翻译越南语脚本"""
    client = get_client()
    if not client:
        return "❌ 请先配置 API Key"
    
    prompt = f"""将以下越南语翻译成中文和英文。

输出格式：
中文：xxx
英文：xxx

越南语原文：
{script_viet}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[翻译失败: {e}]"

# ==================== 生成函数 ====================
def generate_script(persona, vibe, product_hook, duration_seconds=15):
    """生成脚本，带时长控制"""
    client = get_client()
    if not client:
        return None
    
    config = load_config()
    template = config["personas"].get(persona, {}).get("templates", {}).get(vibe, [None])[0]
    
    if not template:
        return None
    
    # 根据时长估算字数（越南语正常语速约 2.5-3 字/秒）
    estimated_words = int(duration_seconds * 2.5)
    word_range = f"{max(10, estimated_words - 8)}-{estimated_words + 8}"
    
    full_prompt = template + f"""

【本次生成要求 - 非常重要】
⏱️ 目标时长：{duration_seconds}秒
📝 目标字数：约{word_range}个越南语单词
💎 产品卖点：{product_hook}
🔗 CTA：下载APP（越南语）

【时长控制规则】
- {duration_seconds}秒的脚本，正常语速约 {estimated_words} 个单词
- 如果生成的脚本太长，请删减次要内容
- 如果太短，请增加细节或重复强调关键信息
- 保持人设和语气不变

请严格按照 {duration_seconds}秒 的长度生成越南语脚本。
只输出脚本正文，不要任何解释。
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=random.uniform(0.9, 1.3),
            frequency_penalty=random.uniform(0.3, 0.7),
            presence_penalty=random.uniform(0.3, 0.7),
            max_tokens=400  # 增加到 400，支持 60 秒脚本
        )
        script_viet = response.choices[0].message.content.strip()
        
        # 估算实际时长
        word_count = len(script_viet.split())
        estimated_duration = round(word_count / 2.5)
        
        translation = translate_script(script_viet)
        return {
            "viet": script_viet, 
            "trans": translation,
            "word_count": word_count,
            "estimated_duration": estimated_duration
        }
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None

# ==================== 语言检测 ====================
def detect_language(text):
    """检测脚本语言"""
    viet_chars = ['á', 'à', 'ả', 'ã', 'ạ', 'ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 
                  'â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ', 'đ', 'é', 'è', 'ẻ', 'ẽ', 'ẹ',
                  'ê', 'ế', 'ề', 'ể', 'ễ', 'ệ', 'í', 'ì', 'ỉ', 'ĩ', 'ị',
                  'ó', 'ò', 'ỏ', 'õ', 'ọ', 'ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ',
                  'ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ', 'ú', 'ù', 'ủ', 'ũ', 'ụ',
                  'ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự', 'ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ']
    
    viet_count = sum(1 for c in text if c in viet_chars)
    if viet_count > 3:
        return "vi"
    
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    if len(chinese_chars) > 5:
        return "zh"
    
    if text.isascii() and len(text) > 10:
        return "en"
    
    return "unknown"

# ==================== 脚本分析函数 ====================
def analyze_script(script_text):
    """分析脚本，生成新人设配置"""
    client = get_client()
    if not client:
        return {"error": "请先配置 API Key"}
    
    detected_lang = detect_language(script_text)
    lang_name = {"vi": "越南语", "zh": "中文", "en": "英文", "unknown": "未知"}.get(detected_lang, "未知")
    
    prompt = f"""分析以下{lang_name}社交媒体口播脚本，生成新人设配置。

脚本：{script_text}

输出 JSON 格式（只输出 JSON）：
{{
  "persona_name": "人设名称（中文，2-4字）",
  "persona_desc": "人设描述",
  "vibe_name": "语气名称",
  "vibe_desc": "语气描述",
  "template": "完整的提示词模板（使用{lang_name}，包含人设、语气、结构要求、CTA）",
  "key_phrases": ["关键短语1", "关键短语2"]
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )
        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"error": "解析失败"}
    except Exception as e:
        return {"error": str(e)}

# ==================== 初始化 Session ====================
if "scripts" not in st.session_state:
    st.session_state.scripts = []
if "generated_config" not in st.session_state:
    st.session_state.generated_config = None

# ==================== 顶部 Tab ====================
tab1, tab2, tab3 = st.tabs(["⚙️ 配置管理", "📊 脚本分析", "📁 导入/导出"])

with tab1:
    st.subheader("✏️ 人设和模板配置")
    st.caption("修改人设、语气或模板内容")
    
    config = load_config()
    personas = list(config["personas"].keys())
    
    col1, col2 = st.columns(2)
    with col1:
        edit_persona = st.selectbox("选择人设", personas, key="edit_persona")
    with col2:
        edit_vibe = st.selectbox("选择语气", config["personas"][edit_persona]["vibes"], key="edit_vibe")
    
    # 显示和编辑模板
    templates = config["personas"][edit_persona]["templates"].get(edit_vibe, [])
    if templates:
        edited_template = st.text_area(
            "模板内容",
            value=templates[0],
            height=200,
            help="修改后点击保存"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("💾 保存修改"):
                config["personas"][edit_persona]["templates"][edit_vibe][0] = edited_template
                save_config(config)
                st.success("已保存")
                st.rerun()
        with col2:
            if st.button("➕ 添加新语气"):
                new_vibe = st.text_input("新语气名称", key="new_vibe")
                if new_vibe:
                    config["personas"][edit_persona]["vibes"].append(new_vibe)
                    config["personas"][edit_persona]["templates"][new_vibe] = ["新模板内容..."]
                    save_config(config)
                    st.success(f"已添加语气: {new_vibe}")
                    st.rerun()
    
    # 添加新人设
    with st.expander("➕ 添加新人设"):
        new_persona = st.text_input("人设名称")
        new_persona_desc = st.text_input("描述")
        new_persona_vibes = st.text_input("语气列表（用逗号分隔）", "默认语气")
        
        if st.button("创建新人设"):
            if new_persona:
                vibe_list = [v.strip() for v in new_persona_vibes.split(",")]
                config["personas"][new_persona] = {
                    "vibes": vibe_list,
                    "templates": {v: ["新模板内容..."] for v in vibe_list}
                }
                save_config(config)
                st.success(f"已添加人设: {new_persona}")
                st.rerun()

with tab2:
    st.subheader("📊 脚本分析器")
    st.caption("粘贴任意语言的脚本，AI 会自动分析并生成配置")
    
    analysis_script = st.text_area(
        "粘贴脚本",
        height=150,
        placeholder="支持任何语言：越南语、中文、英文、泰语..."
    )
    
    if analysis_script:
        detected = detect_language(analysis_script)
        lang_display = {"vi": "🇻🇳 越南语", "zh": "🇨🇳 中文", "en": "🇬🇧 英文"}.get(detected, "❓ 未知")
        st.caption(f"检测到语言: {lang_display}")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_btn = st.button("🔍 分析脚本", type="primary", use_container_width=True)
    
    if analyze_btn and analysis_script:
        with st.spinner("分析中..."):
            result = analyze_script(analysis_script)
            if "error" not in result:
                st.session_state.generated_config = result
                st.success("分析完成！")
            else:
                st.error(f"分析失败: {result.get('error')}")
    
    if st.session_state.generated_config and "error" not in st.session_state.generated_config:
        st.divider()
        st.subheader("📋 分析结果")
        
        result = st.session_state.generated_config
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**人设**: {result.get('persona_name', '?')}")
            st.info(f"**描述**: {result.get('persona_desc', '?')}")
        with col2:
            st.info(f"**语气**: {result.get('vibe_name', '?')}")
            st.info(f"**描述**: {result.get('vibe_desc', '?')}")
        
        st.subheader("🔧 生成的模板")
        st.code(result.get('template', '无'), language="text")
        
        if st.button("➕ 添加到配置"):
            config = load_config()
            persona_name = result.get('persona_name', '新人设')
            vibe_name = result.get('vibe_name', '新语气')
            
            if persona_name not in config["personas"]:
                config["personas"][persona_name] = {
                    "vibes": [vibe_name],
                    "templates": {vibe_name: [result.get('template', '')]}
                }
            else:
                config["personas"][persona_name]["vibes"].append(vibe_name)
                config["personas"][persona_name]["templates"][vibe_name] = [result.get('template', '')]
            
            save_config(config)
            st.success(f"已添加: {persona_name} - {vibe_name}")
            st.rerun()

with tab3:
    st.subheader("📁 导入/导出配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**导出当前配置**")
        config_json = json.dumps(load_config(), ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下载配置文件",
            data=config_json,
            file_name="prompts.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        st.markdown("**导入配置文件**")
        uploaded = st.file_uploader("上传 prompts.json", type=["json"])
        if uploaded:
            new_config = json.load(uploaded)
            save_config(new_config)
            st.success("配置已导入")
            st.rerun()
    
    st.divider()
    st.markdown("**重置为默认配置**")
    if st.button("🔄 恢复默认配置", use_container_width=True):
        save_config(load_default_config())
        st.success("已恢复默认配置")
        st.rerun()

# ==================== 左侧边栏（简单生成设置） ====================
with st.sidebar:
    st.title("🎬 脚本生成")
    
    # API Key 设置
    st.subheader("🔑 API 设置")
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
        placeholder="sk-...",
        help="去 platform.deepseek.com 获取"
    )
    if api_key:
        st.session_state.api_key = api_key
    
    if not is_api_ready():
        st.warning("⚠️ 请填写有效的 API Key")
        st.stop()
    else:
        st.success("✅ API 已就绪")
    
    st.divider()
    
    # 生成设置
    st.subheader("🎮 生成设置")
    
    config = load_config()
    personas = list(config["personas"].keys())
    
    persona = st.selectbox("👩 人设", personas)
    vibe = st.selectbox("🎭 语气", config["personas"][persona]["vibes"])
    product_hook = st.selectbox("💎 卖点", config["product_hooks"])
    
    # 时长设置
    st.subheader("⏱️ 时长设置")
    duration = st.selectbox(
        "脚本时长",
        ["15秒", "30秒", "45秒", "60秒"],
        index=0,
        help="选择目标时长，AI 会尽量控制在这个长度"
    )
    
    num_scripts = st.slider("📝 生成数量", 1, 5, 1)
    
    # 时长说明
    duration_map = {"15秒": 15, "30秒": 30, "45秒": 45, "60秒": 60}
    target_seconds = duration_map.get(duration, 15)
    st.caption(f"💡 目标时长 {target_seconds} 秒，约 {int(target_seconds * 2.5)} 个越南语单词")
    
    st.divider()
    
    # 生成按钮
    generate_btn = st.button("🚀 生成脚本", type="primary", use_container_width=True)
    
    # 清空按钮
    if st.button("🗑️ 清空列表", use_container_width=True):
        st.session_state.scripts = []
        st.rerun()

# ==================== 主区域：显示脚本 ====================
st.subheader(f"📜 生成的脚本 ({len(st.session_state.scripts)} 条)")

# 导出按钮
col1, col2 = st.columns([5, 1])
with col2:
    if st.session_state.scripts and st.button("💾 导出 CSV", use_container_width=True):
        df = pd.DataFrame(st.session_state.scripts)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="下载",
            data=csv,
            file_name=f"scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# 生成逻辑
if generate_btn:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(num_scripts):
        status_text.text(f"正在生成第 {i+1}/{num_scripts} 条...")
        result = generate_script(persona, vibe, product_hook)
        
        if result:
            st.session_state.scripts.insert(0, {
                "persona": persona,
                "vibe": vibe,
                "product_hook": product_hook,
                "script_viet": result["viet"],
                "translation": result["trans"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        progress_bar.progress((i + 1) / num_scripts)
        time.sleep(0.3)
    
    status_text.text(f"✅ 生成完成！共 {num_scripts} 条")
    st.rerun()

# 显示脚本列表
if st.session_state.scripts:
    for idx, script in enumerate(st.session_state.scripts[:30]):
        with st.expander(f"📝 #{idx+1} | {script['persona']} - {script['vibe']} | {script['product_hook']}"):
            col_v, col_t = st.columns(2)
            with col_v:
                st.markdown("**🇻🇳 越南语**")
                st.code(script['script_viet'], language="text")
            with col_t:
                st.markdown("**🇨🇳/🇬🇧 中文 & 英文**")
                st.code(script['translation'], language="text")
else:
    st.info("👈 在左侧选择人设、语气、卖点，然后点击「生成脚本」")

# 页脚
st.divider()
st.caption("💡 提示：可以在顶部「配置管理」中修改人设、语气和模板内容")
