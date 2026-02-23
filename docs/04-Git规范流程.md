# Git 规范流程（标准化）

## 1. 分支模型
- `main`：稳定可发布
- `develop`：日常集成
- `feature/*`：功能开发分支
- `fix/*`：缺陷修复分支

## 2. 开发流程
1. 从 `develop` 拉取最新代码
2. 创建功能分支：`feature/<模块>-<简述>`
3. 小步提交，保证每次 commit 可解释、可回滚
4. 推送并发起 PR 到 `develop`
5. 通过评审与基础验证后合并
6. 版本发布时从 `develop` 合并到 `main`

## 3. Commit 规范（Conventional Commits）
格式：`<type>(<scope>): <subject>`

常用 type：
- `feat`：新功能
- `fix`：修复
- `docs`：文档
- `refactor`：重构
- `test`：测试
- `chore`：构建/依赖/工具

示例：
- `feat(frontend): add bottom tab navigation`
- `feat(backend): implement todo and stats api`
- `docs(requirements): add mvp scope and acceptance criteria`

## 4. PR 规范
- 标题清晰，关联功能点
- 描述包含：变更内容、验证方式、影响范围
- 至少 1 名评审通过后合并

## 5. 标签与发布建议
- 版本号建议：`v0.1.0`（MVP 初版）
- 发布前检查：文档、构建、基本手工验证
