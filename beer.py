import streamlit as st
import pandas as pd
import sqlite3
import os
import time
from datetime import datetime
import plotly.express as px

# 1. 초기 설정
IMG_DIR = "beer_images"
DB_FILE = "beer_pro.db"
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS beers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  날짜 TEXT, 이름 TEXT, 제조사 TEXT, 종류 TEXT, 
                  도수 REAL, 가격 REAL, 향 INTEGER, 맛 INTEGER, 
                  바디감 INTEGER, 밸런스 INTEGER, 종합평점 REAL, 
                  한줄평 TEXT, 이미지경로 TEXT)''')
    conn.commit()
    return conn

def safe_float(val, default=0.0):
    try: return float(val) if val is not None else default
    except: return default

conn = init_db()
df = pd.read_sql_query("SELECT * FROM beers", conn)

st.set_page_config(page_title="Beer Note Pro v3.6", layout="wide", page_icon="🍺")

# 이미지 크기 강제 조절 CSS (120px 고정)
st.markdown("""
    <style>
        div[data-testid="stImage"] img {
            height: 120px !important;
            width: auto !important;
            object-fit: contain !important;
            border-radius: 8px;
            border: 1px solid #f0f0f0;
        }
        .beer-card {
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #eee;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# 맥주 종류 목록 업데이트 (Hazy 스타일 추가)
BEER_STYLES = [
    "Lager", "IPA", "Hazy IPA", "Pale Ale", "Hazy Pale Ale", 
    "Stout", "Pilsner", "Wheat", "Sour", "Porter", "기타"
]

# --- 사이드바 ---
st.sidebar.header("📝 새 맥주 기록")
with st.sidebar.form("beer_form", clear_on_submit=True):
    name = st.text_input("맥주 이름")
    company = st.text_input("제조사")
    beer_type = st.selectbox("종류", BEER_STYLES)
    col_in1, col_in2 = st.columns(2)
    abv = col_in1.number_input("도수 (%)", 0.0, 25.0, 0.0, 0.1)
    price = col_in2.number_input("가격 ($)", 0.0, 1000.0, 0.0, 0.1)
    uploaded_file = st.file_uploader("라벨 사진 업로드", type=['jpg', 'png', 'jpeg'])
    
    st.write("---")
    sc_cols = st.columns(2)
    sc1 = sc_cols[0].slider("향", 1, 5, 1)
    sc2 = sc_cols[1].slider("맛", 1, 5, 1)
    sc3 = sc_cols[0].slider("바디감", 1, 5, 1)
    sc4 = sc_cols[1].slider("밸런스", 1, 5, 1)
    comment = st.text_area("시음평")
    
    if st.form_submit_button("기록 저장"):
        if name:
            avg = round((sc1 + sc2 + sc3 + sc4) / 4, 2)
            img_path = ""
            if uploaded_file:
                img_path = os.path.join(IMG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}.jpg")
                with open(img_path, "wb") as f: f.write(uploaded_file.getbuffer())
            cur = conn.cursor()
            cur.execute("INSERT INTO beers (날짜, 이름, 제조사, 종류, 도수, 가격, 향, 맛, 바디감, 밸런스, 종합평점, 한줄평, 이미지경로) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (datetime.now().strftime("%Y-%m-%d"), name, company, beer_type, abv, price, sc1, sc2, sc3, sc4, avg, comment, img_path))
            conn.commit()
            st.sidebar.success("저장 완료!")
            time.sleep(0.5); st.rerun()

# --- 메인 화면 ---
tab1, tab2, tab3 = st.tabs(["📊 목록 보기", "📈 취향 분석", "🛠️ 수정 및 삭제"])

with tab1:
    search = st.text_input("🔍 검색")
    view_df = df[df['이름'].str.contains(search, case=False) | df['제조사'].str.contains(search, case=False)] if search else df
    
    for _, row in view_df.sort_values("날짜", ascending=False).iterrows():
        st.markdown(f'<div class="beer-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 3, 1])
        with c1:
            if row['이미지경로'] and os.path.exists(row['이미지경로']):
                st.image(row['이미지경로'], use_container_width=False)
            else:
                st.write("📷 사진 없음")
        with c2:
            st.subheader(row['이름'])
            st.write(f"**{row['종류']}** | {row['제조사']} | {row['도수']}%")
            st.caption(row['한줄평'])
        with c3:
            st.metric("평점", f"⭐ {row['종합평점']}")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df, names='종류', title="선호 스타일", hole=0.4), use_container_width=True)
        c2.plotly_chart(px.histogram(df, x="종합평점", title="평점 분포"), use_container_width=True)

with tab3:
    if not df.empty:
        choice = st.selectbox("기록 선택", df.index, format_func=lambda i: f"{df.at[i, '이름']} ({df.at[i, '날짜']})")
        row = df.loc[choice]
        
        with st.form("edit_form"):
            st.subheader("✏️ 정보 수정")
            col_e1, col_e2 = st.columns([1, 2])
            with col_e1:
                if row['이미지경로'] and os.path.exists(row['이미지경로']):
                    st.image(row['이미지경로'], use_container_width=False)
                u_file = st.file_uploader("사진 변경", type=['jpg', 'png', 'jpeg'])
            with col_e2:
                u_name = st.text_input("이름", row["이름"])
                u_comp = st.text_input("제조사", row["제조사"])
                # 수정 시에도 추가된 종류를 올바르게 인식하도록 설정
                try: current_style_index = BEER_STYLES.index(row["종류"])
                except: current_style_index = 0
                u_type = st.selectbox("종류", BEER_STYLES, index=current_style_index)
                u_abv = st.number_input("도수", 0.0, 25.0, safe_float(row["도수"]))
                u_price = st.number_input("가격", 0.0, 1000.0, safe_float(row["가격"]))
            
            st.write("---")
            se_cols = st.columns(4)
            u_sc1 = se_cols[0].slider("향", 1, 5, int(row["향"]))
            u_sc2 = se_cols[1].slider("맛", 1, 5, int(row["맛"]))
            u_sc3 = se_cols[2].slider("바디감", 1, 5, int(row["바디감"]))
            u_sc4 = se_cols[3].slider("밸런스", 1, 5, int(row["밸런스"]))
            u_comm = st.text_area("시음평", value=str(row["한줄평"]))
            
            if st.form_submit_button("💾 수정 저장"):
                u_avg = round((u_sc1 + u_sc2 + u_sc3 + u_sc4) / 4, 2)
                final_path = row['이미지경로']
                if u_file:
                    final_path = os.path.join(IMG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{u_name}.jpg")
                    with open(final_path, "wb") as f: f.write(u_file.getbuffer())
                cur = conn.cursor()
                cur.execute("""UPDATE beers SET 이름=?, 제조사=?, 종류=?, 도수=?, 가격=?, 향=?, 맛=?, 바디감=?, 밸런스=?, 종합평점=?, 한줄평=?, 이미지경로=? 
                               WHERE id=?""", (u_name, u_comp, u_type, u_abv, u_price, u_sc1, u_sc2, u_sc3, u_sc4, u_avg, u_comm, final_path, int(row['id'])))
                conn.commit()
                st.success("수정 완료!"); time.sleep(0.5); st.rerun()
            
        if st.button("🗑️ 삭제"):
            if row['이미지경로'] and os.path.exists(row['이미지경로']): os.remove(row['이미지경로'])
            cur = conn.cursor()
            cur.execute("DELETE FROM beers WHERE id=?", (int(row['id']),))
            conn.commit()
            st.warning("삭제됨"); time.sleep(0.5); st.rerun()