import streamlit as st
import mysql.connector
import pandas as pd
import folium
from streamlit_folium import st_folium

# ============================================================================
# BLOCK 1: PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Restaurant Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# ============================================================================
# BLOCK 2: CUSTOM STYLING (CUSTOMIZATION #1) - PINK & GREEN THEME
# ============================================================================
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
        color: #FF1493;
    }
    .metric-container {
        background: linear-gradient(135deg, #FFB6D9 0%, #B4F8C8 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    /* Pink and Green themed buttons and elements */
    .stButton>button {
        background-color: #FF1493 !important;
        color: white !important;
        border: 2px solid #32CD32 !important;
    }
    .stButton>button:hover {
        background-color: #32CD32 !important;
        border: 2px solid #FF1493 !important;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFE5F0 0%, #E5FFE5 100%);
    }
    /* Headers with pink/green */
    h1, h2, h3 {
        color: #FF1493 !important;
    }
    /* Success messages in green */
    .stSuccess {
        background-color: #B4F8C8 !important;
        color: #006400 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# BLOCK 3: DATABASE CONNECTION
# ============================================================================
@st.cache_resource
def get_database_connection():
    """Establish connection to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='db-mysql-itom-do-user-28250611-0.j.db.ondigitalocean.com',
            port=25060,
            user='restaurant_readonly',
            password='SecurePassword123!',
            database='restaurant'
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"❌ Database connection failed: {err}")
        return None

# Test database connection
conn = get_database_connection()
if conn and conn.is_connected():
    st.sidebar.success("✅ Database connected successfully!")
    # Test query to verify data
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM business_location")
        count = cursor.fetchone()[0]
        st.sidebar.info(f"📊 Total restaurants in DB: {count}")
        cursor.close()
    except Exception as e:
        st.sidebar.error(f"Query test failed: {e}")
else:
    st.sidebar.error("❌ Database connection failed!")

# ============================================================================
# BLOCK 4: HELPER FUNCTIONS
# ============================================================================
def get_vote_range():
    """Get minimum and maximum vote counts from database"""
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(votes) as min_votes, MAX(votes) as max_votes FROM business_location")
            result = cursor.fetchone()
            cursor.close()
            if result and result[0] is not None and result[1] is not None:
                return int(result[0]), int(result[1])
            else:
                st.warning("⚠️ No vote data found in database")
                return 0, 1000
        except Exception as e:
            st.error(f"Error getting vote range: {e}")
            return 0, 1000
    return 0, 1000

def search_restaurants(name_pattern, min_votes, max_votes):
    """Search restaurants based on filters"""
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT name, votes, city 
                FROM business_location 
                WHERE name LIKE %s 
                AND votes BETWEEN %s AND %s 
                ORDER BY votes DESC
            """
            cursor.execute(query, (f'%{name_pattern}%', min_votes, max_votes))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            st.error(f"Database query error: {e}")
            return []
    return []

def get_restaurant_locations():
    """Get restaurant coordinates for map"""
    if conn:
        try:
            query = """
                SELECT name, latitude, longitude 
                FROM business_location 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error loading map data: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# ============================================================================
# BLOCK 5: SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.title("🍽️ Navigation")
tab_selection = st.sidebar.radio(
    "Select a tab:",
    ["📋 HW Summary", "🔍 Database Search", "🗺️ Interactive Map"]
)

# ============================================================================
# TAB 1: HW SUMMARY
# ============================================================================
if tab_selection == "📋 HW Summary":
    st.markdown('<p class="big-font">Restaurant Dashboard - Homework Summary</p>', unsafe_allow_html=True)
    
    # CUSTOMIZATION: Using columns for layout (CUSTOMIZATION #2)
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=150)
    
    with col2:
        st.markdown("### 👤 MSBA STUDENT AT SMU")
        st.write("**Name:** Jada Williams")
        st.write("**Course:** ITOM6265")
        st.write("**Assignment:** Restaurant Dashboard with Streamlit")
        st.write("**Date:** November 2024")
    
    st.markdown("---")
    
    st.markdown("### 🎨 Customizations Implemented")
    
    customizations = {
        "1. Custom CSS Styling - Pink & Green Theme": "Added custom pink and green gradient colors for headers, buttons, sidebar, and metric containers",
        "2. Two-Column Layout": "Used Streamlit columns for better visual organization in Summary tab",
        "3. Custom Map Tiles": "Implemented CartoDB Positron tiles for the interactive map (instead of default OpenStreetMap)",
        "4. Enhanced Data Display": "Color-coded result counts and styled tables with custom pink/green formatting",
        "5. Interactive Widgets": "Added emoji icons and captions for better user experience with pink/green hover effects"
    }
    
    for title, description in customizations.items():
        with st.container():
            st.markdown(f"**{title}**")
            st.info(description)
    
    st.markdown("---")
    st.markdown("### 📊 Dashboard Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database Connection", "Active ✅")
    
    with col2:
        st.metric("Search Filters", "Name + Votes")
    
    with col3:
        st.metric("Map Markers", "Interactive 📍")

# ============================================================================
# TAB 2: DATABASE SEARCH (QUESTION 1 - 40 POINTS)
# ============================================================================
elif tab_selection == "🔍 Database Search":
    st.title("🔍 Restaurant Database Search")
    st.markdown("Search for restaurants by name and vote count")
    
    # Get vote range from database
    min_votes_db, max_votes_db = get_vote_range()
    
    # CUSTOMIZATION: Using columns for input layout (CUSTOMIZATION #2 continued)
    col1, col2 = st.columns(2)
    
    with col1:
        name_input = st.text_input(
            "🏪 Restaurant Name",
            placeholder="Enter restaurant name (e.g., Dishoom)",
            help="Leave empty to show all restaurants"
        )
    
    with col2:
        vote_range = st.slider(
            "📊 Vote Range",
            min_value=int(min_votes_db),
            max_value=int(max_votes_db),
            value=(int(min_votes_db), int(max_votes_db)),
            help="Filter restaurants by number of votes"
        )
    
    # Search button
    search_button = st.button("🔍 Get results", type="primary", use_container_width=True)
    
    if search_button:
        with st.spinner("Searching database..."):
            results = search_restaurants(name_input, vote_range[0], vote_range[1])
            
            if results:
                # CUSTOMIZATION: Enhanced data display with color-coded count (CUSTOMIZATION #3)
                st.success(f"✅ Found {len(results)} restaurant(s)")
                
                # Convert to DataFrame for better display
                df = pd.DataFrame(results, columns=['Restaurant Name', 'Votes', 'City'])
                
                # Display as styled table
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                # Additional statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Results", len(results))
                with col2:
                    st.metric("Avg Votes", f"{df['Votes'].mean():.0f}")
                with col3:
                    st.metric("Max Votes", df['Votes'].max())
                
            else:
                st.warning("⚠️ No restaurants found matching your criteria. Try adjusting the filters.")
    
    # Instructions
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        - **Empty name field**: Shows all restaurants within the vote range
        - **Specific name**: Searches for restaurants containing that text
        - **Vote range**: Filter restaurants by popularity (vote count)
        - **Combined filters**: Both filters work together for precise results
        
        **Example Searches:**
        - Name: "Dishoom" → Shows all Dishoom locations
        - Votes: 0-500 → Shows restaurants with 0 to 500 votes
        - Both: Name "Pizza" + Votes 100-1000 → Shows pizza places with 100-1000 votes
        """)

# ============================================================================
# TAB 3: INTERACTIVE MAP (QUESTION 2 - 40 POINTS)
# ============================================================================
elif tab_selection == "🗺️ Interactive Map":
    st.title("🗺️ Restaurant Locations in London")
    st.markdown("Explore restaurant locations on an interactive map")
    
    # Display button
    map_button = st.button(
        "🗺️ Display map!",
        type="primary",
        use_container_width=True,
        help="Map of restaurants in London. Click on teardrop to check names."
    )
    
    st.caption("Map of restaurants in London. Click on teardrop to check names.")
    
    if map_button or 'show_map' in st.session_state:
        st.session_state['show_map'] = True
        
        with st.spinner("Loading restaurant locations..."):
            # Get location data
            location_df = get_restaurant_locations()
            
            if not location_df.empty:
                st.success(f"✅ Loaded {len(location_df)} restaurant locations")
                
                # Create folium map centered on London
                # CUSTOMIZATION: Using CartoDB Positron tiles (CUSTOMIZATION #3)
                m = folium.Map(
                    location=[51.5074, -0.1278],
                    zoom_start=12,
                    tiles='CartoDB positron'
                )
                
                # Add markers for each restaurant with pink/green theme
                for idx, row in location_df.iterrows():
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=folium.Popup(row['name'], max_width=300),
                        tooltip=row['name'],
                        icon=folium.Icon(color='pink', icon='cutlery', prefix='fa')
                    ).add_to(m)
                
                # Display map
                st_folium(m, width=1400, height=600)
                
                # Statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Restaurants on Map", len(location_df))
                with col2:
                    st.info("💡 Click on any pink marker to see the restaurant name")
                
            else:
                st.error("❌ No location data available")
    
    # Map information
    with st.expander("ℹ️ Map Information"):
        st.markdown("""
        **Map Features:**
        - 🗺️ Custom CartoDB Positron tiles for clean visualization
        - 📍 Pink markers indicate restaurant locations
        - 🖱️ Click markers to see restaurant names
        - 🔍 Zoom in/out using the +/- buttons
        - 🌍 Pan around the map by clicking and dragging
        
        **Note:** Only restaurants with valid coordinates are displayed on the map.
        """)

# ============================================================================
# FOOTER
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 About")
st.sidebar.info("""
This dashboard connects to a MySQL database containing restaurant information 
and provides search and visualization capabilities.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")
                
