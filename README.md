# Chatbot FAQ UPA TIK - Server API

Chatbot berbasis AI untuk menjawab pertanyaan seputar layanan UPA TIK menggunakan teknologi Natural Language Processing (NLP).

## Persyaratan Sistem

### Minimum Requirements:
- **Python**: 3.8 atau lebih baru
- **RAM**: Minimal 2GB (4GB direkomendasikan)
- **Storage**: 1GB ruang kosong
- **OS**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+

### Hardware Tambahan (Opsional):
- **GPU**: NVIDIA dengan CUDA untuk performa lebih cepat
- **RAM**: 8GB+ untuk dataset besar

## Instalasi

### 1. download dan extract ZIP file

### 2. Setup Python Environment

#### Windows:
```cmd
# Buat virtual environment
python -m venv chatbot_env

# Aktivasi environment
chatbot_env\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### macOS/Linux:
```bash
# Buat virtual environment
python3 -m venv chatbot_env

# Aktivasi environment
source chatbot_env/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install Dependencies

#### Opsi A: Install Otomatis (Recommended)
```bash
pip install -r requirements.txt
```

#### Opsi B: Install Manual (Jika Opsi A Gagal)
```bash
# Install satu per satu
pip install Flask==2.3.3
pip install Flask-CORS==4.0.0
pip install pandas==2.1.1
pip install numpy==1.24.3
pip install sentence-transformers==2.2.2
pip install scikit-learn==1.3.0

# Install PyTorch (CPU version)
pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2+cpu --index-url https://download.pytorch.org/whl/cpu
```

#### Opsi C: Untuk GPU NVIDIA (Advanced)
```bash
# Jika punya GPU NVIDIA dengan CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Struktur Project

```
CHATBOT FAQ ABCD R.../
│
├── assets/               # File aset (jika ada)
├── frontend/             # File frontend chatbot
│   ├── chatbot.css      # Styling chatbot
│   ├── chatbot.js       # JavaScript chatbot
│   └── index.html       # Halaman utama
│
├── model_cache/         # Cache model AI (dibuat otomatis)
├── chatbot_env/         # Virtual environment (dibuat saat setup)
├── dataset.json         # Dataset pertanyaan-jawaban
├── server.py            # Server API backend
├── requirements.txt     # Dependencies Python
└── README.md           # Panduan ini
```

## ▶ Menjalankan Server

### 1. Aktivasi Environment (Jika Belum)
#### Windows:
```cmd
chatbot_env\Scripts\activate
```

#### macOS/Linux:
```bash
source chatbot_env/bin/activate
```

### 2. Jalankan Server
```bash
python server.py
```

### 3. Server Siap!
```
 ✓ Server berjalan di: http://localhost:5000
 ✓ Chat endpoint: POST /api/chat
 ✓ Health check: GET /health
 ✓ Statistik: GET /api/stats
```

## Testing API

### 1. Test Health Check
```bash
# Windows (PowerShell)
Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET

# macOS/Linux (curl)
curl http://localhost:5000/health
```

### 2. Test Chat
```bash
# Windows (PowerShell)
$body = @{ message = "Lupa password SIAKAD" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/chat" -Method POST -Body $body -ContentType "application/json"

# macOS/Linux (curl)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Lupa password SIAKAD"}'
```

## Endpoints API

### 1. Chat Endpoint
- **URL**: `POST /api/chat`
- **Input**:
  ```json
  {
    "message": "Pertanyaan pengguna"
  }
  ```
- **Output**:
  ```json
  {
    "status": "success",
    "message": "Jawaban chatbot",
    "category": "Kategori",
    "confidence": 0.95,
    "response_time": 0.123,
    "timestamp": "2025-09-10 12:30:45"
  }
  ```

### 2. Health Check
- **URL**: `GET /health`
- **Output**: Status server dan chatbot

### 3. Statistik
- **URL**: `GET /api/stats`
- **Output**: Statistik penggunaan chatbot

## Konfigurasi

### Custom Dataset
Buat file `dataset.json` dengan format:
```json
[
  {
    "kategori": "Akademik",
    "pertanyaan": "Pertanyaan 1?",
    "jawaban": "Jawaban untuk pertanyaan 1"
  },
  {
    "kategori": "Teknis",
    "pertanyaan": "Pertanyaan 2?",
    "jawaban": "Jawaban untuk pertanyaan 2"
  }
]
```

### Environment Variables (Opsional)
```bash
# Set port custom
export FLASK_PORT=8080

# Set mode debug
export FLASK_DEBUG=true
```

## Troubleshooting

### Error: "Model tidak dapat dimuat"
```bash
# Solusi 1: Install ulang sentence-transformers
pip uninstall sentence-transformers
pip install sentence-transformers==2.2.2

# Solusi 2: Clear cache
rm -rf model_cache/
```

### Error: "CUDA out of memory"
```bash
# Paksa pakai CPU
export CUDA_VISIBLE_DEVICES=""
python server.py
```

### Error: "Port already in use"
```bash
# Windows: Kill process di port 5000
netstat -ano | findstr 5000
taskkill /PID [PID_NUMBER] /F

# macOS/Linux: Kill process di port 5000
lsof -ti:5000 | xargs kill -9
```

### Error: "Module not found"
```bash
# Pastikan virtual environment aktif
# Windows:
chatbot_env\Scripts\activate

# macOS/Linux:
source chatbot_env/bin/activate

# Install ulang requirements
pip install -r requirements.txt
```

## Update Dependencies

```bash
# Update semua packages ke versi terbaru
pip install --upgrade -r requirements.txt

# Update package tertentu
pip install --upgrade Flask sentence-transformers
```

## Logs dan Monitoring

### Lokasi Logs
- **Console**: Real-time logs ditampilkan di terminal
- **Level**: INFO, WARNING, ERROR

### Monitoring Performa
- Akses `/api/stats` untuk melihat statistik
- Monitor response time dan confidence score
- Track success rate chatbot


## Tips Penggunaan

1. **Pertama kali running**: Tunggu model download
2. **Chat tidak respon**: Cek apakah server backend sudah jalan
3. **Dataset custom**: Edit file `dataset.json` sesuai kebutuhan
4. **Performance**: Tutup aplikasi lain jika RAM terbatas
5. **Browser**: Gunakan Chrome untuk performa terbaik

## Support

Jika mengalami masalah:
1. Cek log error di terminal
2. Pastikan semua dependencies terinstal
3. Cek versi Python (minimal 3.8)
4. Restart server dan coba lagi
---

**Dibuat dengan ❤️ untuk UPA TIK**