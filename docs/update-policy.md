# AI-READONLY: 自动更新和来源规则

## 生效条件

Agent 必须已接入 GitHub，拥有本仓库所需的写入权限，并由宿主在任务结束时调用写回工具。静态 Markdown 不能主动执行同步。默认只追加到 `workflow/`、`memory/`、`skills/` 的已有 Markdown 文件；CLI 不改身份、目标、历史归档或系统配置。

每次任务结束：识别新长期信息 → 检查用户原话与公开保存依据 → 分类和去重 → 追加条目 → 创建分支、提交和 PR → 返回链接。没有新增、存在公开授权疑问或缺少工具时，不写入，报告实际状态。当前任务的搭建授权不等于授权未来上传全部聊天。

## 条目格式

```markdown
## YYYY-MM-DD — 条目标题

- 状态：pending
- 内容：{{最小必要经验或偏好}}
- 类型：{{用户原话或已验证事实或AI推断}}
- 来源：{{允许公开的来源标识和最短必要摘要}}
- 适用范围：{{适用场景}}
- 验证结果：{{观察到的结果或未验证}}
- 冲突：{{引用冲突的旧条目或无}}
- 公开保存依据：{{本次或既有明确授权}}
- 记录者：{{AI名称与任务标识}}
```

`pending` 是提案，`confirmed` 必须有本人明确依据，`superseded` 保留旧记录并指向新规则。占位符和 AI 推断不是个人事实。冲突未解决时并列保留，不覆盖旧结论。

## 分类

| 内容 | 目的文件 |
| --- | --- |
| 沟通和交付习惯 | `workflow/preferences.md` |
| 工具偏好 | `workflow/tools.md` |
| 执行顺序和任务优先级 | `workflow/priorities.md` |
| 成功、失败和经验 | `memory/experiences.md` |
| 本人最终决策 | `memory/decisions.md` |
| 跨任务的长期个人偏好 | `memory/preferences.md` |
| 技能证据和能力差距 | `skills/inventory.md` |
| 学习计划和进度 | `skills/learning-plan.md` |

## 工具示例（给可执行工具的 Agent）

```sh
python3 scripts/archive.py export --output /tmp/personal-ai-context.md
python3 scripts/archive.py propose --path memory/experiences.md --file /tmp/entry.md --title '记录已确认的任务经验'
```

写入工具复用 `gh` 的登录或宿主注入的 `GH_TOKEN`。令牌只保存在宿主的秘密存储，不能写入仓库、提示词或条目。建议专用 GitHub App 或限此仓库的 fine-grained token：Contents read/write、Pull requests read/write、Metadata read；读档无需写权限。CI 配置和分支管理权限留给维护者。

主分支启用 PR 与检查约束。个人仓库不要求另一位审阅者批准，避免唯一所有者无法自审；是否合并由所有者或明确授权的维护工具决定。AI 标签和检测器不能阻止拥有管理权限的人关闭保护，也不能验证所有事实或识别全部隐私内容。
