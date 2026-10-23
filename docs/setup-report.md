# AI-READONLY: 仓库搭建与验收报告

日期：2026-10-23（Asia/Shanghai）。本报告记录技术初始化验收；后续本人确认的档案填写见 [档案更新说明](profile-update-2026-10-23.md)。

## 交付结果

公开仓库：[kkwbkk/personal-ai-archive](https://github.com/kkwbkk/personal-ai-archive)。已提供五个核心目录、12 份 Markdown 模板、AI 操作规则、跨平台接入指南、只读 OpenAPI、更新工具及历史恢复入口。初始化时仅发布空白模板，未迁移资料原件或聊天记录；后续档案摘要经本人明确确认并授权发布。

| 目录 | 使用方法 |
| --- | --- |
| `identity/` | 填写身份、职业、核心标签、目标和原则；本人明确指示后修改。 |
| `workflow/` | 填写工作节奏、沟通习惯、工具和任务优先级；允许受控追加。 |
| `memory/` | 追加经验、重要决策和长期偏好，保留日期、来源、状态与冲突。 |
| `skills/` | 记录已有技能的证据、能力差距和学习计划。 |
| `archive/` | 索引已完成项目和旧文档，按模板建立经授权的历史归档。 |

所有模板均为 UTF-8 Markdown，首行有 `AI-READONLY` 或 `AI-WRITABLE` 标签，预留 `{{...}}` 字段。标签为协作约定；真正访问控制依赖 GitHub。

## 已观察到的验证结果

| 检查 | 结果与证据 |
| --- | --- |
| 仓库创建与公开访问 | 已由 GitHub API 确认仓库所有者和 public 状态。无凭据读取成功，固定提交导出 12 份模板。 |
| 更新提案、提交及合并 | [验收 PR #1](https://github.com/kkwbkk/personal-ai-archive/pull/1) 已合并；使用明确标记为非个人记忆的合成样本。 |
| 还原入口实际执行 | [恢复工作流](https://github.com/kkwbkk/personal-ai-archive/actions/runs/39887866818) 成功创建 [恢复 PR #2](https://github.com/kkwbkk/personal-ai-archive/pull/2)。GitHub 要求批准机器人 PR 的检查，已通过现有维护权限完成。 |
| 恢复后内容一致 | PR #2 已合并。目标与恢复结果的完整 Git tree 均为 `2d2eeb3865eef420708e3a7df8f07ef4cf7f2f37`；验收条目已从当前档案移除，历史仍保留。 |
| 分支保护 | 服务端确认：管理员同样受约束；要求 PR、GitHub Actions 的 `archive-check` 成功且分支为最新；禁止强制推送及删除主分支；要求线性历史和讨论解决。 |
| 拦截未通过检查的主线更新 | 实际尝试直接更新 main，GitHub 返回 HTTP 422：必需检查尚未通过。未绕过保护。 |
| 工具与结构检查 | 本地 24 项测试通过；覆盖路径越界、只读拒绝、重复条目、固定快照、恢复过期和文件树不匹配等。线上结果见 [Archive validation](https://github.com/kkwbkk/personal-ai-archive/actions/workflows/validate.yml)。 |
| 运行环境兼容 | 已核实并固定支持 Node.js 24 的 checkout v7.0.1，运行系统固定 Ubuntu 24.04；更新后的 [线上运行](https://github.com/kkwbkk/personal-ai-archive/actions/runs/39887666093) 成功。 |

早期失败运行保留在 Actions 历史中：新增只读保护后，一条旧测试样本未同步更新，已修正并添加拒绝只读写入的测试。该失败不表示个人资料丢失。后续状态以最新提交的检查为准。

## AI 接入快速指南

1. 有 GitHub 工具：向 AI 提供仓库地址并复制 [README 的启动提示](../README.md)。让其报告实际读取的提交 SHA 和文件。
2. 没有 GitHub 工具：让已接入的 Agent 用 `scripts/archive.py export` 导出上下文包，再交给目标 AI。快照不会自行刷新。
3. 需要写回：在宿主中连接 GitHub 并授予本仓库所需的 Contents、Pull requests 权限；任务结束调用 `propose`，返回真实 PR 地址。合并前为待接受提案，默认不会影响其他 AI 读取的 main。
4. 查看平台的具体入口和限制：[ai-integration.md](../ai-integration.md)。ChatGPT、Gemini、Claude、dots、Muse 的接入能力已用官方文档核实，但没有代你登录这些账号或逐一开启连接。

## 完成边界

- 仓库侧搭建和更新、恢复链路已执行验收。各 AI 账号的首次连接、实际工具动作和持续回调尚未逐一启用或测试；公开仓库不能自行监听其他平台的对话。
- 初始化时保留空白模板，后续已按本人确认填写必要摘要。占位符不是个人事实；技术样本没有当作本人偏好。真实偏好准确度和跨 AI 协作价值，需在你允许公开的真实小样本上判断，尚未完成用户价值验收。
- 自动写回需要宿主执行工具，默认建立 PR，不自动合并。单人仓库设为零必需批准人数，避免唯一所有者无法自审；这不是独立人工审计。合并可由你已授权的维护 Agent 在检查通过后完成。
- 常见凭证模式检测不是完整隐私检测。公开内容及其历史可被复制，Git 恢复不能撤回别人已有的副本。
- 网页恢复是一键触发“生成恢复提案”，仍需指定目标、通过检查并合并；恢复工作流改动或早期初始化中间版本可能需要额外的工作流管理权限。详见 [恢复指南](recovery.md)。

## 回滚与所有权

主档案和领域含义由仓库所有者控制。修改有提交和 PR 可查；恢复通过新提交保留历史，不使用强制推送。建议以 `v1.0.0` 为初始化完成后的恢复基线。移除 AI 宿主的 GitHub 授权可停止其后续访问，保留本仓库 Markdown 即可迁移到其他 Git 服务或本地文件。
