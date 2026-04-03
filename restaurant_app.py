import streamlit as st
import json
import os
import shutil
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from jsonschema import validate, ValidationError as JsonSchemaValidationError

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="California Culinary Map",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background-color: #0f0e0c;
    color: #f0ece4;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1814;
    border-right: 1px solid #2e2b25;
}

/* Header */
.main-header {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 900;
    color: #f0ece4;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.main-subheader {
    color: #c8a96e;
    font-size: 0.95rem;
    font-weight: 300;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Restaurant card */
.restaurant-card {
    background: linear-gradient(135deg, #1c1a16 0%, #201e19 100%);
    border: 1px solid #2e2b25;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
    position: relative;
    overflow: hidden;
}
.restaurant-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #c8a96e, #8b6914);
}
.restaurant-card:hover {
    border-color: #c8a96e44;
}
.card-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #f0ece4;
    margin-bottom: 0.3rem;
}
.card-location {
    color: #c8a96e;
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.card-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.8rem;
}
.badge {
    background: #2a2620;
    border: 1px solid #3a3630;
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    color: #c8a96e;
}
.badge-rating {
    background: #1e2a1a;
    border-color: #3a5030;
    color: #7cb87a;
}
.badge-price {
    background: #2a1e1a;
    border-color: #503a30;
    color: #c87a5a;
}
.card-vibe {
    font-style: italic;
    color: #8a8278;
    font-size: 0.88rem;
    margin-bottom: 0.5rem;
}
.signatures-list {
    color: #c8b898;
    font-size: 0.85rem;
}

/* Section headers */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: #f0ece4;
    border-bottom: 1px solid #2e2b25;
    padding-bottom: 0.5rem;
    margin-bottom: 1.2rem;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #1c1a16 !important;
    border: 1px solid #3a3630 !important;
    color: #f0ece4 !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #c8a96e !important;
    box-shadow: 0 0 0 2px #c8a96e22 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #c8a96e, #8b6914);
    color: #0f0e0c;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    font-family: 'DM Sans', sans-serif;
    letter-spacing: 0.5px;
    padding: 0.5rem 1.5rem;
    transition: opacity 0.2s;
}
.stButton > button:hover {
    opacity: 0.85;
    color: #c8a96e !important;
}

/* Danger button */
.danger-btn > button {
    background: linear-gradient(135deg, #c85a3a, #8b2a14) !important;
    color: #f0ece4 !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #1c1a16 !important;
    border-color: #3a3630 !important;
    color: #f0ece4 !important;
}

/* Alert/info boxes */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 8px !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #c8a96e !important;
}

/* Divider */
hr {
    border-color: #2e2b25 !important;
}

/* Metric */
[data-testid="metric-container"] {
    background: #1c1a16;
    border: 1px solid #2e2b25;
    border-radius: 10px;
    padding: 1rem;
}
[data-testid="metric-container"] label {
    color: #8a8278 !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #c8a96e !important;
    font-family: 'Playfair Display', serif !important;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: #1c1a16 !important;
    border: 1px solid #2e2b25 !important;
    border-radius: 8px !important;
    color: #f0ece4 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
FILEPATH      = 'structured_restaurant_data.json'
BACKUP_PATH   = 'structured_restaurant_data.json.bak'

EXAMPLE_RESTAURANT_PARAGRAPH = (
    'Down in **Santa Monica**, **Mar de Cortez** serves as a **sun-drenched**, '
    '**casual taqueria** specializing in **Baja-style seafood**. With a **4.2/5** '
    'rating, it captures the salt-air energy of the coast through its signature '
    'beer-battered snapper tacos and zesty octopus ceviche, making it a premier '
    'spot for open-air dining near the pier. Price range: $'
)

EXAMPLE_OUTPUT = """
    {
    "name": "Mar de Cortez",
    "location": "Santa Monica",
    "type": "casual taqueria",
    "food_style": "Baja-style seafood",
    "rating": 4.2,
    "price_range": 1,
    "signatures": ["beer-battered snapper tacos", "zesty octopus ceviche"],
    "vibe": "salt-air energy",
    "environment": "a premier sun-drenched spot for open-air dining near the pier.",
    "shortcomings": []
    }
"""

RESTAURANT_SCHEMA = {
    "type": "object",
    "required": ["name","location","type","food_style","rating",
                 "price_range","signatures","vibe","environment","shortcomings"],
    "properties": {
        "name":         {"type": "string"},
        "location":     {"type": "string"},
        "type":         {"type": "string"},
        "food_style":   {"type": "string"},
        "rating":       {"type": "number"},
        "price_range":  {"type": "integer"},
        "signatures":   {"type": "array", "items": {"type": "string"}},
        "vibe":         {"type": "string"},
        "environment":  {"type": "string"},
        "shortcomings": {"type": "array", "items": {"type": "string"}}
    },
    "additionalProperties": False
}

# ── Helper functions ──────────────────────────────────────────────────────────
def load_data(file_path=FILEPATH):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_data(data, file_path=FILEPATH, backup_path=BACKUP_PATH):
    if os.path.exists(file_path):
        shutil.copy(file_path, backup_path)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def llm_model(system_msg, prompt_txt, params=None):
    api_key = st.session_state.get("api_key", "")
    credentials = Credentials(
        url="https://us-south.ml.cloud.ibm.com",
        api_key=api_key if api_key else None
    )
    model = ModelInference(
        model_id="ibm/granite-4-h-small",
        project_id="skills-network",
        credentials=credentials,
        params=params or {}
    )
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": prompt_txt}
    ]
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"]

def restaurant_data_structure_prompt_generation(restaurant_paragraph):
    base_system_msg = f"""
    You are a precise data extraction assistant specializing in the restaurant industry.
    Your job is to read a restaurant description paragraph and convert it into a structured JSON object.
    Follow these strict rules:
    - Extract only information explicitly stated in the description. Do not invent details.
    - Output ONLY valid JSON — no extra text, no markdown code blocks, no explanations.
    - For the "price_range" field, convert dollar signs into an integer ($ = 1, $$ = 2, $$$ = 3).
    - For the "signatures" field, list the standout or signature dishes mentioned.
    - For the "shortcomings" field, list any criticisms or negatives mentioned. If none, use [].
    - All field names must match exactly: name, location, type, food_style, rating,
      price_range, signatures, vibe, environment, shortcomings.
    """
    base_user_prompt = f"""
    Task: Extract the restaurant info into a structured JSON object with these fields:
    name, location, type, food_style, rating, price_range, signatures, vibe, environment, shortcomings.
    Convert dollar sign notation into an integer for price_range.
    Return ONLY the JSON object.

    Restaurant description:
    {restaurant_paragraph}

    Example:
    Input: {EXAMPLE_RESTAURANT_PARAGRAPH}
    Output: {EXAMPLE_OUTPUT}
    """
    return base_system_msg, base_user_prompt

def JSON_auto_repair_prompts(candidate_json_output, error_message):
    system_msg = """
    You are a strict JSON repair specialist. Fix malformed or invalid JSON to conform to the schema.
    Output ONLY the corrected JSON object — no explanations, no markdown, no extra text.
    Fix only what is broken. Keep all valid data intact.
    """
    prompt = f"""
    The following JSON failed schema validation.
    Fix ONLY the issues described in the error and return the corrected JSON.

    --- Faulty JSON ---
    {candidate_json_output}

    --- Error ---
    {error_message}

    Corrected JSON:
    """
    return system_msg, prompt

def new_data_entry_process(paragraph, itemId):
    system_msg, user_prompt = restaurant_data_structure_prompt_generation(paragraph)
    raw_output = llm_model(system_msg, user_prompt)

    max_retries = 3
    attempt = 0
    final_output = None

    while attempt < max_retries:
        try:
            cleaned = (raw_output.strip()
                       .removeprefix("```json").removeprefix("```")
                       .removesuffix("```").strip())
            parsed = json.loads(cleaned)
            validate(instance=parsed, schema=RESTAURANT_SCHEMA)
            parsed["itemId"] = itemId
            final_output = parsed
            break
        except (json.JSONDecodeError, JsonSchemaValidationError) as e:
            attempt += 1
            if attempt < max_retries:
                r_sys, r_prompt = JSON_auto_repair_prompts(raw_output, str(e))
                raw_output = llm_model(r_sys, r_prompt)
            else:
                final_output = None

    return final_output

def price_stars(n):
    return "💰" * n if n else "—"

def rating_color(r):
    if r >= 4.5: return "#7cb87a"
    if r >= 4.0: return "#c8a96e"
    if r >= 3.5: return "#c87a5a"
    return "#c85a3a"

def render_restaurant_card(record, idx):
    name        = record.get("name", "Unknown")
    location    = record.get("location", "—")
    rtype       = record.get("type", "—")
    food_style  = record.get("food_style", "—")
    rating      = record.get("rating", 0)
    price_range = record.get("price_range", 0)
    signatures  = record.get("signatures", [])
    vibe        = record.get("vibe", "")
    shortcoming = record.get("shortcomings", [])

    sigs_html = " · ".join(f"<span>{s}</span>" for s in signatures) if signatures else "—"
    short_html = (", ".join(shortcoming) if shortcoming else "<em>None noted</em>")

    st.markdown(f"""
    <div class="restaurant-card">
        <div class="card-name">#{idx} &nbsp; {name}</div>
        <div class="card-location">📍 {location}</div>
        <div class="card-meta">
            <span class="badge">{rtype}</span>
            <span class="badge">{food_style}</span>
            <span class="badge badge-rating">⭐ {rating}</span>
            <span class="badge badge-price">{price_stars(price_range)}</span>
        </div>
        <div class="card-vibe">"{vibe}"</div>
        <div class="signatures-list">🍴 {sigs_html}</div>
        {f'<div style="margin-top:0.5rem;color:#8a6a6a;font-size:0.82rem;">⚠️ {short_html}</div>' if shortcoming else ''}
    </div>
    """, unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False
# ── Theme Management ──────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

def get_theme_css(theme):
    if theme == "Dark":
        return """
        .stApp { background-color: #0f0e0c; color: #f0ece4; }
        [data-testid="stSidebar"] { background-color: #1a1814; border-right: 1px solid #2e2b25; }
        .restaurant-card { background: linear-gradient(135deg, #1c1a16 0%, #201e19 100%); border: 1px solid #2e2b25; }
        .card-name { color: #f0ece4; }
        .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: #1c1a16 !important; color: #f0ece4 !important; }
        [data-testid="stRadio"] label {
        color: #f0ece4 !important; /* Brighter white for dark mode */
        font-weight: 500;
}
        """
    else:
        return """
        .stApp { background-color: #fdfcf0; color: #1a1814; }
        [data-testid="stSidebar"] { background-color: #f0ede4; border-right: 1px solid #dcd8cc; }
        .restaurant-card { 
            background: #f7f4ed; 
            border: 1px solid #dcd8cc; 
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        }
        .card-name { color: #1a1814; }
        .card-location { color: #8b6914; }
        .badge { background: #e8e4d9; color: #5a4d32; border: 1px solid #dcd8cc; }
        .stTextInput input, .stTextArea textarea, .stNumberInput input { 
            background-color: #ffffff !important; 
            color: #1a1814 !important; 
            border: 1px solid #c8a96e !important; 
        }
        .main-header { color: #1a1814 !important; }
        .main-subheader { color: #8b6914 !important; }
        .stButton > button { background: #c8a96e; color: #ffffff; }
        .stMetricValue { color: #8b6914 !important; }
        """
        
        """
        /* ── LIGHT MODE THEME ───────────────────────────── */

        .stApp {
            background-color: #faf9f6;
            color: #1f1f1f;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f3f1ea;
            border-right: 1px solid #e2dfd6;
        }

        /* Restaurant Card */
        .restaurant-card {
            background: #ffffff;
            border: 1px solid #e6e2d9;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.2s ease;
        }

        .restaurant-card:hover {
            border-color: #c8a96e;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        }

        /* Text */
        .card-name {
            color: #1a1814;
        }

        .card-location {
            color: #8b6f3d;
        }

        /* Badges */
        .badge {
            background: #f6f4ee;
            border: 1px solid #e2dfd6;
            color: #6b5a3a;
        }

        .badge-rating {
            background: #edf7ee;
            border-color: #cfe6d1;
            color: #2e7d32;
        }

        .badge-price {
            background: #fff3ec;
            border-color: #f1d2c5;
            color: #b85c38;
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            background-color: #ffffff !important;
            color: #1a1814 !important;
            border: 1px solid #d6d2c8 !important;
            border-radius: 8px !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: #c8a96e !important;
            box-shadow: 0 0 0 2px rgba(200,169,110,0.2) !important;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background-color: #ffffff !important;
            border: 1px solid #d6d2c8 !important;
            color: #1a1814 !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #d4b483, #b89655);
            color: #ffffff;
            border-radius: 8px;
            border: none;
            font-weight: 500;
        }

        .stButton > button:hover {
            opacity: 0.9;
            color: #c8a96e !important;
        }

        /* Metrics */
        [data-testid="metric-container"] {
            background: #ffffff;
            border: 1px solid #e6e2d9;
            border-radius: 10px;
        }

        /* Divider */
        hr {
            border-color: #e2dfd6 !important;
        }
        """
    
    
        

# Inject CSS
st.markdown(f"<style>{get_theme_css(st.session_state.theme)}</style>", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0;">
        <div class="main-subheader">
            🍽️ Culinary Map
            California Restaurant DB
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # API Key input
    #st.markdown("<div style='color:#8a8278;font-size:0.78rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.3rem;'>IBM WatsonX API Key</div>", unsafe_allow_html=True)
    #api_key_input = st.text_input(
    #    "API Key", type="password",
    #    value=st.session_state.api_key,
    #    placeholder="Paste your API key here...",
    #    label_visibility="collapsed"
    #)
    #if api_key_input:
    #    st.session_state.api_key = api_key_input
    #    st.success("API key set ✓", icon="🔑"
    
    #st.markdown("""<div class="main-subheader">
    #        🍽️ Culinary Map
    #    </div>""",unsafe_allow_html=True)
    
    # Theme Toggle
    #new_theme = st.toggle("Light Mode", value=(st.session_state.theme == "Light"))
    st.markdown('<div class="main-subheader">', unsafe_allow_html=True)
    new_theme = st.toggle("Change Mode", value=(st.session_state.theme == "Light"))
    st.markdown('</div>', unsafe_allow_html=True)
    if new_theme != (st.session_state.theme == "Light"):
        st.session_state.theme = "Light" if new_theme else "Dark"
        st.rerun()
        
    st.divider()

    # Navigation
    st.markdown("<div style='color:#8a8278;font-size:0.78rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.8rem;'>Navigation</div>", unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        ["📋 Browse All", "🔍 View Record", "➕ Add Restaurant", "✏️ Edit Record", "🗑️ Delete Record"],
        label_visibility="collapsed"
    )

    st.divider()
    data_all = load_data()
    st.metric("Total Restaurants", len(data_all))

# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">California Culinary Map</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subheader">Restaurant Intelligence Database</div>', unsafe_allow_html=True)

# ── Pages ─────────────────────────────────────────────────────────────────────

# ── 1. BROWSE ALL ─────────────────────────────────────────────────────────────
if page == "📋 Browse All":
    data = load_data()
    st.markdown('<div class="section-title">All Restaurants</div>', unsafe_allow_html=True)

    if not data:
        st.info("No restaurants in the database yet. Add one using the sidebar!")
    else:
        # Search/filter bar
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Search by name or location", placeholder="e.g. Santa Monica, taqueria...")
        with col_filter:
            sort_by = st.selectbox("Sort by", ["Index", "Name", "Rating ↓", "Price ↓"])

        filtered = data
        if search:
            q = search.lower()
            filtered = [r for r in data if
                        q in r.get("name","").lower() or
                        q in r.get("location","").lower() or
                        q in r.get("type","").lower() or
                        q in r.get("food_style","").lower()]

        if sort_by == "Name":
            filtered = sorted(filtered, key=lambda r: r.get("name",""))
        elif sort_by == "Rating ↓":
            filtered = sorted(filtered, key=lambda r: r.get("rating", 0), reverse=True)
        elif sort_by == "Price ↓":
            filtered = sorted(filtered, key=lambda r: r.get("price_range", 0), reverse=True)

        st.caption(f"Showing {len(filtered)} of {len(data)} restaurants")
        st.divider()

        for idx, record in enumerate(filtered):
            render_restaurant_card(record, idx)

# ── 2. VIEW RECORD ────────────────────────────────────────────────────────────
elif page == "🔍 View Record":
    data = load_data()
    st.markdown('<div class="section-title">View Detailed Record</div>', unsafe_allow_html=True)

    if not data:
        st.info("No restaurants in the database yet.")
    else:
        options = {f"[{i}] {r.get('name','Unknown')} — {r.get('location','?')}": i
                   for i, r in enumerate(data)}
        selected = st.selectbox("Select a restaurant", list(options.keys()))
        idx = options[selected]
        record = data[idx]

        st.divider()
        render_restaurant_card(record, idx)

        st.divider()
        st.markdown("**Full Record (JSON)**")
        st.json(record)

# ── 3. ADD RESTAURANT ─────────────────────────────────────────────────────────
elif page == "➕ Add Restaurant":
    st.markdown('<div class="section-title">Add New Restaurant</div>', unsafe_allow_html=True)

    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your IBM WatsonX API key in the sidebar before adding a restaurant.")
    else:
        st.markdown("""
        <div style="background:#1c1a16;border:1px solid #2e2b25;border-radius:10px;padding:1rem 1.2rem;margin-bottom:1.2rem;color:#8a8278;font-size:0.88rem;">
        Paste a natural language restaurant description below. The AI will automatically extract
        and structure the data into the database.
        </div>
        """, unsafe_allow_html=True)

        paragraph = st.text_area(
            "Restaurant Description",
            placeholder=(
                "e.g. Down in San Francisco, Ember & Salt is an upscale modern American "
                "bistro known for its wood-fired cuisine. With a 4.6/5 rating and $$$ pricing, "
                "signature dishes include dry-aged ribeye and truffle arancini..."
            ),
            height=180
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            submit = st.button("🤖 Process & Add", use_container_width=True)

        if submit:
            if not paragraph.strip():
                st.error("Please enter a restaurant description.")
            else:
                data = load_data()
                item_id = 1000000 + len(data) + 1

                with st.spinner("🔄 AI is extracting restaurant data..."):
                    result = new_data_entry_process(paragraph, item_id)

                if result:
                    data.append(result)
                    save_data(data)
                    st.success(f"✅ **{result.get('name', 'Restaurant')}** has been added successfully!")
                    st.divider()
                    st.markdown("**Preview of added record:**")
                    render_restaurant_card(result, len(data) - 1)
                    st.json(result)
                else:
                    st.error("❌ Failed to process the description after multiple attempts. Please try rephrasing.")

# ── 4. EDIT RECORD ────────────────────────────────────────────────────────────
elif page == "✏️ Edit Record":
    data = load_data()
    st.markdown('<div class="section-title">Edit Restaurant Record</div>', unsafe_allow_html=True)

    if not data:
        st.info("No restaurants in the database yet.")
    else:
        options = {f"[{i}] {r.get('name','Unknown')} — {r.get('location','?')}": i
                   for i, r in enumerate(data)}
        selected = st.selectbox("Select a restaurant to edit", list(options.keys()))
        idx = options[selected]
        record = data[idx].copy()

        st.divider()
        st.markdown(f"**Editing:** {record.get('name', 'Unknown')}")
        st.caption("Leave a field unchanged to keep its current value.")

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                record["name"]       = st.text_input("Name",       value=record.get("name",""))
                record["location"]   = st.text_input("Location",   value=record.get("location",""))
                record["type"]       = st.text_input("Type",       value=record.get("type",""))
                record["food_style"] = st.text_input("Food Style", value=record.get("food_style",""))
                record["vibe"]       = st.text_input("Vibe",       value=record.get("vibe",""))
            with col2:
                record["rating"]      = st.number_input("Rating",      value=float(record.get("rating",0.0)),   min_value=0.0, max_value=5.0, step=0.1)
                record["price_range"] = st.number_input("Price Range", value=int(record.get("price_range",1)),  min_value=1,   max_value=4,   step=1)
                record["environment"] = st.text_input("Environment", value=record.get("environment",""))
                sigs_str  = st.text_input("Signatures (comma-separated)",  value=", ".join(record.get("signatures",[])))
                short_str = st.text_input("Shortcomings (comma-separated)", value=", ".join(record.get("shortcomings",[])))

            record["signatures"]  = [s.strip() for s in sigs_str.split(",")  if s.strip()]
            record["shortcomings"]= [s.strip() for s in short_str.split(",") if s.strip()]

            st.divider()
            col_warn, col_btn = st.columns([3, 1])
            with col_warn:
                st.warning("❗ Changes are saved immediately and cannot be undone (a backup is created).")
            with col_btn:
                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

        if submitted:
            data[idx] = record
            save_data(data)
            st.success(f"✅ **{record.get('name')}** updated successfully!")
            render_restaurant_card(record, idx)

# ── 5. DELETE RECORD ──────────────────────────────────────────────────────────
elif page == "🗑️ Delete Record":
    data = load_data()
    st.markdown('<div class="section-title">Delete Restaurant Record</div>', unsafe_allow_html=True)

    if not data:
        st.info("No restaurants in the database yet.")
    else:
        options = {f"[{i}] {r.get('name','Unknown')} — {r.get('location','?')}": i
                   for i, r in enumerate(data)}
        selected = st.selectbox("Select a restaurant to delete", list(options.keys()))
        idx = options[selected]
        record = data[idx]

        st.divider()
        st.markdown("**Record to be deleted:**")
        render_restaurant_card(record, idx)

        st.divider()
        st.error(f"⚠️ You are about to permanently delete **{record.get('name','this restaurant')}**. A backup will be created.")

        col1, col2 = st.columns([1, 4])
        with col1:
            confirm = st.checkbox("I understand, proceed with deletion")
        if confirm:
            with col1:
                if st.button("🗑️ Delete", use_container_width=True):
                    removed_name = data.pop(idx).get("name", "Record")
                    save_data(data)
                    st.success(f"✅ **{removed_name}** has been deleted. Refresh the page to continue.")
                    st.balloons()
