"""
COM7021 Data Visualisation - Task 1
EcoMove City Transport Authority: data preparation and static visualisations.

Run:  python ecomove_analysis.py
Output: cleaned data summary in the console and eight PNG figures in ./figures
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "EcoMoveMobility.xlsx"
FIG = BASE / "figures"
FIG.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Colour palette (colour-blind validated categorical order, single-hue
# sequential ramp, blue/red diverging pair with a neutral grey midpoint)
# ---------------------------------------------------------------------------
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RED, GREY = "#e34948", "#9a9993"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
SURFACE = "#fcfcfb"
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#eaf2fd", "#9ec5f4", "#5598e7", "#256abf", "#0d366b"])
SEQ_ORANGE = LinearSegmentedColormap.from_list(
    "seq_orange", ["#fdeee7", "#f6b89c", "#eb6834", "#b8461b", "#7a2a0c"])
DIVERGING = LinearSegmentedColormap.from_list(
    "div", ["#184f95", "#6da7ec", "#f0efec", "#ef9a99", "#a32a29"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "DejaVu Sans",
    "font.size": 10, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.labelcolor": INK2,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "axes.axisbelow": True,
})


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved figures/{name}")


def subtitle(ax, text):
    ax.text(0, 1.02, text, transform=ax.transAxes, color=INK2, fontsize=9.5,
            va="bottom")


# ---------------------------------------------------------------------------
# 1. Load and prepare
# ---------------------------------------------------------------------------
def load_data(path=DATA):
    df = pd.read_excel(path)
    # Dates are stored as Excel serial numbers -> convert to datetime
    df["Date"] = pd.to_datetime(df["Date"], unit="D", origin="1899-12-30")
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Year"] = df["Date"].dt.year
    df["Profit_EUR"] = df["Ticket_Revenue_EUR"] - df["Operating_Cost_EUR"]
    df["Cost_Recovery"] = df["Ticket_Revenue_EUR"] / df["Operating_Cost_EUR"]
    df["Event_Day"] = df["Event_Day"].map({"Yes": "Event day", "No": "Normal day"})
    return df


def data_quality_report(df):
    print("Shape:", df.shape)
    print("Date range:", df["Date"].min().date(), "to", df["Date"].max().date())
    print("Missing values:", int(df.isna().sum().sum()))
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Duplicate Record_IDs:", int(df["Record_ID"].duplicated().sum()))
    num = df.select_dtypes("number").drop(columns=["Year"])
    print("\nNumeric summary:\n", num.describe().T.round(2).to_string())


# ---------------------------------------------------------------------------
# 2. Visualisations
# ---------------------------------------------------------------------------
def fig1_time_series(df):
    """Time series: monthly demand and reliability (two aligned panels)."""
    m = df.groupby("Month").agg(Passengers=("Passengers", "sum"),
                                Delay=("Average_Delay_Minutes", "mean"))
    m["Rolling"] = m["Passengers"].rolling(3, center=True).mean()

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 2], "hspace": 0.35})
    a1.plot(m.index, m["Passengers"] / 1e6, color=BLUE, lw=2, marker="o",
            ms=4, label="Monthly passengers")
    a1.plot(m.index, m["Rolling"] / 1e6, color=INK2, lw=1.5, ls="--",
            label="3-month rolling average")
    a1.set_ylabel("Passengers (millions)")
    a1.set_ylim(0, None)
    a1.set_title("Fig 1. Monthly passenger demand and average delay, 2024-2025", pad=22)
    subtitle(a1, "Demand is broadly stable at 1.4-2.1m a month but softens in the second half of 2025")
    a1.legend(loc="lower left", ncol=2)
    peak = m["Passengers"].idxmax()
    a1.annotate(f"Peak {m.loc[peak, 'Passengers']/1e6:.2f}m\n({peak:%b %Y})",
                (peak, m.loc[peak, "Passengers"] / 1e6), xytext=(25, -60),
                textcoords="offset points", fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))

    a2.plot(m.index, m["Delay"], color=ORANGE, lw=2, marker="o", ms=4)
    a2.axhline(df["Average_Delay_Minutes"].mean(), color=GREY, lw=1, ls=":")
    a2.text(m.index[0], df["Average_Delay_Minutes"].mean() + 0.03,
            "2-year average", color=INK2, fontsize=8.5, va="bottom")
    a2.set_ylabel("Avg delay (min)")
    a2.set_title("Average delay per record", fontsize=11, pad=6)
    save(fig, "fig1_time_series.png")


def fig2_city_demand(df):
    """Comparison: total passengers by city, ranked."""
    c = (df.groupby(["City", "Country"])["Passengers"].sum()
           .reset_index().sort_values("Passengers"))
    c["Label"] = c["City"] + " (" + c["Country"] + ")"
    top = c["Passengers"].nlargest(2).min()
    colors = [BLUE if v >= top else "#9ec5f4" for v in c["Passengers"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(c["Label"], c["Passengers"] / 1e6, color=colors, height=0.68)
    for b, v in zip(bars, c["Passengers"]):
        ax.text(b.get_width() + 0.04, b.get_y() + b.get_height() / 2,
                f"{v/1e6:.2f}m", va="center", fontsize=9, color=INK)
    ax.set_xlabel("Total passengers 2024-2025 (millions)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Fig 2. Passenger demand by city", pad=22)
    subtitle(ax, "Paris and Berlin carry ~4.5m passengers each - 77% more than Lyon, the lowest-demand city")
    save(fig, "fig2_city_demand.png")


def fig3_correlation(df):
    """Relationship: correlation heatmap of operational measures."""
    cols = {"Passengers": "Passengers", "Trips": "Trips",
            "Average_Delay_Minutes": "Avg delay", "On_Time_Percentage": "On-time %",
            "Ticket_Revenue_EUR": "Revenue", "Operating_Cost_EUR": "Op. cost",
            "CO2_Saved_KG": "CO2 saved", "Energy_Consumption_KWh": "Energy",
            "Customer_Rating": "Rating", "Accessibility_Complaints": "Access. complaints"}
    corr = df[list(cols)].rename(columns=cols).corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

    fig, ax = plt.subplots(figsize=(9.5, 8))
    sns.heatmap(corr, mask=mask, cmap=DIVERGING, vmin=-1, vmax=1, center=0,
                annot=True, fmt=".2f", annot_kws={"size": 8.5}, square=True,
                linewidths=2, linecolor=SURFACE, cbar_kws={"shrink": 0.7,
                "label": "Pearson correlation (r)"}, ax=ax)
    ax.grid(False)
    ax.set_title("Fig 3. Correlation between operational measures", pad=22)
    subtitle(ax, "Delay is the strongest driver of rating (r = -0.82); complaints scale with volume (r = 0.87)")
    save(fig, "fig3_correlation_heatmap.png")


def fig4_delay_distribution(df):
    """Distribution: box plot of delay by weather condition."""
    order = (df.groupby("Weather")["Average_Delay_Minutes"].median()
               .sort_values().index.tolist())
    pal = {w: ("#ef9a99" if w == "Snow" else "#9ec5f4") for w in order}

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.boxplot(data=df, x="Weather", y="Average_Delay_Minutes", order=order,
                hue="Weather", palette=pal, legend=False, width=0.55, linewidth=1.2,
                flierprops=dict(marker="o", markersize=3, markerfacecolor=GREY,
                                markeredgecolor="none", alpha=0.6), ax=ax)
    med = df.groupby("Weather")["Average_Delay_Minutes"].median()
    for i, w in enumerate(order):
        ax.text(i, med[w] + 0.15, f"{med[w]:.1f}", ha="center", va="bottom",
                fontsize=9, color=INK, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Average delay (minutes)")
    ax.set_title("Fig 4. Distribution of delay by weather condition", pad=22)
    subtitle(ax, "Snow more than doubles the median delay of clear days (8.4 vs 3.7 min); rain is the next worst")
    save(fig, "fig4_delay_by_weather_boxplot.png")


def fig5_cost_recovery(df):
    """Performance indicator: cost-recovery ratio by transport mode."""
    t = df.groupby("Transport_Mode").agg(Rev=("Ticket_Revenue_EUR", "sum"),
                                         Cost=("Operating_Cost_EUR", "sum"))
    t["CR"] = t["Rev"] / t["Cost"]
    t["Profit"] = t["Rev"] - t["Cost"]
    t = t.sort_values("CR")

    fig, ax = plt.subplots(figsize=(10, 5))
    y = np.arange(len(t))
    colors = [RED if v < 1 else BLUE for v in t["CR"]]
    ax.hlines(y, 0, t["CR"], color=colors, lw=2)
    ax.scatter(t["CR"], y, color=colors, s=90, zorder=3,
               edgecolor=SURFACE, linewidth=2)
    ax.axvline(1, color=INK2, lw=1.2, ls="--")
    ax.text(1.01, -0.45, "Break-even (revenue = cost)", fontsize=8.5,
            color=INK2, va="center")
    for yi, (cr, p) in enumerate(zip(t["CR"], t["Profit"])):
        sign = "+" if p >= 0 else "-"
        amt = f"{abs(p)/1e6:.1f}m" if abs(p) >= 1e5 else f"{abs(p)/1e3:.0f}k"
        ax.text(cr + 0.03, yi, f"{cr:.2f}  ({sign}EUR {amt})",
                va="center", fontsize=9, color=INK)
    ax.set_yticks(y, t.index)
    ax.set_xlim(0, 1.5)
    ax.set_ylim(-0.8, len(t) - 0.5)
    ax.set_xlabel("Cost-recovery ratio (ticket revenue / operating cost)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Fig 5. Financial performance by transport mode", pad=22)
    subtitle(ax, "Bike Share and E-Scooters recover only 5-7% of their cost; Park and Ride and Tram are most efficient")
    save(fig, "fig5_cost_recovery_by_mode.png")


def fig6_accessibility_heatmap(df):
    """Accessibility: complaints per 10,000 passengers, route type x mode."""
    g = df.groupby(["Route_Type", "Transport_Mode"]).agg(
        C=("Accessibility_Complaints", "sum"), P=("Passengers", "sum"))
    rate = (g["C"] / g["P"] * 1e4).unstack()
    rate = rate.loc[rate.mean(axis=1).sort_values(ascending=False).index,
                    rate.mean().sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.heatmap(rate, cmap=SEQ_ORANGE, annot=True, fmt=".1f", linewidths=2,
                linecolor=SURFACE, annot_kws={"size": 9},
                cbar_kws={"label": "Complaints per 10,000 passengers"}, ax=ax)
    ax.grid(False)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Fig 6. Accessibility complaint rate by route type and mode", pad=22)
    subtitle(ax, "Suburban Feeder E-Scooter and Bike Share services reach ~50 complaints per 10k passengers - 3-4x the network norm")
    save(fig, "fig6_accessibility_heatmap.png")


def fig7_delay_vs_rating(df):
    """Relationship: on-time performance vs customer rating."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["On_Time_Percentage"], df["Customer_Rating"], s=14,
               color=BLUE, alpha=0.25, edgecolor="none")
    b, a = np.polyfit(df["On_Time_Percentage"], df["Customer_Rating"], 1)
    xs = np.linspace(df["On_Time_Percentage"].min(), df["On_Time_Percentage"].max(), 50)
    ax.plot(xs, a + b * xs, color=ORANGE, lw=2.2)
    r = df["On_Time_Percentage"].corr(df["Customer_Rating"])
    ax.text(0.02, 0.95, f"r = {r:.2f}\nEach +10 pts on-time ~ +{b*10:.2f} rating",
            transform=ax.transAxes, va="top", fontsize=10, color=INK,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID))
    ax.set_xlabel("On-time percentage")
    ax.set_ylabel("Customer rating (1-5)")
    ax.set_title("Fig 7. Punctuality versus customer satisfaction (5,000 records)", pad=22)
    subtitle(ax, "A strong positive relationship: reliability is the main lever for customer experience")
    save(fig, "fig7_ontime_vs_rating_scatter.png")


def fig8_event_days(df):
    """Comparison small multiples: event days vs normal days."""
    metrics = [("Average_Delay_Minutes", "Avg delay (min)", "{:.1f}"),
               ("On_Time_Percentage", "On-time %", "{:.1f}%"),
               ("Customer_Rating", "Customer rating", "{:.2f}")]
    g = df.groupby("Event_Day")[[m[0] for m in metrics]].mean().loc[["Normal day", "Event day"]]

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.3))
    for ax, (col, label, fmt) in zip(axes, metrics):
        bars = ax.bar(g.index, g[col], color=[BLUE, ORANGE], width=0.6)
        for bb, v in zip(bars, g[col]):
            ax.text(bb.get_x() + bb.get_width() / 2, v, fmt.format(v),
                    ha="center", va="bottom", fontsize=10, color=INK)
        ax.set_title(label, fontsize=11)
        ax.grid(axis="x", visible=False)
        ax.margins(y=0.15)
    fig.suptitle("Fig 8. Service performance on major event days vs normal days",
                 x=0.01, ha="left", fontweight="bold", fontsize=13, y=1.06)
    fig.text(0.01, 0.97, "Event days add ~1.3 minutes of delay (+31%), cut punctuality by 4 pts and lower ratings",
             color=INK2, fontsize=9.5)
    fig.tight_layout()
    save(fig, "fig8_event_day_comparison.png")


def summary_tables(df):
    agg = dict(Passengers=("Passengers", "sum"),
               Revenue=("Ticket_Revenue_EUR", "sum"),
               Cost=("Operating_Cost_EUR", "sum"),
               CO2_saved_kg=("CO2_Saved_KG", "sum"),
               Avg_delay=("Average_Delay_Minutes", "mean"),
               On_time=("On_Time_Percentage", "mean"),
               Rating=("Customer_Rating", "mean"),
               Complaints=("Accessibility_Complaints", "sum"))
    for dim in ["Transport_Mode", "City", "Weather", "Route_Type", "Event_Day"]:
        t = df.groupby(dim).agg(**agg)
        t["Cost_recovery"] = t["Revenue"] / t["Cost"]
        t["Complaints_per_10k"] = t["Complaints"] / t["Passengers"] * 1e4
        print(f"\n=== {dim} ===\n", t.round(2).sort_values("Passengers", ascending=False).to_string())


if __name__ == "__main__":
    data = load_data()
    data_quality_report(data)
    summary_tables(data)
    print("\nCreating figures...")
    for f in (fig1_time_series, fig2_city_demand, fig3_correlation,
              fig4_delay_distribution, fig5_cost_recovery,
              fig6_accessibility_heatmap, fig7_delay_vs_rating, fig8_event_days):
        f(data)
