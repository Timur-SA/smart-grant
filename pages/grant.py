import streamlit as st
from SCvalidators.PMvalidator import validate_payments, handlePayments 
from SChandler import readSC, saveSC
import json

st.set_page_config(page_title="МойГрант", page_icon="💰")
grant_name = st.query_params["id"]


st.title("МойГрант")
st.write("онлайн-сервис управления грантами")
st.divider()

st.subheader(f"Грант: {grant_name}")
st.divider()

st.subheader("Подтверждение оплаты")
bill_photo = st.file_uploader("Загрузка чека", 
    type=["jpg"], 
    help="Загрузите фотографию чека с расширением JPG"
)
st.divider()

st.subheader(f"Оплата средствами гранта")

payment_req = st.file_uploader("Реквизиты", 
    type=["json"], 
    help="Загрузите реквизиты для оплаты"
)

if(st.button("Оплатить")):
    payment_report = validate_payments(readSC(grant_name), json.load(payment_req))
    if(payment_report["errors"]): 
        for error in payment_report["errors"]: st.write(error)
    else: 
        st.success("Оплачено!")
        saveSC(grant_name, handlePayments(readSC(grant_name), payment_report))