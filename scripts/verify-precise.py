"""
精准校企合作验证器
对 4月1日以来的所有论文重新判定 collabConfidence：
1. 先重置所有 confirmed -> mentioned（清除之前的误判）
2. 下载 PDF 首页，解析作者机构
3. 只有同时找到公司 + 高校才标 confirmed
"""
import json, os, sys, io, time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_parser import verify_paper

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, '..', 'reports', 'arxiv-daily.json')
SINCE_DATE = '2026-04-01'
MAX_VERIFY = 50  # 每次最多验证50篇

def main():
    with open(ARXIV_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=' * 60)
    print('🔬 精准校企合作验证（4月1日以来）')
    print('=' * 60)

    # 收集 4月1日以来的论文
    candidates = []
    for cid, c in data['companies'].items():
        for p in c['papers']:
            if p['published'][:10] < SINCE_DATE:
                continue
            candidates.append((cid, c, p))

    print(f'\n📊 4月1日以来论文: {len(candidates)} 篇')

    # Step 1: 重置所有这些论文的 confirmed 状态
    reset_count = 0
    for cid, c, p in candidates:
        if p.get('collabConfidence') == 'confirmed' and not p.get('_manualConfirmed'):
            p['collabConfidence'] = 'mentioned' if p.get('hasUniCollab') else 'none'
            p['pdfVerified'] = False
            reset_count += 1
    print(f'🔄 重置 {reset_count} 篇为 mentioned（待重新验证）')

    # Step 2: 对未验证的下载 PDF 验证
    to_verify = [(cid, c, p) for cid, c, p in candidates if not p.get('pdfVerified') and p.get('pdfUrl')]
    print(f'📋 待PDF验证: {len(to_verify)} 篇\n')

    verified = 0
    confirmed = 0
    downgraded = 0

    for cid, c, p in to_verify[:MAX_VERIFY]:
        title_short = p['title'][:55]
        print(f'[{verified+1}/{min(MAX_VERIFY, len(to_verify))}] {c["company"]} | {title_short}...')

        result = verify_paper(p['pdfUrl'])
        time.sleep(2)

        p['pdfVerified'] = True

        if result:
            p['pdfCompanies'] = result['companies_found']
            p['pdfUnis'] = result['unis_found'][:5]
            p['pdfHKUnis'] = result['hk_unis_found']

            if result['is_confirmed_collab']:
                p['collabConfidence'] = 'confirmed'
                p['hasUniCollab'] = True
                confirmed += 1
                unis_short = ', '.join(result['unis_found'][:2])
                comps_short = ', '.join(result['companies_found'][:2])
                print(f'    ✅ CONFIRMED: {comps_short} + {unis_short}')
            elif result['companies_found'] and not result['unis_found']:
                p['collabConfidence'] = 'company_only'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    🏢 Company only: {result["companies_found"]}')
            elif result['unis_found'] and not result['companies_found']:
                p['collabConfidence'] = 'uni_only'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    🎓 Uni only: {result["unis_found"][:2]}')
            else:
                p['collabConfidence'] = 'none'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    ❌ Neither found in header')
        else:
            p['collabConfidence'] = p.get('collabConfidence', 'mentioned')
            print(f'    ⚠️ PDF unavailable')

        verified += 1

    # 更新计数
    for company_id, company_data in data['companies'].items():
        company_data['uniCollabCount'] = sum(1 for p in company_data['papers'] if p.get('hasUniCollab'))
        company_data['hkCollabCount'] = sum(1 for p in company_data['papers'] if p.get('hasHKCollab'))

    data['totalUniCollab'] = sum(c['uniCollabCount'] for c in data['companies'].values())
    data['totalHKCollab'] = sum(c['hkCollabCount'] for c in data['companies'].values())

    with open(ARXIV_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 最终统计
    all_confirmed = []
    for cid, c in data['companies'].items():
        for p in c['papers']:
            if p.get('collabConfidence') == 'confirmed' and p['published'][:10] >= SINCE_DATE:
                all_confirmed.append(f"  {c['company']}: {p['title'][:60]} ({p['published'][:10]})")

    print(f'\n{"=" * 60}')
    print(f'📊 验证完成!')
    print(f'   本次验证: {verified} 篇')
    print(f'   确认校企合作: {confirmed} 篇')
    print(f'   降级/排除: {downgraded} 篇')
    print(f'   剩余待验证: {len(to_verify) - verified} 篇')
    print(f'\n🎓 4月1日以来确认的校企合作:')
    if all_confirmed:
        print('\n'.join(all_confirmed))
    else:
        print('  （暂无确认的校企合作）')
    print(f'{"=" * 60}')

if __name__ == '__main__':
    main()
