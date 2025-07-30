from app import db
from datetime import datetime
from passlib.hash import scrypt

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self, username, password):
        self.username = username
        self.password = scrypt.hash(password)

class Gejala(db.Model):
    __tablename__ = 'gejala'
    id = db.Column(db.String(5), primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    rules = db.relationship('RuleGejala', back_populates='gejala')

    def __repr__(self):
        return f"<Gejala {self.id}: {self.nama}>"

class Penyakit(db.Model):
    __tablename__ = 'penyakit'
    id = db.Column(db.String(5), primary_key=True)
    nama = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text)
    threshold = db.Column(db.Float, nullable=False)
    rules = db.relationship('RuleGejala', back_populates='penyakit')

    def __repr__(self):
        return f"<Penyakit {self.id}: {self.nama}>"

class RuleGejala(db.Model):
    __tablename__ = 'rule_gejala'
    # id = db.Column(db.String(5), primary_key=True)
    penyakit_id = db.Column(db.String(5), db.ForeignKey('penyakit.id'), primary_key=True)
    gejala_id = db.Column(db.String(5), db.ForeignKey('gejala.id'), primary_key=True)
    bobot = db.Column(db.Float, nullable=False)
    penyakit = db.relationship('Penyakit', back_populates='rules')
    gejala = db.relationship('Gejala', back_populates='rules')

    def __repr__(self):
        return f"<RuleGejala {self.penyakit_id}-{self.gejala_id}: {self.bobot}>"

class Diagnosa(db.Model):
    __tablename__ = 'diagnosa'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    penyakit_id = db.Column(db.String(5), db.ForeignKey('penyakit.id'), nullable=False)
    skor_total = db.Column(db.Float, nullable=False)
    gejala_terpenuhi = db.Column(db.Text, nullable=False)
    gejala_skoring = db.Column(db.Text, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    umur = db.Column(db.Integer, nullable=False)
    anak_ke = db.Column(db.Integer, nullable=False)
    usia_kehamilan = db.Column(db.Integer, nullable=False)

    # user = db.relationship('User')
    penyakit = db.relationship('Penyakit')

    def __repr__(self):
        return f"<Diagnosa {self.id}: {self.penyakit_id} ({self.skor_total})>"


class Solusi(db.Model):
    __tablename__ = 'solusi'
    id = db.Column(db.Integer, primary_key=True)
    penyakit_id = db.Column(db.String(5), db.ForeignKey('penyakit.id'), nullable=False)
    skala = db.Column(db.String(10), nullable=False)  
    solusi = db.Column(db.Text, nullable=False)      
    penyakit = db.relationship('Penyakit', backref=db.backref('solusi_list', lazy=True))
