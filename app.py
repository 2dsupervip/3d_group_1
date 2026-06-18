import streamlit as st
import pandas as pd
import json
import itertools

# --- 1. Streamlit Page Configuration & Theme ---
st.set_page_config(layout="wide", page_title="Golden Cross 3D Core v10.1", page_icon="🎯")

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

# --- 2. Data Loading Engine ---
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    return df.iloc[1:].reset_index(drop=True)

# --- 3. Core Engine with Strict Layout Boundary & Deduplication ---
def analyze_matrix_core(df, target_r):
    head_cols = [c for c in range(1, len(df.columns)) if (c - 1) % 3 == 0]
    mid_cols = [c + 1 for c in head_cols]
    tail_cols = [c + 2 for c in head_cols]
    
    positions = [("Head", head_cols), ("Mid", mid_cols), ("Tail", tail_cols)]
    raw_matches = {"Head": {}, "Mid": {}, "Tail": {}}
    
    max_rows = len(df)
    max_y = len(head_cols) - 1
    seen_signatures = set()
    
    for pos_name, cols in positions:
        for y_idx in range(max_y):
            for r in range(max_rows):
                if r >= target_r: continue 
                
                for y_step in range(5):
                    for r_step in range(-4, 5):
                        if y_step == 0 and r_step == 0: continue
                        
                        digits, path_coords, valid = [], [], True
                        neighborhood_dna = []
                        
                        for i in range(4):
                            curr_r = r + i * r_step
                            curr_y = y_idx + i * y_step
                            
                            if curr_r < 0 or curr_r >= target_r or curr_y < 0 or curr_y >= max_y:
                                valid = False; break
                                
                            c_idx = cols[curr_y]
                            val = str(df.iloc[curr_r, c_idx]).strip()
                            if val.lower() in ['x', 'nan', '']:
                                valid = False; break
                            if val.endswith('.0'): val = val[:-2]
                            
                            left_v = str(df.iloc[curr_r, c_idx-1]).strip() if c_idx-1 >= 0 else ""
                            right_v = str(df.iloc[curr_r, c_idx+1]).strip() if c_idx+1 < len(df.columns) else ""
                            neighborhood_dna.append((val, left_v, right_v))
                            
                            digits.append(val)
                            path_coords.append(f"{curr_r}_{c_idx}")
                            
                        if valid:
                            dtup = tuple(digits)
                            path_joined = "->".join(path_coords)
                            dna_tup = (pos_name, tuple(neighborhood_dna))
                            
                            if dna_tup in seen_signatures: continue
                            seen_signatures.add(dna_tup)
                            
                            if dtup not in raw_matches[pos_name]:
                                raw_matches[pos_name][dtup] = set()
                            raw_matches[pos_name][dtup].add(path_joined)
                            
    results = {"Head": [], "Mid": [], "Tail": []}
    target_y = len(head_cols) - 1
    
    for pos_name, cols in positions:
        prefixes = []
        for y_step in range(5):
            for r_step in range(-4, 5):
                if y_step == 0 and r_step == 0: continue
                start_r = target_r - 3 * r_step
                start_y = target_y - 3 * y_step
                if start_r < 0 or start_r >= target_r or start_y < 0: continue
                
                valid, digits = True, []
                for i in range(3):
                    curr_r = start_r + i * r_step
                    curr_y = start_y + i * y_step
                    if curr_r < 0 or curr_r >= target_r or curr_y < 0 or curr_y >= len(cols):
                        valid = False; break
                    val = str(df.iloc[curr_r, cols[curr_y]]).strip()
                    if val.lower() in ['x', 'nan', '']: valid = False; break
                    if val.endswith('.0'): val = val[:-2]
                    digits.append(val)
                    
                if valid:
                    prefixes.append(tuple(digits))
                    
        for guess in range(10):
            guess_str = str(guess)
            match_count = 0
            
            for pref in prefixes:
                test_group = pref + (guess_str,)
                if test_group in raw_matches[pos_name]:
                    match_count += len(raw_matches[pos_name][test_group])
                    
            if match_count >= 1:
                results[pos_name].append({
                    "digit": guess_str, 
                    "match_count": match_count
                })
                
        results[pos_name] = sorted(results[pos_name], key=lambda x: x["match_count"], reverse=True)
        
    return results

# --- 4. Flexible Range Filter Engine (v10.1 No-Data Prevention Fix) ---
def get_digits_by_filter(pos_results, mode_type, min_c=None, max_c=None):
    if not pos_results: return []
    
    # 1. Loneိုင် Consensus (သီးခြားလမ်းကြောင်းများ)
    if mode_type == "single":
        return [r["digit"] for r in pos_results if r["match_count"] == 1]
    # 2. ပုံစံတူ ၂ ခုဝန်းကျင် (Flexible)
    elif mode_type == "double":
        return [r["digit"] for r in pos_results if r["match_count"] <= 2]
    # 3. 🛠 [ပြင်ဆင်ချက်] ၃ ခုနှင့်အထက် ရှိသမျှအားလုံးကို VIP အဖြစ် သိမ်းယူခြင်း (No-Data ကာကွယ်ရန်)
    elif mode_type == "triple":
        return [r["digit"] for r in pos_results if r["match_count"] >= 3]
    # 4. Custom Range
    elif mode_type == "custom" and min_c is not None and max_c is not None:
        return [r["digit"] for r in pos_results if min_c <= r["match_count"] <= max_c]
        
    return []

def generate_27_pairs(results, mode_type, min_c=None, max_c=None):
    h = get_digits_by_filter(results["Head"], mode_type, min_c, max_c)[:3]
    m = get_digits_by_filter(results["Mid"], mode_type, min_c, max_c)[:3]
    t = get_digits_by_filter(results["Tail"], mode_type, min_c, max_c)[:3]
    
    combos = list(itertools.product(h, m, t))
    return ["".join(c) for c in combos]

# --- 5. Actual Result Extract Engine for Backtest ---
def get_actual_result_string(df, target_r):
    try:
        last_col_idx = len(df.columns) - 1
        h_val = str(df.iloc[target_r, last_col_idx - 2]).strip().replace('.0','')
        m_val = str(df.iloc[target_r, last_col_idx - 1]).strip().replace('.0','')
        t_val = str(df.iloc[target_r, last_col_idx]).strip().replace('.0','')
        return f"{h_val}{m_val}{t_val}"
    except:
        return "Unknown"

# --- 6. Main Dashboard Layout ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚙️ CORE SYSTEM</h2>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Calendar Excel (.xlsx)", type=["xlsx"])
    st.markdown("---")
    
    if file:
        st.markdown("### 🔍 TARGET SELECTOR")
        mode = st.radio("Choose Working Mode:", ["Live Mode 🟢", "Batch Backtest Mode 🟡"])
        
        if mode == "Live Mode 🟢":
            target_row = st.number_input("Target Row Number:", value=45, min_value=5)
        else:
            backtest_rounds = st.slider("Backtest Rounds Count (1 to 5):", min_value=1, max_value=5, value=3)
            target_row = st.number_input("Starting Row for Backtest:", value=45, min_value=10)

if file:
    df = load_data(file)
    
    if "Batch Backtest Mode 🟡" in mode:
        st.markdown("<h3 style='color:#D4AF37;'>📊 Automated Robot Batch Backtest Report</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Batch Backtest", use_container_width=True):
            wins = 0
            total_tested = backtest_rounds
            
            for offset in range(backtest_rounds):
                current_target_r = (target_row - 2) - offset
                excel_row_lbl = current_target_r + 2
                
                round_results = analyze_matrix_core(df, current_target_r)
                generated_pairs = generate_27_pairs(round_results, "triple") # VIP Pairs (>=3 matches)
                actual_out = get_actual_result_string(df, current_target_r)
                
                is_win = actual_out in generated_pairs
                if is_win: wins += 1
                
                status_lbl = "<span class='win-text'>🏆 STATUS: WIN (✅ HIT)</span>" if is_win else "<span class='lose-text'>🏆 STATUS: LOSE (❌ MISS)</span>"
                pairs_display = " . ".join(generated_pairs) if generated_pairs else "No Pairs Generated"
                
                st.markdown(f"""
                    <div class="report-card">
                        <h4>🎯 [ROUND {offset+1}] -> Excel Row {excel_row_lbl}</h4>
                        <p>✨ <b>Actual Result:</b> <span style="font-size:16px; color:#ffcc00;">{actual_out}</span></p>
                        <p>🔮 <b>AI VIP 27 Pairs:</b> <span style="color:#b0b0b0;">{pairs_display}</span></p>
                        <p>{status_lbl}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            win_rate = (wins / total_tested) * 100 if total_tested > 0 else 0
            st.markdown("---")
            st.subheader("📈 FINAL EVALUATION SUMMARY")
            st.metric("TOTAL WINS", f"{wins} / {total_tested} Rounds")
            st.metric("WIN RATE PERCENTAGE", f"{win_rate:.1f}%")
            
    else:
        st.markdown("<h3 style='color:#D4AF37;'>📊 Matrix Group Splitter Dashboard</h3>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Master Filter Analytics", use_container_width=True):
            with st.spinner("Calculating Pure Logic..."):
                target_r_idx = target_row - 2
                st.session_state.live_results = analyze_matrix_core(df, target_r_idx)
                st.success("✅ တွက်ချက်မှု အောင်မြင်ပါသည်။")
                
        if "live_results" in st.session_state and st.session_state.live_results is not None:
            res = st.session_state.live_results
            
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
                
                # အမှတ်အများဆုံးထောက်ခံချက်ရသည့် ဂဏန်းများကို ဦးစားပေးပြသရန်
                st.write(f"**ထိပ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_h) if s_h else 'မရှိပါ'}")
                st.write(f"**လယ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_m) if s_m else 'မရှိပါ'}")
                st.write(f"**ပိတ် လုံးဘိုင်ဂဏန်းများ:** {', '.join(s_t) if s_t else 'မရှိပါ'}")
                
            with t2:
                st.markdown("<h4>🥈 ပုံစံတူ ၂ ခုနှင့်အောက် ကိုက်ညီသော လမ်းကြောင်းအတွဲများ</h4>", unsafe_allow_html=True)
                pairs_2 = generate_27_pairs(res, "double")
                st.text_area("2-Match Pairs Text:", value=" . ".join(pairs_2) if pairs_2 else "No Data", height=100)
                
            with t3:
                st.markdown("<h4>🥇 ပုံစံတူ ၃ ခုနှင့်အထက် ရှိသမျှ VIP အတွဲများ</h4>", unsafe_allow_html=True)
                pairs_3 = generate_27_pairs(res, "triple")
                st.text_area("VIP Pairs Text:", value=" . ".join(pairs_3) if pairs_3 else "No Data", height=100)
                
            with t4:
                st.markdown("<h4>⚙️ Custom Range အုပ်စု အရေအတွက် ကန့်သတ်ခြင်း</h4>", unsafe_allow_html=True)
                c_min = st.number_input("Minimum Match Count:", value=4, min_value=1)
                c_max = st.number_input("Maximum Match Count:", value=6, min_value=1)
                
                pairs_c = generate_27_pairs(res, "custom", c_min, c_max)
                st.text_area(f"Custom Pairs ({c_min} to {c_max} Matches):", value=" . ".join(pairs_c) if pairs_c else "No Data", height=100)
else:
    st.info("💡 ဆက်လက်လုပ်ဆောင်ရန်အတွက် ဘယ်ဘက် Sidebar Panel တွင် Excel (.xlsx) ဒေတာဖိုင်ကို တင်ပေးပါ Bro!")
