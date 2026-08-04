<!--
Document Title: RPR MCP Integration
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# MCP integration

Responsibility Pathway Runtime (RPR) can govern outbound Model Context Protocol (MCP) tool calls made by a host application. In the current Public Alpha, RPR acts as a client-side execution and evidence layer in front of an MCP server.

> **Current boundary:** RPR can govern calls to an MCP server. RPR is not yet distributed as an MCP server that exposes its own pathway operations as MCP tools.

## What is implemented

The current MCP path includes:

- local subprocess launch and stdio transport;
- MCP JSON-RPC session and framing;
- protocol-version, server-identity, server-capability, tool-name, and tool-schema binding;
- admission checks before `tools/call`;
- execution-attempt continuity and retained evidence;
- separation of failures known to occur before dispatch from failures that may have happened after dispatch;
- fail-closed handling of ambiguous tool calls as `write_status_unknown`;
- optional independent readback before a mutating effect is treated as complete;
- restart and reconciliation paths that do not silently repeat an unresolved call.

## Responsibility pathway around an MCP call

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

## Verified and unverified scope

The public-alpha verification includes local MCP subprocess and stdio paths, fault injection, restart continuity, and duplicate-dispatch prevention in the tested environment.

The following require environment-specific evaluation:

- remote MCP transports and hosted MCP services;
- enterprise proxy, TLS, identity, and credential arrangements;
- service-specific tool semantics and authoritative readback sources;
- Windows, macOS, containers, and Python environments outside the final Linux/Python 3.11 rehearsal;
- production bypass prevention, monitoring, incident ownership, and deployment suitability.

## Integration responsibilities

RPR does not discover that an arbitrary MCP server is trustworthy. The integrating application remains responsible for:

- selecting and authenticating the MCP server;
- protecting credentials and environment variables;
- restricting the server process, network, filesystem, and tool permissions;
- deciding which tools require Human Gate;
- supplying authoritative independent readback for consequential effects;
- defining repair, reconciliation, resume, and residual ownership;
- preventing alternate execution paths that bypass RPR.

## Not yet implemented

The current release does not expose RPR itself as an MCP server. Tools such as `rpr.get_pathway`, `rpr.request_human_gate`, or `rpr.reconcile` are a possible future interface, not a capability of `0.1.0a2`.

See also:

- [Product scope and architecture](product-scope-architecture.md)
- [Security, integration, and API boundary](security-integration-api.md)
- [Verification, release notes, known issues, and UAT](verification-release-uat.md)
