# Hermes × 经典 QQ：文字消息兼容指南

[English](README.en.md) · [问题反馈](https://github.com/miaomiao-tools/qq-legacy-hermes-compat/issues)

手机能看见 Hermes 回复，经典电脑版 QQ 却只显示“不支持”？这里记录一个经过实际验证的办法：让 Hermes 用普通文本消息发送回复。

这是通过 vibe coding 整理、再经代码检查和真实窗口验证的**非官方兼容指南**，不代表腾讯或 Nous Research。无需下载 Windows 安装程序，不提供 QQ 客户端、登录器或改过的 QQ EXE。

## 先做这一项

将下面一项合并到当前 Hermes 配置已有的 QQ 平台 `extra` 段中：

```yaml
platforms:
  qqbot:
    extra:
      markdown_support: false
```

只改 `markdown_support`，**不要用示例覆盖整个配置文件**。等正在执行的任务结束，再正常退出并重新启动负责 QQ 连接的 Hermes；连接恢复后，在旧 QQ 发一个普通问题，检查新回复。

这个选项会让该适配器发送普通文本，并移除部分 Markdown 排版。同一适配器发往其他设备的文字格式也会受影响。它不补回历史“不支持”消息的正文。

回复即使没有 Markdown 符号，也可能仍通过 Markdown 消息类型发送。改变文字内容，并不等于改变发送类型。

## 验证到哪一步

日期：2026-10-04。客户端为 **Windows 经典 QQ 9.7.23.29368**，通道为官方 QQ 机器人单聊（C2C）。Hermes 基线为 **v2026.9.24 / 0.21.5**，源 HEAD 为 `f97608f178d1ffeca59860195ab7da295f7c8e5f`。

**真实客户端测试是在已有其他本地改动的 Hermes 运行环境中完成的。** 我们另外检查了可选补丁对该上游提交的匹配与回滚；这不等于在未经修改的官方安装上重做了全部实机测试。

| 证据 | 结果 | 证明范围 |
| --- | --- | --- |
| 同一句短文本，间隔 15 秒分别发送 | `msg_type=0` 正常显示；`msg_type=2` 显示“不支持” | 本次客户端的普通文本与 Markdown 对照 |
| 应用配置、重新加载后的日常对话 | 问候、工具调用后回复及连续追问均可阅读 | 正常消息流程，不只是直接 API 测试 |
| 额外的私聊无引用修正 | 58 项相关检查通过 | 54 项已有测试及 4 个新增参数组合，使用隔离测试环境 |
| 无引用修正重新加载后 | 两条新回复正文可见、没有灰色引用框，其中一条含可见网页链接 | 两次真实窗口观察；没有据此验证链接内容 |
| 输入提示 | 单独的 5 秒测试被接口接受；后来正常交互中实际看到“对方正在输入” | 不等于所有提示类型均兼容 |

接口返回成功与客户端能看见是两件事，以上分别核对。未公开用户聊天正文、截图或账号信息。

## 可选：不自动带灰色引用框

受测版本的普通文本回复有时会添加 `message_reference`，导致灰色引用卡片。这个字段不是显示普通文本的必要条件。

[c2c-no-quote.patch](c2c-no-quote.patch) 只增加三行：在 C2C 发送路径移除 `message_reference`，保留被动回复所需的 `msg_id`、`msg_seq` 和正文，群聊发送行为不变。**它是额外源码修正，设置 `markdown_support: false` 不会自动应用它。**

补丁固定针对上述上游提交的 `gateway/platforms/qqbot/adapter.py`。公开补丁已在隔离目录中完成匹配检查、实际应用、反向检查及实际撤销；恢复后与原文件字节一致。新增三行与实机使用的修改完全相同，公开版只规范了换行和上游行号。

应用前备份自己的当前源码，检查已有本地修改。从匹配的 Hermes 源码根目录运行，替换命令中的补丁文件位置：

```sh
git -c core.autocrlf=false apply --check /path/to/c2c-no-quote.patch
git -c core.autocrlf=false apply /path/to/c2c-no-quote.patch
```

这里的 Git 配置只对单条命令生效，用于避免换行转换干扰检查。如果检查失败，停止并人工核对版本与差异；不要强行应用，不要用旧完整文件覆盖当前源码。完成下面的检查后，正常重新加载 Hermes，再检查新回复。旧消息上的引用框不会被修改。

### 可复核的回归检查

[regression_test.py](regression_test.py) 是本项目新增的脱敏测试，使用真实 QQAdapter 发送路径和模拟 HTTP 传输，不连接真实 QQ 接口，也不调用模型。它检查：

- C2C 普通文本正文可发送，保留 `msg_id` / `msg_seq`，不带 `message_reference`。
- Markdown 正文保持原格式。
- 群聊普通文本的原引用字段保持不变。

需要上述 Hermes 源码及其已配置的开发测试环境，包括 pytest、pytest-asyncio、httpx 和适配器运行依赖。把测试文件放到 Hermes 的 `tests/gateway/test_qqbot_plain_reply_reference.py`；如果该文件已存在，请先核对并合并，不要覆盖。然后从 Hermes 根目录使用项目测试入口：

```sh
bash scripts/run_tests.sh tests/gateway/test_qqbot_plain_reply_reference.py tests/gateway/test_qqbot.py --file-retries 0
```

记录的 58 项通过来自受测的本地环境，其他版本可能有不同测试数量。测试通过不能代替旧 QQ 的实际显示检查。

## 恢复原状

- 配置项：修改前没有它，就删掉本次增加的一行；原来已有它，就恢复自己记录的原值。
- 可选源码补丁：先用 `git -c core.autocrlf=false apply --check -R /path/to/c2c-no-quote.patch` 检查，再用同样命令去掉 `--check` 撤销。
- 等现有任务结束后，正常重新启动相关 Hermes。

恢复时保留后续配置和源码修改，不要覆盖整个历史文件。

## 还没有证明的事

只实测了一个经典 QQ 版本和 C2C 文字。图片、文件、按钮、审批卡片、长文本、群聊和长期稳定性不在本次验收范围内。普通文本可见也不等于旧 QQ 支持完整 Markdown。尚未确定占位提示究竟由服务器还是更早的客户端兼容层生成，本方案不依赖这个推测。

## 来源与许可

- [腾讯发送消息文档](https://github.com/tencent-connect/bot-docs/blob/main/docs/develop/api-v2/server-inter/message/send-receive/send.md)
- [受测基线的 Hermes QQ 适配器](https://github.com/NousResearch/hermes-agent/blob/f97608f178d1ffeca59860195ab7da295f7c8e5f/gateway/platforms/qqbot/adapter.py)
- 同类问题：[腾讯 openclaw-qqbot #74](https://github.com/tencent-connect/openclaw-qqbot/issues/74)、[openclaw-china #126](https://github.com/BytePioneer-AI/openclaw-china/issues/126)。这些讨论没有验证本项目的修正。

本项目自有指南、回归测试和三行修改采用 [MIT 许可证](LICENSE)，署名 **miaomiao tools**。上游 Hermes 的原始 MIT 许可与 Nous Research 版权声明完整保存在 [LICENSE.Hermes](LICENSE.Hermes)，来源见 [NOTICE](NOTICE)。

这里不包含 QQ 二进制文件、凭据、真实配置、聊天记录或进程内存材料。
