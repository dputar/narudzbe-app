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

# SIDEBAR NAVIGACIJA
st.sidebar.title("Navigacija")

page = st.sidebar.radio(
    "Glavni modul",
    ["🏠 Početna", "📦 Narudžbe", "📊 Izvještaji", "⚙️ Administracija", "📄 Dokumenti", "🚪 Odjava"]
)

# Podizbornik za Narudžbe
if page == "📦 Narudžbe":
    with st.sidebar.expander("Narudžbe", expanded=True):
        sub_page = st.radio(
            " ",
            ["Aktivne narudžbe", "Sve narudžbe", "Nova narudžba", "Pretraga narudžbi"]
        )
else:
    sub_page = page

# Glavni sadržaj
if page == "🏠 Početna":
    st.title("Dobrodošli u sustav narudžbi")
    st.markdown("Ovdje će kasnije biti dashboard, aktivne narudžbe, statistika...")
    st.info("Za sada je ovo placeholder stranica.")

elif page == "📦 Narudžbe":
    # Dohvati sve narudžbe jednom
    response = supabase.table("main_orders").select("*").order("datum", desc=True).execute()
    df_all = pd.DataFrame(response.data or [])

    if sub_page == "Aktivne narudžbe":
        st.title("Aktivne narudžbe")
        if st.button("🔄 Osvježi"):
            st.rerun()

        df_active = df_all[df_all["oznaci_zaprimljeno"] != True].copy()
        df_active = df_active.fillna("")
        df_active.insert(0, "🗑️", False)

        edited_active = st.data_editor(
            df_active,
            hide_index=True,
            use_container_width=True,
            height=750,
            column_config={
                "🗑️": st.column_config.CheckboxColumn("🗑️", width=50),
                "oznaci_za_narudzbu": st.column_config.CheckboxColumn("Za narudžbu", width=100),
                "oznaci_zaprimljeno": st.column_config.CheckboxColumn("Zaprimljeno", width=100),
            }
        )

        col1, col2 = st.columns([1, 4])
        if col1.button("💾 Spremi promjene"):
            # Čišćenje i spremanje (kao prije)
            records = edited_active.drop(columns=["🗑️"]).to_dict(orient="records")
            records = [{k: v for k, v in row.items() if v is not None} for row in records]
            try:
                supabase.table("main_orders").upsert(records, on_conflict="id").execute()
                st.success("Spremljeno!")
                st.rerun()
            except Exception as e:
                st.error(f"Greška: {e}")

        if col2.button("🗑️ Obriši označene"):
            to_del = edited_active[edited_active["🗑️"] == True]
            if not to_del.empty:
                for rid in to_del["id"].tolist():
                    supabase.table("main_orders").delete().eq("id", rid).execute()
                st.success("Obrisano!")
                st.rerun()
            else:
                st.warning("Nisi označio nijedan red.")

    elif sub_page == "Sve narudžbe":
        st.title("Sve narudžbe")
        if st.button("🔄 Osvježi"):
            st.rerun()

        df_all = df_all.fillna("")
        df_all.insert(0, "🗑️", False)

        edited_all = st.data_editor(
            df_all,
            hide_index=True,
            use_container_width=True,
            height=750,
            column_config={
                "🗑️": st.column_config.CheckboxColumn("🗑️", width=50),
                "oznaci_za_narudzbu": st.column_config.CheckboxColumn("Za narudžbu", width=100),
                "oznaci_zaprimljeno": st.column_config.CheckboxColumn("Zaprimljeno", width=100),
            }
        )

        # Isto spremanje i brisanje kao gore (možeš kopirati kod)

    elif sub_page == "Nova narudžba":
        st.title("Nova narudžba")
        st.info("Ovdje ide nova forma po slici – krećemo u sljedećem koraku")

    elif sub_page == "Pretraga narudžbi":
        st.title("Pretraga narudžbi")
        st.info("Ovdje će biti filteri i tražilica – dodajemo kasnije")

elif page == "⚙️ Administracija":
    st.title("Administracija")
    st.info("Ovdje će biti podizbornici za proizvode, dobavljače, korisnike...")

elif page == "🚪 Odjava":
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()