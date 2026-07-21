#!/usr/bin/env bash
set -euo pipefail

# Данные для подключения к Steam Deck
DECK_IP="192.168.0.196"
DECK_USER="deck"
DECK_PASS="0451"
PLUGIN_NAME="zapret-deck"
DEST_DIR="/home/deck/homebrew/plugins/${PLUGIN_NAME}"

echo "==> 1. Сборка фронтенда..."
# Устанавливаем зависимости если их нет
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build

echo "==> 2. Создание временной папки для деплоя..."
TEMP_DEPLOY_DIR="/tmp/${PLUGIN_NAME}-deploy"
rm -rf "$TEMP_DEPLOY_DIR"
mkdir -p "$TEMP_DEPLOY_DIR"

# Копируем только необходимые для работы файлы
cp -r dist bin py_modules main.py lists plugin.json package.json "$TEMP_DEPLOY_DIR/"

echo "==> 3. Очистка старой версии на Steam Deck..."
sshpass -p "$DECK_PASS" ssh -o StrictHostKeyChecking=no "${DECK_USER}@${DECK_IP}" "echo '$DECK_PASS' | sudo -S rm -rf '${DEST_DIR}' && echo '$DECK_PASS' | sudo -S mkdir -p '${DEST_DIR}' && echo '$DECK_PASS' | sudo -S chown -R deck:deck '${DEST_DIR}'"

echo "==> 4. Копирование файлов на Steam Deck..."
sshpass -p "$DECK_PASS" scp -o StrictHostKeyChecking=no -r "$TEMP_DEPLOY_DIR"/* "${DECK_USER}@${DECK_IP}:${DEST_DIR}/"

echo "==> 5. Исправление прав доступа на бинарники..."
sshpass -p "$DECK_PASS" ssh -o StrictHostKeyChecking=no "${DECK_USER}@${DECK_IP}" "chmod +x '${DEST_DIR}/bin/nfqws' '${DEST_DIR}/bin/usque'"

echo "==> 6. Перезапуск Decky Loader..."
# Пытаемся перезапустить decky службу (обычно это plugin_loader.service или decky.service)
sshpass -p "$DECK_PASS" ssh -o StrictHostKeyChecking=no "${DECK_USER}@${DECK_IP}" "echo '$DECK_PASS' | sudo -S systemctl restart plugin_loader.service 2>/dev/null || echo '$DECK_PASS' | sudo -S systemctl restart decky 2>/dev/null || true"

echo "==> Успешно деплоировано на Steam Deck!"
rm -rf "$TEMP_DEPLOY_DIR"
