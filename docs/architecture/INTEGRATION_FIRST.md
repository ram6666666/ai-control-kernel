# Integration-First Architecture Principle

status: ACTIVE_DESIGN_PRINCIPLE
scope: AI Control Kernel
adopted_at_utc: 2026-09-01T19:28:44Z

## Principle

AI Control Kernel is an integration/control layer, not a mandate to rebuild mature infrastructure.

When a reliable existing component already solves a lower-level problem well, the default is to integrate it behind a stable adapter rather than reimplement it for aesthetic uniformity.

Examples of infrastructure that should normally be integrated rather than rebuilt include:

- durable workflow/runtime engines;
- schedulers and retry engines;
- model/provider SDKs;
- storage and object-transfer systems;
- Git hosting/version control;
- identity/authentication and secret stores;
- tracing/observability backends;
- established schema/serialization libraries.

## What the kernel should own

The kernel should own the cross-system semantics that are specific to this project and are not reliably supplied by any one underlying runtime:

- effective authority/state resolution;
- deterministic transition validation;
- execution-capsule compilation;
- provenance and source-revision binding;
- model-neutral capability/routing contracts;
- artifact identity contracts across storage boundaries;
- independent-audit control semantics;
- user-owned portable operating state;
- adapters that translate these contracts to/from external runtimes.

## Build-vs-integrate gate

Before adding a new subsystem to the kernel, answer:

1. Is this capability part of the kernel's unique control semantics, or generic infrastructure?
2. Does a mature, inspectable component already provide it?
3. Can we define a narrow adapter/interface instead of owning the implementation?
4. Would rebuilding it create a second scheduler, storage layer, workflow engine, agent framework, or provider SDK?
5. Does owning it materially improve portability, authority correctness, auditability, or user control?

If the answer is generic infrastructure with a suitable existing component, integration is preferred.

## Anti-patterns

- rebuilding Temporal-like durable execution inside the kernel;
- embedding model-specific orchestration assumptions into core state semantics;
- using an agent framework as the canonical state database;
- making a provider's memory/session object the user's durable project state;
- requiring LLMs to transport bytes or reconstruct binary artifacts;
- adding framework layers solely to make the architecture appear unified.

## Adapter rule

External integrations should be replaceable. Core machine contracts must not depend on one provider's object model. Provider/runtime-specific details belong behind adapters, while the kernel's authority, provenance, transition and capsule contracts remain model/runtime neutral.
