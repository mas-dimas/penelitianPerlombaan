# 🤖 Bot Telegram Generator Proposal Perlombaan

Bot ini secara otomatis mengisi template Word proposal perlombaan berdasarkan data yang Anda kirim via Telegram.

---

## 📁 Struktur File

```
proposal_bot/
├── bot.py                  ← Kode utama bot
├── template_proposal.docx  ← Template Word (JANGAN DIHAPUS)
├── requirements.txt        ← Daftar library Python
├── Procfile                ← Untuk deploy di Railway
├── .env.example            ← Contoh file environment variable
└── README.md               ← Panduan ini
```

---

## 🚀 Cara Setup (Pertama Kali)

### Langkah 1 — Buat Bot Telegram

1. Buka Telegram, cari **@BotFather**
2. Kirim `/newbot`
3. Ikuti instruksinya (beri nama dan username bot)
4. Salin **token** yang diberikan (contoh: `123456:ABCdef...`)

---

### Langkah 2 — Pilih Cara Menjalankan Bot

#### ✅ Opsi A: Railway (Gratis, Online 24 jam, DIREKOMENDASIKAN)

1. Daftar di [railway.app](https://railway.app) (bisa login pakai GitHub)
2. Buat project baru → pilih **"Deploy from GitHub repo"**
3. Upload semua file ke GitHub (atau bisa pakai [GitHub Desktop](https://desktop.github.com/))
4. Di Railway, buka tab **Variables** → tambahkan:
   ```
   BOT_TOKEN = token_anda_disini
   ```
   Opsional — supaya setiap proposal yang dibuat juga otomatis dikirim salinannya ke Anda sebagai admin/pemilik bot, tambahkan juga:
   ```
   ADMIN_CHAT_ID = chat_id_anda_disini
   ```
   Dapatkan chat ID Anda dengan chat ke bot `@userinfobot` di Telegram. Bisa diisi lebih dari satu ID, pisahkan dengan koma.
5. Klik **Deploy** — bot langsung online!

> 💡 Railway gratis untuk pemakaian ringan (~500 jam/bulan). Cukup untuk bot yang tidak digunakan terus-menerus.

---

#### ✅ Opsi B: Laptop/PC Lokal

**Prasyarat:** Python 3.10+ terinstal

```bash
# 1. Masuk ke folder bot
cd proposal_bot

# 2. Install library
pip install -r requirements.txt

# 3. Jalankan bot
# Windows:
set BOT_TOKEN=token_anda_disini && python bot.py

# Mac/Linux:
BOT_TOKEN=token_anda_disini python bot.py
```

> ⚠️ Bot hanya berjalan selama laptop/PC menyala dan program aktif.

---

## 💬 Cara Pakai Bot

### Perintah yang tersedia

| Perintah | Fungsi |
|----------|--------|
| `/start` | Sapa bot dan lihat info awal |
| `/buat` | Tampilkan format pengisian |
| `/bantuan` | Panduan lengkap |

### Format pengisian (mode wizard, dijawab satu per satu)

Bot berjalan sebagai **wizard**: setiap pertanyaan dijawab satu per satu (bukan satu pesan berisi semua field). Alur singkatnya:

1. Nama Lomba
2. Tanggal Surat
3. Nomor Surat
4. Tanggal Pelaksanaan Lomba
5. Tempat Lomba
6. Penyelenggara
7. Biaya Pendaftaran
8. Link Poster / Sumber
8b. **Foto Poster** — kirim gambar poster lomba langsung sebagai foto (bukan file dokumen). Foto ini akan menggantikan gambar poster contoh di dalam dokumen secara otomatis (rasio gambar disesuaikan agar tidak gepeng/melar). Ketik `-` untuk melewati langkah ini jika belum punya poster.
9. Tahapan Lomba (nama, tanggal, tempat — diulang sesuai jumlah tahapan)
10. Kelompok Peserta, tiap kelompok berisi:
    - Nama Kelompok
    - Peserta (nama, kelas, bidang lomba, **dosen pembimbing akademik**, dan **dosen pembimbing tugas akhir** — pertanyaan dosen TA hanya muncul otomatis bila kelas peserta terdeteksi tingkat 4, misalnya diawali "IV")
    - Dosen Pembimbing **Lomba** untuk kelompok tersebut (berbeda dari dosen akademik/TA di atas — ini mengisi tabel "Dosen Pembimbing" terpisah)

Bot akan membalas dengan file `.docx` yang sudah terisi otomatis! 🎉

---

## 🔧 Kustomisasi Template

Jika ingin mengganti template Word:

1. Edit file `template_proposal.docx` sesuai kebutuhan
2. **Pastikan teks placeholder berikut tetap ada** (dipakai bot untuk penggantian):
   - `18 Juni 2026` → akan diganti tanggal surat
   - `Data, AI & Policy APAC Hackathon: Financial Health Frontiers` → nama lomba
   - `19 Mei s.d. 6 November 2026` → tanggal lomba
   - `Chulangkorn University` → penyelenggara
   - `Tidak dipungut biaya` → biaya pendaftaran
   - `APAC HACKATHON 2026` → nama lomba pendek (di heading tabel)
   - Nama peserta: `Satria Tegar Bimantara`, `Intan Bella Safira Putri Dewi`, `Muhammad Ghani Nurramdhan`, `David Sam Limbong`
   - `R. Budiarto Hadiprakoso, MMSI.` → dosen pembimbing
   - `https://www.apru.org/...` → link poster

---

## ❓ FAQ

**Q: Apakah bot bisa dipakai banyak orang sekaligus?**
A: Ya, bot mendukung banyak pengguna secara bersamaan.

**Q: Apakah dokumen yang dibuat tersimpan di server?**
A: Tidak. File langsung dikirim ke Telegram dan dihapus dari server setelah itu.

**Q: Bagaimana jika peserta kurang dari 4 orang?**
A: Cukup isi sesuai jumlah peserta (pisah koma). Maksimal 4 peserta.

**Q: Apakah bisa diubah untuk 1 kelompok lebih?**
A: Perlu modifikasi kode di `bot.py`. Hubungi developer.
