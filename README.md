# Album Explorer

相册语义浏览器，消费 `album-assetizer` 生成的图像描述数据，提供多维度浏览体验。

## 功能

- **时间线视图**：按月分组瀑布流浏览
- **地图视图**：Leaflet 地图聚合标记，按地理位置浏览
- **聚类相册**：HDBSCAN embedding 聚类，自动命名
- **全文搜索**：搜索描述、标签、场景
- **标签图谱**：D3 力导向图展示标签共现关系
- **图片详情**：大图预览 + 完整元数据

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -e .
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 运行数据处理任务（首次使用）

```bash
cd backend

# GPS 反查城市名
python -m tasks.reverse_geocode

# 批量生成缩略图（耗时较长）
python -m tasks.generate_thumbnails --workers 4

# 生成 embedding 向量（需要 GPU，约 1-2 分钟）
pip install -e ".[ml]"
python -m tasks.generate_embeddings

# 执行聚类
python -m tasks.run_clustering

# 构建标签共现图
python -m tasks.build_tag_graph
```

### 4. 启动开发服务器

```bash
# 终端 1：后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

访问 http://localhost:3000

## 技术栈

- 后端：FastAPI + SQLite + aiosqlite
- 前端：Vue 3 + Vite + TailwindCSS + Pinia
- 地图：Leaflet + markercluster
- 聚类：HDBSCAN + bge-small-zh-v1.5
- 图谱：D3.js force layout

## 目录结构

```
album-explorer/
├── backend/          # Python 后端
│   ├── app/          # FastAPI 应用
│   └── tasks/        # 数据处理任务
├── frontend/         # Vue 3 前端
│   └── src/
└── data/             # 生成数据（缩略图、向量）
```
