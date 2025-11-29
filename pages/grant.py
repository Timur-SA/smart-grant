import streamlit as st
from SCvalidators.PMvalidator import validate_payments, handlePayments, qr2json
from SChandler import readSC, saveSC
from SCvalidators.BillValidator import extract_receipt_data_from_image, fetch_receipt
import json


def format_currency(amount):
    """Форматирует сумму в читаемый формат с пробелами"""
    return f"{amount:,} ₽".replace(",", " ")

def display_sc_info(data):
    """
    Отображает информацию о смарт-контракте в структурированном виде
    
    Args:
        data: dict - JSON-структура смарт-контракта
    """
    # Метаданные гранта
    st.markdown(f"**Общий бюджет:** {format_currency(data['grant_metadata']['total_budget'])}")
    st.markdown(f"**Период:** {data['grant_metadata']['start_date']} — {data['grant_metadata']['end_date']} ({data['grant_metadata']['duration_months']} мес.)")
    st.divider()

    # Этапы
    for stage in data['stages']:
        st.subheader(f"{stage['stage_name']}")
        st.markdown(f"**Бюджет этапа:** {format_currency(stage['stage_budget'])} | **Сроки:** {stage['start_date']} — {stage['end_date']} ({stage['duration_months']} мес.)")
        
        # Правила трат
        for rule in stage['spending_rules']:
            st.markdown(f"**{rule['rule_name']}**")
            st.markdown(f"Лимит: {format_currency(rule['limit'])}")
            
            # Категории (если есть)
            if 'allowed_categories' in rule and rule['allowed_categories']:
                if isinstance(rule['allowed_categories'][0], dict):
                    categories = [cat['category'] for cat in rule['allowed_categories']]
                else:
                    categories = rule['allowed_categories']
                st.markdown("- " + "\n- ".join(categories))
            
            st.write("")  # Небольшой отступ
        
        st.divider()

st.set_page_config(page_title="МойГрант", page_icon="💰")
grant_name = st.query_params["id"]


st.title("МойГрант")
st.write("онлайн-сервис управления грантами")
st.divider()

st.subheader(f"Грант: {grant_name}")
st.write(f"Баланс: {readSC(grant_name)["grant_metadata"]["total_budget"]} ₽")
st.divider()

st.subheader("Подтверждение оплаты")
bill_photo = st.file_uploader("Загрузка чека", 
    type=["jpg"], 
    help="Загрузите фотографию чека с расширением JPG"
)
if(st.button("Подтвердить")):
    bill_data = extract_receipt_data_from_image(bill_photo)
    succes, _ = fetch_receipt(bill_data)

    if(succes): st.success("Ваш чек принят!")
    else: st.warning("Ваш чек не найден в базе ФНС!")
st.divider()

st.subheader(f"Оплата средствами гранта")

payment_req = st.file_uploader("Реквизиты", 
    type=["jpg", "png", "jpeg"], 
    help="Загрузите реквизиты для оплаты"
)


if(st.button("Оплатить")):
    if(payment_req):
        payment_report = validate_payments(readSC(grant_name), json.loads(qr2json(payment_req)))
        if(payment_report["errors"]): 
            for error in payment_report["errors"]: st.write(error)
        else: 
            st.success("Оплачено!")
            saveSC(grant_name, handlePayments(readSC(grant_name), payment_report))
            st.rerun()
    else: st.error("Перевод не распознан")


st.divider()
st.subheader("Подобрная информация смартконтракта")
display_sc_info(readSC(grant_name))