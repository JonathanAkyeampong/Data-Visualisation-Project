"""
COM7021 Data Visualisation - Task 1
EcoMove interactive dashboard for senior managers (Plotly Dash).

Run:  python ecomove_dashboard.py   then open http://127.0.0.1:8050
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from ecomove_analysis import load_data

df = load_data()

BLUE, ORANGE, RED, GREY, AQUA = "#2a78d6", "#eb6834", "#e34948", "#9a9993", "#1baf7a"
INK, INK2, GRID, SURFACE, PAGE = "#0b0b0b", "#52514e", "#e6e5e0", "#ffffff", "#f4f4f1"
FONT = "Inter, Segoe UI, Helvetica, Arial, sans-serif"


def style(fig, title, height=340):
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=15, color=INK)),
        height=height, margin=dict(l=10, r=20, t=50, b=10),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family=FONT, color=INK2, size=12), showlegend=False,
        hoverlabel=dict(bgcolor="white", font_family=FONT))
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def eur(v):
    return f"EUR {v/1e6:.2f}m" if v >= 1e6 else f"EUR {v/1e3:,.0f}k"


def dropdown(id_, label, col):
    opts = sorted(df[col].unique())
    return html.Div([
        html.Label(label, className="flabel"),
        dcc.Dropdown(id=id_, options=opts, value=[], multi=True,
                     placeholder="All"),
    ], className="filter")


def kpi(id_, label):
    return html.Div([html.Div(label, className="klabel"),
                     html.Div(id=id_, className="kvalue"),
                     html.Div(id=id_ + "-sub", className="ksub")], className="kpi")


app = Dash(__name__, title="EcoMove Mobility Dashboard")
server = app.server  # WSGI entry point for hosting (gunicorn ecomove_dashboard:server)
app.index_string = app.index_string.replace("</head>", """
<style>
 body{margin:0;background:%s;font-family:%s;color:%s}
 .wrap{max-width:1400px;margin:0 auto;padding:20px 24px 40px}
 h1{font-size:24px;margin:0 0 4px} .lede{color:%s;margin:0 0 16px;font-size:14px}
 .filters{display:grid;grid-template-columns:1.3fr repeat(6,1fr);gap:12px;background:#fff;
   padding:14px;border-radius:10px;border:1px solid %s;margin-bottom:16px}
 .flabel{font-size:12px;font-weight:600;color:%s;display:block;margin-bottom:4px}
 .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
 .kpi{background:#fff;border:1px solid %s;border-radius:10px;padding:12px 14px}
 .klabel{font-size:12px;color:%s;text-transform:uppercase;letter-spacing:.04em}
 .kvalue{font-size:26px;font-weight:700;margin-top:4px} .ksub{font-size:12px;color:%s}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
 .card{background:#fff;border:1px solid %s;border-radius:10px;padding:6px}
 .wide{grid-column:1/-1}
 @media(max-width:900px){.filters,.kpis,.grid{grid-template-columns:1fr}}
</style></head>""" % (PAGE, FONT, INK, INK2, GRID, INK2, GRID, INK2, INK2, GRID))

app.layout = html.Div(className="wrap", children=[
    html.H1("EcoMove City Transport Authority - Mobility Performance"),
    html.P("Senior management view of demand, reliability, finance, accessibility and "
           "sustainability across 12 European cities (Jan 2024 - Dec 2025). "
           "Use the filters to focus on any city, mode, route type, weather or event day.",
           className="lede"),
    html.Div(className="filters", children=[
        html.Div([html.Label("Date range", className="flabel"),
                  dcc.DatePickerRange(id="dates", min_date_allowed=df.Date.min(),
                                      max_date_allowed=df.Date.max(),
                                      start_date=df.Date.min(), end_date=df.Date.max(),
                                      display_format="DD MMM YYYY")]),
        dropdown("country", "Country", "Country"),
        dropdown("city", "City", "City"),
        dropdown("mode", "Transport mode", "Transport_Mode"),
        dropdown("route", "Route type", "Route_Type"),
        dropdown("weather", "Weather", "Weather"),
        dropdown("event", "Event day", "Event_Day"),
    ]),
    html.Div(className="kpis", children=[
        kpi("k-pass", "Passengers"), kpi("k-fin", "Cost recovery"),
        kpi("k-rel", "On-time performance"), kpi("k-sat", "Customer rating"),
        kpi("k-co2", "CO2 saved"), kpi("k-acc", "Accessibility complaints"),
        kpi("k-rev", "Ticket revenue"), kpi("k-delay", "Average delay"),
    ]),
    html.Div(className="grid", children=[
        html.Div(dcc.Graph(id="g-trend"), className="card wide"),
        html.Div(dcc.Graph(id="g-city"), className="card"),
        html.Div(dcc.Graph(id="g-country"), className="card"),
        html.Div(dcc.Graph(id="g-mode"), className="card"),
        html.Div(dcc.Graph(id="g-weather"), className="card"),
        html.Div(dcc.Graph(id="g-access"), className="card"),
        html.Div(dcc.Graph(id="g-co2"), className="card"),
    ]),
])


def filter_df(start, end, country, city, mode, route, weather, event):
    d = df[(df.Date >= start) & (df.Date <= end)]
    for col, sel in [("Country", country), ("City", city), ("Transport_Mode", mode), ("Route_Type", route),
                     ("Weather", weather), ("Event_Day", event)]:
        if sel:
            d = d[d[col].isin(sel)]
    return d


def empty(title):
    f = go.Figure()
    f.add_annotation(text="No records match these filters", showarrow=False,
                     font=dict(size=14, color=INK2))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return style(f, title)


@app.callback(
    [Output(i, "children") for i in
     ["k-pass", "k-pass-sub", "k-fin", "k-fin-sub", "k-rel", "k-rel-sub",
      "k-sat", "k-sat-sub", "k-co2", "k-co2-sub", "k-acc", "k-acc-sub",
      "k-rev", "k-rev-sub", "k-delay", "k-delay-sub"]] +
    [Output(i, "figure") for i in
     ["g-trend", "g-city", "g-country", "g-mode", "g-weather", "g-access", "g-co2"]],
    [Input("dates", "start_date"), Input("dates", "end_date"),
     Input("country", "value"), Input("city", "value"), Input("mode", "value"), Input("route", "value"),
     Input("weather", "value"), Input("event", "value")])
def update(start, end, country, city, mode, route, weather, event):
    d = filter_df(start, end, country, city, mode, route, weather, event)
    titles = ["Monthly passengers and average delay", "Passenger demand by city",
              "Demand and cost recovery by country",
              "Cost recovery by transport mode", "Delay distribution by weather",
              "Accessibility complaints per 10,000 passengers by route type",
              "CO2 saved by city and transport mode (tonnes)"]
    if d.empty:
        return ["-", "no data"] * 8 + [empty(t) for t in titles]

    pax, rev, cost = d.Passengers.sum(), d.Ticket_Revenue_EUR.sum(), d.Operating_Cost_EUR.sum()
    comp = d.Accessibility_Complaints.sum()
    kpis = [
        f"{pax/1e6:.2f}m", f"{len(d):,} service records",
        f"{rev/cost:.2f}", f"{'surplus' if rev >= cost else 'deficit'} {eur(abs(rev - cost))}",
        f"{d.On_Time_Percentage.mean():.1f}%", "mean on-time share",
        f"{d.Customer_Rating.mean():.2f} / 5", "mean rating",
        f"{d.CO2_Saved_KG.sum()/1e3:,.0f} t", f"{d.CO2_Saved_KG.sum()/pax*1000:.0f} kg per 1,000 pax",
        f"{comp:,}", f"{comp/pax*1e4:.1f} per 10,000 passengers",
        eur(rev), f"cost {eur(cost)}",
        f"{d.Average_Delay_Minutes.mean():.2f} min", "mean delay per record",
    ]

    # 1. Trend: passengers (bars) with delay as a separate small panel
    m = d.groupby("Month").agg(P=("Passengers", "sum"), D=("Average_Delay_Minutes", "mean")).reset_index()
    from plotly.subplots import make_subplots
    f1 = make_subplots(rows=1, cols=2, column_widths=[0.62, 0.38], horizontal_spacing=0.08,
                       subplot_titles=("Passengers (millions)", "Average delay (min)"))
    f1.add_trace(go.Scatter(x=m.Month, y=m.P / 1e6, mode="lines+markers", line=dict(color=BLUE, width=2),
                            hovertemplate="%{x|%b %Y}<br>%{y:.2f}m passengers<extra></extra>"), 1, 1)
    f1.add_trace(go.Scatter(x=m.Month, y=m.D, mode="lines+markers", line=dict(color=ORANGE, width=2),
                            hovertemplate="%{x|%b %Y}<br>%{y:.2f} min<extra></extra>"), 1, 2)
    f1.update_annotations(font=dict(size=12, color=INK2))
    f1 = style(f1, titles[0], 320)

    # 2. City demand
    c = d.groupby("City").agg(P=("Passengers", "sum"), OT=("On_Time_Percentage", "mean")).reset_index().sort_values("P")
    f2 = px.bar(c, x="P", y="City", orientation="h", custom_data=["OT"])
    f2.update_traces(marker_color=BLUE, hovertemplate="%{y}<br>%{x:,.0f} passengers<br>On-time %{customdata[0]:.1f}%<extra></extra>")
    f2 = style(f2, titles[1], 380)
    f2.update_layout(xaxis_title="Passengers", yaxis_title=None)

    # 2b. Country comparison: passengers per country, cost recovery in hover and label
    k = d.groupby("Country").agg(P=("Passengers", "sum"), R=("Ticket_Revenue_EUR", "sum"),
                                 C=("Operating_Cost_EUR", "sum"), N=("City", "nunique"),
                                 RT=("Customer_Rating", "mean")).reset_index()
    k["CR"] = k.R / k.C
    k = k.sort_values("P")
    fc = go.Figure(go.Bar(x=k.P / 1e6, y=k.Country, orientation="h", marker_color=AQUA,
                          text=[f"CR {v:.2f}" for v in k.CR], textposition="outside",
                          customdata=k[["N", "CR", "RT"]],
                          hovertemplate="%{y}<br>%{x:.2f}m passengers across %{customdata[0]} cities"
                                        "<br>Cost recovery %{customdata[1]:.2f}<br>Rating %{customdata[2]:.2f}<extra></extra>"))
    fc = style(fc, titles[2], 380)
    fc.update_layout(xaxis_title="Passengers (millions)  ·  label = cost-recovery ratio",
                     xaxis_range=[0, k.P.max() / 1e6 * 1.25])

    # 3. Cost recovery by mode
    t = d.groupby("Transport_Mode").agg(R=("Ticket_Revenue_EUR", "sum"), C=("Operating_Cost_EUR", "sum")).reset_index()
    t["CR"] = t.R / t.C
    t = t.sort_values("CR")
    f3 = go.Figure(go.Bar(x=t.CR, y=t.Transport_Mode, orientation="h",
                          marker_color=[RED if v < 1 else BLUE for v in t.CR],
                          text=[f"{v:.2f}" for v in t.CR], textposition="outside",
                          hovertemplate="%{y}<br>Cost recovery %{x:.2f}<extra></extra>"))
    f3.add_vline(x=1, line_dash="dash", line_color=INK2,
                 annotation_text="break-even", annotation_position="bottom right")
    f3 = style(f3, titles[3], 380)
    f3.update_layout(xaxis_title="Revenue / operating cost", xaxis_range=[0, max(1.4, t.CR.max() * 1.15)])

    # 4. Delay by weather
    order = d.groupby("Weather").Average_Delay_Minutes.median().sort_values().index.tolist()
    f4 = px.box(d, x="Weather", y="Average_Delay_Minutes", category_orders={"Weather": order})
    f4.update_traces(marker_color=BLUE, line_color=BLUE, fillcolor="rgba(42,120,214,0.25)")
    f4 = style(f4, titles[4])
    f4.update_layout(yaxis_title="Delay (min)", xaxis_title=None)

    # 5. Accessibility complaints rate by route type
    a = d.groupby("Route_Type").agg(C=("Accessibility_Complaints", "sum"), P=("Passengers", "sum")).reset_index()
    a["Rate"] = a.C / a.P * 1e4
    a = a.sort_values("Rate")
    f5 = go.Figure(go.Bar(x=a.Rate, y=a.Route_Type, orientation="h", marker_color=ORANGE,
                          text=[f"{v:.1f}" for v in a.Rate], textposition="outside",
                          hovertemplate="%{y}<br>%{x:.1f} complaints per 10k passengers<extra></extra>"))
    f5 = style(f5, titles[5])
    f5.update_layout(xaxis_title="Complaints per 10,000 passengers", xaxis_range=[0, a.Rate.max() * 1.2])

    # 6. CO2 treemap
    co = d.groupby(["City", "Transport_Mode"]).CO2_Saved_KG.sum().reset_index()
    co["Tonnes"] = co.CO2_Saved_KG / 1e3
    f6 = px.treemap(co, path=[px.Constant("All cities"), "City", "Transport_Mode"], values="Tonnes",
                    color="Tonnes", color_continuous_scale=["#cde2fb", "#5598e7", "#104281"])
    f6.update_traces(hovertemplate="%{label}<br>%{value:,.0f} t CO2 saved<extra></extra>",
                     marker=dict(line=dict(color="white", width=2)))
    f6 = style(f6, titles[6], 420)
    f6.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=50, b=10))

    return kpis + [f1, f2, fc, f3, f4, f5, f6]


if __name__ == "__main__":
    import os
    app.run(debug=False, port=int(os.environ.get("PORT", 8050)))
