# `tools_list.json` provenance (DR-42, batch one)

| field | value |
|---|---|
| source path (in-repo, read-only nested repo) | `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` |
| source sha256 | `fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df` |
| source bytes | 154272 |
| source shape | a complete JSON-RPC response (`id` / `jsonrpc` / `result.tools[]`) |
| tools in the fixture | **177** |
| fixture shape | the **same** JSON-RPC response envelope (`tools_list.json` has always been a `tools/list` response) |
| fixture serialization | compact, `sort_keys`, UTF-8 **without BOM**, LF, no trailing newline |
| fixture sha256 | `50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0` |
| fixture bytes | 71481 |
| name shape | `^(editor|project|running_game|os)_[a-z0-9_]+$` (177/177) |

The fixture is regenerated from the source with

```python
doc = {"id": 1, "jsonrpc": "2.0", "result": {"tools": tools}}
json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

which is exactly the shape the old fixture had (a compact, key-sorted
`tools/list` response) — so `McpClient::list_tool_schemas`,
`src/tools/index.rs` and every test keep parsing it unchanged. Only the tool
names and their `inputSchema`s are new.

> **Live verification is deferred to batch two.** This batch is offline: the
> fixture is copied from the in-repo contract document, and the live
> `tools/list` reply of the running engine has **not** been compared against it
> byte-for-byte. That comparison (`GET /mcp` tool count == 177, names equal) is
> a batch-two obligation (DR-47).
