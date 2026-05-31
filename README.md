# Album Explorer

相册语义浏览器，消费 `album-assetizer` 生成的图像描述数据，提供多维度浏览体验。

## 功能

### 浏览

- **首页推荐**：最近拍摄、随机精选、热门主题、已保存搜索、热门地点多区块并列，各区块独立刷新
- **时间线视图**：按月分组浏览，前 3 个月立即加载两行，其余懒加载（滚动到视口自动触发），支持展开/收起/折叠
- **地图视图**：城市聚合气泡（低缩放）+ 单点标记（高缩放），点击直接打开详情
- **聚类相册**：HDBSCAN embedding 聚类，自动命名，支持手动设置/取消封面图
- **标签图谱**：D3 力导向图展示标签共现关系，可调节最小共现阈值
- **统一探索页**：支持文本搜索 + 城市/省份/月份/标签/日期范围/GPS 多维筛选 + 日历选择器

### 搜索

- **FTS5 全文搜索**：覆盖描述、场景、标签、城市名
- **统一查询模型**：QueryBuilder 支持任意筛选组合
- **保存搜索**：将常用筛选条件保存为快捷入口

### 图片管理

- **手动相册**：创建/删除相册，添加/移出图片，批量操作
- **图片删除**：确认后原图移到回收站（`D:\数据备份\图像\.trash`），数据库标记删除
- **批量选择**：手机相册风格多选，支持批量添加到相册、批量删除
- **相似图片**：基于预计算 Top-K 邻居的即时相似推荐

### 图片详情

- 大图预览 + 左右箭头/键盘切换 + 相邻图片预加载
- 完整元数据（时间、地点、聚类、标签、活动、主体）
- 上下文探索：相似图片、同主题、相关标签图片
- 元数据可点击跳转到探索页筛选
- 添加到相册 / 删除操作

### 界面

- **暗色/亮色主题**：一键切换，自动检测系统偏好，localStorage 持久化
- **每行显示数量可调**：滑块控制网格列数（4-12），自动刷新填满两行
- 响应式布局，可折叠侧边栏

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

# GPS 反查城市名（基于地级市 Shapefile 点在面查询）
# 首次需下载行政区划数据：git clone --depth 1 https://github.com/GaryBikini/ChinaAdminDivisonSHP.git data/china_shp
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

# 预计算相似图片邻居
python -m tasks.build_neighbors

# 丰富聚类信息（摘要、封面、标签）
python -m tasks.enrich_clusters
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

- 后端：FastAPI + SQLite + aiosqlite + FTS5
- 前端：Vue 3 + Vite + TailwindCSS + Pinia + Vue Router
- 地图：Leaflet + markercluster
- 地理编码：GeoPandas + 地级市 Shapefile（点在面查询）
- 聚类：HDBSCAN + bge-small-zh-v1.5
- 相似度：cosine similarity 预计算 Top-K 邻居
- 图谱：D3.js force layout

## 目录结构

```
album-explorer/
├── backend/
│   ├── app/
│   │   ├── routers/       # API 路由
│   │   │   ├── assets.py      # 图片 CRUD + 删除 + 相似 + 上下文
│   │   │   ├── albums.py      # 手动相册 CRUD
│   │   │   ├── clusters.py    # 聚类列表 + 详情
│   │   │   ├── map_view.py    # 地图点位 + 城市聚合
│   │   │   ├── saved_searches.py  # 保存搜索 CRUD
│   │   │   ├── stats.py       # 统计 + 推荐
│   │   │   ├── tags.py        # 标签列表 + 图谱
│   │   │   ├── timeline.py    # 时间线
│   │   │   └── thumbnails.py  # 缩略图服务
│   │   ├── services/
│   │   │   └── query_builder.py  # 统一查询构建器
│   │   ├── database.py    # DB 连接 + FTS5 初始化
│   │   ├── models.py      # Pydantic 模型
│   │   └── main.py        # FastAPI 入口
│   └── tasks/             # 离线数据处理任务
│       ├── build_neighbors.py      # 预计算 Top-K 相似邻居
│       ├── build_tag_graph.py      # 标签共现图
│       ├── enrich_clusters.py      # 聚类信息丰富
│       ├── generate_embeddings.py  # 向量生成
│       ├── generate_thumbnails.py  # 缩略图生成
│       ├── reverse_geocode.py      # GPS 反查
│       └── run_clustering.py       # HDBSCAN 聚类
├── frontend/
│   └── src/
│       ├── views/         # 页面组件
│       ├── components/    # 通用组件（PhotoGrid, PhotoDetail, AlbumPicker 等）
│       ├── stores/        # Pinia 状态（ui, filters）
│       ├── api/           # API 封装
│       └── router/        # 路由配置
└── data/                  # 生成数据（缩略图、向量）
```
