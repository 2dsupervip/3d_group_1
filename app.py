import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data Loading ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 2. History Core Engine ---
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

# --- 3. Stable Target Evaluator Engine ---
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
                    prefixes.append({
                        "prefix": tuple(digits), 
                        "path": f"{' -> '.join(path_str)} -> [TARGET]",
                        "r_step": r_step,
                        "y_step": y_step
                    })
        
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
                        "history_paths": super_groups[pos_name][test_group],
                        "target_r_step": pref["r_step"],
                        "target_y_step": pref["y_step"]
                    })
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
    return results

# --- 4. Beautiful & Sharp Premium Image Engine ---
def draw_matrix_path_clean(df, target_excel_row, pos_cols, target_path, raw_hist_paths, target_r_step, target_y_step, guess_digit, position_title):
    plt.clf() 
    colors = ["#99ff99", "#ff99c2", "#99e6ff", "#ffd1b3"] # စိမ်း၊ နီ၊ ပြာ၊ လိမ္မော်
    cell_map, all_r, all_y = {}, [], []
    
    # ၁။ Target လမ်းကြောင်းကို အရင်မြေပုံသွင်းမည်
    for p in target_path.split("->"):
        p = p.strip().replace("[TARGET]", "").strip("-").strip()
        if p.startswith("R") and "_Y" in p:
            r, y = int(p.split("_Y")[0][1:]) - 2, int(p.split("_Y")[1])
            cell_map[(r, y)] = colors[0]
            all_r.append(r); all_y.append(y)
            
    # ၂။ History လမ်းကြောင်းများထဲမှ Target နှင့် တိုင်မင်ခြေလှမ်း (Steps) ကွက်တိကိုက်ညီသော ထိပ်တန်း ၃ ခုကိုသာ စစ်ထုတ်၍ အရောင်ခြယ်မည်
    valid_hist_count = 0
    for hp in raw_hist_paths:
        if valid_hist_count >= 3: break
        p_parts = hp.split("->")
        if len(p_parts) == 4:
            r0 = int(p_parts[0].split("_Y")[0][1:]) - 2
            y0 = int(p_parts[0].split("_Y")[1])
            r1 = int(p_parts[1].split("_Y")[0][1:]) - 2
            y1 = int(p_parts[1].split("_Y")[1])
            
            # ခြေလှမ်း အကွာအဝေး ကိုက်ညီမှု ရှိ/မရှိ စစ်ဆေးခြင်း
            if (r1 - r0 == target_r_step) and (y1 - y0 == target_y_step):
                valid_hist_count += 1
                col_idx = valid_hist_count # ၁၊ ၂၊ ၃ (နီ၊ ပြာ၊ လိမ္မော်)
                for pt in p_parts:
                    r, y = int(pt.split("_Y")[0][1:]) - 2, int(pt.split("_Y")[1])
                    if (r, y) not in cell_map: 
                        cell_map[(r, y)] = colors[col_idx % 4]
                    all_r.append(r); all_y.append(y)

    # ၃။ ယခုလက်ရှိအကြိမ် Target နေရာကို အစိမ်းရောင် သတ်မှတ်ခြင်း
    target_r, target_y = target_excel_row - 2, len(pos_cols) - 1
    cell_map[(target_r, target_y)] = colors[0]
    all_r.append(target_r); all_y.append(target_y)

    active_years = sorted(list(set(all_y)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    plot_rows, plot_cols = max_r - min_r, len(active_years)

    # ပုံထွက် မျက်နှာစာ အချိုးအစား ညှိနှိုင်းခြင်း
    fig, ax = plt.subplots(figsize=(max(plot_cols * 0.85, 6), max(plot_rows * 0.48, 4.5)))
    fig.subplots_adjust(left=0.15, right=0.85, top=0.8, bottom=0.2) 
    ax.axis('off')
    
    # 🔒 PREMIUM WATERMARK (မှုန်ပျပျ ပါးပါးကြည်ကြည်လေးဖြင့် အဆင့်မြင့်စွာ ၅ ကြောင်း ခင်းခြင်း)
    watermark_positions = [0.22, 0.36, 0.50, 0.64, 0.78]
    for wp in watermark_positions:
        fig.text(0.5, wp, 'GOLDEN CROSS 3D', fontsize=36, color='#dcdcdc',
                 ha='center', va='center', alpha=0.28, rotation=35, zorder=0)
    
    # 🌟 FIXED HIGH-TECH TITLE (ဇယားကွက်၏ ထိပ်ဆုံး အလယ်ဗဟိုတွင် တပ်ဆင်ခြင်း)
    draw_number = target_excel_row - 13
    ax.set_title(f"🌟 THE GOLDEN CROSS 3D ({draw_number}/2026) {position_title} Digit {guess_digit}", 
                 fontsize=14, pad=25, weight='bold', color='#111111', ha='center')

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
            
            # မူရင်း ဆဲလ်ကွက်များကို မျက်စိအေးစေသော မီးခိုးနုရောင် Soft Background ပေးခြင်း
            row_colors.append(cell_map.get((r, y_idx), "#fcfcfc"))
        table_data.append(row_text); table_colors.append(row_colors)
        
    table = ax.table(cellText=table_data, cellColours=table_colors, 
                     rowLabels=[f"R-{r+2}" for r in range(min_r, max_r)], 
                     colLabels=[f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in active_years], 
                     loc='center', cellLoc='center')
    table.scale(1, 1.6)
    table.set_fontsize(10)
    
    # ဆဲလ်ကွက်များအတွင်း စာလုံးအကြီးအသေးနှင့် အကျယ်အဝန်းကို အချောသပ်ခြင်း
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(0.075)
            cell.set_linewidth(0.5)
            cell.set_edgecolor('#e0e0e0') # ဇယားလိုင်းများကို နုနုလေးပြောင်းခြင်း
        if (row-1, col) in [(r - min_r, active_years.index(y)) for (r, y) in cell_map.keys()]:
            cell.get_text().set_fontsize(13)
            cell.get_text().set_weight('bold')
            
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 5. @st.fragment Lazy Image UI Module ---
@st.fragment
def render_group_image_ui(df, target_row, current_cols, key, item_digit, idx, grp):
    draw_number = target_row - 13
    file_naming = f"{draw_number}-2026_{key}_Digit_{item_digit}_Group_{idx+1}.jpg"
    
    # Target ခြေလှမ်းများကို လှမ်းယူခြင်း
    target_r_step = grp[0]['target_r_step']
    target_y_step = grp[0]['target_y_step']
    
    st.download_button(
        label=f"📥 အုပ်စု {idx+1} ပုံထုတ်မည် (Download)",
        data=draw_matrix_path_clean(df, target_row, current_cols, grp[0]['target_path'], grp[0]['history_paths'], target_r_step, target_y_step, item_digit, key),
        file_name=file_naming,
        mime="image/jpeg",
        key=f"dl_confirm_{key}_{item_digit}_grp_{idx}",
        use_container_width=True
    )

# --- 6. Streamlit Main UI ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D")
st.title("🎯 Golden Cross 3D - Masterpiece Premium Engine v4.4")

file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if file:
    df = load_data(file)
    target_row = st.number_input("Excel Row Number", value=25, min_value=2)
    
    if "results" not in st.session_state:
        st.session_state.results = None
        st.session_state.h_cols = None
        st.session_state.m_cols = None
        st.session_state.t_cols = None

    if st.button("🚀 Master Filter ဖြင့် တိုက်စစ်မည်", use_container_width=True):
        with st.spinner("စာသားရလဒ်များကို စက္ကန့်ပိုင်းအတွင်း တွက်ချက်နေပါသည်..."):
            super_groups, head_cols, mid_cols, tail_cols = build_super_groups_fast(df)
            results = evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_row)
            
            st.session_state.results = results
            st.session_state.h_cols = head_cols
            st.session_state.m_cols = mid_cols
            st.session_state.t_cols = tail_cols
            st.success("✅ တွက်ချက်မှု ပြီးမြောက်ပါပြီ။")

    if st.session_state.results is not None:
        results = st.session_state.results
        h_cols, m_cols, t_cols = st.session_state.h_cols, st.session_state.m_cols, st.session_state.t_cols
        
        st.markdown("---")
        st.header("🏆 Master Filter Analysis Results")
        
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
                                st.markdown(f"### 📦 အုပ်စု {idx+1}")
                                for sub_idx, match in enumerate(grp):
                                    st.markdown(f"**လမ်းကြောင်း {sub_idx+1}:** `{match['target_path']}`")
                                
                                current_cols = h_cols if key=="Head" else (m_cols if key=="Mid" else t_cols)
                                render_group_image_ui(df, target_row, current_cols, key, item['digit'], idx, grp)
                                st.markdown("---")
