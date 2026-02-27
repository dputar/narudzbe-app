import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo

# ────────────────────────────────────────────────
#  CONFIG
# ────────────────────────────────────────────────

st.set_page_config(page_title="Sustav narudžbi", layout="wide")

SUPABASE_URL = "https://vwekjvazuexwoglxqrtg.supabase.co"
SUPABASE_KEY = "TVOJ_SUPABASE_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TZ = ZoneInfo("Europe/Zagreb")

# ────────────────────────────────────────────────
#  SESSION STATE
# ────────────────────────────────────────────────

if "narudzbe_proizvodi" not in st.session_state:
    st.session_state.narudzbe_proizvodi = []

if "stranica" not in st.session_state:
    st.session_state.stranica = "pregled"

if "user" not in st.session_state:
    st.session_state.user = None

if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ────────────────────────────────────────────────
#  LOGIN
# ────────────────────────────────────────────────

if st.session_state.user is None:

    st.title("Prijava u sustav narudžbi")
    tab1, tab2 = st.tabs(["Prijava", "Registracija"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Lozinka", type="password", key="login_password")

        if st.button("Prijavi se"):
            try:
                res = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error(f"Greška: {e}")

    with tab2:
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Lozinka", type="password", key="reg_password")

        if st.button("Registriraj se"):
            try:
                supabase.auth.sign_up(
                    {"email": email, "password": password}
                )
                st.success("Registracija uspješna – prijavi se.")
            except Exception as e:
                st.error(f"Greška: {e}")

# ────────────────────────────────────────────────
#  APP
# ────────────────────────────────────────────────

else:

    # SIDEBAR
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

    # ────────────────────────────────────────────────
    #  PREGLED
    # ────────────────────────────────────────────────

    if st.session_state.stranica == "pregled":

        st.title("Pregled narudžbi")

        if st.button("🔄 Osvježi"):
            st.rerun()

        response = supabase.table("main_orders") \
            .select("*") \
            .order("datum_vrijeme_narudzbe", desc=True) \
            .execute()

        df = pd.DataFrame(response.data or [])

        if not df.empty:

            df = df.fillna("")
            df = df.loc[:, ~df.columns.duplicated()]

            columns_to_hide = [
                "created_at",
                "updated_at",
                "user_id"
            ]

            columns_to_show = [
                c for c in df.columns if c not in columns_to_hide
            ]

            st.dataframe(
                df[columns_to_show],
                use_container_width=True,
                height=700
            )
        else:
            st.info("Još nema narudžbi.")

    # ────────────────────────────────────────────────
    #  NOVA NARUDŽBA
    # ────────────────────────────────────────────────

    elif st.session_state.stranica == "nova":

        st.title("Nova narudžba")

        col_l, col_d = st.columns([1, 2])

        with col_l:

            korisnik = st.text_input("Korisnik")
            skladiste = st.text_input("Skladište")
            tip_klijenta = st.selectbox(
                "Tip klijenta",
                ["Doznaka", "Narudžba", "Uzorak", "Reprezentacija"]
            )
            klijent = st.text_input("Klijent")
            odgovorna = st.text_input("Odgovorna osoba")
            datum = st.date_input("Datum", datetime.today())
            napomena = st.text_area("Napomena")

        with col_d:

            st.subheader("Proizvodi")

            if st.session_state.narudzbe_proizvodi:

                df = pd.DataFrame(
                    st.session_state.narudzbe_proizvodi
                )

                df["Ukupno"] = df["Kol."] * df["Cijena"]

                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )

                ukupno = df["Ukupno"].sum()
                st.markdown(
                    f"### UKUPNO: {ukupno:,.2f} EUR + PDV"
                )
            else:
                st.info("Još nema proizvoda.")

            # Gumb za prikaz forme
            if st.button("➕ Dodaj proizvod"):
                st.session_state.show_form = True

            # Forma
            if st.session_state.show_form:

                with st.form("dodaj_proizvod", clear_on_submit=True):

                    sifra = st.text_input("Šifra")
                    naziv = st.text_input("Naziv proizvoda *")

                    col1, col2 = st.columns(2)

                    kol = col1.number_input(
                        "Količina *",
                        min_value=0.01,
                        step=0.01
                    )

                    cijena = col2.number_input(
                        "Cijena po komadu",
                        min_value=0.0,
                        step=0.01
                    )

                    dobavljac = st.text_input("Dobavljač")

                    submitted = st.form_submit_button(
                        "Dodaj u narudžbu"
                    )

                    if submitted:

                        if naziv and kol > 0:

                            st.session_state.narudzbe_proizvodi.append({
                                "Šifra": sifra,
                                "Naziv": naziv,
                                "Kol.": kol,
                                "Cijena": cijena,
                                "Dobavljač": dobavljac
                            })

                            st.session_state.show_form = False
                            st.rerun()
                        else:
                            st.error(
                                "Naziv i količina su obavezni!"
                            )

        # ─────────────────────────────────────
        #  SPREMI NARUDŽBU
        # ─────────────────────────────────────

        if st.session_state.narudzbe_proizvodi:

            col1, col2 = st.columns(2)

            if col1.button("Odustani"):
                st.session_state.narudzbe_proizvodi = []
                st.session_state.stranica = "pregled"
                st.rerun()

            if col2.button("Spremi narudžbu"):

                for proizvod in st.session_state.narudzbe_proizvodi:

                    red = {
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
                        "datum_vrijeme_narudzbe": datetime.now(TZ).isoformat()
                    }

                    supabase.table("main_orders") \
                        .insert(red) \
                        .execute()

                st.success("Narudžba uspješno spremljena!")
                st.session_state.narudzbe_proizvodi = []
                st.session_state.stranica = "pregled"
                st.rerun()