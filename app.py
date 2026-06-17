import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. Data & Logic Engine ---
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
                        
                        digits, path_str, valid = [], [], True
                        for i in range(4):
                            curr_r, curr_y = r + i * r_step, y_idx + i * y_step
                            if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y:
                                valid = False
                                break
                            val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                            if val.lower() in ['x', 'nan', '']: 
                                valid = False
                                break
                            if val.endswith('.0'): 
                                val = val[:-2]
                            digits.append(val)
                            path_str.append(f"R{curr_r+2}_Y{curr_y}")
                            
                        if valid:
                            dtup = tuple(digits)
                            if dtup not in history_counts[pos_name]: 
                                history_counts[pos_name][dtup] = set()
                            history_counts[pos_name][dtup].add("->".join(path_str))
                            
        for dtup, paths in history_counts[pos_name].items():
            if len(paths) >= 3: 
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
                    if val.lower() in ['x', 'nan', '']: 
                        valid = False
                        break
                    if val.endswith('.0'): 
                        val = val[:-2]
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
                    hist_paths = super_groups[pos_name][test_group]
                    matches.append({
                        "group_digits": test_group,
                        "target_path": pref["path"],
                        "history_paths": hist_paths[:3] 
                    })
                    
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
        
    return results

# --- 2. On-Demand Image Engine ---
def draw_matrix_path(df, target_excel_row, pos_cols, target_path, hist_paths):
    colors = ["#99ff99", "#ff99c2", "#99e6ff", "#ffd1b3"]
    cell_map, all_r, all_y = {}, [], []
    
    def add_to_map(path, col_idx):
        for p in path.split("->"):
            p = p.strip().replace("[TARGET]", "").strip("-").strip()
            if p.startswith("R") and "_Y" in p:
                r, y = int(p.split("_Y")[0][1:]) - 2, int(p.split("_Y")[1])
                if (r, y) not in cell_map: 
                    cell_map[(r, y)] = colors[col_idx]
                all_r.append(r)
                all_y.append(y)

    add_to_map(target_path, 0)
    for i, hp in enumerate(hist_paths): 
        add_to_map(hp, (i % 3) + 1)
    
    target_r = target_excel_row - 2
    cell_map[(target_r, len(pos_cols)-1)] = colors[0]
    all_r.append(target_r)
    all_y.append(len(pos_cols)-1)

    min_r, max_r = max(0, min(all_r)-2), min(len(df), max(all_r)+3)
    min_y, max_y = max(0, min(all_y)-1), min(len(pos_cols), max(all_y)+2)

    plot_rows = max_r - min_r
    plot_cols = max_y - min_y

    fig, ax = plt.subplots(figsize=(plot_cols * 1.2, plot_rows * 0.6))
    ax.axis('off')
    
    table_data = [[str(df.iloc[r, pos_cols[y]]).strip().replace('.0','') for y in range(min_y, max_y)] for r in range(min_r, max_r)]
    table_colors = [[cell_map.get((r, y), "#f0f0f0") for y in range(min_y, max_y)] for r in range(min_r, max_r)]
    
    col_labels = [f"{97 + y}" if (97 + y) < 100 else f"{y - 3:02d}" for y in range(min_y, max_y)]
    row_labels = [f"R-{r+2}" for r in range(min_r, max_r)]
    
    table = ax.table(cellText=table_data, cellColours=table_colors, 
                     rowLabels=row_labels, colLabels=col_labels, 
                     loc='center', cellLoc='center')
    table.scale(1, 1.8)
    table.set_fontsize(12)
    
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 3. Streamlit UI Build ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D")
st.title("🎯 Golden Cross 3D - Master Filter Engine")

file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if file:
    df = load_data(file)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("ယခုအကြိမ် နေရာ (Target)")
        target_row = st.number_input("Excel Row Number (ဥပမာ ၁၂ ကြိမ်မြောက်အတွက် 25)", value=25, min_value=2)
        
    # Session State သုံး၍ Button နှိပ်ပါက Data ပျောက်မသွားအောင် ထိန်းထားခြင်း
    if "calculated_results" not in st.session_state:
        st.session_state.calculated_results = None
        st.session_state.super_g = None
        st.session_state.h_cols = None
        st.session_state.m_cols = None
        st.session_state.t_cols = None

    if st.button("🚀 Master Filter ဖြင့် တိုက်စစ်မည်", use_container_width=True):
        with st.spinner("Data များကို တွက်ချက်နေပါသည်..."):
            super_groups, head_cols, mid_cols, tail_cols = build_super_groups(df)
            results = evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_row)
            
            st.session_state.calculated_results = results
            st.session_state.super_g = super_groups
            st.session_state.h_cols = head_cols
            st.session_state.m_cols = mid_cols
            st.session_state.t_cols = tail_cols

    if st.session_state.calculated_results is not None:
        results = st.session_state.calculated_results
        h_cols = st.session_state.h_cols
        m_cols = st.session_state.m_cols
        t_cols = st.session_state.t_cols
        
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
                            groups = [item["evidence"][i:i+3] for i in range(0, len(item["evidence"]), 3)]
                            
                            for idx, grp in enumerate(groups):
                                st.markdown(f"### 📦 အုပ်စု {idx+1}")
                                for sub_idx, match in enumerate(grp):
                                    st.markdown(f"**လမ်းကြောင်း {sub_idx+1}:** `{match['target_path']}`")
                                
                                # ဖြေရှင်းချက်: st.download_button ထဲတွင် ပုံဆွဲသည့် function ကို တစ်ခါတည်းထည့်ခြင်းဖြင့် အစပြန်မရောက်တော့ပါ
                                current_cols = h_cols if key=="Head" else (m_cols if key=="Mid" else t_cols)
                                
                                # download နှိပ်မှ နောက်ကွယ်ကနေ runtime ထဲ ပုံဝင်ဆွဲပေးမည် (On-Demand + Safe Mode)
                                st.download_button(
                                    label=f"📸 အုပ်စု {idx+1} ပုံထုတ်မည်",
                                    data=draw_matrix_path(df, target_row, current_cols, grp[0]['target_path'], grp[0]['history_paths']),
                                    file_name=f"GC_3D_{key}_Digit_{item['digit']}_Group_{idx+1}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_{key}_{item['digit']}_grp_{idx}",
                                    use_container_width=True
                                )
                                st.markdown("---")
