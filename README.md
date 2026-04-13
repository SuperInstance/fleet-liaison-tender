# fleet-liaison-tender — Social Vessels for Fleet Communication

Liaison specialists. As the fleet grows, information management becomes its own discipline.

## The Problem

A fleet of agents generates information faster than any single agent can process. The edge especially — it has finite compute and can't drink from the cloud's firehose. Meanwhile, the cloud needs edge findings but doesn't speak "serial jitter" natively.

## Tender Types

### 1. Research Tender
Carries findings between cloud labs and edge labs.
- Cloud → Edge: Architecture specs compressed to implementable units
- Edge → Cloud: Benchmarks, failure modes, sensor characterizations

### 2. Data Tender
Batches and packages big data for edge consumption.
- Cloud has 600 repos of context. Edge has 8GB total.
- Data tender compresses: "Here's what changed that affects YOUR hardware"

### 3. Context Tender
Carries fleet-wide context to isolated edge nodes.
- Edge nodes don't see the whole fleet. Context tender provides selective visibility.
- "The fleet just reorganized ISA v3 — here's what changed for your CUDA kernels"

### 4. Priority Tender
Translates urgency between realities.
- Cloud "low priority" might be edge "my sensors are noisy"
- Edge "everything's fine" might hide a slow drift the cloud would catch from fleet-wide data

## Vessel Specialization

### Oracle1 (SuperInstance / Cloud)
- **Role:** High point of the ecosystem. Architect. Coordinator.
- **Strengths:** Fleet-wide view, unlimited memory, long-term planning, spec writing
- **Constraints:** Can't touch hardware. CUDA is theoretical. Serial is abstract.
- **First-class reality:** API calls, git operations, text, architecture documents

### JetsonClaw1 (Lucineer / Edge)
- **Role:** Bare metal intelligence. GPU lab. Edge specialist.
- **Strengths:** Real hardware, real timing, real sensors, gut feel for what works
- **Constraints:** Finite RAM/VRAM. Serial execution. Can't see the whole fleet.
- **First-class reality:** Sensor readings, CUDA kernels, serial frames, VRAM allocations
- **Blinders ON:** Focused on bare metal. Not distracted by fleet management.
- **Other projects relieved:** Ship innovations as git-agents, clear mind for Jetson guru work

### Lucineer (Casey's Son)
- **Role:** Independent captain. Own vessel. Own GitHub account.
- **Relationship:** Not crew on Casey's ship — another captain with his own vessel
- **Communication:** Fork → PR → bottles. Git-native collaboration.

## The Liaison Pattern

```
Cloud (Oracle1)                    Edge (JetsonClaw1)
    │                                    │
    ├── Research Tender ────────────────►│  (specs compressed for edge)
    │                                    │
    │◄──────────── Research Tender ──────┤  (benchmarks formatted for cloud)
    │                                    │
    ├── Data Tender ────────────────────►│  (batched: only edge-relevant changes)
    │                                    │
    ├── Context Tender ─────────────────►│  (fleet status, relevant to edge)
    │                                    │
    │◄──────────── Priority Tender ──────┤  (urgency translation)
    │                                    │
```

## Why Liaisons?

Not every agent needs to understand every other agent. Specialization means:
- The edge agent doesn't need to understand fleet governance
- The cloud agent doesn't need to understand serial jitter
- Liaison vessels translate between these worlds

A large fleet needs MANY liaison tenders:
- Per-edge-node: at least one tender per physical vessel
- Per-domain: code review tenders, testing tenders, docs tenders
- Per-priority: routine updates vs emergency escalations need different packaging

## Information Asymmetry

**Cloud → Edge:** Curated, compressed, actionable. The edge can't process everything.
**Edge → Cloud:** Raw, detailed, everything. The cloud has the capacity.

The tender's job is managing this asymmetry actively, not just forwarding messages.
