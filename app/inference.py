from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Penyakit, RuleGejala


def forward_chaining(session: Session, gejala_user: List[str]) -> List[Dict]:
   
    results = []
    penyakit_list = session.query(Penyakit).all()
    for penyakit in penyakit_list:
        rule_items = session.query(RuleGejala).filter_by(penyakit_id=penyakit.id).all()
        total_bobot = sum(item.bobot for item in rule_items)
        match_items = [item for item in rule_items if item.gejala_id in gejala_user]
        total_match = sum(item.bobot for item in match_items)
        if total_match >= penyakit.threshold:
            results.append({
                'penyakit_id': penyakit.id,
                'nama': penyakit.nama,
                'skor': total_match,
                'gejala': [item.gejala_id for item in match_items]
            })
    return sorted(results, key=lambda x: x['skor'], reverse=True)


def backward_chaining(session: Session, target: str, answers: Dict[str, bool]) -> Dict:
  
    penyakit = session.query(Penyakit).get(target)
    rule_items = (
        session.query(RuleGejala)
        .filter_by(penyakit_id=target)
        .order_by(RuleGejala.bobot.desc())
        .all()
    )
    skor = 0.0
    gejala_ya = []
    for item in rule_items:
        if answers.get(item.gejala_id, False):
            skor += item.bobot
            gejala_ya.append(item.gejala_id)
        if skor >= penyakit.threshold:
            break
    status = 'terdiagnosis' if skor >= penyakit.threshold else 'tidak terdiagnosis'
    return {
        'penyakit_id': penyakit.id,
        'nama': penyakit.nama,
        'skor': skor,
        'gejala_terjawab': gejala_ya,
        'status': status
    }
