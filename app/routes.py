from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime
from app.models import Admin as User, Gejala, Penyakit, RuleGejala, Diagnosa, Solusi
from app.inference import forward_chaining, backward_chaining
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    session.clear()
    return render_template('main.html')  

@bp.route('/data-diri', methods=['GET', 'POST'])
def data_diri():
    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form.get('nama')
        umur = request.form.get('umur')
        anak_ke = request.form.get('anak_ke')
        usia_kehamilan = request.form.get('usia_kehamilan')

        # Simpan di session
        session['pasien_data'] = {
            'nama': nama,
            'umur': umur,
            'anak_ke': anak_ke,
            'usia_kehamilan': usia_kehamilan
        }

        # Redirect ke halaman forward chaining (misal step pertama = 0)
        return redirect(url_for('main.forward_step', step=0))

    # Kalau GET, tampilkan form
    return render_template('data_diri.html')

@bp.route('/diri', methods=['GET', 'POST'])
def diri():
    if request.method == 'POST' and 'nama' in request.form:
        # POST dari form data diri
        session['pasien_data'] = {
            'nama': request.form.get('nama'),
            'umur': request.form.get('umur'),
            'anak_ke': request.form.get('anak_ke'),
            'usia_kehamilan': request.form.get('usia_kehamilan'),
        }
        penyakit_id = session.get('penyakit_id')
        return redirect(url_for('main.confirm_step', penyakit_id=penyakit_id, step=0))

    elif request.method == 'POST' and 'penyakit_id' in request.form:
        # POST dari form pilih penyakit
        session['penyakit_id'] = request.form['penyakit_id']
        return render_template('diri.html')

    elif request.method == 'GET' and 'penyakit_id' in request.args:
        # GET dengan query string ?penyakit_id=P01
        session['penyakit_id'] = request.args.get('penyakit_id')
        return render_template('diri.html')

    return redirect(url_for('main.pilih_penyakit'))  # fallback


@bp.route('/pilih-penyakit')
def pilih_penyakit():
    penyakit = Penyakit.query.all()
    return render_template('pilih_penyakit.html', penyakit=penyakit)

@bp.route('/diagnose', methods=['POST'])
def diagnose():
    selected = request.form.getlist('gejala')
    results = forward_chaining(db.session, selected)
    for res in results:
        db.session.add(Diagnosa(
            tanggal=datetime.utcnow(),
            penyakit_id=res['penyakit_id'],
            skor_total=res['skor'],
            gejala_terpenuhi=','.join(res['gejala'])
        ))
    db.session.commit()
    return render_template('result.html', results=results)

# Backward Chaining
@bp.route('/confirm/<penyakit_id>/step/<int:step>', methods=['GET', 'POST'])
def confirm_step(penyakit_id, step):
    if 'pasien_data' not in session:
        return redirect(url_for('main.diri'))

    # Ambil data penyakit & aturan-aturannya
    penyakit = Penyakit.query.get_or_404(penyakit_id)
    rule_items = sorted(penyakit.rules, key=lambda x: x.bobot, reverse=True)
    total = len(rule_items)

    # Cegah step out of range
    if step >= total:
        return redirect(url_for('main.confirm_step', penyakit_id=penyakit_id, step=0))

    # Inisialisasi jawaban
    if 'backward_answers' not in session:
        session['backward_answers'] = {}

    if request.method == 'POST':
        # Ambil nilai jawaban
        try:
            nilai_user = int(request.form.get('jawab', 0))
        except ValueError:
            nilai_user = 0

        answers = session.get('backward_answers', {})
        current_gej_id = rule_items[step].gejala_id
        answers[current_gej_id] = nilai_user
        session['backward_answers'] = answers
        session.modified = True

        # Hitung skor saat ini
        skor_saat_ini = 0.0
        for r in rule_items[:step + 1]:
            gid = r.gejala_id
            if gid in answers:
                skor_saat_ini += answers[gid] * r.bobot

        # Hitung sisa skor maksimum
        sisa_skor_maks = sum(r.bobot * 3 for r in rule_items[step + 1:])

        # Ambil threshold
        threshold = penyakit.threshold

        # Evaluasi early termination
        if skor_saat_ini + sisa_skor_maks < threshold:
            gejala_terjawab = [gid for gid, val in answers.items() if val > 0]
            session.pop('backward_answers', None)

            pasien = session.get('pasien_data')
            return render_template('confirm_result.html', result={
                'penyakit_id': penyakit.id,
                'penyakit_nama': penyakit.nama,
                'status': 'tidak terpenuhi',
                'skor': round(skor_saat_ini, 2),
                'persentase': None,
                'kelas': None,
                'gejala_terjawab': gejala_terjawab
            }, 
            nama=pasien.get('nama'),
            umur=int(pasien.get('umur')) if pasien.get('umur') else None,
            anak_ke=int(pasien.get('anak_ke')) if pasien.get('anak_ke') else None,
            usia_kehamilan=int(pasien.get('usia_kehamilan')) if pasien.get('usia_kehamilan') else None)

        # Lanjut ke pertanyaan berikutnya
        if step + 1 < total:
            return redirect(url_for('main.confirm_step', penyakit_id=penyakit_id, step=step + 1))

        # Hitung final jika sudah pertanyaan terakhir
        all_answers = session.get('backward_answers', {})
        skor_aktual_final = 0.0
        skor_maks_final = 0.0

        for r in rule_items:
            gid = r.gejala_id
            if all_answers.get(gid, 0) > 0:
                skor_aktual_final += all_answers[gid] * r.bobot
            skor_maks_final += 3 * r.bobot

        persentase = (skor_aktual_final / skor_maks_final) * 100 if skor_maks_final > 0 else 0.0

        if persentase < 50:
            kelas = 'Ringan'
        elif persentase < 75:
            kelas = 'Sedang'
        else:
            kelas = 'Berat'

        gejala_terjawab = [gid for gid, val in all_answers.items() if val > 0]
        session.pop('backward_answers', None)
        gejala_skoring = ', '.join([f"{gid}({all_answers.get(gid, 0)})" for gid in gejala_terjawab])

        pasien = session.get('pasien_data')

        diagnosa = Diagnosa(
            tanggal=datetime.utcnow(),
            penyakit_id=penyakit.id,
            skor_total=round(skor_aktual_final, 2),
            gejala_terpenuhi=",".join([str(gid) for gid in gejala_terjawab]),
            gejala_skoring=gejala_skoring,
            nama=pasien.get('nama'),
            umur=int(pasien.get('umur')) if pasien.get('umur') else None,
            anak_ke=int(pasien.get('anak_ke')) if pasien.get('anak_ke') else None,
            usia_kehamilan=int(pasien.get('usia_kehamilan')) if pasien.get('usia_kehamilan') else None
        )
        db.session.add(diagnosa)
        db.session.commit()

        solusi_list = Solusi.query.filter_by(
            penyakit_id=penyakit.id,
            skala=kelas
        ).all()

        return render_template('confirm_result.html', result={
            'penyakit_id': penyakit.id,
            'penyakit_nama': penyakit.nama,
            'status': 'terpenuhi',
            'skor': round(skor_aktual_final, 2),
            'persentase': round(persentase, 2),
            'kelas': kelas,
            'gejala_terjawab': gejala_terjawab,
            'solusi_list': solusi_list
        })

    # GET request → tampilkan pertanyaan skala
    gejala = rule_items[step].gejala
    return render_template('confirm_step.html', penyakit=penyakit, gejala=gejala, step=step + 1, total=total)


# Fungsi bantu hitung hasil per penyakit
def compute_hasil(all_answers, rule_bobot, threshold_penyakit):
    hasil_per_penyakit = []
    for pid, batas in threshold_penyakit.items():
        skor_aktual = 0.0
        skor_maks   = 0.0

        if pid not in rule_bobot:
            continue

        for gid, bobot in rule_bobot[pid].items():
            if gid in all_answers:
                skor_aktual += all_answers[gid] * bobot
            skor_maks += 3 * bobot

        if skor_aktual <= 0:
            continue

        persentase = (skor_aktual / skor_maks) * 100 if skor_maks > 0 else 0.0

        if persentase < 50:
            kelas = 'Ringan'
        elif persentase < 75:
            kelas = 'Sedang'
        else:
            kelas = 'Berat'

        nama_penyakit = Penyakit.query.filter_by(id=pid).first().nama

        hasil_per_penyakit.append({
            'penyakit_nama': nama_penyakit,
            'persentase': round(persentase, 2),
            'kelas': kelas
        })

    return hasil_per_penyakit

@bp.route('/forward/<int:step>', methods=['GET', 'POST'])
def forward_step(step):
    # Cek apakah data diri sudah ada di session
    if 'pasien_data' not in session:
        return redirect(url_for('main.data_diri'))
    
    gejala_list = Gejala.query.all()
    total = len(gejala_list)

    if step >= total:
        all_answers = session.get('fwd_answers', {})
        penyakit_list = Penyakit.query.all()

        # Gunakan key string untuk ID penyakit
        threshold_penyakit = {str(p.id): p.threshold for p in penyakit_list}

        aturan_list = RuleGejala.query.all()
        rule_bobot = {}
        for aturan in aturan_list:
            pid_str = str(aturan.penyakit_id)
            gid_str = str(aturan.gejala_id)
            if pid_str not in rule_bobot:
                rule_bobot[pid_str] = {}
            rule_bobot[pid_str][gid_str] = aturan.bobot

        hasil_per_penyakit = compute_hasil(all_answers, rule_bobot, threshold_penyakit)

        # Tambahkan solusi ke hasil
        for res in hasil_per_penyakit:
            pid = Penyakit.query.filter_by(nama=res['penyakit_nama']).first().id
            solusi_list = Solusi.query.filter(
                Solusi.penyakit_id == pid,
                Solusi.skala.ilike(res['kelas'])
            ).all()
            res['solusi_list'] = solusi_list

        pasien = session.get('pasien_data')
        if pasien and hasil_per_penyakit:
            terbaik = max(hasil_per_penyakit, key=lambda x: x['persentase'])
            pid_terbaik = Penyakit.query.filter_by(nama=terbaik['penyakit_nama']).first().id

            gejala_terpilih = []
            for gid_str, val in all_answers.items():
                # Ganti get(int()) dengan filter_by(kode=)
                gej = Gejala.query.filter_by(id=gid_str).first()
                if gej:
                    gejala_terpilih.append({
                        'id': gej.id,
                        'skor': val
                    })

            skor_total = sum([g['skor'] for g in gejala_terpilih])
            gejala_terpenuhi = ', '.join([g['id'] for g in gejala_terpilih])
            gejala_skoring = ', '.join([f"{g['id']}({g['skor']})" for g in gejala_terpilih])

            diagnosa = Diagnosa(
                tanggal=datetime.utcnow(),
                penyakit_id=pid_terbaik,
                skor_total=skor_total,
                gejala_terpenuhi=gejala_terpenuhi,
                gejala_skoring=gejala_skoring,
                nama=pasien.get('nama'),
                umur=int(pasien.get('umur')) if pasien.get('umur') else None,
                anak_ke=int(pasien.get('anak_ke')) if pasien.get('anak_ke') else None,
                usia_kehamilan=int(pasien.get('usia_kehamilan')) if pasien.get('usia_kehamilan') else None
            )
            db.session.add(diagnosa)
            db.session.commit()

        session.pop('fwd_answers', None)
        session.pop('pasien_data', None)
        return render_template('result.html', results=hasil_per_penyakit, terbaik=terbaik)

    # Jika masih dalam range gejala
    penyakit_list = Penyakit.query.all()
    threshold_penyakit = {str(p.id): p.threshold for p in penyakit_list}

    aturan_list = RuleGejala.query.all()
    rule_bobot = {}
    for aturan in aturan_list:
        pid_str = str(aturan.penyakit_id)
        gid_str = str(aturan.gejala_id)
        if pid_str not in rule_bobot:
            rule_bobot[pid_str] = {}
        rule_bobot[pid_str][gid_str] = aturan.bobot

    pasien = session.get('pasien_data')
    if not pasien:
        return redirect(url_for('main.data_diri'))

    if 'fwd_answers' not in session:
        session['fwd_answers'] = {}

    if request.method == 'POST':
        answers = session['fwd_answers']
        try:
            nilai_user = int(request.form.get('jawab', 0))
        except ValueError:
            nilai_user = 0

        current_gej = gejala_list[step]
        # Simpan dengan key kode gejala, jika id bukan integer
        answers[str(current_gej.id)] = nilai_user
        session['fwd_answers'] = answers
        session.modified = True

        skor_actual = {pid: 0.0 for pid in threshold_penyakit}
        sisa_maks = {pid: 0.0 for pid in threshold_penyakit}

        # Hitung skor aktual berdasarkan jawaban (gunakan string key)
        for pid in skor_actual.keys():
            for gid, bobot in rule_bobot.get(pid, {}).items():
                if gid in answers:
                    skor_actual[pid] += answers[gid] * bobot

        # Hitung sisa maksimal untuk gejala yang belum dijawab
        for pid in sisa_maks.keys():
            for gid, bobot in rule_bobot.get(pid, {}).items():
                if gid not in answers:
                    sisa_maks[pid] += 3 * bobot  # Asumsi maksimal skor jawaban 3

        # Cek apakah bisa skip pertanyaan berikutnya
        can_skip = True
        for pid, threshold in threshold_penyakit.items():
            if skor_actual.get(pid, 0) + sisa_maks.get(pid, 0) >= threshold:
                can_skip = False
                break

        if can_skip:
            return redirect(url_for('main.forward_step', step=total))

        return redirect(url_for('main.forward_step', step=step+1))

    # Jika GET, tampilkan pertanyaan gejala saat ini
    gejala = gejala_list[step]
    return render_template(
        'forward_step.html',
        gejala=gejala,
        step=step+1,
        total=total
    )
