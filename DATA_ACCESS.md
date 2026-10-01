# Data access

The research uses PFF FC's 2022 World Cup tracking and events. The provider's current [Gradient Sports release page](https://www.gradientsports.com/blog/enhanced-2022-world-cup-dataset) describes free access.

To obtain the underlying data:

1. Visit the release page and use its access form if available.
2. Otherwise email [support@gradientsports.com](mailto:support@gradientsports.com), listed on the [official contact page](https://www.gradientsports.com/contact).
3. Request the **2022 FIFA World Cup dataset originally released by PFF FC**, including tracking, events, metadata, rosters and data specifications. Explain that you are reproducing an SSAC research submission and ask for the applicable usage and sharing terms.

Both links and the listed email address were checked on 2026-10-01. Dataset access is handled by the provider. The Colab notebook uses the included derived inputs and does not require raw files.

This repo contains normalized computed features, classifier parameters and scores, binary labels, anonymous event links, tactical recovery flags and computed pitch-control fields. Figure 1 uses rendered annotation artwork instead of numeric player positions. Raw provider files, trajectories, player velocities, event records and original coordinate arrays are excluded.

SSAC accepts code, permitted derived data and provider access instructions for abstract-stage reproducibility. A dataset-specific redistribution license was not found in the provider's public documentation, and permission to share these derived inputs remains unconfirmed. The MIT license applies to code only; conference guidance does not establish data-sharing rights.
