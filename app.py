import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────

st.set_page_config(page_title="Sustav narudžbi", layout="wide")

SUPABASE_URL = "https://vwekjvazuexwoglxqrtg.supabase.co"
SUPABASE_KEY = "TVOJ_SUPABASE_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TZ = ZoneInfo("Europe/Zagreb")

# ────────────────────────────────────────────────
# SESSION
# ────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None

if "stranica" not in st.session_state:
    st.session_state.stranica = "pregled"

if "narudzbe_proizvodi" not in st.session_state:
    st.session_state.narudzbe_proizvodi = []

# ────────────────────────────────────────────────
# LOGIN
# ────────────────────────────────────────────────

if st.session_state.user is None:

    st.title("Prijava")

    email = st.text_input("Email")
    password = st.text_input("Lozinka", type="password")

    if st.button("Prijavi se"):
        try:
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error(f"Greška: {e}")

# ────────────────────────────────────────────────
# APP
# ────────────────────────────────────────────────

else:

    st.sidebar.title("Navigacija")

    if st.sidebar.button("Pregled narudžbi"):
        st.session_state.stranica = "pregled"
        st.rerun()

    if st.sidebar.button("Nova narudžba"):
        st.session_state.stranica = "nova"
        st.rerun()

    if st.sidebar.button("Odjavi se"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # ────────────────────────────────────────────
    # PREGLED
    # ────────────────────────────────────────────

    if st.session_state.stranica == "pregled":

        st.title("Pregled narudžbi")

        try:
            response = supabase.table("main_orders").select("*").execute()
            df = pd.DataFrame(response.data or [])
        except Exception as e:
            st.error(f"Greška baze: {e}")
            st.stop()

        if not df.empty:

            df = df.loc[:, ~df.columns.duplicated()]
            df = df.fillna("")

            # FILTER
            st.subheader("Filter")

            filter_klijent = st.text_input("Filtriraj po klijentu")

            if filter_klijent:
                df = df[df["klijent"].astype(str).str.contains(filter_klijent, case=False)]

            # DELETE
            st.subheader("Briši narudžbu po order_id")

            delete_id = st.text_input("Upiši order_id za brisanje")

            if st.button("Obriši"):
                supabase.table("main_orders") \
                    .delete() \
                    .eq("order_id", delete_id) \
                    .execute()
                st.success("Obrisano")
                st.rerun()

            st.dataframe(df, use_container_width=True, height=600)

            # EXPORT
            st.download_button(
                "Preuzmi Excel",
                df.to_csv(index=False).encode("utf-8"),
                "narudzbe.csv",
                "text/csv"
            )

        else:
            st.info("Nema podataka.")

    # ────────────────────────────────────────────
    # NOVA NARUDŽBA
    # ────────────────────────────────────────────

    if st.session_state.stranica == "nova":

        st.title("Nova narudžba")

        korisnik = st.text_input("Korisnik")
        skladiste = st.text_input("Skladište")
        tip_klijenta = st.selectbox(
            "Tip klijenta",
            ["Doznaka", "Narudžba", "Uzorak", "Reprezentacija"]
        )
        klijent = st.text_input("Klijent")
        odgovorna = st.text_input("Odgovorna osoba")
        datum = st.date_input("Datum")
        napomena = st.text_area("Napomena")

        st.subheader("Proizvodi")

        with st.form("dodaj_proizvod", clear_on_submit=True):

            sifra = st.text_input("Šifra")
            naziv = st.text_input("Naziv proizvoda")
            kol = st.number_input("Količina", min_value=0.01)
            cijena = st.number_input("Cijena", min_value=0.0)
            dobavljac = st.text_input("Dobavljač")

            if st.form_submit_button("Dodaj proizvod"):

                st.session_state.narudzbe_proizvodi.append({
                    "Šifra": sifra,
                    "Naziv": naziv,
                    "Kol.": kol,
                    "Cijena": cijena,
                    "Dobavljač": dobavljac
                })

                st.rerun()

        if st.session_state.narudzbe_proizvodi:

            df = pd.DataFrame(st.session_state.narudzbe_proizvodi)
            df["Ukupno"] = df["Kol."] * df["Cijena"]

            st.dataframe(df, use_container_width=True)

            if st.button("Spremi narudžbu"):

                order_id = str(uuid.uuid4())

                for proizvod in st.session_state.narudzbe_proizvodi:

                    red = {
                        "order_id": order_id,
                        "datum": str(datum),
                        "korisnik": korisnik,
                        "skladiste": skladiste,
                        "tip_klijenta": tip_klijenta,
                        "klijent": klijent,
                        "odgovorna_osoba": odgovorna,
                        "sifra_proizvoda": proizvod["Šifra"],
                        "naziv_proizvoda": proizvod["Naziv"],
                        "kolicina": proizvod["Kol."],
                        "cijena": proizvod["Cijena"],
                        "ukupno": proizvod["Kol."] * proizvod["Cijena"],
                        "dobavljac": proizvod["Dobavljač"],
                        "napomena": napomena,
                        "unio_korisnik": st.session_state.user.email,
                        "created_at": datetime.now(TZ).isoformat()
                    }

                    supabase.table("main_orders").insert(red).execute()

                st.success(f"Narudžba spremljena! ID: {order_id}")
                st.session_state.narudzbe_proizvodi = []
                st.rerun()