import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import uuid
from rag import load_data, search_relevant_places

# กำหนดค่า API KEY
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ตั้งค่า Streamlit
st.set_page_config(page_title="TripTech AI", page_icon="🌴")
st.title("🌴 TripTech AI")

# โหลดข้อมูลจาก Excel
df = load_data()

# สร้าง session_id เพื่อแยกแต่ละการใช้งาน
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ฟังก์ชันบันทึกข้อความลง Excel
def save_to_excel(session_id, role, message):
    path = "chat_history.xlsx"
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

# เตรียมตัวแปรเก็บบทสนทนา
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงบทสนทนาเก่า
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# รับข้อความจากผู้ใช้
user_input = st.chat_input("อยากเที่ยวที่ไหน ถามมาได้เลย...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_to_excel(st.session_state.session_id, "user", user_input)

    # ค้นหาสถานที่จาก Excel
    results = search_relevant_places(df, user_input)
    context = "\n".join(
        f"- {r['ชื่อสถานที่']} ({r['จังหวัด']}): {r['คำอธิบาย']}" for r in results
    )

    # รวมบทสนทนาเดิมเป็นบริบท
    history_text = ""
    for i, msg in enumerate(st.session_state.messages):
        if i == 0 and msg["role"] == "assistant":
            continue
        role = "ผู้ใช้" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['content']}\n"

    # สร้าง prompt
    prompt = f"""
คุณคือไกด์ท่องเที่ยวในภาคใต้ของประเทศไทย
ต่อไปนี้คือบทสนทนาระหว่างคุณกับผู้ใช้:
{history_text}

ข้อมูลสถานที่อ้างอิง:
{context}

กรุณาตอบคำถามล่าสุดต่อจากบทสนทนาเดิมอย่างสอดคล้อง ใช้ภาษากระชับ เป็นกันเอง ไม่ทักทายซ้ำถ้าไม่ใช่ประโยคแรก
"""

    # เรียก Gemini AI
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"❌ เกิดข้อผิดพลาดจาก Gemini: {e}"

    # แสดงและบันทึกคำตอบ AI
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    save_to_excel(st.session_state.session_id, "assistant", bot_reply)
