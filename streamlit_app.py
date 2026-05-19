import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from collections import Counter
import re

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="UK Top 50 Playlist Market Structure Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# TITLE
# =====================================================

st.title("🎵 United Kingdom Top 50 Playlist Market Structure Dashboard")
st.markdown("### Atlantic Recording Corporation Analytics")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_data():

    df = pd.read_csv("Atlantic_United_Kingdom.csv")

    # Convert date
    df['date'] = pd.to_datetime(df['date'])

    # Duration in minutes
    df['duration_min'] = df['duration_ms'] / 60000

    # Explicit label
    df['explicit_label'] = df['is_explicit'].apply(
        lambda x: 'Explicit' if x else 'Clean'
    )

    # Rank groups
    def rank_group(pos):
        if pos <= 10:
            return "Top 10"
        elif pos <= 20:
            return "Top 20"
        else:
            return "Top 50"

    df['rank_group'] = df['position'].apply(rank_group)

    # Normalize artists
    delimiters = r',|&|feat\.|featuring| x '

    def split_artists(artist_string):
        artists = re.split(delimiters, str(artist_string).lower())
        artists = [a.strip().title() for a in artists if a.strip()]
        return artists

    df['artist_list'] = df['artist'].apply(split_artists)

    # Collaboration count
    df['collaboration_count'] = df['artist_list'].apply(len)

    # Track type
    df['track_type'] = df['collaboration_count'].apply(
        lambda x: 'Collaboration' if x > 1 else 'Solo'
    )

    return df


df = load_data()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("🎛 Filters")

# Date range
min_date = df['date'].min()
max_date = df['date'].max()

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date]
)

# Artist filter
all_artists = sorted(list(set(
    artist
    for sublist in df['artist_list']
    for artist in sublist
)))

selected_artists = st.sidebar.multiselect(
    "Select Artist",
    all_artists
)

# Album filter
album_filter = st.sidebar.multiselect(
    "Album Type",
    options=df['album_type'].unique(),
    default=df['album_type'].unique()
)

# Explicit filter
explicit_filter = st.sidebar.multiselect(
    "Explicit / Clean",
    options=df['explicit_label'].unique(),
    default=df['explicit_label'].unique()
)

# Track type filter
track_filter = st.sidebar.multiselect(
    "Solo / Collaboration",
    options=df['track_type'].unique(),
    default=df['track_type'].unique()
)

# =====================================================
# APPLY FILTERS
# =====================================================

filtered_df = df.copy()

# Date filtering
if len(selected_dates) == 2:
    start_date, end_date = selected_dates

    filtered_df = filtered_df[
        (filtered_df['date'] >= pd.to_datetime(start_date)) &
        (filtered_df['date'] <= pd.to_datetime(end_date))
    ]

# Album filter
filtered_df = filtered_df[
    filtered_df['album_type'].isin(album_filter)
]

# Explicit filter
filtered_df = filtered_df[
    filtered_df['explicit_label'].isin(explicit_filter)
]

# Track type filter
filtered_df = filtered_df[
    filtered_df['track_type'].isin(track_filter)
]

# Artist filter
if selected_artists:
    filtered_df = filtered_df[
        filtered_df['artist_list'].apply(
            lambda artists: any(a in artists for a in selected_artists)
        )
    ]

# =====================================================
# KPI CALCULATIONS
# =====================================================

all_artists_flat = [
    artist
    for sublist in filtered_df['artist_list']
    for artist in sublist
]

artist_counts = Counter(all_artists_flat)

unique_artists = len(set(all_artists_flat))

total_entries = len(filtered_df)

collaboration_ratio = round(
    (filtered_df['track_type'] == 'Collaboration').mean() * 100,
    2
)

explicit_share = round(
    (filtered_df['explicit_label'] == 'Explicit').mean() * 100,
    2
)

single_ratio = round(
    (filtered_df['album_type'].str.lower() == 'single').mean() * 100,
    2
)

top_5_share = 0

if len(artist_counts) > 0:
    top_5_share = round(
        (
            sum(dict(artist_counts.most_common(5)).values())
            / total_entries
        ) * 100,
        2
    )

diversity_score = round(
    unique_artists / total_entries,
    2
) if total_entries > 0 else 0

# =====================================================
# KPI SECTION
# =====================================================

st.markdown("## 📌 Executive KPIs")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Unique Artists", unique_artists)
col2.metric("Collaboration Ratio", f"{collaboration_ratio}%")
col3.metric("Explicit Share", f"{explicit_share}%")
col4.metric("Single Ratio", f"{single_ratio}%")
col5.metric("Top 5 Artist Share", f"{top_5_share}%")
col6.metric("Diversity Score", diversity_score)

st.divider()

# =====================================================
# TABS
# =====================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎤 Artist Analysis",
    "🤝 Collaboration",
    "🔞 Explicit Content",
    "💿 Album Analysis",
    "⏱ Duration Insights"
])

# =====================================================
# TAB 1 - ARTIST ANALYSIS
# =====================================================

with tab1:

    st.markdown("## 🎤 Artist Dominance Leaderboard")

    artist_df = pd.DataFrame(
        artist_counts.items(),
        columns=['Artist', 'Appearances']
    )

    artist_df = artist_df.sort_values(
        by='Appearances',
        ascending=False
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.dataframe(
            artist_df.head(15),
            use_container_width=True
        )

    with col2:

        fig_artist = px.bar(
            artist_df.head(15),
            x='Artist',
            y='Appearances',
            title='Top Artists by Playlist Presence',
            text='Appearances'
        )

        st.plotly_chart(
            fig_artist,
            use_container_width=True
        )

# =====================================================
# TAB 2 - COLLABORATION
# =====================================================

with tab2:

    st.markdown("## 🤝 Collaboration Analysis")

    col1, col2 = st.columns(2)

    with col1:

        collab_counts = filtered_df['track_type'].value_counts().reset_index()
        collab_counts.columns = ['Track Type', 'Count']

        fig_collab = px.pie(
            collab_counts,
            names='Track Type',
            values='Count',
            title='Solo vs Collaboration'
        )

        st.plotly_chart(
            fig_collab,
            use_container_width=True
        )

    with col2:

        rank_collab = filtered_df.groupby(
            'rank_group'
        )['collaboration_count'].mean().reset_index()

        fig_rank = px.bar(
            rank_collab,
            x='rank_group',
            y='collaboration_count',
            title='Average Collaborators by Rank Group',
            text='collaboration_count'
        )

        st.plotly_chart(
            fig_rank,
            use_container_width=True
        )

    st.markdown("### 🌐 Collaboration Network")

    G = nx.Graph()

    for artists in filtered_df['artist_list']:

        if len(artists) > 1:

            for i in range(len(artists)):
                for j in range(i + 1, len(artists)):

                    G.add_edge(
                        artists[i],
                        artists[j]
                    )

    if len(G.nodes()) > 0:

        pos = nx.spring_layout(G, seed=42)

        edge_x = []
        edge_y = []

        for edge in G.edges():

            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            hoverinfo='none'
        )

        node_x = []
        node_y = []
        node_text = []

        for node in G.nodes():

            x, y = pos[node]

            node_x.append(x)
            node_y.append(y)
            node_text.append(node)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            hoverinfo='text',
            textposition='top center',
            marker=dict(size=12)
        )

        fig_network = go.Figure(
            data=[edge_trace, node_trace]
        )

        fig_network.update_layout(
            title='Artist Collaboration Network',
            showlegend=False,
            height=700
        )

        st.plotly_chart(
            fig_network,
            use_container_width=True
        )

# =====================================================
# TAB 3 - EXPLICIT CONTENT
# =====================================================

with tab3:

    st.markdown("## 🔞 Explicit Content Analysis")

    col1, col2 = st.columns(2)

    with col1:

        explicit_counts = filtered_df[
            'explicit_label'
        ].value_counts().reset_index()

        explicit_counts.columns = ['Type', 'Count']

        fig_explicit = px.pie(
            explicit_counts,
            names='Type',
            values='Count',
            title='Explicit vs Clean Content'
        )

        st.plotly_chart(
            fig_explicit,
            use_container_width=True
        )

    with col2:

        fig_box = px.box(
            filtered_df,
            x='explicit_label',
            y='position',
            title='Rank Distribution by Content Type'
        )

        st.plotly_chart(
            fig_box,
            use_container_width=True
        )

# =====================================================
# TAB 4 - ALBUM ANALYSIS
# =====================================================

with tab4:

    st.markdown("## 💿 Album Structure Analysis")

    col1, col2 = st.columns(2)

    with col1:

        album_counts = filtered_df[
            'album_type'
        ].value_counts().reset_index()

        album_counts.columns = ['Album Type', 'Count']

        fig_album = px.pie(
            album_counts,
            names='Album Type',
            values='Count',
            title='Single vs Album Distribution'
        )

        st.plotly_chart(
            fig_album,
            use_container_width=True
        )

    with col2:

        fig_tracks = px.scatter(
            filtered_df,
            x='total_tracks',
            y='popularity',
            color='album_type',
            hover_data=['song', 'artist'],
            title='Album Size vs Popularity'
        )

        st.plotly_chart(
            fig_tracks,
            use_container_width=True
        )

# =====================================================
# TAB 5 - DURATION INSIGHTS
# =====================================================

with tab5:

    st.markdown("## ⏱ Track Duration Insights")

    col1, col2 = st.columns(2)

    with col1:

        fig_duration = px.histogram(
            filtered_df,
            x='duration_min',
            nbins=20,
            title='Track Duration Distribution'
        )

        st.plotly_chart(
            fig_duration,
            use_container_width=True
        )

    with col2:

        fig_duration_pop = px.scatter(
            filtered_df,
            x='duration_min',
            y='popularity',
            color='rank_group',
            hover_data=['song', 'artist'],
            title='Duration vs Popularity'
        )

        st.plotly_chart(
            fig_duration_pop,
            use_container_width=True
        )

# =====================================================
# RAW DATA
# =====================================================

st.markdown("## 🗂 Dataset Preview")

st.dataframe(
    filtered_df,
    use_container_width=True
)

# =====================================================
# DOWNLOAD BUTTON
# =====================================================

csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Filtered Dataset",
    data=csv,
    file_name='uk_top50_filtered.csv',
    mime='text/csv'
)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown(
    "### UK Top 50 Playlist Market Structure Dashboard | Atlantic Recording Corporation"
)
