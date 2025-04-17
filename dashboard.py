import numpy as np
from io import StringIO
import panel as pn
import hvplot.pandas
import pandas as pd
import holoviews as hv
from bokeh.models import HoverTool


pn.extension("tabulator")
hv.renderer("bokeh").theme = "light_minimal"


# data extraction
def create_scenario_graphs():
    def read_data():
        file_path = "/Users/carlos.canales/projects/simbev/artifacts/simbev_public_installed_charging_power_and_yearly_energy.csv"
        df = pd.read_csv(file_path)
        return df

    source_data = read_data()

    # Widgets
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

    # df for table
    df_table = pn.rx(filter_data_table)(
        scenario=scenario_selector, luc=luc_selector, unit=unit_selector
    )
    # df_plot = pn.rx(filter_data_plot)(luc=luc_selector, unit=unit_selector)
    df_plot = hvplot.bind(
        filter_data_plot, luc=luc_selector, unit=unit_selector
    ).interactive()

    def filtered_file(scenario, luc, unit):
        df = filter_data_table(scenario, luc, unit)
        sio = StringIO()
        df.to_csv(sio)
        sio.seek(0)
        return sio

    fd = pn.widgets.FileDownload(
        callback=pn.bind(
            filtered_file,
            scenario=scenario_selector,
            luc=luc_selector,
            unit=unit_selector,
        ),
        filename="data.csv",
    )

    hover = HoverTool(
        tooltips=[
            ("Szenario", "@scenario"),
            ("Jahr", "@year"),
            ("Werte", "@value{0.0,0}"),
        ]
    )

    # fig = df_plot.hvplot.scatter(
    #     x='year', y='value', by='scenario',
    #     title=f'Unit: {unit_selector.value} - LUC: {luc_selector.value}',
    #     legend='top_left',
    #     tools=[hover],
    #     responsive=True,
    #     muted_alpha=0,
    #     yformatter='%.0f'
    # ).opts(legend_opts={"click_policy": "hide"})

    # legend as a single row under the graph

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

    # line graph that join the scatter points
    fig = fig_line * fig_scatter

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

    fig = fig.opts(hooks=[modify_legend, sort_legend], show_grid=True, axiswise=True)

    # creating components
    # plot = pn.pane.HoloViews(fig, sizing_mode='stretch_both', name='plot')
    table = pn.widgets.Tabulator(df_table, name="table", sizing_mode="scale_both")

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

    unit_selector.param.watch(update_luc_selector, "value")

    widgets = pn.Row(
        scenario_selector, unit_selector, luc_selector, sizing_mode="scale_width"
    )

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
    # pn.extension(global_css=[':root { --design-background-color: purple; }'])

    # dashboard.show()
    # dashboard.save("/Users/carlos.canales/projects/hosting/carlosrodrigo5.github.io/index.html", embed=True)


def create_sensitivity_analysis_graph():
    def read_data():
        file_path = "/Users/carlos.canales/projects/simbev/artifacts/simbev_sensitivity_analysis.csv"
        df = pd.read_csv(file_path)
        return df

    reference = pd.read_csv(
        "/Users/carlos.canales/projects/simbev/artifacts/simbev_public_installed_charging_power_and_yearly_energy.csv"
    )
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

    source_data = read_data()
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

    # Widgets
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
        # if luc and len(luc) > 0:
        #     data = data[data['LUC'] == luc]
        # data =
        return source_data[
            (source_data["unit"] == unit)
            & (source_data["LUC"] == luc)
            & (source_data["parameter"] == parameter)
        ].set_index(["parameter"])
        # fig = df_plot.hvplot.scatter(
        #     x='year', y='value', by='scenario',
        #     title=f'Unit: {unit_selector.value} - LUC: {luc_selector.value}',
        #     legend='top_left',
        #     tools=[hover],
        #     responsive=True,
        #     muted_alpha=0,
        #     yformatter='%.0f'
        # ).opts(legend_opts={"click_policy": "hide"})

    # df for table
    df_table = pn.rx(filter_data_table)(
        parameter=parameter_selector, luc=luc_selector, unit=unit_selector
    )
    # df_plot = pn.rx(filter_data_plot)(luc=luc_selector, unit=unit_selector)
    df_plot = hvplot.bind(
        filter_data_plot,
        parameter=parameter_selector,
        luc=luc_selector,
        unit=unit_selector,
    ).interactive()

    def filtered_file(parameter, luc, unit):
        df = filter_data_table(parameter, luc, unit)
        sio = StringIO()
        df.to_csv(sio)
        sio.seek(0)
        return sio

    fd = pn.widgets.FileDownload(
        callback=pn.bind(
            filtered_file,
            parameter=parameter_selector,
            luc=luc_selector,
            unit=unit_selector,
        ),
        filename="data.csv",
    )

    hover = HoverTool(
        tooltips=[
            ("Parameter", "@parameter"),
            ("Werte", "@value{0.0,0}"),
            ("LUC", "@LUC"),
        ]
    )

    fig = df_plot.hvplot.bar(
        x="variable",
        y="value",
        title=f"",
        ylabel="Werte",
        xlabel="Variabel",
        color="color",
        # tools=[hover],
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

    table = pn.widgets.Tabulator(df_table, name="table", sizing_mode="scale_both")

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

    unit_selector.param.watch(update_luc_selector, "value")

    widgets = pn.Row(
        parameter_selector, unit_selector, luc_selector, sizing_mode="scale_width"
    )

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
    # pn.extension(global_css=[':root { --design-background-color: purple; }'])

    # dashboard.show()
    # dashboard.save("/Users/carlos.canales/projects/hosting/carlosrodrigo5.github.io/index.html", embed=True)


############################# WIDGETS & CALLBACK ###########################################

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


def create_page1():
    obj = create_scenario_graphs()
    return pn.Column(
        # pn.pane.Markdown("## Dataset Explorer"),
        obj,
        align="center",
    )


def create_page2():
    obj = create_sensitivity_analysis_graph()
    return pn.Column(
        # pn.pane.Markdown("## Dataset Explorer"),
        obj,
        align="center",
    )


mapping = {
    "Page1": create_page1,
    "Page2": create_page2,
}

global main_area
main_area = pn.Column(mapping["Page1"], styles={"width": "100%"})


# def show_page(page_key):
#     global main_area
#     main_area.clear()
#     main_area.append(mapping[page_key])

#
# button1.on_click(lambda event: show_page("Page1"))
# button2.on_click(lambda event: show_page("Page2"))



button1.on_click(lambda event: (main_area.clear(), main_area.append(mapping["Page1"])))
button2.on_click(lambda event: (main_area.clear(), main_area.append(mapping["Page2"])))

button1.js_on_click(
    args={},
    code="""
    window.location.reload();
""",
)
button2.js_on_click(
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

# starting_page = pn.state.session_args.get("page", [b"Page2"])[0].decode()
# sidebar = pn.widgets.RadioButtonGroup(
#     value=starting_page,
#     options=list(mapping.keys()),
#     name="Page",
#     sizing_mode="fixed",
#     button_type="success",
# )


# def show(page):
#     return mapping[page]
#
#
# main_area = pn.bind(show, page=sidebar)
# sidebar.param.watch(show, 'value')
# pn.state.location.sync(sidebar, {'value': 'page'})


#################### MAIN LAYOUT ##########################
# main = pn.Column(
#     pn.pane.Markdown("## Dashboard"),
#     create_page1(),
#     sizing_mode="stretch_width",
# )

################### MAIN AREA LAYOUT ##########################


#################### TEMPLATE LAYOUT ##########################
# template = pn.template.FastListTemplate(
#     title="SimBeV Dashboard",
#     sidebar=sidebar,
#     main=[main_area],
#     theme=pn.template.theme,
#     header_background="#f0f0f0",
#     header_color="#000000",
#     header_font_size="20px",
#     sidebar_width=200,
# )

template = pn.template.FastListTemplate(
    title="SimBEV Ergebnisse",
    sidebar=[sidebar],
    main=[main_area],
    header_background="black",
    theme=pn.template.DarkTheme,
    sidebar_width=250,  ## Default is 330
    busy_indicator=None,
)

template.show()
