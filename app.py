import streamlit as st
import pandas as pd
import numpy as np

# --- Data & Logic Engine ---
def load_and_clean_data(file_path):
    # CSV အစား Excel ကို ဖတ်ရန် ပြင်ဆင်ထားခြင်း
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    
    # ပထမဆုံး Row (Header) ကို ဖယ်ထုတ်ပြီး Data သီးသန့်ယူခြင်း
    df = df.iloc[1:].reset_index(drop=True)
    return df

def extract_pattern_groups(df):
    all_extracted_groups = []
    max_rows = len(df)
    
    # ထိပ်ဂဏန်း Column များကို ရှာဖွေခြင်း (1, 4, 7, 10, ...)
    head_cols = [col for col in range(1, len(df.columns)) if (col - 1) % 4 == 0]
    total_years = len(head_cols)
    
    for y_idx in range(total_years - 1, -1, -1):
        for r in range(max_rows):
            for r_step in range(1, 5):
                group_data = get_4digit_group(df, head_cols, r, y_idx, r_step=r_step, y_step=0)
                if group_data:
                    all_extracted_groups.append(group_data)
                    
            for y_step in range(1, 5):
                for r_step in range(0, 5):
                    group_data = get_4digit_group(df, head_cols, r, y_idx, r_step=r_step, y_step=y_step)
                    if group_data:
                        all_extracted_groups.append(group_data)
                        
    return all_extracted_groups

def get_4digit_group(df, head_cols, start_r, start_y_idx, r_step, y_step):
    group = []
    path_info = f"Row {start_r + 2}, Year {df.iloc[0, head_cols[start_y_idx]] if start_r==0 else '...'} | r_step: {r_step}, y_step: {y_step}"
    
    for i in range(4):
        curr_r = start_r + (i * r_step)
        curr_y_idx = start_y_idx + (i * y_step)
        
        if curr_r >= len(df) or curr_y_idx >= len(head_cols):
            return None
            
        col_index = head_cols[curr_y_idx]
        val = str(df.iloc[curr_r, col_index]).strip()
        
        if val.lower() == 'x' or pd.isna(df.iloc[curr_r, col_index]) or val == '':
            return None
            
        # .0 (decimal) ပါလာပါက ဖယ်ရှားရန် (ဥပမာ 8.0 ကို 8 အဖြစ်ပြောင်းရန်)
        if val.endswith('.0'):
            val = val[:-2]
            
        group.append(val)
        
    return {"digits": tuple(group), "path": path_info}

# --- Streamlit UI ---
st.set_page_config(page_title="The Golden Cross 3D - Engine Test", layout="wide")
st.title("🎯 The Golden Cross 3D - Pattern Matrix Extractor")

st.markdown("### ဇယားအတွင်းမှ လမ်းကြောင်းများအားလုံးကို ရှာဖွေခြင်း")

# Excel (xlsx) File ကိုသာ Upload လုပ်ခွင့်ပြုရန် ပြင်ဆင်ထားသည်
uploaded_file = st.file_uploader("Bro ရဲ့ Excel (.xlsx) ဒေတာဖိုင်ကို ထည့်ပါ", type=["xlsx"])

if uploaded_file is not None:
    with st.spinner('Data များကို တွက်ချက်နေပါသည်... အနည်းငယ် စောင့်ပါ။'):
        # Data ဖတ်ခြင်းနှင့် တွက်ချက်ခြင်း
        df = load_and_clean_data(uploaded_file)
        raw_groups = extract_pattern_groups(df)
        
        st.success(f"✅ အောင်မြင်ပါသည်။ စုစုပေါင်း ရှာဖွေတွေ့ရှိသည့် Pattern Group အရေအတွက်: **{len(raw_groups):,}** ခု")
        
        st.subheader("နမူနာ Pattern Group များ (ပထမဆုံး အခု ၅၀)")
        
        display_data = [{"Digits": str(g["digits"]), "Path Info": g["path"]} for g in raw_groups[:50]]
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)
else:
    st.info("ကျေးဇူးပြု၍ `2025_3D.xlsx` ဖိုင်ကို Upload တင်ပေးပါ။")
