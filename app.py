import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Nova narudžba", layout="wide")

TZ = ZoneInfo("Europe/Zagreb")

# ────────────────────────────────────────────────
#  SESSION STATE – čuva listu proizvoda i stanje forme
# ────────────────────────────────────────────────

if "narudzbe_proizvodi" not in st.session_state:
    st.session_state.narudzbe_proizvodi = []

if "show_dodaj_proizvod" not in st.session_state:
    st.session_state.show_dodaj_proizvod = False

# ────────────────────────────────────────────────
#  GLAVNI NASLOV + GUMB ZA POVRATAK
# ────────────────────────────────────────────────

col_naslov, col_natrag = st.columns([5, 1])
with col_naslov:
    st.title("Nova narudžba")

with col_natrag:
    if st.button("← Natrag na pregled"):
        st.session_state.narudzbe_proizvodi = []
        st.session_state.show_dodaj_proizvod = False
        st.rerun()

# ────────────────────────────────────────────────
#  LIJEVI STUPAC – podaci o narudžbi
# ────────────────────────────────────────────────

col_lijevo, col_desno = st.columns([1, 2])

with col_lijevo:
    st.markdown("**Korisnik**")
    korisnik = st.selectbox("", ["Daniel Putar", "Drugi korisnik"], index=0, label_visibility="collapsed")
    st.success(f"✓ {korisnik}")

    st.markdown("**Skladište**")
    skladiste = st.selectbox("", ["Osijek - Glavno skladište"], index=0, label_visibility="collapsed")
    st.success(f"✓ {skladiste}")

    st.markdown("**Tip klijenta**")
    tip_klijenta = st.selectbox("", ["", "Doznaka", "Narudžba", "Uzorak"], index=0, label_visibility="collapsed")
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
    odgovorna = st.selectbox("", ["Nema", "Osoba 1", "Osoba 2"], index=0, label_visibility="collapsed")
    if odgovorna != "Nema":
        st.success(f"✓ {odgovorna}")
    else:
        st.success("✓ Nema")

    st.markdown("**Datum kada je odobren nalog**")
    datum = st.date_input("", datetime.today(), label_visibility="collapsed")
    st.info("Default: današnji datum")

    st.markdown("**Napomena**")
    napomena = st.text_area("", placeholder="Vidljivo nama, ne dobavljaču", height=100, label_visibility="collapsed")

# ────────────────────────────────────────────────
#  DESNI STUPAC – tablica proizvoda + dodavanje
# ────────────────────────────────────────────────

with col_desno:
    st.markdown("**Proizvodi**")

    # Tablica proizvoda
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
                "Kol.": st.column_config.NumberColumn("Kol.", min_value=0.01, step=0.01, format="%.2f"),
                "Cijena": st.column_config.NumberColumn("Cijena", format="%.2f"),
                "Ukupno": st.column_config.NumberColumn("Ukupno", format="%.2f", disabled=True),
                "Dobavljač": st.column_config.TextColumn("Dobavljač"),
            }
        )

        ukupno = edited["Ukupno"].sum()
        st.markdown(f"**UKUPNO: {ukupno:,.2f} EUR + PDV**")
    else:
        st.info("Još nema proizvoda. Dodaj ih gumbom +")

    # Gumb za otvaranje modala za dodavanje
    if st.button("➕ Dodaj proizvod", type="primary"):
        st.session_state.show_dodaj_proizvod = True

    # Modal / expander za dodavanje proizvoda
    if st.session_state.show_dodaj_proizvod:
        with st.expander("Dodaj proizvod", expanded=True):
            col1, col2 = st.columns(2)
            sifra = col1.text_input("Šifra")
            naziv = col2.text_input("Naziv proizvoda *")

            col3, col4 = st.columns(2)
            kol = col3.number_input("Količina *", min_value=0.01, step=0.01, format="%.2f")
            cijena = col4.number_input("Cijena po komadu", min_value=0.0, step=0.01, format="%.2f")

            dobavljac = st.text_input("Dobavljač")

            col_g, col_x = st.columns([1, 1])
            if col_g.button("Dodaj u narudžbu"):
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
                    st.session_state.show_dodaj_proizvod = False
                    st.rerun()
                else:
                    st.error("Naziv i količina su obavezni!")

            if col_x.button("Odustani"):
                st.session_state.show_dodaj_proizvod = False
                st.rerun()

# ────────────────────────────────────────────────
#  DONJI GUMBI
# ────────────────────────────────────────────────

col1, col2 = st.columns(2)
if col1.button("Odustani", type="secondary"):
    st.session_state.narudzbe_proizvodi = []
    st.rerun()

if col2.button("Spremi narudžbu", type="primary"):
    if st.session_state.narudzbe_proizvodi:
        st.success("Narudžba spremljena! (spremanje u bazu dodajemo u sljedećem koraku)")
    else:
        st.warning("Dodaj barem jedan proizvod!")