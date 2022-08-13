import streamlit as st

def app():
    st.title('Welcome to your FPL helper')
    st.markdown("I have created this web App to help with your FPL team selection and " +
                "to provide you with your team's progress.")
    st.subheader('You can use this App to:')
    st.markdown(''' 
    - View data for different teams
    - View player data
    - View your own team's progress and ranking
    ''')
    st.header('Created by Joshua Johnstone')
    st.markdown('Should you come across any errors or have any questions, please email myself at joshhjohnstone@gmail.com.')

