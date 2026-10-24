# BitWatts: computational and energy accounting contract

**BitWatts** is the project-specific name for BGR's computation/resource measurement system. This release tracks action interactions, candidate rule checks, hypothetical observation branches, wall-clock process time, and number of verified predictions. These counts are **not** physical power, energy, watts, joules, or electrical efficiency.

Measured electrical energy in a later hardware experiment would require externally instrumented power \(P(t)\) and duration:

\[E=\int_{t_0}^{t_1}P(t)\,dt.\]

No sensor or measurement has supplied \(P(t)\) for v0.84; physical energy measurement remains deferred by the user. Do not estimate watts or power savings from node/candidate counts alone. Keep physical and model-semantic metrics separate.
