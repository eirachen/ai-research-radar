"""精准验证指定日期范围的论文"""
import json, os, sys, io, time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_parser import verify_paper

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, '..', 'reports', 'arxiv-daily.json')

# 日期范围参数
DATE_FROM = '2026-03-01'
DATE_TO = '2026-03-02'

def main():
    with open(ARXIV_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=' * 60)
    print(f'PDF验证: {DATE_FROM} ~ {DATE_TO}')
    print('=' * 60)

    candidates = []
    for cid, c in data['companies'].items():
        for p in c['papers']:
            pub = p['published'][:10]
            if pub < DATE_FROM or pub > DATE_TO:
                continue
            candidates.append((cid, c, p))

    print(f'该日期范围论文: {len(candidates)} 篇')

    # 重置这些论文的 confirmed
    reset = 0
    for cid, c, p in candidates:
        if p.get('collabConfidence') == 'confirmed':
            p['collabConfidence'] = 'mentioned' if p.get('hasUniCollab') else 'none'
            p['pdfVerified'] = False
            reset += 1
    print(f'重置: {reset} 篇')

    to_verify = [(cid, c, p) for cid, c, p in candidates if not p.get('pdfVerified') and p.get('pdfUrl')]
    print(f'待验证: {len(to_verify)} 篇\n')

    verified = confirmed = downgraded = 0

    for cid, c, p in to_verify:
        title_short = p['title'][:55]
        print(f'[{verified+1}/{len(to_verify)}] {c["company"]} | {title_short}...')

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
                print(f'    YES {result["companies_found"]} + {result["unis_found"][:2]}')
            elif result['companies_found'] and not result['unis_found']:
                p['collabConfidence'] = 'company_only'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    company only: {result["companies_found"]}')
            elif result['unis_found'] and not result['companies_found']:
                p['collabConfidence'] = 'uni_only'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    uni only: {result["unis_found"][:2]}')
            else:
                p['collabConfidence'] = 'none'
                p['hasUniCollab'] = False
                downgraded += 1
                print(f'    none found')
        else:
            p['collabConfidence'] = p.get('collabConfidence', 'mentioned')
            print(f'    PDF unavailable')

        verified += 1

    # 更新计数
    for company_id, company_data in data['companies'].items():
        company_data['uniCollabCount'] = sum(1 for p in company_data['papers'] if p.get('hasUniCollab'))
        company_data['hkCollabCount'] = sum(1 for p in company_data['papers'] if p.get('hasHKCollab'))
    data['totalUniCollab'] = sum(c['uniCollabCount'] for c in data['companies'].values())
    data['totalHKCollab'] = sum(c.get('hkCollabCount', 0) for c in data['companies'].values())

    with open(ARXIV_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 结果
    print(f'\n{"=" * 60}')
    print(f'验证: {verified} 篇 | 确认校企合作: {confirmed} | 降级: {downgraded}')
    confirmed_list = []
    for cid, c in data['companies'].items():
        for p in c['papers']:
            pub = p['published'][:10]
            if pub >= DATE_FROM and pub <= DATE_TO and p.get('collabConfidence') == 'confirmed':
                confirmed_list.append(f"  {c['company']}: {p['title'][:60]} ({pub})")
    print(f'\n确认的校企合作:')
    if confirmed_list:
        print('\n'.join(confirmed_list))
    else:
        print('  (无)')
    print('=' * 60)

if __name__ == '__main__':
    main()
