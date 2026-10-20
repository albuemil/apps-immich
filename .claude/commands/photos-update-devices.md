Run the device albums update script to add any missing photos and videos to existing 🎥 device albums (no new albums are created):

```bash
python3 user_scripts/update_device_albums.py
```

Report how many assets were added to each album, and the total count added. If an album was skipped for having no rules, say so — it needs an entry in `DEVICES` at the top of the script.
