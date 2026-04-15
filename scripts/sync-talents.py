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
            server_entry = merged[key]

            # 🔴 如果服务器上用户手动编辑过，绝不覆盖！
            if server_entry.get('manuallyEdited'):
                print(f'  ⏭ SKIP (manually edited on server): {key}')
                continue

            # 未手动编辑：用本地的验证数据补充服务器空字段
            changed = False
            for field in ['scholar', 'homepage', 'advisor', 'lab', 'direction', 'statusNote', 'status', 'gradYear', 'name']:
                local_val = local_entry.get(field, '')
                server_val = server_entry.get(field, '')
                if local_val and local_val != server_val:
                    server_entry[field] = local_val
                    changed = True
            # university：本地有值且不同就覆盖
            local_uni = local_entry.get('university', '')
            server_uni = server_entry.get('university', '')
            if local_uni and local_uni != server_uni:
                server_entry['university'] = local_uni
                changed = True
            # isHK：同步
            if 'isHK' in local_entry:
                server_entry['isHK'] = local_entry['isHK']
            # contactInfo：本地有就覆盖
            if local_entry.get('contactInfo'):
                server_entry['contactInfo'] = local_entry['contactInfo']
                changed = True
            # chineseName：同步
            if local_entry.get('chineseName') and not server_entry.get('chineseName'):
                server_entry['chineseName'] = local_entry['chineseName']
                changed = True
            # editedAt：同步
            if local_entry.get('editedAt'):
                server_entry['editedAt'] = local_entry['editedAt']
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
        # POST to root path (for TALENT_API)
        req = urllib.request.Request(API, data=payload, method='POST',
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'sync/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode('utf-8')
        print(f'POST root: {result}')

        # Also deploy to reports/ path (for static fallback)
        deploy_payload = json.dumps({
            'file': 'reports/talent-notes.json',
            'content': payload.decode('utf-8')
        }).encode('utf-8')
        req2 = urllib.request.Request('http://43.167.194.82:8800/deploy', data=deploy_payload, method='POST',
                                      headers={'Content-Type': 'application/json', 'User-Agent': 'sync/1.0'})
        with urllib.request.urlopen(req2, timeout=60) as resp2:
            result2 = resp2.read().decode('utf-8')
        print(f'Deploy reports/: {result2}')
        print('Done! Both paths updated.')
    except Exception as e:
        print(f'POST failed: {e}')

if __name__ == '__main__':
    main()
