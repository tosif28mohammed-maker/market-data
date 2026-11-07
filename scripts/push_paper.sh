#!/bin/bash
# commit paper/ (intraday paper robot) safely while other robots also push
git config user.name "market-data-bot"; git config user.email "actions@users.noreply.github.com"
git add paper data/intra* 2>/dev/null
git commit -qm "${1:-intraday paper}" || exit 0
for i in 1 2 3; do git pull -q --rebase -X theirs && git push -q && exit 0; sleep 5; done
