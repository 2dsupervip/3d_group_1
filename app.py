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
                        if y_step == 0 and r_step == 0: continue
                        
                        digits, path_str, valid = [], [], True
                        for i in range(4):
                            curr_r, curr_y = r + i * r_step, y_idx + i * y_step
                            if curr_r < 0 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y:
                                valid = False; break
                            val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                            if val.lower() in ['x', 'nan', '']: valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            digits.append(val); path_str.append(f"R{curr_r+2}_Y{curr_y}")
                            
                        if valid:
                            dtup = tuple(digits)
                            if dtup not in history_counts[pos_name]: history_counts[pos_name][dtup] = set()
                            history_counts[pos_name][dtup].add("->".join(path_str))
                            
        for dtup, paths in history_counts[pos_name].items():
            if len(paths) >= 3: super_groups[pos_name][dtup] = list(paths)
    return super_groups, head_cols, mid_cols, tail_cols

# --- 2. On-Demand Image Engine ---
def draw_matrix_path(df, target_excel_row, pos_cols, target_path, hist_paths):
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
    cell_map[(target_r, len(pos_cols)-1)] = colors[0]
    all_r.append(target_r); all_y.append(len(pos_cols)-1)

    min_r, max_r = max(0, min(all_r)-2), min(len(df), max(all_r)+3)
    min_y, max_y = max(0, min(all_y)-1), min(len(pos_cols), max(all_y)+2)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis('off')
    
    table_data = [[str(df.iloc[r, pos_cols[y]]).strip().replace('.0','') for y in range(min_y, max_y)] for r in range(min_r, max_r)]
    table_colors = [[cell_map.get((r, y), "#f0f0f0") for y in range(min_y, max_y)] for r in range(min_r, max_r)]
    
    table = ax.table(cellText=table_data, cellColours=table_colors, loc='center', cellLoc='center')
    table.scale(1, 1.8)
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 3. UI ---
st.set_page_config(layout="wide")
st.title("🎯 Golden Cross 3D - Master Filter")
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = load_data(file)
    target_row = st.number_input("Target Row", value=25)
    if st.button("🚀 တိုက်စစ်မည်"):
        super_groups, h, m, t = build_super_groups(df)
        results = evaluate_target(df, super_groups, h, m, t, target_row)
        
        for title, key in [("Head", "Head"), ("Mid", "Mid"), ("Tail", "Tail")]:
            with st.expander(f"{title} Analysis"):
                for item in results[key]:
                    st.write(f"### ဂဏန်း: {item['digit']}")
                    # အုပ်စု ၃ ခု ခွဲပြခြင်း
                    groups = [item["evidence"][i:i+3] for i in range(0, len(item["evidence"]), 3)]
                    for idx, grp in enumerate(groups):
                        st.write(f"#### အုပ်စု {idx+1}")
                        for match in grp:
                            if st.button(f"🎨 ပုံဆွဲရန်: {match['target_path'][-15:]}", key=f"{key}_{item['digit']}_{match['target_path']}"):
                                img = draw_matrix_path(df, target_row, (h if key=="Head" else m if key=="Mid" else t), match['target_path'], match['history_paths'])
                                st.download_button("📥 Download", img, file_name="result.jpg")
