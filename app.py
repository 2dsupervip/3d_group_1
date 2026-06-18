import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import json

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
                        "path": f"{' -> '.join(path_str)} -> [TARGET]"
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
                        "history_paths": super_groups[pos_name][test_group][:3]
                    })
            if len(matches) >= 3:
                pos_results.append({"digit": guess_str, "score": len(matches), "evidence": matches})
        results[pos_name] = sorted(pos_results, key=lambda x: x["score"], reverse=True)
    return results

# --- 4. Advanced High-Speed Smart Crop Image Engine (Golden Title Edition) ---
def draw_matrix_path_clean(df, target_excel_row, pos_cols, target_path, hist_paths, guess_digit, position_title):
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
    cell_map[(target_r, target_y)] = colors[0]
    all_r.append(target_r); all_y.append(target_y)

    # 🛠 [လော့ဂျစ်အသစ်] Advanced Smart Crop: အရောင်ရှိသောနှစ်များကိုသာ စစ်ထုတ်ပြီး ကြားကွက်လပ်ကို ညှပ်ထုတ်ခြင်း
    colored_years = sorted(list(set(all_y)))
    active_years = []
    
    # Year 00 မှ Target Year (26) အထိ စစ်ဆေးမည်
    for y in range(len(pos_cols)):
        # ၎င်းနှစ်သည် အရောင်ရှိသောနှစ်ဖြစ်လျှင် သို့မဟုတ် အရောင်ရှိသောနှစ်များနှင့် ဘေးချင်းကပ် ၂ နှစ်အတွင်း Buffer ရှိလျှင် ချန်မည်
        if any(abs(y - cy) <= 2 for cy in colored_years) or y == target_y:
            active_years.append(y)
            
    active_years = sorted(list(set(active_years)))
    min_r, max_r = max(0, min(all_r) - 2), min(len(df), max(all_r) + 3)
    
    plot_rows = max_r - min_r
    plot_cols = len(active_years)

    # 📐 ဇယားဘေးပတ်လည် သုံးဘက်နှင့် ခေါင်းစဉ်အပေါ်ကို .3 Margin ကွက်တိ Layout ချခြင်း
    fig, ax = plt.subplots(figsize=(max(plot_cols * 0.42, 5), max(plot_rows * 0.42, 4)))
    fig.subplots_adjust(left=0.12, right=0.88, top=0.85, bottom=0.15) 
    ax.axis('off')
    
    # 🔒 ELEGANT BACKDROP WATERMARK
    fig.text(0.5, 0.5, 'GOLDEN CROSS 3D  •  PREMIUM BLUEPRINT', fontsize=24, color='#b0b0b0',
             ha='center', va='center', alpha=0.12, rotation=25, zorder=0, fontweight='bold')
    
    # 🌟 FIXED GOLDEN TITLE (ခေါင်းစဉ်ကို ရွှေရောင်ပြောင်းပြီး Year Row နှင့် ကပ်လျက် Pad=10 သို့ လျှော့ချခြင်း)
    draw_number = target_excel_row - 13
    ax.set_title(f"🌟 THE GOLDEN CROSS 3D ({draw_number}/2026) {position_title} Digit {guess_digit}", 
                 fontsize=13, pad=10, weight='bold', color='#D4AF37', ha='center') # #D4AF37 သည် Premium Metallic Gold ဖြစ်သည်

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
    
    # 📐 Column Width ကို အခုထက်ပိုကျဉ်းပြီး စမတ်ကျကျဖြစ်အောင် 0.055 သို့ ညှိခြင်း
    for (row, col), cell in table.get_celld().items():
        if col >= 0: 
            cell.set_width(0.055)
            cell.set_linewidth(0.4)
            cell.set_edgecolor('#e0e0e0') 
        if (row-1, col) in [(r - min_r, active_years.index(y)) for (r, y) in cell_map.keys() if y in active_years]:
            cell.get_text().set_fontsize(11)
            cell.get_text().set_weight('bold')
            
    buf = BytesIO()
    plt.savefig(buf, format="jpeg", dpi=300, bbox_inches='tight')
    plt.close(fig)
    return buf

# --- 6. Streamlit Main Tab-Divided UI ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D Pro")
st.title("🎯 Golden Cross 3D - Ultimate Master Engine v5.0")

# Tab စနစ်ကို အချောသပ်ခွဲထုတ်ခြင်း
tab1, tab2 = st.tabs(["🏆 Tab 1: Fast Text Analysis", "📸 Tab 2: Lightning Blueprint Generator"])

with tab1:
    st.subheader("📊 1. စာသားရလဒ် အမြန်တွက်ချက်ခြင်း အပိုင်း")
    file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"], key="tab1_uploader")
    
    if file:
        df = load_data(file)
        target_row = st.number_input("Excel Row Number", value=25, min_value=2, key="tab1_row")
        
        if st.button("🚀 Master Filter စာသားထုတ်မည်", use_container_width=True):
            with st.spinner("စာသားရလဒ်များကို စက္ကန့်ပိုင်းအတွင်း ဒုံးပျံလို တွက်ချက်နေပါသည်..."):
                super_groups, head_cols, mid_cols, tail_cols = build_super_groups_fast(df)
                results = evaluate_target(df, super_groups, head_cols, mid_cols, tail_cols, target_row)
                
                st.success("✅ တွက်ချက်မှု ပြီးမြောက်ပါပြီ။ အောက်က အုပ်စုကုဒ်ကို ကူးယူပြီး Tab 2 တွင် ပုံထုတ်ပါ။")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                positions_ui = [("Head (ထိပ်)", "Head", res_col1), ("Mid (အလယ်)", "Mid", res_col2), ("Tail (ပိတ်)", "Tail", res_col3)]
                
                for title, key, col in positions_ui:
                    with col:
                        st.markdown(f"### {title}")
                        if not results[key]: st.info("ထောက်ခံမှု မတွေ့ပါ။")
                        else:
                            for item in results[key]:
                                with st.expander(f"ဂဏန်း [ {item['digit']} ] - ลမ်းကြောင်း {item['score']} ခု"):
                                    groups = [item["evidence"][i:i+3] for i in range(0, len(item["evidence"]), 3)]
                                    for idx, grp in enumerate(groups):
                                        st.markdown(f"**📦 အုပ်စု {idx+1} (Copy Button ကို နှိပ်ပါ)**")
                                        
                                        # Tab 2 သို့ ယူသွားရန်အတွက် လမ်းကြောင်းဒေတာကို စနစ်တကျ JSON String ပြောင်းပေးခြင်း
                                        package = {
                                            "target_row": target_row,
                                            "position_title": key,
                                            "guess_digit": item['digit'],
                                            "group_idx": idx + 1,
                                            "target_path": grp[0]['target_path'],
                                            "history_paths": grp[0]['history_paths']
                                        }
                                        package_str = json.dumps(package)
                                        
                                        # Copy Button အဖြစ် သုံးနိုင်ရန် st.code ဖြင့် ထုတ်ပေးခြင်း
                                        st.code(package_str, language="json")
                                        st.markdown("---")

with tab2:
    st.subheader("📸 2. တစ်စက္ကန့်အတွင်း ပုံတိုက်ရိုက်ထုတ်ယူခြင်း အပိုင်း")
    file_t2 = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"], key="tab2_uploader")
    
    if file_t2:
        df_t2 = load_data(file_t2)
        head_cols, mid_cols, tail_cols = build_super_groups_fast(df_t2)[1:]
        
        # Tab 1 မှ ကူးလာသော စာသားကို Paste ချမည့် နေရာ
        paste_input = st.text_area("📋 Tab 1 မှ မိတ္တူကူးလာသော အုပ်စုစာသား (Group Code) ကို ဒီနေရာမှာ Paste ချပါ:", height=120)
        
        if paste_input.strip():
            try:
                pkg = json.loads(paste_input.strip())
                
                # အချက်အလက်များ ပြန်လည်ထုတ်ယူခြင်း
                t_row = pkg["target_row"]
                pos_title = pkg["position_title"]
                g_digit = pkg["guess_digit"]
                g_idx = pkg["group_idx"]
                t_path = pkg["target_path"]
                h_paths = pkg["history_paths"]
                
                current_cols = head_cols if pos_title=="Head" else (mid_cols if pos_title=="Mid" else tail_cols)
                draw_num = t_row - 13
                file_naming = f"{draw_num}-2026_{pos_title}_Digit_{g_digit}_Group_{g_idx}.jpg"
                
                st.info(f"✅ အုပ်စုဖတ်ရှုမှု အောင်မြင်သည်- {pos_title} Digit {g_digit} (အုပ်စု {g_idx})")
                
                # Lightning Direct Download Button
                st.download_button(
                    label=f"📸 {pos_title} Digit {g_digit} (အုပ်စု-{g_idx}) ပုံကို တိုက်ရိုက်ဒေါင်းလုဒ်ဆွဲမည်",
                    data=draw_matrix_path_clean(df_t2, t_row, current_cols, t_path, h_paths, g_digit, pos_title),
                    file_name=file_naming,
                    mime="image/jpeg",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error("❌ စာသားပုံစံ မမှန်ကန်ပါ။ Tab 1 မှ ကုဒ်တစ်ခုလုံးကို ကွက်တိ ကူးယူလာခဲ့ပါ။")
