# PomodoroTable

一个番茄钟 MVP 项目（Windows 优先），前端使用 Vue 3 + Element Plus，后端使用 FastAPI。
后续会补充 Agent 功能，根据用户习惯（如番茄钟持续时间等）给出 AI 建议。

## 界面预览
- Android 界面：![Android 界面](android.png)
- Windows 界面：![Windows 界面](windows.png)

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

浏览器访问：`http://127.0.0.1:5173`（若端口被占用，Vite 会自动切换并在终端提示）

## 标准 Git 流程（简版）
```bash
git checkout -b feature/<module>-<summary>
# 小步提交
git add .
git commit -m "feat(frontend): add dark mode theme switch"
git commit -m "fix(frontend): stabilize fullscreen focus layout"
git commit -m "docs(readme): refine startup and screenshot sections"
```

完整规范见 `docs/04-Git规范流程.md`。
