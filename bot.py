"""
Bot Telegram — Generator Proposal Perlombaan (Wizard Mode)
Alur: pengguna menjawab satu per satu, bot memandu langkah demi langkah.
"""

import os, re, shutil, zipfile, copy, logging
from datetime import datetime
from lxml import etree
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN     = os.getenv("BOT_TOKEN", "MASUKKAN_TOKEN_BOT_DISINI")
TEMPLATE_PATH = "template_proposal.docx"

# ── State ConversationHandler ──────────────────────────────────────────────────
(
    S_NAMA_LOMBA,
    S_TANGGAL_SURAT,
    S_NOMOR_SURAT,
    S_TANGGAL_LOMBA,
    S_TEMPAT_LOMBA,
    S_PENYELENGGARA,
    S_BIAYA,
    S_LINK_POSTER,
    S_JML_TAHAPAN,
    S_TAHAPAN,
    S_JML_KELOMPOK,
    S_NAMA_KELOMPOK,
    S_JML_PESERTA,
    S_PESERTA,
    S_DOSEN,
    S_KONFIRMASI,
) = range(16)

TEMPAT_OPTIONS = [["Daring", "Luring", "Daring dan Luring"]]

# ══════════════════════════════════════════════════════════════════════════════
# HELPER — kirim pertanyaan dengan keyboard opsional
# ══════════════════════════════════════════════════════════════════════════════
async def ask(update, text, keyboard=None, tip=None):
    full = text
    if tip:
        full += f"\n\n💡 _Contoh: {tip}_"
    if keyboard:
        await update.message.reply_text(
            full,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
    else:
        await update.message.reply_text(
            full,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )

def progress(step, total):
    filled = round(step / total * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {step}/{total}"

# ══════════════════════════════════════════════════════════════════════════════
# /start  &  /buat
# ══════════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Saya bot *Generator Proposal Perlombaan*.\n\n"
        "Ketik /buat untuk mulai membuat proposal baru.\n"
        "Ketik /batal kapan saja untuk membatalkan.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

async def cmd_buat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await ask(
        update,
        "📝 *Langkah 1/15 — Nama Lomba*\n" + progress(1, 15) + "\n\nKetik nama lengkap lomba yang diikuti:",
        tip="Compfest 18 2026",
    )
    return S_NAMA_LOMBA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Nama Lomba
# ══════════════════════════════════════════════════════════════════════════════
async def get_nama_lomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nama_lomba"] = update.message.text.strip()
    await ask(
        update,
        "📅 *Langkah 2/15 — Tanggal Surat*\n" + progress(2, 15) + "\n\nMasukkan tanggal surat hari ini:",
        tip="2 Juli 2026",
    )
    return S_TANGGAL_SURAT

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Tanggal Surat
# ══════════════════════════════════════════════════════════════════════════════
async def get_tanggal_surat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tanggal_surat"] = update.message.text.strip()
    await ask(
        update,
        "🔢 *Langkah 3/15 — Nomor Surat*\n" + progress(3, 15) + "\n\nMasukkan nomor surat (ketik `-` jika belum ada):",
        tip="002/SKT/VII/2026",
    )
    return S_NOMOR_SURAT

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Nomor Surat
# ══════════════════════════════════════════════════════════════════════════════
async def get_nomor_surat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nomor_surat"] = update.message.text.strip()
    await ask(
        update,
        "🗓️ *Langkah 4/15 — Tanggal Pelaksanaan Lomba*\n" + progress(4, 15) + "\n\nMasukkan tanggal lomba berlangsung:",
        tip="17 Juni s.d. 27 September 2026",
    )
    return S_TANGGAL_LOMBA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Tanggal Lomba
# ══════════════════════════════════════════════════════════════════════════════
async def get_tanggal_lomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tanggal_lomba"] = update.message.text.strip()
    await ask(
        update,
        "📍 *Langkah 5/15 — Tempat Lomba*\n" + progress(5, 15) + "\n\nPilih tempat pelaksanaan:",
        keyboard=TEMPAT_OPTIONS,
    )
    return S_TEMPAT_LOMBA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Tempat Lomba
# ══════════════════════════════════════════════════════════════════════════════
async def get_tempat_lomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tempat_lomba"] = update.message.text.strip()
    await ask(
        update,
        "🏛️ *Langkah 6/15 — Penyelenggara*\n" + progress(6, 15) + "\n\nSiapa penyelenggara lomba ini?",
        tip="Fakultas Ilmu Komputer, Universitas Indonesia",
    )
    return S_PENYELENGGARA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Penyelenggara
# ══════════════════════════════════════════════════════════════════════════════
async def get_penyelenggara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["penyelenggara"] = update.message.text.strip()
    await ask(
        update,
        "💰 *Langkah 7/15 — Biaya Pendaftaran*\n" + progress(7, 15) + "\n\nBerapa biaya pendaftaran?",
        keyboard=[["Tidak dipungut biaya"], ["Rp 60.000"], ["Rp 100.000"], ["Rp 150.000"]],
        tip="Rp 60.000",
    )
    return S_BIAYA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Biaya
# ══════════════════════════════════════════════════════════════════════════════
async def get_biaya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["biaya"] = update.message.text.strip()
    await ask(
        update,
        "🔗 *Langkah 8/15 — Link Poster / Sumber*\n" + progress(8, 15) + "\n\nMasukkan URL sumber informasi lomba:",
        tip="https://compfest.id/",
    )
    return S_LINK_POSTER

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Link Poster
# ══════════════════════════════════════════════════════════════════════════════
async def get_link_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link_poster"] = update.message.text.strip()
    await ask(
        update,
        "📋 *Langkah 9/15 — Jumlah Tahapan Lomba*\n" + progress(9, 15) + "\n\nAda berapa tahapan dalam lomba ini?",
        keyboard=[["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]],
    )
    return S_JML_TAHAPAN

# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — Jumlah Tahapan
# ══════════════════════════════════════════════════════════════════════════════
async def get_jml_tahapan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 1 or int(txt) > 15:
        await update.message.reply_text("⚠️ Masukkan angka antara 1–15.")
        return S_JML_TAHAPAN
    n = int(txt)
    context.user_data["jml_tahapan"] = n
    context.user_data["tahapan"] = []
    context.user_data["_tahapan_idx"] = 0
    await ask(
        update,
        f"📌 *Tahapan 1/{n} — Nama Tahap*\n\nKetik nama tahapan ke-1:",
        tip="Pendaftaran Batch 1",
    )
    return S_TAHAPAN

# ══════════════════════════════════════════════════════════════════════════════
# STEP 10 — Isi Tahapan (loop)
# Setiap tahapan: nama → tanggal → tempat  (3 sub-step per tahapan)
# Sub-state ditandai di context.user_data["_tahapan_sub"]: 0=nama,1=tgl,2=tmpt
# ══════════════════════════════════════════════════════════════════════════════
async def get_tahapan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud      = context.user_data
    n       = ud["jml_tahapan"]
    idx     = ud["_tahapan_idx"]          # tahapan ke-berapa (0-based)
    sub     = ud.get("_tahapan_sub", 0)   # 0=nama, 1=tanggal, 2=tempat
    current = ud.get("_tahapan_current", {})

    if sub == 0:
        current["nama"] = update.message.text.strip()
        ud["_tahapan_current"] = current
        ud["_tahapan_sub"] = 1
        await ask(
            update,
            f"📅 *Tahapan {idx+1}/{n} — Tanggal*\n\nKapan tahapan _{current['nama']}_ berlangsung?",
            tip="17 Juni s.d. 9 Juli 2026",
        )
        return S_TAHAPAN

    elif sub == 1:
        current["tanggal"] = update.message.text.strip()
        ud["_tahapan_current"] = current
        ud["_tahapan_sub"] = 2
        await ask(
            update,
            f"📍 *Tahapan {idx+1}/{n} — Tempat Pelaksanaan*\n\nPilih tempat tahapan _{current['nama']}_:",
            keyboard=TEMPAT_OPTIONS,
        )
        return S_TAHAPAN

    else:  # sub == 2
        current["tempat"] = update.message.text.strip()
        ud["tahapan"].append(dict(current))
        ud["_tahapan_current"] = {}
        ud["_tahapan_sub"] = 0
        ud["_tahapan_idx"] = idx + 1

        if idx + 1 < n:
            await ask(
                update,
                f"📌 *Tahapan {idx+2}/{n} — Nama Tahap*\n\nKetik nama tahapan ke-{idx+2}:",
                tip="Final",
            )
            return S_TAHAPAN
        else:
            # Selesai semua tahapan → lanjut ke kelompok
            await ask(
                update,
                "👥 *Langkah 11/15 — Jumlah Kelompok*\n" + progress(11, 15) +
                "\n\nAda berapa kelompok peserta?",
                keyboard=[["1", "2", "3"], ["4", "5", "6"]],
            )
            return S_JML_KELOMPOK

# ══════════════════════════════════════════════════════════════════════════════
# STEP 11 — Jumlah Kelompok
# ══════════════════════════════════════════════════════════════════════════════
async def get_jml_kelompok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 1 or int(txt) > 10:
        await update.message.reply_text("⚠️ Masukkan angka antara 1–10.")
        return S_JML_KELOMPOK
    n = int(txt)
    context.user_data["jml_kelompok"] = n
    context.user_data["kelompok"] = []
    context.user_data["_kelompok_idx"] = 0
    await ask(
        update,
        f"✏️ *Kelompok 1/{n} — Nama Kelompok*\n\nKetik nama kelompok ke-1:",
        tip="Kelompok 1  atau  Tim CTF",
    )
    return S_NAMA_KELOMPOK

# ══════════════════════════════════════════════════════════════════════════════
# STEP 12 — Nama Kelompok
# ══════════════════════════════════════════════════════════════════════════════
async def get_nama_kelompok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud  = context.user_data
    idx = ud["_kelompok_idx"]
    n   = ud["jml_kelompok"]

    # Simpan nama kelompok ke slot sementara
    ud["_kelompok_nama_sementara"] = update.message.text.strip()

    await ask(
        update,
        f"👤 *Kelompok {idx+1}/{n} — Jumlah Peserta*\n\nAda berapa peserta di kelompok _{ud['_kelompok_nama_sementara']}_?",
        keyboard=[["1", "2", "3"], ["4", "5"]],
    )
    return S_JML_PESERTA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 13 — Jumlah Peserta per Kelompok
# ══════════════════════════════════════════════════════════════════════════════
async def get_jml_peserta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 1 or int(txt) > 10:
        await update.message.reply_text("⚠️ Masukkan angka 1–10.")
        return S_JML_PESERTA
    ud  = context.user_data
    idx = ud["_kelompok_idx"]
    n   = ud["jml_kelompok"]
    np  = int(txt)
    ud["_peserta_total"]   = np
    ud["_peserta_idx"]     = 0
    ud["_peserta_sub"]     = 0   # 0=nama,1=kelas,2=bidang
    ud["_peserta_list"]    = []
    nama_klp = ud["_kelompok_nama_sementara"]
    await ask(
        update,
        f"👤 *{nama_klp} — Peserta 1/{np}: Nama*\n\nKetik nama peserta ke-1:",
        tip="Davis Virgiawan",
    )
    return S_PESERTA

# ══════════════════════════════════════════════════════════════════════════════
# STEP 14 — Isi Peserta (loop: nama → kelas → bidang)
# ══════════════════════════════════════════════════════════════════════════════
async def get_peserta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud       = context.user_data
    pidx     = ud["_peserta_idx"]
    ptotal   = ud["_peserta_total"]
    sub      = ud["_peserta_sub"]
    kidx     = ud["_kelompok_idx"]
    ktotal   = ud["jml_kelompok"]
    nama_klp = ud["_kelompok_nama_sementara"]
    cur      = ud.get("_peserta_current", {})

    if sub == 0:
        cur["nama"] = update.message.text.strip()
        ud["_peserta_current"] = cur
        ud["_peserta_sub"] = 1
        await ask(
            update,
            f"🏫 *{nama_klp} — Peserta {pidx+1}/{ptotal}: Kelas*\n\nKetik kelas _{cur['nama']}_:",
            tip="IV RPKK",
        )
        return S_PESERTA

    elif sub == 1:
        cur["kelas"] = update.message.text.strip()
        ud["_peserta_current"] = cur
        ud["_peserta_sub"] = 2
        await ask(
            update,
            f"🎯 *{nama_klp} — Peserta {pidx+1}/{ptotal}: Bidang Lomba*\n\nKetik bidang yang diikuti _{cur['nama']}_:",
            tip="Capture The Flag",
        )
        return S_PESERTA

    else:  # sub == 2
        cur["bidang"] = update.message.text.strip()
        ud["_peserta_list"].append(dict(cur))
        ud["_peserta_current"] = {}
        ud["_peserta_sub"] = 0
        ud["_peserta_idx"] = pidx + 1

        if pidx + 1 < ptotal:
            await ask(
                update,
                f"👤 *{nama_klp} — Peserta {pidx+2}/{ptotal}: Nama*\n\nKetik nama peserta ke-{pidx+2}:",
                tip="Gede Gangga Widiagung",
            )
            return S_PESERTA
        else:
            # Selesai peserta di kelompok ini → tanya dosen
            ud["_dosen_kelompok_target"] = kidx
            await ask(
                update,
                f"👨‍🏫 *{nama_klp} — Dosen Pembimbing*\n\nSiapa dosen pembimbing untuk kelompok ini?\n_(pisah koma jika lebih dari satu)_",
                tip="Dr. Hendra Wijaya, M.T.",
            )
            return S_DOSEN

# ══════════════════════════════════════════════════════════════════════════════
# STEP 15 — Dosen per Kelompok
# ══════════════════════════════════════════════════════════════════════════════
async def get_dosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud    = context.user_data
    kidx  = ud["_kelompok_idx"]
    ktotal = ud["jml_kelompok"]
    nama_klp = ud["_kelompok_nama_sementara"]
    dosen = update.message.text.strip()

    # Simpan kelompok lengkap
    ud["kelompok"].append({
        "nama":    nama_klp,
        "peserta": ud["_peserta_list"],
        "dosen":   dosen,
    })
    ud["_kelompok_idx"] = kidx + 1

    if kidx + 1 < ktotal:
        await ask(
            update,
            f"✏️ *Kelompok {kidx+2}/{ktotal} — Nama Kelompok*\n\nKetik nama kelompok ke-{kidx+2}:",
            tip="Kelompok 2",
        )
        return S_NAMA_KELOMPOK
    else:
        # Semua kelompok selesai → konfirmasi
        return await tampilkan_konfirmasi(update, context)

# ══════════════════════════════════════════════════════════════════════════════
# KONFIRMASI — tampilkan ringkasan sebelum generate
# ══════════════════════════════════════════════════════════════════════════════
async def tampilkan_konfirmasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    lines = [
        "✅ *Ringkasan Data Proposal*\n",
        f"📌 *Nama Lomba:* {ud['nama_lomba']}",
        f"📅 *Tanggal Surat:* {ud['tanggal_surat']}",
        f"🔢 *Nomor Surat:* {ud['nomor_surat']}",
        f"🗓️ *Tanggal Lomba:* {ud['tanggal_lomba']}",
        f"📍 *Tempat:* {ud['tempat_lomba']}",
        f"🏛️ *Penyelenggara:* {ud['penyelenggara']}",
        f"💰 *Biaya:* {ud['biaya']}",
        f"🔗 *Link:* {ud['link_poster']}",
        f"\n📋 *Tahapan ({ud['jml_tahapan']}):*",
    ]
    for i, t in enumerate(ud["tahapan"], 1):
        lines.append(f"  {i}. {t['nama']} | {t['tanggal']} | {t['tempat']}")
    lines.append(f"\n👥 *Kelompok ({ud['jml_kelompok']}):*")
    for klp in ud["kelompok"]:
        lines.append(f"  🔹 *{klp['nama']}* — Dosen: {klp['dosen']}")
        for j, p in enumerate(klp["peserta"], 1):
            lines.append(f"      {j}. {p['nama']} ({p['kelas']}) — {p['bidang']}")

    lines.append("\n\nApakah data sudah benar?")
    await ask(
        update,
        "\n".join(lines),
        keyboard=[["✅ Ya, buat proposal!"], ["❌ Ulangi dari awal"]],
    )
    return S_KONFIRMASI

# ══════════════════════════════════════════════════════════════════════════════
# KONFIRMASI — handler pilihan
# ══════════════════════════════════════════════════════════════════════════════
async def get_konfirmasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if "Ulangi" in txt or "❌" in txt:
        context.user_data.clear()
        await update.message.reply_text(
            "🔄 Data dihapus. Ketik /buat untuk mulai dari awal.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "⏳ Sedang membuat proposal...",
        reply_markup=ReplyKeyboardRemove(),
    )
    ud = context.user_data
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", ud["nama_lomba"])[:25]
    out  = f"proposal_{safe}_{ts}.docx"

    ok = generate_proposal(ud, out)
    if ok and os.path.exists(out):
        with open(out, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=out,
                caption=(
                    f"✅ *Proposal berhasil dibuat!*\n"
                    f"📌 {ud['nama_lomba']}\n"
                    f"📅 {ud['tanggal_surat']}"
                ),
                parse_mode="Markdown",
            )
        os.remove(out)
    else:
        await update.message.reply_text("❌ Gagal membuat proposal. Cek log bot.")

    context.user_data.clear()
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════════════
# /batal
# ══════════════════════════════════════════════════════════════════════════════
async def cmd_batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Pembuatan proposal dibatalkan. Ketik /buat untuk memulai lagi.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════════════
# GENERATE DOCX
# ══════════════════════════════════════════════════════════════════════════════
NS  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W   = f"{{{NS}}}"

def txt_of(elem):
    return "".join(t.text or "" for t in elem.iter(f"{W}t"))

def set_txt(run, new_text):
    """Ganti teks semua <w:t> dalam satu run, pertahankan styling."""
    ts = run.findall(f"{W}t")
    if not ts:
        return
    ts[0].text = new_text
    if len(new_text) > 0:
        ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for t in ts[1:]:
        t.getparent().remove(t)

def para_text(para):
    return "".join(t.text or "" for t in para.iter(f"{W}t"))

def is_yellow(elem):
    for hi in elem.iter(f"{W}highlight"):
        if hi.get(f"{W}val") == "yellow":
            return True
    return False

def clone_row(row):
    return copy.deepcopy(row)

def replace_in_para(para, old, new):
    """Replace teks di seluruh paragraf (gabungkan semua run dulu)."""
    full = para_text(para)
    if old not in full:
        return
    new_full = full.replace(old, new)
    runs = para.findall(f".//{W}r")
    if not runs:
        return
    # Simpan semua teks di run pertama, hapus run lainnya
    rPr = runs[0].find(f"{W}rPr")
    for r in runs:
        for t in r.findall(f"{W}t"):
            r.remove(t)
    # Tambah w:t baru ke run pertama
    t_elem = etree.SubElement(runs[0], f"{W}t")
    t_elem.text = new_full
    t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    # Hapus run lain (tapi jaga rPr run pertama)
    parent = runs[0].getparent()
    for r in runs[1:]:
        if r in list(parent):
            parent.remove(r)

def generate_proposal(ud: dict, output_path: str) -> bool:
    try:
        shutil.copy(TEMPLATE_PATH, output_path)
        exdir = output_path + "_ex"
        with zipfile.ZipFile(output_path, "r") as z:
            z.extractall(exdir)

        doc_path = os.path.join(exdir, "word", "document.xml")
        tree = etree.parse(doc_path)
        root = tree.getroot()
        body = root.find(f"{W}body")

        nama_lomba   = ud["nama_lomba"]
        tgl_surat    = ud["tanggal_surat"]
        nomor_surat  = ud["nomor_surat"]
        tgl_lomba    = ud["tanggal_lomba"]
        tempat_lomba = ud["tempat_lomba"]
        penyeleng    = ud["penyelenggara"]
        biaya        = ud["biaya"]
        link_poster  = ud["link_poster"]
        tahapan      = ud["tahapan"]
        kelompok     = ud["kelompok"]

        # ── 1. Semua occurrences NAMA_LOMBA & tanggal surat ─────────────────
        for para in body.iter(f"{W}p"):
            full = para_text(para)
            if "NAMA_LOMBA" in full:
                replace_in_para(para, "NAMA_LOMBA", nama_lomba)
            if "DD MM YY" in full:
                replace_in_para(para, "DD MM YY", tgl_surat)
            if "Bogor, DD MM" in para_text(para):
                replace_in_para(para, "Bogor, DD MM", f"Bogor, {tgl_surat.split()[0]} {tgl_surat.split()[1] if len(tgl_surat.split())>1 else ''}")

        # Re-parse setelah modifikasi paragraf bebas
        full_txt_replace(doc_path, tree, {
            "NAMA_LOMBA":                              nama_lomba,
            "DD MM YY":                                tgl_surat,
            "17 Juni s.d. 27 September 2026":          tgl_lomba,
            "Daring dan Luring":                       tempat_lomba,
            "Fakultas Ilmu Komputer Universitas Indonesia": penyeleng,
            "Rp 60.000":                               biaya,
            "https://compfest.id/":                    link_poster,
        })

        # Re-parse setelah full_txt_replace
        tree = etree.parse(doc_path)
        root = tree.getroot()
        body = root.find(f"{W}body")

        # ── 2. Nomor Surat (cell kosong di tabel header) ────────────────────
        for tr in body.iter(f"{W}tr"):
            cells = tr.findall(f".//{W}tc")
            for i, tc in enumerate(cells):
                if "Nomor" in txt_of(tc) and i + 2 < len(cells):
                    val_cell = cells[i + 2]
                    for para in val_cell.findall(f".//{W}p"):
                        replace_in_para(para, para_text(para), nomor_surat)
                    break

        # ── 3. Tabel TAHAPAN — hapus baris lama, insert baris baru ──────────
        # Cari tabel yang headernya "No. | Tahap | Tanggal | Pelaksanaan"
        tahapan_tbl = None
        for tbl in body.iter(f"{W}tbl"):
            rows = tbl.findall(f"{W}tr")
            if rows:
                hdr = txt_of(rows[0])
                if "Tahap" in hdr and "Tanggal" in hdr:
                    tahapan_tbl = tbl
                    break

        if tahapan_tbl is not None:  # noqa
            rows = tahapan_tbl.findall(f"{W}tr")
            # Simpan baris header (rows[0]) dan satu baris contoh (rows[1])
            hdr_row     = rows[0]
            sample_row  = rows[1] if len(rows) > 1 else rows[0]
            # Hapus semua baris non-header
            for r in rows[1:]:
                tahapan_tbl.remove(r)
            # Insert baris baru untuk setiap tahapan
            for i, thn in enumerate(tahapan):
                new_row = clone_row(sample_row)
                cells   = new_row.findall(f".//{W}tc")
                # Kolom: No | Tahap | Tanggal | Pelaksanaan
                for para in cells[0].iter(f"{W}p"):
                    replace_in_para(para, para_text(para), f"{i+1}.")
                for para in cells[1].iter(f"{W}p"):
                    replace_in_para(para, para_text(para), thn["nama"])
                for para in cells[2].iter(f"{W}p"):
                    replace_in_para(para, para_text(para), thn["tanggal"])
                for para in cells[3].iter(f"{W}p"):
                    replace_in_para(para, para_text(para), thn["tempat"])
                tahapan_tbl.append(new_row)

        # ── 4. Tabel PESERTA — hapus baris lama, insert per kelompok ─────────
        peserta_tbl = None
        for tbl in body.iter(f"{W}tbl"):
            rows = tbl.findall(f"{W}tr")
            if rows:
                hdr = txt_of(rows[0])
                if "Nama" in hdr and "Kelas" in hdr and "Bidang" in hdr:
                    peserta_tbl = tbl
                    break

        if peserta_tbl is not None:
            rows = peserta_tbl.findall(f"{W}tr")
            hdr_row        = rows[0]
            sample_klp_row = rows[1]  if len(rows) > 1 else rows[0]  # baris "Kelompok X"
            sample_pes_row = rows[2]  if len(rows) > 2 else rows[0]  # baris peserta
            for r in rows[1:]:
                peserta_tbl.remove(r)

            for klp in kelompok:
                # Baris header kelompok (merge 5 kolom)
                new_klp = clone_row(sample_klp_row)
                for para in new_klp.iter(f"{W}p"):
                    if para_text(para).strip():
                        replace_in_para(para, para_text(para), klp["nama"])
                        break
                peserta_tbl.append(new_klp)

                # Baris per peserta
                for j, p in enumerate(klp["peserta"]):
                    new_pes = clone_row(sample_pes_row)
                    pcells  = new_pes.findall(f".//{W}tc")
                    if len(pcells) >= 5:
                        for para in pcells[0].iter(f"{W}p"):
                            replace_in_para(para, para_text(para), f"{j+1}.")
                        for para in pcells[1].iter(f"{W}p"):
                            replace_in_para(para, para_text(para), p["nama"])
                        for para in pcells[2].iter(f"{W}p"):
                            replace_in_para(para, para_text(para), p["kelas"])
                        for para in pcells[3].iter(f"{W}p"):
                            replace_in_para(para, para_text(para), p["bidang"])
                        for para in pcells[4].iter(f"{W}p"):
                            replace_in_para(para, para_text(para), f"Diizinkan ({klp['dosen']})")
                    peserta_tbl.append(new_pes)

        # ── 5. Tabel DOSEN PEMBIMBING ────────────────────────────────────────
        dosen_tbl = None
        for tbl in body.iter(f"{W}tbl"):
            rows = tbl.findall(f"{W}tr")
            if rows:
                hdr = txt_of(rows[0])
                if "Dosen Pembimbing" in hdr and "Nama Kelompok" in hdr:
                    dosen_tbl = tbl
                    break

        if dosen_tbl is not None:
            rows = dosen_tbl.findall(f"{W}tr")
            hdr_row    = rows[0]
            sample_row = rows[1] if len(rows) > 1 else rows[0]
            for r in rows[1:]:
                dosen_tbl.remove(r)
            for i, klp in enumerate(kelompok):
                new_row = clone_row(sample_row)
                dcells  = new_row.findall(f".//{W}tc")
                if len(dcells) >= 3:
                    for para in dcells[0].iter(f"{W}p"):
                        replace_in_para(para, para_text(para), f"{i+1}.")
                    for para in dcells[1].iter(f"{W}p"):
                        replace_in_para(para, para_text(para), klp["nama"])
                    for para in dcells[2].iter(f"{W}p"):
                        replace_in_para(para, para_text(para), klp["dosen"])
                dosen_tbl.append(new_row)

        # ── Simpan & repack ──────────────────────────────────────────────────
        tree.write(doc_path, xml_declaration=True, encoding="UTF-8", standalone=True)
        os.remove(output_path)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for r, _, files in os.walk(exdir):
                for fn in files:
                    fp  = os.path.join(r, fn)
                    arc = os.path.relpath(fp, exdir)
                    zout.write(fp, arc)
        shutil.rmtree(exdir)
        return True

    except Exception as e:
        logger.error(f"generate_proposal error: {e}", exc_info=True)
        if os.path.exists(exdir):
            shutil.rmtree(exdir)
        return False


def full_txt_replace(doc_path, tree, replacements: dict):
    """Replace teks sederhana langsung di XML string (lebih andal untuk teks tersebar)."""
    with open(doc_path, "rb") as f:
        raw = f.read().decode("utf-8")
    for old, new in replacements.items():
        raw = raw.replace(old, new)
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(raw)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if BOT_TOKEN == "MASUKKAN_TOKEN_BOT_DISINI":
        print("⚠️  Set environment variable BOT_TOKEN terlebih dahulu.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("buat", cmd_buat)],
        states={
            S_NAMA_LOMBA:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nama_lomba)],
            S_TANGGAL_SURAT:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_tanggal_surat)],
            S_NOMOR_SURAT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nomor_surat)],
            S_TANGGAL_LOMBA:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_tanggal_lomba)],
            S_TEMPAT_LOMBA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tempat_lomba)],
            S_PENYELENGGARA:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_penyelenggara)],
            S_BIAYA:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_biaya)],
            S_LINK_POSTER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_poster)],
            S_JML_TAHAPAN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_jml_tahapan)],
            S_TAHAPAN:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tahapan)],
            S_JML_KELOMPOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_jml_kelompok)],
            S_NAMA_KELOMPOK:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_nama_kelompok)],
            S_JML_PESERTA:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_jml_peserta)],
            S_PESERTA:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_peserta)],
            S_DOSEN:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dosen)],
            S_KONFIRMASI:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_konfirmasi)],
        },
        fallbacks=[CommandHandler("batal", cmd_batal)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv)
    print("🤖 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
