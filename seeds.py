# seeds.py (letakkan di root project, sejajar folder app/)
import os
import sys


# Tambahkan root project ke PYTHONPATH
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import create_app & db dari app/__init__.py
from app import create_app, db
# Import model dari app/models.py
from app.models import Gejala, Penyakit, RuleGejala, Solusi, Admin
from werkzeug.security import generate_password_hash

def run_seed():
    flask_app = create_app()

    with flask_app.app_context():
        # 1. Seed tabel penyakit
        penyakit_list = [
            {'id': 'P01', 'nama': 'Depresi',   'deskripsi': 'Gangguan Depresi',   'threshold': 7.0},
            {'id': 'P02', 'nama': 'Stres',      'deskripsi': 'Gangguan Stres',     'threshold': 7.5},
            {'id': 'P03', 'nama': 'Kecemasan',  'deskripsi': 'Gangguan Kecemasan', 'threshold': 7.0},
        ]
        for p in penyakit_list:
            db.session.merge(Penyakit(**p))

        # 2. Seed tabel gejala
        gejala_list = [
            {'id': 'G01', 'nama': 'Merasa sedih atau murung hampir sepanjang waktu', 'kategori' : 'Depresi'},
            {'id': 'G02', 'nama': 'Sering merasa sedih atau tidak bersemangat', 'kategori' : 'Depresi'},
            {'id': 'G03', 'nama': 'Tidak bisa menikmati hal-hal seperti biasa', 'kategori' : 'Depresi'},
            {'id': 'G04', 'nama': 'Merasa lelah atau tidak memiliki energi', 'kategori' : 'Depresi'},
            {'id': 'G05', 'nama': 'Merasa bersalah tanpa alasan jelas', 'kategori' : 'Depresi'},
            {'id': 'G06', 'nama': 'Merasa ingin menangis tanpa bisa dikendalikan', 'kategori' : 'Depresi'},
            {'id': 'G07', 'nama': 'Sulit tidur karena rasa cemas', 'kategori' : 'Depresi'},
            {'id': 'G08', 'nama': 'Segala hal terasa beban berat', 'kategori' : 'Depresi'},
            {'id': 'G09', 'nama': 'Sulit bangkit dari keterpurukan', 'kategori' : 'Depresi'},
            {'id': 'G10', 'nama': 'Merasa hidup tidak memiliki harapan', 'kategori' : 'Depresi'},
            {'id': 'G11', 'nama': 'Sulit mengontrol hal-hal penting dalam hidup', 'kategori' : 'Stres'},
            {'id': 'G12', 'nama': 'Merasa Stres dalam sebulan terakhir', 'kategori' : 'Stres'},
            {'id': 'G13', 'nama': 'Kesulitan menangani masalah pribadi', 'kategori' : 'Stres'},
            {'id': 'G14', 'nama': 'Segala sesuatu tidak sesuai harapan', 'kategori' : 'Stres'},
            {'id': 'G15', 'nama': 'Tertekan oleh banyak tanggung jawab', 'kategori' : 'Stres'},
            {'id': 'G16', 'nama': 'Mudah marah karena hal-hal kecil', 'kategori' : 'Stres'},
            {'id': 'G17', 'nama': 'Kehilangan kepercayaan diri', 'kategori' : 'Stres'},
            {'id': 'G18', 'nama': 'Stres akibat tuntutan pekerjaan/rumah tangga', 'kategori' : 'Stres'},
            {'id': 'G19', 'nama': 'Masalah bertambah lebih cepat dari kemampuan', 'kategori' : 'Stres'},
            {'id': 'G20', 'nama': 'Tidak dapat mengatasi semua gangguan hidup', 'kategori' : 'Stres'},
            {'id': 'G21', 'nama': 'Merasa gugup, cemas, atau gelisah hampir setiap hari', 'kategori' : 'Kecemasan'},
            {'id': 'G22', 'nama': 'Tidak dapat mengendalikan rasa khawatir', 'kategori' : 'Kecemasan'},
            {'id': 'G23', 'nama': 'Terlalu khawatir terhadap hal kecil', 'kategori' : 'Kecemasan'},
            {'id': 'G24', 'nama': 'Begitu gelisah sampai sulit duduk diam', 'kategori' : 'Kecemasan'},
            {'id': 'G25', 'nama': 'Merasa takut seolah sesuatu buruk akan terjadi', 'kategori' : 'Kecemasan'},
            {'id': 'G26', 'nama': 'Cemas tentang kesehatan bayi (perinatal)', 'kategori' : 'Kecemasan'},
            {'id': 'G27', 'nama': 'Hindari aktivitas karena rasa takut berlebihan', 'kategori' : 'Kecemasan'},
            {'id': 'G28', 'nama': 'Gangguan tidur akibat kekhawatiran', 'kategori' : 'Kecemasan'},
            {'id': 'G29', 'nama': 'Serangan panik atau gejala fisik cemas', 'kategori' : 'Kecemasan'},
            {'id': 'G30', 'nama': 'Cemas tentang kemampuan menjadi ibu', 'kategori' : 'Kecemasan'},
        ]
        for g in gejala_list:
            db.session.merge(Gejala(**g))

        # 3. Seed tabel rule_gejala dengan bobot
        rule_list = [
            # Depresi (P01)
            ('P01','G01',1.0), ('P01','G02',0.9), ('P01','G03',1.0), ('P01','G04',0.8),
            ('P01','G05',0.7), ('P01','G06',0.6), ('P01','G07',0.7), ('P01','G08',0.8),
            ('P01','G09',0.9), ('P01','G10',1.0),
            # Stres (P02)
            ('P02','G11',1.0), ('P02','G12',0.9), ('P02','G13',0.9), ('P02','G14',0.8),
            ('P02','G15',1.0), ('P02','G16',0.7), ('P02','G17',0.9), ('P02','G18',1.0),
            ('P02','G19',1.0), ('P02','G20',0.9),
            # Kecemasan (P03)
            ('P03','G21',1.0), ('P03','G22',1.0), ('P03','G23',0.9), ('P03','G24',0.8),
            ('P03','G25',0.9), ('P03','G26',1.0), ('P03','G27',0.9), ('P03','G28',1.0),
            ('P03','G29',1.0), ('P03','G30',0.8),
        ]
        for pid, gid, bobot in rule_list:
            db.session.merge(RuleGejala(penyakit_id=pid, gejala_id=gid, bobot=bobot))

               # 4. Seed tabel solusi
                # 4. Seed tabel solusi (dengan format poin-poin)
        solusi_list = [
    # Depresi - ringan
    {'penyakit_id': 'P01', 'skala': 'ringan', 'solusi': 'Lakukan aktivitas yang menyenangkan seperti hobi.'},
    {'penyakit_id': 'P01', 'skala': 'ringan', 'solusi': 'Berbicara dengan orang terdekat atau keluarga.'},
    {'penyakit_id': 'P01', 'skala': 'ringan', 'solusi': 'Coba olahraga ringan seperti jalan kaki atau yoga.'},

    # Depresi - sedang
    {'penyakit_id': 'P01', 'skala': 'sedang', 'solusi': 'Ikuti sesi konseling dengan psikolog.'},
    {'penyakit_id': 'P01', 'skala': 'sedang', 'solusi': 'Tidur dan pola makan teratur.'},
    {'penyakit_id': 'P01', 'skala': 'sedang', 'solusi': 'Batasi penggunaan media sosial yang bersifat negatif.'},

    # Depresi - berat
    {'penyakit_id': 'P01', 'skala': 'berat', 'solusi': 'Segera konsultasi dengan psikiater.'},
    {'penyakit_id': 'P01', 'skala': 'berat', 'solusi': 'Pertimbangkan terapi medis jika disarankan.'},
    {'penyakit_id': 'P01', 'skala': 'berat', 'solusi': 'Libatkan keluarga atau orang dekat untuk dukungan.'},

    # Stres - ringan
    {'penyakit_id': 'P02', 'skala': 'ringan', 'solusi': 'Coba meditasi atau pernapasan dalam.'},
    {'penyakit_id': 'P02', 'skala': 'ringan', 'solusi': 'Ambil waktu istirahat yang cukup.'},
    {'penyakit_id': 'P02', 'skala': 'ringan', 'solusi': 'Kurangi konsumsi kafein.'},

    # Stres - sedang
    {'penyakit_id': 'P02', 'skala': 'sedang', 'solusi': 'Evaluasi penyebab stres utama.'},
    {'penyakit_id': 'P02', 'skala': 'sedang', 'solusi': 'Diskusikan masalah dengan teman dekat atau profesional.'},
    {'penyakit_id': 'P02', 'skala': 'sedang', 'solusi': 'Coba teknik time management dan journaling.'},

    # Stres - berat
    {'penyakit_id': 'P02', 'skala': 'berat', 'solusi': 'Cari bantuan profesional seperti psikolog.'},
    {'penyakit_id': 'P02', 'skala': 'berat', 'solusi': 'Hindari keputusan besar saat kondisi tidak stabil.'},
    {'penyakit_id': 'P02', 'skala': 'berat', 'solusi': 'Ikuti terapi relaksasi atau terapi kognitif.'},

    # Kecemasan - ringan
    {'penyakit_id': 'P03', 'skala': 'ringan', 'solusi': 'Gunakan teknik grounding atau mindfulness.'},
    {'penyakit_id': 'P03', 'skala': 'ringan', 'solusi': 'Hindari konsumsi berita berlebihan.'},
    {'penyakit_id': 'P03', 'skala': 'ringan', 'solusi': 'Lakukan aktivitas fisik ringan setiap hari.'},

    # Kecemasan - sedang
    {'penyakit_id': 'P03', 'skala': 'sedang', 'solusi': 'Ikuti sesi konseling secara rutin.'},
    {'penyakit_id': 'P03', 'skala': 'sedang', 'solusi': 'Tuliskan perasaan dalam jurnal harian.'},
    {'penyakit_id': 'P03', 'skala': 'sedang', 'solusi': 'Kurangi paparan stresor seperti pekerjaan berlebih.'},

    # Kecemasan - berat
    {'penyakit_id': 'P03', 'skala': 'berat', 'solusi': 'Segera konsultasi dengan psikiater.'},
    {'penyakit_id': 'P03', 'skala': 'berat', 'solusi': 'Pertimbangkan penggunaan obat anti-cemas jika perlu.'},
    {'penyakit_id': 'P03', 'skala': 'berat', 'solusi': 'Libatkan keluarga untuk pendampingan dan dukungan.'},
]


        for s in solusi_list:
            db.session.merge(Solusi(**s))




        db.session.commit()
        print("✅ Seeding selesai.")

if __name__ == '__main__':
    run_seed()

