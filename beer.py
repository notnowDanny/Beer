import streamlit as st
import pandas as pd
import sqlite3
import os
import time
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components
import base64

# --- [수정] 실행 중인 파일의 절대 경로를 기준으로 폴더 지정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "beer_images")
DB_FILE = os.path.join(BASE_DIR, "beer_pro.db")

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

conn = init_db()
df = pd.read_sql_query("SELECT * FROM beers", conn)

st.set_page_config(page_title="Beer Note Pro v4.0", layout="wide", page_icon="🍺")

# --- [수정] 대소문자 및 경로 문제를 방지하는 Base64 변환 함수 ---
def get_image_base64(path):
    if not path:
        return None
        
    # DB에 저장된 경로가 상대경로라면 절대경로로 보정
    if not os.path.isabs(path):
        # 만약 경로에 'beer_images/'가 중복으로 들어가는 것을 방지
        filename = os.path.basename(path)
        actual_path = os.path.join(IMG_DIR, filename)
    else:
        actual_path = path

    # 파일 존재 여부 확인 (리눅스 서버 대응)
    if os.path.exists(actual_path):
        with open(actual_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

def render_custom_image(img_path):
    b64_str = get_image_base64(img_path)
    if b64_str:
        html_code = f"""
        <div style="display: flex; justify-content: center; align-items: center; 
                    height: 120px; width: 100%; background-color: #f9f9f9; 
                    border-radius: 10px; border: 1px solid #eee; overflow: hidden;">
            <img src="data:image/jpeg;base64,{b64_str}" 
                 style="max-height: 100%; max-width: 100%; object-fit: contain;">
        </div>
        """
    else:
        html_code = """
        <div style="display: flex; justify-content: center; align-items: center; 
                    height: 120px; width: 100%; background-color: #f9f9f9; 
                    border-radius: 10px; border: 1px solid #eee; color: #999; font-size: 14px;">
            📷 No Photo
        </div>
        """
    components.html(html_code, height=130)

BEER_STYLES = ["Lager", "IPA", "Hazy IPA", "Pale Ale", "Hazy Pale Ale", "Stout", "Pilsner", "Wheat", "Sour", "Porter", "기타"]

# --- 사이드바 ---
st.sidebar.header("📝 새 맥주 기록")
with st.sidebar.form("beer_form", clear_on_submit=True):
    name = st.text_input("맥주 이름")
    company = st.text_input("제조사")
    beer_type = st.selectbox("종류", BEER_STYLES)
    col_in1, col_in2 = st.columns(2)
    abv = col_in1.number_input("도수 (%)", 0.0, 25.0, 0.0, 0.1)
    price = col_in2.number_input("가격 ($)", 0.0, 1000.0, 0.0, 0.1)
    uploaded_file = st.file_uploader("라벨 사진", type=['jpg', 'png', 'jpeg'])
    
    st.write("---")
    sc1 = st.slider("향", 1, 5, 1)
    sc2 = st.slider("맛", 1, 5, 1)
    sc3 = st.slider("바디감", 1, 5, 1)
    sc4 = st.slider("밸런스", 1, 5, 1)
    comment = st.text_area("시음평")
    
    if st.form_submit_button("기록 저장"):
        if name:
            avg = round((sc1 + sc2 + sc3 + sc4) / 4, 2)
            # 파일명을 저장할 때 폴더명 포함 구조로 통일
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}.jpg"
            img_path = os.path.join(IMG_DIR, filename)
            
            if uploaded_file:
                with open(img_path, "wb") as f: 
                    f.write(uploaded_file.getbuffer())
            else:
                img_path = ""
                
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
        with st.container(border=True):
            c1, c2, c3 = st.columns([1.5, 3, 1])
            with c1:
                render_custom_image(row['이미지경로'])
            with c2:
                st.subheader(row['이름'])
                st.write(f"**{row['종류']}** | {row['제조사']} | {row['도수']}%")
                st.caption(row['한줄평'])
            with c3:
                st.metric("평점", f"⭐ {row['종합평점']}")

with tab2:
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df, names='종류', title="선호 스타일", hole=0.4), use_container_width=True)
        c2.plotly_chart(px.histogram(df, x="종합평점", title="평점 분포"), use_container_width=True)

with tab3:
    if not df.empty:
        choice = st.selectbox("수정할 기록 선택", df.index, format_func=lambda i: f"{df.at[i, '이름']} ({df.at[i, '날짜']})")
        row = df.loc[choice]
        
        with st.form("edit_form"):
            st.subheader("✏️ 정보 수정")
            col_e1, col_e2 = st.columns([1.5, 2])
            with col_e1:
                st.write("**현재 이미지**")
                render_custom_image(row['이미지경로'])
                u_file = st.file_uploader("이미지 교체", type=['jpg', 'png', 'jpeg'])
            with col_e2:
                u_name = st.text_input("이름", row["이름"])
                u_comp = st.text_input("제조사", row["제조사"])
                u_type = st.selectbox("종류", BEER_STYLES, index=BEER_STYLES.index(row["종류"]) if row["종류"] in BEER_STYLES else 0)
                u_abv = st.number_input("도수", 0.0, 25.0, float(row["도수"]))
                u_price = st.number_input("가격", 0.0, 1000.0, float(row["가격"]))
            
            st.write("---")
            u_sc1 = st.slider("향", 1, 5, int(row["향"]), key="e1")
            u_sc2 = st.slider("맛", 1, 5, int(row["맛"]), key="e2")
            u_sc3 = st.slider("바디감", 1, 5, int(row["바디감"]), key="e3")
            u_sc4 = st.slider("밸런스", 1, 5, int(row["밸런스"]), key="e4")
            u_comm = st.text_area("시음평", value=str(row["한줄평"]))
            
            if st.form_submit_button("💾 수정사항 저장"):
                u_avg = round((u_sc1 + u_sc2 + u_sc3 + u_sc4) / 4, 2)
                final_path = row['이미지경로']
                if u_file:
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{u_name}.jpg"
                    final_path = os.path.join(IMG_DIR, filename)
                    with open(final_path, "wb") as f: f.write(u_file.getbuffer())
                cur = conn.cursor()
                cur.execute("""UPDATE beers SET 이름=?, 제조사=?, 종류=?, 도수=?, 가격=?, 향=?, 맛=?, 바디감=?, 밸런스=?, 종합평점=?, 한줄평=?, 이미지경로=? 
                               WHERE id=?""", (u_name, u_comp, u_type, u_abv, u_price, u_sc1, u_sc2, u_sc3, u_sc4, u_avg, u_comm, final_path, int(row['id'])))
                conn.commit()
                st.success("수정 완료!"); time.sleep(0.5); st.rerun()
            
        if st.button("🗑️ 영구 삭제"):
            if row['이미지경로']:
                filename = os.path.basename(row['이미지경로'])
                actual_path = os.path.join(IMG_DIR, filename)
                if os.path.exists(actual_path):
                    os.remove(actual_path)
            cur = conn.cursor()
            cur.execute("DELETE FROM beers WHERE id=?", (int(row['id']),))
            conn.commit()
            st.warning("삭제 완료"); time.sleep(0.5); st.rerun()
