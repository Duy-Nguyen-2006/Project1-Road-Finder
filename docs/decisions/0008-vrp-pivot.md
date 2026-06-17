# 0008 VRP Delivery Routing Pivot

Date: 2026-06-18 (record) / 2026-06-14 (decision made, commit `b7afc10` + `02e98dd` + `a2bc8f4`)

## Status

Accepted

## Context

The original Road Finder MVP (per `Walkthrough.md` P0–P17 and the
`hcm-fixture-v1` graph) was scoped as a single Start / End shortest-path
finder backed by a local HCM road graph and a Bidirectional Dijkstra
solver. By 2026-06-04 that MVP was technically complete: 71 backend
tests passed, `/shortest-path` and `/graph-bounds` were live, and the
frontend was a two-mode (Start / End) picker on a Leaflet map.

Immediately after the MVP cutover, the project owner needed the same
backend infrastructure (local graph, snap, Bidirectional Dijkstra,
LRU cache) to solve a different problem: optimising delivery routes
for a fleet of shippers handling many pickup → dropoff orders in
TP.HCM. That use case is a Vehicle Routing Problem (VRP) with
pickup-before-dropoff precedence constraints, not a point-to-point
shortest path.

The MVP codebase could technically answer the fleet use case, but only
by calling `/shortest-path` once per leg and reimplementing the
assignment + tour optimisation client-side. Doing so would have left
the optimisation, precedence handling, and leg reuse logic out of
the backend contract and out of the test matrix.

Two options were on the table:

1. **Keep MVP scope.** Tell the project owner the system only does
   point-to-point, and add a separate "fleet" service in a different
   repo or runtime.
2. **Pivot the same repo to VRP.** Extend the local graph loader and
   Dijkstra pipeline with assignment / TSP / VRP solvers, add three
   more endpoints, and rewrite the frontend to manage a fleet of
   shippers and orders.

The shared graph runtime, snap service, LRU cache, and leg builder
make option 2 substantially cheaper than option 1 in terms of new
code. The cost is rewriting docs and tests that documented the MVP
shape, and accepting that any external caller still using
`/shortest-path` or `/optimize-route` will break.

## Decision

Pivot the existing Road Finder repo to **VRP Delivery Routing**.

Concretely, between 2026-06-14 and the present:

- **Backend endpoints:** drop `/shortest-path`, `/optimize-route`,
  and the hyphenated `/graph-bounds`. Add `/route` (single leg),
  `/assignments` (1 order + N shipper ranking), `/tours` (1 shipper
  + N order TSP), and `/fleet` (M shipper + N order VRP). The
  existing `/health` and a renamed `/graph/bounds` (with a slash) are
  kept.
- **Graph model:** extend each edge with `oneway: bool` and
  `road_type: str`. Build a directed adjacency plus a reverse
  adjacency so Bidirectional Dijkstra respects oneway streets. Edge
  cost is `distance × multiplier(road_type)`, with
  `avoid_road_types` and `avoid_edge_ids` in `RoutingOptions`
  blocking traversal.
- **Solvers:** keep Bidirectional Dijkstra for `/route` and as the
  inner cost matrix. Add `optimize_tour` in `domain/tsp.py`
  (brute-force ≤ 8 stops for `optimal=true`, nearest-neighbor +
  2-opt heuristic otherwise). Add `solve_vrp` in `domain/vrp.py`
  (cheapest-insertion assignment + intra-route 2-opt + inter-route
  relocate, with a brute-force path for `len(orders) ≤ 3` and
  `len(shippers) ≤ 2`).
- **Frontend:** drop `useRoutePoints`, `RouteControls`, and the
  Start / End / Waypoint mode UI. Introduce `useVrpState`,
  `ModeSwitcher` (Order Pickup/Dropoff ↔ Shipper), `OptionsPanel`
  (avoid_road_types checkboxes), and `FleetResultPanel`. The map
  now draws one polyline per shipper in a fixed 8-color palette.
- **Docs and tests:** rewrite `README.md`, `Walkthrough.md`, and
  `docs/product/*` to match the new shape. Add four story packets
  (`US-001` to `US-004`) under `E01 VRP Delivery Routing` and
  register them in `harness.db` via `harness-cli story add`. Old
  `Code.md` (3.7 MB of unrelated i18n content) and
  `repomix-output.xml` (snapshot of the TSP/OSRM code state) are
  moved to `.archive/` so the active tree reflects the current
  shape.
- **Real HCM data:** generate a 1710-node / 2339-edge
  `road_graph.hcm-v1.json` from Overpass via `osmnx` and commit it
  as a smoke target, alongside the deterministic
  `road_graph.json` fixture used by unit tests.

## Alternatives Considered

1. **Add a parallel fleet service in a new repo.** Cleanest separation
   but duplicates the graph loader, snap service, cost matrix, and
   LRU cache. Loses the chance to share `RoutingOptions` semantics
   across product surfaces. Rejected because the marginal cost of
   extending the existing service was small.
2. **Keep `/shortest-path` and add a thin fleet wrapper.** Avoids a
   breaking API change but pushes the VRP solver into the client or
   into ad-hoc multi-call patterns. The server would still answer
   "give me a leg" questions but not "plan the fleet." Rejected
   because the call shape gets worse, not better, and the precedence
   + assignment logic has to live somewhere — the server is the
   right place.
3. **Defer VRP until after a real OSM graph is generated.** Wait for
   a fully baked HCM graph before adding the VRP layer. Rejected
   because the fixture graph is enough to design and test the
   solvers, and the solver code does not depend on the graph being
   "real."

## Consequences

Positive:

- One backend, one contract, one set of tests covers both the
  single-leg ("find me a route from A to B") and the fleet ("plan
  five shippers across ten orders") use cases.
- The `CostMatrix` and `RouteCache` become the single source of
  truth for inter-node distances, so the LRU cache is shared across
  `/route`, `/tours`, and `/fleet` calls with the same start/end
  pair.
- The frontend state model (`useVrpState`) is closer to the actual
  dispatcher workflow and forces the user to think in terms of
  orders, pickups, dropoffs, and shipper capacity — not arbitrary
  "waypoints."

Tradeoffs:

- Any external caller of the old `/shortest-path`, `/optimize-route`,
  or hyphenated `/graph-bounds` is broken. The commit message and
  the `droid-wiki/lore.md` history note the breaking change, but
  there is no versioned migration.
- The `RoutingOptions` surface is wider (avoid_road_types,
  avoid_edge_ids, plus the new solver thresholds) and the
  cost-multiplier table is part of the de facto contract. Future
  changes to multipliers are silently a behaviour change.
- The frontend went from a 2-mode (Start / End) UI to a 3-mode
  (Order Pickup / Order Dropoff / Shipper) state machine, which
  means new ergonomic bugs around the "pending pickup" state
  (clicking dropoff without first clicking pickup) and around
  removing a pickup that has a paired dropoff.

## Follow-Up

- Write `BL-007` (expose `brute_force_threshold` for TSP and VRP
  through `RoutingOptions`) so the brute-force cutoff is a tunable
  contract, not a hidden default. Tracked in
  `docs/stories/backlog.md`.
- Write `BL-008` is this decision record; link from
  `Walkthrough.md §9 Quyết định đã chốt`.
- Decide whether `Road Finder` (the project name) still fits the
  product, or whether it should be renamed to "VRP Delivery
  Routing" (or similar) to match the README and the new shape.
  Out of scope for this decision.
- Investigate why the v1 graph has so many small disconnected
  components in the southern part of the bbox (oneway network
  effect); possibly a graph-data issue, possibly a model issue
  where some stops look connected only via the reverse adjacency.
  Tracked in `Walkthrough.md §10 R6`.
