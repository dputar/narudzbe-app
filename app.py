import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# Ako imaš Supabase, ostavi ovo; ako ne, možeš ga maknuti
# SUPABASE_URL = "..."
# SUPABASE_KEY = "..."
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# TZ = ZoneInfo("Europe/Zagreb")

# Za testiranje bez baze – koristimo session state
if "narudzbe_proizvodi" not in st.session_state:
    st.session_state.narudzbe_proizvodi = []

st.set_page_config(page_title="Nova narudžba", layout="wide")

st.title("Nova narudžba")

# ==================== LIJEVI DIO ====================
col_lijevo, col_desno = st.columns([1, 2])

with col_lijevo:
    st.markdown("### Korisnik")
    korisnik = st.selectbox("Korisnik", ["", "Daniel Putar", "Drugi korisnik"], index=0)
    if korisnik:
        st.success(f"Odabrano: {korisnik}")

    st.markdown("### Skladište")
    skladiste = st.selectbox("Skladište", ["", "Osijek - Glavno skladište", "Drugo skladište"], index=0)
    if skladiste:
        st.success(f"Odabrano: {skladiste}")

    st.markdown("### Tip klijenta")
    tip_klijenta = st.selectbox("Tip klijenta", ["", "Doznaka", "Narudžba", "Uzorak"], index=0)
    if tip_klijenta:
        st.success(f"Odabrano: {tip_klijenta}")

    st.markdown("### Klijent")
    klijent = st.text_input("Klijent (ili iz padajućeg kasnije)")
    if klijent:
        st.success(f"Uneseno: {klijent}")

    st.markdown("### Odgovorna osoba")
    odgovorna = st.text_input("Odgovorna osoba")
    if odgovorna:
        st.success(f"Odgovorna: {odgovorna}")

    st.markdown("### Datum kada je odobren nalog")
    datum = st.date_input("Datum", datetime.today())
    st.info(f"Default: današnji datum")

    st.markdown("### Napomena")
    napomena = st.text_area("Napomena (vidljiva nama, ne dobavljaču)")
    if napomena:
        st.info(f"Napomena: {napomena}")

# ==================== DESNI DIO ====================
with col_desno:
    st.markdown("### Proizvodi")

    # Tablica proizvoda
    if st.session_state.narudzbe_proizvodi:
        df_proizvodi = pd.DataFrame(st.session_state.narudzbe_proizvodi)
        edited_df = st.data_editor(
            df_proizvodi,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Šifra": st.column_config.TextColumn("Šifra", width="medium"),
                "Naziv": st.column_config.TextColumn("Naziv", width="large"),
                "Kol.": st.column_config.NumberColumn("Kol.", min_value=0.0, step=0.01, format="%.2f"),
                "Cijena": st.column_config.NumberColumn("Cijena", format="%.2f"),
                "Ukupno": st.column_config.NumberColumn("Ukupno", format="%.2f"),
                "Dobavljač": st.column_config.TextColumn("Dobavljač"),
            }
        )
        # Računanje ukupno
        edited_df["Ukupno"] = edited_df["Kol."] * edited_df["Cijena"]
        ukupno = edited_df["Ukupno"].sum()
        st.markdown(f"**UKUPNO: {ukupno:,.2f} EUR + PDV**")
    else:
        st.info("Još nema proizvoda. Dodaj ih zelenim gumbom +")

    # Gumb za dodavanje novog retka (modal)
    if st.button("➕ Dodaj proizvod", type="primary"):
        with st.expander("Dodaj proizvod", expanded=True):
            col1, col2 = st.columns(2)
            sifra = col1.text_input("Šifra")
            naziv = col2.text_input("Naziv proizvoda")
            kol = st.number_input("Količina", min_value=0.0, step=0.01, format="%.2f")
            cijena = st.number_input("Cijena po komadu", min_value=0.0, step=0.01, format="%.2f")
            dobavljac = st.text_input("Dobavljač")

            if st.button("Dodaj u listu"):
                if naziv and kol > 0:
                    novi_proizvod = {
                        "Šifra": sifra,
                        "Naziv": naziv,
                        "Kol.": kol,
                        "Cijena": cijena,
                        "Ukupno": kol * cijena,
                        "Dobavljač": dobavljac
                    }
                    st.session_state.narudzbe_proizvodi.append(novi_proizvod)
                    st.rerun()
                else:
                    st.error("Naziv i količina su obavezni!")

# Gumbi na dnu
col1, col2 = st.columns(2)
if col1.button("Odustani", type="secondary"):
    st.warning("Odustali ste od narudžbe")
if col2.button("Spremi narudžbu", type="primary"):
    st.success("Narudžba spremljena! (još nije implementirano spremanje u bazu)")