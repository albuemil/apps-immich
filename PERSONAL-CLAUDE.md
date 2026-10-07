# Personal Setup & Claude Session Reference

This file documents personal customizations, setup decisions, and findings from Claude-assisted sessions.

---

## Repository Setup

This is a **personal fork** of [drolosoft/immich-photo-manager](https://github.com/drolosoft/immich-photo-manager).

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | `https://github.com/albuemil/immich-photo-manager` | Personal fork — push here |
| `upstream` | `https://github.com/drolosoft/immich-photo-manager` | Original repo — pull updates from here |

**Sync with upstream:**
```bash
./sync-upstream.sh
# or manually:
git fetch upstream && git merge upstream/main && git push origin main
```

**Versioning:** personal changes are tagged `personal-vX.Y.Z` (independent of upstream plugin version). See `PERSONAL-CHANGELOG.md`.

---

## WSL Environment

Credentials and shortcuts set in `~/.bashrc`:

```bash
export IMMICH_API_KEY="..."
export IMMICH_BASE_URL="http://10.198.5.100:2283"
alias cd_claude="cd /mnt/d/Work/Claude"
```

All scripts in `user_scripts/` read these env vars automatically — no hardcoding needed.

---

## Personal Scripts (`user_scripts/`)

### `update_people_albums.py`
Syncs 👤/👥 people albums from Immich face recognition.
- Matches album names (stripping prefix) to recognized people
- Supports `Name A & Name B` multi-person albums
- Adds missing photos; sets description if empty
- **Skill:** `/photos-update-people`

### `update_location_albums.py`
Syncs 🏛️ landmark albums from GPS city/country metadata.
- Parses `ISO/City` from album name (e.g. `🏛️ RO/Timișoara` → Romania / Timișoara)
- Handles multi-city albums: `🏛️ RO/City1 & City2`
- Paginates metadata search results
- **Skill:** `/photos-update-locations`

### `update_device_albums.py`
Syncs 🎥 device albums ("everything shot with this device").
- Rules live in `DEVICES` at the top of the script, keyed by album name without the prefix: exact EXIF camera `models` and/or `filename_prefixes`
- Filename rules exist because some devices' videos carry no make/model in Immich (DJI Neo 2: only the photos have model `FC9470`; everything from the DJI Fly app is named `dji_fly_*`). The Osmo Mobile/Mimo files are `DJI_<date>_...` and are deliberately not matched
- Adds missing assets only (never removes); sets description if empty; albums with the prefix but no rule are skipped
- To add a device: create the `🎥 Name` album in Immich, add a `"Name": {...}` entry to `DEVICES`
- **Skill:** `/photos-update-devices`

> **Romanian diacritics quirk:** Immich's geocoder (GeoNames) stores city names with legacy
> cedilla characters (`ş` U+015F, `ţ` U+0163) instead of the correct comma-below variants
> (`ș` U+0219, `ț` U+021B). The script normalizes before searching so album names can use
> proper Romanian spelling.

---

## Album Naming Convention

| Type | Format | Example |
|------|--------|---------|
| Travel | `✈️ YYYY/MM 🏳️ ISO/Location` | `✈️ 2023/04 🇪🇸 ES/Tenerife` |
| Landmark | `🏛️ ISO/Location` | `🏛️ RO/Timișoara` |
| People | `👤 Name` or `👥 Name1 & Name2` | `👤 Ina` |
| Device | `🎥 Device` | `🎥 DJI Neo 2` |
| Events | `🎉 YYYY/MM Title` | `🎉 2025/10 Nuntă Simo` |
| dōTERRA | `ō YYYY/MM ISO/City Title` | `ō 2026/05 PL/Katowice Me` |
| Pets | `🐾 Name` | `🐾 Palika` |
| Home/project | `🏗️ Location/Project` | `🏗️ Amzei/Gradina` |

---

## Claude Skills (`.claude/commands/`)

| Skill | Command file | What it does |
|-------|-------------|--------------|
| `/photos-update-people` | `photos-update-people.md` | Runs `update_people_albums.py` |
| `/photos-update-locations` | `photos-update-locations.md` | Runs `update_location_albums.py` |
| `/photos-update-devices` | `photos-update-devices.md` | Runs `update_device_albums.py` |
| `/photos-update-gps-radius` | `photos-update-gps-radius.md` | Runs `update_gps_radius_albums.py` |
| `/photos-rotate` | `photos-rotate.md` | Processes rotate LEFT / rotate RIGHT albums via MCP |

---

## Session Log

### 2026-10-07
- Added `update_device_albums.py` + `/photos-update-devices` skill; created `🎥 DJI Neo 2` (26 assets: 25 videos + 1 photo, 2026-10-02/04)
- Prefix is 🎥, not 📷 — `📷 Best of Emil` already uses 📷 for something else
- Run on the unRAID box (no `httpx` in system Python there): use a venv, or run from WSL as usual

### 2026-07-14
- Fixed Immich v3 breaking change: `GET /api/albums/{id}` no longer returns assets; all scripts updated to use timeline API
- Added `update_gps_radius_albums.py` — finds GPS-tagged photos within km radius of city center; covers Timișoara (12km), TGM (8km), Răstolița (10km), Ocna de Fier (10km)
- Added `/photos-update-gps-radius` skill
- Created `🏛️ RO/Târgu Mureș` album; added 252 photos via GPS radius search
- Fixed 8 photos from 2019-07-30 incorrectly GPS-tagged as Răstolița (fix_missing_gps false positive); corrected to TGM coords
- Fixed zoo GIF GPS to TGM Zoo location
- Ran `fix_missing_gps.py --apply` → 284 GPS fixes applied across library
- Album naming: renamed to `🐾 Speedy` and `🚁 Toys for big boys`

### 2026-07-08
- Immich v3.0.1 upgrade failed — postgres data directory was deleted by a cleanup script
- Recovered from daily SQL dump (`immich-db-backup-20260707T020000-v3.0.1-pg14.19.sql.gz`) synced via rclone to `/root/!!!!Sync_with_jotta/Immich/backups/`
- Dump restored into `postgres` database instead of `immich`; fixed by piping pg_dump between databases
- Full recovery with <24h data loss; all 60k assets, 107 albums, 1243 people intact
- Added `user_docs/postgres-recovery.md` with exact recovery steps

### 2026-06-21
- Added `update_location_albums.py` — discovered Romanian cedilla diacritic mismatch in GeoNames
- Updated both skills to read env vars from environment (removed hardcoded credential extraction)
- Fixed WSL env vars: added `export` keyword to `IMMICH_API_KEY` / `IMMICH_BASE_URL` in `~/.bashrc`
- Added `cd_claude` alias to `~/.bashrc`
- Set up GitHub fork (`albuemil/immich-photo-manager`) with upstream remote
- Added `sync-upstream.sh` and `PERSONAL-CHANGELOG.md` with `personal-vX.Y.Z` tagging
