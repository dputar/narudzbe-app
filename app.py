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

# ────────────────────────────────────────────────
#  GLAVNA STRANICA – Nova narudžba
# ────────────────────────────────────────────────

col_naslov, col_natrag = st.columns([5, 1])
with col_naslov:
    st.title("Nova narudžba")

with col_natrag:
    if st.button("← Natrag na pregled"):
        st.session_state.narudzbe_proizvodi = []
        st.rerun()

# ────────────────────────────────────────────────
#  LIJEVI DIO – podaci o narudžbi
# ────────────────────────────────────────────────

col_lijevo, col_desno = st.columns([1, 2])

with col_lijevo:
    st.markdown("**Korisnik**")
    korisnik = st.selectbox("", ["Daniel Putar"], label_visibility="collapsed")
    st.success(f"✓ {korisnik}")

    st.markdown("**Skladište**")
    skladiste = st.selectbox("", ["Osijek - Glavno skladište"], label_visibility="collapsed")
    st.success(f"✓ {skladiste}")

    st.markdown("**Tip klijenta**")
    tip_klijenta = st.selectbox("", ["", "Doznaka", "Narudžba", "Uzorak"], label_visibility="collapsed")
    if tip_klijenta:
        st.success(f"✓ {tip_klijenta}")
    else:
        st.error("× Tip klijenta")

    st.markdown("**Klijent**")
    klijent = st.text_input("", placeholder="Upiši ime ili odaberi iz padajućeg", label_visibility="collapsed")
    if klijent:
        st.success(f"✓ {klijent}")
    else:
        st.error("× Klijent")

    st.markdown("**Odgovorna osoba**")
    odgovorna = st.selectbox("", ["Nema"], label_visibility="collapsed")
    st.success(f"✓ {odgovorna}")

    st.markdown("**Datum kada je odobren nalog**")
    datum = st.date_input("", datetime.today(), label_visibility="collapsed")

    st.markdown("**Napomena**")
    napomena = st.text_area("", height=100, label_visibility="collapsed")

# ────────────────────────────────────────────────
#  DESNI DIO – tablica proizvoda + dodavanje
# ────────────────────────────────────────────────

with col_desno:
    st.markdown("**Proizvodi**")

    if st.session_state.narudzbe_proizvodi:
        df = pd.DataFrame(st.session_state.narudzbe_proizvodi)
        df["Ukupno"] = df["Kol."] * df["Cijena"]

        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Šifra": st.column_config.TextColumn("Šifra"),
                "Naziv": st.column_config.TextColumn("Naziv"),
                "Kol.": st.column_config.NumberColumn("Kol.", min_value=0.01, step=0.01),
                "Cijena": st.column_config.NumberColumn("Cijena", format="%.2f"),
                "Ukupno": st.column_config.NumberColumn("Ukupno", format="%.2f", disabled=True),
                "Dobavljač": st.column_config.TextColumn("Dobavljač"),
            }
        )

        ukupno = edited["Ukupno"].sum()
        st.markdown(f"**UKUPNO: {ukupno:,.2f} EUR + PDV**")
    else:
        st.info("Još nema proizvoda.")

    if st.button("➕ Dodaj proizvod", type="primary"):
        with st.form("dodaj_proizvod_form", clear_on_submit=True):
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
#  DONJI GUMBI – Spremi / Odustani
# ────────────────────────────────────────────────

col1, col2 = st.columns(2)
if col1.button("Odustani", type="secondary"):
    st.session_state.narudzbe_proizvodi = []
    st.rerun()

if col2.button("Spremi narudžbu", type="primary"):
    if not st.session_state.narudzbe_proizvodi:
        st.warning("Dodaj barem jedan proizvod!")
    else:
        with st.spinner("Spremanje narudžbe..."):
            for proizvod in st.session_state.narudzbe_proizvodi:
                red = {
                    "datum": str(datum),
                    "korisnik": klijent or korisnik,  # koristimo klijent ako je upisan
                    "reprezentacija": skladiste,
                    "tip_klijenta": tip_klijenta,
                    "odgovorna_osoba": odgovorna,
                    "sifra_proizvoda": proizvod["Šifra"],
                    "naziv_proizvoda": proizvod["Naziv"],
                    "kolicina": proizvod["Kol."],
                    "dobavljac": proizvod["Dobavljač"],
                    "cijena": proizvod["Ukupno"],
                    "oznaci_za_narudzbu": False,
                    "napomena_za_nas": napomena,
                    "unio_korisnik": st.session_state.user.email,
                    "datum_vrijeme_narudzbe": datetime.now(TZ).isoformat(),
                }
                supabase.table("main_orders").insert(red).execute()

            st.success("Narudžba spremljena! Svi proizvodi su dodani kao zasebni redovi.")
            st.session_state.narudzbe_proizvodi = []
            st.rerun()