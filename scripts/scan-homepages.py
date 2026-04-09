"""
个人主页联系方式扫描器
扫描 talent-notes.json 中所有有 homepage 的人才，
抓取其个人主页内容，识别并提取：
  - 微信/WeChat ID
  - Email 地址
  - 电话号码
  - CV/简历 下载链接
  - Twitter/X 账号
  - GitHub 账号
  - LinkedIn 链接

提取结果写回 talent-notes.json 的 contactInfo 字段。
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import ssl
import io

# Windows 终端编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TALENT_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "talent-notes.json")

# 放宽 SSL（部分学术个人主页证书可能有问题）
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}


def fetch_page(url, timeout=15):
    """抓取网页内容，返回 HTML 文本"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            raw = resp.read()
            # 尝试多种编码
            for enc in ['utf-8', 'latin-1', 'gbk', 'gb2312']:
                try:
                    return raw.decode(enc)
                except:
                    continue
            return raw.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    ⚠ 抓取失败: {e}")
        return ""


def extract_emails(text):
    """提取 email 地址"""
    # 匹配常见 email 格式，排除图片链接等误匹配
    pattern = r'[a-zA-Z0-9._%+\-]+\s*(?:@|(?:\[at\])|(?:\(at\))|(?:\{at\}))\s*[a-zA-Z0-9.\-]+\s*(?:\.|(?:\[dot\])|(?:\(dot\))|(?:\{dot\}))\s*[a-zA-Z]{2,}'
    raw_matches = re.findall(pattern, text, re.IGNORECASE)
    
    # 也匹配标准 email
    standard = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    
    emails = set()
    for m in standard:
        m = m.strip().lower()
        # 排除常见误匹配
        if any(x in m for x in ['example.com', 'email.com', '.png', '.jpg', '.gif', '.svg', 'webpack', 'babel']):
            continue
        emails.add(m)
    
    return list(emails)


def extract_wechat(text, html):
    """提取微信/WeChat ID"""
    results = []
    
    # 纯文本里找 WeChat / 微信 后面跟的 ID
    patterns = [
        r'(?:wechat|weixin|微信)\s*[：:]\s*([a-zA-Z0-9_\-]{4,20})',
        r'(?:wechat|weixin|微信)\s*(?:id|ID|Id)?\s*[：:]\s*([a-zA-Z0-9_\-]{4,20})',
        r'(?:wechat|weixin|微信)\s*(?:account)?\s*[：:=]\s*([a-zA-Z0-9_\-]{4,20})',
    ]
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        results.extend(matches)
    
    # HTML 中查找带 wechat 的图片（二维码）
    qr_patterns = [
        r'<img[^>]*(?:wechat|weixin|微信)[^>]*src=["\']([^"\']+)["\']',
        r'src=["\']([^"\']*(?:wechat|weixin)[^"\']*)["\']',
    ]
    for pat in qr_patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            if m not in results:
                results.append(f"[QR: {m}]")
    
    return list(set(results))


def extract_phone(text):
    """提取电话号码"""
    patterns = [
        r'(?:phone|tel|telephone|电话|手机|联系电话)\s*[：:]\s*([+\d\s\-()]{7,20})',
        r'(?:phone|tel)\s*[：:=]\s*([+\d\s\-()]{7,20})',
    ]
    results = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        results.extend([m.strip() for m in matches])
    return list(set(results))


def extract_cv_links(html, base_url):
    """提取 CV/简历 下载链接"""
    results = []
    
    # 找含有 CV / resume / 简历 的链接（精确匹配，排除论文链接）
    patterns = [
        # 链接文本明确包含 CV/Resume 字样
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>\s*(?:(?:my\s+)?CV|Resume|简历|Curriculum\s+Vitae)\s*(?:[\(\[<].*?[\)\]>])?\s*</a>',
        # href 中路径名含 cv/resume + PDF 后缀
        r'<a[^>]*href=["\']([^"\']*(?:/cv|/resume|_cv|_resume|CV\.pdf|resume\.pdf)[^"\']*\.(?:pdf|doc|docx))["\']',
        # 直接的 cv.pdf 或 resume.pdf 链接
        r'href=["\']([^"\']*(?:cv|resume)[^"\']*\.pdf)["\']',
    ]
    
    for pat in patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            # 转为绝对 URL
            if m.startswith('http'):
                url = m
            elif m.startswith('//'):
                url = 'https:' + m
            elif m.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                url = f"{parsed.scheme}://{parsed.netloc}{m}"
            else:
                url = base_url.rstrip('/') + '/' + m
            
            # 过滤掉明显不是 CV 的链接
            url_lower = url.lower()
            if any(x in url_lower for x in [
                'openaccess.thecvf.com', 'arxiv.org', 'ieee.org',
                'sciencedirect.com', 'springer.com', 'acm.org',
                'mp.weixin.qq.com', 'paper', 'conference',
                '.css', '.js', '.min.', 'bio.html',
                'papercopilot', 'cvpr', 'eccv', 'iccv', 'nips', 'icml',
                'sites.google.com'
            ]):
                continue
            results.append(url)
    
    return list(set(results))


def extract_social(html, text):
    """提取社交媒体账号"""
    social = {}
    
    # Twitter/X
    twitter_patterns = [
        r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})',
    ]
    for pat in twitter_patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            if m.lower() not in ['share', 'intent', 'home', 'search', 'login', 'signup']:
                social['twitter'] = f"@{m}"
                break
    
    # GitHub
    github_patterns = [
        r'github\.com/([a-zA-Z0-9\-]{1,39})(?:["\'\s/]|$)',
    ]
    for pat in github_patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        for m in matches:
            if m.lower() not in ['topics', 'features', 'explore', 'pricing', 'login', 'signup', 'settings', 'orgs', 'pulls', 'issues', 'marketplace', 'sponsors']:
                social['github'] = f"github.com/{m}"
                break
    
    # LinkedIn
    linkedin = re.findall(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', html, re.IGNORECASE)
    if linkedin:
        social['linkedin'] = f"linkedin.com/in/{linkedin[0]}"
    
    return social


def has_contact_keywords(text):
    """检查页面是否包含联系方式相关关键词"""
    keywords = [
        'wechat', 'weixin', '微信', 'email', 'mail', 'contact',
        'phone', 'tel', '电话', 'cv', 'resume', '简历',
        'twitter', 'github', 'linkedin'
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def scan_homepage(url):
    """扫描一个主页，返回联系方式信息"""
    html = fetch_page(url)
    if not html:
        return None
    
    # 去除 HTML 标签得到纯文本
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text_clean = re.sub(r'<[^>]+>', ' ', text)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    
    info = {
        'emails': extract_emails(text_clean),
        'wechat': extract_wechat(text_clean, html),
        'phone': extract_phone(text_clean),
        'cv': extract_cv_links(html, url),
        'social': extract_social(html, text_clean),
        'scannedAt': time.strftime('%Y-%m-%d'),
        'hasContactKeywords': has_contact_keywords(text_clean),
    }
    
    # 判断是否找到了有用的联系方式
    has_any = bool(info['emails'] or info['wechat'] or info['phone'] or info['cv'] or info['social'])
    info['hasContact'] = has_any
    
    return info


def main():
    # 参数解析
    batch_size = 20  # 每次扫描的人数
    force_rescan = '--force' in sys.argv
    only_new = '--new' in sys.argv  # 只扫描还没扫过的
    
    print("=" * 60)
    print("🔍 个人主页联系方式扫描器")
    print("=" * 60)
    
    # 加载人才数据
    with open(TALENT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    notes = data.get("notes", {})
    
    # 筛选有 homepage 的人才
    candidates = []
    for key, talent in notes.items():
        homepage = talent.get('homepage', '')
        if not homepage:
            continue
        
        # 跳过已扫描过的（除非 force）
        if not force_rescan and not only_new:
            existing_contact = talent.get('contactInfo', {})
            if existing_contact.get('scannedAt'):
                continue
        
        if only_new and talent.get('contactInfo', {}).get('scannedAt'):
            continue
        
        candidates.append((key, talent))
    
    print(f"\n📊 总人才: {len(notes)}")
    print(f"📊 有主页: {sum(1 for t in notes.values() if t.get('homepage'))}")
    print(f"📊 待扫描: {len(candidates)}")
    print(f"📊 本次批量: {min(batch_size, len(candidates))}")
    
    if not candidates:
        print("\n✅ 所有有主页的人才都已扫描过。用 --force 重新扫描全部。")
        return
    
    scanned = 0
    found_contact = 0
    
    for key, talent in candidates[:batch_size]:
        homepage = talent['homepage']
        name = talent.get('name', key)
        
        print(f"\n[{scanned+1}/{min(batch_size, len(candidates))}] {name}")
        print(f"    🌐 {homepage}")
        
        info = scan_homepage(homepage)
        
        if info is None:
            print("    ❌ 页面无法访问")
            notes[key]['contactInfo'] = {
                'scannedAt': time.strftime('%Y-%m-%d'),
                'error': '页面无法访问',
                'hasContact': False,
            }
        else:
            notes[key]['contactInfo'] = info
            
            # 打印发现的内容
            if info['emails']:
                print(f"    📧 Email: {', '.join(info['emails'])}")
            if info['wechat']:
                print(f"    💬 WeChat: {', '.join(info['wechat'])}")
            if info['phone']:
                print(f"    📞 Phone: {', '.join(info['phone'])}")
            if info['cv']:
                print(f"    📄 CV: {', '.join(info['cv'])}")
            if info['social']:
                for platform, handle in info['social'].items():
                    print(f"    🔗 {platform}: {handle}")
            
            if info['hasContact']:
                found_contact += 1
                print(f"    ✅ 发现联系方式！")
            elif info['hasContactKeywords']:
                print(f"    🔍 页面有联系相关关键词但未精确提取到")
            else:
                print(f"    ➖ 未发现联系方式")
        
        scanned += 1
        # 礼貌延迟，避免被封
        time.sleep(2)
    
    # 保存
    data["notes"] = notes
    data["generatedAt"] = time.strftime('%Y-%m-%dT%H:%M:%S') + "Z"
    
    with open(TALENT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"📊 扫描完成！")
    print(f"   扫描: {scanned} 人")
    print(f"   发现联系方式: {found_contact} 人")
    print(f"   剩余待扫描: {len(candidates) - scanned} 人")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
