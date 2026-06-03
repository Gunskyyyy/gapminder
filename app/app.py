import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.title('Gapminder')
st.write("Unlocking Lifetimes: Visualizing Progress in Longevity and Poverty Eradication")

@st.cache_data
def load_data():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    pop = pd.read_csv(os.path.join(BASE_DIR, 'sp_pop_totl.csv'))
    lex = pd.read_csv(os.path.join(BASE_DIR, 'lex.csv'))
    gni = pd.read_csv(os.path.join(BASE_DIR, 'gnicap_atm_con.csv'))

    def to_tidy(df, value_name):
        df = df.set_index(df.columns[0])
        df = df.ffill(axis=1)
        df = df.reset_index()
        df = df.melt(id_vars=df.columns[0], var_name='year', value_name=value_name)
        df.columns = ['country', 'year', value_name]
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['year'])
        df[value_name] = pd.to_numeric(df[value_name], errors='coerce')
        df['year'] = df['year'].astype(int)
        return df

    pop_tidy = to_tidy(pop, 'population')
    lex_tidy = to_tidy(lex, 'life_expectancy')
    gni_tidy = to_tidy(gni, 'gni_per_capita')

    df = pop_tidy.merge(lex_tidy, on=['country', 'year'])
    df = df.merge(gni_tidy, on=['country', 'year'])
    df = df.dropna()
    return df

df = load_data()

years = sorted(df['year'].unique())
countries = sorted(df['country'].unique())

# Session state
if 'year_index' not in st.session_state:
    st.session_state.year_index = 0
if 'playing' not in st.session_state:
    st.session_state.playing = False

# Controls
selected_countries = st.multiselect('Countries', countries, default=list(countries[:10]))

col1, col2 = st.columns([1, 8])
with col1:
    if st.button('▶ Play' if not st.session_state.playing else '⏸ Pause'):
        st.session_state.playing = not st.session_state.playing

with col2:
    selected_year = st.slider('Year', min_value=min(years), max_value=max(years),
                               value=years[st.session_state.year_index])
    st.session_state.year_index = years.index(selected_year)

# Chart
max_gni = df['gni_per_capita'].max()
filtered = df[(df['year'] == years[st.session_state.year_index]) &
              (df['country'].isin(selected_countries))]

fig = px.scatter(
    filtered,
    x='gni_per_capita',
    y='life_expectancy',
    size='population',
    color='country',
    hover_name='country',
    log_x=True,
    size_max=60,
    range_x=[100, max_gni * 1.1],
    range_y=[20, 90],
    labels={
        'gni_per_capita': 'GNI per Capita (PPP, log scale)',
        'life_expectancy': 'Life Expectancy'
    },
    title=f'Gapminder {years[st.session_state.year_index]}'
)

st.plotly_chart(fig, width='stretch')

# Animation loop
if st.session_state.playing:
    time.sleep(0.5)
    st.session_state.year_index = (st.session_state.year_index + 1) % len(years)
    st.rerun()