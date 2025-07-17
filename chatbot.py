import streamlit as st
import google.generativeai as genai
from rag import load_data, search_relevant_places
from login import login

# --- PAGE CONFIG ---
st.set_page_config(page_title="TripTech AI", page_icon="🌴", layout="centered")

# --- AUTHENTICATION ---
if not login():
    st.stop()

# --- MAIN APP ---
st.title("🌴 TripTech AI")

# Load data
df = load_data()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_input := st.chat_input("อยากเที่ยวที่ไหน ถามมาได้เลย..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Search for relevant places
    results = search_relevant_places(df, user_input)
    context = "\n".join(
        f"- {r['ชื่อสถานที่']} ({r['จังหวัด']}): {r['คำอธิบาย']}\nรูปภาพ: {r.get('รูปภาพ', '')}"
        for r in results
    )

    # Build conversation history for the prompt
    history_text = ""
    for msg in st.session_state.messages:
        role = "ผู้ใช้" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['content']}\n"

    # Create the prompt for the generative model
    prompt = f"""
คุณคือไกด์ท่องเที่ยวในภาคใต้ของประเทศไทยที่มีความเชี่ยวชาญและเป็นมิตร
บทสนทนาที่ผ่านมา:
{history_text}
ข้อมูลสถานที่เพื่อใช้อ้างอิง:
{context}
คำแนะนำ:
- ตอบคำถามล่าสุดของผู้ใช้โดยใช้ข้อมูลที่ให้มาและบทสนทนาก่อนหน้า
- ใช้ภาษาที่เป็นกันเอง กระชับ และเข้าใจง่าย
- ถ้าไม่มั่นใจในคำตอบ ให้บอกว่า "ขออภัยค่ะ/ครับ ขณะนี้ยังไม่มีข้อมูลในส่วนนี้"
- ไม่ต้องทักทายซ้ำซ้อน
- หากมีรูปภาพในข้อมูลอ้างอิง ให้แสดงรูปภาพนั้นด้วย
"""

    # Generate response from the model
    try:
        model = genai.GenerativeModel(model_name="gemini-pro")
        response = model.generate_content(prompt)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"❌ ขออภัยค่ะ เกิดข้อผิดพลาด: {e}"
        st.error(bot_reply)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

        # Display images if available in the search results
        for r in results:
            if 'รูปภาพ' in r and isinstance(r['รูปภาพ'], str) and r['รูปภาพ'].startswith("http"):
                st.image(r['รูปภาพ'], caption=r['ชื่อสถานที่'], use_container_width=True)
                if 'เครดิต' in r and isinstance(r['เครดิต'], str) and r['เครดิต'].strip():
                    st.markdown(
                        f"<div style='font-size: 0.8em; color: gray; text-align: right;'>📸 เครดิต: {r['เครดิต']}</div>",
                        unsafe_allow_html=True,
                    )
