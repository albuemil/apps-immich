#!/usr/bin/env python3
"""
Update device albums in Immich.

Albums prefixed with 🎥 collect everything shot with one device.
For each album, finds all assets matching that device's rules (camera
model and/or original filename prefix) and adds any missing ones.
No new albums are created.

Album name format: 🎥 Device  (e.g. 🎥 DJI Neo 2)

Why filename rules: videos from some devices (the DJI Neo 2 among them)
carry no make/model metadata in Immich, so the camera model alone only
catches the photos.
"""

import asyncio
import os
import sys
import httpx

BASE_URL = os.environ.get("IMMICH_BASE_URL", "http://localhost:2283")
API_KEY = os.environ.get("IMMICH_API_KEY", "")

if not API_KEY:
    print("Error: IMMICH_API_KEY environment variable required")
    sys.exit(1)

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

DEVICE_PREFIX = "🎥"

# Album name (without prefix) -> how to recognise that device's files.
#   models:            exact EXIF camera model(s)
#   filename_prefixes: original filename starts with (case-insensitive)
DEVICES = {
    "DJI Neo 2": {
        "models": ["FC9470"],
        # dji_fly_*: files saved by the DJI Fly app (the Osmo/Mimo ones are
        # DJI_<date>_...); compose_video_*: 4K clips the DJI Fly app renders
        "filename_prefixes": ["dji_fly_", "compose_video_"],
    },
}


def strip_prefix(album_name: str) -> str:
    return album_name[len(DEVICE_PREFIX):].strip()


async def get_album_asset_ids(client: httpx.AsyncClient, album_id: str) -> set[str]:
    buckets_resp = await client.get(f"{BASE_URL}/api/timeline/buckets", params={"albumId": album_id, "size": "MONTH"})
    buckets_resp.raise_for_status()
    ids: set[str] = set()
    for bucket in buckets_resp.json():
        b_resp = await client.get(f"{BASE_URL}/api/timeline/bucket", params={
            "albumId": album_id, "size": "MONTH", "timeBucket": bucket["timeBucket"]
        })
        b_resp.raise_for_status()
        ids.update(b_resp.json().get("id", []))
    return ids


async def search(client: httpx.AsyncClient, query: dict) -> list[dict]:
    """Return all assets matching a metadata query, handling pagination."""
    items: list[dict] = []
    page = 1
    while True:
        resp = await client.post(
            f"{BASE_URL}/api/search/metadata",
            json={**query, "page": page, "size": 200},
        )
        resp.raise_for_status()
        assets = resp.json().get("assets", {})
        items.extend(assets.get("items", []))
        if not assets.get("nextPage"):
            break
        page += 1
    return items


async def search_by_model(client: httpx.AsyncClient, model: str) -> set[str]:
    return {a["id"] for a in await search(client, {"model": model})}


async def search_by_filename_prefix(client: httpx.AsyncClient, prefix: str) -> set[str]:
    # originalFileName is a substring match, so filter down to a real prefix
    found = await search(client, {"originalFileName": prefix})
    return {a["id"] for a in found if a["originalFileName"].lower().startswith(prefix.lower())}


async def add_assets(client: httpx.AsyncClient, album_id: str, asset_ids: list[str]) -> int:
    added = 0
    for i in range(0, len(asset_ids), 100):
        batch = asset_ids[i: i + 100]
        resp = await client.put(
            f"{BASE_URL}/api/albums/{album_id}/assets", json={"ids": batch}
        )
        resp.raise_for_status()
        added += sum(1 for r in resp.json() if r.get("success"))
    return added


async def set_description(client: httpx.AsyncClient, album_id: str, desc: str) -> None:
    resp = await client.patch(
        f"{BASE_URL}/api/albums/{album_id}", json={"description": desc}
    )
    resp.raise_for_status()


async def main() -> None:
    async with httpx.AsyncClient(timeout=60.0, headers=HEADERS) as client:
        resp = await client.get(f"{BASE_URL}/api/albums")
        resp.raise_for_status()
        albums = [
            a for a in resp.json()
            if a["albumName"].startswith(DEVICE_PREFIX)
        ]
        print(f"Found {len(albums)} device albums\n")

        total_added = 0

        for album in albums:
            album_id = album["id"]
            album_name = album["albumName"]
            display = strip_prefix(album_name)
            print(f"{'─' * 50}\n{album_name}")

            rules = DEVICES.get(display)
            if not rules:
                print(f"  no rules for '{display}' in DEVICES — skipped")
                continue

            current = await get_album_asset_ids(client, album_id)
            matched: set[str] = set()

            for model in rules.get("models", []):
                found = await search_by_model(client, model)
                print(f"  model {model}: {len(found)}")
                matched.update(found)

            for prefix in rules.get("filename_prefixes", []):
                found = await search_by_filename_prefix(client, prefix)
                print(f"  filename {prefix}*: {len(found)}")
                matched.update(found)

            new_ids = list(matched - current)
            print(f"  current: {len(current)}  matched: {len(matched)}  new: {len(new_ids)}")

            if new_ids:
                added = await add_assets(client, album_id, new_ids)
                print(f"  added {added} assets")
                total_added += added

            if not album.get("description"):
                desc = f"Everything shot with the {display}."
                await set_description(client, album_id, desc)
                print(f"  description set: '{desc}'")

    print(f"\nDone. Total added: {total_added}")


if __name__ == "__main__":
    asyncio.run(main())
