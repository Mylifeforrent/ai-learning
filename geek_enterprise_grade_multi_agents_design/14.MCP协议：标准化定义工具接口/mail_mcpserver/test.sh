curl -X POST http://localhost:8000/api/v1/register \
  -H "Authorization: Bearer test-api-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user01","email":"1299351443@qq.com","passkey":"hxwmjgovnoieiffi"}'


  # 列出所有工具
curl -X POST http://localhost:8000/mcp/ \
  -H "Authorization: Bearer test-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'

# 查看邮件列表
curl -X POST http://localhost:8000/mcp/ \
  -H "Authorization: Bearer test-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_mail_list","arguments":{"email":"tony.p.tian@qq.com","limit":5}},"id":2}'

# 查看邮件详情
curl -X POST http://localhost:8000/mcp/ \
  -H "Authorization: Bearer test-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_mail_detail","arguments":{"email":"tony.p.tian@qq.com","mail_uid":"123"}},"id":3}'

# 发送邮件
curl -X POST http://localhost:8000/mcp/ \
  -H "Authorization: Bearer test-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"send_email","arguments":{"from_email":"tony.p.tian@qq.com","to_email":"receiver@163.com","subject":"测试邮件","body":"这是一封测试邮件"}},"id":4}'