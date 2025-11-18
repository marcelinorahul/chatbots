from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import re
import time
import json
from datetime import datetime
import logging
import os
import gc
import threading

# Pengaturan logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatbotUPATIK:
    def __init__(self, json_file_path=None, use_lightweight_model=True):
        """
        TAHAP 1 INISIALISASI CHATBOT - DIOPTIMALKAN UNTUK MEMORI RENDAH
        """
        logger.info("Menginisialisasi Chatbot dengan optimasi memori...")

        # Paksa garbage collection
        gc.collect()

        # Inisialisasi model sebagai None terlebih dahulu
        self.model = None
        self.question_embeddings = None
        self.processed_questions = None

        # Muat dataset terlebih dahulu
        self.json_file_path = json_file_path
        self.load_dataset()

        # Inisialisasi penyimpanan percakapan
        self.conversation_history = []
        self.evaluation_data = []

        # Atur threshold
        self.threshold = 0.5 if use_lightweight_model else 0.7

        # Coba inisialisasi model
        self.initialize_model(use_lightweight_model)

        logger.info(
            f"Inisialisasi chatbot selesai! Dataset: {len(self.df)} pertanyaan dari {len(self.df['kategori'].unique())} kategori"
        )

    def initialize_model(self, use_lightweight_model=True):
        """Inisialisasi model sentence transformer dengan fallback"""
        try:
            # Coba import sentence_transformers
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            # Simpan untuk digunakan nanti
            self.cosine_similarity = cosine_similarity

            # Coba CUDA terlebih dahulu jika tersedia
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    device = "cuda"
                    logger.info("CUDA tersedia, menggunakan GPU")
                else:
                    device = "cpu"
                    logger.info("CUDA tidak tersedia, menggunakan CPU")
            except ImportError:
                device = "cpu"
                logger.info("PyTorch tidak tersedia, menggunakan CPU")

            # pilih model berdasarkan memori atau komputasi
            if use_lightweight_model:
                model_names = [
                    "all-MiniLM-L6-v2",  # model terakhir cepat dan sumber daya minim, file kecil 90mb cocok untuk demo
                ]
            else:
                model_names = [
                    # Sangat efektif untuk memahami variasi pertanyaan dan bahasa informal
                    "paraphrase-multilingual-mpnet-base-v2",
                    # Fallback jika model inti gagal dimuat. Masih mendukung multi-bahasa tapi lebih ringan
                    "paraphrase-multilingual-MiniLM-L12-v2",
                ]

            # Coba setiap model secara berurutan
            for model_name in model_names:
                try:
                    logger.info(f"Mencoba memuat model: {model_name}")
                    self.model = SentenceTransformer(
                        model_name, device=device, cache_folder="./model_cache"
                    )
                    self.model.eval()
                    logger.info(f"Berhasil memuat model: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Gagal memuat {model_name}: {e}")
                    continue

            if self.model is None:
                raise Exception("Tidak dapat memuat model sentence transformer apapun")

            # Generate embeddings
            self.generate_embeddings()

        except ImportError as e:
            logger.error(f"Library yang diperlukan tidak terinstal: {e}")
            logger.error(
                "Silakan instal: pip install sentence-transformers scikit-learn torch"
            )
            self.model = None

        except Exception as e:
            logger.error(f"Gagal menginisialisasi model: {e}")
            self.model = None

    def load_dataset(self):
        """Muat dataset dari JSON atau gunakan default"""
        try:
            if self.json_file_path and os.path.exists(self.json_file_path):
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)

                data_list = []
                for item in json_data:
                    data_list.append(
                        {
                            "pertanyaan": item["pertanyaan"],
                            "jawaban": item["jawaban"],
                            "kategori": item["kategori"],
                        }
                    )

                self.df = pd.DataFrame(data_list)
                logger.info(f"Dataset dimuat dari JSON: {len(self.df)} pertanyaan")
            else:
                self.load_default_dataset()

        except Exception as e:
            logger.error(f"Error memuat dataset: {e}")
            self.load_default_dataset()

    def load_default_dataset(self):
        """Muat dataset default untuk demo jika tidak terpanggil dataset asli"""
        default_data = [
            {
                "kategori": "Akademik",
                "pertanyaan": "Saya Lupa Password SIAKAD?",
                "jawaban": "Silakan hubungi helpdesk LPTIK pada jam kerja atau kirim email ke heldpesk.lptik@unja.ac.id Silakan hubungi helpdesk LPTIK pada jam kerja atau kirim email ke heldpesk.lptik@unja.ac.id",
            },
            {
                "kategori": "Akademik",
                "pertanyaan": "Saya Lupa password elearning UNJA?",
                "jawaban": "Password elearning sama dengan password siakad,bila password siakad pun lupa silahkan datang ke helpdesk LPTIK atau kirim email ke helpdesk.lptik@unja.ac.id Password elearning sama dengan password siakad, bila password siakad pun lupa silahkan datang ke helpdesk LPTIK atau kirim email ke helpdesk.lptik@unja.ac.id",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Halo",
                "jawaban": "Halo! Ada yang bisa saya bantu terkait akademik, kemahasiswaan, atau kepegawaian di UNJA?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Hai",
                "jawaban": "Hai! Selamat datang di Chatbot UNJA. Silakan tanyakan kebutuhan Anda!",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Selamat pagi",
                "jawaban": "Selamat pagi! Mau tanya tentang SIAKAD, elearning, atau info kampus?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Selamat siang",
                "jawaban": "Selamat siang! Saya siap membantu informasi seputar UNJA. Ada yang bisa saya bantu?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Selamat sore",
                "jawaban": "Selamat sore! Apakah Anda butuh bantuan terkait pendaftaran, jadwal, atau administrasi?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Selamat malam",
                "jawaban": "Selamat malam nih! Apakah Anda butuh bantuan terkait pendaftaran, jadwal, atau administrasi sebelum tidur?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Apa kabar?",
                "jawaban": "Baik sekali! Bagaimana dengan Anda? Ada yang bisa saya bantu hari ini?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Hai bot",
                "jawaban": "Hai! Saya adalah asisten virtual UNJA. Ada yang ingin ditanyakan?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Hello",
                "jawaban": "Hello! Selamat datang di layanan informasi UNJA. Silakan bertanya!",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Assalamualaikum",
                "jawaban": "Waalaikumsalam! Semoga harimu berkah. Ada yang bisa saya bantu seputar UNJA?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Hey",
                "jawaban": "Hey hey! Butuh bantuan soal perkuliahan, sistem, atau info UNJA?",
            },
            {
                "kategori": "Sapaan",
                "pertanyaan": "Bot",
                "jawaban": "Iya, saya di sini! Mau nanya apa hari ini? ",
            },
        ]

        self.df = pd.DataFrame(default_data)
        logger.info(
            f"Dataset default dimuat: {len(self.df)} pertanyaan dari {len(self.df['kategori'].unique())} kategori"
        )

    def preprocess_text(self, text):
        """Preprocessing teks"""
        if not isinstance(text, str) or not text.strip():
            return ""

        text = text.lower()

        # Pemetaan bahasa informal ke formal dasar
        informal_mapping = {
            r"\bgimana\b": "bagaimana",
            r"\bgmn\b": "bagaimana",
            r"\bapaan\b": "apa",
            r"\bknp\b": "kenapa",
            r"\bgk\b": "tidak",
            r"\bga\b": "tidak",
            r"\bkalo\b": "kalau",
            r"\bklo\b": "kalau",
            r"\binfo\b": "informasi",
            r"\buniv\b": "universitas",
            r"\bsiakad\b": "siakad",
            r"\belearning\b": "elearning",
            r"\bpassword\b": "password",
            r"\bpw\b": "password",
        }

        for pattern, replacement in informal_mapping.items():
            text = re.sub(pattern, replacement, text)

        # Bersihkan tanda baca dan normalkan spasi
        text = re.sub(r"[?!.]+", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def generate_embeddings(self):
        """Generate embeddings untuk pertanyaan dataset"""
        if self.model is None:
            logger.error("Model tidak terinisialisasi, tidak dapat generate embeddings")
            return

        logger.info("Membuat embeddings untuk dataset...")

        processed_questions = [self.preprocess_text(q) for q in self.df["pertanyaan"]]

        try:
            self.question_embeddings = self.model.encode(
                processed_questions,
                show_progress_bar=True,
                batch_size=4,  # Ukuran batch sangat kecil
                convert_to_tensor=False,
                normalize_embeddings=True,
            )

            self.processed_questions = processed_questions
            gc.collect()

            logger.info(f"Embeddings berhasil dibuat: {self.question_embeddings.shape}")

        except Exception as e:
            logger.error(f"Error membuat embeddings: {e}")
            # Fallback ke pencocokan teks sederhana
            self.question_embeddings = None
            self.processed_questions = processed_questions

    def get_response(self, user_input):
        """Dapatkan respon untuk input pengguna"""
        start_time = time.time()

        processed_input = self.preprocess_text(user_input)
        if not processed_input:
            return self._error_response(
                user_input, processed_input, "preprocessing_error", start_time
            )

        # Jika model tidak tersedia, gunakan pencocokan teks sederhana
        if self.model is None or self.question_embeddings is None:
            return self._simple_text_matching(user_input, processed_input, start_time)

        try:
            # Generate embedding input pengguna
            user_embedding = self.model.encode(
                [processed_input], convert_to_tensor=False, normalize_embeddings=True
            )

            # Menghitung similarity
            similarities = self.cosine_similarity(
                user_embedding, self.question_embeddings
            )[0]
            best_match_idx = np.argmax(similarities)
            best_similarity = similarities[best_match_idx]

        except Exception as e:
            logger.error(f"Error dalam perhitungan similarity: {e}")
            return self._simple_text_matching(user_input, processed_input, start_time)

        response_time = time.time() - start_time

        if best_similarity >= self.threshold:
            return self._success_response(
                best_match_idx,
                best_similarity,
                user_input,
                processed_input,
                response_time,
            )
        else:
            return self._fallback_response(
                best_similarity, user_input, processed_input, response_time
            )

    def _simple_text_matching(self, user_input, processed_input, start_time):
        """Fallback pencocokan teks sederhana ketika model tidak tersedia"""
        logger.info("Menggunakan pencocokan teks sederhana (model tidak tersedia)")

        best_match_idx = 0
        best_score = 0

        # Pencocokan kata kunci sederhana
        for i, question in enumerate(self.df["pertanyaan"]):
            processed_question = self.preprocess_text(question)

            # Hitung kata yang cocok
            user_words = set(processed_input.split())
            question_words = set(processed_question.split())

            if len(question_words) > 0:
                intersection = len(user_words.intersection(question_words))
                score = intersection / len(question_words)

                if score > best_score:
                    best_score = score
                    best_match_idx = i

        response_time = time.time() - start_time

        if best_score >= 0.5:  # Threshold hasil uji yang seimbang
            return self._success_response(
                best_match_idx, best_score, user_input, processed_input, response_time
            )
        else:
            return self._fallback_response(
                best_score, user_input, processed_input, response_time
            )

    def _success_response(
        self, match_idx, similarity, user_input, processed_input, response_time
    ):
        """Buat respon sukses"""
        response_data = {
            "answer": self.df.iloc[match_idx]["jawaban"],
            "category": self.df.iloc[match_idx]["kategori"],
            "confidence": float(similarity),
            "matched_question": self.df.iloc[match_idx]["pertanyaan"],
            "original_question": user_input,
            "processed_question": processed_input,
            "status": "success",
            "response_time": response_time,
        }

        self.conversation_history.append(
            {
                "user": user_input,
                "bot": response_data["answer"],
                "category": response_data["category"],
                "confidence": float(similarity),
                "status": "success",
                "response_time": response_time,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        return response_data

    def _fallback_response(
        self, similarity, user_input, processed_input, response_time
    ):
        """Buat respon fallback"""
        fallback_message = "Maaf, saya belum bisa memahami pertanyaan kamu nih, bisa coba ubah dengan kata lain. Atau Untuk bantuan lebih lanjut, silakan cek informasi di atas klik tentang chatbot (kepala robot)"

        response_data = {
            "answer": fallback_message,
            "category": "Tidak dikenal",
            "confidence": float(similarity),
            "original_question": user_input,
            "processed_question": processed_input,
            "status": "below_threshold",
            "response_time": response_time,
        }

        self.conversation_history.append(
            {
                "user": user_input,
                "bot": fallback_message,
                "category": "Tidak dikenal",
                "confidence": float(similarity),
                "status": "below_threshold",
                "response_time": response_time,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        return response_data

    def _error_response(self, user_input, processed_input, error_type, start_time):
        """Buat respon error"""
        return {
            "answer": "Maaf, saya tidak memahami pertanyaan Anda. Silakan tulis ulang dengan lebih jelas.",
            "category": "Error",
            "confidence": 0.0,
            "original_question": user_input,
            "processed_question": processed_input,
            "status": error_type,
            "response_time": time.time() - start_time,
        }


# Inisialisasi aplikasi Flask
app = Flask(__name__)
CORS(app)

# Instance chatbot global
chatbot = None
chatbot_status = {"ready": False, "error": None}


def initialize_chatbot_async():
    """Inisialisasi chatbot di background thread"""
    global chatbot, chatbot_status

    try:
        logger.info("Memulai inisialisasi chatbot di background...")
        chatbot_status = {"ready": False, "error": None}

        # Periksa apakah dataset.json ada
        json_path = "dataset.json" if os.path.exists("dataset.json") else None

        # Coba model ringan terlebih dahulu
        chatbot = ChatbotUPATIK(json_file_path=json_path, use_lightweight_model=True)

        chatbot_status = {"ready": True, "error": None}
        logger.info("Inisialisasi chatbot berhasil diselesaikan!")

    except Exception as e:
        error_msg = f"Inisialisasi chatbot gagal: {str(e)}"
        logger.error(error_msg)
        chatbot_status = {"ready": False, "error": error_msg}
        chatbot = None


# Endpoint pemeriksaan kesehatan
@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint pemeriksaan kesehatan"""
    return jsonify(
        {
            "status": "sehat",
            "message": "API Chatbot UPA TIK sedang berjalan",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chatbot_ready": chatbot_status["ready"],
            "chatbot_error": chatbot_status["error"],
        }
    )


# Endpoint chat utama
@app.route("/api/chat", methods=["POST"])
def chat():
    """Endpoint chat utama"""
    try:
        # Periksa apakah chatbot siap
        if not chatbot_status["ready"]:
            if chatbot_status["error"]:
                error_msg = f"Chatbot tidak tersedia: {chatbot_status['error']}"
            else:
                error_msg = "Chatbot masih dalam proses inisialisasi. Silakan tunggu beberapa saat."

            return (
                jsonify(
                    {"error": error_msg, "status": "error", "chatbot_ready": False}
                ),
                503,
            )

        # Validasi request
        if not request.is_json:
            return (
                jsonify(
                    {"error": "Content-Type harus application/json", "status": "error"}
                ),
                400,
            )

        data = request.get_json()

        if not data or "message" not in data:
            return (
                jsonify({"error": "Field 'message' diperlukan", "status": "error"}),
                400,
            )

        user_message = data["message"].strip()

        if not user_message:
            return (
                jsonify({"error": "Pesan tidak boleh kosong", "status": "error"}),
                400,
            )

        logger.info(f"Pesan diterima: {user_message}")

        # Proses dengan chatbot
        response = chatbot.get_response(user_message)

        # Format respon
        widget_response = {
            "status": "success",
            "message": response["answer"],
            "category": response["category"],
            "confidence": round(response["confidence"], 3),
            "response_time": round(response["response_time"], 3),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info(
            f"Respon dikirim: {response['status']} - confidence: {response['confidence']:.3f}"
        )

        return jsonify(widget_response)

    except Exception as e:
        logger.error(f"Error di endpoint chat: {e}")
        return (
            jsonify(
                {
                    "error": "Terjadi kesalahan server internal",
                    "status": "error",
                    "message": "Maaf, terjadi kesalahan. Silakan coba lagi atau hubungi helpdesk.",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ),
            500,
        )


# Endpoint statistik
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Dapatkan statistik chatbot"""
    try:
        if not chatbot_status["ready"] or chatbot is None:
            return jsonify({"error": "Chatbot belum siap"}), 503

        total_conversations = len(chatbot.conversation_history)
        successful_responses = len(
            [h for h in chatbot.conversation_history if h["status"] == "success"]
        )
        avg_confidence = (
            np.mean([h["confidence"] for h in chatbot.conversation_history])
            if chatbot.conversation_history
            else 0
        )
        avg_response_time = (
            np.mean([h["response_time"] for h in chatbot.conversation_history])
            if chatbot.conversation_history
            else 0
        )

        stats = {
            "total_conversations": total_conversations,
            "successful_responses": successful_responses,
            "success_rate": (
                round(successful_responses / total_conversations * 100, 2)
                if total_conversations > 0
                else 0
            ),
            "average_confidence": round(avg_confidence, 3),
            "average_response_time": round(avg_response_time, 3),
            "dataset_size": len(chatbot.df),
            "categories": list(chatbot.df["kategori"].unique()),
            "threshold": chatbot.threshold,
            "model_available": chatbot.model is not None,
        }

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error di endpoint stats: {e}")
        return jsonify({"error": "Terjadi kesalahan server"}), 500

# Endpoint reset
@app.route("/api/reset", methods=["POST"])
def reset_history():
    """Reset riwayat percakapan"""
    try:
        if not chatbot_status["ready"] or chatbot is None:
            return jsonify({"error": "Chatbot belum siap"}), 503

        chatbot.conversation_history.clear()
        return jsonify(
            {"status": "success", "message": "Riwayat percakapan telah direset"}
        )
    except Exception as e:
        logger.error(f"Error di endpoint reset: {e}")
        return jsonify({"error": "Terjadi kesalahan server"}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint tidak ditemukan", "status": "error"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method tidak diizinkan", "status": "error"}), 405


@app.errorhandler(500)
def internal_error(error):
    return (
        jsonify({"error": "Terjadi kesalahan server internal", "status": "error"}),
        500,
    )


if __name__ == "__main__":
    logger.info("Memulai Server API Chatbot UPA TIK...")

    # Mulai inisialisasi chatbot di background thread
    init_thread = threading.Thread(target=initialize_chatbot_async)
    init_thread.daemon = True
    init_thread.start()

    # Mulai server Flask segera
    logger.info("Server dimulai... Chatbot akan tersedia segera.")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
