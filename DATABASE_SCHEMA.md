# 数据库设计文档

## 数据库：微信云开发 / MongoDB

---

## 集合 (Collections)

### 1. `users` - 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `openid` | String | 微信 openid（唯一） |
| `nickName` | String | 昵称 |
| `avatarUrl` | String | 头像 URL |
| `gender` | Number | 性别：0 保密 1 男 2 女 |
| `phone` | String | 手机号（加密存储） |
| `city` | String | 城市 |
| `district` | String | 区域 |
| `level` | String | 等级：P1~P6 |
| `levelVerified` | Boolean | 是否已完成等级认证 |
| `creditScore` | Number | 信用分（0~100，初始 80） |
| `gamesPlayed` | Number | 参与总场次 |
| `bio` | String | 个人简介 |
| `createdAt` | Date | 注册时间 |
| `updatedAt` | Date | 更新时间 |

**索引**：`openid`（唯一），`city + level`（复合）

---

### 2. `skill_videos` - 认证视频表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `userId` | String | 关联 users._id |
| `videoUrl` | String | 云存储视频 URL |
| `coverUrl` | String | 封面图 URL |
| `duration` | Number | 视频时长（秒） |
| `selfRatedLevel` | String | 自评等级 P1~P6 |
| `assignedLevel` | String | 审核分配等级 P1~P6 |
| `status` | String | pending / approved / rejected |
| `reviewNote` | String | 审核备注 |
| `submittedAt` | Date | 提交时间 |
| `reviewedAt` | Date | 审核时间 |
| `reviewerId` | String | 审核员 ID |

---

### 3. `games` - 球局表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `creatorId` | String | 发起人 users._id |
| `title` | String | 球局标题 |
| `description` | String | 球局说明 |
| `venue` | String | 场地名称 |
| `address` | String | 详细地址 |
| `city` | String | 城市 |
| `district` | String | 区域 |
| `date` | String | 日期 YYYY-MM-DD |
| `startTime` | String | 开始时间 HH:mm |
| `endTime` | String | 结束时间 HH:mm |
| `maxPlayers` | Number | 最大人数 |
| `currentPlayers` | Number | 当前人数 |
| `minLevel` | String | 最低水平要求 P1~P6 |
| `maxLevel` | String | 最高水平要求 P1~P6 |
| `fee` | Number | 每人费用（元） |
| `status` | String | OPEN / FULL / CANCELLED / COMPLETED |
| `createdAt` | Date | 创建时间 |

**索引**：`city + date`（复合），`status`，`creatorId`

---

### 4. `game_participants` - 球局参与者表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `gameId` | String | 关联 games._id |
| `userId` | String | 关联 users._id |
| `status` | String | PENDING / APPROVED / REJECTED / CANCELLED |
| `joinedAt` | Date | 申请时间 |
| `updatedAt` | Date | 状态更新时间 |

**索引**：`gameId + userId`（复合唯一），`userId + status`

---

### 5. `reviews` - 评价表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `gameId` | String | 关联 games._id |
| `reviewerId` | String | 评价者 users._id |
| `revieweeId` | String | 被评价者 users._id |
| `rating` | Number | 1~5 星 |
| `tags` | Array | 评价标签列表 |
| `comment` | String | 文字评价 |
| `isPunctual` | Boolean | 是否准时 |
| `createdAt` | Date | 评价时间 |

**索引**：`revieweeId`，`gameId + reviewerId + revieweeId`（复合唯一，防重复评价）

---

### 6. `credit_logs` - 信用日志表

| 字段 | 类型 | 说明 |
|------|------|------|
| `_id` | String | 自动生成 |
| `userId` | String | 关联 users._id |
| `change` | Number | 信用分变化量（正/负） |
| `reason` | String | 变化原因 |
| `gameId` | String | 关联 games._id（可选） |
| `newScore` | Number | 变化后的信用分 |
| `createdAt` | Date | 记录时间 |

**索引**：`userId + createdAt`（复合）

---

## 信用分计算规则

| 事件 | 变化量 | 备注 |
|------|--------|------|
| 准时到场 | +2 | 对方评价 isPunctual=true |
| 连续3次准时 | +5 | 系统自动触发 |
| 迟到15分钟以上 | -5 | 对方评价 isPunctual=false |
| 开局前2小时内取消 | -10 | 取消操作时自动扣除 |
| 确认后未到场 | -20 | 球局结束后系统检测 |
| 无故失联 | -25 | 发起人举报 |
| 获得好评（4-5星） | +2 | 双向评价时 |
| 获得差评（1-2星） | -3 | 双向评价时 |

信用分范围：0~100，初始值：80
