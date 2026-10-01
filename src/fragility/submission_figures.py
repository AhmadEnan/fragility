"""Render the opening-landscape and event-retrieval figures."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, PowerNorm

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/derived"
OUT = ROOT / "results/figures"
OUT.mkdir(parents=True, exist_ok=True)
FONT = (
    "Arial"
    if any((f.name == "Arial" for f in font_manager.fontManager.ttflist))
    else (
        "Liberation Sans"
        if any(f.name == "Liberation Sans" for f in font_manager.fontManager.ttflist)
        else "DejaVu Sans"
    )
)
plt.rcParams.update(
    {
        "font.family": FONT,
        "font.size": 11,
        "text.color": "#182228",
        "axes.labelcolor": "#182228",
        "xtick.color": "#52616a",
        "ytick.color": "#52616a",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ssac27",
        "mathtext.fontset": "stix",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
INK = "#182228"
MUTED = "#52616a"
BLUE = "#185f91"
RED = "#b95345"
GREEN = "#187c57"
GRAY = "#bbc4ca"


def save(fig, name):
    for ext in ["png", "pdf", "svg"]:
        path = OUT / f"{name}.{ext}"
        metadata = (
            {"Date": None}
            if ext == "svg"
            else ({"CreationDate": None, "ModDate": None} if ext == "pdf" else None)
        )
        fig.savefig(path, dpi=300, facecolor="white", metadata=metadata)
        if ext == "svg":
            path.write_text(
                "\n".join(
                    line.rstrip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                )
                + "\n",
                encoding="utf-8",
            )
    plt.close(fig)


def figure1():
    """Render computed control fields beneath fixed illustration artwork."""
    from PIL import Image
    import io

    z = np.load(DATA / "figure1_plot.npz")
    fig = plt.figure(figsize=(14, 8.7))
    control = LinearSegmentedColormap.from_list(
        "teams", ["#cc6658", "#fdfbf8", "#4e89ae"]
    )
    gainmap = LinearSegmentedColormap.from_list(
        "gain", ["#ffffff", "#cde9d6", "#66b185", "#126443"]
    )
    for bounds, field, cmap, norm in [
        ((0.055, 0.235, 0.265, 0.6), z["C0"], control, None),
        (
            (0.675, 0.235, 0.265, 0.6),
            z["gain"],
            gainmap,
            PowerNorm(gamma=0.7, vmin=0, vmax=0.1),
        ),
    ]:
        ax = fig.add_axes(bounds)
        ax.set(xlim=(18, 54), ylim=(-23, 18), aspect="equal")
        ax.axis("off")
        kwargs = {"norm": norm} if norm is not None else {"vmin": 0, "vmax": 1}
        ax.imshow(
            field,
            origin="lower",
            extent=[-52.5, 52.5, -34, 34],
            interpolation="bilinear",
            cmap=cmap,
            **kwargs,
        )
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=300, facecolor="white")
    plt.close(fig)
    background = Image.open(buffer).convert("RGBA")
    image = Image.alpha_composite(background, Image.fromarray(z["overlay_rgba"]))
    path = OUT / "FIGURE_1_OPENING_LANDSCAPE.png"
    pixels = np.asarray(image.convert("RGB")).astype(np.int16)
    y, x = z["correction_xy"].T
    pixels[y, x] += z["correction_rgb"]
    Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)).save(path)
    return path


def figure2():
    res = ROOT / "results/reference"
    perf = pd.read_csv(res / "MODEL_PERFORMANCE.csv").set_index("model")
    ec = pd.read_csv(res / "EVENT_CAPTURE.csv").set_index("model")
    bench = ROOT / "results/reproduced"
    source = bench / "arm_performance.csv"
    dev = pd.read_csv(source).set_index("arm")
    arms = [
        "M0",
        "M0+SOG(incumbent)",
        "M0+EPV_WEIGHTED_CONTROL",
        "M0+EPV_AT_BALL",
        "M0+D_OBSO",
        "M0+DAS",
    ]
    selected = dev.loc[arms]
    dev_labels = [
        "M0: Context baseline",
        "M0 + SOG landscape\nand movement alignment",
        "M0 + EPV-weighted control",
        "M0 + EPV at ball",
        "M0 + OBSO (adapted)",
        "M0 + DAS",
    ]
    labels = dev_labels
    y = np.arange(6)[::-1]
    colors = [GRAY, GREEN, GRAY, GRAY, GRAY, GRAY]
    vals = 100 * selected.event_capture_at_10.to_numpy(float)
    ns = selected.events_captured.to_numpy(int)
    totals = selected.events_total.to_numpy(int)
    auc = selected.auc.to_numpy(float)
    assert np.isfinite(vals).all() and np.allclose(
        vals, 100 * ns / totals, atol=1e-12, rtol=0
    )
    fig = plt.figure(figsize=(14, 8.7))
    fig.text(
        0.055,
        0.945,
        "Comparing models on the same match situations",
        fontsize=17,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.905,
        "16 matches · 38,035 match situations · 752 successful penetrations · Same situations for every model",
        fontsize=11,
        color=MUTED,
    )
    ax = fig.add_axes([0.29, 0.39, 0.3, 0.42])
    ax.barh(y, vals, color=colors, height=0.51, zorder=3)
    ax.set_yticks(y, labels, fontsize=10.5)
    ax.tick_params(axis="y", length=0, pad=13)
    ax.set_ylim(-0.7, 5.7)
    ax.set_xlim(0, 40)
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.set_xlabel("Successful penetrations retrieved (%)", fontsize=11, labelpad=12)
    ax.set_title(
        "A. Events found: top 10% of states",
        loc="left",
        fontsize=13,
        fontweight="bold",
        pad=18,
    )
    ax.grid(axis="x", color="#e6ebee")
    ax.spines["left"].set_visible(False)
    for yy, v, n, total, col in zip(y, vals, ns, totals, colors):
        ax.text(
            v + 0.8,
            yy,
            f"{v:.1f}%\n{n}/{total}",
            va="center",
            fontsize=10,
            fontweight="bold" if col == GREEN else "normal",
        )
    ax2 = fig.add_axes([0.69, 0.39, 0.25, 0.42])
    ax2.scatter(
        auc, y, s=[90 if c == GREEN else 65 for c in colors], c=colors, zorder=4
    )
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks([])
    ax2.set_xlim(0.5, 0.74)
    ax2.set_xticks([0.5, 0.6, 0.7])
    ax2.grid(axis="x", color="#e6ebee")
    ax2.spines["left"].set_visible(False)
    ax2.set_xlabel("Ranking quality (ROC AUC)", fontsize=11, labelpad=12)
    ax2.set_title(
        "B. State discrimination (ROC AUC)",
        loc="left",
        fontsize=13,
        fontweight="bold",
        pad=18,
    )
    for yy, v, col in zip(y, auc, colors):
        ax2.text(
            v + 0.009,
            yy,
            f"{v:.3f}",
            va="center",
            fontsize=11,
            fontweight="bold" if col == GREEN else "normal",
        )
    inc = (
        pd.read_csv(bench / "increments_m0.csv")
        .set_index("arm")
        .loc["M0+SOG(incumbent)"]
    )
    fig.text(
        0.29,
        0.29,
        "M0 → SOG: 195 → 245 events (+25.6%)",
        fontsize=11,
        fontweight="bold",
        color=GREEN,
    )
    fig.text(
        0.69,
        0.29,
        f"SOG vs M0: ΔAUC {inc.d_auc:+.4f} [{inc.ci_lo:.4f}, {inc.ci_hi:.4f}]",
        fontsize=9.5,
        fontweight="bold",
        color=GREEN,
    )
    fig.text(
        0.055,
        0.247,
        "Every model uses the same outcome, match-based cross-validation and top-10% review budget.",
        fontsize=9.5,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.221,
        "These matches were used for model development. Results are retrospective; this is not an independent test.",
        fontsize=9.2,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.192,
        "AUC: probability a positive state ranks above a negative state; 0.5 = chance (half credit for ties).",
        fontsize=9.5,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.16,
        "What the SOG feature block receives",
        fontsize=12,
        fontweight="bold",
    )
    rows = [
        (
            "Context baseline (M0)",
            "Ball location, possession age, pressure, player speeds, defensive geometry and current control.",
        ),
        (
            "Scalar SOG summary",
            "Mean of the highest-scoring 10% of valid hypothetical movements.",
        ),
        (
            "SOG landscape",
            "Score sizes, distribution, leading-score gap and concentration across players.",
        ),
        (
            "Movement alignment",
            "Whether attackers are moving toward their own highest-scoring directions.",
        ),
    ]
    for yrow, (name, description) in zip([0.135, 0.113, 0.091, 0.069], rows):
        fig.text(0.055, yrow, name, fontsize=9.6, color=MUTED, va="center")
        fig.text(0.285, yrow, description, fontsize=9.6, va="center")
    fig.text(
        0.055,
        0.04,
        "SOG algorithm: $S(a)=\\frac{\\sum_r(1-C_0(r))\\,[C_a(r)-C_0(r)]_+}{\\rho_a/(1\\,\\mathrm{m})}$; rank candidate movements by decreasing score.",
        fontsize=11,
        va="center",
    )
    fig.text(
        0.055,
        0.014,
        "$C_0$: baseline attacking control; $C_a$: control after movement $a$; $\\rho_a$: displacement; $[z]_+=\\max(z,0)$. Interval: 95% paired match bootstrap.",
        fontsize=8.7,
        color=MUTED,
        va="center",
    )
    save(fig, "FIGURE_2_REVIEW_UTILITY")
    return (perf, ec)
