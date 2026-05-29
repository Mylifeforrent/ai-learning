本项目是个MCP服务，实现了通过imap_tools和smtp支持邮箱邮件发送的能力
该服务主要提供了以下几个工具
1、邮件列表查看get_mail_list
参数包括：邮箱地址email，文件夹（可选），条数（可选默认20），offset（可选默认0），搜索词（可选）
2、邮件详情查看get_mail_detail
参数包括：邮箱地址email，邮件id
3、发送邮件：send_email
参数包括：发件邮箱地址send_email，收件邮箱地址to_email，标题，正文（支持Multipart）

该服务支持国内qq, sina, 163邮箱，配置文件保存了对应的后缀特征和IMAP、SMTP服务器地址

该服务只能为事先注册的用户提供服务。需要用户提前将用户id（user_id），邮箱（email）和授权码（passkey）写入到加密的配置文件，一个用户可以注册多个邮箱。服务开放了一个额外的http端点接收用户邮箱配置。

该服务需要上游请求携带user_id的请求头，且会在操作时先校验user_id和email/send_email是否和配置文件匹配，才提供服务