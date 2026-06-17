import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data Processing & Logic Engine ---
@st.cache_data
def load_data(file_path):
    # Excel ဖိုင်ကို ဖတ်ခြင်း
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    # Header ကို ဖယ်၍ Data သီးသန့်ယူခြင်း (Index 0 = Excel Row 2)
    return df.iloc[1:].reset_index(drop=True)

@st.cache_data
def build_super_groups(df):
    # Head, Mid, Tail Columns များ ရှာဖွေခြင်း (1, 4, 7... / 2, 5, 8... / 3, 6, 9...)
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    history_counts = {"Head": {}, "Mid": {}, "Tail": {}}
    super_groups = {"Head": set(), "Mid": set(), "Tail": set()}
    
    max_rows = len(df)
    total_years = len(head_cols)
    max_y = total_years - 1 # 2026 ကို ချန်ထားပြီး History အဖြစ်ယူမည်
    
    for pos_name, cols in positions:
        for y_idx in range(max_y):
            for r in range(max_rows):
                for y_step in range(5):
                    for r_step in range(-4, 5):
                        # ရွေ့လျားမှုမရှိသော လမ်းကြောင်းကို ပယ်မည်
                        if y_step == 0 and r_step == 0: 
                            continue
                        
                        digits = []
                        path_str = []
                        valid = True
                        for i in range(4):
                            curr_r = r + i * r_step
                            curr_y = y_idx + i * y_step
                            
                            # Limit ကျော်လွန်ပါက ပယ်မည်
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
                            
                        # Valid ဖြစ်သော ၄ လုံးတွဲ Group ကို မှတ်သားမည်
                        if valid:
                            dtup = tuple(digits)
                            pstr = "->".join(path_str)
                            if dtup not in history_counts[pos_name]:
                                history_counts[pos_name][dtup] = set()
                            history_counts[pos_name][dtup].add(pstr) # Duplicate ရှင်းရန် set ဖြင့်သိမ်းသည်
                            
        # Super Group ဖွဲ့ခြင်း (လမ်းကြောင်းမတူဘဲ အနည်းဆုံး ၃ ကြိမ် ရှိရမည်)
        for dtup, paths in history_counts[pos_name].items():
            if len(paths) >= 3:
                super_groups[pos_name].add(dtup)
                
    return super_groups, head_cols, mid_cols, tail_cols

def evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_excel_row):
    # User ရိုက်ထည့်သော Excel Row (ဥပမာ ၂၅) ကို DataFrame Index သို့ ပြောင်းခြင်း
    target_r = target_excel_row - 2 
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    results = {}
    
    target_y = len(head_cols) - 1 # 2026 (နောက်ဆုံး Column အုပ်စု)
    max_rows = len(df)
    
    for pos_name, cols in positions:
        prefixes = []
        # Target သို့ ဦးတည်လာသော လမ်းကြောင်းများ ရှာဖွေခြင်း (Reverse Tracking)
        for y_step in range(5):
            for r_step in range(-4, 5):
                if y_step == 0 and r_step == 0: 
                    continue
                
                # End point မှနေ၍ Start point ကို နောက်ပြန်ရှာခြင်း
                start_r = target_r - 3 * r_step
                start_y = target_y - 3 * y_step
                
                if start_r < 0 or start_r >= max_rows or start_y < 0:
                    continue
                    
                valid = True
                digits = []
                path_str = []
                # Prefix ၃ လုံးကို ဆွဲထုတ်ခြင်း
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
                        "path": f"Path: {' -> '.join(path_str)} -> [TARGET]"
                    })
        
        # 0 မှ 9 အထိ Target နေရာတွင် အစားထိုး၍ တိုက်စစ်ခြင်း
        pos_results = []
        for guess in range(10):
            guess_str = str(guess)
            matches = []
            for pref in prefixes:
                test_group = pref["prefix"] + (guess_str,)
                # History ထဲမှ Super Group များတွင် ပါဝင်ခြင်း ရှိ/မရှိ စစ်ဆေးခြင်း
                if test_group in super_groups[pos_name]:
                    matches.append(f"Group {test_group} ({pref['path']})")
                    
            # အနည်းဆုံး Super Group ၃ ခုက ထောက်ခံမှသာ အတည်ပြုမည်
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        
        # ထောက်ခံမှု (Score) အများဆုံးကို အပေါ်တွင် ပြရန် စီစဉ်ခြင်း
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
        
    return results

# --- 2. Image Generation Engine (ပုံထုတ်သည့်စနစ်) ---
def generate_matrix_image(df, target_excel_row, position_name, pos_cols, matched_paths_list):
    highlight_cells = set()
    for path_str in matched_paths_list:
        parts = path_str.split("->")
        for p in parts:
            p = p.strip()
            if p.startswith("R") and "_Y" in p:
                r_part, y_part = p.split("_Y")
                r_idx = int(r_part[1:]) - 2 
                y_idx = int(y_part)
                highlight_cells.add((r_idx, y_idx))

    if not highlight_cells:
        return None

    # Auto-Crop Logic: လမ်းကြောင်းရှိသော ဧရိယာကိုသာ ဖြတ်ထုတ်ခြင်း
    target_r = target_excel_row - 2
    min_r = max(0, min([r for r, y in highlight_cells] + [target_r]) - 3)
    max_r = min(len(df), max([r for r, y in highlight_cells] + [target_r]) + 4)
    
    plot_rows = max_r - min_r
    plot_cols = len(pos_cols)

    fig, ax = plt.subplots(figsize=(plot_cols * 1.0, plot_rows * 0.5))
    ax.axis('off')
    
    cell_text = []
    cell_colors = []
    
    for r in range(min_r, max_r):
        row_text = []
        row_colors = []
        for y_idx in range(plot_cols):
            val = str(df.iloc[r, pos_cols[y_idx]]).strip()
            if val.lower() == 'nan' or val == 'x': val = ''
            if val.endswith('.0'): val = val[:-2]
            row_text.append(val)
            
            # အရောင်ခြယ်ခြင်း Logic
            if (r, y_idx) in highlight_cells:
                row_colors.append("#ff9999") # Highlight Path (အနီနုရောင်)
            elif r == target_r and y_idx == plot_cols - 1:
                row_colors.append("#99ff99") # Target Place (အစိမ်းနုရောင်)
            else:
                row_colors.append("#f0f0f0") # Default (မီးခိုးနုရောင်)
                
        cell_text.append(row_text)
        cell_colors.append(row_colors)
        
    # ခေါင်းစဉ်နှင့် ဇယားဘေးတန်း စာသားများ (Year 97 ကနေ စမည်)
    col_labels = [f"{97 + i}" if (97 + i) < 100 else f"{i - 3:02d}" for i in range(plot_cols)]
    row_labels = [f"R-{r+2}" for r in range(min_r, max_r)]
    
    table = ax.table(cellText=cell_text, cellColours=cell_colors, 
                     rowLabels=row_labels, colLabels=col_labels, 
                     loc='center', cellLoc='center')
    
    table.scale(1, 1.8)
    table.set_fontsize(11)
    
    plt.title(f"The Golden Cross 3D: {position_name} Matrix Path", fontsize=15, fontweight='bold', pad=15)
    
    # 300 DPI ဖြင့် Save ခြင်း
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

# --- 3. Streamlit UI Build ---
st.set_page_config(page_title="Golden Cross 3D - Master Filter", layout="wide")
st.title("🎯 The Golden Cross 3D - Master Filter Engine")
st.markdown("History ထဲမှ လမ်းကြောင်းပေါင်း သောင်းချီကို AI Logic ဖြင့် စစ်ထုတ်၍ အတိကျဆုံး ဂဏန်းများကို ရှာဖွေပါ")

uploaded_file = st.file_uploader("Bro ရဲ့ Excel (.xlsx) ဒေတာဖိုင်ကို ထည့်ပါ", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("ယခုအကြိမ် နေရာ (Target)")
        target_excel_row = st.number_input("တွက်လိုသော Excel Row Number ကို ရိုက်ထည့်ပါ (ဥပမာ - ၁၂ ကြိမ်မြောက်အတွက် 25)", min_value=2, max_value=len(df)+1, value=25)
        run_btn = st.button("🚀 Master Filter ဖြင့် တိုက်စစ်မည်", use_container_width=True)

    if run_btn:
        with st.spinner("History Data များကို Super Group အဖြစ် သန့်စင်နေပါသည်..."):
            super_groups, head_cols, mid_cols, tail_cols = build_super_groups(df)
            st.success(f"✅ Data သန့်စင်ခြင်း အောင်မြင်ပါသည်။ တွေ့ရှိသော Super Group များ: Head ({len(super_groups['Head']):,}), Mid ({len(super_groups['Mid']):,}), Tail ({len(super_groups['Tail']):,})")
            
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
                                all_paths = []
                                for ev in item["evidence"]:
                                    st.markdown(f"- `{ev}`")
                                    all_paths.append(ev)
                                
                                # JPEG ထုတ်မည့် ခလုတ်များ
                                img_buf = generate_matrix_image(df, target_excel_row, title, 
                                                                head_cols if key=="Head" else (mid_cols if key=="Mid" else tail_cols), 
                                                                all_paths)
                                if img_buf:
                                    st.download_button(
                                        label=f"📸 {item['digit']} အတွက် ပုံထုတ်ရန်",
                                        data=img_buf,
                                        file_name=f"GoldenCross_{key}_Digit_{item['digit']}.jpg",
                                        mime="image/jpeg",
                                        use_container_width=True
                                    )
