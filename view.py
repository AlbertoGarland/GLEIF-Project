import streamlit as st
import pandas as pd
import plotly.express as px

from repository import (get_directories, set_data, get_config)
from helper_exposition import exposition


def to_streamlit(config: dict):
    st.set_page_config(page_title=config['streamlit']['page_title'],
                       layout=config['streamlit']['layout'])
    st.title(config['streamlit']['page_title'])

    # Met en cache certaines data
    @st.cache_data
    def get_processed_data():
        directories = get_directories(config['files']['names'])
        resultat = set_data(directories)
        GLEIF_Country = exposition(data=resultat, indice=config['rates']['names'])
        GLEIF_Company = exposition(data=resultat, indice=config['rates']['names'], scale=[True])
        return GLEIF_Country, GLEIF_Company

    # Met en cache certaines data
    @st.cache_data
    def get_filtered_data(data, exposition_type, top_bottom, num_countries, ratio_col):
        filtered_data = data[data['Index'] == exposition_type]
        if filtered_data.empty:
            return pd.DataFrame()
        if top_bottom == "Top":
            filtered_data = filtered_data.nlargest(num_countries, ratio_col)
        else:
            filtered_data = filtered_data.nsmallest(num_countries, ratio_col)
        return filtered_data

    # Charge et traite les données
    GLEIF_Country, GLEIF_Company = get_processed_data()

    st.header(config['streamlit']['sub_title'])
    st.header(config['streamlit']['scatter_plot_title'])

    # Choisir l'exposition
    exposition_type = st.selectbox(
        config['streamlit']['select_exposition_type_label'],
        config['rates']['names']
    )

    # Selectionner le nombre de top ou bottom pays dans une catégorie
    top_bottom = st.radio(
        config['streamlit']['show_top_bottom_label'],
        ("Top", "Bottom")
    )

    num_countries = st.slider(
        config['streamlit']['select_num_countries_label'],
        min_value=1,
        max_value=50,
        value=10
    )

    # Filtrer selon la selection
    x_col = config['columns']['gross_exposure']
    y_col = config['columns']['net_exposure']
    size_col = config['columns']['gross_exposure']
    ratio_col = config['columns']['ratio']

    filtered_data = get_filtered_data(GLEIF_Country, exposition_type, top_bottom, num_countries, ratio_col)
    if filtered_data.empty:
        st.error(f"No data available for {exposition_type}.")
        return

    additional_countries = st.multiselect(
        config['streamlit']['add_more_countries_label'],
        options=GLEIF_Country['Country'].unique(),
        default=filtered_data['Country'].tolist()
    )

    # Vérification des critères de séléctions
    selected_countries = set(filtered_data['Country']).union(additional_countries)
    final_filtered_data = GLEIF_Country[
        GLEIF_Country['Country'].isin(selected_countries) & (GLEIF_Country['Index'] == exposition_type)
        ]

    if final_filtered_data.empty:
        st.error(f"No data available for the selected options.")
        return

    # Scatter plot : one country and one index
    fig = px.scatter(
        final_filtered_data,
        x=x_col,
        y=y_col,
        size=size_col,
        color='Country',
        hover_name='Country',
        title=config['plot_titles']['scatter'],
        labels={
            x_col: config['axis_labels']['gross_exposure'],
            y_col: config['axis_labels']['net_exposure'],
            size_col: config['axis_labels']['gross_exposure']
        }
    )

    fig.update_layout(
        title=f"{top_bottom} {num_countries} Countries by {exposition_type} Exposition Ratio",
        legend_title_text=config['axis_labels']['legend_countries'],
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title=config['axis_labels']['gross_exposure'],
        yaxis_title=config['axis_labels']['net_exposure']
    )

    fig.update_traces(
        hovertemplate=config['hover_templates']['scatter'],
        customdata=final_filtered_data[[ratio_col]].to_numpy()
    )

    st.plotly_chart(fig)

    st.subheader(config['streamlit']['final_filtered_data_subheader'])
    st.dataframe(final_filtered_data)

    # Display les data pour toutes les expositions
    for rate in config['rates']['names']:
        rate_data = GLEIF_Country[GLEIF_Country['Index'] == rate]

        if not rate_data.empty:
            st.header(f"{config['streamlit']['highest_exposition_label']} {rate}")
            top_exposition = rate_data.nlargest(5, ratio_col)
            st.dataframe(top_exposition.loc[:, ["Country", x_col, y_col, ratio_col]])

            st.header(f"{config['streamlit']['lowest_exposition_label']} {rate}")
            lowest_exposition = rate_data.nsmallest(5, ratio_col)
            st.dataframe(lowest_exposition.loc[:, ["Country", x_col, y_col, ratio_col]])

    st.header(config['streamlit']['company_analysis_title'])

    # Histogramme: one country and one index
    st.subheader(config['streamlit']['histogram_plot_title'])
    selected_country = st.selectbox(config['streamlit']['select_country_label'], GLEIF_Company['Country'].unique())
    selected_index = st.selectbox(config['streamlit']['select_index_label'], config['rates']['names'])

    company_data = GLEIF_Company[(GLEIF_Company['Country'] == selected_country) &
                                 (GLEIF_Company['Index'] == selected_index)]

    if company_data.empty:
        st.error(f"No data available for {selected_country} and {selected_index}.")
    else:
        # Classe par ratio
        company_data = company_data.sort_values(by=ratio_col, ascending=False)
        fig_company_hist = px.histogram(
            company_data,
            x="Name",
            y=ratio_col,
            color='Name',
            title=f"{selected_country} - {selected_index} Exposition Ratios by Company",
            labels={
                ratio_col: config['axis_labels']['ratio'],
                "Name": "Company"
            }
        )

        fig_company_hist.update_layout(
            title=f"{selected_country} - {selected_index} Exposition Ratios by Company",
            legend_title_text=config['axis_labels']['legend_companies'],
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis_title="Company",
            yaxis_title=config['axis_labels']['ratio'],
            autosize=True,
            width=None,
            height=None,
            xaxis_tickvals=[],
        )

        fig_company_hist.update_traces(
            hovertemplate=config['hover_templates']['histogram']
        )

        st.plotly_chart(fig_company_hist)

    # Deuxième scatter plot: multiple countries for one index
    st.subheader(config['streamlit']['scatter_plot_multiple_title'])
    selected_countries_multi = st.multiselect(config['streamlit']['select_countries_label'],
                                              GLEIF_Company['Country'].unique())
    selected_index_multi = st.selectbox(config['streamlit']['select_index_multiple_label'], config['rates']['names'],
                                        key='multi')

    company_data_multi = GLEIF_Company[(GLEIF_Company['Country'].isin(selected_countries_multi)) &
                                       (GLEIF_Company['Index'] == selected_index_multi)]

    if company_data_multi.empty:
        st.error(f"No data available for the selected countries and {selected_index_multi}.")
    else:
        fig_company_multi = px.scatter(
            company_data_multi,
            x=x_col,
            y=y_col,
            size=size_col,
            color='Country',
            hover_name='Name',
            title=config['plot_titles']['scatter_multiple'],
            labels={
                x_col: config['axis_labels']['gross_exposure'],
                y_col: config['axis_labels']['net_exposure'],
                size_col: config['axis_labels']['gross_exposure']
            }
        )

        fig_company_multi.update_layout(
            title=f"{selected_index_multi} Exposition Ratios by Company",
            legend_title_text=config['axis_labels']['legend_countries'],
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis_title=config['axis_labels']['gross_exposure'],
            yaxis_title=config['axis_labels']['net_exposure']
        )

        fig_company_multi.update_traces(
            hovertemplate=config['hover_templates']['scatter'],
            customdata=company_data_multi[[ratio_col]].to_numpy()
        )

        st.plotly_chart(fig_company_multi)

    # Troisième Scatter Plot: one or multiple countries, two indices
    st.subheader(config['streamlit']['scatter_plot_two_indices_title'])
    selected_countries_two_indices = st.multiselect(config['streamlit']['select_countries_two_label'],
                                                    GLEIF_Company['Country'].unique(), key='two')
    index1 = st.selectbox(config['streamlit']['select_first_index_label'], config['rates']['names'], key='index1')
    index2 = st.selectbox(config['streamlit']['select_second_index_label'], config['rates']['names'], key='index2')

    company_data_index1 = GLEIF_Company[(GLEIF_Company['Country'].isin(selected_countries_two_indices)) &
                                        (GLEIF_Company['Index'] == index1)]
    company_data_index2 = GLEIF_Company[(GLEIF_Company['Country'].isin(selected_countries_two_indices)) &
                                        (GLEIF_Company['Index'] == index2)]

    if company_data_index1.empty or company_data_index2.empty:
        st.error(f"No data available for the selected countries and indices.")
    else:
        company_data_index1['Index_Color'] = index1
        company_data_index2['Index_Color'] = index2

        combined_data = pd.concat([company_data_index1, company_data_index2])

        fig_two_indices = px.scatter(
            combined_data,
            x=x_col,
            y=y_col,
            size=size_col,
            color='Index_Color',
            hover_name='Name',
            title=f"{index1} vs {index2} Exposition Ratios by Company",
            labels={
                x_col: config['axis_labels']['gross_exposure'],
                y_col: config['axis_labels']['net_exposure'],
                size_col: config['axis_labels']['gross_exposure'],
                'Index_Color': 'Index'
            },
            color_discrete_map={
                index1: config['colors']['index1'],
                index2: config['colors']['index2']
            }
        )

        fig_two_indices.update_layout(
            title=f"{index1} vs {index2} Exposition Ratios by Company",
            legend_title_text=config['axis_labels']['legend_index'],
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis_title=config['axis_labels']['gross_exposure'],
            yaxis_title=config['axis_labels']['net_exposure']
        )

        fig_two_indices.update_traces(
            hovertemplate=config['hover_templates']['scatter'],
            customdata=combined_data[[ratio_col]].to_numpy()
        )

        st.plotly_chart(fig_two_indices)

    #  Deuxième histogramme plot for Cash_Flow
    st.header(config['streamlit']['cash_flow_analysis_title'])
    st.subheader(config['streamlit']['cash_flow_histogram_title'])

    # Selectionner le nombre de Top/Bottom
    top_bottom_cash = st.radio(
        config['streamlit']['show_top_bottom_label'],
        ("Top", "Bottom"),
        key='cash_flow'
    )

    num_countries_cash = st.slider(
        config['streamlit']['select_num_countries_label'],
        min_value=1,
        max_value=50,
        value=10,
        key='cash_flow_slider'
    )

    # Filtrer les data en fonction des séléctions
    cash_flow_col = config['columns']['cash_flow']

    filtered_data_cash = GLEIF_Country.copy()
    if top_bottom_cash == "Top":
        filtered_data_cash = filtered_data_cash.nlargest(num_countries_cash, cash_flow_col)
    else:
        filtered_data_cash = filtered_data_cash.nsmallest(num_countries_cash, cash_flow_col)

    additional_countries_cash = st.multiselect(
        config['streamlit']['add_more_countries_label'],
        options=GLEIF_Country['Country'].unique(),
        default=filtered_data_cash['Country'].tolist(),
        key='cash_flow_multiselect'
    )

    # Vérification de la séléction
    selected_countries_cash = set(filtered_data_cash['Country']).union(additional_countries_cash)
    final_filtered_data_cash = GLEIF_Country[
        GLEIF_Country['Country'].isin(selected_countries_cash)
    ]

    if final_filtered_data_cash.empty:
        st.error(f"No data available for the selected options.")
        return

    # Tri par niveau de Cash Flow
    final_filtered_data_cash = final_filtered_data_cash.sort_values(by=cash_flow_col,
                                                                    ascending=(top_bottom_cash == "Bottom"))

    # Histogramme
    fig_cash_flow = px.histogram(
        final_filtered_data_cash,
        x='Country',
        y=cash_flow_col,
        color='Country',
        title=f"{top_bottom_cash} {num_countries_cash} Countries by Cash Flow",
        labels={
            'Country': "Country",
            cash_flow_col: config['axis_labels']['cash_flow']
        }
    )

    fig_cash_flow.update_layout(
        title=f"{top_bottom_cash} {num_countries_cash} Countries by Cash Flow",
        legend_title_text=config['axis_labels']['legend_countries'],
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title="Country",
        yaxis_title=config['axis_labels']['cash_flow']
    )

    fig_cash_flow.update_traces(
        hovertemplate=config['hover_templates']['histogram_cash_flow']
    )

    st.plotly_chart(fig_cash_flow)

# Chargement Streamlit
if __name__ == "__main__":
    config = get_config()
    to_streamlit(config)
