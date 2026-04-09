"""
通过 Lighthouse API 合并新人才数据（不覆盖已有数据）
1. 先 GET 服务器上最新的 talent-notes.json
2. 只把本地新增/更新的人才合并进去（不删除服务器上已有的）
3. POST 回去
"""
import json, sys, io, urllib.request

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API = 'http://43.167.194.82:8800/talent-notes.json'

def main():
    # 1. 读取本地数据
    with open('reports/talent-notes.json', 'r', encoding='utf-8') as f:
        local = json.load(f)
    local_notes = local.get('notes', {})

    # 2. 获取服务器数据
    print('Fetching server data...')
    try:
        req = urllib.request.Request(API, headers={'User-Agent': 'sync/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            server = json.loads(resp.read().decode('utf-8'))
        server_notes = server.get('notes', {})
        print(f'  Server: {len(server_notes)} talents')
    except Exception as e:
        print(f'  ERROR fetching server: {e}')
        print('  Aborting - will not overwrite!')
        return

    # 3. 合并：服务器数据为基础，只补充本地有而服务器没有的，或本地更新了的空字段
    merged = dict(server_notes)  # 服务器数据优先
    added = 0
    updated = 0

    for key, local_entry in local_notes.items():
        if key not in merged:
            # 新人才，直接加入
            merged[key] = local_entry
            added += 1
            print(f'  + NEW: {key}')
        else:
            # 已存在：只补充服务器上为空的字段
            server_entry = merged[key]
            changed = False
            for field in ['scholar', 'homepage', 'advisor', 'lab', 'direction', 'statusNote', 'status', 'gradYear']:
                server_val = server_entry.get(field, '')
                local_val = local_entry.get(field, '')
                if (not server_val or server_val == '待确认') and local_val and local_val != '待确认':
                    server_entry[field] = local_val
                    changed = True
            # university：如果本地的更完整（更长），用本地的覆盖
            local_uni = local_entry.get('university', '')
            server_uni = server_entry.get('university', '')
            if local_uni and len(local_uni) > len(server_uni) and server_uni != local_uni:
                server_entry['university'] = local_uni
                changed = True
            # 合并 contactInfo（如果服务器没有）
            if not server_entry.get('contactInfo') and local_entry.get('contactInfo'):
                server_entry['contactInfo'] = local_entry['contactInfo']
                changed = True
            if changed:
                updated += 1
                print(f'  ~ FILL: {key}')

    print(f'\nMerge result: +{added} new, ~{updated} filled, total {len(merged)}')

    # 4. POST 回服务器
    payload = json.dumps({
        'generatedAt': local.get('generatedAt', ''),
        'notes': merged
    }, ensure_ascii=False).encode('utf-8')

    try:
        req = urllib.request.Request(API, data=payload, method='POST',
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'sync/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode('utf-8')
        print(f'POST result: {result}')
        print('Done! Server data updated (merge, no overwrite).')
    except Exception as e:
        print(f'POST failed: {e}')

if __name__ == '__main__':
    main()
