#!/usr/bin/env python3
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile
import plistlib
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = f"https://api.github.com/repos/{REPO}"
OUT = Path("dist")
OUT.mkdir(exist_ok=True)

def api_get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})
    })
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "SideStore-Source-Builder",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN and "api.github.com" in url else {})
    })
    with urllib.request.urlopen(req) as res:
        return res.read()

def read_app_info(ipa_bytes):
    with zipfile.ZipFile(io.BytesIO(ipa_bytes)) as zf:
        candidates = [n for n in zf.namelist()
                      if n.startswith("Payload/") and n.endswith(".app/Info.plist")]
        if not candidates:
            raise ValueError("IPA 안에서 Payload/*.app/Info.plist를 찾지 못했습니다.")
        return plistlib.loads(zf.read(candidates[0]))

def releases_all():
    result, page = [], 1
    while True:
        batch = api_get(f"{API}/releases?per_page=100&page={page}")
        if not batch:
            break
        result.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return result

config = json.loads(Path("metadata/apps.json").read_text(encoding="utf-8"))
source_meta = config["source"]
overrides = {a["bundleIdentifier"]: a for a in config.get("apps", [])}
apps = {}

for release in releases_all():
    if release.get("draft"):
        continue
    published = release.get("published_at") or release.get("created_at")
    date = (published or datetime.now(timezone.utc).isoformat())[:10]
    notes = (release.get("body") or "").strip()
    for asset in release.get("assets", []):
        if not asset["name"].lower().endswith(".ipa"):
            continue
        ipa = download(asset["browser_download_url"])
        info = read_app_info(ipa)
        bundle = info.get("CFBundleIdentifier")
        version = info.get("CFBundleShortVersionString")
        if not bundle or not version:
            print(f"SKIP {asset['name']}: CFBundleIdentifier 또는 CFBundleShortVersionString 없음", file=sys.stderr)
            continue

        meta = overrides.get(bundle, {})
        display_name = (meta.get("name")
                        or info.get("CFBundleDisplayName")
                        or info.get("CFBundleName")
                        or bundle)
        pages_url = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/"
        icon_url = meta.get("iconURL") or pages_url + "assets/default-icon.png"
        entry = apps.setdefault(bundle, {
            "name": display_name,
            "bundleIdentifier": bundle,
            "developerName": meta.get("developerName") or source_meta.get("defaultDeveloperName", "Unknown Developer"),
            "localizedDescription": meta.get("localizedDescription") or source_meta.get("defaultDescription", "iOS application"),
            "iconURL": icon_url,
            "versions": []
        })
        for optional in ("subtitle", "tintColor"):
            if meta.get(optional):
                entry[optional] = meta[optional]
        entry["versions"].append({
            "version": str(version),
            "date": date,
            "downloadURL": asset["browser_download_url"],
            "size": int(asset["size"]),
            "localizedDescription": notes or f"Release {version}"
        })

for entry in apps.values():
    entry["versions"].sort(key=lambda v: v["date"], reverse=True)

source = {
    "name": source_meta["name"],
    "identifier": source_meta["identifier"],
    "apps": sorted(apps.values(), key=lambda a: a["name"].casefold())
}
Path("dist/apps.json").write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
shutil.copytree("assets", "dist/assets", dirs_exist_ok=True)

repo_url = f"https://github.com/{REPO}"
pages_url = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/"
html = f"""<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{source_meta['name']}</title>
<style>body{{font:16px system-ui;max-width:760px;margin:4rem auto;padding:0 1.2rem;line-height:1.6}}code{{overflow-wrap:anywhere}}a{{color:#0969da}}</style>
<h1>{source_meta['name']}</h1>
<p>SideStore용 개인 앱 저장소입니다.</p>
<p><a href="sidestore://source?url={pages_url}apps.json">SideStore에서 Source 추가</a></p>
<p>Source JSON: <a href="apps.json">{pages_url}apps.json</a></p>
<p>저장소: <a href="{repo_url}">{repo_url}</a></p>
</html>"""
Path("dist/index.html").write_text(html, encoding="utf-8")
print(f"Generated {len(apps)} app entries at dist/apps.json")
