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
    page_title="BIGO LIVE 多语言脚本生成器 + UAC广告文案",
    page_icon="🎬",
    layout="wide"
)

# ==================== 语言配置 ====================
LANGUAGES = {
    "越南语": {"code": "vi", "name": "Tiếng Việt", "cta": "Tải APP", "speed_factor": 2.5, "example": "Bỏ mấy app im lặng đi!", "char_limit_30": 30, "char_limit_90": 90},
    "中文": {"code": "zh", "name": "中文", "cta": "下载APP", "speed_factor": 2.8, "example": "放弃那些无聊的App吧！", "char_limit_30": 30, "char_limit_90": 90},
    "英文": {"code": "en", "name": "English", "cta": "Download APP", "speed_factor": 2.2, "example": "Give up those boring apps!", "char_limit_30": 30, "char_limit_90": 90},
    "泰语": {"code": "th", "name": "ภาษาไทย", "cta": "ดาวน์โหลดแอป", "speed_factor": 2.3, "example": "เลิกใช้แอพที่น่าเบื่อเหล่านั้น!", "char_limit_30": 30, "char_limit_90": 90},
    "印尼语": {"code": "id", "name": "Bahasa Indonesia", "cta": "Unduh Aplikasi", "speed_factor": 2.4, "example": "Tinggalkan aplikasi membosankan itu!", "char_limit_30": 30, "char_limit_90": 90},
    "日语": {"code": "ja", "name": "日本語", "cta": "アプリをダウンロード", "speed_factor": 2.6, "example": "退屈なアプリはもうやめて！", "char_limit_30": 30, "char_limit_90": 90},
    "韩语": {"code": "ko", "name": "한국어", "cta": "앱 다운로드", "speed_factor": 2.4, "example": "지루한 앱들은 그만!", "char_limit_30": 30, "char_limit_90": 90},
    "马来语": {"code": "ms", "name": "Bahasa Melayu", "cta": "Muat Turun Apl", "speed_factor": 2.4, "example": "Tinggalkan aplikasi yang membosankan!", "char_limit_30": 30, "char_limit_90": 90},
    "阿拉伯语": {"code": "ar", "name": "العربية", "cta": "تحميل التطبيق", "speed_factor": 2.0, "example": "تخلى عن تلك التطبيقات المملة!", "char_limit_30": 30, "char_limit_90": 90},
    "西班牙语": {"code": "es", "name": "Español", "cta": "Descargar APP", "speed_factor": 2.3, "example": "¡Deja esas aplicaciones aburridas!", "char_limit_30": 30, "char_limit_90": 90},
    "葡萄牙语": {"code": "pt", "name": "Português", "cta": "Baixar APP", "speed_factor": 2.3, "example": "Deixe esses aplicativos chatos!", "char_limit_30": 30, "char_limit_90": 90}
}

# ==================== UAC 文案维度配置（智能填充版） ====================

UAC_DIMENSIONS = {
    "user_motives": {
        "loneliness": {"zh": "孤独感", "en": "loneliness", "desc": "用户感到孤单，想找人聊天"},
        "boredom": {"zh": "无聊打发时间", "en": "boredom", "desc": "用户下班/睡前无聊，想找点有趣的事"},
        "curiosity": {"zh": "好奇心", "en": "curiosity", "desc": "用户被新奇事物吸引，想探索"},
        "fomo": {"zh": "害怕错过", "en": "FOMO", "desc": "用户怕错过热门内容或社交机会"},
        "status_seeking": {"zh": "寻求关注/地位", "en": "status seeking", "desc": "用户希望被看见、被认可"}
    },
    "scenarios": {
        "night": {"zh": "深夜独处", "en": "late night", "desc": "用户独自在家/宿舍，睡不着"},
        "commute": {"zh": "通勤路上", "en": "commuting", "desc": "用户坐地铁/公交，碎片时间"},
        "weekend": {"zh": "周末空闲", "en": "weekend", "desc": "用户周末宅家，不知道做什么"},
        "break_time": {"zh": "工作/学习间隙", "en": "break time", "desc": "用户短暂休息，想放松一下"}
    },
    "value_props": {
        "instant_chat": {"zh": "即时聊天", "en": "instant chat", "desc": "立刻和人聊天，不用等"},
        "real_attention": {"zh": "真人关注", "en": "real attention", "desc": "被真人看见、回应、关注"},
        "earning": {"zh": "赚钱/收礼物", "en": "earning", "desc": "通过互动获得收益或礼物"},
        "exclusive": {"zh": "独家体验", "en": "exclusive access", "desc": "普通用户没有的特权/内容"},
        "vip_status": {"zh": "VIP身份", "en": "VIP status", "desc": "身份标识，被特殊对待"}
    },
    "cta_types": {
        "soft": {"zh": "试试看", "en": "Try", "desc": "低门槛，适合探索型用户"},
        "action": {"zh": "立即下载", "en": "Download now", "desc": "直接行动号召"},
        "scarcity": {"zh": "限时/限量", "en": "Join now", "desc": "制造紧迫感"}
    }
}

# 结构模板（定义文案框架，而不是固定文本）
STRUCTURE_TEMPLATES = {
    "问题-解决方案": {
        "template": "【问题描述】？【解决方案】。【行动号召】",
        "description": "先引发共鸣，再给出答案"
    },
    "场景-感受-行动": {
        "template": "【场景】，【感受】。【行动号召】",
        "description": "场景带入 + 情感共鸣"
    },
    "好奇-揭秘": {
        "template": "【悬念】？【揭秘答案】。【行动号召】",
        "description": "制造好奇心，然后满足"
    },
    "对比-冲击": {
        "template": "与其【旧行为】，不如【新价值】。【行动号召】",
        "description": "对比产生吸引力"
    },
    "直接-利益": {
        "template": "【核心利益】。【行动号召】",
        "description": "最直接，适合信息流"
    },
    "社交-证明": {
        "template": "【数字/群体】都在【行为】，你还在等什么？【行动号召】",
        "description": "从众心理驱动"
    },
    "故事-开头": {
        "template": "【小故事/场景】。【转折】。【行动号召】",
        "description": "用微型故事吸引"
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
            "女生主动发消息": "女生会主动给你发消息",
            "成为热门/特权人物": "成为热门/特权人物",
            "收礼物/被宠": "收到礼物/被宠爱",
            "不孤单/秒回": "不再孤单/秒回消息",
            "有趣的直播内容": "有趣的直播内容"
        }
    }

def load_config():
    if "config" not in st.session_state:
        st.session_state.config = load_default_config()
    return st.session_state.config

def save_config(config):
    st.session_state.config = config

# ==================== 翻译函数 ====================
def translate_to_chinese(text, source_lang):
    client = get_client()
    if not client:
        return "[翻译需要 API Key]"
    prompt = f"将以下{source_lang}翻译成中文，只输出翻译结果：\n\n{text}"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except:
        return "[翻译失败]"

# ==================== UAC 智能文案生成函数 ====================

def generate_uac_smart(
    motive,           # 用户动机
    scenario,         # 使用场景  
    value_prop,       # 价值主张
    cta_type,         # CTA类型
    target_lang,      # 目标语言
    structure_style,  # 结构模板
    char_limit        # 字符限制
):
    """智能生成单条UAC文案"""
    client = get_client()
    if not client:
        return None
    
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["越南语"])
    lang_code = lang_config["code"]
    
    motive_desc = UAC_DIMENSIONS["user_motives"].get(motive, {})
    scenario_desc = UAC_DIMENSIONS["scenarios"].get(scenario, {})
    value_desc = UAC_DIMENSIONS["value_props"].get(value_prop, {})
    cta_desc = UAC_DIMENSIONS["cta_types"].get(cta_type, {})
    structure_info = STRUCTURE_TEMPLATES.get(structure_style, STRUCTURE_TEMPLATES["问题-解决方案"])
    
    hook_text = load_config().get("product_hooks", {}).get(list(load_config().get("product_hooks", {}).keys())[0], "直播社交")
    
    prompt = f"""你是一个UAC广告文案专家，请为直播社交App写一条{char_limit}字符以内的广告文案。

【目标语言】{lang_config['name']}
【产品】BIGO LIVE - 直播社交平台
【核心卖点】{hook_text}
【字符限制】{char_limit}个字符（包括空格和标点）

【文案维度】
- 用户动机：{motive_desc.get(lang_code, motive_desc.get('en', ''))}（{UAC_DIMENSIONS['user_motives'].get(motive, {}).get('desc', '')}）
- 使用场景：{scenario_desc.get(lang_code, scenario_desc.get('en', ''))}（{UAC_DIMENSIONS['scenarios'].get(scenario, {}).get('desc', '')}）
- 核心价值：{value_desc.get(lang_code, value_desc.get('en', ''))}（{UAC_DIMENSIONS['value_props'].get(value_prop, {}).get('desc', '')}）
- 行动号召类型：{cta_desc.get(lang_code, cta_desc.get('en', ''))}

【结构风格】{structure_style} - {structure_info['description']}

【要求】
1. 写一条自然、口语化的广告文案
2. 不要机械拼接关键词，要自然融入语境
3. {char_limit}字符以内
4. 如果语言不是中文，要用{lang_config['name']}自然表达
5. 只输出文案本身，不要任何解释

直接输出文案："""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=200
        )
        ad_text = response.choices[0].message.content.strip()
        
        ad_text = re.sub(r'^["\']|["\']$', '', ad_text)
        ad_text = ad_text.split('\n')[0]
        
        if len(ad_text) > char_limit:
            ad_text = ad_text[:char_limit-1] + "…"
        
        actual_chars = len(ad_text)
        
        translation = ad_text
        if target_lang != "中文":
            translation = translate_to_chinese(ad_text, lang_config["name"])
        
        return {
            "ad_text": ad_text,
            "translation": translation,
            "actual_chars": actual_chars,
            "char_limit": char_limit,
            "is_valid": actual_chars <= char_limit,
            "language": target_lang,
            "motive": motive,
            "scenario": scenario,
            "value_prop": value_prop,
            "cta_type": cta_type,
            "structure": structure_style,
            "dimension_key": f"{motive}_{scenario}_{value_prop}"
        }
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None


def generate_uac_smart_with_variation(
    motive, scenario, value_prop, cta_type, target_lang, 
    structure_style, char_limit, variation_index, total_variations
):
    """带变体编号的智能生成，确保同维度下生成不同文案"""
    client = get_client()
    if not client:
        return None
    
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["越南语"])
    lang_code = lang_config["code"]
    
    motive_desc = UAC_DIMENSIONS["user_motives"].get(motive, {})
    scenario_desc = UAC_DIMENSIONS["scenarios"].get(scenario, {})
    value_desc = UAC_DIMENSIONS["value_props"].get(value_prop, {})
    cta_desc = UAC_DIMENSIONS["cta_types"].get(cta_type, {})
    structure_info = STRUCTURE_TEMPLATES.get(structure_style, STRUCTURE_TEMPLATES["问题-解决方案"])
    
    hook_text = load_config().get("product_hooks", {}).get(list(load_config().get("product_hooks", {}).keys())[0], "直播社交")
    
    variation_hints = [
        "用第一种表达方式，直接一点",
        "换一个完全不同的角度说，要有新意",
        "用更简短有力的方式，一针见血",
        "加入一点情感色彩，让文案有温度",
        "用反问句开头，引发思考",
        "用场景代入的方式，让用户感同身受",
        "强调紧迫感，催促行动",
        "强调社交价值，突出互动乐趣"
    ]
    variation_hint = variation_hints[variation_index % len(variation_hints)]
    
    prompt = f"""你是一个UAC广告文案专家，请为直播社交App写一条{char_limit}字符以内的广告文案。

【目标语言】{lang_config['name']}
【产品】BIGO LIVE - 直播社交平台
【核心卖点】{hook_text}
【字符限制】{char_limit}个字符（包括空格和标点）

【文案维度】
- 用户动机：{motive_desc.get(lang_code, motive_desc.get('en', ''))}
- 使用场景：{scenario_desc.get(lang_code, scenario_desc.get('en', ''))}
- 核心价值：{value_desc.get(lang_code, value_desc.get('en', ''))}
- 行动号召类型：{cta_desc.get(lang_code, cta_desc.get('en', ''))}

【结构风格】{structure_style} - {structure_info['description']}

【第{variation_index + 1}条，共{total_variations}条 - 要求：{variation_hint}】

【要求】
1. 写一条自然、口语化的广告文案
2. {char_limit}字符以内
3. 如果语言不是中文，要用{lang_config['name']}自然表达
4. 只输出文案本身

直接输出文案："""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 + (variation_index * 0.1),
            max_tokens=200
        )
        ad_text = response.choices[0].message.content.strip()
        
        ad_text = re.sub(r'^["\']|["\']$', '', ad_text)
        ad_text = ad_text.split('\n')[0]
        
        if len(ad_text) > char_limit:
            ad_text = ad_text[:char_limit-1] + "…"
        
        actual_chars = len(ad_text)
        
        translation = ad_text
        if target_lang != "中文":
            translation = translate_to_chinese(ad_text, lang_config["name"])
        
        return {
            "ad_text": ad_text,
            "translation": translation,
            "actual_chars": actual_chars,
            "char_limit": char_limit,
            "is_valid": actual_chars <= char_limit,
            "language": target_lang,
            "motive": motive,
            "scenario": scenario,
            "value_prop": value_prop,
            "cta_type": cta_type,
            "structure": structure_style,
            "dimension_key": f"{motive}_{scenario}_{value_prop}",
            "variation_num": variation_index + 1
        }
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None


def generate_uac_batch(params_list, target_lang, char_limit, progress_callback=None):
    """批量生成UAC文案"""
    results = []
    total = len(params_list)
    
    for idx, params in enumerate(params_list):
        if progress_callback:
            progress_callback(idx + 1, total, f"{params['motive']} + {params['scenario']}")
        
        result = generate_uac_smart(
            motive=params["motive"],
            scenario=params["scenario"],
            value_prop=params["value_prop"],
            cta_type=params["cta_type"],
            target_lang=target_lang,
            structure_style=params["structure"],
            char_limit=char_limit
        )
        
        if result:
            result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results.append(result)
        
        time.sleep(0.3)
    
    return results


def generate_full_asset_pool(target_lang, char_limit, include_premium=True):
    """生成完整的素材池"""
    motives = ["loneliness", "boredom", "curiosity"]
    scenarios = ["night", "commute", "weekend"]
    values = ["instant_chat", "real_attention"]
    
    if include_premium:
        values.append("vip_status")
        values.append("exclusive")
    
    cta_types = ["soft", "action"]
    structures = list(STRUCTURE_TEMPLATES.keys())
    
    all_combinations = []
    
    for motive in motives:
        for scenario in scenarios:
            for value in values:
                for cta in cta_types:
                    for structure in structures[:2]:
                        all_combinations.append({
                            "motive": motive,
                            "scenario": scenario,
                            "value_prop": value,
                            "cta_type": cta,
                            "structure": structure
                        })
    
    seen = set()
    unique_combinations = []
    for combo in all_combinations:
        key = f"{combo['motive']}_{combo['scenario']}_{combo['value_prop']}"
        if key not in seen:
            seen.add(key)
            unique_combinations.append(combo)
    
    return unique_combinations[:40]


# ==================== 口播脚本生成函数 ====================
def generate_script(persona, vibe, product_hook, target_lang, duration_seconds=15):
    client = get_client()
    if not client:
        return None
    
    config = load_config()
    template_raw = config["personas"].get(persona, {}).get("templates", {}).get(vibe, [None])[0]
    if not template_raw:
        return None
    
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["越南语"])
    
    persona_desc_map = {
        "甜妹": "甜妹，20-22岁，声音软糯可爱",
        "御姐": "御姐，25-27岁，高冷有气质",
        "酷飒": "酷飒女生，23-25岁，穿搭潮、表情酷",
        "邻家姐姐": "邻家姐姐，24-26岁，温柔有亲和力"
    }
    persona_desc = persona_desc_map.get(persona, persona)
    
    template = template_raw.format(
        social_media="社交媒体",
        product="BIGO LIVE",
        duration=duration_seconds,
        target_lang=lang_config["name"],
        cta=lang_config["cta"],
        persona_desc=persona_desc
    )
    
    hook_text = config.get("product_hooks", {}).get(product_hook, product_hook)
    estimated_words = int(duration_seconds * lang_config["speed_factor"])
    word_range = f"{max(10, estimated_words - 8)}-{estimated_words + 8}"
    
    full_prompt = template + f"""

【本次生成要求】
🎯 目标语言：{lang_config['name']}
⏱️ 目标时长：{duration_seconds}秒
📝 目标字数：约{word_range}个词
💎 产品卖点：{hook_text}
🔗 CTA：{lang_config['cta']}

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
        
        word_count = len(script.split())
        if target_lang == "中文":
            word_count = len(script)
        
        estimated_duration = round(word_count / lang_config["speed_factor"])
        
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


# ==================== 脚本分析函数 ====================
def detect_language(text):
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

def analyze_script(script_text):
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
if "uac_ads" not in st.session_state:
    st.session_state.uac_ads = []
if "generated_config" not in st.session_state:
    st.session_state.generated_config = None

# ==================== 顶部 Tab ====================
main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs(["🎙️ 口播脚本生成", "📱 UAC 广告文案", "⚙️ 配置管理", "📊 脚本分析", "📁 导入/导出"])


# ==================== UAC 广告文案 Tab ====================
with main_tab2:
    st.header("📱 UAC 广告文案生成器")
    st.caption("基于用户动机 × 场景 × 价值的智能文案生成，AI自然填充而非机械拼接")
    
    if not is_api_ready():
        st.warning("⚠️ 请先在「口播脚本生成」页面填写有效的 API Key")
    else:
        st.success("✅ API 已就绪")
    
    st.divider()
    
    gen_mode = st.radio(
        "生成模式",
        ["🎯 精准定制（手动选择维度）", "🚀 批量素材池（自动生成全集）"],
        horizontal=True,
        help="精准定制：手动选择维度和结构，生成多条 | 批量素材池：自动组合所有维度"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        uac_target_lang = st.selectbox("🌍 目标语言", list(LANGUAGES.keys()), key="uac_lang")
        uac_char_type = st.radio("📏 字符限制", ["30字符", "90字符"], horizontal=True, key="uac_char")
        char_limit = 30 if uac_char_type == "30字符" else 90
        include_premium = st.checkbox("✨ 包含付费意图文案", value=True, help="VIP身份、独家体验等高价值文案（仅批量模式生效）")
    
    with col2:
        if gen_mode == "🎯 精准定制（手动选择维度）":
            motive_options = list(UAC_DIMENSIONS["user_motives"].keys())
            scenario_options = list(UAC_DIMENSIONS["scenarios"].keys())
            value_options = list(UAC_DIMENSIONS["value_props"].keys())
            cta_options = list(UAC_DIMENSIONS["cta_types"].keys())
            structure_options = list(STRUCTURE_TEMPLATES.keys())
            
            motive = st.selectbox("🎯 用户动机", motive_options,
                                  format_func=lambda x: f"{UAC_DIMENSIONS['user_motives'][x]['zh']} - {UAC_DIMENSIONS['user_motives'][x]['desc']}")
            scenario = st.selectbox("🕐 使用场景", scenario_options,
                                    format_func=lambda x: f"{UAC_DIMENSIONS['scenarios'][x]['zh']} - {UAC_DIMENSIONS['scenarios'][x]['desc']}")
            value_prop = st.selectbox("💎 核心价值", value_options,
                                      format_func=lambda x: f"{UAC_DIMENSIONS['value_props'][x]['zh']} - {UAC_DIMENSIONS['value_props'][x]['desc']}")
            cta_type = st.selectbox("📢 CTA类型", cta_options,
                                    format_func=lambda x: f"{UAC_DIMENSIONS['cta_types'][x]['zh']} - {UAC_DIMENSIONS['cta_types'][x]['desc']}")
            structure = st.selectbox("📝 结构模板", structure_options,
                                     format_func=lambda x: f"{x} - {STRUCTURE_TEMPLATES[x]['description']}")
            custom_num = st.slider("📝 生成数量（相同维度生成多条变体）", 1, 10, 3)
        else:
            batch_size = st.slider("📊 生成数量", 10, 50, 25)
            st.caption("💡 系统会自动组合动机×场景×价值，由AI自然填充生成")
    
    st.divider()
    
    with st.expander("📖 完整维度说明（点击展开）", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🎯 用户动机**")
            for k, v in UAC_DIMENSIONS["user_motives"].items():
                st.caption(f"• **{v['zh']}**：{v['desc']}")
            st.markdown("**🕐 使用场景**")
            for k, v in UAC_DIMENSIONS["scenarios"].items():
                st.caption(f"• **{v['zh']}**：{v['desc']}")
            st.markdown("**📢 CTA类型**")
            for k, v in UAC_DIMENSIONS["cta_types"].items():
                st.caption(f"• **{v['zh']}**：{v['desc']}")
        with col_b:
            st.markdown("**💎 核心价值**")
            for k, v in UAC_DIMENSIONS["value_props"].items():
                st.caption(f"• **{v['zh']}**：{v['desc']}")
            st.markdown("**📝 结构模板**")
            for k, v in STRUCTURE_TEMPLATES.items():
                st.caption(f"• **{k}**：{v['description']}")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        generate_btn = st.button("🚀 生成文案", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ 清空列表", use_container_width=True):
            st.session_state.uac_ads = []
            st.rerun()
    
    if generate_btn and is_api_ready():
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_new_ads = []
        
        if gen_mode == "🎯 精准定制（手动选择维度）":
            for i in range(custom_num):
                status_text.text(f"正在生成第 {i+1}/{custom_num} 条...")
                result = generate_uac_smart_with_variation(
                    motive=motive, scenario=scenario, value_prop=value_prop,
                    cta_type=cta_type, target_lang=uac_target_lang,
                    structure_style=structure, char_limit=char_limit,
                    variation_index=i, total_variations=custom_num
                )
                if result:
                    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    all_new_ads.append(result)
                progress_bar.progress((i + 1) / custom_num)
                time.sleep(0.2)
        else:
            status_text.text("正在构建维度组合...")
            combinations = generate_full_asset_pool(uac_target_lang, char_limit, include_premium)
            combinations = combinations[:batch_size]
            
            def update_progress(current, total, current_combo):
                progress_bar.progress(current / total)
                status_text.text(f"正在生成 [{current}/{total}] {current_combo}")
            
            results = generate_uac_batch(combinations, uac_target_lang, char_limit, update_progress)
            if results:
                all_new_ads.extend(results)
        
        st.session_state.uac_ads = all_new_ads + st.session_state.uac_ads
        status_text.text(f"✅ 生成完成！共 {len(all_new_ads)} 条文案")
        time.sleep(0.5)
        st.rerun()
    
    st.subheader(f"📜 文案素材池 ({len(st.session_state.uac_ads)} 条)")
    st.caption("💡 每条文案代表一个不同的语义信号组合，用于Google Ads Asset Group测试")
    
    if st.session_state.uac_ads:
        motive_counts = {}
        for ad in st.session_state.uac_ads:
            motive = ad.get('motive', 'unknown')
            motive_counts[motive] = motive_counts.get(motive, 0) + 1
        
        cols = st.columns(min(4, len(motive_counts)))
        for i, (motive, count) in enumerate(list(motive_counts.items())[:4]):
            motive_zh = UAC_DIMENSIONS["user_motives"].get(motive, {}).get("zh", motive)
            with cols[i]:
                st.metric(f"🎯 {motive_zh}", f"{count}条")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.session_state.uac_ads and st.button("🗑️ 去重", use_container_width=True):
            seen = set()
            unique_ads = []
            for ad in st.session_state.uac_ads:
                key = ad.get('dimension_key', ad['ad_text'])
                if key not in seen:
                    seen.add(key)
                    unique_ads.append(ad)
            st.session_state.uac_ads = unique_ads
            st.rerun()
    with col3:
        if st.session_state.uac_ads and st.button("💾 导出CSV", key="export_uac", use_container_width=True):
            df = pd.DataFrame(st.session_state.uac_ads)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下载", data=csv, file_name=f"uac_ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
    
    if st.session_state.uac_ads:
        for idx, ad in enumerate(st.session_state.uac_ads[:50]):
            lang_emoji = {
                "越南语": "🇻🇳", "中文": "🇨🇳", "英文": "🇬🇧",
                "泰语": "🇹🇭", "印尼语": "🇮🇩", "日语": "🇯🇵",
                "韩语": "🇰🇷", "马来语": "🇲🇾", "阿拉伯语": "🇸🇦",
                "西班牙语": "🇪🇸", "葡萄牙语": "🇵🇹"
            }.get(ad.get("language", ""), "🌐")
            
            actual = ad.get('actual_chars', 0)
            limit = ad.get('char_limit', 0)
            char_status = f"✅ {actual}/{limit}" if actual <= limit else f"⚠️ {actual}/{limit}"
            
            motive_zh = UAC_DIMENSIONS["user_motives"].get(ad.get('motive', ''), {}).get("zh", ad.get('motive', ''))
            scenario_zh = UAC_DIMENSIONS["scenarios"].get(ad.get('scenario', ''), {}).get("zh", ad.get('scenario', ''))
            value_zh = UAC_DIMENSIONS["value_props"].get(ad.get('value_prop', ''), {}).get("zh", ad.get('value_prop', ''))
            
            with st.expander(f"#{idx+1} | {char_status} | {motive_zh} + {scenario_zh} → {value_zh}", expanded=True):
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown(f"**{lang_emoji} {ad.get('language', '')} 原文**")
                    st.code(ad['ad_text'], language="text")
                with col_right:
                    st.markdown("**🇨🇳 中文翻译**")
                    st.code(ad['translation'], language="text")
                
                structure_zh = next((k for k, v in STRUCTURE_TEMPLATES.items() if k == ad.get('structure', '')), ad.get('structure', ''))
                st.caption(f"📝 结构：{structure_zh} | 🎯 动机：{motive_zh} | 🕐 场景：{scenario_zh} | 💎 价值：{value_zh}")
    else:
        st.info("👆 选择生成模式后点击「生成文案」")


# ==================== 口播脚本生成 Tab ====================
with main_tab1:
    st.header("🎙️ 口播脚本生成器")
    st.caption("生成社交媒体口播脚本，支持11种语言")
    
    st.subheader("🔑 API 设置")
    api_key = st.text_input("DeepSeek API Key", type="password", value=st.session_state.get("api_key", ""), placeholder="sk-...", key="main_api")
    if api_key:
        st.session_state.api_key = api_key
    
    if not is_api_ready():
        st.warning("⚠️ 请填写有效的 API Key（格式：sk-xxx）")
    else:
        st.success("✅ API 已就绪")
    
    st.divider()
    st.subheader("🎮 生成设置")
    
    config = load_config()
    personas = list(config["personas"].keys())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        persona = st.selectbox("👩 人设", personas, key="script_persona")
    with col2:
        vibe = st.selectbox("🎭 语气", config["personas"][persona]["vibes"], key="script_vibe")
    with col3:
        target_lang = st.selectbox("🌍 输出语言", list(LANGUAGES.keys()), index=0, key="script_lang")
        st.caption(f"💬 示例：{LANGUAGES[target_lang]['example']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        product_hook = st.selectbox("💎 卖点", list(config.get("product_hooks", {}).keys()), key="script_hook")
    with col2:
        duration = st.selectbox("⏱️ 时长", ["15秒", "30秒", "45秒", "60秒"], index=0, key="script_duration")
        duration_map = {"15秒": 15, "30秒": 30, "45秒": 45, "60秒": 60}
        duration_seconds = duration_map.get(duration, 15)
    with col3:
        num_scripts = st.slider("📝 生成数量", 1, 5, 1, key="script_num")
    
    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🚀 生成口播脚本", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ 清空脚本列表", use_container_width=True):
            st.session_state.scripts = []
            st.rerun()
    
    st.subheader(f"📜 生成的脚本 ({len(st.session_state.scripts)} 条)")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.session_state.scripts and st.button("💾 导出脚本 CSV", key="export_script", use_container_width=True):
            df = pd.DataFrame(st.session_state.scripts)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下载", data=csv, file_name=f"scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
    
    if generate_btn and is_api_ready():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(num_scripts):
            status_text.text(f"正在生成第 {i+1}/{num_scripts} 条（{LANGUAGES[target_lang]['name']}，{duration_seconds}秒）...")
            result = generate_script(persona, vibe, product_hook, target_lang, duration_seconds)
            
            if result:
                st.session_state.scripts.insert(0, {
                    "persona": persona, "vibe": vibe, "product_hook": product_hook,
                    "language": target_lang, "duration": duration_seconds,
                    "word_count": result["word_count"], "script": result["script"],
                    "translation": result["translation"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            progress_bar.progress((i + 1) / num_scripts)
            time.sleep(0.3)
        
        status_text.text(f"✅ 生成完成！共 {num_scripts} 条")
        st.rerun()
    
    if st.session_state.scripts:
        for idx, script in enumerate(st.session_state.scripts[:30]):
            lang_emoji = {
                "越南语": "🇻🇳", "中文": "🇨🇳", "英文": "🇬🇧",
                "泰语": "🇹🇭", "印尼语": "🇮🇩", "日语": "🇯🇵",
                "韩语": "🇰🇷", "马来语": "🇲🇾", "阿拉伯语": "🇸🇦",
                "西班牙语": "🇪🇸", "葡萄牙语": "🇵🇹"
            }.get(script.get("language", ""), "🌐")
            
            duration_info = f" | ⏱️ {script.get('duration', '?')}秒"
            word_info = f" | 📝 {script.get('word_count', '?')}词"
            
            with st.expander(f"📝 #{idx+1} | {lang_emoji} {script['language']} | {script['persona']} - {script['vibe']} | {script['product_hook']}{duration_info}{word_info}", expanded=True):
                st.markdown(f"**{lang_emoji} {script['language']} 原文：**")
                st.code(script['script'], language="text")
                st.markdown("---")
                st.markdown("**🇨🇳 中文翻译：**")
                st.code(script['translation'], language="text")
    else:
        st.info("👈 在上方选择语言、人设、语气、卖点，然后点击「生成口播脚本」")


# ==================== 配置管理 Tab ====================
with main_tab3:
    st.subheader("✏️ 人设和模板配置")
    config = load_config()
    personas = list(config["personas"].keys())
    
    col1, col2 = st.columns(2)
    with col1:
        edit_persona = st.selectbox("选择人设", personas, key="config_persona")
    with col2:
        edit_vibe = st.selectbox("选择语气", config["personas"][edit_persona]["vibes"], key="config_vibe")
    
    templates = config["personas"][edit_persona]["templates"].get(edit_vibe, [])
    if templates:
        edited_template = st.text_area("模板内容", value=templates[0], height=200)
        if st.button("💾 保存修改"):
            config["personas"][edit_persona]["templates"][edit_vibe][0] = edited_template
            save_config(config)
            st.success("已保存")
            st.rerun()
    
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
    
    with st.expander("➕ 添加产品卖点"):
        new_hook = st.text_input("新卖点名称")
        new_hook_desc = st.text_input("卖点描述（用于提示词）")
        if st.button("添加卖点"):
            if new_hook and new_hook_desc:
                config = load_config()
                if "product_hooks" not in config:
                    config["product_hooks"] = {}
                config["product_hooks"][new_hook] = new_hook_desc
                save_config(config)
                st.success(f"已添加卖点: {new_hook}")
                st.rerun()
            else:
                st.warning("请填写卖点名称和描述")


# ==================== 脚本分析 Tab ====================
with main_tab4:
    st.subheader("📊 脚本分析器")
    st.caption("粘贴任意语言的脚本，AI 会自动分析并生成配置")
    
    if not is_api_ready():
        st.warning("⚠️ 请先在「口播脚本生成」页面填写有效的 API Key")
    else:
        analysis_script = st.text_area("粘贴脚本", height=150, placeholder="支持任何语言：越南语、中文、英文、泰语、西班牙语...")
        
        if analysis_script:
            detected = detect_language(analysis_script)
            lang_display = {"vi": "🇻🇳 越南语", "zh": "🇨🇳 中文", "en": "🇬🇧 英文"}.get(detected, "❓ 未知")
            st.caption(f"检测到语言: {lang_display}")
        
        if st.button("🔍 分析脚本", type="primary"):
            if analysis_script:
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
            with col2:
                st.info(f"**语气**: {result.get('vibe_name', '?')}")
            
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


# ==================== 导入/导出 Tab ====================
with main_tab5:
    st.subheader("📁 导入/导出配置")
    col1, col2 = st.columns(2)
    with col1:
        config_json = json.dumps(load_config(), ensure_ascii=False, indent=2)
        st.download_button("📥 下载配置文件", data=config_json, file_name="prompts.json", mime="application/json")
    with col2:
        uploaded = st.file_uploader("上传 prompts.json", type=["json"])
        if uploaded:
            new_config = json.load(uploaded)
            save_config(new_config)
            st.success("配置已导入")
            st.rerun()
    
    st.divider()
    if st.button("🔄 恢复默认配置"):
        save_config(load_default_config())
        st.success("已恢复默认配置")
        st.rerun()


# ==================== 页脚 ====================
st.divider()
st.caption("💡 提示：可以在顶部「配置管理」中修改人设、语气和模板内容 | UAC广告文案支持30/90字符限制")
