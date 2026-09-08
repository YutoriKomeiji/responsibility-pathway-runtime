<!--
Document Title: RPR MCP Integration
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# MCP integration

Responsibility Pathway Runtime (RPR) can govern outbound Model Context Protocol (MCP) tool calls made by a host application. Published Public Alpha `0.1.0a6` includes a local read-only `rpr-mcp` inspection server and read-only Responsibility Routing visibility.

> **Published-release boundary:** PyPI `0.1.0a6` governs outbound MCP calls and includes the local read-only RPR MCP inspection server plus `rpr.get_route_visibility`. It does not include any mutating RPR MCP tool.

## What is implemented in published `0.1.0a6`

The published outbound MCP path includes:

- local subprocess launch and stdio transport;
- MCP JSON-RPC session and framing;
- protocol-version, server-identity, server-capability, tool-name, and tool-schema binding;
- admission checks before `tools/call`;
- execution-attempt continuity and retained evidence;
- separation of failures known to occur before dispatch from failures that may have happened after dispatch;
- fail-closed handling of ambiguous tool calls as `write_status_unknown`;
- optional independent readback before a mutating effect is treated as complete;
- restart and reconciliation paths that do not silently repeat an unresolved call;
- read-only Responsibility Routing visibility with `authority_inferred: false`.

Published `rpr-mcp` exposes only:

- `rpr.get_status`
- `rpr.list_pathways`
- `rpr.get_pathway`
- `rpr.get_route_visibility`
- `rpr.get_evidence`
- `rpr.list_unresolved`

## Responsibility pathway around an outbound MCP call

```text
host application or agent
  -> proposed MCP tool call
  -> actor, declared Authority, pathway state, and Responsibility Routing
  -> admitted MCP server and tool binding
  -> tools/call over the configured transport
  -> tool result
  -> independent readback when required
  -> completed | write_status_unknown | repair | reconcile | bounded human gate | hold
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

An unresolved call must not be retried merely because the client process restarted or the transport timed out. It also must not be converted automatically into Human Gate merely because the outcome is uncertain. Responsibility Routing may preserve the unresolved effect under a reconciliation hold or another explicitly eligible and authorized route.

## Responsibility Routing visibility

Published `0.1.0a6` includes the read-only tool:

- `rpr.get_route_visibility`

`rpr.get_route_visibility(pathway_id)` exposes current state, narrow compatibility route classification, a persisted declared route when present, the Human Return point, Residual Owner, and an explicit `authority_inferred: false` marker.

The tool does not select a receiver, grant Authority, approve work, execute work, reconcile effects, resume execution, or mutate pathway state. Receiver capability, evidence transfer, successful transport, and route selection do not create Authority.

## Running the read-only server

```bash
python -m pip install responsibility-pathway-runtime==0.1.0a6
rpr-mcp --database ./rpr.sqlite3
```

For unreleased repository source:

```bash
python -m pip install -e .
rpr-mcp --database ./rpr.sqlite3
```

The server opens the existing SQLite file with `mode=ro`. It has no MCP tool for approval, execution, transition, reconciliation, repair, resume, or Authority grant. Status output does not disclose the database filesystem path.

Example local MCP client configuration:

```json
{
  "command": "rpr-mcp",
  "args": ["--database", "/absolute/path/to/rpr.sqlite3"]
}
```

> **Trust boundary:** Read-only does not mean non-sensitive. Pathway definitions, route metadata, and retained evidence may contain operational information. Run the server only for a trusted local MCP client under operating-system permissions that already allow reading the database. It is not an authentication, authorization, tenant-isolation, or redaction gateway.

## Verified and unverified scope

Published public-alpha verification includes local outbound MCP subprocess and stdio paths, read-only MCP inspection, Responsibility Routing visibility, fault injection, restart continuity, and duplicate-dispatch prevention in the tested environment.

The route-visibility evidence includes tests for:

- Responsibility Routing inspection without state mutation;
- persisted declared route readback;
- narrow state-to-route compatibility mapping;
- `authority_inferred: false`;
- invalid receiver and Authority non-propagation behavior;
- malformed requests and missing pathway IDs.

The following still require environment-specific evaluation:

- remote MCP transports and hosted MCP services;
- enterprise proxy, TLS, identity, and credential arrangements;
- service-specific tool semantics and authoritative readback sources;
- Windows, macOS, containers, and Python environments outside the tested profile;
- production authentication, authorization, tenant isolation, bypass prevention, monitoring, incident ownership, and deployment suitability.

## Integration responsibilities

RPR does not discover that an arbitrary MCP server, client, or route receiver is trustworthy or authorized. The integrating application and operator remain responsible for:

- selecting and authenticating MCP peers;
- supplying receiver eligibility and delegation source-of-truth;
- protecting credentials, database files, and environment variables;
- restricting process, network, filesystem, and tool permissions;
- deciding which outbound tools require bounded Human Gate;
- supplying authoritative independent readback for consequential effects;
- defining repair, reconciliation, resume, and residual ownership;
- preventing alternate execution paths that bypass RPR;
- preventing untrusted MCP clients from reading pathway, route, and evidence data.

## Not implemented as MCP mutations

Published `0.1.0a6` does not expose mutating RPR MCP operations. Tools such as `rpr.request_human_gate`, `rpr.approve`, `rpr.execute`, `rpr.reconcile`, or `rpr.resume` are not current capabilities.

See also:

- [Product scope and architecture](product-scope-architecture.md)
- [Responsibility Routing migration](responsibility-routing-migration.md)
- [Security, integration, and API boundary](security-integration-api.md)
- [Verification, release notes, known issues, and UAT](verification-release-uat.md)
