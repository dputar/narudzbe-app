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
#  LOGIN
# ────────────────────────────────────────────────

if "user" not in st.session_state or st.session_state.user is None:
    st.title("Prijava u sustav narudžbi")
    tab1, tab2 = st.tabs(["Prijava", "Registracija"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.stranica = "pregled"
                st.rerun()
            except Exception as e:
                st.error(f"Greška: {e}")

    with tab2:
        email = st.text_input("Email")
        password = st.text_input("Lozinka", type="password")
        if st.button("Registriraj se"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registracija OK – prijavi se")
            except Exception as e:
                st.error(f"Greška: {e}")
else:
    # ────────────────────────────────────────────────
    #  SIDEBAR
    # ────────────────────────────────────────────────

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
        st.session_state.stranica = "login"
        st.rerun()

    # ────────────────────────────────────────────────
    #  PREGLED NARUDŽBI
    # ────────────────────────────────────────────────

    if st.session_state.stranica == "pregled":
        st.title("Pregled narudžbi")

        if st.button("🔄 Osvježi"):
            st.rerun()

        response = supabase.table("main_orders").select("*").order("datum", desc=True).execute()
        df = pd.DataFrame(response.data or [])

        if not df.empty:
            df = df.fillna("")
            df.insert(0, "🗑️", False)

            # Preimenuj reprezentacija u Skladište
            if "reprezentacija" in df.columns:
                df = df.rename(columns={"reprezentacija": "Skladište"})

            # Ukloni nepotrebne stupce iz prikaza
            columns_to_show = [c for c in df.columns if c not in ["created_at", "updated_at", "user_id"]]

            edited_df = st.data_editor(
                df[columns_to_show],
                hide_index=True,
                use_container_width=True,
                height=750,
                column_config={
                    "🗑️": st.column_config.CheckboxColumn("🗑️", width=60),
                    "oznaci_za_narudzbu": st.column_config.CheckboxColumn("Za narudžbu", width=100),
                    "oznaci_zaprimljeno": st.column_config.CheckboxColumn("Zaprimljeno", width=100),
                }
            )

            col_a, col_b = st.columns([1, 4])
            if col_a.button("💾 Spremi promjene", type="primary"):
                # Samo dozvoljeni stupci
                allowed = [
                    "id", "datum", "korisnik", "Skladište", "odgovorna_osoba",
                    "sifra_proizvoda", "naziv_proizvoda", "kolicina", "dobavljac",
                    "oznaci_za_narudzbu", "broj_narudzbe", "oznaci_zaprimljeno",
                    "napomena_dobavljac", "napomena_za_nas", "unio_korisnik",
                    "datum_vrijeme_narudzbe", "datum_vrijeme_zaprimanja", "cijena"
                ]
                records = edited_df[allowed].copy()
                records = records.where(pd.notnull(records), None)
                records = records.to_dict(orient="records")

                try:
                    supabase.table("main_orders").upsert(records, on_conflict="id").execute()
                    st.success("Promjene spremljene!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Greška pri spremanju: {e}")

            if col_b.button("🗑️ Obriši označene"):
                to_delete = edited_df[edited_df["🗑️"] == True]
                if not to_delete.empty:
                    for rid in to_delete["id"].tolist():
                        supabase.table("main_orders").delete().eq("id", rid).execute()
                    st.success("Obrisano!")
                    st.rerun()
                else:
                    st.warning("Nisi označio nijedan red.")
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
            if st.button("← Natrag na pregled"):
                st.session_state.narudzbe_proizvodi = []
                st.session_state.stranica = "pregled"
                st.rerun()

        col_lijevo, col_desno = st.columns([1, 2])

        with col_lijevo:
            st.markdown("**Korisnik**")
            korisnik = st.selectbox("", ["Daniel Putar"], label_visibility="collapsed")
            st.success(f"✓ {korisnik}")

            st.markdown("**Skladište**")
            skladiste = st.selectbox("", ["Osijek - Glavno skladište"], label_visibility="collapsed")
            st.success(f"✓ {skladiste}")

            st.markdown("**Tip klijenta**")
            tip_klijenta = st.selectbox("", ["Doznaka", "Narudžba", "Uzorak", "Reprezentacija"], label_visibility="collapsed")
            if tip_klijenta:
                st.success(f"✓ {tip_klijenta}")
            else:
                st.error("× Tip klijenta")

            st.markdown("**Klijent**")
            klijent = st.text_input("", placeholder="Upiši ime", label_visibility="collapsed")
            if klijent:
                st.success(f"✓ {klijent}")
            else:
                st.error("× Klijent")

            st.markdown("**Odgovorna osoba**")
            odgovorna_lista = ["Nema", "Daniel Putar", "Druga osoba"]
            odgovorna = st.selectbox("", odgovorna_lista, label_visibility="collapsed")
            if odgovorna == "Nema":
                odgovorna = st.text_input("Slobodan unos odgovorne osobe", "")
            st.success(f"✓ {odgovorna}")

            st.markdown("**Datum**")
            datum = st.date_input("", datetime.today(), label_visibility="collapsed")

            st.markdown("**Napomena**")
            napomena = st.text_area("", height=100, label_visibility="collapsed")

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

            if st.button("➕ Dodaj proizvod", type="primary"):
                with st.form("dodaj_proizvod", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    sifra = col1.text_input("Šifra")
                    naziv = col2.text_input("Naziv proizvoda *")

                    col3, col4 = st.columns(2)
                    kol = col3.number_input("Količina *", min_value=0.01, step=0.01, format="%.2f")
                    cijena = col4.number_input("Cijena po komadu", min_value=0.0, step=0.01, format="%.2f")

                    dobavljac = st.text_input("Dobavljač")

                    submitted = st.form_submit_button("Dodaj u narudžbu")
                    if submitted:
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