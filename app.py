import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Sustav narudžbi", layout="wide")

SUPABASE_URL = "https://vwekjvazuexwoglxqrtg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3ZWtqdmF6dWV4d29nbHhxcnRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMzMyOTcsImV4cCI6MjA4NzYwOTI5N30.59dWvEsXOE-IochSguKYSw_mDwFvEXHmHbCW7Gy_tto"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TZ = ZoneInfo("Europe/Zagreb")

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

    tab1, tab2 = st.tabs(["📋 Pregled i uređivanje", "➕ Nova narudžba"])

    with tab1:
        st.subheader("Sve narudžbe")

        if st.button("🔄 Osvježi tablicu"):
            st.rerun()

        response = supabase.table("main_orders").select("*").order("datum", desc=True).execute()
        df = pd.DataFrame(response.data or [])

        if not df.empty:
            df = df.fillna("")
            df.insert(0, "🗑️ Za brisanje", False)

            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                height=850,
                column_config={
                    "🗑️ Za brisanje": st.column_config.CheckboxColumn("🗑️", width=60),
                    "oznaci_za_narudzbu": st.column_config.CheckboxColumn("Za narudžbu", width=100),
                    "oznaci_zaprimljeno": st.column_config.CheckboxColumn("Zaprimljeno", width=100),
                }
            )

            col_a, col_b = st.columns([1, 4])
            if col_a.button("💾 Spremi promjene", type="primary"):
                allowed = [
                    "id", "datum", "korisnik", "reprezentacija", "odgovorna_osoba",
                    "sifra_proizvoda", "naziv_proizvoda", "kolicina", "dobavljac",
                    "oznaci_za_narudzbu", "broj_narudzbe", "oznaci_zaprimljeno",
                    "napomena_dobavljac", "napomena_za_nas", "unio_korisnik",
                    "datum_vrijeme_narudzbe", "datum_vrijeme_zaprimanja"
                ]
                records = edited_df[allowed].copy()

                records = records.where(pd.notnull(records), None)
                records = records.to_dict(orient="records")

                try:
                    supabase.table("main_orders").upsert(records, on_conflict="id").execute()
                    st.success("✅ Promjene spremljene!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Greška pri spremanju: {e}")

            if col_b.button("🗑️ Obriši označene redove", type="secondary"):
                to_delete = edited_df[edited_df["🗑️ Za brisanje"] == True]
                if not to_delete.empty:
                    for rid in to_delete["id"].tolist():
                        supabase.table("main_orders").delete().eq("id", rid).execute()
                    st.success(f"Obrisano {len(to_delete)} redova!")
                    st.rerun()
                else:
                    st.warning("Nisi označio nijedan red.")

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
                    "datum_vrijeme_narudzbe": datetime.now(TZ).isoformat(),
                }
                supabase.table("main_orders").insert(new_row).execute()
                st.success("Narudžba dodana! ✅")
                st.rerun()