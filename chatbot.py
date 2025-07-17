import streamlit as st
import google.generativeai as genai
from rag import load_data, search_relevant_places
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

# โหลด config.yaml สำหรับล็อกอิน
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# ฟังก์ชันบันทึกผู้ใช้ใหม่ลง config.yaml
def save_user_to_yaml(username, name, email, password):
    from streamlit_authenticator.utilities.hasher import Hasher
    hashed_pw = Hasher.hash(password)
    config["credentials"]["usernames"][username] = {
        "name": name,
        "email": email,
        "password": hashed_pw
    }
    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False)

# สร้างตัวจัดการการล็อกอิน
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# หน้าล็อกอิน
name, authentication_status, username = authenticator.login("Login", location="main")

# ฟอร์มสมัครสมาชิกแบบบันทึกถาวร
with st.expander("📝 สมัครสมาชิกใหม่"):
    with st.form("register_form", clear_on_submit=True):
        new_username = st.text_input("👤 ชื่อผู้ใช้", key="reg_user")
        new_name = st.text_input("🧑‍💼 ชื่อเต็ม", key="reg_name")
        new_email = st.text_input("📧 อีเมล", key="reg_email")
        new_password = st.text_input("🔑 รหัสผ่าน", type="password", key="reg_pass")
        submitted = st.form_submit_button("สมัครสมาชิก")

        if submitted:
            if new_username in config["credentials"]["usernames"]:
                st.error("❌ ชื่อนี้ถูกใช้ไปแล้ว")
            else:
                save_user_to_yaml(new_username, new_name, new_email, new_password)
                st.success("✅ สมัครสำเร็จแล้ว! ไปล็อกอินได้เลย")

# หน้าหลักเมื่อเข้าสู่ระบบสำเร็จ
if authentication_status:
    authenticator.logout("ออกจากระบบ", "sidebar")
    st.sidebar.write(f"👋 ยินดีต้อนรับ {name}")

    # ฟอร์มเปลี่ยนรหัสผ่าน
    with st.sidebar.expander("🔐 เปลี่ยนรหัสผ่าน"):
        try:
            if authenticator.reset_password(username, "เปลี่ยนรหัสผ่าน"):
                st.success("เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")
        except Exception as e:
            st.error(e)

    # ======= ระบบหลัก TripTech AI =======
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    st.set_page_config(page_title="TripTech AI", page_icon="🌴")
    st.title("🌴 TripTech AI")

    df = load_data()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("อยากเที่ยวที่ไหน ถามมาได้เลย...")

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        results = search_relevant_places(df, user_input)
        context = "\n".join(
            f"- {r['ชื่อสถานที่']} ({r['จังหวัด']}): {r['คำอธิบาย']}\nรูปภาพ: {r.get('รูปภาพ', '')}"
            for r in results
        )

        history_text = ""
        for i, msg in enumerate(st.session_state.messages):
            if i == 0 and msg["role"] == "assistant":
                continue
            role = "ผู้ใช้" if msg["role"] == "user" else "AI"
            history_text += f"{role}: {msg['content']}\n"

        prompt = f"""
คุณคือไกด์ท่องเที่ยวในภาคใต้ของประเทศไทย
ต่อไปนี้คือบทสนทนาระหว่างคุณกับผู้ใช้:
{history_text}

ข้อมูลสถานที่อ้างอิง:
{context}

กรุณาตอบคำถามล่าสุดต่อจากบทสนทนาเดิมอย่างสอดคล้อง ใช้ภาษากระชับ เป็นกันเอง ไม่ทักทายซ้ำถ้าไม่ใช่ประโยคแรก
"""

        try:
            model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")
            response = model.generate_content(prompt)
            bot_reply = response.text
        except Exception as e:
            bot_reply = f"❌ เกิดข้อผิดพลาดจาก Gemini: {e}"

        st.chat_message("assistant").markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        for r in results:
            if 'รูปภาพ' in r and isinstance(r['รูปภาพ'], str) and r['รูปภาพ'].startswith("http"):
                st.image(r['รูปภาพ'], caption=r['ชื่อสถานที่'], use_container_width=True)
                if 'เครดิต' in r and isinstance(r['เครดิต'], str) and r['เครดิต'].strip():
                    st.markdown(
                        f"<div style='font-size: 0.8em; color: gray;'>📸 เครดิต: {r['เครดิต']}</div>",
                        unsafe_allow_html=True
                    )

elif authentication_status is False:
    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
elif authentication_status is None:
    st.warning("🔐 กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")