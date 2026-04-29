import requests
import streamlit as st

API_BASE = "https://movie-recommender-2-q91v.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

st.markdown("""
<style>
body { background-color: #0e1117; }
.block-container { max-width: 1500px; padding-top: 1rem; }
.movie-card img {
    width: 100%;
    border-radius: 12px;
    transition: transform 0.25s ease;
}
.movie-card img:hover { transform: scale(1.05); }
.section-title { font-size: 1.4rem; font-weight: 600; margin: 10px 0; color: white; }
div[data-testid="stButton"] button {
    background: none !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    cursor: pointer !important;
}
div[data-testid="stButton"] button:hover {
    background: none !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────
for k, v in {
    "view": "home",
    "selected_tmdb_id": None,
    "search_query": "",
    "search_results": [],
    "input_key": 0,          # incrementing this destroys & recreates the text_input
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── NAVIGATION ────────────────────────────────────────────
def open_movie(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id

def go_home():
    st.session_state.view = "home"
    st.session_state.selected_tmdb_id = None
    st.session_state.search_query = ""
    st.session_state.search_results = []
    st.session_state.input_key += 1   # ← forces text_input to be blank

# ── API ───────────────────────────────────────────────────
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json() if r.status_code < 400 else None
    except:
        return None

# ── PARSER ────────────────────────────────────────────────
def parse_search(data, keyword):
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

# ── GRID ──────────────────────────────────────────────────
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
            m = cards[idx]; idx += 1
            tmdb_id = m.get("tmdb_id")
            title   = m.get("title", "Unknown")
            poster  = m.get("poster_url")
            with colset[c]:
                if poster:
                    st.markdown(f'<div class="movie-card"><img src="{poster}" title="{title}"></div>',
                                unsafe_allow_html=True)
                if st.button(title, key=f"btn_{tmdb_id}_{idx}"):
                    open_movie(tmdb_id)
                    st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    if st.button("🏠 Home", key="sidebar_home"):
        go_home()
        st.rerun()
    category = st.selectbox("Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"])
    cols = st.slider("Columns", 4, 8, 6)

# ── HEADER ────────────────────────────────────────────────
st.markdown("<h1 style='color:white;'>🎬 Movie Recommender</h1>", unsafe_allow_html=True)
st.divider()

# ── HOME ──────────────────────────────────────────────────
if st.session_state.view == "home":

    # input_key changes every time go_home() is called
    # → Streamlit sees a NEW widget → always renders empty
    query = st.text_input("Search movies", key=f"search_{st.session_state.input_key}")

    if query:
        # new search typed — fetch fresh results
        if query != st.session_state.search_query:
            st.session_state.search_query = query
            data = api_get("/tmdb/search", {"query": query})
            st.session_state.search_results = parse_search(data, query) if data else []

        poster_grid(st.session_state.search_results, cols)
        st.stop()

    # no query → show category browse
    st.markdown(f"<div class='section-title'>{category.replace('_',' ').title()}</div>",
                unsafe_allow_html=True)
    cards = api_get("/home", {"category": category})
    poster_grid(cards or [], cols)

# ── DETAILS ───────────────────────────────────────────────
elif st.session_state.view == "details":

    if st.button("← Back", key="back"):
        go_home()
        st.rerun()

    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.error("No movie selected.")
        st.stop()

    data = api_get(f"/movie/id/{tmdb_id}")
    if not data:
        st.error("Could not load movie.")
        st.stop()

    left, right = st.columns([1, 2])
    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)
    with right:
        st.subheader(data.get("title", ""))
        st.write(data.get("overview", ""))

    if data.get("backdrop_url"):
        st.image(data["backdrop_url"], use_column_width=True)

    st.divider()
    st.subheader("Recommendations")
    recs = api_get("/recommend/genre", {"tmdb_id": tmdb_id})
    poster_grid(recs or [], cols)