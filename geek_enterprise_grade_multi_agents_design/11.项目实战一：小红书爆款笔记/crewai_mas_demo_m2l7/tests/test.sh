# ======= 重要提示 =======
# 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 各地域配置不同，请根据实际地域修改
# === 执行时请删除该注释 ===

curl --location 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' \
--header "Authorization: Bearer sk-ffe676b99d034fc9846d47ba62537b0c" \
--header 'Content-Type: application/json' \
--data '{
  "model": "qwen3.6-flash",
  "messages": [
  {
    "role": "user",
    "content": [
      {"type": "image_url", "image_url": {"url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"}},
      {"type": "text", "text": "图中描绘的是什么景象?"}
    ]
  }]
}'