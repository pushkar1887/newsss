# Project backup

This public repository stores a snapshot of the project in [GitHub Releases](https://github.com/pushkar1887/newsss/releases/tag/project-backup-2026-10-28). The snapshot contains 320,088 files and 109 directories, including hidden directories and the nested Git data. The credentials file was intentionally excluded.

The project files are stored in a split archive, so they are available after downloading and restoring the release assets; they are not individually browsable in the repository.

## Restore the project

1. Download all four assets from the release into the same folder:
   - `new_viral_proj.tar.gz.part001`
   - `new_viral_proj.tar.gz.part002`
   - `manifest.jsonl.gz`
   - `summary.json`
2. Download [restore_backup.py](https://github.com/pushkar1887/newsss/blob/main/restore_backup.py) into that same folder.
3. Open PowerShell in that folder and run:

   ```powershell
   python .\restore_backup.py --assets . --destination .
   ```

The script requires Python 3.10 or newer and no additional packages. It verifies the SHA-256 of every downloaded asset and restored file, then creates a `new_viral_proj` folder. It refuses to overwrite an existing folder with that name. The restored files require approximately 5.53 GB of free space.
