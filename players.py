import pandas as pd
import streamlit as st
import requests
from understatapi import UnderstatClient
import datetime
import seaborn as sns
import matplotlib

understat = UnderstatClient()

def app():
    st.title('Player Data')
    st.markdown('Sorry, this page is still being built. Please come check again later.')