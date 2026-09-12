Radar de Vagas Jr - Londrina / Maringá

Coleta inteligente de vagas da Gupy, com score de compatibilidade com meu CV e alerta anti-spam no Telegram.
[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![DuckDB](https://img.shields.io/badge/DB-DuckDB-yellow)]()
[![Status](https://img.shields.io/badge/Status-Dia%2008%2F11-green)]()

### 1. O Problema
A aplicação Radar de Vagas Jr surgiu de uma necessidade especial de conhecer e aprender sobre as necessidades que as empresas de tecnologia da região de Maringá/Londrina possuem. Os dados estão espalhadas na Gupy, com títulos diferentes (`Jr`, `Estágio`, `Trainee`) e 90% não são pra Londrina/Maringá ou são spam de vaga repetida no Telegram. 

### 2. A Solução
A ideia foi criar um Bot que coleta 5 termos de busca, filtra por cidade/remoto, calcula compatibilidade com meu CV usando TF-IDF (cosine similarity) + bônus Jr, e só envia no Telegram vagas novas com score > 35%.

### 3. Stack
- **Coleta:** `requests` + Gupy API
- **Banco:** `DuckDB` (`vagas` e `vagas_enviadas` pra anti-spam)
- **Inteligência:** `Scikit-learn (TfidfVectorizer)` + Regex
- **Alerta:** Telegram Bot API
- **Análise:** Pandas + Matplotlib
- **Dashboard:** Streamlit
- Automatizar com GitHub Actions rodando 8h/8h

### 4. Insights possíveis que a aplicação fornece:
- **Top Empresa:** Melhores empresas que oferecem vagas do tipo Jr, Estágio e Trainee
- **Banco De Vagas:** Banco de vagas para diversos tipo de análise
- **Top Skills Jr na região:** Python, SQL, Excel, Power BI
- **Salário Médio Jr:** Calculo de salário médio de top vagas

### 5. Como Rodar
```bash
pip install -r requirements.txt
# coloque seu meu_cv.txt na pasta
# configure TELEGRAM_TOKEN e CHAT_ID no .env
python main.py
