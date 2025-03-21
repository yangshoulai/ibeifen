# 消息备份机器人

一个功能强大的 Telegram 消息备份机器人，支持多种类型消息的备份、搜索和管理。

## 功能特点

### 消息备份
- 支持多种消息类型的备份：
  - 📝 文本消息
  - 🖼 图片消息
  - 🎥 视频消息
  - 📄 文档消息
  - 🎤 语音消息
- 自动将消息转发到指定频道存档
- 智能分词存储，支持中文搜索
- 保留原始消息的所有元数据

### 用户管理
- 支持用户注册/注销
- 自动注册功能
- 用户数据隔离
- 用户数据统计

### 消息搜索
- 支持关键词搜索
- 分页显示搜索结果
- 美观的消息预览
- 便捷的消息查看按钮
- 支持查看原始消息

### 个人统计
- 详细的消息类型统计
- 备份时间范围统计
- 总消息数统计

## 命令列表

- `/start` - 显示帮助信息
- `/register` - 注册用户
- `/unregister` - 注销用户（同时删除所有备份数据）
- `/search [关键词]` - 搜索消息
  - 直接使用 `/search` 显示最近的消息
  - 使用 `/search 关键词` 搜索特定消息
- `/me` - 查看个人信息统计

## 技术特点

- 使用 Python 3.11 开发
- 基于 python-telegram-bot 21.10 框架
- SQLite 数据库存储
- SQLAlchemy ORM 支持
- Docker 容器化部署
- 支持环境变量配置

## 环境要求

- Python 3.11+
- SQLite 3
- Docker（可选）

## 配置说明

项目使用环境变量进行配置，支持 `.env` 文件：

```env
# 必需配置
BOT_TOKEN=your_bot_token
BEIFEN_CHAT_ID=your_channel_id

# 可选配置
DATABASE_URL=sqlite:///data/bot.db
PROXY=your_proxy_url
```

## 快速开始

1. 克隆项目：
   ```bash
   git clone https://github.com/yourusername/telegram-backup-bot.git
   cd telegram-backup-bot
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入必要的配置信息
   ```

4. 运行机器人：
   ```bash
   python -m src.main
   ```

### Docker 部署

1. 构建镜像：
   ```bash
   docker build -t telegram-backup-bot .
   ```

2. 运行容器：
   ```bash
   docker run -d \
     --name telegram-backup-bot \
     -v $(pwd)/data:/app/data \
     --env-file .env \
     telegram-backup-bot
   ```

## 数据存储

- 用户信息：用户ID、用户名、注册时间等
- 消息记录：
  - 消息ID
  - 用户ID
  - 消息类型
  - 消息内容
  - 文件ID（媒体文件）
  - 转发消息ID
  - 创建时间
  - 分词结果

## 注意事项

1. 请确保机器人具有在目标频道发送消息的权限
2. 建议定期备份数据库文件
3. 注销用户会删除该用户的所有备份数据
4. 媒体文件的 file_id 可能会过期，建议使用频道转发功能

## 开发计划

- [ ] 支持更多消息类型
- [ ] 添加消息标签功能
- [ ] 支持导出备份数据
- [ ] 添加管理员功能
- [ ] 支持自定义消息模板

## 贡献指南

欢迎提交 Issue 和 Pull Request。在提交 PR 之前，请确保：

1. 代码符合 PEP 8 规范
2. 添加必要的测试用例
3. 更新相关文档

## 许可证

MIT License

