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

# --- Sidebar navigation ---
st.sidebar.title("Navigacija")

# Glavni izbornik
page = st.sidebar.radio(
    "Odaberi modul",
    [
        "🏠 Početna",
        "📦 Narudžbe",
        "📊 Izvještaji",
        "⚙️ Administracija",
        "📄 Dokumenti",
        "🚪 Odjava"
    ]
)

# Podizbornici (koristimo st.expander za hijerarhiju)
if page == "📦 Narudžbe":
    with st.sidebar.expander("Narudžbe", expanded=True):
        sub_page = st.radio(
            " ",
            ["Aktivne narudžbe", "Sve narudžbe", "Nova narudžba", "Pretraga narudžbi"]
        )
elif page == "⚙️ Administracija":
    with st.sidebar.expander("Administracija", expanded=True):
        sub_page = st.radio(
            " ",
            ["Proizvodi", "Dobavljači", "Korisnici", "Šifarnici"]
        )
else:
    sub_page = page  # za ostale stranice

# --- Glavni sadržaj (prema odabiru) ---
if page == "🏠 Početna":
    st.title("Dobrodošli u sustav narudžbi")
    st.write("Ovdje će biti dashboard, ključni pokazatelji, aktivne narudžbe itd.")
    st.info("Ovo je početna stranica. Još nije implementirana.")

elif page == "📦 Narudžbe" or page == "📦 Narudžbe":
    if sub_page == "Aktivne narudžbe":
        st.title("Aktivne narudžbe")
        st.info("Ovdje će biti lista aktivnih (npr. ne-zaprimljenih) narudžbi.")
        # Kasnije dodajemo filter + tablicu

    elif sub_page == "Sve narudžbe":
        st.title("Sve narudžbe")
        if st.button("🔄 Osvježi"):
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
                records = records.where(pd.notnull(records), None).to_dict(orient="records")
                try:
                    supabase.table("main_orders").upsert(records, on_conflict="id").execute()
                    st.success("Promjene spremljene!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Greška: {e}")
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

    elif sub_page == "Nova narudžba":
        st.title("Nova narudžba")
        # ... (možeš ovdje ostaviti staru formu za dodavanje narudžbe)
        with st.form("new_order_form", clear_on_submit=True):
            # (tvoja stara forma ovdje - kopiraj ako želiš)
            st.write("Ovdje ide forma za novu narudžbu (možeš kopirati staru)")

    elif sub_page == "Pretraga narudžbi":
        st.title("Pretraga narudžbi")
        st.info("Ovdje će biti pretraga po različitim kriterijima.")

elif page == "📊 Izvještaji":
    st.title("Izvještaji")
    st.info("Ovdje će biti različiti izvještaji i statistike.")

elif page == "⚙️ Administracija":
    if sub_page == "Proizvodi":
        st.title("Proizvodi")
        st.info("Ovdje će biti lista proizvoda + dodavanje/uređivanje.")

    elif sub_page == "Dobavljači":
        st.title("Dobavljači")
        st.info("Ovdje će biti lista dobavljača + dodavanje/uređivanje.")

    elif sub_page == "Korisnici":
        st.title("Korisnici")
        st.info("Ovdje će biti upravljanje korisnicima.")

    elif sub_page == "Šifarnici":
        st.title("Šifarnici")
        st.info("Ovdje će biti ostali šifarnici (npr. kategorije, statusi...).")

elif page == "📄 Dokumenti":
    st.title("Dokumenti")
    st.info("Ovdje će biti generiranje i pregled dokumenata (PDF, Excel...).")

elif page == "🚪 Odjava":
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()