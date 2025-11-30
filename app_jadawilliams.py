import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import BytesIO
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="NBA Contract Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1D428A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize SQLite database with NBA data"""
    conn = sqlite3.connect('nba_contracts.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create Players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT,
            team TEXT,
            age INTEGER,
            height TEXT,
            weight INTEGER,
            years_in_league INTEGER,
            draft_year INTEGER,
            draft_position INTEGER
        )
    ''')
    
    # Create Contracts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            team TEXT,
            start_date DATE,
            end_date DATE,
            total_value REAL,
            annual_salary REAL,
            contract_type TEXT,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    ''')
    
    # Create Performance Stats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season TEXT,
            games_played INTEGER,
            minutes_per_game REAL,
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            field_goal_pct REAL,
            three_point_pct REAL,
            free_throw_pct REAL,
            usage_rate REAL,
            win_shares REAL,
            per REAL,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    ''')
    
    # Create Injuries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS injuries (
            injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            injury_type TEXT,
            injury_date DATE,
            return_date DATE,
            games_missed INTEGER,
            recurring BOOLEAN,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    ''')
    
    # Create Teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            city TEXT,
            conference TEXT,
            division TEXT,
            current_payroll REAL,
            salary_cap_space REAL,
            luxury_tax_status TEXT
        )
    ''')
    
    conn.commit()
    return conn

# ============================================================================
# DATA LOADING & SAMPLE DATA
# ============================================================================

def load_sample_data(conn):
    """Load sample NBA data"""
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM players")
    if cursor.fetchone()[0] > 0:
        return
    
    # Sample Players (using real NBA player IDs)
    players = [
        (2544, 'LeBron James', 'SF', 'Los Angeles Lakers', 39, '6-9', 250, 21, 2003, 1),
        (201939, 'Stephen Curry', 'PG', 'Golden State Warriors', 36, '6-2', 185, 15, 2009, 7),
        (203507, 'Giannis Antetokounmpo', 'PF', 'Milwaukee Bucks', 29, '6-11', 243, 11, 2013, 15),
        (203999, 'Nikola Jokic', 'C', 'Denver Nuggets', 29, '6-11', 284, 9, 2014, 41),
        (1629029, 'Luka Doncic', 'PG', 'Dallas Mavericks', 25, '6-7', 230, 6, 2018, 3),
        (203954, 'Joel Embiid', 'C', 'Philadelphia 76ers', 30, '7-0', 280, 9, 2014, 3),
        (201142, 'Kevin Durant', 'SF', 'Phoenix Suns', 36, '6-10', 240, 17, 2007, 2),
        (203081, 'Damian Lillard', 'PG', 'Milwaukee Bucks', 34, '6-2', 195, 12, 2012, 6),
        (202331, 'Kawhi Leonard', 'SF', 'Los Angeles Clippers', 33, '6-7', 225, 13, 2011, 15),
        (1628369, 'Jayson Tatum', 'SF', 'Boston Celtics', 26, '6-8', 210, 7, 2017, 3),
        (1629630, 'Tyrese Haliburton', 'PG', 'Indiana Pacers', 24, '6-5', 185, 4, 2020, 12),
        (1630162, 'Anthony Edwards', 'SG', 'Minnesota Timberwolves', 23, '6-4', 225, 4, 2020, 1),
        (203076, 'Anthony Davis', 'PF', 'Los Angeles Lakers', 31, '6-10', 253, 12, 2012, 1),
        (1628983, 'Shai Gilgeous-Alexander', 'PG', 'Oklahoma City Thunder', 26, '6-6', 195, 6, 2018, 11),
        (1629027, 'Trae Young', 'PG', 'Atlanta Hawks', 26, '6-1', 164, 6, 2018, 5),
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO players VALUES (?,?,?,?,?,?,?,?,?,?)', players)
    
    # Sample Contracts
    contracts = []
    for player_id, name, pos, team, age, ht, wt, yrs, draft_yr, draft_pos in players:
        # Generate realistic contract values
        if age < 26:
            salary = np.random.uniform(25, 40)
        elif age < 30:
            salary = np.random.uniform(35, 52)
        else:
            salary = np.random.uniform(30, 48)
        
        start_date = '2023-07-01'
        end_date = '2027-06-30'
        total_value = salary * 4
        
        contracts.append((player_id, team, start_date, end_date, total_value, salary, 'Max Contract'))
    
    cursor.executemany('''
        INSERT INTO contracts (player_id, team, start_date, end_date, total_value, annual_salary, contract_type)
        VALUES (?,?,?,?,?,?,?)
    ''', contracts)
    
    # Sample Performance Stats (2023-24 season)
    stats = [
        (2544, '2023-24', 71, 35.3, 25.7, 7.3, 8.3, 54.0, 41.0, 75.0, 28.5, 7.2, 25.8),
        (201939, '2023-24', 74, 32.7, 26.4, 4.5, 5.1, 45.0, 40.8, 92.3, 29.2, 8.5, 27.4),
        (203507, '2023-24', 73, 35.2, 30.4, 11.5, 6.5, 61.1, 27.4, 65.7, 35.2, 11.8, 31.2),
        (203999, '2023-24', 79, 34.6, 26.4, 12.4, 9.0, 58.3, 35.9, 81.7, 28.3, 13.7, 29.8),
        (1629029, '2023-24', 70, 37.5, 33.9, 9.2, 9.8, 48.7, 38.2, 78.6, 36.8, 10.2, 28.7),
        (203954, '2023-24', 39, 34.7, 34.7, 11.0, 5.6, 52.9, 38.8, 88.3, 37.1, 9.8, 31.4),
        (201142, '2023-24', 75, 37.2, 27.1, 6.6, 5.0, 52.3, 41.3, 85.6, 30.5, 9.5, 27.8),
        (203081, '2023-24', 58, 35.3, 24.3, 4.2, 7.0, 42.2, 35.4, 92.0, 30.1, 6.8, 23.9),
        (202331, '2023-24', 68, 34.1, 23.7, 6.1, 3.6, 52.5, 41.7, 88.5, 29.8, 7.4, 25.3),
        (1628369, '2023-24', 74, 35.7, 26.9, 8.1, 4.9, 47.1, 37.6, 83.3, 29.6, 8.9, 25.0),
        (1629630, '2023-24', 69, 32.7, 20.1, 3.9, 10.9, 47.7, 36.4, 85.5, 24.8, 7.1, 22.6),
        (1630162, '2023-24', 79, 35.1, 25.9, 5.4, 5.1, 46.1, 35.7, 83.6, 30.2, 8.3, 23.4),
        (203076, '2023-24', 76, 35.5, 24.7, 12.6, 3.5, 55.6, 27.1, 81.6, 28.7, 9.4, 27.8),
        (1628983, '2023-24', 75, 33.9, 30.1, 5.5, 6.2, 53.5, 35.3, 87.4, 33.4, 10.8, 30.2),
        (1629027, '2023-24', 54, 36.2, 25.7, 2.8, 10.8, 43.0, 37.3, 86.0, 32.5, 5.7, 24.1),
    ]
    
    cursor.executemany('''
        INSERT INTO performance_stats (player_id, season, games_played, minutes_per_game, 
        points_per_game, rebounds_per_game, assists_per_game, field_goal_pct, 
        three_point_pct, free_throw_pct, usage_rate, win_shares, per)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', stats)
    
    # Sample Injuries
    injuries = [
        (2544, 'Ankle Sprain', '2024-01-15', '2024-02-01', 8, False),
        (203954, 'Knee Surgery', '2024-02-01', '2024-04-15', 32, True),
        (202331, 'Knee Inflammation', '2023-12-10', '2024-01-05', 12, True),
        (203081, 'Calf Strain', '2024-01-20', '2024-02-28', 18, False),
    ]
    
    cursor.executemany('''
        INSERT INTO injuries (player_id, injury_type, injury_date, return_date, games_missed, recurring)
        VALUES (?,?,?,?,?,?)
    ''', injuries)
    
    # Sample Teams
    teams = [
        ('Los Angeles Lakers', 'Los Angeles', 'Western', 'Pacific', 178.5, -38.5, 'Over Cap'),
        ('Golden State Warriors', 'San Francisco', 'Western', 'Pacific', 192.3, -52.3, 'Luxury Tax'),
        ('Milwaukee Bucks', 'Milwaukee', 'Eastern', 'Central', 168.7, -28.7, 'Over Cap'),
        ('Denver Nuggets', 'Denver', 'Western', 'Northwest', 162.4, -22.4, 'Over Cap'),
        ('Dallas Mavericks', 'Dallas', 'Western', 'Southwest', 155.8, -15.8, 'Under Cap'),
    ]
    
    cursor.executemany('''
        INSERT INTO teams (team_name, city, conference, division, current_payroll, salary_cap_space, luxury_tax_status)
        VALUES (?,?,?,?,?,?,?)
    ''', teams)
    
    conn.commit()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_player_image(player_id):
    """Fetch player image from NBA.com"""
    url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except:
        pass
    return None

def calculate_value_index(row):
    """Calculate player value index (0-100)"""
    # Normalize stats
    ppg_norm = min(row['points_per_game'] / 35, 1) * 30
    per_norm = min(row['per'] / 35, 1) * 25
    ws_norm = min(row['win_shares'] / 15, 1) * 20
    efficiency = (row['field_goal_pct'] / 60) * 15
    availability = (row['games_played'] / 82) * 10
    
    value = ppg_norm + per_norm + ws_norm + efficiency + availability
    return round(value, 1)

def calculate_contract_efficiency(stats_df, contracts_df):
    """Calculate contract efficiency rating"""
    merged = pd.merge(stats_df, contracts_df, on='player_id')
    merged['value_index'] = merged.apply(calculate_value_index, axis=1)
    merged['efficiency_rating'] = (merged['value_index'] / merged['annual_salary']) * 10
    return merged

# ============================================================================
# DATABASE QUERY FUNCTIONS
# ============================================================================

@st.cache_data
def get_all_players(_conn):
    """Get all players"""
    return pd.read_sql_query("SELECT * FROM players", _conn)

@st.cache_data
def get_player_stats(_conn):
    """Get player statistics"""
    return pd.read_sql_query("SELECT * FROM performance_stats", _conn)

@st.cache_data
def get_contracts(_conn):
    """Get contract data"""
    return pd.read_sql_query("SELECT * FROM contracts", _conn)

@st.cache_data
def get_injuries(_conn):
    """Get injury data"""
    return pd.read_sql_query("SELECT * FROM injuries", _conn)

@st.cache_data
def get_teams(_conn):
    """Get team data"""
    return pd.read_sql_query("SELECT * FROM teams", _conn)

def get_player_details(_conn, player_id):
    """Get detailed player information"""
    query = f"""
        SELECT p.*, ps.*, c.annual_salary, c.contract_type, c.end_date
        FROM players p
        LEFT JOIN performance_stats ps ON p.player_id = ps.player_id
        LEFT JOIN contracts c ON p.player_id = c.player_id
        WHERE p.player_id = {player_id}
    """
    return pd.read_sql_query(query, _conn)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Initialize database
    conn = init_database()
    load_sample_data(conn)
    
    # Sidebar
    st.sidebar.image("https://cdn.nba.com/logos/leagues/logo-nba.svg", width=100)
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        ["🏠 Dashboard", "👤 Player Database", "📊 Analytics", "💰 Contract Manager", 
         "🏥 Injury Tracker", "💬 SQL Chat"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Database Stats")
    players_df = get_all_players(conn)
    st.sidebar.metric("Total Players", len(players_df))
    st.sidebar.metric("Active Contracts", len(get_contracts(conn)))
    st.sidebar.metric("Total Injuries", len(get_injuries(conn)))
    
    # Main content
    if page == "🏠 Dashboard":
        show_dashboard(conn)
    elif page == "👤 Player Database":
        show_player_database(conn)
    elif page == "📊 Analytics":
        show_analytics(conn)
    elif page == "💰 Contract Manager":
        show_contract_manager(conn)
    elif page == "🏥 Injury Tracker":
        show_injury_tracker(conn)
    elif page == "💬 SQL Chat":
        show_sql_chat(conn)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def show_dashboard(conn):
    st.markdown('<h1 class="main-header">🏀 NBA Contract Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    players_df = get_all_players(conn)
    stats_df = get_player_stats(conn)
    contracts_df = get_contracts(conn)
    
    # Merge data
    merged_df = pd.merge(players_df, stats_df, on='player_id')
    merged_df = pd.merge(merged_df, contracts_df, on='player_id')
    merged_df['value_index'] = merged_df.apply(calculate_value_index, axis=1)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payroll", f"${merged_df['annual_salary'].sum():.1f}M")
    with col2:
        st.metric("Avg Contract Value", f"${merged_df['annual_salary'].mean():.1f}M")
    with col3:
        st.metric("Top Performer", merged_df.loc[merged_df['value_index'].idxmax(), 'name'])
    with col4:
        avg_value = merged_df['value_index'].mean()
        st.metric("Avg Value Index", f"{avg_value:.1f}")
    
    st.markdown("---")
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌟 Top 5 Performers by Value Index")
        top_performers = merged_df.nlargest(5, 'value_index')[['name', 'team', 'value_index', 'points_per_game']]
        st.dataframe(top_performers, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("💰 Highest Paid Players")
        top_paid = merged_df.nlargest(5, 'annual_salary')[['name', 'team', 'annual_salary', 'value_index']]
        top_paid['annual_salary'] = top_paid['annual_salary'].apply(lambda x: f"${x:.1f}M")
        st.dataframe(top_paid, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Performance vs Salary")
        fig = px.scatter(
            merged_df,
            x='annual_salary',
            y='value_index',
            size='points_per_game',
            color='position',
            hover_data=['name', 'team'],
            title='Player Value Analysis',
            labels={'annual_salary': 'Annual Salary ($M)', 'value_index': 'Value Index'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Position Distribution")
        position_counts = merged_df['position'].value_counts()
        fig = px.pie(
            values=position_counts.values,
            names=position_counts.index,
            title='Players by Position'
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: PLAYER DATABASE
# ============================================================================

def show_player_database(conn):
    st.title("👤 Player Database")
    
    players_df = get_all_players(conn)
    stats_df = get_player_stats(conn)
    contracts_df = get_contracts(conn)
    
    # Merge data
    full_df = pd.merge(players_df, stats_df, on='player_id')
    full_df = pd.merge(full_df, contracts_df, on='player_id')
    full_df['value_index'] = full_df.apply(calculate_value_index, axis=1)
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("🔍 Search by Name", "")
    with col2:
        filter_position = st.selectbox("Position", ["All"] + sorted(full_df['position'].unique().tolist()))
    with col3:
        filter_team = st.selectbox("Team", ["All"] + sorted(full_df['team'].unique().tolist()))
    
    # Apply filters
    filtered_df = full_df.copy()
    if search_name:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_name, case=False)]
    if filter_position != "All":
        filtered_df = filtered_df[filtered_df['position'] == filter_position]
    if filter_team != "All":
        filtered_df = filtered_df[filtered_df['team'] == filter_team]
    
    st.markdown("---")
    
    # Display player cards
    st.subheader(f"📋 Players ({len(filtered_df)} found)")
    
    for idx, row in filtered_df.iterrows():
        with st.expander(f"**{row['name']}** - {row['position']} | {row['team']}"):
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                img = get_player_image(row['player_id'])
                if img:
                    st.image(img, use_container_width=True)
                else:
                    st.write("🏀")
            
            with col2:
                st.markdown("**Personal Info**")
                st.write(f"Age: {row['age']}")
                st.write(f"Height: {row['height']}")
                st.write(f"Weight: {row['weight']} lbs")
                st.write(f"Experience: {row['years_in_league']} years")
                st.write(f"Draft: {row['draft_year']} (Pick #{row['draft_position']})")
            
            with col3:
                st.markdown("**2023-24 Stats**")
                st.write(f"PPG: {row['points_per_game']:.1f}")
                st.write(f"RPG: {row['rebounds_per_game']:.1f}")
                st.write(f"APG: {row['assists_per_game']:.1f}")
                st.write(f"FG%: {row['field_goal_pct']:.1f}%")
                st.write(f"PER: {row['per']:.1f}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Annual Salary", f"${row['annual_salary']:.1f}M")
            with col2:
                st.metric("Value Index", f"{row['value_index']:.1f}", 
                         delta=f"{row['value_index'] - full_df['value_index'].mean():.1f} vs avg")

# ============================================================================
# PAGE: ANALYTICS
# ============================================================================

def show_analytics(conn):
    st.title("📊 Advanced Analytics")
    
    players_df = get_all_players(conn)
    stats_df = get_player_stats(conn)
    contracts_df = get_contracts(conn)
    
    # Merge data
    full_df = pd.merge(players_df, stats_df, on='player_id')
    full_df = pd.merge(full_df, contracts_df, on='player_id')
    full_df['value_index'] = full_df.apply(calculate_value_index, axis=1)
    full_df['efficiency_rating'] = (full_df['value_index'] / full_df['annual_salary']) * 10
    
    tab1, tab2, tab3 = st.tabs(["💎 Value Analysis", "📈 Performance Trends", "🎯 Position Comparison"])
    
    with tab1:
        st.subheader("Contract Efficiency Analysis")
        
        # Efficiency scatter
        fig = px.scatter(
            full_df,
            x='annual_salary',
            y='value_index',
            size='points_per_game',
            color='efficiency_rating',
            hover_data=['name', 'team', 'position'],
            title='Player Value vs Contract (Size = PPG, Color = Efficiency)',
            labels={'annual_salary': 'Annual Salary ($M)', 'value_index': 'Value Index'},
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔥 Best Value Contracts**")
            best_value = full_df.nlargest(5, 'efficiency_rating')[['name', 'annual_salary', 'value_index', 'efficiency_rating']]
            best_value['annual_salary'] = best_value['annual_salary'].apply(lambda x: f"${x:.1f}M")
            best_value['efficiency_rating'] = best_value['efficiency_rating'].apply(lambda x: f"{x:.2f}")
            st.dataframe(best_value, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**⚠️ Overvalued Contracts**")
            worst_value = full_df.nsmallest(5, 'efficiency_rating')[['name', 'annual_salary', 'value_index', 'efficiency_rating']]
            worst_value['annual_salary'] = worst_value['annual_salary'].apply(lambda x: f"${x:.1f}M")
            worst_value['efficiency_rating'] = worst_value['efficiency_rating'].apply(lambda x: f"{x:.2f}")
            st.dataframe(worst_value, hide_index=True, use_container_width=True)
    
    with tab2:
        st.subheader("Performance Metrics Distribution")
        
        metric = st.selectbox("Select Metric", 
                             ['points_per_game', 'rebounds_per_game', 'assists_per_game', 
                              'field_goal_pct', 'per', 'win_shares'])
        
        fig = px.histogram(
            full_df,
            x=metric,
            nbins=20,
            title=f'{metric.replace("_", " ").title()} Distribution',
            labels={metric: metric.replace("_", " ").title()}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Box plot by position
        fig = px.box(
            full_df,
            x='position',
            y=metric,
            title=f'{metric.replace("_", " ").title()} by Position',
            labels={metric: metric.replace("_", " ").title()}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Position-Based Analysis")
        
        # Average stats by position
        position_stats = full_df.groupby('position').agg({
            'points_per_game': 'mean',
            'rebounds_per_game': 'mean',
            'assists_per_game': 'mean',
            'annual_salary': 'mean',
            'value_index': 'mean'
        }).round(2)
        
        st.dataframe(position_stats, use_container_width=True)
        
        # Radar chart for selected player
        selected_player = st.selectbox("Select Player for Radar Chart", full_df['name'].tolist())
        player_data = full_df[full_df['name'] == selected_player].iloc[0]
        
        categories = ['PPG', 'RPG', 'APG', 'FG%', 'PER']
        values = [
            player_data['points_per_game'] / 35 * 100,
            player_data['rebounds_per_game'] / 15 * 100,
            player_data['assists_per_game'] / 12 * 100,
            player_data['field_goal_pct'] / 60 * 100,
            player_data['per'] / 35 * 100
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=selected_player
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title=f"{selected_player} Performance Radar"
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: CONTRACT MANAGER
# ============================================================================

def show_contract_manager(conn):
    st.title("💰 Contract Manager")
    
    tab1, tab2 = st.tabs(["📋 View Contracts", "➕ Add/Edit Contract"])
    
    with tab1:
        contracts_df = get_contracts(conn)
        players_df = get_all_players(conn)
        
        # Merge for display
        display_df = pd.merge(contracts_df, players_df[['player_id', 'name', 'position']], on='player_id')
        display_df = display_df[['name', 'position', 'team', 'annual_salary', 'total_value', 
                                 'start_date', 'end_date', 'contract_type']]
        display_df = display_df.sort_values('annual_salary', ascending=False)
        
        # Display contracts
        st.dataframe(
            display_df.style.format({
                'annual_salary': '${:.1f}M',
                'total_value': '${:.1f}M'
            }),
            hide_index=True,
            use_container_width=True
        )
        
        # Contract summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Contracts", len(contracts_df))
        with col2:
            st.metric("Total Annual Spend", f"${contracts_df['annual_salary'].sum():.1f}M")
        with col3:
            st.metric("Avg Contract", f"${contracts_df['annual_salary'].mean():.1f}M")
    
    with tab2:
        st.subheader("Add New Contract")
        
        players_df = get_all_players(conn)
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_player_name = st.selectbox("Select Player", players_df['name'].tolist())
            player_id = players_df[players_df['name'] == selected_player_name]['player_id'].values[0]
            team = st.text_input("Team", players_df[players_df['name'] == selected_player_name]['team'].values[0])
            contract_type = st.selectbox("Contract Type", 
                                        ["Max Contract", "Veteran Extension", "Rookie Contract", 
                                         "Mid-Level Exception", "Minimum Contract"])
        
        with col2:
            start_date = st.date_input("Start Date", datetime.now())
            years = st.slider("Contract Length (years)", 1, 5, 4)
            end_date = start_date + timedelta(days=365 * years)
            st.write(f"End Date: {end_date}")
            annual_salary = st.number_input("Annual Salary ($M)", min_value=1.0, max_value=60.0, value=30.0, step=0.5)
            total_value = annual_salary * years
            st.write(f"**Total Value:** ${total_value:.1f}M")
        
        if st.button("💾 Save Contract", type="primary"):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contracts (player_id, team, start_date, end_date, total_value, annual_salary, contract_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (int(player_id), team, str(start_date), str(end_date), total_value, annual_salary, contract_type))
            conn.commit()
            st.success(f"✅ Contract added for {selected_player_name}!")
            st.cache_data.clear()
            st.rerun()

# ============================================================================
# PAGE: INJURY TRACKER
# ============================================================================

def show_injury_tracker(conn):
    st.title("🏥 Injury Tracker")
    
    injuries_df = get_injuries(conn)
    players_df = get_all_players(conn)
    
    # Merge data
    injury_display = pd.merge(injuries_df, players_df[['player_id', 'name', 'team']], on='player_id')
    
    tab1, tab2 = st.tabs(["📊 Injury Overview", "➕ Add Injury Record"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Injuries", len(injuries_df))
        with col2:
            st.metric("Total Games Missed", injuries_df['games_missed'].sum())
        with col3:
            recurring_count = injuries_df['recurring'].sum()
            st.metric("Recurring Injuries", recurring_count)
        
        st.markdown("---")
        
        # Recent injuries
        st.subheader("Recent Injuries")
        recent_injuries = injury_display.sort_values('injury_date', ascending=False)
        st.dataframe(
            recent_injuries[['name', 'team', 'injury_type', 'injury_date', 'return_date', 'games_missed', 'recurring']],
            hide_index=True,
            use_container_width=True
        )
        
        # Injury type distribution
        st.subheader("Injury Types Distribution")
        injury_types = injuries_df['injury_type'].value_counts()
        fig = px.bar(
            x=injury_types.index,
            y=injury_types.values,
            labels={'x': 'Injury Type', 'y': 'Count'},
            title='Most Common Injuries'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Add Injury Record")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_player = st.selectbox("Player", players_df['name'].tolist())
            player_id = players_df[players_df['name'] == selected_player]['player_id'].values[0]
            injury_type = st.text_input("Injury Type", "Ankle Sprain")
            injury_date = st.date_input("Injury Date", datetime.now())
        
        with col2:
            return_date = st.date_input("Expected Return Date", datetime.now() + timedelta(days=14))
            games_missed = st.number_input("Games Missed", min_value=0, value=5, step=1)
            recurring = st.checkbox("Recurring Injury")
        
        if st.button("💾 Save Injury Record", type="primary"):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO injuries (player_id, injury_type, injury_date, return_date, games_missed, recurring)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (int(player_id), injury_type, str(injury_date), str(return_date), games_missed, recurring))
            conn.commit()
            st.success("✅ Injury record added!")
            st.cache_data.clear()
            st.rerun()

# ============================================================================
# PAGE: SQL CHAT
# ============================================================================

def show_sql_chat(conn):
    st.title("💬 SQL Chat Interface")
    
    st.markdown("""
    Ask questions about the database in natural language. The system will translate your 
    question into SQL and execute it.
    """)
    
    # Example questions
    with st.expander("📝 Example Questions"):
        st.markdown("""
        - Show me all players making over $40M per year
        - Who are the top 5 scorers?
        - Which players have recurring injuries?
        - What's the average salary by position?
        - Show me all point guards under 25 years old
        """)
    
    # Query input
    user_query = st.text_area("Ask a question about the NBA database:", height=100)
    
    if st.button("🔍 Search", type="primary"):
        if user_query:
            with st.spinner("Translating and executing query..."):
                # Simple query translation (in production, use LLM)
                sql_query = translate_natural_to_sql(user_query)
                
                st.code(sql_query, language='sql')
                
                try:
                    result_df = pd.read_sql_query(sql_query, conn)
                    st.subheader("Results:")
                    st.dataframe(result_df, use_container_width=True)
                    
                    st.download_button(
                        "📥 Download Results (CSV)",
                        result_df.to_csv(index=False),
                        "query_results.csv",
                        "text/csv"
                    )
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")
        else:
            st.warning("Please enter a question!")
    
    # Show database schema
    with st.expander("📚 Database Schema"):
        st.markdown("""
        **Tables:**
        - `players`: player_id, name, position, team, age, height, weight, years_in_league, draft_year, draft_position
        - `contracts`: contract_id, player_id, team, start_date, end_date, total_value, annual_salary, contract_type
        - `performance_stats`: stat_id, player_id, season, games_played, minutes_per_game, points_per_game, rebounds_per_game, assists_per_game, field_goal_pct, three_point_pct, free_throw_pct, usage_rate, win_shares, per
        - `injuries`: injury_id, player_id, injury_type, injury_date, return_date, games_missed, recurring
        - `teams`: team_id, team_name, city, conference, division, current_payroll, salary_cap_space, luxury_tax_status
        """)

def translate_natural_to_sql(query):
    """Simple rule-based translation (replace with LLM in production)"""
    query_lower = query.lower()
    
    # Simple pattern matching
    if "over" in query_lower and "million" in query_lower or "$" in query_lower:
        # Extract amount
        import re
        amount = re.findall(r'\d+', query_lower)
        if amount:
            amount = amount[0]
            return f"""
                SELECT p.name, p.position, p.team, c.annual_salary
                FROM players p
                JOIN contracts c ON p.player_id = c.player_id
                WHERE c.annual_salary > {amount}
                ORDER BY c.annual_salary DESC
            """
    
    elif "top" in query_lower and "scorer" in query_lower:
        amount = "5"
        import re
        nums = re.findall(r'\d+', query_lower)
        if nums:
            amount = nums[0]
        return f"""
            SELECT p.name, p.team, ps.points_per_game
            FROM players p
            JOIN performance_stats ps ON p.player_id = ps.player_id
            ORDER BY ps.points_per_game DESC
            LIMIT {amount}
        """
    
    elif "recurring" in query_lower and "injur" in query_lower:
        return """
            SELECT p.name, p.team, i.injury_type, i.games_missed
            FROM players p
            JOIN injuries i ON p.player_id = i.player_id
            WHERE i.recurring = 1
        """
    
    elif "average salary" in query_lower and "position" in query_lower:
        return """
            SELECT p.position, AVG(c.annual_salary) as avg_salary, COUNT(*) as player_count
            FROM players p
            JOIN contracts c ON p.player_id = c.player_id
            GROUP BY p.position
            ORDER BY avg_salary DESC
        """
    
    elif "point guard" in query_lower and "under" in query_lower:
        import re
        age = re.findall(r'\d+', query_lower)
        if age:
            age = age[0]
            return f"""
                SELECT p.name, p.age, p.team, ps.points_per_game, ps.assists_per_game
                FROM players p
                JOIN performance_stats ps ON p.player_id = ps.player_id
                WHERE p.position = 'PG' AND p.age < {age}
                ORDER BY ps.assists_per_game DESC
            """
    
    # Default fallback
    return "SELECT * FROM players LIMIT 10"

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
