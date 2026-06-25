import joblib
import streamlit as st
import pandas as pd

st.set_page_config(page_icon='🏠',page_title="House Price Prediction",layout='wide')
with open("Rf_model.joblib",'rb') as file:
    model=joblib.load(file)

df=pd.read_csv('cleaned_df.csv')

with st.sidebar:
    st.title("House Price Prediction App")
    st.image("house.jpg")

with st.container(border=True):
    col1,col2=st.columns(2)
    with col1:
        location=st.selectbox("location: ",options=df['location'].unique())
        sqft=st.number_input("sq.ft ",min_value=300)
    with col2:
        bath=st.selectbox("Bath ",options=sorted(df['bath'].unique()))
        bhk=st.selectbox("BHK's ",options=sorted(df['bhk'].unique()))

def get_encoded_loc(location):
    for loc,encoded in zip(df['location'],df['encoded_loc']):
        if location==loc:
            return encoded



encoded_loc=get_encoded_loc(location)

if st.button('predict'):
    inp_data=[[sqft,bath,bhk,encoded_loc]]
    pred=model.predict(inp_data)
    pred=float(f'{pred[0]:2f}')
    st.title(f"predicted price: Rs. {pred*100000}")