#!/usr/bin/env bash
set -e
REPO=/home/yakim/ai-rag-template
# ЗАМЕНИ email ниже на свой GitHub-email, чтобы зелёные квадраты считались!
GIT_NAME="yakim"
GIT_EMAIL="yakim@local"
cd "$REPO"
DATE=$(date +%F)
# допиши строку в дневник обучения (green graph на GitHub)
echo "- $DATE : прогресс по AI Engineering треку" >> LEARNING_LOG.md
git -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" add -A
if git -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" diff --cached --quiet; then
  echo "nothing to commit"
  exit 0
fi
git -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" commit -m "daily: $DATE learning log"
# раскомментируй, когда добавишь remote (после создания репо на GitHub):
# git push origin main || true
