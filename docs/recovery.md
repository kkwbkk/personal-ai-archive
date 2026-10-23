# AI-READONLY: 版本历史与恢复指南

所有进入 GitHub 的变更都有 Git 提交。主分支禁止强制推送和删除，通过 PR 和检查更新。未保存到 Git 的本地编辑不属于 GitHub 历史。

## 网页恢复入口

1. 在 [提交历史](https://github.com/kkwbkk/personal-ai-archive/commits/main/) 找到要恢复的版本，复制完整 40 位提交 SHA。
2. 打开 [Restore archive snapshot](https://github.com/kkwbkk/personal-ai-archive/actions/workflows/restore.yml)，选择 **Run workflow**，填写 SHA 和恢复原因。
3. 工作流从该历史快照建立新提交和恢复 PR，链接出现在运行摘要中。检查通过后合并，主分支恢复为目标快照内容，之前的全部提交仍可追溯。

这是一次触发的恢复入口，仍需选择目标并合并 PR，不是无需确认的破坏性重置。如果 GitHub 要求批准由自动化创建的 PR 检查，在 PR 上批准运行。工作流只接受主线可达历史提交。

## 交给当前 AI 处理

```text
请把 kkwbkk/personal-ai-archive 恢复到主分支历史中的 <完整提交SHA>，
用恢复 PR 保留历史，报告检查结果和 PR 链接。不要 force push。
```

Agent 入口为 `python3 scripts/archive.py restore --commit <完整SHA> --reason '恢复原因'`，使用其现有 `gh` 授权。

如果目标版本改变 `.github/workflows/`，GitHub 可能需要可管理工作流的凭证；只用 Contents 权限的自动化会明确失败，不能绕过权限。由拥有该范围授权的维护者执行同一个恢复动作。

## 边界

回退不会从 Git 历史、Fork 或缓存中抹去已公开的信息。误公开的凭证应先撤销，之后再处理历史清理。删除本地工作副本不影响远端；撤销普通更新应再建立一个恢复 PR。
