import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Sustav narudžbi", layout="wide")

SUPABASE_URL = "https://vwekjvazuexwoglxqrtg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3ZWtqdmF6dWV4d29nbHhxcnRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMzMyOTcsImV4cCI6MjA4NzYwOTI5N30.59dWvEsXOE-IochSguKYSw_mDwFvEXHmHbCW7Gy_tto"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TZ = ZoneInfo("Europe/Zagreb")

# ────────────────────────────────────────────────
#  SESSION STATE
# ────────────────────────────────────────────────

if "narudzbe_proizvodi" not in st.session_state:
    st.session_state.narudzbe_proizvodi = []

if "stranica" not in st.session_state:
    st.session_state.stranica = "pregled"

# ────────────────────────────────────────────────
#  LOGIN – jedinstveni key-evi
# ────────────────────────────────────────────────

if "user" not in st.session_state or st.session_state.user is None:
    st.title("Prijava u sustav narudžbi")
    tab1, tab2 = st.tabs(["Prijava", "Registracija"])

    with tab1:
        email = st.text_input("Email", key="login_email_input")
        password = st.text_input("Lozinka", type="password", key="login_password_input")
        if st.button("Prijavi se", key="login_prijavi_button"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.stranica = "pregled"
                st.rerun()
            except Exception as e:
                st.error(f"Greška: {e}")

    with tab2:
        email = st.text_input("Email", key="reg_email_input")
        password = st.text_input("Lozinka", type="password", key="reg_password_input")
        if st.button("Registriraj se", key="reg_registriraj_button"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registracija OK – prijavi se")
            except Exception as e:
                st.error(f"Greška: {e}")
else:
    # ────────────────────────────────────────────────
    #  SIDEBAR – jedinstveni key-evi
    # ────────────────────────────────────────────────

    st.sidebar.title("Navigacija")
    if st.sidebar.button("Pregled narudžbi", key="sidebar_pregled"):
        st.session_state.stranica = "pregled"
        st.rerun()
    if st.sidebar.button("Nova narudžba", key="sidebar_nova"):
        st.session_state.stranica = "nova"
        st.rerun()
    if st.sidebar.button("Odjavi se", key="sidebar_odjava"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.stranica = "login"
        st.rerun()

    # ────────────────────────────────────────────────
    #  PREGLED NARUDŽBI – čistimo duplicirane stupce i prikazujemo samo dataframe
    # ────────────────────────────────────────────────

    if st.session_state.stranica == "pregled":
        st.title("Pregled narudžbi")

        if st.button("🔄 Osvježi", key="pregled_osvjezi"):
            st.rerun()

        response = supabase.table("main_orders").select("*").order("datum", desc=True).execute()
        df = pd.DataFrame(response.data or [])

        if not df.empty:
            df = df.fillna("")

            # Čišćenje dupliciranih naziva stupaca (uzimamo samo prvi pojavljeni)
            df = df.loc[:, ~df.columns.duplicated()]

            # Preimenuj reprezentacija u Skladište
            if "reprezentacija" in df.columns:
                df = df.rename(columns={"reprezentacija": "Skladište"})

            # Ukloni nepotrebne stupce iz prikaza
            columns_to_show = [c for c in df.columns if c not in ["created_at", "updated_at", "user_id"]]

            # Ako i dalje ima dupliciranih stupaca – ručno čistimo
            df = df.loc[:, ~df.columns.duplicated(keep='first')]

            st.dataframe(
                df[columns_to_show],
                use_container_width=True,
                height=750
            )

            st.info("Za sada je pregled samo čitanje. Edit i brisanje dodajemo u sljedećem koraku.")
        else:
            st.info("Još nema narudžbi.")

    # ────────────────────────────────────────────────
    #  NOVA NARUDŽBA – po slici
    # ────────────────────────────────────────────────

    elif st.session_state.stranica == "nova":
        col_naslov, col_natrag = st.columns([5, 1])
        with col_naslov:
            st.title("Nova narudžba")

        with col_natrag:
            if st.button("← Natrag na pregled", key="nova_natrag"):
                st.session_state.narudzbe_proizvodi = []
                st.session_state.stranica = "pregled"
                st.rerun()

        col_lijevo, col_desno = st.columns([1, 2])

        with col_lijevo:
            st.markdown("**Korisnik**")
            korisnik = st.selectbox("", ["Daniel Putar"], key="nova_korisnik", label_visibility="collapsed")
            st.success(f"✓ {korisnik}")

            st.markdown("**Skladište**")
            skladiste = st.selectbox("", ["Osijek - Glavno skladište"], key="nova_skladiste", label_visibility="collapsed")
            st.success(f"✓ {skladiste}")

            st.markdown("**Tip klijenta**")
            tip_klijenta = st.selectbox("", ["Doznaka", "Narudžba", "Uzorak", "Reprezentacija"], key="nova_tip_klijenta", label_visibility="collapsed")
            if tip_klijenta:
                st.success(f"✓ {tip_klijenta}")
            else:
                st.error("× Tip klijenta")

            st.markdown("**Klijent**")
            klijent = st.text_input("", placeholder="Upiši ime", key="nova_klijent", label_visibility="collapsed")
            if klijent:
                st.success(f"✓ {klijent}")
            else:
                st.error("× Klijent")

            st.markdown("**Odgovorna osoba**")
            odgovorna_lista = ["Nema", "Daniel Putar", "Druga osoba"]
            odgovorna = st.selectbox("", odgovorna_lista, key="nova_odgovorna_select", label_visibility="collapsed")
            if odgovorna == "Nema":
                odgovorna = st.text_input("Slobodan unos odgovorne osobe", key="nova_odgovorna_slobodno")
            st.success(f"✓ {odgovorna}")

            st.markdown("**Datum**")
            datum = st.date_input("", datetime.today(), key="nova_datum", label_visibility="collapsed")

            st.markdown("**Napomena**")
            napomena = st.text_area("", height=100, key="nova_napomena", label_visibility="collapsed")

        with col_desno:
            st.markdown("**Proizvodi**")

            if st.session_state.narudzbe_proizvodi:
                df = pd.DataFrame(st.session_state.narudzbe_proizvodi)
                df["Ukupno"] = df["Kol."] * df["Cijena"]
                st.dataframe(df, use_container_width=True, height=400)
                ukupno = df["Ukupno"].sum()
                st.markdown(f"**UKUPNO: {ukupno:,.2f} EUR + PDV**")
            else:
                st.info("Još nema proizvoda.")

            if st.button("➕ Dodaj proizvod", key="nova_dodaj_gumb", type="primary"):
                with st.form("dodaj_proizvod", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    sifra = col1.text_input("Šifra", key="dodaj_sifra")
                    naziv = col2.text_input("Naziv proizvoda *", key="dodaj_naziv")

                    col3, col4 = st.columns(2)
                    kol = col3.number_input("Količina *", min_value=0.01, step=0.01, format="%.2f", key="dodaj_kol")
                    cijena = col4.number_input("Cijena po komadu", min_value=0.0, step=0.01, format="%.2f", key="dodaj_cijena")

                    dobavljac = st.text_input("Dobavljač", key="dodaj_dobavljac")

                    col_g, col_x = st.columns([1, 1])
                    if col_g.button("Dodaj u narudžbu", key="dodaj_spremi"):
                        if naziv and kol > 0:
                            novi = {
                                "Šifra": sifra,
                                "Naziv": naziv,
                                "Kol.": kol,
                                "Cijena": cijena,
                                "Ukupno": kol * cijena,
                                "Dobavljač": dobavljac
                            }
                            st.session_state.narudzbe_proizvodi.append(novi)
                            st.rerun()
                        else:
                            st.error("Naziv i količina su obavezni!")

                    if col_x.button("Odustani", key="dodaj_odustani"):
                        st.session_state.show_dodaj_proizvod = False
                        st.rerun()

    # ────────────────────────────────────────────────
    #  SPREMI NARUDŽBU – svaki proizvod zaseban red
    # ────────────────────────────────────────────────

    if st.session_state.stranica == "nova" and st.session_state.narudzbe_proizvodi:
        col1, col2 = st.columns(2)
        if col1.button("Odustani", type="secondary"):
            st.session_state.narudzbe_proizvodi = []
            st.session_state.stranica = "pregled"
            st.rerun()

        if col2.button("Spremi narudžbu", type="primary"):
            for proizvod in st.session_state.narudzbe_proizvodi:
                red = {
                    "datum": str(datum),
                    "korisnik": klijent or korisnik,
                    "Skladište": skladiste,
                    "tip_klijenta": tip_klijenta,
                    "odgovorna_osoba": odgovorna,
                    "sifra_proizvoda": proizvod["Šifra"],
                    "naziv_proizvoda": proizvod["Naziv"],
                    "kolicina": proizvod["Kol."],
                    "dobavljac": proizvod["Dobavljač"],
                    "cijena": proizvod["Ukupno"],
                    "napomena_za_nas": napomena,
                    "unio_korisnik": st.session_state.user.email,
                    "datum_vrijeme_narudzbe": datetime.now(TZ).isoformat(),
                }
                supabase.table("main_orders").insert(red).execute()

            st.success("Narudžba spremljena! Svi proizvodi su zasebni redovi.")
            st.session_state.narudzbe_proizvodi = []
            st.session_state.stranica = "pregled"
            st.rerun()