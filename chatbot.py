import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from rag import load_data, search_relevant_places

# ตั้งค่า API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# โหลดข้อมูลผู้ใช้
user_df = pd.read_excel("data/users.xlsx")

# ฟังก์ชันตรวจสอบการเข้าสู่ระบบ
def login(username, password):
    return any((user_df["username"] == username) & (user_df["password"] == password))

# ตรวจสอบสถานะล็อกอิน
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 เข้าสู่ระบบ TripTech AI")
    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")
    if st.button("เข้าสู่ระบบ"):
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("เข้าสู่ระบบสำเร็จ")
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# ✅ หลังล็อกอินสำเร็จ เริ่มใช้งาน
st.set_page_config(page_title="TripTech AI", page_icon="🌴")
st.title("🌴 TripTech AI")

# โหลดข้อมูลสถานที่
df = load_data()

# เตรียม session_id เป็นชื่อผู้ใช้
session_id = st.session_state.username

# โหลดประวัติการคุยของผู้ใช้ (จาก Excel)
history_path = "data/chat_history.xlsx"
if os.path.exists(history_path):
    history_df = pd.read_excel(history_path)
    user_history = history_df[history_df["session_id"] == session_id]
    st.session_state.messages = user_history[["role", "message"]].to_dict(orient="records")
else:
    st.session_state.messages = []

# แสดงประวัติสนทนา
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["message"])

# ฟังก์ชันบันทึกข้อความลง Excel
def save_to_excel(session_id, role, message):
    path = "data/chat_history.xlsx"
    if os.path.exists(path):
        df = pd.read_excel(path)
    else:
        df = pd.DataFrame(columns=["session_id", "role", "message"])
    df = pd.concat([df, pd.DataFrame([{
        "session_id": session_id,
        "role": role,
        "message": message
    }])], ignore_index=True)
    df.to_excel(path, index=False)

# รับข้อความใหม่
user_input = st.chat_input("อยากเที่ยวที่ไหน ถามมาได้เลย...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "message": user_input})
    save_to_excel(session_id, "user", user_input)

    # หา context จาก Excel
    results = search_relevant_places(df, user_input)
    context = "\n".join(
        f"- {r['ชื่อสถานที่']} ({r['จังหวัด']}): {r['คำอธิบาย']}" for r in results
    )

    # รวมบทสนทนาเป็น prompt
    history_text = ""
    for i, msg in enumerate(st.session_state.messages):
        if i == 0 and msg["role"] == "assistant":
            continue
        role = "ผู้ใช้" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['message']}\n"

    prompt = f"""
คุณคือไกด์ท่องเที่ยวในภาคใต้ของประเทศไทย
ต่อไปนี้คือบทสนทนาระหว่างคุณกับผู้ใช้:
{history_text}

ข้อมูลสถานที่อ้างอิง:
{context}

กรุณาตอบคำถามล่าสุดต่อจากบทสนทนาเดิมอย่างสอดคล้อง ใช้ภาษากระชับ เป็นกันเอง ไม่ทักทายซ้ำถ้าไม่ใช่ประโยคแรก
"""

    # เรียก Gemini
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"❌ เกิดข้อผิดพลาดจาก Gemini: {e}"

    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "message": bot_reply})
    save_to_excel(session_id, "assistant", bot_reply)
