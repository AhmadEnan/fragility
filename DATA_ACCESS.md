# Data access

The research uses PFF FC's 2022 World Cup tracking and events. The provider's current [Gradient Sports release page](https://www.gradientsports.com/blog/enhanced-2022-world-cup-dataset) describes free access.

To obtain the underlying data:

1. Visit the release page and use its access form if available.
2. Otherwise email [support@gradientsports.com](mailto:support@gradientsports.com), listed on the [official contact page](https://www.gradientsports.com/contact).
3. Request the **2022 FIFA World Cup dataset originally released by PFF FC**, including tracking, events, metadata, rosters and data specifications. Explain that you are reproducing an SSAC research submission and ask for the applicable usage and sharing terms.

The release and contact pages were checked on 2026-10-01. The email is publicly listed; delivery and access approval have not been tested. The Colab notebook does not require these raw files.

This repo contains normalized computed features, classifier parameters and scores, binary labels, anonymous event links, tactical recovery flags and computed pitch-control fields. Figure 1 uses rendered annotation artwork instead of numeric player positions. Raw provider files, trajectories, player velocities, event records and original coordinate arrays are excluded.

SSAC's reply confirms that code, permitted derived data/features and provider access instructions are an appropriate abstract-stage approach. It also states that reproducibility affects evaluation but is not a submission requirement.

A dataset-specific redistribution license was not found on the provider's public release or terms pages. The invitation to share findings does not establish permission for downloadable feature tables. Provider permission for these derived inputs has not been independently confirmed. Conference guidance and the code's MIT license do not grant third-party data rights.
