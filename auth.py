
.import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def login():
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )

    name, authentication_status, username = authenticator.login('main')

    if authentication_status:
        authenticator.logout('Logout', 'main')
        st.write(f'Welcome *{name}* 👋')
        return True
    elif authentication_status is False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status is None:
        st.warning('Please enter your username and password')
        return False
