from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta
import joblib
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import os

from database import (
    init_db,

    # Data Saham
    save_stock_data,
    save_stock_data_bulk,
    get_all_stock_data,

    # Model
    save_model,
    get_all_models,
    get_model_by_id,
    update_model,
    delete_model,

    # Prediksi
    save_prediction,
    get_prediction_history,
    delete_prediction
)

# =====================================
# CONFIG
# =====================================

load_dotenv()

app = Flask(__name__)
CORS(app)

BACKEND_PORT = int(os.getenv("BACKEND_PORT", 5000))

MODEL_FOLDER = "models"

os.makedirs(MODEL_FOLDER, exist_ok=True)

# =====================================
# INIT DATABASE
# =====================================

init_db()

# =====================================
# HOME
# =====================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "API Prediksi Harga Saham"
    })

# =====================================
# UPLOAD DATASET SAHAM
# =====================================

@app.route("/api/stocks/upload", methods=["POST"])
def upload_stock_data():

    try:
        # =========================
        # VALIDASI FILE
        # =========================
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "File tidak ditemukan"
            }), 400

        file = request.files["file"]

        # =========================
        # READ CSV
        # =========================
        df = pd.read_csv(file, sep=';')

        # =========================
        # CLEAN COLUMN NAMES
        # =========================
        df.columns = df.columns.str.strip()

        # =========================
        # VALIDASI KOLOM WAJIB
        # =========================
        required_cols = ["Date", "Close", "High", "Low", "Open"]

        for col in required_cols:
            if col not in df.columns:
                return jsonify({
                    "success": False,
                    "message": f"Kolom {col} tidak ditemukan di file CSV"
                }), 400

        # =========================
        # HAPUS DATA KOSONG
        # =========================
        df = df.dropna(subset=required_cols)

        # =========================
        # CONVERT KE LIST
        # =========================
        data_list = [
            (
                row.Date,
                float(row.Close),
                float(row.High),
                float(row.Low),
                float(row.Open)
            )
            for row in df.itertuples(index=False)
        ]

        # =========================
        # BULK INSERT
        # =========================
        save_stock_data_bulk(data_list)

        return jsonify({
            "success": True,
            "total_data": len(data_list)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# =====================================
# GET DATA SAHAM
# =====================================

@app.route("/api/stocks", methods=["GET"])
def get_stocks():

    data = get_all_stock_data()

    result = []

    for row in data:
        result.append({
            "id_data": row[0],
            "date": row[1],
            "close_price": row[2],
            "high_price": row[3],
            "low_price": row[4],
            "open_price": row[5]
        })

    return jsonify(result)

# =====================================
# UPLOAD MODEL .KERAS
# =====================================

@app.route("/api/models/upload", methods=["POST"])
def upload_model():

    try:

        if "model" not in request.files:
            return jsonify({
                "success": False,
                "message": "File model tidak ditemukan"
            }), 400

        model_file = request.files["model"]

        nama_model = request.form[
            "nama_model"
        ]

        timestep = int(
            request.form["timestep"]
        )

        filename = model_file.filename

        filepath = os.path.join(
            MODEL_FOLDER,
            filename
        )

        model_file.save(filepath)

        save_model(
            nama_model,
            filepath,
            timestep
        )

        return jsonify({
            "success": True,
            "message": "Model berhasil diupload"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =====================================
# GET MODEL
# =====================================

@app.route("/api/models", methods=["GET"])
def get_models():

    rows = get_all_models()

    result = []

    for row in rows:

        result.append({
            "id_model": row[0],
            "nama_model": row[1],
            "file_model": row[2],
            "timestep": row[3],
            "created_at": str(row[4])
        })

    return jsonify(result)

@app.route(
    "/api/models/<int:id_model>",
    methods=["PUT"]
)
def edit_model(id_model):

    try:

        model = get_model_by_id(id_model)

        if not model:
            return jsonify({
                "success": False,
                "message": "Model tidak ditemukan"
            }), 404

        nama_model = request.form[
            "nama_model"
        ]

        timestep = int(
            request.form["timestep"]
        )

        file_model = model[2]

        # upload model baru
        if "model" in request.files:

            uploaded_file = request.files["model"]

            if uploaded_file.filename:

                if (
                    file_model and
                    os.path.exists(file_model)
                ):
                    os.remove(file_model)

                filename = uploaded_file.filename

                file_model = os.path.join(
                    MODEL_FOLDER,
                    filename
                )

                uploaded_file.save(
                    file_model
                )

        update_model(
            id_model,
            nama_model,
            file_model,
            timestep
        )

        return jsonify({
            "success": True,
            "message": "Model berhasil diperbarui"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
@app.route(
    "/api/models/<int:id_model>",
    methods=["DELETE"]
)
def remove_model(id_model):

    try:

        model = get_model_by_id(id_model)

        if not model:

            return jsonify({
                "success": False,
                "message": "Model tidak ditemukan"
            }), 404

        file_model = model[2]

        # hapus file keras
        if (
            file_model and
            os.path.exists(file_model)
        ):
            os.remove(file_model)

        # hapus database
        delete_model(id_model)

        return jsonify({
            "success": True,
            "message": "Model berhasil dihapus"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =====================================
# PREDIKSI
# =====================================

@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        id_model = data["id_model"]

        model_info = get_model_by_id(id_model)

        if not model_info:
            return jsonify({
                "success": False,
                "message": "Model tidak ditemukan"
            }), 404

        model_path = model_info[2]
        timestep = model_info[3]

        model = load_model(model_path)

        # =================================
        # AMBIL DATA SAHAM TERAKHIR
        # =================================

        stocks = get_all_stock_data()

        if len(stocks) < timestep:
            return jsonify({
                "success": False,
                "message": f"Minimal membutuhkan {timestep} data"
            }), 400

        features = []

        for row in reversed(stocks[:timestep]):

            features.append([
                row[5],  # open_price
                row[3],  # high_price
                row[4],  # low_price
                row[2]   # close_price
            ])

        # =================================
        # LOAD SCALER
        # =================================

        scaler_path = os.path.join(
            "scaler",
            "minmax_scaler.pkl"
        )

        scaler = joblib.load(scaler_path)

        X = np.array(features)

        X_scaled = scaler.transform(
            X.reshape(-1, 4)
        )

        X_scaled = X_scaled.reshape(
            1,
            timestep,
            4
        )

        print("INPUT SHAPE:", X_scaled.shape)

        # =================================
        # PREDIKSI
        # =================================

        prediction = model.predict(X_scaled)

        # hasil prediksi masih dalam bentuk normalized close
        pred_close_scaled = prediction[0][0]

        # buat dummy array 4 fitur
        dummy = np.zeros((1, 4))

        # letakkan hasil prediksi pada kolom close
        # sesuaikan posisi close dengan urutan saat training
        dummy[0, 3] = pred_close_scaled

        # inverse transform
        denorm = scaler.inverse_transform(dummy)

        predicted_price = float(denorm[0, 3])

        # =================================
        # TANGGAL PREDIKSI
        # 1 HARI SETELAH DATA TERBARU
        # =================================

        last_date_value = stocks[0][1]

        if isinstance(last_date_value, str):
            last_date = datetime.strptime(
                last_date_value,
                "%Y-%m-%d"
            ).date()
        else:
            last_date = last_date_value

        prediction_date = (
            last_date + timedelta(days=1)
        )

        print("Tanggal terakhir :", last_date)
        print("Tanggal prediksi :", prediction_date)

        # =================================
        # SIMPAN HASIL PREDIKSI
        # =================================

        save_prediction(
            id_model,
            prediction_date,
            predicted_price
        )

        return jsonify({
            "success": True,
            "date_prediksi": str(prediction_date),
            "harga_prediksi": predicted_price
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# =====================================
# RIWAYAT PREDIKSI
# =====================================

@app.route("/api/predictions", methods=["GET"])
def prediction_history():

    rows = get_prediction_history()

    result = []

    for row in rows:

        result.append({
            "id_prediksi": row[0],
            "date_prediksi": str(row[1]),
            "harga_prediksi": row[2],
            "created_at": str(row[3]),
            "id_model": row[4],
            "nama_model": row[5]
        })

    return jsonify(result)

@app.route(
    "/api/predictions/<int:id_prediksi>",
    methods=["DELETE"]
)
def remove_prediction(id_prediksi):

    try:

        delete_prediction(id_prediksi)

        return jsonify({
            "success": True,
            "message": "History berhasil dihapus"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =====================================
# CHART DATA
# =====================================

@app.route("/api/stocks/chart", methods=["GET"])
def get_stock_chart():

    data = get_all_stock_data()

    data = list(reversed(data))

    result = []

    for row in data:
        result.append({
            "date": str(row[1]),
            "close_price": row[2],
            "high_price": row[3],
            "low_price": row[4],
            "open_price": row[5]
        })

    return jsonify(result)

# =====================================
# RUN APP
# =====================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=BACKEND_PORT,
        debug=True
    )