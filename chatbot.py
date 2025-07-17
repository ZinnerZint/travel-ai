import streamlit as st
import google.generativeai as genai
from rag import load_data, search_relevant_places

# ตั้งค่า API key สำหรับ Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ตั้งค่าหน้าหลัก
st.set_page_config(page_title="TripTech AI", page_icon="🌴")
st.title("🌴 TripTech AI")

# โหลดข้อมูลจาก Excel
df = load_data()

# เตรียมตัวแปรสำหรับเก็บบทสนทนา
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงบทสนทนาเดิมทั้งหมด
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# กล่องรับข้อความผู้ใช้
user_input = st.chat_input("อยากเที่ยวที่ไหน ถามมาได้เลย...")

if user_input:
    # บันทึกข้อความจากผู้ใช้
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ค้นหาสถานที่ที่เกี่ยวข้องจาก Excel
    results = search_relevant_places(df, user_input)
    context = "\n".join(
        f"- {r['ชื่อสถานที่']} ({r['จังหวัด']}): {r['คำอธิบาย']}"
        for r in results
    )

    # รวมบทสนทนาเดิมเป็นบริบท
    history_text = ""
    for i, msg in enumerate(st.session_state.messages):
        if i == 0 and msg["role"] == "assistant":
            continue  # ข้ามข้อความทักทายซ้ำ
        role = "ผู้ใช้" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['content']}\n"

    # รวม prompt
    prompt = f"""
คุณคือไกด์ท่องเที่ยวในภาคใต้ของประเทศไทย
ต่อไปนี้คือบทสนทนาระหว่างคุณกับผู้ใช้:
{history_text}

ข้อมูลสถานที่อ้างอิง:
{context}

กรุณาตอบคำถามล่าสุดต่อจากบทสนทนาเดิมอย่างสอดคล้อง ใช้ภาษากระชับ เป็นกันเอง ไม่ทักทายซ้ำถ้าไม่ใช่ประโยคแรก
"""

    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")  # ใช้ Gemini Pro
        response = model.generate_content(prompt)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"❌ เกิดข้อผิดพลาดจาก Gemini: {e}"

    # แสดงคำตอบจาก AI
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
