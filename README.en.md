# Hermes × Classic QQ: Plain-text Compatibility Guide

[简体中文](README.md) · [Issues](https://github.com/miaomiao-tools/qq-legacy-hermes-compat/issues)

Can you read Hermes replies on your phone, while classic desktop QQ only shows an unsupported-message notice? This guide records a tested workaround: send ordinary text messages from Hermes.

This is an **unofficial guide**, developed through vibe coding and checked through code review, automated tests, and observations in the real client. It is not endorsed by Tencent or Nous Research. **No Windows installer is required.** This project does not distribute a QQ client, login tool, or modified executable.

## Start with one setting

Merge this setting into the existing QQ adapter's `extra` section in your current Hermes configuration:

```yaml
platforms:
  qqbot:
    extra:
      markdown_support: false
```

Change only `markdown_support`; **do not replace your entire configuration with this example**. Wait for active tasks to finish, then shut down and restart the Hermes instance responsible for the QQ connection. Once it reconnects, ask a normal question from classic QQ and inspect the new reply.

This makes the adapter send plain text and strip some Markdown formatting. It also affects text sent through that adapter to other devices. It cannot recover the bodies of old unsupported messages.

A reply containing no Markdown syntax can still be sent as a Markdown message. Changing the wording is not the same as changing the message type.

## What was verified

Date: 2026-10-04. Client: **Windows classic QQ 9.7.23.29368**. Transport: official QQ Bot C2C messaging. Hermes baseline: **v2026.9.24 / 0.21.5**, source HEAD `f97608f178d1ffeca59860195ab7da295f7c8e5f`.

**The real-client tests used a Hermes installation that already contained other local modifications.** We separately checked that the optional patch below applies and rolls back against the specified upstream file. That does not amount to repeating every live test on an otherwise unmodified upstream installation.

| Evidence | Result | Scope |
| --- | --- | --- |
| Identical short text sent 15 seconds apart | `msg_type=0` displayed; `msg_type=2` displayed the unsupported notice | Plain-text/Markdown comparison in this client |
| Normal conversations after configuring and restarting | Greetings, a reply after a tool call, and follow-up replies were readable | The normal message flow, not just direct API calls |
| Optional C2C no-quote change | 58 relevant checks passed | 54 existing tests and 4 new parameter combinations in an isolated test environment |
| After loading the no-quote change | Two new replies were readable without gray quote cards; one contained a visible web link | Two real UI observations; the link's content was not evaluated |
| Input notification | A separate five-second test was accepted by the API; the typing indicator was later seen during normal interaction | Not a guarantee for every notification type |

API acceptance and visible delivery were checked separately. User chat bodies, screenshots, and account identifiers are not published.

## Optional: remove automatic quote cards in private replies

The tested version sometimes adds `message_reference` to plain-text replies, producing a gray quote card. That field is not necessary for displaying ordinary text.

[c2c-no-quote.patch](c2c-no-quote.patch) adds three lines to remove `message_reference` only on the C2C send path. It preserves the reply-correlation fields `msg_id` and `msg_seq`, the message body, and existing group-chat behavior. **This is a separate source modification; setting `markdown_support: false` does not apply it.**

The patch targets `gateway/platforms/qqbot/adapter.py` at the exact upstream commit above. In an isolated directory, it passed the forward check, actual application, reverse check, and actual reversal; the restored bytes matched the original file. Its three added lines are identical to the live-tested modification. Only line endings and upstream line positions were standardized for distribution.

Back up your current source and inspect existing local changes. From the matching Hermes source root, replace the example patch location and run:

```sh
git -c core.autocrlf=false apply --check /path/to/c2c-no-quote.patch
git -c core.autocrlf=false apply /path/to/c2c-no-quote.patch
```

The Git setting applies only to that command and prevents newline conversion from interfering with verification. If the check fails, stop and review the version and diff; do not force it or replace a modified source file with an old copy. Run the checks below, reload Hermes normally, and inspect a new reply. Existing quote cards in historical messages will remain.

### Reproducible regression check

[regression_test.py](regression_test.py) contains the new sanitized test. It exercises the real QQAdapter send path through a mock HTTP transport, without contacting QQ or invoking a model. It checks that:

- C2C plain text preserves its body, `msg_id`, and `msg_seq`, without `message_reference`.
- Markdown retains its existing body format.
- Group-chat plain text retains its existing reference field.

Use the stated Hermes source and its configured development test environment, including pytest, pytest-asyncio, httpx, and the adapter's runtime dependencies. Place the file at `tests/gateway/test_qqbot_plain_reply_reference.py` in that source tree. If the destination already exists, review and merge instead of overwriting it. Run the project's test entry point from its root:

```sh
bash scripts/run_tests.sh tests/gateway/test_qqbot_plain_reply_reference.py tests/gateway/test_qqbot.py --file-retries 0
```

The recorded 58 passing checks refer to the tested local environment; other revisions may have different counts. Passing tests does not replace checking the actual classic QQ window.

## Rollback

- Configuration: remove the added setting if it was previously absent, or restore its recorded previous value.
- Optional source patch: first run `git -c core.autocrlf=false apply --check -R /path/to/c2c-no-quote.patch`, then remove `--check` from that command to reverse the patch.
- Wait for active tasks to finish, then restart the relevant Hermes instance normally.

Preserve later configuration and source edits; do not overwrite whole files with historical copies.

## Limits

Only one classic QQ version and C2C text were tested. Images, files, buttons, approval cards, long messages, group chats, and long-term reliability are outside this acceptance scope. Readable plain text does not mean full Markdown support. We have not established whether the unsupported notice originates on the server or in an earlier client compatibility layer; the workaround does not depend on that hypothesis.

## Sources and licensing

- [Tencent message API documentation](https://github.com/tencent-connect/bot-docs/blob/main/docs/develop/api-v2/server-inter/message/send-receive/send.md)
- [Hermes adapter at the tested baseline](https://github.com/NousResearch/hermes-agent/blob/f97608f178d1ffeca59860195ab7da295f7c8e5f/gateway/platforms/qqbot/adapter.py)
- Similar reports: [Tencent openclaw-qqbot #74](https://github.com/tencent-connect/openclaw-qqbot/issues/74) and [openclaw-china #126](https://github.com/BytePioneer-AI/openclaw-china/issues/126). Those discussions do not validate this project's changes.

The new guide, regression test, and three-line modification are licensed under [MIT](LICENSE), credited to **miaomiao tools**. The exact upstream MIT license and Nous Research copyright notice are preserved in [LICENSE.Hermes](LICENSE.Hermes); provenance is recorded in [NOTICE](NOTICE).

No QQ binaries, credentials, real configuration, chat records, or process-memory materials are included.
