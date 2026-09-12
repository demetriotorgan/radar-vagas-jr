import os, re, time, requests, pandas as pd, duckdb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()
DB = "vagas.duckdb"
CV_FILE = "meu_cv.txt"

# --- NORMALIZAÇÃO DO DIA 08 ---
def normalizar_empresa(nome):
    if not nome or pd.isna(nome):
        return "Não informado"
    n = str(nome).lower().strip()
    n = re.sub(r'\b(ltda|eireli|me|s\.?a\.?|s\/a|brasil|brazil|cosmeticos)\b', '', n)
    n = re.sub(r'[^\w\s]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    palavras = n.split()
    if len(palavras) > 1 and palavras[0] in ['grupo','super','lojas','rede','instituto']:
        # Mantém Instituto + próxima palavra (seu caso Instituto Infnet)
        return ' '.join(palavras[:2]).title()
    return ' '.join(palavras[:2]).title()

def normalizar_url(url):
    if not url or pd.isna(url): return ""
    return str(url).strip().rstrip('/').lower()

def bonus_jr(titulo):
    t = str(titulo).lower()
    return 30 if any(k in t for k in ['jr','junior','trainee','estagio','estágio']) else 0

def main():
    con = duckdb.connect(DB)
    con.execute("""
    CREATE TABLE IF NOT EXISTS vagas(
      id VARCHAR PRIMARY KEY, empresa VARCHAR, empresa_norm VARCHAR,
      careerPageUrl VARCHAR, careerPageUrl_norm VARCHAR,
      titulo VARCHAR, cidade VARCHAR, remoto BOOLEAN, tipo VARCHAR,
      data TIMESTAMP, link VARCHAR, descricao TEXT, score DOUBLE, data_coleta TIMESTAMP
    )""")
    con.execute("CREATE TABLE IF NOT EXISTS vagas_enviadas (id VARCHAR PRIMARY KEY)")

    # Tenta adicionar colunas se banco for antigo
    for col in ["empresa_norm VARCHAR", "careerPageUrl_norm VARCHAR"]:
        try: con.execute(f"ALTER TABLE vagas ADD COLUMN {col}")
        except: pass

    # COLETA
    termos = ["analista de dados jr", "analista de dados junior", "estagio dados", "estágio dados", "trainee dados"]
    todas = []
    for termo in termos:
        print(f"Buscando: {termo}")
        try:
            r = requests.get("https://employability-portal.gupy.io/api/v1/jobs",
                             params={"jobName":termo,"limit":100,"offset":0}, timeout=15)
            todas.extend(r.json().get('data', []))
        except Exception as e:
            print(f"Erro {termo}: {e}")
        time.sleep(1)

    df = pd.DataFrame([{
        "id": j.get('id'), "empresa": j.get('careerPageName'),
        "careerPageUrl": j.get('careerPageUrl'), "titulo": j.get('name'),
        "cidade": j.get('city') or j.get('cityState') or "Remoto",
        "remoto": j.get('isRemoteWork'), "tipo": j.get('workplaceType'),
        "data": j.get('publishedDate'), "link": j.get('careerPageUrl'),
        "descricao": j.get('description')
    } for j in todas]).drop_duplicates(subset=['id'])

    if df.empty:
        print("Nenhuma vaga hoje")
        return

    # FILTRO DIA 02
    cidades_alvo = ['Maringá', 'Londrina', 'Maringa']
    mask = df['cidade'].isin(cidades_alvo) | (df['remoto'] == True) | (df['tipo'].astype(str).str.contains('remote|remoto', case=False, na=False))
    df_f = df[mask].copy()
    print(f"Filtradas: {len(df_f)} de {len(df)}")

    # SCORE DIA 03
    df_f['descricao'] = df_f['descricao'].fillna('')
    df_f['texto_vaga'] = (df_f['titulo'] + " " + df_f['titulo'] + " " + df_f['descricao']).str.lower()

    if not os.path.exists(CV_FILE):
        print(f"{CV_FILE} não encontrado")
        return

    with open(CV_FILE, 'r', encoding='utf-8') as f:
        meu_cv = f.read().lower()

    tfidf = TfidfVectorizer(ngram_range=(1,2))
    mat = tfidf.fit_transform([meu_cv] + df_f['texto_vaga'].tolist())
    scores = cosine_similarity(mat[0:1], mat[1:]).flatten()
    df_f['score'] = (scores * 100).round(1)
    df_f['score_final'] = df_f['score'] + df_f['titulo'].apply(bonus_jr)

    # DIA 08 - NORMALIZAÇÃO
    df_f['empresa_norm'] = df_f['empresa'].apply(normalizar_empresa)
    df_f['careerPageUrl_norm'] = df_f['careerPageUrl'].apply(normalizar_url)

    df_save = df_f[['id','empresa','empresa_norm','careerPageUrl','careerPageUrl_norm','titulo','cidade','remoto','tipo','data','link','descricao','score_final']].rename(columns={'score_final':'score'})

    con.execute("""
    INSERT INTO vagas BY NAME SELECT * FROM df_save
    ON CONFLICT (id) DO UPDATE SET score = EXCLUDED.score, link = EXCLUDED.link, empresa_norm = EXCLUDED.empresa_norm
    """)
    con.execute("UPDATE vagas SET data_coleta = CURRENT_TIMESTAMP WHERE data_coleta IS NULL")
    print(f"Banco com: {con.execute('SELECT COUNT(*) FROM vagas').fetchone()[0]} vagas")

    # DIA 04 - ANTI-SPAM
    df_novas = con.execute("SELECT * FROM vagas WHERE id NOT IN (SELECT id FROM vagas_enviadas) AND score >= 35 ORDER BY score DESC").df()
    print(f"Novas pra enviar: {len(df_novas)}")

    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')

    if not TOKEN or not CHAT_ID:
        print("Sem TELEGRAM_TOKEN/CHAT_ID nos Secrets - pulando envio")
        con.close()
        return

    for _, v in df_novas.iterrows():
        msg = f"🔥 Score {v['score']}% - {v['titulo']}\n\n🏢 {v['empresa_norm']} | 📍 {v['cidade']}\n🔗 {v['link']}"
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})
        if r.status_code == 200:
            con.execute(f"INSERT OR IGNORE INTO vagas_enviadas VALUES ('{v['id']}')")
            print(f"✅ Enviado: {v['titulo'][:50]}")
        else:
            print(f"❌ Erro Telegram: {r.text}")

    con.close()
    print("Dia 08 CONCLUÍDO!")

if __name__ == "__main__":
    main()
