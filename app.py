import streamlit as st
import home
import teams
import players
import my_team
import vml
import aas
import seaborn
import matplotlib
import pandas
import numpy
import requests
import datetime
from understatapi import UnderstatClient


pages = {'Home': home, 'Team Data': teams, 'Player Data': players, 'My Team': my_team,
         'Victor Moses Lawn': vml, 'Team AAweSome 2022': aas}

# Add sidebar to to app

st.sidebar.markdown('### FPL App')
st.sidebar.markdown('Navigate through the App using this side bar')
selection = st.sidebar.radio('Go to', list(pages.keys()))
page = pages[selection]
page.app()




