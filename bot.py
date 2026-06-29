"""
Bot Telegram - Generator Proposal Perlombaan
Cara pakai: Kirim /buat lalu isi semua field sesuai format
"""

import os
import re
import shutil
import zipfile
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Konfigurasi ───────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "MASUKKAN_TOKEN_BOT_DISINI")
TEMPLATE_PATH = "template_proposal.docx"

# ─── Field yang bisa diubah ────────────────────────────────────────────────────
# Label resmi (untuk tampilan /bantuan)
FIELD_LABELS = {
    "nomor_surat":       "Nomor Surat",
    "tanggal_surat":     "Tanggal Surat",
    "nama_lomba":        "Nama Lomba",
    "nama_lomba_pendek": "Nama Lomba Pendek",
    "tanggal_lomba":     "Tanggal Lomba",
    "tempat_lomba":      "Tempat Lomba",
    "penyelenggara":     "Penyelenggara",
    "biaya":             "Biaya Pendaftaran",
    "nama_peserta":      "Nama Peserta",
    "kelas_peserta":     "Kelas Peserta",
    "dosen_pembimbing":  "Dosen Pembimbing",
    "link_poster":       "Link Poster",
}

# Semua alias yang diterima saat parsing (lowercase)
# Satu key internal bisa punya banyak alias
FIELD_ALIASES: dict[str, list[str]] = {
    "nomor_surat":       ["nomor surat", "nomor"],
    "tanggal_surat":     ["tanggal surat", "tanggal"],
    "nama_lomba":        ["nama lomba"],
    "nama_lomba_pendek": ["nama lomba pendek", "nama pendek"],
    "tanggal_lomba":     ["tanggal lomba", "tanggal pelaksanaan"],
    "tempat_lomba":      ["tempat lomba", "tempat"],
    "penyelenggara":     ["penyelenggara"],
    "biaya":             ["biaya pendaftaran", "biaya"],
    "nama_peserta":      ["nama peserta", "peserta"],
    "kelas_peserta":     ["kelas peserta", "kelas"],
    "dosen_pembimbing":  ["dosen pembimbing", "dosen"],
    "link_poster":       ["link poster", "link poster / sumber", "poster", "sumber", "link"],
}

FORMAT_CONTOH = """
*Format Pengisian:*

```
Nomor Surat: 002/SKT/2025
Tanggal Surat: 1 Juli 2025
Nama Lomba: National Programming Contest 2025
Nama Lomba Pendek: NPC 2025
Tanggal Lomba: 10 s.d. 15 Agustus 2025
Tempat Lomba: Daring
Penyelenggara: Universitas Gadjah Mada
Biaya Pendaftaran: Tidak dipungut biaya
Nama Peserta: Budi Santoso, Ani Rahayu, Citra Dewi
Kelas Peserta: III RPLK, III RPLK, III RPLK
Dosen Pembimbing: Dr. Ir. Hendra Wijaya, M.T.
Link Poster: https://example.com/poster
```

Kirim data di atas (boleh copy-paste lalu ubah isinya) dan bot akan langsung membuatkan proposalnya! 📄
"""

# ─── Parsing input user ────────────────────────────────────────────────────────
def parse_input(text: str) -> tuple:
    """Parsing teks multi-baris jadi dict field, toleran terhadap variasi label."""
    data = {}
    # Kumpulkan baris; nilai bisa multi-baris (mis. nama dosen sangat panjang)
    lines = text.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" in line:
            key_raw, _, value_raw = line.partition(":")
            key_clean = key_raw.strip().lower()
            value_clean = value_raw.strip()
            # Cocokkan ke salah satu alias
            matched_key = None
            for internal_key, aliases in FIELD_ALIASES.items():
                if key_clean in aliases:
                    matched_key = internal_key
                    break
            if matched_key:
                data[matched_key] = value_clean
        i += 1

    # Cek apakah semua field wajib ada
    required = [k for k in FIELD_LABELS if k != "nama_lomba_pendek"]
    missing = [FIELD_LABELS[k] for k in required if k not in data]
    if missing:
        return None, missing
    # Nama lomba pendek default ke nama_lomba jika tidak diisi
    if "nama_lomba_pendek" not in data:
        data["nama_lomba_pendek"] = data.get("nama_lomba", "")
    return data, []

# ─── Pengganti teks di XML ─────────────────────────────────────────────────────
def xml_replace(content: str, old: str, new: str) -> str:
    """Replace teks biasa dalam XML (escape karakter khusus)."""
    def escape_xml(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return content.replace(escape_xml(old), escape_xml(new))

def xml_replace_raw(content: str, old: str, new: str) -> str:
    """Replace nilai yang sudah di-escape di XML."""
    old_esc = old.replace("&", "&amp;")
    new_esc = new.replace("&", "&amp;")
    return content.replace(old_esc, new_esc)

# ─── Generate baris peserta ────────────────────────────────────────────────────
def build_peserta_rows(peserta_list: list, kelas_list: list, dosen: str) -> str:
    """Buat baris tabel peserta dalam XML OOXML."""
    rows = []
    for i, (nama, kelas) in enumerate(zip(peserta_list, kelas_list), start=1):
        row = f"""        <w:tr>
          <w:tc><w:p><w:r><w:t>{i}.</w:t></w:r></w:p></w:tc>
          <w:tc><w:p><w:r><w:t>{nama.strip()}</w:t></w:r></w:p></w:tc>
          <w:tc><w:p><w:r><w:t>{kelas.strip()}</w:t></w:r></w:p></w:tc>
          <w:tc><w:p><w:r><w:t>Lomba</w:t></w:r></w:p></w:tc>
          <w:tc><w:p><w:r><w:t>Diizinkan ({dosen})</w:t></w:r></w:p></w:tc>
        </w:tr>"""
        rows.append(row)
    return "\n".join(rows)

# ─── Proses generate dokumen ────────────────────────────────────────────────────
def generate_proposal(data: dict, output_path: str) -> bool:
    """Salin template, lalu replace semua placeholder dengan data user."""
    try:
        shutil.copy(TEMPLATE_PATH, output_path)

        peserta_list = [p.strip() for p in data["nama_peserta"].split(",")]
        kelas_list   = [k.strip() for k in data["kelas_peserta"].split(",")]
        dosen        = data["dosen_pembimbing"]

        # Ekstrak docx (zip)
        extract_dir = output_path + "_extracted"
        with zipfile.ZipFile(output_path, "r") as z:
            z.extractall(extract_dir)

        doc_xml_path = os.path.join(extract_dir, "word", "document.xml")
        with open(doc_xml_path, "r", encoding="utf-8") as f:
            content = f.read()

        # ── Tanggal surat (muncul banyak tempat) ──
        content = content.replace("Bogor, 18 Juni 2026", f"Bogor, {data['tanggal_surat']}")
        content = content.replace("18 Juni 2026", data["tanggal_surat"])

        # ── Nama lomba panjang ──
        nama_lama    = "Data, AI &amp; Policy APAC Hackathon: Financial Health Frontiers"
        nama_lama_2  = "Data, AI &amp; Policy APAC Hackathon: Financial Health"
        nama_baru    = data["nama_lomba"].replace("&", "&amp;")

        # Nama lomba di "Hal" (baris surat + body)
        content = content.replace(
            "Lomba 2026 </w:t></w:r><w:r><w:rPr>",
            f"{data['nama_lomba_pendek']} </w:t></w:r><w:r><w:rPr>",
        )
        content = content.replace(nama_lama, nama_baru)
        content = content.replace(nama_lama_2, nama_baru)

        # ── Detail lomba (Lampiran I) ──
        content = content.replace("19 Mei s.d. 6 November 2026", data["tanggal_lomba"])
        content = content.replace("Daring dan Luring", data["tempat_lomba"])
        content = content.replace("Chulangkorn </w:t></w:r>", f"{data['penyelenggara']}</w:t></w:r>")
        content = content.replace("Tidak dipungut biaya", data["biaya"])

        # ── Nama lomba pendek di heading tabel ──
        content = content.replace("APAC HACKATHON 2026", data["nama_lomba_pendek"].upper())

        # ── Peserta: ganti nama satu per satu ──
        nama_lama_list = [
            "Satria Tegar Bimantara",
            "Intan Bella Safira Putri Dewi",
            "Muhammad Ghani Nurramdhan",
            "David Sam Limbong",
        ]
        for i, nama_baru_peserta in enumerate(peserta_list[:4]):
            if i < len(nama_lama_list):
                content = content.replace(nama_lama_list[i], nama_baru_peserta)
            # Kelas
        kelas_lama = "III RPLK"
        for i, kl in enumerate(kelas_list[:4]):
            content = content.replace(kelas_lama, kl, 1)  # replace satu per satu

        # ── Dosen pembimbing ──
        content = content.replace("R. Budiarto Hadiprakoso, MMSI.", dosen)

        # ── Nomor surat (kosong di template, isi dengan nomor baru) ──
        # Di template nomor surat berupa cell kosong setelah "Nomor : "
        # Pattern XML: setelah tag Nomor ada cell kosong → kita insert nomor
        content = content.replace(
            "<w:t>Nomor</w:t></w:r></w:p></w:tc>\n          <w:tc><w:p><w:r><w:t>:</w:t>",
            f"<w:t>Nomor</w:t></w:r></w:p></w:tc>\n          <w:tc><w:p><w:r><w:t>:</w:t>",
        )
        # Isi field nomor di Lampiran (setelah "Nomor\t:")
        content = re.sub(
            r'(<w:t>Nomor</w:t>.*?<w:t xml:space="preserve">\t:\s*</w:t></w:r>)(\s*</w:p>)',
            lambda m: m.group(1) + f'<w:r><w:t xml:space="preserve"> {data["nomor_surat"]}</w:t></w:r>' + m.group(2),
            content,
            flags=re.DOTALL
        )

        # ── Link poster ──
        content = content.replace(
            "https://www.apru.org/event/2026-hackathon-financial-health-frontiers//",
            data["link_poster"]
        )

        # Tulis kembali
        with open(doc_xml_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Repack ke docx
        os.remove(output_path)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname   = os.path.relpath(file_path, extract_dir)
                    zout.write(file_path, arcname)

        shutil.rmtree(extract_dir)
        return True

    except Exception as e:
        logger.error(f"Error generate_proposal: {e}", exc_info=True)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        return False

# ─── Handler perintah /start ───────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Saya bot generator *Proposal Perlombaan*.\n\n"
        "Ketik /buat untuk melihat format pengisian dan membuat proposal.\n"
        "Ketik /bantuan untuk melihat panduan lengkap.",
        parse_mode="Markdown"
    )

# ─── Handler perintah /buat ────────────────────────────────────────────────────
async def cmd_buat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FORMAT_CONTOH, parse_mode="Markdown")

# ─── Handler perintah /bantuan ─────────────────────────────────────────────────
async def cmd_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Panduan Penggunaan Bot*\n\n"
        "1️⃣ Ketik /buat untuk melihat format\n"
        "2️⃣ Copy format yang muncul\n"
        "3️⃣ Ubah isinya sesuai lomba yang diikuti\n"
        "4️⃣ Kirim ke bot — proposal .docx akan langsung dikirim balik!\n\n"
        "*Field yang bisa diubah:*\n" +
        "\n".join(f"• {label}" for label in FIELD_LABELS.values()) +
        "\n\n_Nama Peserta & Kelas Peserta dipisah koma, urutan harus sama._",
        parse_mode="Markdown"
    )

# ─── Handler pesan biasa (isi form) ────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    # Hanya proses jika ada minimal satu label yang dikenal (cek semua alias)
    text_lower = text.lower()
    all_aliases = [alias for aliases in FIELD_ALIASES.values() for alias in aliases]
    has_label = any(f"{alias}:" in text_lower for alias in all_aliases)
    if not has_label:
        await update.message.reply_text(
            "Tidak mengenali format. Ketik /buat untuk melihat format pengisian. 😊"
        )
        return

    data, missing = parse_input(text)
    if missing:
        await update.message.reply_text(
            f"⚠️ Field berikut belum diisi:\n" + "\n".join(f"• {m}" for m in missing) +
            "\n\nSilakan lengkapi dan kirim ulang. Ketik /buat untuk melihat format."
        )
        return

    await update.message.reply_text("⏳ Sedang membuat proposal, mohon tunggu sebentar...")

    # Buat nama file output unik
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", data["nama_lomba"])[:30]
    output_path = f"proposal_{safe_name}_{ts}.docx"

    success = generate_proposal(data, output_path)

    if success and os.path.exists(output_path):
        with open(output_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=output_path,
                caption=(
                    f"✅ *Proposal berhasil dibuat!*\n\n"
                    f"📌 Lomba: {data['nama_lomba']}\n"
                    f"📅 Tanggal surat: {data['tanggal_surat']}\n"
                    f"🔢 Nomor: {data['nomor_surat']}"
                ),
                parse_mode="Markdown"
            )
        os.remove(output_path)
    else:
        await update.message.reply_text(
            "❌ Gagal membuat proposal. Cek log bot atau hubungi admin."
        )

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    if BOT_TOKEN == "MASUKKAN_TOKEN_BOT_DISINI":
        print("⚠️  Harap isi BOT_TOKEN di file bot.py atau set environment variable BOT_TOKEN")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("buat",    cmd_buat))
    app.add_handler(CommandHandler("bantuan", cmd_bantuan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot berjalan... Tekan Ctrl+C untuk berhenti.")
    app.run_polling()

if __name__ == "__main__":
    main()
