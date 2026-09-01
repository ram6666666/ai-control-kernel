# AI Control Kernel

AI Control Kernel is a user-owned, model-neutral control layer for long-running work across AI models, agents, tools, and workflow runtimes.

It is **not another agent framework** and does not aim to reimplement mature infrastructure such as durable workflow engines, schedulers, model SDKs, or storage systems. Its purpose is to integrate them behind a consistent control plane that keeps project state, authority, provenance, permissions, execution boundaries, and auditability outside any individual model or conversation.

The project focuses on the layer between human intent and replaceable AI executors: deterministic effective-state resolution, bounded execution capsules, artifact identity, immutable lifecycle evidence, capability-based routing, independent audit, cross-model handoff, and portable user-controlled state.

> **Use deterministic software for mechanics, AI for semantic reasoning, and humans for goals and material decisions. Integrate mature infrastructure wherever possible instead of rebuilding it.**

## Current status

`v0.1` is in design/migration. No production cutover is authorized.

The project originated inside `ram6666666/ai-`. During the initial migration:

- this repository becomes the canonical home for AI Control Kernel engineering design, code, schemas, tests, and releases after migration verification;
- `ram6666666/ai-` remains the canonical cross-project AI operating-system/control-plane repository and retains the current control-task lineage;
- migration must not create two peer sources of task or policy truth;
- implementation begins only after the v0.1 design-freeze gate passes.

## v0.1 target scope

- schema validation;
- effective policy/task/package state resolution;
- legal transition validation;
- immutable-event validation and materialized read models;
- artifact identity and SHA-256 when real bytes are available;
- execution-capsule compilation.

## Non-goals

- replacing Temporal/LangGraph/other mature workflow infrastructure;
- autonomous scientific or semantic decisions;
- model/vendor lock-in;
- LLM-mediated binary transport;
- replacing independent audit or human material acceptance;
- immediate migration of the entire existing control plane.

Design provenance and migration details live under `docs/` and `provenance/`.
