# EvoLLM – Projekto migravimo planas

Pilnas EvoLLM projekto perkėlimo iš vieno serverio į kitą procesas.
Projektas veikia su **Docker Compose**, todėl nereikia rankiniu būdu diegti Python, PostgreSQL, Ollama ar jokių kitų priklausomybių – viską valdo Docker.

---

## 1. Perkeliami failai ir duomenys

### Programinis kodas ir konfigūracija
| Failas / katalogas | Paskirtis |
|---|---|
| `backend/` | Serverinė logika (FastAPI, agentai, servisai) |
| `frontend/` | Grafinė sąsaja (NiceGUI) |
| `Dockerfile.backend`, `Dockerfile.frontend` | Docker image'ų aprašai |
| `docker-compose.yml` | Visų servisų konfigūracija |
| `.env` | Slaptažodžiai, API raktai, DB URL |

### Duomenys (Docker volumes)

Projektas naudoja 3 Docker volumes:

| Volume | Turinys | Ar būtina perkelti? |
|---|---|---|
| `evollm_postgres_data` | Vartotojai, task'ai, dokumentų metaduomenys | **Taip** |
| `evollm_chroma_data` | Vektorinė DB (įkelti dokumentai RAG) | **Taip** |
| `evollm_ollama_data` | LLM modeliai (qwen3:0.6b, qwen3.5:9b) | Ne – atsisiunčiami iš naujo |

---

## 2. Duomenų eksportavimas iš seno serverio

### 2.1 PostgreSQL backup
```bash
docker exec evollm-postgres-1 pg_dump -U postgres evollm > evollm_backup.sql
```

### 2.2 ChromaDB backup
```bash
docker run --rm \
  -v evollm_chroma_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup.tar.gz /data
```

### 2.3 Kodo ir konfigūracijos kopijavimas
```bash
scp -r EvoLLM/ user@new-server:~/EvoLLM/
scp evollm_backup.sql user@new-server:~/
scp chroma_backup.tar.gz user@new-server:~/
```

---

## 3. Diegimas naujoje aplinkoje

### 3.1 Docker diegimas
Naujame serveryje reikia įdiegti tik **Docker**:
```bash
curl -fsSL https://get.docker.com | sh
sudo apt install docker-compose-plugin
```

Visas kitas programas (Python, PostgreSQL, Ollama) Docker sukuria automatiškai iš `docker-compose.yml`.

### 3.2 Konfigūracijos atnaujinimas
Naujame serveryje sukurti `.env` failą:
```env
DATABASE_URL=postgresql://postgres:<slaptazodis>@postgres:5432/evollm
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL_SMALL=qwen3:0.6b
OLLAMA_MODEL_BIG=qwen3.5:9b
CHROMADB_PATH=/app/chroma_data
JWT_SECRET=<stiprus-unikalus-raktas>
JWT_EXPIRE_HOURS=24
TAVILY_API_KEY=<api-raktas>
```

>`JWT_SECRET` turi likti toks pat kaip senajame serveryje – kitaip visi esami vartotojų prisijungimai nustos veikti.

### 3.3 PostgreSQL duomenų atkūrimas
```bash
cd ~/EvoLLM

# Paleisti tik postgres konteinerį
docker compose up -d postgres

# Importuoti duomenis
docker exec -i evollm-postgres-1 psql -U postgres evollm < ~/evollm_backup.sql
```

### 3.4 ChromaDB duomenų atkūrimas
```bash
docker run --rm \
  -v evollm_chroma_data:/data \
  -v $HOME:/backup \
  alpine tar xzf /backup/chroma_backup.tar.gz -C /
```

### 3.5 Projekto paleidimas
```bash
cd ~/EvoLLM
docker compose up --build -d
```

Docker automatiškai:
- Sukuria backend ir frontend image'us iš Dockerfile
- Instaliuoja visas Python priklausomybes (`requirements.txt`)
- Paleidžia PostgreSQL, Ollama, backend ir frontend konteinerius

### 3.6 Ollama modelių atsisiuntimas
```bash
docker exec evollm-ollama-1 ollama pull qwen3:0.6b
docker exec evollm-ollama-1 ollama pull qwen3.5:9b
```

### 3.7 Domeno / URL nustatymas
- Atnaujinti CORS konfigūraciją `backend/main.py` – įrašyti naują domeno adresą į `allow_origins`
- Sukonfigūruoti reverse proxy (nginx), nukreipiant:
  - Frontend → `http://localhost:8080`
  - Backend API → `http://localhost:8000`
- Išduoti SSL sertifikatą (pvz., Let's Encrypt):
  ```bash
  sudo certbot --nginx -d jūsų-domenas.lt
  ```

---

## 4. Migravimo patikrinimo testai

Po sėkmingo diegimo atlikti šiuos patikrinimus:

### 4.1 Sistemos pasiekiamumas
- [ ] Atidaryti programą naršyklėje – atsidaro prisijungimo puslapis
- [ ] Backend health check: `GET /health` grąžina `{"status": "ok"}`
- [ ] Visi konteineriai veikia: `docker compose ps` – visi statusas `running`

### 4.2 Autentikacija
- [ ] Prisijungti su esamu vartotoju (iš backup'o) – sėkmingas prisijungimas
- [ ] Užregistruoti naują vartotoją – sėkminga registracija
- [ ] Bandyti pasiekti `/task/history` be tokeno – gauti `401 Unauthorized`

### 4.3 Duomenų bazė
- [ ] Po prisijungimo matyti ankstesnių task'ų istoriją
- [ ] Sukurti naują task'ą – jis išsaugomas DB ir pasirodo istorijoje
- [ ] Ištrinti task'ą – jis dingsta iš sąrašo

### 4.4 LLM pipeline
- [ ] Sukurti task'ą su paprastu tekstu – pipeline sėkmingai praeina visus 4 agentus (Planner -> Researcher -> Coder -> Reviewer)
- [ ] Atsakymas grąžinamas ir matomas UI

### 4.5 RAG dokumentai
- [ ] Matyti anksčiau įkeltus dokumentus (iš backup'o)
- [ ] Įkelti naują PDF/TXT dokumentą – sėkmingas įkėlimas
- [ ] Sukurti task'ą su įjungtu RAG – sistema naudoja dokumentų turinį
- [ ] Ištrinti dokumentą – jis dingsta iš sąrašo

### 4.6 Veikimo palyginimas
- [ ] Palyginti atsakymų greitį su ankstesniu serveriu
- [ ] Patikrinti konteinerių logus – nėra kritinių klaidų: `docker compose logs --tail=50`
