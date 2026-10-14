#!/usr/bin/env bash
set -e

PLUGIN_NAME="zapret-deck"
ZIP_NAME="${PLUGIN_NAME}.zip"

echo "🔨 Building frontend with npm..."
npm run build

echo "📦 Creating release structure..."
BUILD_DIR="/tmp/${PLUGIN_NAME}_build"
rm -rf "${BUILD_DIR}" "${ZIP_NAME}"
mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}"

# Copy plugin root files
cp plugin.json "${BUILD_DIR}/${PLUGIN_NAME}/"
cp package.json "${BUILD_DIR}/${PLUGIN_NAME}/"
cp main.py "${BUILD_DIR}/${PLUGIN_NAME}/"
[ -f warp_manager.py ] && cp warp_manager.py "${BUILD_DIR}/${PLUGIN_NAME}/"
[ -f zapret_manager.py ] && cp zapret_manager.py "${BUILD_DIR}/${PLUGIN_NAME}/"
[ -f LICENSE ] && cp LICENSE "${BUILD_DIR}/${PLUGIN_NAME}/"
cp README*.md "${BUILD_DIR}/${PLUGIN_NAME}/"

# Copy directories
mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}/dist"
cp -r dist/* "${BUILD_DIR}/${PLUGIN_NAME}/dist/"

mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}/bin"
cp -r bin/* "${BUILD_DIR}/${PLUGIN_NAME}/bin/"

mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}/lists"
cp -r lists/* "${BUILD_DIR}/${PLUGIN_NAME}/lists/"

mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}/py_modules"
cp -r py_modules/* "${BUILD_DIR}/${PLUGIN_NAME}/py_modules/"

mkdir -p "${BUILD_DIR}/${PLUGIN_NAME}/tray"
cp -r tray/* "${BUILD_DIR}/${PLUGIN_NAME}/tray/"

[ -d assets ] && cp -r assets "${BUILD_DIR}/${PLUGIN_NAME}/"

echo "🗜️ Packaging ${ZIP_NAME}..."
cd "${BUILD_DIR}"
zip -r "${ZIP_NAME}" "${PLUGIN_NAME}" -x "*.git*" "*__pycache__*" "*.pyc" "*node_modules*"
cd - > /dev/null

mv "${BUILD_DIR}/${ZIP_NAME}" "./${ZIP_NAME}"
rm -rf "${BUILD_DIR}"

echo "✅ Package ready: ${ZIP_NAME}"
ls -lh "${ZIP_NAME}"
sha256sum "${ZIP_NAME}"
