#!/usr/bin/env bash
# Curl 示例脚本：调用 API v2 的 /parse 与 /import 端点
# Usage:
#   1) 配置 BASE_URL 与 TOKEN
#   2) ./scripts/api_examples.sh parse
#   3) ./scripts/api_examples.sh import

BASE_URL="http://localhost:8000/api/v2"
# 将此处替换为有效的 JWT（如果 API 开启鉴权）
TOKEN="<YOUR_JWT_TOKEN>"

JSON_PAYLOAD_PARSE=$(cat <<'JSON'
{
  "pdf_path": "backend/tests/test_data/sample_statement.pdf",
  "output_dir": null
}
JSON
)

JSON_PAYLOAD_IMPORT=$(cat <<'JSON'
{
  "pdf_path": "backend/tests/test_data/sample_statement.pdf"
}
JSON
)

hdrs_common=( -H "Content-Type: application/json" )
if [ "$TOKEN" != "<YOUR_JWT_TOKEN>" ]; then
  hdrs_common+=( -H "Authorization: Bearer $TOKEN" )
fi

case "$1" in
  parse)
    echo "POST $BASE_URL/parse"
    curl -sS -X POST "$BASE_URL/parse" "${hdrs_common[@]}" -d "$JSON_PAYLOAD_PARSE" | python -m json.tool
    ;;

  import)
    echo "POST $BASE_URL/import"
    echo "注意：/import 会写入数据库，请在开发/测试环境执行。"
    curl -sS -X POST "$BASE_URL/import" "${hdrs_common[@]}" -d "$JSON_PAYLOAD_IMPORT" | python -m json.tool
    ;;

  *)
    echo "Usage: $0 {parse|import}"
    exit 1
    ;;
esac
