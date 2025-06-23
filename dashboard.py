import os

import numpy as np
from io import StringIO
import panel as pn
import hvplot.pandas
import pandas as pd
import holoviews as hv
from bokeh.models import HoverTool
import boto3
import io


pn.extension("tabulator")
hv.renderer("bokeh").theme = "light_minimal"


# s3 = boto3.client(
#     "s3",
#     region_name=os.environ.get("REGION"),
#     aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
#     aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
# )
#
#
# def read_parquet_from_s3(path):
#     bucket = path.split("/")[2]
#     key = "/".join(path.split("/")[3:])
#     obj = s3.get_object(Bucket=bucket, Key=key)
#     df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
#     return df


simbev_results = pd.read_parquet(
    "data/simbev_public_installed_charging_power_and_yearly_energy.parquet"
)
ss_analysis = pd.read_parquet("data/simbev_sensitivity_analysis.parquet")


def create_scenario_graphs():
    # --------------- Functions -----------
    def filter_data_table(scenario, luc, unit):
        data = source_data.copy()
        data["year"] = data["year"].astype(int).astype(str)
        data["value"] = data["value"].round(2)
        if scenario != "Alle":
            data = data[data["scenario"] == scenario]
        if luc and len(luc) > 0:
            data = data[data["LUC"] == luc]
        data = data[data["unit"] == unit].reset_index(drop=True)
        return data

    def filter_data_plot(luc, unit):
        # if luc and len(luc) > 0:
        #     data = data[data['LUC'] == luc]
        # data =
        return source_data[
            (source_data["unit"] == unit) & (source_data["LUC"] == luc)
        ].set_index(["scenario", "year"])
        # fig = df_plot.hvplot.scatter(
        #     x='year', y='value', by='scenario',
        #     title=f'Unit: {unit_selector.value} - LUC: {luc_selector.value}',
        #     legend='top_left',
        #     tools=[hover],
        #     responsive=True,
        #     muted_alpha=0,
        #     yformatter='%.0f'
        # ).opts(legend_opts={"click_policy": "hide"})

    def get_filtered_file(scenario, luc, unit):
        df = filter_data_table(scenario, luc, unit)
        sio = StringIO()
        df.to_csv(sio)
        sio.seek(0)
        return sio

    def modify_legend(plot, element):
        if hasattr(plot.state, "legend"):
            for legend in plot.state.legend:
                legend.title = "Szenario"  # Set legend title
                legend.title_text_font_size = "12pt"  # Customize title size
                legend.title_text_font_style = "bold"  # Set title style
                legend.border_line_color = "black"  # Add a border
                legend.background_fill_color = "white"  # Change background
                legend.title_text_align = "center"
                legend.label_standoff = 10  # Adjust spacing to simulate centering
                legend.spacing = 5  # Control spacing between legend items
                legend.margin = 0  # Adjust legend padding
                legend.location = (-80, 0)  # Adjust legend position

    def sort_legend(plot, element):
        plot.handles["plot"].legend[0].items.reverse()

    # update luc_selector options based on unit selection
    def update_luc_selector(event):
        if event.new == "MW":
            luc_selector.options = list(
                source_data[source_data["unit"] == "MW"]["LUC"].unique()
            )
        elif event.new == "GWh/year":
            luc_selector.options = list(
                source_data[source_data["unit"] == "GWh/year"]["LUC"].unique()
            )
        else:
            luc_selector.options = list(source_data["LUC"].unique())

    # --------------- Read Data  -----------

    source_data = simbev_results.copy()

    # -------------- Create Widgets --------------
    scenario_selector = pn.widgets.Select(
        name="Szenario \n (nur für Tabelle)",
        options=["Alle"] + list(source_data["scenario"].unique()),
        height=80,
        sizing_mode="scale_width",
    )
    unit_selector = pn.widgets.Select(
        name="Unit",
        options=list(source_data["unit"].unique())[::-1],
        height=80,
        sizing_mode="scale_width",
    )
    luc_selector = pn.widgets.Select(
        name="LUC",
        options=list(source_data["LUC"].unique()),
        height=80,
        sizing_mode="scale_width",
    )

    widgets = pn.Row(
        scenario_selector, unit_selector, luc_selector, sizing_mode="scale_width"
    )

    # --------------- Data Filtering --------------
    df_table = pn.rx(filter_data_table)(
        scenario=scenario_selector, luc=luc_selector, unit=unit_selector
    )
    df_plot = hvplot.bind(
        filter_data_plot, luc=luc_selector, unit=unit_selector
    ).interactive()

    # --------------- Create Plots --------------
    hover = HoverTool(
        tooltips=[
            ("Szenario", "@scenario"),
            ("Jahr", "@year"),
            ("Werte", "@value{0.0,0}"),
        ]
    )

    fig_line = df_plot.hvplot.line(
        x="year",
        y="value",
        by="scenario",
        title=f"",
        ylabel="Werte",
        xlabel="Jahr",
        legend="bottom",
        tools=[hover],
        responsive=True,
        muted_alpha=0,
    ).opts(
        legend_opts={
            "click_policy": "hide",
        },
        fontsize={
            "title": 16,
            "labels": 14,
            "xticks": 12,
            "yticks": 12,
            "legend": 12,
            "legend_title": 10,
        },
        legend_cols=2,
        # height=700,
    )

    fig_scatter = df_plot.hvplot.scatter(
        x="year",
        y="value",
        by="scenario",
        title=f"",
        ylabel="Werte",
        xlabel="Jahr",
        legend="bottom",
        tools=[hover],
        responsive=True,
        muted_alpha=0,
    ).opts(
        legend_opts={
            "click_policy": "hide",
        },
        fontsize={
            "title": 16,
            "labels": 14,
            "xticks": 12,
            "yticks": 12,
            "legend": 12,
            "legend_title": 10,
        },
        legend_cols=3,
        # height=700,
    )

    fig = fig_line * fig_scatter
    fig = fig.opts(hooks=[modify_legend, sort_legend], show_grid=True, axiswise=True)

    # ------------------- Create Table --------------
    table = pn.widgets.Tabulator(df_table, name="table", sizing_mode="scale_both")

    fd = pn.widgets.FileDownload(  # FileDownload widget to download the filtered data
        callback=pn.bind(
            get_filtered_file,
            scenario=scenario_selector,
            luc=luc_selector,
            unit=unit_selector,
        ),
        filename="data.csv",
    )

    # ------------------- Update Widgets --------------
    unit_selector.param.watch(update_luc_selector, "value")

    # ------------------- Create Dashboard --------------
    dashboard = pn.Row(
        pn.Column(
            # pn.pane.Markdown("### Charging Power Trends"),
            widgets,
            fig.output(),  #
            max_width=1000,
            height=700,
            width_policy="max",
        ),
        pn.Column(
            # empty_table.DataFrame(df, height=300),
            fd,
            table,
            sizing_mode="scale_both",
        ),
    )

    return dashboard


def create_sensitivity_analysis_graph():
    # --------------- Functions --------------
    def filter_data_table(parameter, luc, unit):
        data = source_data.copy()
        data["value"] = data["value"].round(2)
        if parameter != "Alle":
            data = data[data["parameter"] == parameter]
        if luc and len(luc) > 0:
            data = data[data["LUC"] == luc]
        data = data[data["unit"] == unit].reset_index(drop=True)
        return data.drop(columns=["color"])

    def filter_data_plot(parameter, luc, unit):
        return source_data[
            (source_data["unit"] == unit)
            & (source_data["LUC"] == luc)
            & (source_data["parameter"] == parameter)
        ].set_index(["parameter"])

    def get_filtered_file(parameter, luc, unit):
        df = filter_data_table(parameter, luc, unit)
        sio = StringIO()
        df.to_csv(sio)
        sio.seek(0)
        return sio

    # update luc_selector options based on unit selection
    def update_luc_selector(event):
        if event.new == "MW":
            luc_selector.options = list(
                source_data[source_data["unit"] == "MW"]["LUC"].unique()
            )
        elif event.new == "GWh/year":
            luc_selector.options = list(
                source_data[source_data["unit"] == "GWh/year"]["LUC"].unique()
            )
        else:
            luc_selector.options = list(source_data["LUC"].unique())

    # --------------- Data Preparation -----------
    reference = simbev_results.copy()
    reference = reference[
        (reference["scenario"] == "Referenzszenario") & (reference["year"] == 2030)
    ]
    reference_1 = reference.copy()
    reference_2 = reference.copy()

    reference["parameter"] = "Mehrverbrauch"
    reference_1["parameter"] = "Ladeleistung"
    reference_2["parameter"] = "Batterie"
    reference = pd.concat([reference, reference_1, reference_2], axis=0)
    reference["variable"] = "Referenzszenario 2030"

    source_data = ss_analysis.copy()
    source_data["parameter"] = source_data["case"].apply(lambda x: x.split("_")[0])
    source_data["variable"] = source_data["case"].apply(lambda x: x.split("_")[1])

    source_data.drop(columns=["case", "year"], inplace=True)
    source_data = source_data[["LUC", "parameter", "variable", "value", "unit"]]

    source_data = pd.concat(
        [source_data, reference[["LUC", "parameter", "variable", "value", "unit"]]],
        axis=0,
    )
    source_data = source_data.sort_values(by=["value"], ascending=[True])

    source_data["color"] = np.where(
        source_data["variable"] == "Referenzszenario 2030", "#e0b90b", "#0b68e0"
    )

    # -------------------- Create Widgets --------------
    parameter_selector = pn.widgets.Select(
        name="Parameter \n (nur für Tabelle)",
        options=list(source_data["parameter"].unique()),
        height=80,
        sizing_mode="scale_width",
    )
    unit_selector = pn.widgets.Select(
        name="Unit",
        options=list(source_data["unit"].unique())[::-1],
        height=80,
        sizing_mode="scale_width",
    )
    luc_selector = pn.widgets.Select(
        name="LUC",
        options=list(source_data["LUC"].unique()),
        height=80,
        sizing_mode="scale_width",
    )

    widgets = pn.Row(
        parameter_selector, unit_selector, luc_selector, sizing_mode="scale_width"
    )

    # ----------------- Data Filtering --------------
    df_table = pn.rx(filter_data_table)(
        parameter=parameter_selector, luc=luc_selector, unit=unit_selector
    )
    df_plot = hvplot.bind(
        filter_data_plot,
        parameter=parameter_selector,
        luc=luc_selector,
        unit=unit_selector,
    ).interactive()

    # ----------------- Create Plots --------------
    hover = HoverTool(
        tooltips=[
            ("Variable", "@variable"),
            ("Werte", "@value{0.0,0}"),
        ]
    )

    fig = df_plot.hvplot.bar(
        x="variable",
        y="value",
        title=f"",
        ylabel="Werte",
        xlabel="Variabel",
        color="color",
        tools=[hover],
        responsive=True,
        muted_alpha=0,
    ).opts(
        fontsize={
            "title": 16,
            "labels": 14,
            "xticks": 12,
            "yticks": 12,
            "legend": 12,
            "legend_title": 10,
        },
        # height=700,
        xrotation=45,
        # width=800
        # height=400
    )

    # ------------ Create Table --------------
    table = pn.widgets.Tabulator(df_table, name="table", sizing_mode="scale_both")

    fd = pn.widgets.FileDownload( # FileDownload widget to download the filtered data
        callback=pn.bind(
            get_filtered_file,
            parameter=parameter_selector,
            luc=luc_selector,
            unit=unit_selector,
        ),
        filename="data.csv",
    )

    # ----------------- Update Widgets --------------
    unit_selector.param.watch(update_luc_selector, "value")

    # ----------------- Create Dashboard --------------
    dashboard = pn.Row(
        pn.Column(
            # pn.pane.Markdown("### Charging Power Trends"),
            widgets,
            fig.output(),  #
            max_width=1000,
            width_policy="max",
            height=700,
        ),
        pn.Column(
            # empty_table.DataFrame(df, height=300),
            fd,
            table,
            sizing_mode="stretch_both",
        ),
    )

    return dashboard


############################# CALLBACKS ####################################

button1 = pn.widgets.Button(
    name="Szenarien",
    button_type="primary",
    icon="chart-histogram",
    styles={"width": "100%"},
)
button2 = pn.widgets.Button(
    name="Sensitivitätsanalyse",
    button_type="warning",
    icon="chart-dots-filled",
    styles={"width": "100%"},
)

dashboard1 = pn.Column(
    pn.pane.Markdown("## Dashboard"),
    create_scenario_graphs(),
    sizing_mode="stretch_width",
)

dashboard2 = pn.Column(
    pn.pane.Markdown("## Dashboard"),
    create_sensitivity_analysis_graph(),
    sizing_mode="stretch_width",
)

############################# MAIN AREA ####################################
main_area = pn.Column(dashboard1, styles={"width": "100%"})


def create_page1():
    global main_area
    main_area.clear()
    main_area.append(dashboard1)


def create_page2():
    global main_area
    main_area.clear()
    main_area.append(dashboard2)

button1.on_click(lambda event: create_page1())
button2.on_click(lambda event: create_page2())

button1.js_on_click(
    args={},
    code="""
    window.location.reload();
""",
)

#################### SIDEBAR LAYOUT ##########################
sidebar = pn.Column(
    pn.pane.Markdown("## Seiten"),
    button1,
    button2,
    styles={"width": "100%", "padding": "15px"},
)


#################### TEMPLATE LAYOUT ##########################
template = pn.template.FastListTemplate(
    title="SimBEV Ergebnisse",
    sidebar=[sidebar],
    main=[main_area],
    header_background="black",
    theme=pn.template.DarkTheme,
    sidebar_width=250,  ## Default is 330
    busy_indicator=None,
)

template.servable()
#template.show()