import streamlit as st
import datetime
import pandas as pd
import locale

try:
    locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
    except:
        pass  # Locale tidak tersedia, pakai format manual


def format_rp(angka):
    try:
        return locale.currency(angka or 0, grouping=True, symbol='Rp ')[:-3]
    except:
        return f"Rp {angka or 0:,.0f}".replace(",", ".")


try:
    from model import Transaksi
    from manajer_anggaran import AnggaranHarian
    from konfigurasi import KATEGORI_PENGELUARAN
except ImportError as e:
    st.error(f"Gagal mengimpor modul: {e}. Pastikan file .py lain ada.")
    st.stop()

st.set_page_config(page_title="Catatan Pengeluaran", layout="wide",
                   initial_sidebar_state="expanded")


@st.cache_resource
def get_anggaran_manager():
    print(">>> STREAMLIT: (Cache Resource) Menginisialisasi AnggaranHarian...")
    return AnggaranHarian()


anggaran = get_anggaran_manager()


def halaman_input(anggaran):
    st.header("💸 Tambah Pengeluaran Baru")
    with st.form("form_transaksi_baru", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            deskripsi = st.text_input("Deskripsi*", placeholder="Contoh: Makan siang")
        with col2:
            kategori = st.selectbox("Kategori*:", KATEGORI_PENGELUARAN, index=0)
        col3, col4 = st.columns([1, 1])
        with col3:
            jumlah = st.number_input("Jumlah (Rp)*:", min_value=0.01, step=1000.0,
                                     format="%.0f", value=None, placeholder="Contoh: 25000")
        with col4:
            tanggal = st.date_input("Tanggal*:", value=datetime.date.today())
        submitted = st.form_submit_button("💾 Simpan Transaksi")
        if submitted:
            if not deskripsi:
                st.warning("Deskripsi wajib diisi!", icon="⚠️")
            elif jumlah is None or jumlah <= 0:
                st.warning("Jumlah wajib diisi!", icon="⚠️")
            else:
                with st.spinner("Menyimpan..."):
                    tx = Transaksi(deskripsi, float(jumlah), kategori, tanggal)
                    if anggaran.tambah_transaksi(tx):
                        st.success("Transaksi berhasil disimpan!", icon="✅")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan transaksi.", icon="❌")


def halaman_riwayat(anggaran):
    st.subheader("📋 Detail Semua Transaksi")
    if st.button("🔄 Refresh Riwayat"):
        st.cache_data.clear()
        st.rerun()
    with st.spinner("Memuat riwayat..."):
        df_transaksi = anggaran.get_dataframe_transaksi()
    if df_transaksi is None:
        st.error("Gagal mengambil riwayat transaksi.")
    elif df_transaksi.empty:
        st.info("Belum ada transaksi yang tercatat.")
    else:
        st.dataframe(df_transaksi, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("🗑️ Hapus Transaksi")
        st.caption("Masukkan ID transaksi yang ingin dihapus (lihat kolom id pada tabel di atas).")
        col_hapus1, _ = st.columns([1, 2])
        with col_hapus1:
            id_hapus = st.number_input("ID Transaksi yang Ingin Dihapus:", min_value=1,
                                       step=1, value=None, placeholder="Contoh: 3",
                                       key="input_id_hapus")
        if id_hapus is not None:
            id_hapus_int = int(id_hapus)
            data_terpilih = df_transaksi[df_transaksi['id'] == id_hapus_int]
            if data_terpilih.empty:
                st.warning(f"Tidak ditemukan transaksi dengan ID {id_hapus_int}.")
            else:
                baris = data_terpilih.iloc[0]
                st.info(f"Preview: ID {baris['id']} | {baris['tanggal']} | "
                        f"{baris['kategori']} | {baris['deskripsi']} | {baris['Jumlah (Rp)']}")
                if 'konfirmasi_hapus' not in st.session_state:
                    st.session_state.konfirmasi_hapus = False
                if 'id_dikonfirmasi' not in st.session_state:
                    st.session_state.id_dikonfirmasi = None
                col_b1, col_b2, _ = st.columns([1, 1, 4])
                with col_b1:
                    if st.button("🗑️ Hapus Transaksi Ini", type="primary", key="btn_hapus_init"):
                        st.session_state.konfirmasi_hapus = True
                        st.session_state.id_dikonfirmasi = id_hapus_int
                if st.session_state.konfirmasi_hapus and st.session_state.id_dikonfirmasi == id_hapus_int:
                    st.warning(f"Yakin hapus ID {id_hapus_int}? Tindakan ini tidak dapat dibatalkan.", icon="⚠️")
                    col_k1, col_k2, _ = st.columns([1, 1, 4])
                    with col_k1:
                        if st.button("✅ Ya, Hapus Sekarang", type="primary", key="btn_konfirm_hapus"):
                            with st.spinner("Menghapus..."):
                                berhasil = anggaran.hapus_transaksi(id_hapus_int)
                            if berhasil:
                                st.success(f"Transaksi ID {id_hapus_int} berhasil dihapus!")
                                st.session_state.konfirmasi_hapus = False
                                st.session_state.id_dikonfirmasi = None
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"Gagal menghapus transaksi ID {id_hapus_int}.")
                                st.session_state.konfirmasi_hapus = False
                    with col_k2:
                        if st.button("❌ Batal", key="btn_batal_hapus"):
                            st.session_state.konfirmasi_hapus = False
                            st.session_state.id_dikonfirmasi = None
                            st.rerun()


def halaman_ringkasan(anggaran):
    st.subheader("📊 Ringkasan Pengeluaran")
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        pilihan_periode = st.selectbox(
            "Filter Periode:",
            ["Semua Waktu", "Hari Ini", "Pilih Tanggal"],
            key="filter_periode",
            on_change=lambda: st.cache_data.clear()
        )
    tanggal_filter = None
    label_periode = "(Semua Waktu)"
    if pilihan_periode == "Hari Ini":
        tanggal_filter = datetime.date.today()
        label_periode = f"({tanggal_filter.strftime('%d %b')})"
    elif pilihan_periode == "Pilih Tanggal":
        if 'tanggal_pilihan_state' not in st.session_state:
            st.session_state.tanggal_pilihan_state = datetime.date.today()
        tanggal_filter = st.date_input(
            "Pilih Tanggal:",
            value=st.session_state.tanggal_pilihan_state,
            key="tanggal_pilihan",
            on_change=lambda: setattr(st.session_state, 'tanggal_pilihan_state',
                                      st.session_state.tanggal_pilihan) or st.cache_data.clear()
        )
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"
    with col_filter2:
        @st.cache_data(ttl=300)
        def hitung_total_cached(tgl_filter):
            return anggaran.hitung_total_pengeluaran(tanggal=tgl_filter)

        total_pengeluaran = hitung_total_cached(tanggal_filter)
        st.metric(label=f"Total Pengeluaran {label_periode}", value=format_rp(total_pengeluaran))
    st.divider()
    st.subheader(f"Pengeluaran per Kategori {label_periode}")

    @st.cache_data(ttl=300)
    def get_kategori_cached(tgl_filter):
        return anggaran.get_pengeluaran_per_kategori(tanggal=tgl_filter)

    with st.spinner("Memuat ringkasan kategori..."):
        dict_per_kategori = get_kategori_cached(tanggal_filter)
    if not dict_per_kategori:
        st.info("Tidak ada data untuk periode ini.")
    else:
        try:
            data_kategori = [{"Kategori": kat, "Total": jml} for kat, jml in dict_per_kategori.items()]
            df_kategori = pd.DataFrame(data_kategori).sort_values(by="Total", ascending=False).reset_index(drop=True)
            df_kategori['Total (Rp)'] = df_kategori['Total'].apply(format_rp)
            col_kat1, col_kat2 = st.columns(2)
            with col_kat1:
                st.write("Tabel:")
                st.dataframe(df_kategori[['Kategori', 'Total (Rp)']], hide_index=True, use_container_width=True)
            with col_kat2:
                st.write("Grafik:")
                st.bar_chart(df_kategori.set_index('Kategori')['Total'], use_container_width=True)
        except Exception as e:
            st.error(f"Gagal menampilkan ringkasan: {e}")


def main():
    st.sidebar.title("🪙 Catatan Pengeluaran")
    menu_pilihan = st.sidebar.radio("Pilih Menu:", ["Tambah", "Riwayat", "Ringkasan"], key="menu_utama")
    st.sidebar.markdown("---")
    st.sidebar.info("Jobsheet - Aplikasi Keuangan")
    manajer_anggaran = get_anggaran_manager()
    if menu_pilihan == "Tambah":
        halaman_input(manajer_anggaran)
    elif menu_pilihan == "Riwayat":
        halaman_riwayat(manajer_anggaran)
    elif menu_pilihan == "Ringkasan":
        halaman_ringkasan(manajer_anggaran)
    st.markdown("---")
    st.caption("Pengembangan Aplikasi Berbasis OOP")


if __name__ == "__main__":
    main()
