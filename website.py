import streamlit as st
from SChandler import getSCs

grants = getSCs()

def main():
    st.set_page_config(page_title="МойГрант", page_icon="💰")

    st.title("МойГрант")
    st.write("онлайн-сервис управления грантами")
    st.divider()

    with st.sidebar:
        st.header("Профиль")
        stage = st.selectbox("Роль:", ["Грантодатель", "Исполнитель"])

    if(stage=="Грантодатель"): grantmaker()
    else: executor(); 

def grantmaker():
    st.subheader("Список созданных вами грантов:")
    grants = getSCs()

    if(not grants): st.write("Вы ещё не создавали гранты")
    for _grant in grants: st.write(f"- {_grant}")

    if(st.button("Создать грант")): st.switch_page("pages/newgrant.py")

def executor():
    st.subheader("Список полученных вами грантов:")
    grants = getSCs()
    
    if(not grants): st.write("У вас ещё нет грантов")
    for _grant in grants: st.markdown(f'- <a href="/grant?id={_grant}">{_grant}</a>', unsafe_allow_html=True)