# API 设计（MVP）

## 1. 通用返回
- 成功：`{ "code": 0, "message": "ok", "data": ... }`
- 失败：`{ "code": 非0, "message": "错误信息", "data": null }`

## 2. 待办
- `GET /api/todos`：获取待办列表
- `POST /api/todos`：新增待办
- `PATCH /api/todos/{todo_id}/toggle`：切换完成状态
- `PUT /api/todos/{todo_id}`：修改待办
- `DELETE /api/todos/{todo_id}`：删除待办

## 3. 未来待办集
- `GET /api/collections`：获取未来待办集列表
- `POST /api/collections`：新增未来待办集
- `PUT /api/collections/{collection_id}`：修改未来待办集
- `DELETE /api/collections/{collection_id}`：删除未来待办集

## 4. 锁机
- `GET /api/focus/status`：获取当前锁机状态
- `POST /api/focus/start`：启动专注会话
- `POST /api/focus/stop`：停止专注会话

## 5. 统计
- `GET /api/stats`：获取统计数据（支持可选参数 `days`，如 `7`、`30`）
- `POST /api/stats/record`：记录一次番茄完成（`duration_minutes`）
- `POST /api/stats/interrupt`：记录一次专注中断（`duration_minutes`）

`GET /api/stats` 的 data 补充字段：
- `completion_trend`：历史完成曲线点（`[{ date, count }]`）
- `completion_times`：历史完成时间列表（ISO 时间字符串）
- `range_days`：当前统计范围（`null` 表示全部）

## 7. 计时行为说明
- 待办可重复执行，已完成待办也可再次发起番茄计时
- 支持倒计时模式和正计时模式
- 提供“提前完成”按钮，点击后立即按完成会话记录统计

## 6. 我的
- `GET /api/me`：获取当前用户信息
