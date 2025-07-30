from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Admin, Diagnosa, Penyakit, Gejala, RuleGejala
from app import db
from passlib.hash import scrypt
import ast

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    debug_password_input = None
    debug_hash_db = None
    debug_verifikasi = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin:
            debug_password_input = password
            debug_hash_db = admin.password
            try:
                if scrypt.verify(password, admin.password):
                    debug_verifikasi = "Berhasil"
                    session['admin_id'] = admin.id
                    return redirect(url_for('admin.dashboard'))
                else:
                    debug_verifikasi = "Gagal"
                    flash('Login gagal. Username atau password salah.')
            except Exception as e:
                debug_verifikasi = f"Gagal - Error: {str(e)}"
                flash('Terjadi kesalahan saat verifikasi password.')
        else:
            flash('Login gagal. Username atau password salah.')

    return render_template(
        'admin/login.html',
        debug_password_input=debug_password_input,
        debug_hash_db=debug_hash_db,
        debug_verifikasi=debug_verifikasi
    )

@admin_bp.route('/create-admin')
def create_admin():
    from passlib.hash import scrypt
    new_admin = Admin(
        username='admin',
        password=scrypt.hash('admin123')
    )
    db.session.add(new_admin)
    db.session.commit()
    return "Admin berhasil dibuat."

def parse_all_answers(jawaban_string):
    all_answers = {}
    pasangan = jawaban_string.split(', ')
    for p in pasangan:
        if '(' in p and ')' in p:
            gid = p.split('(')[0]
            try:
                nilai = int(p.split('(')[1].replace(')', ''))
                all_answers[gid] = nilai
            except ValueError:
                pass
    return all_answers


def compute_hasil(all_answers):
    hasil_per_penyakit = []
    from app.models import Penyakit, RuleGejala  # atau sesuaikan path modelnya

    penyakit_list = Penyakit.query.all()
    for penyakit in penyakit_list:
        pid = penyakit.id
        threshold = penyakit.threshold
        rules = RuleGejala.query.filter_by(penyakit_id=pid).all()

        skor_aktual = 0.0
        skor_maks = 0.0

        for rule in rules:
            gid = rule.gejala_id
            bobot = rule.bobot
            if gid in all_answers:
                skor_aktual += all_answers[gid] * bobot
            skor_maks += 3 * bobot

        if skor_aktual <= 0 or skor_maks == 0:
            continue

        persentase = (skor_aktual / skor_maks) * 100

        if persentase < 50:
            kelas = 'Ringan'
        elif persentase < 75:
            kelas = 'Sedang'
        else:
            kelas = 'Berat'

        hasil_per_penyakit.append({
            'penyakit_nama': penyakit.nama,
            'persentase': round(persentase, 2),
            'kelas': kelas
        })

    return hasil_per_penyakit


@admin_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))

    page = request.args.get('page', 1, type=int)
    per_page = 50

    pagination = Diagnosa.query.order_by(Diagnosa.tanggal.desc()).paginate(page=page, per_page=per_page, error_out=False)
    diagnosa_list = pagination.items

    for d in diagnosa_list:
        all_answers = parse_all_answers(d.gejala_skoring)
        hasil = compute_hasil(all_answers)
        if hasil:
            d.penyakit_nama = hasil[0]['penyakit_nama']
            d.persentase = hasil[0]['persentase']
            d.kelas = hasil[0]['kelas']
        else:
            d.penyakit_nama = '-'
            d.persentase = 0
            d.kelas = '-'
    
            # Hitung jumlah penyakit P01, P02, P03
    penyakit_P01_count = Diagnosa.query.filter_by(penyakit_id='P01').count()
    penyakit_P02_count = Diagnosa.query.filter_by(penyakit_id='P02').count()
    penyakit_P03_count = Diagnosa.query.filter_by(penyakit_id='P03').count()

    return render_template('admin/dashboard.html', diagnosa_list=diagnosa_list, pagination=pagination,
                           penyakit_P01_count=penyakit_P01_count,
                           penyakit_P02_count=penyakit_P02_count,
                           penyakit_P03_count=penyakit_P03_count)

@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('Berhasil logout.')
    return redirect(url_for('admin.login'))

@admin_bp.route('/penyakit/tambah', methods=['GET', 'POST'])
def tambah_penyakit():
    if request.method == 'POST':
        id = request.form['id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        threshold = request.form['threshold']

        # Cek apakah ID sudah ada
        existing = Penyakit.query.get(id)
        if existing:
            flash('ID penyakit sudah ada!', 'warning')
            return redirect(request.url)

        penyakit = Penyakit(id=id, nama=nama, deskripsi=deskripsi, threshold=threshold)
        db.session.add(penyakit)
        db.session.commit()
        flash('Penyakit berhasil ditambahkan.', 'success')
        return redirect(request.url)

    semua_penyakit = Penyakit.query.order_by(Penyakit.id).all()
    return render_template('admin/tambah_penyakit.html', semua_penyakit=semua_penyakit)

@admin_bp.route('/gejala/tambah', methods=['GET', 'POST'])
def tambah_gejala():
    if request.method == 'POST':
        id = request.form['id']
        nama = request.form['nama']
        kategori = request.form['kategori']  # ini ID penyakit

        gejala = Gejala(id=id, nama=nama, kategori=kategori)
        db.session.add(gejala)
        db.session.commit()
        flash('Gejala berhasil ditambahkan.', 'success')
        return redirect(request.url)

    semua_gejala = Gejala.query.order_by(Gejala.id).all()
    semua_penyakit = Penyakit.query.order_by(Penyakit.nama).all()
    return render_template('admin/tambah_gejala.html', semua_gejala=semua_gejala, semua_penyakit=semua_penyakit)

@admin_bp.route('/rule_gejala/tambah', methods=['GET', 'POST'])
def tambah_rule_gejala():
    if request.method == 'POST':
        penyakit_id = request.form['penyakit_id']
        gejala_id = request.form['gejala_id']
        bobot = float(request.form['bobot'])

        # Cek jika sudah ada
        existing = RuleGejala.query.filter_by(penyakit_id=penyakit_id, gejala_id=gejala_id).first()
        if existing:
            flash('Rule gejala ini sudah ada.', 'warning')
            return redirect(request.url)

        rule = RuleGejala(penyakit_id=penyakit_id, gejala_id=gejala_id, bobot=bobot)
        db.session.add(rule)
        db.session.commit()
        flash('Rule gejala berhasil ditambahkan.', 'success')
        return redirect(request.url)

    semua_penyakit = Penyakit.query.all()
    semua_gejala = Gejala.query.all()
    semua_rule = RuleGejala.query.all()
    return render_template('admin/tambah_rule_gejala.html', semua_penyakit=semua_penyakit, semua_gejala=semua_gejala, semua_rule=semua_rule)

# Hapus Penyakit
@admin_bp.route('/penyakit/hapus/<string:id>', methods=['POST'])
def hapus_penyakit(id):
    penyakit = Penyakit.query.get_or_404(id)

    # Hapus semua rule yang terkait dengan penyakit ini
    RuleGejala.query.filter_by(penyakit_id=id).delete()

    db.session.delete(penyakit)
    db.session.commit()
    flash('Penyakit berhasil dihapus.', 'success')
    return redirect(url_for('admin.tambah_penyakit'))

# Hapus Gejala
@admin_bp.route('/gejala/hapus/<string:id>', methods=['POST'])
def hapus_gejala(id):
    gejala = Gejala.query.get_or_404(id)
    db.session.delete(gejala)
    db.session.commit()
    flash('Gejala berhasil dihapus.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/diagnosa/<int:id>')
def detail_diagnosa(id):
    diagnosa = Diagnosa.query.filter_by(id=id).first()

    all_answers = parse_all_answers(diagnosa.gejala_skoring)
    hasil = compute_hasil(all_answers)

    # Ambil hanya hasil dengan skala paling berat
    tingkat_kelas = {'Ringan': 1, 'Sedang': 2, 'Berat': 3}
    hasil_tertinggi = max(hasil, key=lambda x: tingkat_kelas.get(x['kelas'], 0))

    diagnosa.skala = hasil_tertinggi  # atau simpan hanya hasil_tertinggi['kelas'] saja

    gejala_ids = [g.strip() for g in diagnosa.gejala_terpenuhi.split(',') if g.strip()]
    gejala_nama_list = Gejala.query.filter(Gejala.id.in_(gejala_ids)).all()


    return render_template(
        'admin/detail_diagnosa.html',
        diagnosa=diagnosa,
        gejala_nama_list=gejala_nama_list,
        gejala_ids=gejala_ids,  # string gejala_terpenuhi
    )
