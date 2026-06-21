import streamlit as st
import pandas as pd
import numpy as np
import itertools

# --- 1. Streamlit Page Configuration & Dark Theme UI ---
st.set_page_config(layout="wide", page_title="Golden Cross v16.0 Core", page_icon="🎯")

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
    .score-box {
        background-color: #111827; border: 1px solid #1f2937;
        padding: 12px; border-radius: 6px; font-family: monospace; font-size: 14px; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Loading Engine (Reads Single Calendar Sheet) ---
@st.cache_data
def load_calendar_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df

# --- 3. Virtual Matrix Engine (Generates 70,000+ Paths inside Python Memory) ---
def analyze_virtual_matrix(df, target_year, target_draw, is_backtest=False):
    raw_years_row = df.iloc[0].tolist()
    
    # 🛠 [Column Match Repair]: '26' သို့မဟုတ် '2026' ကော်လံကို အတိအကျ ဖမ်းယူခြင်း
    target_col_base = -1
    for c_idx, raw_val in enumerate(raw_years_row):
        y_val = str(raw_val).strip()
        if not y_val or y_val.lower() == 'nan' or y_val == '': continue
        short_y = str(target_year)[-2:]
        if y_val == short_y or y_val == str(target_year):
            target_col_base = c_idx
            break
            
    if target_col_base == -1:
        target_col_base = len(df.columns) - 4 

    # 🛠 [Exact Row Offset Repair]: ၂၀၂၆ အကြိမ် ၁ = Row 14 / အကြိမ် ၁၁ = Row 24 ကွက်တိ ပုံသေနည်း
    target_row_idx = target_draw + 13
    
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    
    raw_paths_compiled = {"Head": {}, "Mid": {}, "Tail": {}}
    seen_composite_keys = set()
    
    max_rows = len(df)
    max_y_idx = len(head_cols) - 1
    
    # ၇၀,၀၀၀ ကျော် လမ်းကြောင်းများကို Memory ထဲတွင် Virtual ပေါင်းစပ် Loops ပတ်ခြင်း
    for pos_name, cols in positions:
        for y_idx in range(max_y_idx):
            for r_idx in range(2, max_rows):
                
                # ⚠️ [Strict Time-Capsule Control]: အတိတ်ပွဲစစ်လျှင် ရွေးချယ်ထားသောပွဲအောက်ခြေ (အနာဂတ်ဒေတာ) ကို ပိတ်ဆို့ခြင်း
                if is_backtest and r_idx >= target_row_idx: continue
                elif not is_backtest and r_idx >= len(df) - 1: continue

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
                            if val.lower() in ['x', 'nan', '']: valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            
                            digits.append(val)
                            
                            raw_lbl = raw_years_row[c_idx]
                            virtual_orig_year = str(raw_lbl).strip() if (str(raw_lbl).lower() != 'nan' and pd.notna(raw_lbl)) else "Unknown"
                            virtual_row_no = curr_r - 1
                            path_identifiers.append(f"{virtual_orig_year}_{virtual_row_no}")
                            
                        if valid:
                            # Composite DNA Key ဖြင့် နေရာတူပွားနေသော ဒေတာတုံးတုများ ညှပ်ပိတ်ခြင်း
                            composite_dna = f"{pos_name}_{y_step}_{r_step}_" + "-".join(path_identifiers)
                            if composite_dna in seen_composite_keys: continue
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
                    
                if valid: prefixes_found.append(tuple(digits))
                    
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

# --- 4. Filtering & 27 Pairs Generator ---
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

# 🛠 [Old Pure Text Display Fix]: အရင်ကုဒ်အဟောင်းအတိုင်း ၀ မှ ၉ အသေးစိတ်ကို စာသားသန့်သန့်ဖြင့် စီပြပေးမည့် Function
def display_granular_scores_text(pos_results, mode_type, min_c=None, max_c=None):
    if not pos_results:
        st.write("ဂဏန်းအချက်အလက်မရှိပါ")
        return
        
    allowed_digits = get_digits_by_filter(pos_results, mode_type, min_c, max_c)
    score_map = {str(i): 0 for i in range(10)}
    for r in pos_results:
        if r["digit"] in allowed_digits:
            score_map[r["digit"]] = r["match_count"]
            
    max_digit = max(score_map, key=score_map.get) if any(score_map.values()) else ""
    
    # စာသားသန့်သန့်ကို ဖုန်းမျက်နှာပြင်တွင် စီတန်းပြသခြင်း
    lines = []
    for i in range(10):
        d_str = str(i)
        score = score_map[d_str]
        fire = " 🔥 [MAIN]" if (d_str == max_digit and score > 0) else ""
        lines.append(f"ဂဏန်း [{d_str}] -> ကိုက်ညီမှု {score} ကြိမ် {fire}")
        
    st.markdown(f"<div class='score-box'>{'<br/>'.join(lines)}</div>", unsafe_allow_html=True)

# --- 5. Real Result Extractor Engine ---
def get_actual_result_string(df, target_year, target_draw):
    try:
        raw_years_row = df.iloc[0].tolist()
        target_col_base = -1
        for c_idx, raw_val in enumerate(raw_years_row):
            y_val = str(raw_val).strip()
            if not y_val or y_val.lower() == 'nan' or y_val == '': continue
            short_y = str(target_year)[-2:]
            if y_val == short_y or y_val == str(target_year):
                target_col_base = c_idx
                break
        if target_col_base == -1: target_col_base = len(df.columns) - 4
        
        target_row_idx = target_draw + 13
        h_val = str(df.iloc[target_row_idx, target_col_base]).strip().replace('.0','')
        m_val = str(df.iloc[target_row_idx, target_col_base + 1]).strip().replace('.0','')
        t_val = str(df.iloc[target_row_idx, target_col_base + 2]).strip().replace('.0','')
        return f"{h_val}{m_val}{t_val}"
    except:
        return "N/A"

# --- 6. User Interface Control Panel ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚙️ SYSTEM v16.0</h2>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Calendar File (2025_3D.xlsx)", type=["xlsx"])
    st.markdown("---")
    
    if file:
        st.markdown("### 🔍 MODE CONTROL")
        app_mode = st.radio("Working Mode:", ["Live Mode 🟢", "Deep Batch Backtest 🟡"])
        
        st.markdown("### 🔢 INPUT BOXES")
        input_year = st.number_input("Target Year (ခုနှစ်):", value=2026, min_value=1996, max_value=2030)
        input_draw = st.number_input("Target Draw (အကြိမ်ရေ):", value=11, min_value=1, max_value=50)
        
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
                
                if curr_draw <= 0: continue 
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
                        <h4>🎯 [ROUND {offset+1}] -> Year 20{curr_year if curr_year < 100 else str(curr_year)[-2:]} | Draw {curr_draw}</h4>
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
        # --- Live Mode Tabs Layout ---
        st.markdown(f"<h3 style='color:#D4AF37;'>📊 Virtual Matrix Dashboard (Year {input_year} | Draw {input_draw})</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Live Master Filter Analytics", use_container_width=True):
            with st.spinner("Processing 70,000+ Virtual Paths Syncing..."):
                st.session_state.v16_results = analyze_virtual_matrix(df_calendar, input_year, input_draw, is_backtest=False)
                st.success("✅ ၂၀၂၆ အတွက် ၇၀,၀၀0 ကျော် လမ်းကြောင်းများအားလုံး Virtual ပေါင်းစပ်တွက်ချက်မှု အောင်မြင်ပါသည်။")
                
        if "v16_results" in st.session_state and st.session_state.v16_results is not None:
            res = st.session_state.v16_results
            
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
                
                st.write(f"**ထိပ် လုံးဘိုင်:** {', '.join(s_h) if s_h else 'မရှိပါ'}")
                st.write(f"**လယ် လုံးဘိုင်:** {', '.join(s_m) if s_m else 'မရှိပါ'}")
                st.write(f"**ပိတ် လုံးဘိုင်:** {', '.join(s_t) if s_t else 'မရှိပါ'}")
                
                st.markdown("---")
                st.markdown("### 📊 အုပ်စုအသေးစိတ် ရမှတ်အပြည့်အစုံ (0 to 9)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**[ထိပ် HEAD အသေးစိတ်]**")
                    display_granular_scores_text(res["Head"], "single")
                with col2:
                    st.markdown("**[လယ် MID အသေးစိတ်]**")
                    display_granular_scores_text(res["Mid"], "single")
                with col3:
                    st.markdown("**[ပိတ် TAIL အသေးစိတ်]**")
                    display_granular_scores_text(res["Tail"], "single")
                
            with t2:
                st.markdown("<h4>🥈 ပုံစံတူ ၂ ခုနှင့်အောက် ကိုက်ညီသော လမ်းကြောင်းအတွဲများ</h4>", unsafe_allow_html=True)
                pairs_2 = generate_27_pairs(res, "double")
                st.text_area("2-Match Pairs Text:", value=" . ".join(pairs_2) if pairs_2 else "No Data", height=100)
                
                st.markdown("---")
                st.markdown("### 📊 အုပ်စုအသေးစိတ် ရမှတ်အပြည့်အစုံ (0 to 9)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**[ထိပ် HEAD အသေးစိတ်]**")
                    display_granular_scores_text(res["Head"], "double")
                with col2:
                    st.markdown("**[လယ် MID အသေးစိတ်]**")
                    display_granular_scores_text(res["Mid"], "double")
                with col3:
                    st.markdown("**[ပိတ် TAIL အသေးစိတ်]**")
                    display_granular_scores_text(res["Tail"], "double")
                
            with t3:
                st.markdown("<h4>🥇 ပုံစံတူ ၃ ခုနှင့်အထက် ရှိသမျှ True VIP အတွဲများ</h4>", unsafe_allow_html=True)
                pairs_3 = generate_27_pairs(res, "triple")
                st.text_area("VIP Pairs Text:", value=" . ".join(pairs_3) if pairs_3 else "No Data", height=100)
                
                st.markdown("---")
                st.markdown("### 📊 အုပ်စုအသေးစိတ် ရမှတ်အပြည့်အစုံ (0 to 9)")
                col1, col2, col3 = st.columns
