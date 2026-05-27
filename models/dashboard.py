from database.conexao_supabase import get_supabase_client, get_tenant_id
from datetime import datetime, timedelta
from collections import defaultdict

STATUS_ORDER = ['solicitada', 'em_triagem', 'aguardando_aprovacao', 'aprovada', 'aprovada_ressalvas', 'em_recrutamento', 'publicada', 'rascunho', 'encerrada']
STATUS_LABELS = {
    'solicitada': 'Solicitada', 'em_triagem': 'Em Triagem',
    'aguardando_aprovacao': 'Aguard. Aprovação', 'aprovada': 'Aprovada',
    'aprovada_ressalvas': 'Aprovada c/ Ressalvas', 'em_recrutamento': 'Em Recrutamento',
    'publicada': 'Publicada', 'rascunho': 'Rascunho', 'encerrada': 'Encerrada',
}


def _client():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None, None
    return get_supabase_client(), tenant_id


def get_kpis():
    client, tenant_id = _client()
    if not client:
        return {}

    vagas = client.table('vagas').select('id,status_vaga').eq('tenant_id', tenant_id).execute()
    vagas_data = vagas.data or []

    vagas_ativas = sum(1 for v in vagas_data if v.get('status_vaga') in ('publicada', 'em_recrutamento'))
    vagas_encerradas = sum(1 for v in vagas_data if v.get('status_vaga') == 'encerrada')
    total_vagas = len(vagas_data)

    candidaturas = client.table('candidaturas').select('id,nota,status').eq('tenant_id', tenant_id).execute()
    cand_data = candidaturas.data or []
    total_candidatos = len(cand_data)

    notas = []
    for c in cand_data:
        n = c.get('nota')
        if n is not None:
            try: notas.append(float(n))
            except: pass
    score_medio = round(sum(notas) / len(notas), 1) if notas else 0
    avaliacoes_ia = sum(1 for c in cand_data if c.get('nota') is not None)

    contratados = sum(1 for c in cand_data if c.get('status') == 'Contratado')
    taxa_conversao = round(contratados / total_candidatos * 100, 1) if total_candidatos > 0 else 0

    return {
        'vagas_ativas': vagas_ativas,
        'vagas_encerradas': vagas_encerradas,
        'total_vagas': total_vagas,
        'total_candidatos': total_candidatos,
        'score_medio': score_medio,
        'avaliacoes_ia': avaliacoes_ia,
        'taxa_conversao': taxa_conversao,
        'contratados': contratados,
    }


def get_vagas_por_status():
    client, tenant_id = _client()
    if not client:
        return {}

    result = client.table('vagas').select('status_vaga').eq('tenant_id', tenant_id).execute()
    data = result.data or []

    counts = defaultdict(int)
    for v in data:
        counts[v.get('status_vaga', 'rascunho')] += 1

    labels = []
    values = []
    colors = {
        'solicitada': '#f59e0b', 'em_triagem': '#3b82f6',
        'aguardando_aprovacao': '#8b5cf6', 'aprovada': '#10b981',
        'aprovada_ressalvas': '#f59e0b', 'em_recrutamento': '#06b6d4',
        'publicada': '#10b981', 'rascunho': '#94a3b8', 'encerrada': '#ef4444',
    }

    for s in STATUS_ORDER:
        if counts[s] > 0:
            labels.append(STATUS_LABELS.get(s, s))
            values.append(counts[s])
    return {'labels': labels, 'values': values, 'colors': [colors.get(s, '#94a3b8') for s in STATUS_ORDER if counts[s] > 0]}


def get_candidatos_por_status():
    client, tenant_id = _client()
    if not client:
        return {}

    result = client.table('candidaturas').select('status').eq('tenant_id', tenant_id).execute()
    data = result.data or []

    counts = defaultdict(int)
    for c in data:
        s = c.get('status') or 'Pendente'
        counts[s] += 1

    labels = []
    values = []
    colors_list = []
    palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

    for i, (status, count) in enumerate(sorted(counts.items(), key=lambda x: -x[1])):
        labels.append(status)
        values.append(count)
        colors_list.append(palette[i % len(palette)])

    return {'labels': labels, 'values': values, 'colors': colors_list}


def get_notas_distribuicao():
    client, tenant_id = _client()
    if not client:
        return {}

    result = client.table('candidaturas').select('nota').eq('tenant_id', tenant_id).execute()
    data = result.data or []

    buckets = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for c in data:
        n = c.get('nota')
        if n is None:
            continue
        n = float(n)
        if n <= 20: buckets['0-20'] += 1
        elif n <= 40: buckets['21-40'] += 1
        elif n <= 60: buckets['41-60'] += 1
        elif n <= 80: buckets['61-80'] += 1
        else: buckets['81-100'] += 1

    return {'labels': list(buckets.keys()), 'values': list(buckets.values())}


def get_vagas_por_mes():
    client, tenant_id = _client()
    if not client:
        return {}

    result = client.table('vagas').select('created_at').eq('tenant_id', tenant_id).order('created_at', desc=False).execute()
    data = result.data or []

    from dateutil import parser
    months = defaultdict(int)
    for v in data:
        try:
            dt = parser.isoparse(v['created_at'])
            key = dt.strftime('%b/%y')
            months[key] += 1
        except:
            pass

    return {'labels': list(months.keys()), 'values': list(months.values())}


def get_recentes():
    client, tenant_id = _client()
    if not client:
        return [], [], []

    vagas = client.table('vagas').select('id,titulo,status_vaga,user_created,created_at').eq('tenant_id', tenant_id).order('created_at', desc=True).limit(5).execute()
    candidaturas = client.table('candidaturas').select('id,status,nota,created_at,vaga_id').eq('tenant_id', tenant_id).order('created_at', desc=True).limit(5).execute()

    vaga_ids = list(set(c.get('vaga_id') for c in candidaturas.data if c.get('vaga_id')))
    if vaga_ids:
        vagas_map_res = client.table('vagas').select('id,titulo').eq('tenant_id', tenant_id).in_('id', vaga_ids).execute()
        vagas_map = {v['id']: v['titulo'] for v in vagas_map_res.data or []}
    else:
        vagas_map = {}

    recent_cands = []
    for c in candidaturas.data or []:
        recent_cands.append({
            'id': c['id'],
            'status': c.get('status', 'Pendente'),
            'nota': c.get('nota'),
            'data': c.get('created_at', '')[:10],
            'vaga_titulo': vagas_map.get(c.get('vaga_id'), '—'),
        })

    return vagas.data or [], recent_cands