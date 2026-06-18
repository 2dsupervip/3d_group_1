import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import json
import re
import itertools

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
        margin-bottom: 10px;
    }
    .metric-title { font-size: 15px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { color: #ffffff; font-size: 18px; font-weight: 500; letter-spacing: 1px; }
    
    /* Button Styling */
    div.stButton > button {
        background-color: #D4AF37 !important; color: #0e1117 !important; 
        font-weight: bold !important; font-size: 15px !important;
        border-radius: 8px !important; transition: all 0.3s ease !important;
    }
    div.stButton > button:hover { background-color: #f3cd44 !important; transform: scale(1.01); }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Loading Engine ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 3. History Core Engine ---
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
        for y_idx in range(max_y):
            for r in range(max_rows):
                for y_step in range(5):
                    for r_step in range(-4, 5):
                        if y_step == 0 and r_step == 0: continue
                        
                        digits, path_str, valid = [], [], True
                        for i in range(4):
                            curr_r = r + i * r_step
                            curr_y = y_idx + i * y_step
                            if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y:
                                valid = False; break
                            val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                            if val.lower() in ['x', 'nan', '']:
                                valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            digits.append(val)
                            path_str.append(f"R{curr_r+2}_Y{curr_y}")
                            
                        if valid:
                            dtup = tuple(digits)
                            if dtup not in history_counts: history_counts[dtup] = set()
                            history_counts[dtup].add("->".join(path_str))
                            
        for dtup, paths in history_counts.items():
            if len(paths) >= 3: 
                super_groups[pos_name][dtup] = list(paths)
                
    return super_groups, head_cols, mid_cols, tail_cols

# --- 4. Stable Target Evaluator Engine ---
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

# --- 5. Premium Image Engine (Calendar Overlap Correctly Checked v7.6) ---
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

    # 🛠 [လော့ဂျစ်အမှန်ပြင်ဆင်ချက်] Column Space အစား ကလင်ဒါနှစ် (Actual Year) ကို အခြေခံ၍ Smart Crop ပြုလုပ်ခြင်း
    def get_actual_year_label(y_idx):
        return 97 + y_idx if (97 + y_idx) < 100 else (y_idx - 3)

    colored_actual_years = set(get_actual_year_label(y) for y in all_y)
    active_years = []
    
    for y in range(len(pos_cols)):
        curr_act_year = get_actual_year_label(y)
        # မိမိနှစ် သို့မဟုတ် ဘေးချင်းကပ်နှစ်များ ကလင်ဒါအရကိုက်ညီလျှင် ချန်လှပ်မည်
        if any(abs(curr_act_year - cy) <= 1 for cy in colored_actual_years) or y == target_y:
            active_years.append(y)
            
    active_years = sorted(list(set(active_years)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    plot_rows = max_r - min_r
    plot_cols = len(active_years)

    # 📐 Layout ကို သုံးဖက်ပတ်လည် .3 Margin အပြည့်ချန်ခြင်း
    fig, ax = plt.subplots(figsize=(max(plot_cols * 0.42, 5), max(plot_rows * 0.42, 4)))
    fig.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.12) 
    ax.axis('off')
    
    # 🔒 PREMIUM BACKGROUND WATERMARK
    fig.text(0.5, 0.5, 'GOLDEN CROSS 3D  •  PREMIUM BLUEPRINT', fontsize=24, color='#b0b0b0',
             ha='center', va='center', alpha=0.12, rotation=25, zorder=0, fontweight='bold')
    
    # 🌟 ULTRA-TIGHT GOLDEN TITLE (ခေါင်းစဉ်စာသားကို ဇယားထိပ်သို့ အနီးကပ်ဆုံး ထိုးသိပ်ကပ်ထားပါသည်)
    draw_number = target_excel_row - 13
    ax.text(0.5, 0.98, f"🌟 THE GOLDEN CROSS 3D ({draw_number}/2026) {position_title} Digit {guess_digit}", 
            fontsize=13, weight='bold', color='#D4AF37', ha='center', transform=ax.transAxes)

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
    table.set_fontsize(9)
    
    # 📐 Column Width စနစ်တကျ ကျဉ်းမြောင်းစေခြင်း
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(0.052)
            cell.set_linewidth(0.4)
            cell.set_edgecolor('#e0e0e0') 
        if (row-1, col) in [(r - min_r, active_years.index(y)) for (r, y) in cell_map.keys() if y in active_years]:
            cell.get_text().set_fontsize(11)
            cell.get_text().set_weight('bold')
            
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 6. Helper Function for Advanced Pairs Grouping ---
def get_tier_combinations(results, tier_index):
    # သက်ဆိုင်ရာ Rank အလိုက် ဒေတာရှိမရှိ စစ်ဆေးပြီး အစုအဖွဲ့အတွဲလိုက်ထုတ်ပေးရန်
    h_list = [results["Head"][tier_index]["digit"]] if tier_index < len(results["Head"]) else []
    m_list = [results["Mid"][tier_index]["digit"]] if tier_index < len(results["Mid"]) else []
    t_list = [results["Tail"][tier_index]["digit"]] if tier_index < len(results["Tail"]) else []
    
    # အကယ်၍ ရမှတ်တူညီသော ဂဏန်းများရှိခဲ့ပါက ၎င်းတို့ကိုပါ ထည့်သွင်းတွက်ချက်ရန်
    if tier_index < len(results["Head"]):
        h_score = results["Head"][tier_index]["score"]
        h_list = [r["digit"] for r in results["Head"] if r["score"] == h_score]
    if tier_index < len(results["Mid"]):
        m_score = results["Mid"][tier_index]["score"]
        m_list = [r["digit"] for r in results["Mid"] if r["score"] == m_score]
    if tier_index < len(results["Tail"]):
        t_score = results["Tail"][tier_index]["score"]
        t_list = [r["digit"] for r in results["Tail"] if r["score"] == t_score]
        
    if not h_list: h_list = ["-"]
    if not m_list: m_list = ["-"]
    if not t_list: t_list = ["-"]
    
    # Cartesian Product ဖြင့် ပေါင်းစပ်နိုင်သမျှ အတွဲအစပ်အားလုံးထုတ်ယူခြင်း
    combos = list(itertools.product(h_list, m_list, t_list))
    return " . ".join(["".join(c) for c in combos])

# --- 7. Session State Initializing ---
if "results" not in st.session_state: st.session_state.results = None
if "h_cols" not in st.session_state: st.session_state.h_cols = None
if "m_cols" not in st.session_state: st.session_state.m_cols = None
if "t_cols" not in st.session_state: st.session_state.t_cols = None
if "paste_box_value" not in st.session_state: st.session_state.paste_box_value = ""

# --- 8. Sidebar Panel ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Excel Data File (.xlsx)", type=["xlsx"])
    st.markdown("---")
    target_row = st.number_input("Excel Row Target Number", value=25, min_value=2)
    st.markdown("<br><p style='color:#888;'>v7.6 Perfect Logic Edition</p>", unsafe_allow_html=True)

# --- 9. Main Application Interface ---
if file:
    df = load_data(file)
    
    tab1, tab2 = st.tabs(["📊 MATRIX ANALYSIS", "📸 DESIGN PRINT"])
    
    with tab1:
        st.markdown("<h3 style='color:#D4AF37;'>📊 AI Target Matrix Analysis</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Master Filter တိုက်စစ်မည်", use_container_width=True):
            with st.spinner("ရလဒ်များကို စက္ကန့်ပိုင်းအတွင်း တွက်ချက်နေပါသည်..."):
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
            
            # 🛠 [လော့ဂျစ်အသစ်] စနစ်ကျသော ၃ လုံးတွဲ ကွက်တိအတွဲအစပ်စနစ် (Tier Formatting)
            pairs_super = get_tier_combinations(results, 0)
            pairs_vip   = get_tier_combinations(results, 1)
            pairs_backup = get_tier_combinations(results, 2)
            
            # Format တကျ စုစည်းထားသော စာသားပုံစံ
            copy_text = f"🥇 SUPER VIP ***\n{pairs_super}\n\n🥈 VIP **\n{pairs_vip}\n\n🥉 BACKUP *\n{pairs_backup}"
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # UI Displays
            st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #ffcc00;">
                    <div class="metric-title" style="color:#ffcc00;">🥇 SUPER VIP ***</div>
                    <div class="metric-value">{pairs_super}</div>
                </div>
                <div class="metric-card" style="border-left: 5px solid #00ccff;">
                    <div class="metric-title" style="color:#00ccff;">🥈 VIP **</div>
                    <div class="metric-value">{pairs_vip}</div>
                </div>
                <div class="metric-card" style="border-left: 5px solid #9ca3af;">
                    <div class="metric-title" style="color:#9ca3af;">🥉 BACKUP *</div>
                    <div class="metric-value">{pairs_backup}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # 📋 COPY AREA
            st.text_area("📋 Copy Pairs Text (အောက်ကခလုတ်ဖြင့် တိုက်ရိုက်ကူးယူနိုင်ပါသည်):", value=copy_text, height=130, disabled=True)
            
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
            
        # Paste Input Box
        paste_input = st.text_area("📥 PASTE CODE HERE", value=st.session_state.paste_box_value, height=100, key="paste_box_area")
        
        if paste_input.strip():
            if st.button("📸 PRINT BLUEPRINT", use_container_width=True):
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
                    
                    # Image generation in RAM memory
                    img_data = draw_matrix_path_clean(df, t_row, current_cols, t_path, h_paths, g_digit, pos_title)
                    
                    st.success(f"🎯 Blueprint ဖန်တီးမှု အောင်မြင်သည်- {pos_title} Digit {g_digit} (အုပ်စု {g_idx})")
                    
                    # 🚀 AUTO DOWNLOAD TRIGGER BUTTON
                    st.download_button(
                        label="📥 DOWNLOAD NOW (ဖုန်းထဲသို့တိုက်ရိုက်သိမ်းဆည်းရန်နှိပ်ပါ)",
                        data=img_data,
                        file_name=file_naming,
                        mime="image/jpeg",
                        use_container_width=True,
                        key="direct_download_trigger"
                    )
                    
                    # Box စာသားကို ချက်ချင်းရှင်းလင်းပစ်ခြင်း
                    st.session_state.paste_box_value = ""
                    
                except Exception as e:
                    st.error("❌ စာသားပုံစံ မမှန်ကန်ပါ။ Tab 1 မှ ကုဒ်တစ်ခုလုံးကို အစအဆုံး ပြန်ကူးပေးပါ။")
else:
    st.info("💡 စတင်ရန်အတွက် ဘယ်ဘက် Sidebar Panel တွင် Excel (.xlsx) ဒေတာဖိုင်ကို အရင်ဆုံး တင်ပေးပါ Bro!")
