import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-recommender-2-q91v.onrender.com"
# API_BASE = "http://127.0.0.1:8000"

TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# NETFLIX CSS
# =============================
st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.block-container {
    max-width: 1500px;
    padding-top: 1rem;
}
.movie-card {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.movie-card:hover {
    transform: scale(1.08);
    z-index: 10;
    box-shadow: 0 10px 25px rgba(0,0,0,0.6);
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
    font-size: 0.85rem;
}
.section-title {
    font-size: 1.4rem;
    font-weight: 600;
    margin: 10px 0;
}
a {
    text-decoration: none !important;
}
</style>
""", unsafe_allow_html=True)

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

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
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()

# =============================
# API
# =============================
@st.cache_data(ttl=30)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        if r.status_code >= 400:
            return None, "API Error"
        return r.json(), None
    except Exception as e:
        return None, str(e)

# =============================
# NETFLIX GRID (FIXED)
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        st.info("No movies found.")
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
                else:
                    st.write("No Image")

# =============================
# PARSER
# =============================
def parse_tmdb_search_to_cards(data, keyword):
    keyword = keyword.lower()
    items = []

    if isinstance(data, dict) and "results" in data:
        for m in data["results"]:
            if m.get("id") and m.get("title"):
                items.append({
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
                })

    elif isinstance(data, list):
        items = data

    filtered = [x for x in items if keyword in x["title"].lower()]
    return filtered if filtered else items

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

    if query:
        data, err = api_get_json("/tmdb/search", {"query": query})

        if err:
            st.error(err)
        else:
            cards = parse_tmdb_search_to_cards(data, query)
            poster_grid(cards, cols)

        st.stop()

    st.markdown(f"<div class='section-title'>{category.replace('_',' ').title()}</div>", unsafe_allow_html=True)

    cards, err = api_get_json("/home", {"category": category})

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
    data, err = api_get_json(f"/movie/id/{tmdb_id}")

    if err:
        st.error(err)
        st.stop()

    left, right = st.columns([1, 2])

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], width="stretch")

    with right:
        st.subheader(data.get("title"))
        st.write(data.get("overview"))

    if data.get("backdrop_url"):
        st.image(data["backdrop_url"], width="stretch")

    st.divider()
    st.subheader("Recommendations")

    recs, _ = api_get_json("/recommend/genre", {"tmdb_id": tmdb_id})
    poster_grid(recs, cols)