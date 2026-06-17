import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data Processing & Logic Engine ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

@st.cache_data
def build_super_groups(df):
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    history_counts = {"Head": {}, "Mid": {}, "Tail": {}}
    
    # Set အစား Dict ဖြင့်ပြောင်းသိမ်းမည် (History လမ်းကြောင်းများကို အရောင်ခြယ်ရန် ပြန်ခေါ်သုံးနိုင်ရန်)
    super_groups = {"Head": {}, "Mid": {}, "Tail": {}} 
    
    max_rows = len(df)
    total_years = len(head_cols)
    max_y = total_years - 1 
    
    for pos_name, cols in positions:
        for y_idx in range(max_y):
            for r in range(max_rows):
                for y_step in range(5):
                    for r_step in range(-4, 5):
                        if y_step == 0 and r_step == 0: 
                            continue
                        
                        digits = []
                        path_str = []
                        valid = True
                        for i in range(4):
                            curr_r = r + i * r_step
                            curr_y = y_idx + i * y_step
                            
                            if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y:
                                valid = False
                                break
                            
                            val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                            if val.lower() == 'x' or val == '' or val == 'nan':
                                valid = False
                                break
                                
                            if val.endswith('.0'): val = val[:-2]
                            digits.append(val)
                            path_str.append(f"R{curr_r+2}_Y{curr_y}")
                            
                        if valid:
                            dtup = tuple(digits)
                            pstr = "->".join(path_str)
                            if dtup not in history_counts[pos_name]:
                                history_counts[pos_name][dtup] = set()
                            history_counts[pos_name][dtup].add(pstr) 
                            
        for dtup, paths in history_counts[pos_name].items():
            if len(paths) >= 3:
                # History လမ်းကြောင်းများကို သိမ်းဆည်းထားမည်
                super_groups[pos_name][dtup] = list(paths)
                
    return super_groups, head_cols, mid_cols, tail_cols

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
                if y_step == 0 and r_step == 0: 
                    continue
                
                start_r = target_r - 3 * r_step
                start_y = target_y - 3 * y_step
                
                if start_r < 0 or start_r >= max_rows or start_y < 0:
                    continue
                    
                valid = True
                digits = []
                path_str = []
                for i in range(3):
                    curr_r = start_r + i * r_step
                    curr_y = start_y + i * y_step
                    
                    if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= len(cols):
                        valid = False
                        break
                        
                    val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                    if val.lower() == 'x' or val == '' or val == 'nan':
                        valid = False
                        break
                    if val.endswith('.0'): val = val[:-2]
                    digits.append(val)
                    path_str.append(f"R{curr_r+2}_Y{curr_y}")
                    
                if valid:
                    prefixes.append({
                        "prefix": tuple(digits),
                        "path": f"{' -> '.join(path_str)} -> [TARGET]"
                    })
        
        pos_results = []
        for guess in range(10):
            guess_str = str(guess)
            matches = []
            for pref in prefixes:
                test_group = pref["prefix"] + (guess_str,)
                if test_group in super_groups[pos_name]:
                    # Target နှင့် တိုက်ဆိုင်သော History လမ်းကြောင်းများကို ဆွဲထုတ်ခြင်း
                    hist_paths = super_groups[pos_name][test_group]
                    matches.append({
                        "group_digits": test_group,
                        "target_path": pref["path"],
                        "history_paths": hist_paths[:3] # အများဆုံး History ၃ ခုကိုသာ ယူမည်
                    })
                    
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
        
    return results

# --- 2. Image Generation Engine (2D Auto-Crop & Multi-Color) ---
def generate_matrix_image(df, target_excel_row, position_key, pos_cols, match_data):
    # Colors: Target(Green), Hist1(Pink), Hist2(Cyan), Hist3(Orange)
    colors = ["#99ff99", "#ff99c2", "#99e6ff", "#ffd1b3"] 
    
    cell_color_map = {}
    all_r = []
    all_y = []
    
    # Path အား ဖြတ်တောက်၍ Coordinate ယူမည့် Helper Function
    def parse_path(path_str, color_code):
        parts = path_str.split("->")
        for p in parts:
            p = p.strip()
            if p.startswith("R") and "_Y" in p:
                r_part, y_part = p.split("_Y")
                r_idx = int(r_part[1:]) - 2 
                y_idx = int(y_part)
                
                # အရောင်မထပ်စေရန် (ပထမဆုံးရောက်သော အရောင်ကိုသာ ယူမည်)
                if (r_idx, y_idx) not in cell_color_map:
                    cell_color_map[(r_idx, y_idx)] = color_code
                all_r.append(r_idx)
                all_y.append(y_idx)

    # 1. Target Path ကို အစိမ်းရောင် ခြယ်မည်
    parse_path(match_data["target_path"], colors[0])
    
    # Target End Point အတိအကျကို အစိမ်းရောင် ထပ်ခြယ်မည်
    target_r = target_excel_row - 2
    target_y = len(pos_cols) - 1
    cell_color_map[(target_r, target_y)] = colors[0]
    all_r.append(target_r)
    all_y.append(target_y)

    # 2. History Paths များကို အရောင်ခွဲ၍ ခြယ်မည်
    for i, h_path in enumerate(match_data["history_paths"]):
        c_idx = (i + 1) % len(colors)
        parse_path(h_path, colors[c_idx])

    if not all_r or not all_y:
        return None

    # 3. 2D Auto-Crop Logic (လမ်းကြောင်းရှိသော ဧရိယာကိုသာ ဖြတ်ထုတ်မည်)
    min_r = max(0, min(all_r) - 2)
    max_r = min(len(df), max(all_r) + 3)
    min_y = max(0, min(all_y) - 1)
    max_y = min(len(pos_cols), max(all_y) + 2)
    
    plot_rows = max_r - min_r
    plot_cols = max_y - min_y

    fig, ax = plt.subplots(figsize=(plot_cols * 1.2, plot_rows * 0.6))
    ax.axis('off')
    
    cell_text = []
    cell_colors = []
    
    for r in range(min_r, max_r):
        row_text = []
        row_colors = []
        for y_idx in range(min_y, max_y):
            val = str(df.iloc[r, pos_cols[y_idx]]).strip()
            if val.lower() in ['nan', 'x']: val = ''
            if val.endswith('.0'): val = val[:-2]
            row_text.append(val)
            
            if (r, y_idx) in cell_color_map:
                row_colors.append(cell_color_map[(r, y_idx)])
            else:
                row_colors.append("#f0f0f0") # Default Color
                
        cell_text.append(row_text)
        cell_colors.append(row_colors)
        
    col_labels = [f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in range(min_y, max_y)]
    row_labels = [f"R-{r+2}" for r in range(min_r, max_r)]
    
    table = ax.table(cellText=cell_text, cellColours=cell_colors, 
                     rowLabels=row_labels, colLabels=col_labels, 
                     loc='center', cellLoc='center')
    
    table.scale(1, 1.8)
    table.set_fontsize(12)
    
    # မြန်မာဖောင့် Issue မဖြစ်စေရန် key (Head/Mid/Tail) ကိုသာ Title အဖြစ် သုံးထားသည်
    plt.title(f"Golden Cross: {position_key} Path Analysis", fontsize=16, fontweight='bold', pad=15)
    
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

# --- 3. Streamlit UI Build ---
st.set_page_config(page_title="Golden Cross 3D - Master Filter", layout="wide")
st.title("🎯 The Golden Cross 3D - Master Filter Engine")

uploaded_file = st.file_uploader("Excel (.xlsx) ဒေတာဖိုင်ကို ထည့်ပါ", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("ယခုအကြိမ် နေရာ (Target)")
        target_excel_row = st.number_input("Excel Row Number ကို ရိုက်ထည့်ပါ (ဥပမာ - 25)", min_value=2, max_value=len(df)+1, value=25)
        run_btn = st.button("🚀 Master Filter ဖြင့် တိုက်စစ်မည်", use_container_width=True)

    if run_btn:
        with st.spinner("History Data များကို Super Group အဖြစ် သန့်စင်နေပါသည်..."):
            super_groups, head_cols, mid_cols, tail_cols = build_super_groups(df)
            
        with st.spinner("Target ဖြင့် တိုက်စစ်နေပါသည်..."):
            results = evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_excel_row)
            
            st.markdown("---")
            st.header("🏆 Master Filter Analysis Results")
            
            res_col1, res_col2, res_col3 = st.columns(3)
            positions_ui = [("Head (ထိပ်)", "Head", res_col1), ("Mid (အလယ်)", "Mid", res_col2), ("Tail (ပိတ်)", "Tail", res_col3)]
            
            for title, key, col in positions_ui:
                with col:
                    st.subheader(title)
                    if not results[key]:
                        st.info("ဤအကြိမ်အတွက် ခိုင်မာသော ထောက်ခံမှု မတွေ့ပါ။")
                    else:
                        for item in results[key]:
                            with st.expander(f"ဂဏန်း [ {item['digit']} ] - ထောက်ခံသည့် လမ်းကြောင်း {item['score']} ခု"):
                                # Target လမ်းကြောင်း တစ်ခုချင်းစီအတွက် ပုံထုတ်ရန် Button များ ခွဲထုတ်ထားသည်
                                for i, match_data in enumerate(item["evidence"]):
                                    st.markdown(f"**Target Path {i+1}:** `{match_data['target_path']}`")
                                    
                                    img_buf = generate_matrix_image(df, target_excel_row, key, 
                                                                    head_cols if key=="Head" else (mid_cols if key=="Mid" else tail_cols), 
                                                                    match_data)
                                    if img_buf:
                                        st.download_button(
                                            label=f"📸 လမ်းကြောင်း {i+1} ကို ပုံထုတ်ရန်",
                                            data=img_buf,
                                            file_name=f"GC_{key}_Digit{item['digit']}_Path{i+1}.jpg",
                                            mime="image/jpeg",
                                            use_container_width=True
                                        )
                                    st.markdown("---")
