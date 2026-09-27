#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 item B + item D4: repair `tools/tool_channels.json`.

  B  `os_deploy_to_android_device` moves off `payload` (verb `deploy` is an action
     verb: `read_payload` only counts read-verb tools, so its evidence gate could
     never be satisfied - TASK-119 D1) onto `file_effect`, which is what a deploy
     actually produces (an exported/installed artifact).
  B  `editor_capture_screenshot` moves onto `payload`: `capture` is a READ_VERBS
     member and the contract allows the base64 answer *or* a file, and 10 of its
     25 calls never wrote a file - judging it on `file_effect` would score legal
     successes as evidence-free (TASK-119 D5).
  D4 the top level now says out loud that `basis` is a CHANNEL-LEVEL template
     (22/28/51/76 tools share one sentence per channel; only `subject` differs),
     so a reviewer cannot mistake it for a per-tool argument.

Idempotent. Run:  python recovery/work/task120/fix_channels.py
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PATH = os.path.join(ROOT, "tools", "tool_channels.json")

DEPLOY_SUBJECT = "导出产物：部署写出的 APK / 推到设备上的产物（本机只能测到它的拒绝分支）"
DEPLOY_BASIS = (
    "file_effect：deploy 是**动作动词**，不是读类动词，所以它的回包不是测量结果——"
    "`read_payload` 只对 READ_VERBS 里的动词累加，把它声明成 `payload` 会让这条工具的通道证据"
    "**恒为 0**（TASK-119 D1：无论真机接上、部署成功多少次都不会变）。它真正可观测的产物是部署"
    "写出的文件（导出的 APK）。声明依据是契约描述「将项目导出并部署到 Android 设备」。"
    "本机没有 Android 预设、没有设备，所以这条通道上目前只有拒绝分支（-32001 / -32602），"
    "台账如实记为 `计数达标缺证据`。"
)
SHOT_SUBJECT = "截图帧：回包里的 base64 PNG（或落盘的那张 PNG）"
SHOT_BASIS = (
    "payload：`capture` 属于 READ_VERBS（TASK-111 的规则），而契约写的是「返回 base64 PNG **或**"
    "保存到文件」——两条都是合法成功路径。25 次调用里只有 15 次留下文件效果，把 `file_effect` 当"
    "权威通道会把 10 次合法的内联成功判成「没有证据」（TASK-119 D5）。所以权威通道是回包载荷本身："
    "`ok=true` 且回包是实质载荷（回包即测量结果）。落盘的那几次另有 `file_effect` 记录，可作旁证。"
)
BASIS_SCOPE_NOTE = (
    "每条 `basis` 是**通道级模板**：同一通道的 22/28/51/76 条逐字相同，只有 `subject` 逐条不同。"
    "它说明的是「为什么这条通道配这类工具」，不是逐工具的推理记录；逐工具的推理在 `subject`、"
    "该工具的会话/manifest，以及台账 §0.1 的见证表里（TASK-119 D6）。"
)


def main():
    raw = io.open(PATH, encoding="utf-8").read()
    doc = json.loads(raw)
    entries = doc["channels"]
    deploy = entries["os_deploy_to_android_device"]
    shot = entries["editor_capture_screenshot"]
    changed = []
    if deploy.get("channel") != "file_effect":
        deploy["channel"] = "file_effect"
        changed.append("os_deploy_to_android_device.channel")
    if deploy.get("subject") != DEPLOY_SUBJECT:
        deploy["subject"] = DEPLOY_SUBJECT
        changed.append("os_deploy_to_android_device.subject")
    if deploy.get("basis") != DEPLOY_BASIS:
        deploy["basis"] = DEPLOY_BASIS
        changed.append("os_deploy_to_android_device.basis")
    if shot.get("channel") != "payload":
        shot["channel"] = "payload"
        changed.append("editor_capture_screenshot.channel")
    if shot.get("subject") != SHOT_SUBJECT:
        shot["subject"] = SHOT_SUBJECT
        changed.append("editor_capture_screenshot.subject")
    if shot.get("basis") != SHOT_BASIS:
        shot["basis"] = SHOT_BASIS
        changed.append("editor_capture_screenshot.basis")
    if doc.get("basis_scope") != "channel_template":
        doc["basis_scope"] = "channel_template"
        changed.append("basis_scope")
    if doc.get("basis_scope_note") != BASIS_SCOPE_NOTE:
        doc["basis_scope_note"] = BASIS_SCOPE_NOTE
        changed.append("basis_scope_note")
    counts = {}
    for entry in entries.values():
        counts[entry["channel"]] = counts.get(entry["channel"], 0) + 1
    if doc.get("channel_counts") != counts:
        doc["channel_counts"] = counts
        changed.append("channel_counts")
    if not changed:
        print("unchanged")
        return
    # keep the declared order of top-level keys, inserting the two new fields after _channels
    out = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(out)
    print("changed: %s" % ", ".join(changed))
    print("channel_counts: %s" % json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
