This file explains how to remove large files from git history and prepare the repository for GitHub.

Steps (recommended):

1. Install Git LFS (recommended for future large files)

   - Windows (PowerShell):

     choco install git-lfs
     git lfs install

   - Or download from https://git-lfs.github.com/

2. Track large file types (example):

   git lfs track "models/**"
   git lfs track "data/**"
   git add .gitattributes

3. Remove large files from the index (do NOT run until you review):

   git rm --cached -r data models instance
   git commit -m "Remove data, models and instance from repository"

4. If large files were already pushed and you need to remove them from history, use one of these tools:

   - BFG Repo-Cleaner (easy):

     java -jar bfg.jar --delete-folders data --delete-folders models --delete-folders instance
     git reflog expire --expire=now --all && git gc --prune=now --aggressive

   - git filter-repo (recommended if available):

     pip install git-filter-repo
     git filter-repo --invert-paths --paths data/ --paths models/ --paths instance/

   After rewriting history, force-push to remote (be careful):

     git push --force --all
     git push --force --tags

5. Verify size reduction using `git count-objects -vH` and inspect large files with `git verify-pack -v .git/objects/pack/pack-*.idx | sort -k3 -n | tail -n 20`.

Notes:
- These operations rewrite history. If others collaborate on this repo, coordinate before force-pushing.
- Keep backups before running history-rewriting commands.
- After cleaning, use `git lfs track` for model/data patterns so future pushes use LFS.
