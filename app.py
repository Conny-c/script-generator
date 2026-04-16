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
    page_title="BIGO LIVE 多语言脚本生成器",
    page_icon="🎬",
    layout="wide"
)

# ==================== 语言配置 ====================
LANGUAGES = {
    "越南语": {
        "code": "vi",
        "name": "Tiếng Việt",
        "cta": "Tải APP",
        "speed_factor": 2.5,
        "example": "Bỏ mấy app im lặng đi!"
    },
    "中文": {
        "code": "zh",
        "name": "中文",
        "cta": "下载APP",
        "speed_factor": 2.8,
        "example": "放弃那些无聊的App吧！"
    },
    "英文": {
        "code": "en",
        "name": "English",
        "cta": "Download APP",
        "speed_factor": 2.2,
        "example": "Give up those boring apps!"
    },
    "泰语": {
        "code": "th",
        "name": "ภาษาไทย",
        "cta": "ดาวน์โหลดแอป",
        "speed_factor": 2.3,
        "example": "เลิกใช้แอพที่น่าเบื่อเหล่านั้น!"
    },
    "印尼语": {
        "code": "id",
        "name": "Bahasa Indonesia",
        "cta": "Unduh Aplikasi",
        "speed_factor": 2.4,
        "example": "Tinggalkan aplikasi membosankan itu!"
    },
    "日语": {
        "code": "ja",
        "name": "日本語",
        "cta": "アプリをダウンロード",
        "speed_factor": 2.6,
        "example": "退屈なアプリはもうやめて！"
    },
    "韩语": {
        "code": "ko",
        "name": "한국어",
        "cta": "앱 다운로드",
        "speed_factor": 2.4,
        "example": "지루한 앱들은 그만!"
    },
    "马来语": {
        "code": "ms",
        "name": "Bahasa Melayu",
        "cta": "Muat Turun Apl",
        "speed_factor": 2.4,
        "example": "Tinggalkan aplikasi yang membosankan!"
    },
    "阿拉伯语": {
        "code": "ar",
        "name": "العربية",
        "cta": "تحميل التطبيق",
        "speed_factor": 2.0,
        "example": "تخلى عن تلك التطبيقات المملة!"
    },
    # ========== 新增 ==========
    "西班牙语": {
        "code": "es",
        "name": "Español",
        "cta": "Descargar APP",
        "speed_factor": 2.3,
        "example": "¡Deja esas aplicaciones aburridas!"
    },
    "葡萄牙语": {
        "code": "pt",
        "name": "Português",
        "cta": "Baixar APP",
        "speed_factor": 2.3,
        "example": "Deixe esses aplicativos chatos!"
    }
}

# ==================== API Key 管理 ====================
def get_client():
    api_key = st.session_state.get("api_key", "")
    if not api_key or not api_key.startswith("sk-"):
        return None
    return openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def is_api_ready():
    api_key = st.session_state.get("api_key", "")
    return api_key.startswith("sk-") and len(api_key) > 10

# ==================== 配置管理 ====================
def load_default_config():
    return {
        "personas": {
            "甜妹": {
                "vibes": ["撒娇型", "元气型", "委屈型"],
                "templates": {
                    "撒娇型": ["你是{social_media}脚本写手，为{product} App写{duration}秒口播脚本。\n\n【人设】{persona_desc}\n【语气】撒娇、可爱、带一点点委屈\n\n【脚本结构】\n1. 抱怨竞品\n2. 反转：用户会得到好处\n3. 夸张结果\n4. 身份诱惑\n5. CTA\n\n【要求】\n- 使用{target_lang}\n- {duration}秒\n- 自然口语化\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "元气型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】元气、热情\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "委屈型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】委屈、小抱怨\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"]
                }
            },
            "御姐": {
                "vibes": ["高冷挑衅型", "温柔知性型", "闺蜜吐槽型"],
                "templates": {
                    "高冷挑衅型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】高冷、挑衅\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "温柔知性型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】温柔知性\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "闺蜜吐槽型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】闺蜜吐槽\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"]
                }
            },
            "酷飒": {
                "vibes": ["干脆直接型", "带点不耐烦型"],
                "templates": {
                    "干脆直接型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】干脆直接\n\n【要求】\n- {target_lang}，{duration}秒\n- 短句为主\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "带点不耐烦型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】带点不耐烦\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"]
                }
            },
            "邻家姐姐": {
                "vibes": ["关心型", "分享型"],
                "templates": {
                    "关心型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】关心、真诚\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"],
                    "分享型": ["你是{social_media}脚本写手。\n\n【人设】{persona_desc}\n【语气】分享秘密\n\n【要求】\n- {target_lang}，{duration}秒\n- 结尾：{cta}\n\n只输出脚本正文。"]
                }
            }
        },
        "product_hooks": {
            "女生主动发消息": "女生会主动给你发消息 / Girls will message you first",
            "成为热门/特权人物": "成为热门/特权人物 / Become a hot person",
            "收礼物/被宠": "收到礼物/被宠爱 / Receive gifts",
            "不孤单/秒回": "不再孤单/秒回消息 / No more loneliness",
            "有趣的直播内容": "有趣的直播内容 / Interesting live content"
        }
    }

def load_config():
    if "config" not in st.session_state:
        st.session_state.config = load_default_config()
    return st.session_state.config

def save_config(config):
    st.session_state.config = config

# ==================== 生成函数 ====================
def generate_script(persona, vibe, product_hook, target_lang, duration_seconds=15):
    """生成指定语言的脚本"""
    client = get_client()
    if not client:
        return None
    
    config = load_config()
    template_raw = config["personas"].get(persona, {}).get("templates", {}).get(vibe, [None])[0]
    
    if not template_raw:
        return None
    
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["越南语"])
    
    # 人设描述
    persona_desc_map = {
        "甜妹": "甜妹，20-22岁，声音软糯可爱",
        "御姐": "御姐，25-27岁，高冷有气质",
        "酷飒": "酷飒女生，23-25岁，穿搭潮、表情酷",
        "邻家姐姐": "邻家姐姐，24-26岁，温柔有亲和力"
    }
    persona_desc = persona_desc_map.get(persona, persona)
    
    # 替换模板变量
    template = template_raw.format(
        social_media="社交媒体",
        product="BIGO LIVE",
        duration=duration_seconds,
        target_lang=lang_config["name"],
        cta=lang_config["cta"],
        persona_desc=persona_desc
    )
    
    # 获取卖点翻译
    hook_text = config.get("product_hooks", {}).get(product_hook, product_hook)
    if " / " in hook_text:
        hook_text = hook_text.split(" / ")[0] if target_lang == "中文" else hook_text.split(" / ")[1]
    
    # 估算字数
    estimated_words = int(duration_seconds * lang_config["speed_factor"])
    word_range = f"{max(10, estimated_words - 8)}-{estimated_words + 8}"
    
    full_prompt = template + f"""

【本次生成要求】
🎯 目标语言：{lang_config['name']}
⏱️ 目标时长：{duration_seconds}秒
📝 目标字数：约{word_range}个词
💎 产品卖点：{hook_text}
🔗 CTA：{lang_config['cta']}

【语言要求】
- 必须使用{lang_config['name']}
- 自然口语化，像真人说话
- 不要直译，要符合当地表达习惯

请严格按照要求生成{duration_seconds}秒的{lang_config['name']}脚本。
只输出脚本正文，不要任何解释。
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=random.uniform(0.9, 1.3),
            frequency_penalty=random.uniform(0.3, 0.7),
            presence_penalty=random.uniform(0.3, 0.7),
            max_tokens=500
        )
        script = response.choices[0].message.content.strip()
        
        # 字数统计
        word_count = len(script.split())
        if target_lang == "中文":
            word_count = len(script)
        
        estimated_duration = round(word_count / lang_config["speed_factor"])
        
        # 翻译成中文供检查（如果不是中文）
        translation = script
        if target_lang != "中文":
            translation = translate_to_chinese(script, lang_config["name"])
        
        return {
            "script": script,
            "translation": translation,
            "word_count": word_count,
            "estimated_duration": estimated_duration
        }
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None

def translate_to_chinese(text, source_lang):
    """翻译成中文"""
    client = get_client()
    if not client:
        return "[翻译需要 API Key]"
    
    prompt = f"将以下{source_lang}翻译成中文，只输出翻译结果：\n\n{text}"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except:
        return "[翻译失败]"

# ==================== 初始化 Session ====================
if "scripts" not in st.session_state:
    st.session_state.scripts = []

# ==================== UI ====================
st.title("🎬 BIGO LIVE 多语言脚本生成器")
st.markdown("支持越南语、中文、英文、泰语、印尼语、日语、韩语等")

# ==================== 左侧边栏 ====================
with st.sidebar:
    st.header("🔑 API 设置")
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
    
    st.header("🎮 生成设置")
    
    config = load_config()
    personas = list(config["personas"].keys())
    
    col1, col2 = st.columns(2)
    with col1:
        persona = st.selectbox("👩 人设", personas)
    with col2:
        vibe = st.selectbox("🎭 语气", config["personas"][persona]["vibes"])
    
    # 语言选择
    st.subheader("🌍 输出语言")
    target_lang = st.selectbox(
        "脚本语言",
        list(LANGUAGES.keys()),
        index=0,
        help="选择要生成的脚本语言"
    )
    
    # 显示语言示例
    lang_example = LANGUAGES[target_lang]["example"]
    st.caption(f"💬 示例：{lang_example}")
    
    # 卖点选择
    product_hooks = list(config.get("product_hooks", {}).keys())
    product_hook = st.selectbox("💎 卖点", product_hooks)
    
    # 时长设置
    st.subheader("⏱️ 时长设置")
    duration = st.selectbox("脚本时长", ["15秒", "30秒", "45秒", "60秒"], index=0)
    duration_map = {"15秒": 15, "30秒": 30, "45秒": 45, "60秒": 60}
    duration_seconds = duration_map.get(duration, 15)
    
    lang_speed = LANGUAGES[target_lang]["speed_factor"]
    st.caption(f"💡 目标 {duration_seconds} 秒，约 {int(duration_seconds * lang_speed)} 个词")
    
    num_scripts = st.slider("📝 生成数量", 1, 5, 1)
    
    st.divider()
    
    generate_btn = st.button("🚀 生成脚本", type="primary", use_container_width=True)
    
    if st.button("🗑️ 清空列表", use_container_width=True):
        st.session_state.scripts = []
        st.rerun()

# ==================== 主区域 ====================
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
        lang_display = LANGUAGES[target_lang]["name"]
        status_text.text(f"正在生成第 {i+1}/{num_scripts} 条（{lang_display}，{duration_seconds}秒）...")
        
        result = generate_script(persona, vibe, product_hook, target_lang, duration_seconds)
        
        if result:
            st.session_state.scripts.insert(0, {
                "persona": persona,
                "vibe": vibe,
                "product_hook": product_hook,
                "language": target_lang,
                "duration": duration_seconds,
                "word_count": result["word_count"],
                "script": result["script"],
                "translation": result["translation"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        progress_bar.progress((i + 1) / num_scripts)
        time.sleep(0.3)
    
    status_text.text(f"✅ 生成完成！共 {num_scripts} 条 {lang_display} 脚本")
    st.rerun()

# 显示脚本列表
if st.session_state.scripts:
    for idx, script in enumerate(st.session_state.scripts[:30]):
        lang_emoji = {
            "越南语": "🇻🇳", "中文": "🇨🇳", "英文": "🇬🇧",
            "泰语": "🇹🇭", "印尼语": "🇮🇩", "日语": "🇯🇵",
            "韩语": "🇰🇷", "马来语": "🇲🇾", "阿拉伯语": "🇸🇦"
        }.get(script.get("language", ""), "🌐")
        
        duration_info = f" | ⏱️ {script.get('duration', '?')}秒"
        word_info = f" | 📝 {script.get('word_count', '?')}词"
        
        with st.expander(f"📝 #{idx+1} | {lang_emoji} {script['language']} | {script['persona']} - {script['vibe']} | {script['product_hook']}{duration_info}{word_info}"):
            col_v, col_t = st.columns(2)
            with col_v:
                lang_name = script.get("language", "脚本")
                st.markdown(f"**{lang_emoji} {lang_name}**")
                st.code(script['script'], language="text")
            with col_t:
                st.markdown("**🇨🇳 中文翻译**")
                st.code(script['translation'], language="text")
else:
    st.info("👈 在左侧选择语言、人设、语气、卖点，然后点击「生成脚本」")

# 页脚
st.divider()
st.caption("💡 支持多语言：越南语、中文、英文、泰语、印尼语、日语、韩语、马来语、阿拉伯语")
