import requests
import streamlit as st
import time   # 🔥 for cache busting

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-recommender-2-q91v.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# CSS (NETFLIX STYLE)
# =============================
st.markdown("""
<style>
body { background-color: #0e1117; }
.block-container { max-width: 1500px; padding-top: 1rem; }

.movie-card {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.movie-card:hover {
    transform: scale(1.08);
    z-index: 10;
    box-shadow: 0 15px 30px rgba(0,0,0,0.7);
}
.movie-card img {
    width: 100%;
    border-radius: 12px;
}
.movie-overlay {
    position: absolute;
    bottom: 0;
    width: 100%;
    padding: 10px;
    background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
    color: white;
    font-size: 0.9rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 15px 0;
}
a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# =============================
# ROUTING
# =============================
qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")

if qp_view in ("home", "details"):
    st.session_state.view = qp_view

if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass

def goto_home():
    st.session_state.view = "home"
    st.query_params.clear()
    st.rerun()

# =============================
# API FUNCTIONS
# =============================

# 🔥 NO CACHE (search)
def api_get_json_no_cache(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json(), None
    except Exception as e:
        return None, str(e)

# ✅ CACHE (home, details)
@st.cache_data(ttl=30)
def api_get_json_cached(path, params):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json(), None
    except Exception as e:
        return None, str(e)

# =============================
# GRID UI
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        st.warning("No movies found 😢")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for _ in range(rows):
        colset = st.columns(cols)

        for c in range(cols):
            if idx >= len(cards):
                break

            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "")
            poster = m.get("poster_url")

            with colset[c]:
                if poster:
                    st.markdown(f"""
                    <a href="?view=details&id={tmdb_id}">
                        <div class="movie-card">
                            <img src="{poster}">
                            <div class="movie-overlay">{title}</div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    if st.button("🏠 Home"):
        goto_home()

    category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"]
    )

    cols = st.slider("Columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.markdown("<h1 style='color:white;'>🎬 Movie Recommender</h1>", unsafe_allow_html=True)
st.divider()

# =============================
# HOME
# =============================
if st.session_state.view == "home":

    query = st.text_input("Search movies")

    # 🔥 SEARCH (NO CACHE + TIMESTAMP FIX)
    if query and len(query) > 2:
        with st.spinner("Searching movies..."):
            data, err = api_get_json_no_cache(
                "/tmdb/search",
                {"query": query, "t": time.time()}  # 🔥 cache breaker
            )

        if err:
            st.error(err)
        else:
            results = data.get("results", [])
            cards = [{
                "tmdb_id": m["id"],
                "title": m["title"],
                "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
            } for m in results if m.get("id") and m.get("title")]

            poster_grid(cards, cols)

        st.stop()

    # 🔥 HOME DATA (cached)
    st.markdown(f"<div class='section-title'>{category.replace('_',' ').title()}</div>", unsafe_allow_html=True)

    cards, err = api_get_json_cached("/home", {"category": category})

    if err:
        st.error(err)
    else:
        poster_grid(cards, cols)

# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    if st.button("← Back"):
        goto_home()

    tmdb_id = st.session_state.selected_tmdb_id
    data, err = api_get_json_cached(f"/movie/id/{tmdb_id}", {})

    if err or not data:
        st.error(err or "No data found")
        st.stop()

    left, right = st.columns([1, 2])

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)

    with right:
        st.subheader(data.get("title"))
        st.write(data.get("overview"))

    if data.get("backdrop_url"):
        st.image(data["backdrop_url"], use_column_width=True)

    st.divider()
    st.subheader("Recommendations")

    recs, _ = api_get_json_cached("/recommend/genre", {"tmdb_id": tmdb_id})
    poster_grid(recs, cols)