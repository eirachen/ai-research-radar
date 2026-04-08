import json

d = json.load(open('reports/arxiv-daily.json', 'r', encoding='utf-8'))
for cid, c in sorted(d['companies'].items(), key=lambda x: -x[1]['count']):
    papers = c['papers']
    top3 = [p['title'][:70] for p in papers[:3]]
    unis = set()
    dirs = {}
    for p in papers:
        unis.update(p.get('universities', []))
        for dd in p.get('directions', []):
            dirs[dd['label']] = dirs.get(dd['label'], 0) + 1
    top_dirs = sorted(dirs.items(), key=lambda x: -x[1])[:4]
    print(f"=== {c['icon']} {c['company']} ({c['count']}篇, {c['uniCollabCount']}校合作) ===")
    print(f"  方向: {', '.join(d[0]+'('+str(d[1])+')' for d in top_dirs)}")
    print(f"  高校: {', '.join(sorted(unis)[:8])}")
    for t in top3:
        print(f"  - {t}")
    print()
