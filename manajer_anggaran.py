import datetime
import pandas as pd
from database import execute_query, fetch_query, get_dataframe, setup_database_initial
from model import Transaksi


class AnggaranHarian:
    """Mengelola logika bisnis pengeluaran harian (Repository Pattern)."""
    _db_setup_done = False  # Flag untuk memastikan setup DB hanya dicek sekali per sesi

    def __init__(self):
        if not AnggaranHarian._db_setup_done:
            print("[AnggaranHarian] Melakukan pengecekan/setup database awal...")
            if setup_database_initial():
                AnggaranHarian._db_setup_done = True
                print("[AnggaranHarian] Database siap.")
            else:
                print("[AnggaranHarian] KRITICAL: Setup database awal GAGAL!")

    def tambah_transaksi(self, transaksi) -> bool:
        if not isinstance(transaksi, Transaksi) or transaksi.jumlah <= 0:
            return False
        sql = "INSERT INTO transaksi (deskripsi, jumlah, kategori, tanggal) VALUES (?, ?, ?, ?)"
        params = (
            transaksi.deskripsi,
            transaksi.jumlah,
            transaksi.kategori,
            transaksi.tanggal.strftime("%Y-%m-%d")
        )
        last_id = execute_query(sql, params)
        if last_id is not None:
            transaksi.id = last_id
            return True
        return False

    def get_semua_transaksi_obj(self) -> list:
        sql = "SELECT id, deskripsi, jumlah, kategori, tanggal FROM transaksi ORDER BY tanggal DESC, id DESC"
        rows = fetch_query(sql, fetch_all=True)
        transaksi_list = []
        if rows:
            for row in rows:
                transaksi_list.append(Transaksi(
                    id_transaksi=row['id'],
                    deskripsi=row['deskripsi'],
                    jumlah=row['jumlah'],
                    kategori=row['kategori'],
                    tanggal=row['tanggal']
                ))
        return transaksi_list

    def get_dataframe_transaksi(self, filter_tanggal=None) -> pd.DataFrame:
        query = "SELECT id, tanggal, kategori, deskripsi, jumlah FROM transaksi"
        params = None
        if filter_tanggal:
            query += " WHERE tanggal = ?"
            params = (filter_tanggal.strftime("%Y-%m-%d"),)
        query += " ORDER BY tanggal DESC, id DESC"
        df = get_dataframe(query, params=params)
        if not df.empty:
            try:
                import locale
                locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
                df['Jumlah (Rp)'] = df['jumlah'].map(
                    lambda x: locale.currency(x or 0, grouping=True, symbol='Rp ')[:-3]
                )
            except:
                df['Jumlah (Rp)'] = df['jumlah'].map(
                    lambda x: f"Rp {x or 0:,.0f}".replace(",", ".")
                )
            df = df[['id', 'tanggal', 'kategori', 'deskripsi', 'Jumlah (Rp)']]
        return df

    def hitung_total_pengeluaran(self, tanggal=None) -> float:
        sql = "SELECT SUM(jumlah) FROM transaksi"
        params = None
        if tanggal:
            sql += " WHERE tanggal = ?"
            params = (tanggal.strftime("%Y-%m-%d"),)
        result = fetch_query(sql, params=params, fetch_all=False)
        if result and result[0] is not None:
            return float(result[0])
        return 0.0

    def get_pengeluaran_per_kategori(self, tanggal=None) -> dict:
        hasil = {}
        sql = "SELECT kategori, SUM(jumlah) FROM transaksi"
        params = []
        if tanggal:
            sql += " WHERE tanggal = ?"
            params.append(tanggal.strftime("%Y-%m-%d"))
        sql += " GROUP BY kategori HAVING SUM(jumlah) > 0 ORDER BY SUM(jumlah) DESC"
        rows = fetch_query(sql, params=tuple(params) if params else None, fetch_all=True)
        if rows:
            for row in rows:
                kategori = row['kategori'] if row['kategori'] else "Lainnya"
                jumlah = float(row[1]) if row[1] is not None else 0.0
                hasil[kategori] = jumlah
        return hasil

    def hapus_transaksi(self, id_transaksi: int) -> bool:
        """
        Menghapus transaksi berdasarkan ID dari database.

        Args:
            id_transaksi (int): ID transaksi yang ingin dihapus.

        Returns:
            bool: True jika penghapusan berhasil, False jika gagal.
        """
        if not isinstance(id_transaksi, int) or id_transaksi <= 0:
            print(f"[AnggaranHarian] ID transaksi tidak valid: {id_transaksi}")
            return False

        sql = "DELETE FROM transaksi WHERE id = ?"
        params = (id_transaksi,)
        result = execute_query(sql, params)

        if result is not None:
            print(f"[AnggaranHarian] Transaksi ID {id_transaksi} berhasil dihapus.")
            return True
        else:
            print(f"[AnggaranHarian] Gagal menghapus transaksi ID {id_transaksi}.")
            return False
