# 贡献指南

感谢你对 Album Explorer 的关注！欢迎提交 Issue 和 Pull Request。

## 开发环境搭建

### 前置条件

- Python 3.11+
- Node.js 18+
- 一份由 [album-assetizer](https://github.com/SeanWong17/album-assetizer) 生成的数据库

### 启动开发环境

```bash
# 后端
cd backend
pip install -e ".[ml]"
cp ../.env.example ../.env  # 编辑 .env 填入实际路径
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## 提交 PR

1. Fork 本仓库并创建功能分支
2. 确保代码能正常构建（`npm run build` / `python -c "from app.main import app"`)
3. 提交信息使用中文，简明描述改动内容
4. 一个 PR 只做一件事，保持改动聚焦

## 代码风格

- 后端：遵循现有代码风格，使用 type hints
- 前端：TypeScript + Vue 3 Composition API，使用 TailwindCSS
- 提交信息格式：`模块：简要描述`（如 `搜索页：支持自适应分页`）

## 报告问题

提交 Issue 时请包含：
- 问题描述和复现步骤
- 运行环境（OS、Python 版本、Node 版本）
- 相关日志或截图
