import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data Loading ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 2. High-Performance Target-Driven Logic Engine ---
def analyze_fast_mode(df, target_excel_row):
    target_r = target_excel_row - 2
    max_rows = len(df)
    
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    target_y = len(head_cols) - 1 # 2026 Column
    
    results = {}
    
    for pos_name, cols in positions:
        # အဆင့် (၁) - Target နေရာမှ နောက်ပြန်ဖြန့်ထွက်သော လမ်းကြောင်း (Prefixes) ၄၄ ကြောင်းကို အရင်ရှာခြင်း
        valid_prefixes = []
        for y_step in range(5):
            for r_step in range(-4, 5):
                if y_step == 0 and r_step == 0: continue
                
                start_r = target_r - 3 * r_step
                start_y = target_y - 3 * y_step
                
                if start_r < 0 or start_r >= max_rows or start_y < 0: continue
                
                valid = True
                digits = []
                path_str = []
                for i in range(3):
                    curr_r = start_r + i * r_step
                    curr_y = start_y + i * y_step
                    if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= len(cols):
                        valid = False; break
                    val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                    if val.lower() in ['x', 'nan', '']:
                        valid = False; break
                    if val.endswith('.0'): val = val[:-2]
                    digits.append(val)
                    path_str.append(f"R{curr_r+2}_Y{curr_y}")
                    
                if valid:
                    valid_prefixes.append({
                        "prefix_tup": tuple(digits),
                        "target_path_str": f"{' -> '.join(path_str)} -> [TARGET]"
                    })
                    
        # အဆင့် (၂) - ပစ်မှတ်ရှိသော ဂဏန်းတွဲ ၄၄၀ ခုကိုသာ History ထဲတွင် အမြန်ကွက်စစ်ခြင်း
        pos_results = []
        for guess in range(10):
            guess_str = str(guess)
            evidence_matches = []
            
            for p_info in valid_prefixes:
                test_group = p_info["prefix_tup"] + (guess_str,)
                
                # အဆိုပါ test_group သည် History (97-25) ထဲတွင် ဘယ်နေရာတွေမှာ ရှိခဲ့လဲ ကွက်ရှာခြင်း
                history_found_paths = []
                for h_y in range(target_y): # 2026 မပါ
                    for h_r in range(max_rows):
                        for h_ystep in range(5):
                            for h_rstep in range(-4, 5):
                                if h_ystep == 0 and h_rstep == 0: continue
                                
                                h_valid = True
                                h_digits = []
                                h_path_str = []
                                for i in range(4):
                                    curr_hr = h_r + i * h_rstep
                                    curr_hy = h_y + i * h_ystep
                                    if curr_hr < 0 or curr_hr >= max_rows or curr_hy < 0 or curr_hy >= target_y:
                                        h_valid = False; break
                                    val = str(df.iloc[curr_hr, cols[curr_hy]]).strip()
                                    if val.lower() in ['x', 'nan', '']:
                                        h_valid = False; break
                                    if val.endswith('.0'): val = val[:-2]
                                    h_digits.append(val)
                                    h_path_str.append(f"R{curr_hr+2}_Y{curr_hy}")
                                    
                                if h_valid and tuple(h_digits) == test_group:
                                    history_found_paths.append("->".join(h_path_str))
                                    
                # လမ်းကြောင်းမတူဘဲ အနည်းဆုံး ၃ ကြိမ် ရှိမရှိ စစ်ဆေးခြင်း
                if len(history_found_paths) >= 3:
                    evidence_matches.append({
                        "group_digits": test_group,
                        "target_path": p_info["target_path_str"],
                        "history_paths": list(set(history_found_paths))[:3]
                    })
                    
            if len(evidence_matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(evidence_matches), "evidence": evidence_matches})
                
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
        
    return results, head_cols, mid_cols, tail_cols

# --- 3. Optimized Image Engine (လွတ်နေသောနှစ်များ ဖြုတ်သည့်စနစ်) ---
def draw_matrix_path_clean(df, target_excel_row, pos_cols, target_path, hist_paths):
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
    
    target_r = target_excel_row - 2
    target_y = len(pos_cols) - 1
    cell_map[(target_r, target_y)] = colors[0]
    all_r.append(target_r); all_y.append(target_y)

    # လမ်းကြောင်းရှိသော သီးသန့်နှစ် (Years) မန်ဘာများကိုသာ ယူမည်
    active_years = sorted(list(set(all_y)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    
    plot_rows = max_r - min_r
    plot_cols = len(active_years)

    # စာလုံးမကျပ်စေရန် အရွယ်အစားကို ကျစ်ကျစ်လျစ်လျစ် ညှိခြင်း
    fig, ax = plt.subplots(figsize=(plot_cols * 0.7, plot_rows * 0.45))
    ax.axis('off')
    
    table_data = []
    table_colors = []
    
    for r in range(min_r, max_r):
        row_text = []
        row_colors = []
        for y_idx in active_years:
            val = str(df.iloc[r, pos_cols[y_idx]]).strip().replace('.0','')
            if val.lower() in ['nan', 'x']: val = ''
            row_text.append(val)
            row_colors.append(cell_map.get((r, y_idx), "#f0f0f0"))
        table_data.append(row_text)
        table_colors.append(row_colors)
        
    col_labels = [f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in active_years]
    row_labels = [f"R-{r+2}" for r in range(min_r, max_r)]
    
    table = ax.table(cellText=table_data, cellColours=table_colors, 
                     rowLabels=row_labels, colLabels=col_labels, 
                     loc='center', cellLoc='center')
    
    table.scale(1, 1.5)
    table.set_fontsize(10)
    
    # Column အကျယ်ကို ဂဏန်း နှစ်လုံးစာ ကွက်တိဖြစ်အောင် ထိန်းညှိခြင်း
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(0.08) # Column width ပြတ်သားအောင် သတ်မှတ်ခြင်း
            
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 4. Streamlit UI Build ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D")
st.title("🎯 Golden Cross 3D - High Speed Master Filter")

file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if file:
    df = load_data(file)
    target_row = st.number_input("Excel Row Number", value=25, min_value=2)
    
    if "fast_results" not in st.session_state:
        st.session_state.fast_results = None
        st.session_state.h_cols = None
        st.session_state.m_cols = None
        st.session_state.t_cols = None

    if st.button("🚀 Master Filter ဖြင့် စက္ကန့်ပိုင်းအတွင်း တိုက်စစ်မည်", use_container_width=True):
        with st.spinner("Target-Driven Algorithm ဖြင့် အမြန်နှုန်းမြှင့် တွက်ချက်နေပါသည်..."):
            # ပြင်ဆင်ချက်: evaluate_target အစား အသစ်ပြောင်းထားသော analyze_fast_mode ကို အမှန်အတိုင်း ခေါ်ယူလိုက်ပါပြီ
            results, h_cols, m_cols, t_cols = analyze_fast_mode(df, target_row)
            st.session_state.fast_results = results
            st.session_state.h_cols = h_cols
            st.session_state.m_cols = m_cols
            st.session_state.t_cols = t_cols
            st.success("✅ တွက်ချက်မှု ပြီးမြောက်ပါပြီ။")

    if st.session_state.fast_results is not None:
        results = st.session_state.fast_results
        h_cols = st.session_state.h_cols
        m_cols = st.session_state.m_cols
        t_cols = st.session_state.t_cols
        
        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns(3)
        positions_ui = [("Head (ထိပ်)", "Head", res_col1), ("Mid (အလယ်)", "Mid", res_col2), ("Tail (ပိတ်)", "Tail", res_col3)]
        
        for title, key, col in positions_ui:
            with col:
                st.subheader(title)
                if not results[key]:
                    st.info("ထောက်ခံမှု မတွေ့ပါ။")
                else:
                    for item in results[key]:
                        with st.expander(f"ဂဏန်း [ {item['digit']} ] - လမ်းကြောင်း {item['score']} ခု"):
                            groups = [item["evidence"][i:i+3] for i in range(0, len(item["evidence"]), 3)]
                            for idx, grp in enumerate(groups):
                                st.markdown(f"### 📦 အုပ်စု {idx+1}")
                                for sub_idx, match in enumerate(grp):
                                    st.markdown(f"**လမ်းကြောင်း {sub_idx+1}:** `{match['target_path']}`")
                                
                                current_cols = h_cols if key=="Head" else (m_cols if key=="Mid" else t_cols)
                                
                                st.download_button(
                                    label=f"📸 အုပ်စု {idx+1} ပုံထုတ်မည်",
                                    data=draw_matrix_path_clean(df, target_row, current_cols, grp[0]['target_path'], grp[0]['history_paths']),
                                    file_name=f"GC_3D_{key}_Digit_{item['digit']}_Group_{idx+1}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_{key}_{item['digit']}_grp_{idx}",
                                    use_container_width=True
                                )
                                st.markdown("---")
