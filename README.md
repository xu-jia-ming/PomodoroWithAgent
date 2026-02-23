# PomodoroTable

一个番茄钟 MVP 项目（Windows 优先），前端使用 Vue3 + Element Plus，后端使用 FastAPI。后续会补上agent功能, 根据用户习惯(番茄钟持续时间...)给出对应的AI建议.

## 文档
- 需求说明：`docs/01-需求说明.md`
- 技术架构：`docs/02-技术方案与架构.md`
- API 设计：`docs/03-API设计.md`
- Git 规范：`docs/04-Git规范流程.md`
- 启动指南：`docs/05-开发与启动指南.md`

## 启动（Windows）

### 1) 启动后端
```bash
cd backend
conda create -n pomodoro-table python=3.11 -y
conda activate pomodoro-table
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2) 启动前端
```bash
cd frontend
npm install
npm run dev
```

浏览器访问：`http://127.0.0.1:5173`

## 标准 Git 流程（简版）
```bash
git checkout -b feature/mvp-initial
# 小步提交
git add .
git commit -m "docs(requirements): add mvp docs"
git commit -m "feat(frontend): implement 5-tab views with element plus"
git commit -m "feat(backend): add fastapi mvp endpoints"
```

完整规范见 `docs/04-Git规范流程.md`。
