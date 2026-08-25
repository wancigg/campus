"""校桥 CampusBridge · 内容审核模块（文本 + 图片）

三级风控：
  1. PASS   → 本地词 + 图片黑名单 都过；若启用 AI 也通过 → 直接发布（is_approved=True）
  2. WARN   → 本地没问题，但 AI 判中风险（或 AI 不可用）→ 进管理员审核队列（is_approved=False）
  3. BLOCK  → 命中本地严重违规词 / 图片黑名单 → 直接拒绝发布（flash 报错 + 不入库）

注意：DeepSeek 深度审核**可选项**。没配置 DEEPSEEK_API_KEY 时：
  - 不做 AI 复核，本地词过 → 直接 PASS（避免因为没 API 导致所有内容都进审核队列）
  - 图片也只做 MD5 黑名单匹配 + 文件类型白名单校验
"""

import os
import hashlib
import re
from typing import Literal

# ===== 本地违规词表（兜底；可按需扩充） =====
# 分类（block=直接拦截，warn=进审核队列）
BAD_WORDS_BLOCK = [
    # 作弊类（直接堵死，校园场景硬红线）
    '代考', '代考机构', '替考', '枪手', '考试答案', '泄题', '买答案', '卖答案',
    '代写', '代笔', '论文代写', '作业代写', 'essay代写', '代做毕设', '毕设代做',
    # 严重违法违规
    '赌博', '赌场', '博彩', '外围女', '有偿陪侍', '色情服务',
    '冰毒', '毒品', '麻古', '摇头丸', 'k粉',
    '枪支', '气枪', '仿真枪', '弩', '管制刀具',
    '邪教', '法轮功', '政治敏感词', '反动标语',
    '诈骗', '刷单', '杀猪盘', '裸贷', '高利贷',
    '办证', '假证', '刻章', '发票',
]

BAD_WORDS_WARN = [
    # 轻微风险（进人工审核，不直接拒）
    '卖课', '有偿补课', '私下交易', '约炮', '包夜', '上门',
    '跳楼价', '原价', '秒杀',  # 营销类（校园场景防止纯广告刷屏）
    '拼单', '砍一刀', '助力', '邀请码',
    '微信加我', '加vx', '加v信', '私聊我', '私我',  # 引流类（防纯广告号）
]

# ===== 图片 MD5 黑名单（用户可自行 append，比如已知违规图就把 md5 放这里） =====
IMAGE_MD5_BLACKLIST: set[str] = set()

# 图片格式白名单（防止上传非图片伪装）
ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 单图 ≤ 10MB


# ================================================================
# 1. 文本审核（本地关键字 + DeepSeek 可选）
# ================================================================

def _keyword_scan(text: str) -> tuple[str, list[str]]:
    """纯本地关键字扫描，返回 (level, hits)。level ∈ {'block','warn','pass'}"""
    text_norm = (text or '').lower()
    block_hits = [w for w in BAD_WORDS_BLOCK if w and w in text_norm]
    if block_hits:
        return 'block', list(dict.fromkeys(block_hits))
    warn_hits = [w for w in BAD_WORDS_WARN if w and w in text_norm]
    if warn_hits:
        return 'warn', list(dict.fromkeys(warn_hits))
    return 'pass', []


def _deepseek_ai_moderate(text: str, api_key: str | None, context_type: str) -> tuple[str, str, list[str]]:
    """调用 DeepSeek 做 AI 文本审核，返回 (level, reason, tags)。失败降级 PASS。"""
    if not api_key or not text:
        return 'pass', '', []
    try:
        import requests
        prompt = f"""你是校园社区平台的合规审核员。审核以下{context_type}内容，严格按 JSON 格式输出：
{{"level": "pass|warn|block", "reason": "中文一句话说明", "tags": ["违规分类标签",...]}}
规则：
- block：涉黄/涉赌/涉毒/涉政/考试作弊/代写代考/招嫖等违法内容
- warn：低俗擦边/纯广告引流/恶意营销/约炮私聊等
- pass：正常校园讨论/学习/生活分享
内容如下：
---
{text[:3000]}
---
只输出 JSON，不要解释。"""
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0, 'max_tokens': 400, 'response_format': {'type': 'json_object'}
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return 'pass', '', []
        import json
        content = resp.json()['choices'][0]['message']['content'].strip()
        # 偶尔模型会包 ```json ... ```，去掉
        content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.I | re.M)
        content = re.sub(r'\s*```$', '', content, flags=re.I | re.M)
        data = json.loads(content)
        lvl = str(data.get('level', 'pass')).lower()
        if lvl not in {'pass', 'warn', 'block'}:
            lvl = 'pass'
        reason = str(data.get('reason', ''))[:200]
        tags = data.get('tags') or []
        if not isinstance(tags, list):
            tags = []
        return lvl, reason, [str(t)[:20] for t in tags]
    except Exception:
        # 网络/超时/解析失败，一律 PASS 不影响发布
        return 'pass', '', []


def moderate_text(
    text: str,
    context_type: Literal['forum_post', 'material_desc', 'textbook_desc', 'comment', 'chat'] = 'forum_post',
) -> dict:
    """文本审核入口。
    返回:
      {
        "level":   "pass" | "warn" | "block",
        "safe":    bool,              # True=可以直接发布（非 block）
        "reject":  bool,              # True=直接拒（block）
        "hits":    list[str],         # 命中的违规词 / AI tags
        "reason":  str,               # 中文原因（用于 flash / moderation_note）
        "by":      "keyword" | "ai" | "both" | "none",
      }
    """
    level_kw, hits_kw = _keyword_scan(text)
    if level_kw == 'block':
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': hits_kw, 'by': 'keyword',
            'reason': f"内容包含违规词：{'、'.join(hits_kw)}，平台已自动拦截。",
        }

    # AI 深度复核（可选）
    try:
        from flask import current_app
        api_key = current_app.config.get('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY', '')
    except Exception:
        api_key = os.getenv('DEEPSEEK_API_KEY', '')

    level_ai, reason_ai, tags_ai = _deepseek_ai_moderate(text, api_key, context_type)

    # 合并：本地 warn + AI warn = warn；本地 pass + AI 没配 = pass；AI block 视为 warn（宁可人工也别误杀）
    if level_ai == 'block':
        merged_level, merged_by, merged_reason, merged_hits = (
            'warn', 'ai', reason_ai or 'AI 识别为高风险，等待管理员审核。', tags_ai
        )
    elif level_ai == 'warn' or level_kw == 'warn':
        hits = list(dict.fromkeys(hits_kw + tags_ai))
        reason_parts = []
        if level_kw == 'warn':
            reason_parts.append(f"本地命中：{'、'.join(hits_kw)}")
        if reason_ai:
            reason_parts.append(f"AI：{reason_ai}")
        merged_level = 'warn'
        merged_by = 'both' if (level_kw == 'warn' and level_ai == 'warn') else (
            'keyword' if level_kw == 'warn' else 'ai'
        )
        merged_reason = '；'.join([p for p in reason_parts if p]) or '内容待管理员人工审核。'
        merged_hits = hits
    else:
        merged_level, merged_by, merged_reason, merged_hits = 'pass', 'none', '', []

    return {
        'level': merged_level,
        'safe': merged_level != 'block',
        'reject': merged_level == 'block',
        'hits': merged_hits,
        'reason': merged_reason,
        'by': merged_by,
    }


# ================================================================
# 2. 图片审核（本地 MD5 黑名单 + 类型/大小 白名单）
# ================================================================

def _md5_of_bytes(blob: bytes) -> str:
    return hashlib.md5(blob).hexdigest()


def moderate_image_bytes(blob: bytes, filename: str = '') -> dict:
    """图片字节审核。
    blob: 上传文件 bytes；filename: 原始文件名（判断扩展名）
    返回：同 moderate_text，但 level 仅 block/pass
    """
    # 1. 扩展名白名单
    ext = ''
    if filename and '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
    if ext and ext not in ALLOWED_IMAGE_EXT:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'不支持的扩展名：.{ext}'], 'by': 'keyword',
            'reason': f"仅支持 {'/'.join(sorted(ALLOWED_IMAGE_EXT))} 格式图片。",
        }
    # 2. 大小限制
    if len(blob) > MAX_IMAGE_SIZE:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'文件过大 {len(blob)//1024}KB'], 'by': 'keyword',
            'reason': f"单张图片不得超过 {MAX_IMAGE_SIZE//1024//1024}MB。",
        }
    # 3. MD5 黑名单
    md5 = _md5_of_bytes(blob)
    if md5 in IMAGE_MD5_BLACKLIST:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'MD5黑名单:{md5[:8]}...'], 'by': 'keyword',
            'reason': '图片已被平台列入黑名单，禁止上传。',
        }
    # 4. Pillow 真·图片校验（防止 txt.exe 改后缀）
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(blob)) as im:
            im.verify()
    except Exception:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': ['损坏/伪造图片'], 'by': 'keyword',
            'reason': '图片已损坏或不是合法图片文件。',
        }
    return {
        'level': 'pass', 'safe': True, 'reject': False,
        'hits': [], 'reason': '', 'by': 'none',
    }


def moderate_image_path(filepath: str) -> dict:
    """按路径读文件 → moderate_image_bytes"""
    try:
        with open(filepath, 'rb') as f:
            blob = f.read()
    except Exception as e:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': ['读文件失败'], 'by': 'keyword',
            'reason': f'图片读取失败：{e}',
        }
    return moderate_image_bytes(blob, filename=os.path.basename(filepath))
