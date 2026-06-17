import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data Loading ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 2. High-Speed Indexing Core Engine ---
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
                            curr_r, curr_y = r + i * r_step, y_idx + i * y_step
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
            if len(paths) >= 3: super_groups[pos_name][dtup] = list(paths)
                
    return super_groups, head_cols, mid_cols, tail_cols

# --- 3. Target Alignment Evaluator (တိုင်မင် အတိအကျကိုက်သော လမ်းကြောင်းများသာ စစ်ထုတ်ခြင်း) ---
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
                    curr_r, curr_y = start_r + i * r_step, start_y + i * y_step
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
                    # တိုင်မင် (Step Alignment) တိုက်စစ်ခြင်း - လမ်းကြောင်း ၄ ခုစလုံး တူညီသော ခြေလှမ်းရှိရမည်
                    filtered_hist = []
                    for hp in super_groups[pos_name][test_group]:
                        p_parts = hp.split("->")
                        if len(p_parts) >= 2:
                            r1, y1 = int(p_parts[0].split("_Y")[0][1:])-2, int(p_parts[0].split("_Y")[1])
                            r2, y2 = int(p_parts[1].split("_Y")[0][1:])-2, int(p_parts[1].split("_Y")[1])
                            if (r2 - r1 == pref["r_step"]) and (y2 - y1 == pref["y_step"]):
                                filtered_hist.append(hp)
                    
                    if len(filtered_hist) >= 3 or (len(filtered_hist) > 0 and len(matches) >= 2):
                        hist_to_use = filtered_hist if len(filtered_hist) >= 3 else super_groups[pos_name][test_group]
                        matches.append({
                            "group_digits": test_group,
                            "target_path": pref["path"],
                            "history_paths": hist_to_use[:3]
                        })
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
    return results

# --- 4. Premium Image Engine (Watermark + Bold Font + Auto-Fill + Margins) ---
def draw_matrix_path_clean(df, target_excel_row, pos_cols, target_path, hist_paths, guess_digit):
    plt.clf() 
    colors = ["#99ff99", "#ff99c2", "#99e6ff", "#ffd1b3"] # စိမ်း၊ နီ၊ ပြာ၊ လိမ္မော်
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
    cell_map[(target_r, target_y)] = colors[0] # ယခုအကြိမ်ကို အစိမ်းရောင်အသေခြယ်မည်
    all_r.append(target_r); all_y.append(target_y)

    active_years = sorted(list(set(all_y)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    plot_rows, plot_cols = max_r - min_r, len(active_years)

    # ပတ်လည် Margin ချန်ရန်အတွက် ရုပ်ထွက်ပြင်ဆင်ခြင်း
    fig, ax = plt.subplots(figsize=(max(plot_cols * 0.8, 5), max(plot_rows * 0.5, 4)))
    fig.subplots_adjust(left=0.3, right=0.7, top=0.7, bottom=0.3) # 0.3 Margin ဘေးပတ်လည်ချန်ခြင်း
    ax.axis('off')
    
    # 🔒 ANTI-THEFT WATERMARK စနစ် (စာသားနောက်ခံကို ၄၅ ဒီဂရီစောင်း၍ ထည့်ခြင်း)
    fig.text(0.5, 0.5, 'GOLDEN CROSS 3D', fontsize=35, color='gray',
             ha='center', va='center', alpha=0.12, rotation=45, zorder=0)
    
    # 🌟 PREMIUM DYNAMIC TITLE (အကြိမ်ရေ အလိုအလျောက်တွက်ချက်ခြင်း)
    draw_number = target_excel_row - 13
    ax.set_title(f"🌟 THE GOLDEN CROSS 3D ({draw_number}/2026)", fontsize=14, pad=20, weight='bold', color='#1a1a1a')

    table_data, table_colors = [], []
    for r in range(min_r, max_r):
        row_text, row_colors = [], []
        for y_idx in active_years:
            if r == target_r and y_idx == target_y:
                # 🎯 ယခုလက်ရှိအကြိမ် Green Color မှာ ဂဏန်းကို အလိုအလျောက် တစ်ခါတည်း ဖြည့်ပေးခြင်း
                val = str(guess_digit)
            else:
                val = str(df.iloc[r, pos_cols[y_idx]]).strip().replace('.0','')
                if val.lower() in ['nan', 'x']: val = ''
            row_text.append(val)
            row_colors.append(cell_map.get((r, y_idx), "#ffffff")) # မူရင်းဆဲလ်များကို အဖြူရောင်ပြောင်းလဲ၍ အရောင်လွတ်များ ရှင်းထုတ်ခြင်း
        table_data.append(row_text); table_colors.append(row_colors)
        
    table = ax.table(cellText=table_data, cellColours=table_colors, 
                     rowLabels=[f"R-{r+2}" for r in range(min_r, max_r)], 
                     colLabels=[f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in active_years], 
                     loc='center', cellLoc='center')
    table.scale(1, 1.6)
    table.set_fontsize(10)
    
    # 🔥 FONT SIZE ကြီးခြင်းနှင့် Column အကျယ်ကို ဂဏန်း နှစ်လုံးစာ ကျဉ်းခြင်း စနစ်
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(0.07) # Column အကျယ်ကို ကျစ်ကျစ်လျစ်လျစ် ညှိခြင်း
        # လမ်းကြောင်းရှိသော အရောင်ပါသည့် ဆဲလ်ကွက်များကို စစ်ထုတ်ပြီး စာလုံးအထူနှင့် Font ကြီးပေးခြင်း
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
    if st.button(f"📸 အုပ်စု {idx+1} ပုံထုတ်မည်", key=f"btn_{key}_{item_digit}_grp_{idx}", use_container_width=True):
        with st.spinner("Watermark နှင့် Title များကို သေသေချာချာ ရေးဆွဲနေပါသည်..."):
            img_buf = draw_matrix_path_clean(df, target_row, current_cols, grp[0]['target_path'], grp[0]['history_paths'], item_digit)
            st.image(img_buf, caption=f"THE GOLDEN CROSS 3D - {key} Digit {item_digit}")
            st.download_button(
                label="📥 မူပိုင်ခွင့်ပါဝင်သော ပုံကို ဖုန်းထဲသို့ သိမ်းဆည်းရန် နှိပ်ပါ",
                data=img_buf,
                file_name=f"GC_3D_{key}_Digit_{item_digit}_Group_{idx+1}.jpg",
                mime="image/jpeg",
                key=f"dl_confirm_{key}_{item_digit}_grp_{idx}",
                use_container_width=True
            )

# --- 6. Streamlit Main UI ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D")
st.title("🎯 Golden Cross 3D - Premium Copy-Protection Engine v4.0")

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
                                
                                # Fragment UI သို့ ဒေတာပို့လွှတ်ခြင်း
                                render_group_image_ui(df, target_row, current_cols, key, item['digit'], idx, grp)
                                st.markdown("---")
