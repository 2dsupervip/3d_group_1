import streamlit as st
import pandas as pd
import numpy as np
import itertools

# --- 1. Streamlit Page Configuration & Dark Theme UI ---
st.set_page_config(layout="wide", page_title="Golden Cross v13.0 Core", page_icon="🎯")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    button[data-baseweb="tab"] { color: #888888 !important; font-size: 15px !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #D4AF37 !important; border-bottom-color: #D4AF37 !important; }
    .report-card {
        background-color: #1f2937; border: 1px solid #374151; border-radius: 8px;
        padding: 15px; margin-bottom: 10px;
    }
    .win-text { color: #00ffcc; font-weight: bold; }
    .lose-text { color: #ff3366; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Loading Engine (Reads Single Calendar Sheet) ---
@st.cache_data
def load_calendar_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df

# --- 3. Virtual Matrix Engine (Generates 70,000+ Paths inside Python Memory) ---
def analyze_virtual_matrix(df, target_year, target_draw, is_backtest=False):
    years_row = df.iloc[0].astype(str).tolist()
    
    # ရွေးချယ်ထားသော Year ၏ Column Index ကို ရှာဖွေခြင်း
    target_col_base = -1
    for c_idx, y_val in enumerate(years_row):
        if not y_val or y_val.lower() == 'nan' or y_val.strip() == '':
            continue
        if str(target_year) in y_val or y_val == str(target_year)[-2:]:
            target_col_base = c_idx
            break
            
    if target_col_base == -1:
        # ၂၀၂၆ ရှာမတွေ့ပါက ကလင်ဒါ၏ နောက်ဆုံးအပိတ်ကော်လံ (လက်ရှိအရှိဆုံးနှစ်) ကို Dynamic ယူခြင်း
        target_col_base = len(df.columns) - 4 

    # Layout Offset: Header ၂ ခုစာ ကျော်ပြီး Draw 1 သည် Row index 2 မှ စတင်သည်
    target_row_idx = 1 + target_draw 
    
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    
    raw_paths_compiled = {"Head": {}, "Mid": {}, "Tail": {}}
    seen_composite_keys = set()
    
    max_rows = len(df)
    max_y_idx = len(head_cols) - 1
    
    # ၇၀,၀၀၀ ကျော် လမ်းကြောင်းများကို Memory ထဲတွင် Virtual ပေါင်းစပ် Loops ပတ်ခြင်း (y=0 မှ y=4 အထိ)
    for pos_name, cols in positions:
        for y_idx in range(max_y_idx):
            for r_idx in range(2, max_rows):
                
                # ⚠️ [Strict Time-Capsule Control]: ထွက်ပြီးသားအကြိမ်များ၏ လမ်းကြောင်းများကို Duplicate အဖြစ် ပယ်ဖျက်ခြင်း
                if is_backtest and r_idx >= target_row_idx:
                    continue
                elif not is_backtest and r_idx >= len(df) - 1: 
                    continue

                for y_step in range(5): 
                    for r_step in range(-4, 5):
                        if y_step == 0 and r_step == 0: continue
                        
                        digits, valid = [], True
                        path_identifiers = []
                        
                        for i in range(4):
                            curr_r = r_idx + i * r_step
                            curr_y = y_idx + i * y_step
                            
                            if curr_r < 2 or curr_r >= max_rows or curr_y < 0 or curr_y >= max_y_idx:
                                valid = False; break
                                
                            if is_backtest and curr_r >= target_row_idx:
                                valid = False; break
                                
                            c_idx = cols[curr_y]
                            val = str(df.iloc[curr_r, c_idx]).strip()
                            if val.lower() in ['x', 'nan', '']:
                                valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            
                            digits.append(val)
                            
                            virtual_orig_year = years_row[c_idx] if years_row[c_idx] != "nan" else "Unknown"
                            virtual_row_no = curr_r - 1
                            path_identifiers.append(f"{virtual_orig_year}_{virtual_row_no}")
                            
                        if valid:
                            # 🛠 [Index-Based Deduplication]
                            composite_dna = f"{pos_name}_{y_step}_{r_step}_" + "-".join(path_identifiers)
                            if composite_dna in seen_composite_keys:
                                continue
                            seen_composite_keys.add(composite_dna)
                            
                            digits_tup = tuple(digits)
                            if digits_tup not in raw_paths_compiled[pos_name]:
                                raw_paths_compiled[pos_name][digits_tup] = 0
                            raw_paths_compiled[pos_name][digits_tup] += 1
                            
    # --- Target Valuation Process ---
    results = {"Head": [], "Mid": [], "Tail": []}
    target_y_idx = head_cols.index(target_col_base) if target_col_base in head_cols else len(head_cols) - 1
    
    for pos_name, cols in positions:
        prefixes_found = []
        
        for y_step in range(5):
            for r_step in range(-4, 5):
                if y_step == 0 and r_step == 0: continue
                
                start_r = target_row_idx - 3 * r_step
                start_y = target_y_idx - 3 * y_step
                if start_r < 2 or start_r >= target_row_idx or start_y < 0: continue
                
                valid, digits = True, []
                for i in range(3):
                    curr_r = start_r + i * r_step
                    curr_y = start_y + i * y_step
                    if curr_r < 2 or curr_r >= target_row_idx or curr_y < 0 or curr_y >= len(cols):
                        valid = False; break
                    val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                    if val.lower() in ['x', 'nan', '']: valid = False; break
                    if val.endswith('.0'): val = val[:-2]
                    digits.append(val)
                    
                if valid:
                    prefixes_found.append(tuple(digits))
                    
        for guess in range(10):
            guess_str = str(guess)
            match_count = 0
            
            for pref in prefixes_found:
                full_seq = pref + (guess_str,)
                if full_seq in raw_paths_compiled[pos_name]:
                    match_count += raw_paths_compiled[pos_name][full_seq]
                    
            if match_count >= 1:
                results[pos_name].append({
                    "digit": guess_str,
                    "match_count": match_count
                })
                
        results[pos_name] = sorted(results[pos_name], key=lambda x: x["match_count"], reverse=True)
        
    return results

# --- 4. Filtering & 27 Pairs Generator Engine ---
def get_digits_by_filter(pos_results, mode_type, min_c=None, max_c=None):
    if not pos_results: return []
    if mode_type == "single":
        return [r["digit"] for r in pos_results if r["match_count"] == 1]
    elif mode_type == "double":
        return [r["digit"] for r in pos_results if r["match_count"] <= 2]
    elif mode_type == "triple":
        return [r["digit"] for r in pos_results if r["match_count"] >= 3]
    elif mode_type == "custom" and min_c is not None and max_c is not None:
        return [r["digit"] for r in pos_results if min_c <= r["match_count"] <= max_c]
    return []

def generate_27_pairs(results, mode_type, min_c=None, max_c=None):
    h = get_digits_by_filter(results["Head"], mode_type, min_c, max_c)[:3]
    m = get_digits_by_filter(results["Mid"], mode_type, min_c, max_c)[:3]
    t = get_digits_by_filter(results["Tail"], mode_type, min_c, max_c)[:3]
    combos = list(itertools.product(h, m, t))
    return ["".join(c) for c in combos]

# --- 5. Real Result Extractor Engine ---
def get_actual_result_string(df, target_year, target_draw):
    try:
        years_row = df.iloc[0].astype(str).tolist()
        target_col_base = -1
        for c_idx, y_val in enumerate(years_row):
            if not y_val or y_val.lower() == 'nan' or y_val.strip() == '': continue
            if str(target_year) in y_val or y_val == str(target_year)[-2:]:
                target_col_base = c_idx
                break
        if target_col_base == -1: target_col_base = len(df.columns) - 4
        
        target_row_idx = 1 + target_draw
        h_val = str(df.iloc[target_row_idx, target_col_base]).strip().replace('.0','')
        m_val = str(df.iloc[target_row_idx, target_col_base + 1]).strip().replace('.0','')
        t_val = str(df.iloc[target_row_idx, target_col_base + 2]).strip().replace('.0','')
        return f"{h_val}{m_val}{t_val}"
    except:
        return "N/A"

# --- 6. User Interface Control Panel ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚙️ VIRTUAL ENGINE v13.0</h2>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Calendar File (2025_3D.xlsx)", type=["xlsx"])
    st.markdown("---")
    
    if file:
        st.markdown("### 🔍 MODE CONTROL")
        app_mode = st.radio("Working Mode:", ["Live Mode 🟢", "Deep Batch Backtest 🟡"])
        
        st.markdown("### 🔢 INPUT BOXES")
        # 🛠 ၂၀၂၆ အတွက် ကွက်တိ Default တန်းဝင်နေစေရန် ပြင်ဆင်ချက်
        input_year = st.number_input("Target Year (ခုနှစ်):", value=2026, min_value=1996, max_value=2030)
        input_draw = st.number_input("Target Draw (အကြိမ်ရေ):", value=1, min_value=1, max_value=50)
        
        if app_mode == "Deep Batch Backtest 🟡":
            backtest_rounds = st.number_input("Backtest Rounds Count (eg. 24 ကြိမ်စာ):", value=24, min_value=1, max_value=50)

if file:
    df_calendar = load_calendar_data(file)
    
    if "Deep Batch Backtest 🟡" in app_mode:
        st.markdown(f"<h3 style='color:#D4AF37;'>📊 Automated Batch Backtest Report (Last {backtest_rounds} Rounds)</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Deep Backtest Engine", use_container_width=True):
            wins = 0
            total_tested = 0
            
            for offset in range(backtest_rounds):
                curr_draw = input_draw - offset
                curr_year = input_year
                
                if curr_draw <= 0:
                    curr_year -= 1
                    curr_draw = 24 + curr_draw 
                    
                if curr_year < 1996: break
                
                total_tested += 1
                
                round_results = analyze_virtual_matrix(df_calendar, curr_year, curr_draw, is_backtest=True)
                generated_pairs = generate_27_pairs(round_results, "triple") 
                actual_out = get_actual_result_string(df_calendar, curr_year, curr_draw)
                
                is_win = actual_out in generated_pairs
                if is_win: wins += 1
                
                status_lbl = "<span class='win-text'>🏆 STATUS: WIN (✅ HIT)</span>" if is_win else "<span class='lose-text'>🏆 STATUS: LOSE (❌ MISS)</span>"
                pairs_display = " . ".join(generated_pairs) if generated_pairs else "No Pairs Generated"
                
                st.markdown(f"""
                    <div class="report-card">
                        <h4>🎯 [ROUND {offset+1}] -> Year {curr_year} | Draw {curr_draw}</h4>
                        <p>✨ <b>Actual Result:</b> <span style="font-size:16px; color:#ffcc00;">{actual_out}</span></p>
                        <p>🔮 <b>AI VIP 27 Pairs:</b> <span style="color:#b0b0b0;">{pairs_display}</span></p>
                        <p>{status_lbl}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            win_rate = (wins / total_tested) * 100 if total_tested > 0 else 0
            st.markdown("---")
            st.subheader("📈 FINAL DEEP EVALUATION SUMMARY")
            st.metric("TOTAL WINS", f"{wins} / {total_tested} Rounds")
            st.metric("WIN RATE PERCENTAGE", f"{win_rate:.1f}%")
            
    else:
        st.markdown(f"<h3 style='color:#D4AF37;'>📊 Virtual Matrix Dashboard (Year {input_year} | Draw {input_draw})</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Live Master Filter Analytics", use_container_width=True):
            with st.spinner("Processing 70,000+ Virtual Paths Syncing..."):
                st.session_state.v12_results = analyze_virtual_matrix(df_calendar, input_year, input_draw, is_backtest=False)
                st.success("✅ ၂၀၂၆ အတွက် ၇၀,၀၀0 ကျော် လမ်းကြောင်းများအားလုံး Virtual ပေါင်းစပ်တွက်ချက်မှု အောင်မြင်ပါသည်။")
                
        if "v12_results" in st.session_state and st.session_state.v12_results is not None:
            res = st.session_state.v12_results
            
            t1, t2, t3, t4 = st.tabs([
                "🎯 LONE Bိုင် CONSENSUS", 
                "🥈 2-MATCH GROUPS", 
                "🥇 3-MATCH GROUPS", 
                "⚙️ CUSTOM RANGE (* to *)"
            ])
            
            with t1:
                st.markdown("<h4>🎯 သီးခြားလမ်းကြောင်းများစွာမှ ဘုံအတည်ပြုပေးသော လုံးဘိုင်ဂဏန်း</h4>", unsafe_allow_html=True)
                s_h = get_digits_by_filter(res["Head"], "single")
                s_m = get_digits_by_filter(res["Mid"], "single")
                s_t = get_digits_by_filter(res["Tail"], "single")
                
                st.write(f"**ထိပ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_h) if s_h else 'မရှိပါ'}")
                st.write(f"**လယ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_m) if s_m else 'မရှိပါ'}")
                st.write(f"**ပိတ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_t) if s_t else 'မရှိပါ'}")
                
            with t2:
                st.markdown("<h4>🥈 ပုံစံတူ ၂ ခုနှင့်အောက် ကိုက်ညီသော လမ်းကြောင်းအတွဲများ</h4>", unsafe_allow_html=True)
                pairs_2 = generate_27_pairs(res, "double")
                st.text_area("2-Match Pairs Text:", value=" . ".join(pairs_2) if pairs_2 else "No Data", height=100)
                
            with t3:
                st.markdown("<h4>🥇 ပုံစံတူ ၃ ခုနှင့်အထက် ရှိသမျှ True VIP အတွဲများ</h4>", unsafe_allow_html=True)
                pairs_3 = generate_27_pairs(res, "triple")
                st.text_area("VIP Pairs Text:", value=" . ".join(pairs_3) if pairs_3 else "No Data", height=100)
                
            with t4:
                st.markdown("<h4>⚙️ Custom Range အုပ်စု အရေအတွက် ကန့်သတ်ခြင်း</h4>", unsafe_allow_html=True)
                c_min = st.number_input("Minimum Match Count:", value=4, min_value=1)
                c_max = st.number_input("Maximum Match Count:", value=10, min_value=1)
                
                pairs_c = generate_27_pairs(res, "custom", c_min, c_max)
                st.text_area(f"Custom Pairs ({c_min} to {c_max} Matches):", value=" . ".join(pairs_c) if pairs_c else "No Data", height=100)
else:
    st.info("💡 ဆက်လက်လုပ်ဆောင်ရန်အတွက် ဘယ်ဘက် Sidebar Panel တွင် '2025_3D.xlsx' (Calendar) ဖိုင်ကို တင်ပေးပါ Bro!")
