#!/usr/bin/env python3
"""
Sync latest data to Lighthouse server after git push.
Calls /pull-github API to pull index.html + arxiv-daily.json + index.json
Then calls sync-talents.py to push talent data.
"""
import urllib.request, json, sys, os

SERVER = "http://43.167.194.82:8800"

def pull_github():
    """Tell server to pull latest files from GitHub"""
    print("[1/2] Calling /pull-github API...")
    try:
        req = urllib.request.Request(
            f"{SERVER}/pull-github",
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read().decode())
        if result.get("ok"):
            for f in result.get("updated", []):
                print(f"  ✅ {f['file']} ({f['size']:,} bytes)")
            return True
        else:
            print(f"  ❌ Server error: {result}")
            return False
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def sync_reports():
    """Pull report .md files from GitHub to server"""
    print("[2/2] Syncing report files...")
    try:
        # Get index.json to find all report files
        idx_url = "https://raw.githubusercontent.com/eirachen/ai-research-radar/main/reports/index.json"
        req = urllib.request.Request(idx_url, headers={"User-Agent": "ai-radar-sync"})
        resp = urllib.request.urlopen(req, timeout=15)
        reports = json.loads(resp.read().decode())
        
        synced = 0
        for report_path in reports:
            fn = report_path.split("/")[-1] if "/" in report_path else report_path
            gh_url = f"https://raw.githubusercontent.com/eirachen/ai-research-radar/main/reports/{fn}"
            try:
                req = urllib.request.Request(gh_url, headers={"User-Agent": "ai-radar-sync"})
                resp = urllib.request.urlopen(req, timeout=15)
                content = resp.read().decode("utf-8")
                
                # Deploy to server via /deploy API (with subdir support)
                payload = json.dumps({"file": f"reports/{fn}", "content": content})
                deploy_req = urllib.request.Request(
                    f"{SERVER}/deploy",
                    method="POST",
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                deploy_resp = urllib.request.urlopen(deploy_req, timeout=30)
                deploy_result = json.loads(deploy_resp.read().decode())
                if deploy_result.get("ok"):
                    synced += 1
            except Exception as e:
                print(f"  ⚠️ {fn}: {e}")
        
        print(f"  ✅ {synced}/{len(reports)} reports synced")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

if __name__ == "__main__":
    ok1 = pull_github()
    ok2 = sync_reports()
    
    if ok1:
        print("\n✅ Lighthouse 同步完成！")
    else:
        print("\n⚠️ 部分同步失败，请检查")
    
    sys.exit(0 if ok1 else 1)
