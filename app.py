import pandas as pd
import calendar as cal
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc



# PREPARATION DONNEES --------------------------
df = pd.read_csv("data.csv")

cols = [
    "CustomerID",
    "Gender",
    "Location",
    "Product_Category",
    "Quantity",
    "Avg_Price",
    "Transaction_Date",
    "Month",
    "Discount_pct"
]

df = df[cols].copy()
df["CustomerID"] = df["CustomerID"].fillna(0).astype(int)
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
df["Total_price"] = df["Quantity"] * df["Avg_Price"] * (1 - df["Discount_pct"] / 100)

CURRENT_MONTH = 12


# FONCTIONS ----------------------------
def meilleure_vente(data, top=10, ascending=False):
    freq = (
        data.groupby("Product_Category")["Quantity"]
        .sum()
        .sort_values(ascending=ascending)
    )
    return freq.head(top)


def indicateur_du_mois(data, current_month=12, freq=True, abbr=False):
    data_mois = data[data["Month"] == current_month]

    if freq:
        result = data_mois["Quantity"].sum()
    else:
        result = data_mois["Total_price"].sum()

    month_name = cal.month_abbr[current_month] if abbr else cal.month_name[current_month]
    return month_name, result


def barplot_top_10_ventes(data, current_month=12):
    data_mois = data[data["Month"] == current_month].copy()

    top = meilleure_vente(data_mois, top=10, ascending=False).reset_index()

    data_top = data_mois[data_mois["Product_Category"].isin(top["Product_Category"])]

    ventes = (
        data_top.groupby(["Product_Category", "Gender"])["Quantity"]
        .sum()
        .reset_index()
    )

    ventes["Product_Category"] = pd.Categorical(
        ventes["Product_Category"],
        categories=top["Product_Category"].tolist(),
        ordered=True
    )
    ventes = ventes.sort_values("Product_Category", ascending=True)

    fig = px.bar(
        ventes,
        x="Quantity",
        y="Product_Category",
        color="Gender",
        barmode="group",
        title="Frequence des 10 meilleures ventes",
        labels={
            "Product_Category": "Catégorie du produit",
            "Quantity": "Total vente",
            "Gender": "Sexe"
        },
        color_discrete_map={
            "F": "#636EFA",
            "M": "#EF553B"
        },
        category_orders={
            "Product_Category": top["Product_Category"].tolist(),
            "Gender": ["F", "M"]
        }
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="#E5ECF6",
        plot_bgcolor="#E5ECF6",
        legend_title_text="Sexe",
        title_font=dict(size=14),
        font=dict(size=11)
    )

    return fig


def plot_evolution_chiffre_affaire(data):
    data_copy = data.copy().set_index("Transaction_Date")
    evolution = data_copy["Total_price"].resample("W").sum().reset_index()

    fig = px.line(
        evolution,
        x="Transaction_Date",
        y="Total_price",
        title="Evolution du chiffre d'affaire par semaine",
        labels={
            "Transaction_Date": "Semaine",
            "Total_price": "Chiffre d'affaire"
        }
    )

    fig.update_traces(line=dict(color="#636EFA", width=2))

    fig.update_layout(
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="#E5ECF6",
        plot_bgcolor="#E5ECF6",
        title_font=dict(size=14),
        font=dict(size=11)
    )
    return fig


def plot_chiffre_affaire_mois(data, current_month):
    previous_month = 12 if current_month == 1 else current_month - 1

    mois_courant = indicateur_du_mois(
        data, current_month=current_month, freq=False, abbr=False
    )
    mois_precedent = indicateur_du_mois(
        data, current_month=previous_month, freq=False, abbr=False
    )

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            value=mois_courant[1],
            mode="number+delta",
            number={"valueformat": ".3s"},
            delta={
                "reference": mois_precedent[1],
                "valueformat": ".3s"
            },
            title={"text": f"{mois_courant[0]}"}
        )
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=25, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#2a3f5f")
    )

    return fig


def plot_vente_mois(data, current_month, abbr=False):
    previous_month = 12 if current_month == 1 else current_month - 1

    mois_courant = indicateur_du_mois(
        data, current_month=current_month, freq=True, abbr=abbr
    )
    mois_precedent = indicateur_du_mois(
        data, current_month=previous_month, freq=True, abbr=abbr
    )

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=mois_courant[1],
            delta={"reference": mois_precedent[1]},
            title={"text": f"{mois_courant[0]}"}
        )
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=25, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#2a3f5f")
    )

    return fig


def table_last_100(data, current_month):
    df_last_100 = (
        data[data["Month"] == current_month]
        .sort_values("Transaction_Date", ascending=False)
        .head(100)
        .copy()
    )

    df_last_100["Date"] = df_last_100["Transaction_Date"].dt.strftime("%Y-%m-%d")

    df_last_100 = df_last_100[
        [
            "Date",
            "Gender",
            "Location",
            "Product_Category",
            "Quantity",
            "Avg_Price",
            "Discount_pct"
        ]
    ]

    return df_last_100



# TABLEAU DE BORD ------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

zone_options = [
    {"label": z, "value": z}
    for z in sorted(df["Location"].dropna().unique())
]

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        html.H1(
                            "ECAP Store",
                            style={
                                "margin": "0",
                                "fontSize": "24px",
                                "fontWeight": "700",
                                "color": "#1f2d3d"
                            }
                        ),
                        style={
                            "height": "100%",
                            "display": "flex",
                            "alignItems": "center",
                            "paddingLeft": "12px",
                            "backgroundColor": "#c7e6ef"
                        }
                    ),
                    md=6
                ),
                dbc.Col(
                    html.Div(
                        dcc.Dropdown(
                            id="zone-dropdown",
                            options=zone_options,
                            value=None,
                            clearable=True,
                            placeholder="Choisissez des zones",
                            style={"width": "330px"}
                        ),
                        style={
                            "height": "100%",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "backgroundColor": "#c7e6ef"
                        }
                    ),
                    md=6
                ),
            ],
            className="g-0",
            style={"height": "7vh"}
        ),
# INDICATEURS 
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id="ca-mois",
                                        config={"displayModeBar": False},
                                        style={"height": "100%"}
                                    ),
                                    md=6,
                                    style={"height": "100%", "padding": "10px"}
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="vente-mois",
                                        config={"displayModeBar": False},
                                        style={"height": "100%"}
                                    ),
                                    md=6,
                                    style={"height": "100%", "padding": "10px"}
                                ),
                            ],
                            className="g-0",
                            style={"height": "25vh"}
                        ),
# BARPLOT TOP 10 VENTES
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id="top-10-ventes",
                                        config={"displayModeBar": False},
                                        style={"height": "100%"}
                                    ),
                                    md=12,
                                    style={"height": "100%", "padding": "10px"}
                                ),
                            ],
                            className="g-0",
                            style={"height": "68vh"}
                        ),
                    ],
                    md=5
                ),
# GRAPH EVOLUTION CA
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        id="evolution-ca",
                                        config={"displayModeBar": False},
                                        style={"height": "100%"}
                                    ),
                                    md=12,
                                    style={"height": "100%", "padding": "10px"}
                                ),
                            ],
                            className="g-0",
                            style={"height": "48vh"}
                        ),
# TABLE 100 VENTES
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H4(
                                                "Table des 100 dernières ventes",
                                                style={
                                                    "margin": "0 0 8px 0",
                                                    "fontSize": "18px",
                                                    "fontWeight": "600"
                                                }
                                            ),
                                            html.Div(
                                                dash_table.DataTable(
                                                    id="table-last-100",
                                                    page_size=10,
                                                    page_action="native",
                                                    sort_action="native",
                                                    filter_action="native",
                                                    style_table={
                                                        "width": "100%",
                                                        "overflowX": "auto",
                                                        "overflowY": "auto",
                                                        "maxHeight": "34vh"
                                                    },
                                                    style_cell={
                                                        "textAlign": "center",
                                                        "padding": "4px",
                                                        "fontFamily": "Arial",
                                                        "fontSize": "12px",
                                                        "minWidth": "88px",
                                                        "width": "88px",
                                                        "maxWidth": "140px",
                                                        "whiteSpace": "nowrap",
                                                        "border": "1px solid #D6D6D6"
                                                    },
                                                    style_header={
                                                        "fontWeight": "bold",
                                                        "backgroundColor": "#F6F6F6",
                                                        "border": "1px solid #D6D6D6",
                                                        "fontSize": "12px"
                                                    },
                                                    style_data={
                                                        "backgroundColor": "white",
                                                        "border": "1px solid #E1E1E1"
                                                    },
                                                    css=[
                                                        {
                                                            "selector": ".dash-spreadsheet-menu",
                                                            "rule": "display: none;"
                                                        }
                                                    ]
                                                ),
                                                style={
                                                    "flex": "1",
                                                    "overflow": "auto"
                                                }
                                            )
                                        ],
                                    ),
                                    md=12,
                                    style={"height": "100%"}
                                ),
                            ],
                            className="g-0",
                            style={"height": "45vh"}
                        ),
                    ],
                    md=7
                ),
            ],
            className="g-0",
            style={"height": "93vh"}
        ),
    ],
    fluid=True,
    className="p-0",
    style={
        "height": "100vh",
        "backgroundColor": "white",
        "overflow": "hidden"
    }
)


# CALLBACK ---------------------------
@app.callback(
    Output("ca-mois", "figure"),
    Output("vente-mois", "figure"),
    Output("top-10-ventes", "figure"),
    Output("evolution-ca", "figure"),
    Output("table-last-100", "data"),
    Output("table-last-100", "columns"),
    Input("zone-dropdown", "value")
)
def update_dashboard(selected_zone):
    data_filtered = df.copy()

    if selected_zone:
        data_filtered = data_filtered[data_filtered["Location"] == selected_zone]

    fig_ca = plot_chiffre_affaire_mois(data_filtered, CURRENT_MONTH)
    fig_ventes = plot_vente_mois(data_filtered, CURRENT_MONTH, False)
    fig_top = barplot_top_10_ventes(data_filtered, CURRENT_MONTH)
    fig_evolution = plot_evolution_chiffre_affaire(data_filtered)

    table_df = table_last_100(data_filtered, CURRENT_MONTH)

    return (
        fig_ca,
        fig_ventes,
        fig_top,
        fig_evolution,
        table_df.to_dict("records"),
        [{"name": c.replace("_", " "), "id": c} for c in table_df.columns]
    )


if __name__ == "__main__":
    app.run(debug=False, port=8055, jupyter_mode="external")