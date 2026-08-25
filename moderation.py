# -*- coding: utf-8 -*-
"""校桥 CampusBridge · 内容审核模块（文本 + 图片 + 文件）

三级风控 + AI 增强审核：
  1. PASS   → 本地词 + 图片基础校验通过；AI 也通过 → 直接发布（is_approved=True）
  2. WARN   → 本地没问题，但 AI 判中风险 → 进管理员审核队列（is_approved=False）
  3. BLOCK  → 命中本地严重违规词 / 图片黑名单 / AI 识别为违法 → 直接拒绝

AI 审核说明：
  - 需要在 .env 配置 DEEPSEEK_API_KEY
  - 未配置时自动降级为仅本地关键词 + 图片基础校验
  - 文本审核使用 deepseek-chat 模型
  - 图片审核使用视觉能力（deepseek-chat 支持多模态）
  - AI 调用超时或失败自动降级为 PASS，不影响用户上传体验
"""

import os
import hashlib
import re
import base64
import json as _json
from typing import Literal, Optional

# ===== 本地违规词表（兜底；可按需扩充） =====
BAD_WORDS_BLOCK = [
    '代考', '代考机构', '替考', '枪手', '考试答案', '泄题', '买答案', '卖答案',
    '代写', '代笔', '论文代写', '作业代写', 'essay代写', '代做毕设', '毕设代做',
    '赌博', '赌场', '博彩', '外围女', '有偿陪侍', '色情服务',
    '冰毒', '毒品', '麻古', '摇头丸', 'k粉',
    '枪支', '气枪', '仿真枪', '弩', '管制刀具',
    '邪教', '法轮功', '政治敏感词', '反动标语',
    '诈骗', '刷单', '杀猪盘', '裸贷', '高利贷',
    '办证', '假证', '刻章', '发票',
    '翻墙', 'VPN翻墙',
]

BAD_WORDS_WARN = [
    '卖课', '有偿补课', '私下交易', '约炮', '包夜', '上门',
    '跳楼价', '原价', '秒杀',
    '拼单', '砍一刀', '助力', '邀请码',
    '微信加我', '加vx', '加v信', '私聊我', '私我',
]

# ===== 图片 MD5 黑名单 =====
IMAGE_MD5_BLACKLIST: set = set()

# 图片格式白名单
ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 单图 ≤ 10MB

# AI 审核图片最大尺寸（base64 编码后控制在 4MB 以内以适配 API）
_AI_IMAGE_MAX_BYTES = 4 * 1024 * 1024


# ================================================================
# 0. 工具函数
# ================================================================

def _get_api_key() -> str:
    """获取 DEEPSEEK_API_KEY，优先 Flask config，兜底 .env"""
    try:
        from flask import current_app
        key = current_app.config.get('DEEPSEEK_API_KEY', '')
        if key:
            return key.strip()
    except Exception:
        pass
    return os.getenv('DEEPSEEK_API_KEY', '').strip()


def _resize_image_for_ai(blob: bytes) -> bytes:
    """如果图片超过 AI 限制，等比缩小到适配尺寸"""
    if len(blob) <= _AI_IMAGE_MAX_BYTES:
        return blob
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(blob))
        img.thumbnail((1024, 1024), Image.LANCZOS)
        buf = io.BytesIO()
        fmt = img.format or 'JPEG'
        if fmt == 'PNG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            fmt = 'JPEG'
        img.save(buf, format=fmt, quality=85)
        return buf.getvalue()
    except Exception:
        return blob[:_AI_IMAGE_MAX_BYTES]


def _image_to_data_url(blob: bytes, ext: str = 'jpeg') -> str:
    """图片字节 → data URL（base64 编码）"""
    ext = ext.lower().lstrip('.')
    if ext == 'jpg':
        ext = 'jpeg'
    mime_map = {'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif',
                'webp': 'image/webp', 'bmp': 'image/bmp'}
    mime = mime_map.get(ext, 'image/jpeg')
    b64 = base64.b64encode(blob).decode('ascii')
    return f'data:{mime};base64,{b64}'


# ================================================================
# 1. 文本审核
# ================================================================

def _keyword_scan(text: str):
    """纯本地关键字扫描，返回 (level, hits)"""
    text_norm = (text or '').lower()
    block_hits = [w for w in BAD_WORDS_BLOCK if w and w in text_norm]
    if block_hits:
        return 'block', list(dict.fromkeys(block_hits))
    warn_hits = [w for w in BAD_WORDS_WARN if w and w in text_norm]
    if warn_hits:
        return 'warn', list(dict.fromkeys(warn_hits))
    return 'pass', []


def _ai_text_moderate(text: str, api_key: str, context_type: str):
    """调用 AI 做文本审核，返回 (level, reason, tags)。失败降级 PASS。"""
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
                'temperature': 0, 'max_tokens': 400, 'response_format': {'type': 'json_object'},
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return 'pass', '', []
        content = resp.json()['choices'][0]['message']['content'].strip()
        content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.I | re.M)
        content = re.sub(r'\s*```$', '', content, flags=re.I | re.M)
        data = _json.loads(content)
        lvl = str(data.get('level', 'pass')).lower()
        if lvl not in {'pass', 'warn', 'block'}:
            lvl = 'pass'
        reason = str(data.get('reason', ''))[:200]
        tags = data.get('tags') or []
        if not isinstance(tags, list):
            tags = []
        return lvl, reason, [str(t)[:20] for t in tags]
    except Exception:
        return 'pass', '', []


def moderate_text(
    text: str,
    context_type: str = 'forum_post',
):
    """文本审核入口。
    返回: {level, safe, reject, hits, reason, by, ai_used}
    """
    level_kw, hits_kw = _keyword_scan(text)
    if level_kw == 'block':
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': hits_kw, 'by': 'keyword', 'ai_used': False,
            'reason': f"内容包含违规词：{'、'.join(hits_kw)}，平台已自动拦截。",
        }

    api_key = _get_api_key()
    ai_used = bool(api_key)
    level_ai, reason_ai, tags_ai = _ai_text_moderate(text, api_key, context_type)

    if level_ai == 'block':
        merged_level, merged_by = 'warn', 'ai'
        merged_reason = reason_ai or 'AI 识别为高风险，等待管理员审核。'
        merged_hits = tags_ai
    elif level_ai == 'warn' or level_kw == 'warn':
        hits = list(dict.fromkeys(hits_kw + tags_ai))
        reason_parts = []
        if level_kw == 'warn':
            reason_parts.append(f"本地命中：{'、'.join(hits_kw)}")
        if reason_ai:
            reason_parts.append(f"AI：{reason_ai}")
        merged_level = 'warn'
        merged_by = 'both' if (level_kw == 'warn' and level_ai == 'warn') else (
            'keyword' if level_kw == 'warn' else 'ai')
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
        'ai_used': ai_used,
    }


# ================================================================
# 2. 图片审核（本地校验 + AI 视觉审核）
# ================================================================

def _md5_of_bytes(blob: bytes) -> str:
    return hashlib.md5(blob).hexdigest()


def _ai_image_moderate(blob: bytes, filename: str, api_key: str):
    """AI 图片内容审核，返回 (level, reason, tags)。失败降级 PASS。"""
    if not api_key or not blob:
        return 'pass', '', []
    try:
        import requests
        # 图片预处理：缩小到适配尺寸
        safe_blob = _resize_image_for_ai(blob)
        ext = 'jpeg'
        if filename and '.' in filename:
            ext = filename.rsplit('.', 1)[1].lower()
        data_url = _image_to_data_url(safe_blob, ext)

        prompt = """你是校园社区平台的图片内容审核员。审核以下图片，严格按 JSON 格式输出：
{"level": "pass|warn|block", "reason": "中文一句话说明", "tags": ["违规分类标签",...]}
规则：
- block：色情/暴力/恐怖/极端/违法违规图片
- warn：低俗擦边/广告引流/二维码/联系方式等
- pass：正常校园相关图片（学习资料/生活分享/风景/物品照片等）
注意：正常的人物头像、学习场景、风景、书籍/物品照片一律判定 pass。
只输出 JSON，不要解释。"""

        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {'type': 'image_url', 'image_url': {'url': data_url}},
                        ],
                    }
                ],
                'temperature': 0, 'max_tokens': 300,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return 'pass', '', []
        content = resp.json()['choices'][0]['message']['content'].strip()
        content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.I | re.M)
        content = re.sub(r'\s*```$', '', content, flags=re.I | re.M)
        data = _json.loads(content)
        lvl = str(data.get('level', 'pass')).lower()
        if lvl not in {'pass', 'warn', 'block'}:
            lvl = 'pass'
        reason = str(data.get('reason', ''))[:200]
        tags = data.get('tags') or []
        if not isinstance(tags, list):
            tags = []
        return lvl, reason, [str(t)[:20] for t in tags]
    except Exception:
        return 'pass', '', []


def moderate_image_bytes(blob: bytes, filename: str = ''):
    """图片审核（本地校验 + AI 视觉审核）。
    返回: {level, safe, reject, hits, reason, by, ai_used}
    """
    # 1. 扩展名白名单
    ext = ''
    if filename and '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
    if ext and ext not in ALLOWED_IMAGE_EXT:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'不支持的扩展名：.{ext}'], 'by': 'keyword', 'ai_used': False,
            'reason': f"仅支持 {'/'.join(sorted(ALLOWED_IMAGE_EXT))} 格式图片。",
        }

    # 2. 大小限制
    if len(blob) > MAX_IMAGE_SIZE:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'文件过大 {len(blob)//1024}KB'], 'by': 'keyword', 'ai_used': False,
            'reason': f"单张图片不得超过 {MAX_IMAGE_SIZE//1024//1024}MB。",
        }

    # 3. MD5 黑名单
    md5 = _md5_of_bytes(blob)
    if md5 in IMAGE_MD5_BLACKLIST:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': [f'MD5黑名单:{md5[:8]}...'], 'by': 'keyword', 'ai_used': False,
            'reason': '图片已被平台列入黑名单，禁止上传。',
        }

    # 4. Pillow 真图校验
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(blob)) as im:
            im.verify()
    except Exception:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': ['损坏/伪造图片'], 'by': 'keyword', 'ai_used': False,
            'reason': '图片已损坏或不是合法图片文件。',
        }

    # 5. AI 视觉审核（可选）
    api_key = _get_api_key()
    ai_used = bool(api_key)
    if ai_used:
        try:
            level_ai, reason_ai, tags_ai = _ai_image_moderate(blob, filename, api_key)
            if level_ai == 'block':
                return {
                    'level': 'block', 'safe': False, 'reject': True,
                    'hits': tags_ai, 'by': 'ai', 'ai_used': True,
                    'reason': f"图片未通过 AI 审核：{reason_ai}",
                }
            elif level_ai == 'warn':
                return {
                    'level': 'warn', 'safe': True, 'reject': False,
                    'hits': tags_ai, 'by': 'ai', 'ai_used': True,
                    'reason': reason_ai or '图片内容待人工审核。',
                }
        except Exception:
            pass

    return {
        'level': 'pass', 'safe': True, 'reject': False,
        'hits': [], 'reason': '', 'by': 'none', 'ai_used': ai_used,
    }


def moderate_image_path(filepath: str):
    """按路径读文件 → moderate_image_bytes"""
    try:
        with open(filepath, 'rb') as f:
            blob = f.read()
    except Exception as e:
        return {
            'level': 'block', 'safe': False, 'reject': True,
            'hits': ['读文件失败'], 'by': 'keyword', 'ai_used': False,
            'reason': f'图片读取失败：{e}',
        }
    return moderate_image_bytes(blob, filename=os.path.basename(filepath))


# ================================================================
# 3. 便捷函数：上传内容一键审核
# ================================================================

def check_upload(
    text: str = '',
    context_type: str = 'forum_post',
    image_blobs: Optional[list] = None,
    image_filenames: Optional[list] = None,
):
    """
    一键审核上传内容（文本 + 多张图片）。
    返回: {
        'level': 'pass'|'warn'|'block',
        'safe': bool, 'reject': bool,
        'text_result': dict,
        'image_results': [dict, ...],
        'reason': str,
    }
    """
    text_result = moderate_text(text, context_type) if text else {
        'level': 'pass', 'safe': True, 'reject': False,
        'hits': [], 'reason': '', 'by': 'none', 'ai_used': False,
    }

    image_results = []
    if image_blobs:
        fnames = image_filenames or [''] * len(image_blobs)
        for blob, fn in zip(image_blobs, fnames):
            r = moderate_image_bytes(blob, filename=fn)
            image_results.append(r)

    # 汇总：block > warn > pass
    all_levels = [text_result['level']] + [r['level'] for r in image_results]
    if 'block' in all_levels:
        final_level = 'block'
    elif 'warn' in all_levels:
        final_level = 'warn'
    else:
        final_level = 'pass'

    reasons = []
    if text_result.get('reason'):
        reasons.append(text_result['reason'])
    for r in image_results:
        if r.get('reason'):
            reasons.append(r['reason'])

    return {
        'level': final_level,
        'safe': final_level != 'block',
        'reject': final_level == 'block',
        'text_result': text_result,
        'image_results': image_results,
        'reason': '；'.join(reasons) if reasons else '',
    }
