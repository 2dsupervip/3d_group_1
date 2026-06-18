import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import json
import re
import itertools
import base64

# --- 1. Streamlit Configuration & Dark Theme UI ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D Pro", page_icon="🎯")

st.markdown("""
    <style>
    /* Global Background and Text */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Tab Styling */
    button[data-baseweb="tab"] { color: #888888 !important; font-size: 16px !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #D4AF37 !important; border-bottom-color: #D4AF37 !important; }
    
    /* Metrics / Summary Cards Styling */
    .metric-card {
        background-color: #1f2937; border: 1px solid #374151; border-radius: 10px;
        padding: 15px; text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 12px;
    }
    .metric-title { font-size: 15px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { color: #ffffff; font-size: 16px; font-weight: 500; letter-spacing: 2px; line-height: 1.8; }
    
    /* Button Styling */
    div.stButton > button {
        background-color: #D4AF37 !important; color: #0e1117 !important; 
        font-weight: bold !important; font-size: 16px !important;
        border-radius: 8px !important; transition: all 0.3s ease !important;
        height: 48px !important;
    }
    div.stButton > button:hover { background-color: #f3cd44 !important; transform: scale(1.01); }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Loading Engine ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 3. History Core Engine with Neighborhood Block Filter ---
@st.cache_data
def build_super_groups_fast(df):
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    super_groups = {"Head": {}, "Mid": {}, "Tail": {}}
    max_rows = len(df)
    max_y = len(head_cols) - 1 
    
    for pos_name, cols in positions:
        history_counts = {}
        # ဒေတာ Block ကြီးတစ်ခုလုံး ပုံတူထပ်နေခြင်းကို စစ်ထုတ်ရန် Signature Registry
        seen_neighborhood_blocks = {}
        
        for y_idx in range(max_y):
            for r in range(max_rows):
                for y_step in range(5):
                    for r_step in range(-4, 5):
                        if y_step == 0 and r_step == 0: continue
                        
                        digits, path_str, valid = [], [], True
                        neighborhood_signature = [] # 🛠 ပတ်ဝန်းကျင် ဝဲ/ယာ ဒေတာစုစည်းမှု
                        
                        for i in range(4):
                            curr_r = r + i * r_step
                            curr_y = y_idx + i * y_step
                            if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y:
                                valid = False; break
                            
                            c_idx = cols[curr_y]
                            val = str(df.iloc[curr_r, c_idx]).strip()
                            if val.lower() in ['x', 'nan', '']:
                                valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            
                            # 🛠 [လော့ဂျစ်အသစ်] လက်ရှိဆဲလ်၏ ဝဲဘက်နှင့် ညာဘက် ဂဏန်းများကိုပါ ဆွဲထုတ်၍ ဒေတာတုံးတု စစ်ဆေးရန်
                            left_val = str(df.iloc[curr_r, c_idx - 1]).strip() if c_idx - 1 >= 0 else ""
                            right_val = str(df.iloc[curr_r, c_idx + 1]).strip() if c_idx + 1 < len(df.columns) else ""
                            neighborhood_signature.append((val, left_val, right_val))
                            
                            digits.append(val)
                            path_str.append(f"R{curr_r+2}_Y{curr_y}")
                            
                        if valid:
                            dtup = tuple(digits)
                            block_sig = tuple(neighborhood_signature)
                            path_joined = "->".join(path_str)
                            
                            # 🛠 [လော့ဂျစ်အသစ်] ဂဏန်းချင်းတူရုံတင်မကဘဲ ဘေးပတ်ဝန်းကျင်ပါ ပုံတူထပ်နေလျှင် လုံးဝလက်မခံဘဲ ပယ်ဖျက်ပစ်ခြင်း
                            if block_sig in seen_neighborhood_blocks:
                                # ဒေတာတုံးတူသော်လည်း နေရာမတူပါက ဒုတိယတစ်ခုကို Registry ထဲထည့်သော်လည်း ရမှတ်ထဲမထည့်ပါ
                                continue
                            
                            seen_neighborhood_blocks[block_sig] = path_joined
                            
                            if dtup not in history_counts: history_counts[dtup] = set()
                            history_counts[dtup].add(path_joined)
                            
        for dtup, paths in history_counts.items():
            if len(paths) >= 3: 
                super_groups[pos_name][dtup] = list(paths)
                
    return super_groups, head_cols, mid_cols, tail_cols

# --- 4. Target Evaluator Engine ---
def evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_excel_row):
    target_r = target_excel_row - 2 
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    results = {}
    target_y = len(head_cols) - 1 
    max_rows = len(df)
    
    for pos_name, cols in positions:
        prefixes = []
        for y_step in range(5):
            for r_step in range(-4, 5):
                if y_step == 0 and r_step == 0: continue
                start_r = target_r - 3 * r_step
                start_y = target_y - 3 * y_step
                if start_r < 0 or start_r >= max_rows or start_y < 0: continue
                
                valid, digits, path_str = True, [], []
                for i in range(3):
                    curr_r = start_r + i * r_step
                    curr_y = start_y + i * y_step
                    if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= len(cols):
                        valid = False; break
                    val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                    if val.lower() in ['x', 'nan', '']: valid = False; break
                    if val.endswith('.0'): val = val[:-2]
                    digits.append(val)
                    path_str.append(f"R{curr_r+2}_Y{curr_y}")
                    
                if valid:
                    prefixes.append({"prefix": tuple(digits), "path": f"{' -> '.join(path_str)} -> [TARGET]"})
        
        pos_results = []
        for guess in range(10):
            guess_str = str(guess)
            matches = []
            for pref in prefixes:
                test_group = pref["prefix"] + (guess_str,)
                if test_group in super_groups[pos_name]:
                    matches.append({
                        "group_digits": test_group,
                        "target_path": pref["path"],
                        "history_paths": super_groups[pos_name][test_group][:3]
                    })
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
    return results

# --- 5. High-Resolution Fixed Cell Width Image Engine ---
def draw_matrix_path_clean(df, target_excel_row, pos_cols, target_path, hist_paths, guess_digit, position_title):
    plt.clf() 
    colors = ["#99ff99", "#ff99c2", "#99e6ff", "#ffd1b3"] 
    cell_map, all_r, all_y = {}, [], []
    
    def add_to_map(path, col_idx):
        for p in path.split("->"):
            p = p.strip().replace("[TARGET]", "").strip("-").strip()
            if p.startswith("R") and "_Y" in p:
                r, y = int(p.split("_Y")[0][1:]) - 2, int(p.split("_Y")[1])
                if (r, y) not in cell_map: cell_map[(r, y)] = colors[col_idx]
                all_r.append(r); all_y.append(y)

    add_to_map(target_path, 0)
    for i, hp in enumerate(hist_paths): add_to_map(hp, (i % 3) + 1)
    
    target_r, target_y = target_excel_row - 2, len(pos_cols) - 1
    cell_map[(target_r, target_y)] = colors[0]
    all_r.append(target_r); all_y.append(target_y)

    def get_actual_year_label(y_idx):
        return 97 + y_idx if (97 + y_idx) < 100 else (y_idx - 3)

    colored_actual_years = set(get_actual_year_label(y) for y in all_y)
    active_years = []
    for y in range(len(pos_cols)):
        curr_act_year = get_actual_year_label(y)
        if any(abs(curr_act_year - cy) <= 1 for cy in colored_actual_years) or y == target_y:
            active_years.append(y)
            
    active_years = sorted(list(set(active_years)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    plot_rows = max_r - min_r
    plot_cols = len(active_years)

    # 📐 Cell Width ပုံသေ Lock ချ၍ ဖုန်းမျက်နှာပြင်ပေါ်တွင် စာလုံးကြီးကြီးပြသနိုင်ရန် ညှိခြင်း
    fixed_cell_width = 0.55
    fig_w = max(6, plot_cols * fixed_cell_width)
    fig_h = max(5, plot_rows * 0.42)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.subplots_adjust(left=0.1, right=0.9, top=0.92, bottom=0.1) 
    ax.axis('off')
    
    # Watermark
    fig.text(0.5, 0.5, 'GOLDEN CROSS 3D  •  PREMIUM BLUEPRINT', fontsize=22, color='#b0b0b0',
             ha='center', va='center', alpha=0.11, rotation=25, zorder=0, fontweight='bold')
    
    # 🌟 Title Layout Fix (ခေါင်းစဉ်စာသားအား Year မျဉ်းနှင့် အနီးကပ်ဆုံးညှိသည်)
    draw_number = target_excel_row - 13
    ax.set_title(f"🌟 THE GOLDEN CROSS 3D ({draw_number}/2026) {position_title} Digit {guess_digit}", 
                 fontsize=13, pad=12, weight='bold', color='#D4AF37', ha='center')

    table_data, table_colors = [], []
    for r in range(min_r, max_r):
        row_text, row_colors = [], []
        for y_idx in active_years:
            if r == target_r and y_idx == target_y:
                val = str(guess_digit)
            else:
                val = str(df.iloc[r, pos_cols[y_idx]]).strip().replace('.0','')
                if val.lower() in ['nan', 'x']: val = ''
            row_text.append(val)
            row_colors.append(cell_map.get((r, y_idx), "#f8f9fa"))
        table_data.append(row_text); table_colors.append(row_colors)
        
    col_labels = [f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in active_years]
    row_labels = [f"R-{r+2}" for r in range(min_r, max_r)]
    
    table = ax.table(cellText=table_data, cellColours=table_colors, 
                     rowLabels=row_labels, colLabels=col_labels, 
                     loc='center', cellLoc='center')
    table.scale(1, 1.5)
    table.auto_set_font_size(False)
    
    # ဆဲလ်တိုင်းကို Font Size 11 အသေ Lock ပိတ်ခြင်း
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(fixed_cell_width * 0.12)
            cell.set_linewidth(0.4)
            cell.set_edgecolor('#e0e0e0') 
            cell.get_text().set_fontsize(10)
        if (row-1, col) in [(r - min_r, active_years.index(y)) for (r, y) in cell_map.keys() if y in active_years]:
            cell.get_text().set_fontsize(12)
            cell.get_text().set_weight('bold')
            
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 6. 27 Pairs Grid Rank Combinations Engine ---
def get_tier_combinations_v9_0(results, tier_index):
    # ရမှတ်တူညီသော ထိပ်လယ်ပိတ်ဂဏန်းအားလုံးကို အဆင့်အလိုက်စနစ်တကျစုစည်းခြင်း
    def extract_digits_by_tier(pos):
        if tier_index >= len(results[pos]): return ["-"]
        target_score = results[pos][tier_index]["score"]
        return [r["digit"] for r in results[pos] if r["score"] == target_score]

    h_list = extract_digits_by_tier("Head")
    m_list = extract_digits_by_tier("Mid")
    t_list = extract_digits_by_tier("Tail")
    
    # Cartesian Product ဖြင့် ၂၇ တွဲကို အဆင့်အလိုက် Dynamic ဖြန့်ခင်းခြင်း
    combos = list(itertools.product(h_list, m_list, t_list))
    final_pairs = ["".join(c) for c in combos if "-" not in c]
    
    return " . ".join(final_pairs) if final_pairs else "No Data"

# --- 7. Session State Main Logic ---
if "results" not in st.session_state: st.session_state.results = None
if "h_cols" not in st.session_state: st.session_state.h_cols = None
if "m_cols" not in st.session_state: st.session_state.m_cols = None
if "t_cols" not in st.session_state: st.session_state.t_cols = None

with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Excel Data File (.xlsx)", type=["xlsx"])
    st.markdown("---")
    target_row = st.number_input("Excel Row Target Number", value=25, min_value=2)

if file:
    df = load_data(file)
    tab1, tab2 = st.tabs(["📊 MATRIX ANALYSIS", "📸 DESIGN PRINT"])
    
    with tab1:
        st.markdown("<h3 style='color:#D4AF37;'>📊 AI Target Matrix Analysis</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Master Filter တိုက်စစ်မည်", use_container_width=True):
            with st.spinner("ရလဒ်များကို တွက်ချက်နေပါသည်..."):
                super_groups, head_cols, mid_cols, tail_cols = build_super_groups_fast(df)
                results = evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_row)
                
                st.session_state.results = results
                st.session_state.h_cols = head_cols
                st.session_state.m_cols = mid_cols
                st.session_state.t_cols = tail_cols
                st.success("✅ တွက်ချက်မှု အောင်မြင်ပါသည်။")
        
        if st.session_state.results is not None:
            results = st.session_state.results
            h_cols, m_cols, t_cols = st.session_state.h_cols, st.session_state.m_cols, st.session_state.t_cols
            
            # ၂၇ တွဲ ဖြန့်ခင်းမှုစနစ်သစ် (v9.0 Strict Clean Tiers)
            sv_pairs = get_tier_combinations_v9_0(results, 0)
            v_pairs  = get_tier_combinations_v9_0(results, 1)
            b_pairs  = get_tier_combinations_v9_0(results, 2)
            
            copy_text = f"🥇 SUPER VIP ***\n{sv_pairs}\n\n🥈 VIP **\n{v_pairs}\n\n🥉 BACKUP *\n{b_pairs}"
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #ffcc00;">
                    <div class="metric-title" style="color:#ffcc00;">🥇 SUPER VIP ***</div>
                    <div class="metric-value">{sv_pairs}</div>
                </div>
                <div class="metric-card" style="border-left: 5px solid #00ccff;">
                    <div class="metric-title" style="color:#00ccff;">🥈 VIP **</div>
                    <div class="metric-value">{v_pairs}</div>
                </div>
                <div class="metric-card" style="border-left: 5px solid #9ca3af;">
                    <div class="metric-title" style="color:#9ca3af;">🥉 BACKUP *</div>
                    <div class="metric-value">{b_pairs}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.text_area("📋 Copy Pairs Text:", value=copy_text, height=140, disabled=True)
            st.markdown("<br><hr>", unsafe_allow_html=True)
            
            res_col1, res_col2, res_col3 = st.columns(3)
            positions_ui = [("Head (ထိပ်)", "Head", res_col1), ("Mid (အလယ်)", "Mid", res_col2), ("Tail (ပိတ်)", "Tail", res_col3)]
            
            for title, key, col in positions_ui:
                with col:
                    st.subheader(title)
                    if not results[key]: st.info("ထောက်ခံမှု မတွေ့ပါ။")
                    else:
                        for item in results[key]:
                            with st.expander(f"ဂဏန်း [ {item['digit']} ] - လမ်းကြောင်း {item['score']} ခု"):
                                groups = [item["evidence"][i:i+3] for i in range(0, len(item["evidence"]), 3)]
                                for idx, grp in enumerate(groups):
                                    st.markdown(f"**📋 GROUP-{idx+1} CODE**")
                                    package = {
                                        "target_row": target_row, "position_title": key, "guess_digit": item['digit'],
                                        "group_idx": idx + 1, "target_path": grp[0]['target_path'], "history_paths": grp[0]['history_paths']
                                    }
                                    st.code(json.dumps(package), language="json")
                                    st.markdown("---")

    with tab2:
        st.markdown("<h3 style='color:#D4AF37;'>📸 Design Print Studio</h3>", unsafe_allow_html=True)
        
        if st.session_state.h_cols is not None:
            head_cols, mid_cols, tail_cols = st.session_state.h_cols, st.session_state.m_cols, st.session_state.t_cols
        else:
            head_cols, mid_cols, tail_cols = build_super_groups_fast(df)[1:]
            
        # Paste Box Input area
        paste_input = st.text_area("📥 PASTE CODE HERE", height=100, key="studio_paste_box")
        
        if paste_input.strip():
            # 🛠 Auto Download + Auto Clear Box System (v9.0 Fixed)
            if st.button("📸 PRINT", use_container_width=True):
                try:
                    cleaned_input = re.sub(r'^>\s*', '', paste_input.strip(), flags=re.MULTILINE)
                    cleaned_input = cleaned_input.replace('\n', '').strip()
                    
                    pkg = json.loads(cleaned_input)
                    t_row = pkg["target_row"]
                    pos_title = pkg["position_title"]
                    g_digit = pkg["guess_digit"]
                    g_idx = pkg["group_idx"]
                    t_path = pkg["target_path"]
                    h_paths = pkg["history_paths"]
                    
                    current_cols = head_cols if pos_title=="Head" else (mid_cols if pos_title=="Mid" else tail_cols)
                    draw_num = t_row - 13
                    file_naming = f"{draw_num}-2026_{pos_title}_Digit_{g_digit}_Group_{g_idx}.jpg"
                    
                    img_data = draw_matrix_path_clean(df, t_row, current_cols, t_path, h_paths, g_digit, pos_title)
                    
                    # JS Injection for Instant Downloader
                    b64_img = base64.b64encode(img_data.getvalue()).decode()
                    js_script = f"""
                        <a id="auto_dl_link" href="data:image/jpeg;base64,{b64_img}" download="{file_naming}"></a>
                        <script>
                            document.getElementById('auto_dl_link').click();
                        </script>
                    """
                    st.components.v1.html(js_script, height=0)
                    st.success(f"🎯 Blueprint `{file_naming}` အား ဖုန်းထဲသို့ အလိုအလျောက် ဒေါင်းလုဒ်ရယူပြီးပါပြီ။")
                    
                    # 🔒 Box စာသားကို ရှင်းလင်းပစ်ပြီးမှ Refresh ခေါ်ခြင်း
                    st.session_state.studio_paste_box = ""
                    st.rerun()
                    
                except Exception as e:
                    st.error("❌ စာသားပုံစံ မမှန်ကန်ပါ။ Tab 1 မှ ကုဒ်တစ်ခုလုံးကို ပြန်လည်ကူးယူလာပါ။")
else:
    st.info("💡 စတင်ရန်အတွက် ဘယ်ဘက် Sidebar Panel တွင် Excel (.xlsx) ဒေတာဖိုင်ကို အရင်ဆုံး တင်ပေးပါ Bro!")
