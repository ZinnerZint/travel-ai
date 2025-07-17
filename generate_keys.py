try:
    from streamlit_authenticator.utilities.hasher import Hasher
except ModuleNotFoundError:
    print("❌ กรุณาติดตั้งไลบรารีด้วยคำสั่ง: pip install streamlit-authenticator")
    exit()

# 🔐 รหัสผ่านแบบ plain text
passwords = ['zinner123', 'triptech2025']  # แก้ไขได้ตามต้องการ

# ✅ แฮชแต่ละรหัสผ่านด้วยการวนลูป
hashed_passwords = [Hasher.hash(pw) for pw in passwords]

print("✅ รหัสผ่านที่ถูกเข้ารหัสแล้ว:")
print(hashed_passwords)
