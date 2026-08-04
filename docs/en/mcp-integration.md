<!--
Document Title: RPR MCP Integration
Document Type: Public Product Guide
Status: Public Alpha and Unreleased Source Preview
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# MCP integration

Responsibility Pathway Runtime (RPR) can govern outbound Model Context Protocol (MCP) tool calls made by a host application. In the published Public Alpha `0.1.0a2`, RPR acts as a client-side execution and evidence layer in front of an MCP server.

> **Published-release boundary:** PyPI `0.1.0a2` governs calls to an MCP server. It does not expose RPR pathway operations as MCP tools.

## What is implemented in `0.1.0a2`

The published outbound MCP path includes:

- local subprocess launch and stdio transport;
- MCP JSON-RPC session and framing;
- protocol-version, server-identity, server-capability, tool-name, and tool-schema binding;
- admission checks before `tools/call`;
- execution-attempt continuity and retained evidence;
- separation of failures known to occur before dispatch from failures that may have happened after dispatch;
- fail-closed handling of ambiguous tool calls as `write_status_unknown`;
- optional independent readback before a mutating effect is treated as complete;
- restart and reconciliation paths that do not silently repeat an unresolved call.

## Responsibility pathway around an outbound MCP call

```text
host application or agent
  -> proposed MCP tool call
  -> actor, authority, Human Gate, and pathway state
  -> admitted MCP server and tool binding
  -> tools/call over the configured transport
  -> tool result
  -> independent readback when required
  -> completed | write_status_unknown | repair | reconcile | human gate
```

A successful JSON-RPC response is evidence that the MCP server returned a result. It is not, by itself, proof that a consequential external effect was applied correctly. For mutating tools, the integration should provide an independent and authoritative readback source.

## Ambiguous outcomes

RPR distinguishes between:

| Observation | RPR treatment |
|---|---|
| The call was rejected before it could be sent | Failed with `dispatch_state: not_sent` |
| The call may have been sent, but no reliable result exists | `write_status_unknown` |
| A transport error occurs after dispatch cannot be ruled out | `write_status_unknown` |
| The MCP server returns an explicit tool error | Failed with the returned tool result retained |
| A success result is returned but required readback is unavailable | `write_status_unknown` |
| Independent readback verifies the external effect | Succeeded with readback evidence |

An unresolved call must not be retried merely because the client process restarted or the transport timed out.

## Unreleased read-only RPR MCP server preview

The current source tree contains a Phase 1 read-only stdio MCP server for inspecting an existing RPR SQLite pathway store. This source preview is **not included in the published PyPI `0.1.0a2` package** and has not yet been promoted as a new package release.

Start it from an editable source installation:

```bash
python -m pip install -e .
rpr-mcp --database ./rpr.sqlite3
```

The preview exposes only:

- `rpr.get_status`
- `rpr.list_pathways`
- `rpr.get_pathway`
- `rpr.get_evidence`
- `rpr.list_unresolved`

The server opens the existing SQLite file with `mode=ro`. It has no MCP tool for approval, execution, transition, reconciliation, repair, or resume. Status output does not disclose the database filesystem path.

Example local MCP client configuration:

```json
{
  "command": "rpr-mcp",
  "args": ["--database", "/absolute/path/to/rpr.sqlite3"]
}
```

> **Trust boundary:** Read-only does not mean non-sensitive. Pathway definitions and retained evidence may contain operational information. Run the preview only for a trusted local MCP client under operating-system permissions that already allow reading the database. It is not an authentication, authorization, tenant-isolation, or redaction gateway.

## Verified and unverified scope

The published public-alpha verification includes local outbound MCP subprocess and stdio paths, fault injection, restart continuity, and duplicate-dispatch prevention in the tested environment.

The read-only server preview adds tests for:

- read-only SQLite opening and rejection of write statements;
- MCP initialization, `tools/list`, and `tools/call`;
- empty, listed, individual, evidence, and unresolved-pathway results;
- malformed JSON-RPC and invalid arguments;
- structured tool errors and missing pathway IDs;
- stdout containing JSON-RPC messages only;
- rejection of missing and non-RPR databases.

The following still require environment-specific evaluation:

- remote MCP transports and hosted MCP services;
- enterprise proxy, TLS, identity, and credential arrangements;
- service-specific tool semantics and authoritative readback sources;
- Windows, macOS, containers, and Python environments outside the tested profile;
- production authentication, authorization, tenant isolation, bypass prevention, monitoring, incident ownership, and deployment suitability.

## Integration responsibilities

RPR does not discover that an arbitrary MCP server or client is trustworthy. The integrating application and operator remain responsible for:

- selecting and authenticating MCP peers;
- protecting credentials, database files, and environment variables;
- restricting process, network, filesystem, and tool permissions;
- deciding which outbound tools require Human Gate;
- supplying authoritative independent readback for consequential effects;
- defining repair, reconciliation, resume, and residual ownership;
- preventing alternate execution paths that bypass RPR;
- preventing untrusted MCP clients from reading pathway and evidence data.

## Still not implemented

The source preview does not expose mutating RPR operations. Tools such as `rpr.request_human_gate`, `rpr.approve`, `rpr.execute`, `rpr.reconcile`, or `rpr.resume` remain future design candidates, not current capabilities.

See also:

- [Product scope and architecture](product-scope-architecture.md)
- [Security, integration, and API boundary](security-integration-api.md)
- [Verification, release notes, known issues, and UAT](verification-release-uat.md)
