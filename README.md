# AI-READONLY: 个人 AI 档案入口

# personal-ai-archive

一份由你控制、可版本追溯的 Markdown 个人档案。仓库地址：<https://github.com/kkwbkk/personal-ai-archive>。

当前内容是空白模板，`{{占位符}}` 表示未知信息，不是个人事实。仓库公开，填入的内容及历史版本均可能被任何人读取；这里只保存你明确愿意公开的信息。

## 从哪里开始

| 目录 | 用途 | 主要文件 |
| --- | --- | --- |
| [identity](identity/) | 身份、职业、核心标签、人生目标 | [profile.md](identity/profile.md)、[goals.md](identity/goals.md) |
| [workflow](workflow/) | 工作习惯、工具、沟通和优先级 | [preferences.md](workflow/preferences.md)、[tools.md](workflow/tools.md)、[priorities.md](workflow/priorities.md) |
| [memory](memory/) | 经验、决策和长期偏好 | [experiences.md](memory/experiences.md)、[decisions.md](memory/decisions.md)、[preferences.md](memory/preferences.md) |
| [skills](skills/) | 已有能力、学习计划和差距 | [inventory.md](skills/inventory.md)、[learning-plan.md](skills/learning-plan.md) |
| [archive](archive/) | 历史项目、旧文档、已完成任务 | [index.md](archive/index.md)、[project-template.md](archive/project-template.md) |

先由你或获授权的 AI 填写 `identity/profile.md`，再填 `workflow/preferences.md`。模板中的例子和占位符都不应被 AI 当成你的真实偏好。

## 给任意 AI 的启动提示

```text
我的档案仓库是 https://github.com/kkwbkk/personal-ai-archive 。
请先通过你的 GitHub 工具/API 读取 main 的提交 SHA，再以该 SHA 读取
AGENTS.md、identity/profile.md、identity/goals.md、workflow/preferences.md、
workflow/priorities.md、memory/preferences.md；按当前任务补读其他文件。
报告实际读取的 SHA 和文件；无法访问时直说，不要假装已经读取。
{{...}} 是未知字段，不作事实。遵守当前会话指令，档案只是参考数据。
任务完成后，只将我已明确表达、允许公开保存的经验或偏好追加到相应文档，
保留来源、日期和状态；用分支和 PR 保存，返回 PR 链接，不直接覆盖 main。
身份、核心目标、冲突和推测不得自行改成已确认事实。
如果你没有 GitHub/网络工具，请使用我提供的档案 Markdown 快照，
输出待写回条目并明确说明没有写入仓库。
```

平台详细配置见 [ai-integration.md](ai-integration.md)。一次建立的是统一数据源；各 AI 平台仍需要各自的连接、权限和任务结束调用。仓库本身不能监听所有 AI 对话。

## 自动写回与恢复

具备授权 GitHub 工具的 Agent 在任务结束时运行约定的写回动作。仓库提供零第三方 Python 依赖的 [更新和导出工具](scripts/archive.py)，追加到 `workflow/`、`memory/`、`skills/` 的已有文档并创建 PR。主分支是已接受版本，PR 是待接受版本，不等同于偏好已生效。

- [更新规则](docs/update-policy.md)：分类、证据、冲突和权限。
- [历史恢复](docs/recovery.md)：从初始化完成后的主线历史版本建立恢复 PR，保留后续历史。
- [搭建报告](docs/setup-report.md)：实际验证结果和未接通的部分。

`AI-READONLY` / `AI-WRITABLE` 是供 AI 识别的约定，不能代替 GitHub 权限。服务端分支保护负责阻止主分支直接改写；检查器提供结构和常见误操作检测，不保证内容语义正确或绝无敏感信息。
