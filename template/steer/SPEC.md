# Spec

Fill this in before building. `/steer-spec` will help draft it, but a human should read and approve every access rule.

The goal is to write down the things nobody usually asks for: who may see what, what the agent is allowed to touch, and how someone would try to misuse each feature.

## 1. Product summary

<!-- Two or three sentences. What it does, for whom. -->

## 2. Actors

| Actor | How they are identified | Notes |
|---|---|---|
| <!-- e.g. Customer --> | <!-- e.g. session cookie, JWT sub --> | |
| <!-- e.g. Support admin --> | | |
| <!-- e.g. The agent itself --> | Acts on behalf of the session user only | |

## 3. Data objects and ownership

| Object | Owned by | Sensitive fields |
|---|---|---|
| <!-- e.g. Order --> | <!-- e.g. Customer (orders.customer_id) --> | <!-- e.g. address, phone --> |

## 4. Access matrix

For each object and actor: none, own, all. Ask "who should be allowed to see this?" for every row.

| Object | Actor | Read | Create | Update | Delete |
|---|---|---|---|---|---|
| | | | | | |

## 5. Agent tools

Every function the model can call. If the agent has no tools, write "none" and skip.

| Tool | Inputs the model supplies | Identity source | Side effects | Limits enforced in code | Needs user confirmation |
|---|---|---|---|---|---|
| <!-- get_order --> | <!-- order_id --> | <!-- session, never an argument --> | <!-- none --> | <!-- scoped to session user --> | <!-- no --> |
| <!-- request_refund --> | <!-- order_id, amount --> | <!-- session --> | <!-- creates refund --> | <!-- amount <= order total, ceiling X --> | <!-- yes --> |

## 6. Policy sources

Where each policy the agent relies on comes from. User messages are never a policy source.

| Policy | Source |
|---|---|
| <!-- Refund window --> | <!-- policies table / config file, versioned --> |

## 7. Features

Repeat this block for each feature. Each feature becomes one or more rows in `steer/TRACKER.md`.

### F1. <!-- name -->

- **What it does:**
- **Actors:**
- **Touches data:** <!-- objects --> 
- **Side effects:**
- **Access rules:** <!-- reference the matrix, note anything special -->
- **Misuse cases:** <!-- IDs from steer/MISUSE.md plus anything feature-specific -->
  - M1: <!-- how it applies here, expected behaviour -->
- **Acceptance tests:** <!-- happy path -->
- **Gates that apply:** <!-- G1, G2 ... -->
