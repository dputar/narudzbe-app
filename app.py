import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="Sustav narudžbi", layout="wide")

SUPABASE_URL = "https://vwekjvazuexwoglxqrtg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3ZWtqdmF6dWV4d29nbHhxcnRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMzMyOTcsImV4cCI6MjA4NzYwOTI5N30.59dWvEsXOE-IochSguKYSw_mDwFvEXHmHbCW7Gy_tto"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🛒 Prijava u sustav narudžbi")
    tab1, tab2 = st.tabs(["Prijava", "Registracija"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Lozinka", type="password", key="login_pass")
        if st.button("Prijavi se", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Prijava uspješna!")
                st.rerun()
            except Exception as e:
                st.error(f"Greška: {e}")
    with tab2:
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Lozinka", type="password", key="reg_pass")
        if st.button("Registriraj se", type="primary"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registracija uspješna!")
            except Exception as e:
                st.error(f"Greška: {e}")
else:
    st.sidebar.success(f"👤 {st.session_state.user.email} (Admin)")

    if st.sidebar.button("Odjavi se"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🛒 Sustav narudžbi")

    tab1, tab2 = st.tabs(["📋 Pregled narudžbi", "➕ Nova narudžba"])

    with tab1:
        st.subheader("Sve narudžbe")
        response = supabase.table("main_orders").select("*").order("datum", desc=True).execute()
        df = pd.DataFrame(response.data or [])

        if not df.empty:
            # Format za prikaz (da se ne mora scrollati previše)
            for col in ["datum", "datum_vrijeme_narudzbe", "datum_vrijeme_zaprimanja"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d.%m.%y %H:%M')

            st.dataframe(df, use_container_width=True, height=750)

            st.info("Za sada možete dodavati nove narudžbe u drugom tabu. Edit kvačica i brisanje dodajemo u sljedećoj verziji.")

        else:
            st.info("Još nema narudžbi.")

    with tab2:
        st.subheader("Nova narudžba")
        with st.form("new_order_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            datum = col1.date_input("Datum", datetime.today())
            korisnik = col2.text_input("Korisnik (za koga ide narudžba)")
            reprezentacija = col3.text_input("Reprezentacija / Skladište")

            col4, col5 = st.columns(2)
            odgovorna_osoba = col4.text_input("Odgovorna osoba")
            sifra_proizvoda = col5.text_input("Šifra proizvoda")

            naziv_proizvoda = st.text_input("Naziv proizvoda")
            kolicina = st.number_input("Količina", min_value=0.0, step=0.01, format="%.2f")
            dobavljac = st.text_input("Dobavljač")

            col6, col7 = st.columns(2)
            oznaci_za_narudzbu = col6.checkbox("Označi za narudžbu")
            broj_narudzbe = col7.text_input("Broj narudžbe")

            napomena_dobavljac = st.text_area("Napomena koju vidi dobavljač")
            napomena_za_nas = st.text_area("Napomena za nas (interna)")

            submitted = st.form_submit_button("➕ Dodaj narudžbu")
            if submitted:
                new_row = {
                    "datum": str(datum),
                    "korisnik": korisnik,
                    "reprezentacija": reprezentacija,
                    "odgovorna_osoba": odgovorna_osoba,
                    "sifra_proizvoda": sifra_proizvoda,
                    "naziv_proizvoda": naziv_proizvoda,
                    "kolicina": kolicina,
                    "dobavljac": dobavljac,
                    "oznaci_za_narudzbu": oznaci_za_narudzbu,
                    "broj_narudzbe": broj_narudzbe,
                    "napomena_dobavljac": napomena_dobavljac,
                    "napomena_za_nas": napomena_za_nas,
                    "unio_korisnik": st.session_state.user.email,
                    "datum_vrijeme_narudzbe": datetime.now().isoformat(),
                }
                supabase.table("main_orders").insert(new_row).execute()
                st.success("Narudžba dodana! ✅")
                st.rerun()