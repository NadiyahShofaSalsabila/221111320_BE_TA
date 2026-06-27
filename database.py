import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# ==========================
# LOAD ENVIRONMENT VARIABLES
# ==========================
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USERNAME", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_DATABASE", "prediksi_saham")

# ==========================
# KONEKSI DATABASE
# ==========================
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# ==========================
# INISIALISASI DATABASE
# ==========================
def init_db():
    try:
        # Buat database jika belum ada
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )

        cursor = conn.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"
        )

        conn.commit()
        conn.close()

        # Koneksi ke database yang baru dibuat
        conn = get_connection()
        cursor = conn.cursor()

        # ==========================
        # TABEL DATA SAHAM
        # ==========================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_saham (
                id_data INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                close_price FLOAT NOT NULL,
                high_price FLOAT NOT NULL,
                low_price FLOAT NOT NULL,
                open_price FLOAT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT uq_date UNIQUE (date)
            )
        """)

        # ==========================
        # TABEL MODEL
        # ==========================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model (
                id_model INT AUTO_INCREMENT PRIMARY KEY,
                nama_model VARCHAR(255) NOT NULL,
                file_model VARCHAR(500) NOT NULL,
                timestep INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==========================
        # TABEL PREDIKSI
        # ==========================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediksi_harga (
                id_prediksi INT AUTO_INCREMENT PRIMARY KEY,
                id_model INT NOT NULL,
                date_prediksi DATE NOT NULL,
                harga_prediksi FLOAT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_model
                FOREIGN KEY (id_model)
                REFERENCES model(id_model)
                ON DELETE CASCADE
                ON UPDATE CASCADE
            )
        """)

        conn.commit()
        conn.close()

        print("Database berhasil diinisialisasi.")

    except Error as e:
        print("Error saat inisialisasi database:", e)

# ==================================================
# CRUD DATA SAHAM
# ==================================================

def save_stock_data(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO data_saham (
            date,
            close_price,
            high_price,
            low_price,
            open_price
        )
        VALUES (%s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            open_price = VALUES(open_price)
    """, data)

    conn.commit()
    conn.close()

def clear_stock_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM data_saham")

    conn.commit()
    cursor.close()
    conn.close()

def save_stock_data_bulk(data_list):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT IGNORE INTO data_saham (
            date,
            close_price,
            high_price,
            low_price,
            open_price
        )
        VALUES (%s, %s, %s, %s, %s)
    """, data_list)

    conn.commit()
    conn.close()


def get_all_stock_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id_data,
            date,
            close_price,
            high_price,
            low_price,
            open_price
        FROM data_saham
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_stock_data_by_id(id_data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM data_saham
        WHERE id_data = %s
    """, (id_data,))

    row = cursor.fetchone()

    conn.close()
    return row


def delete_stock_data(id_data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM data_saham
        WHERE id_data = %s
    """, (id_data,))

    conn.commit()
    conn.close()


def delete_all_stock_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM data_saham")

    conn.commit()
    conn.close()

# ==================================================
# CRUD MODEL
# ==================================================

def save_model(nama_model, file_model, timestep):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO model (
            nama_model,
            file_model,
            timestep
        )
        VALUES (%s, %s, %s)
    """, (
        nama_model,
        file_model,
        timestep
    ))

    conn.commit()
    conn.close()


def get_all_models():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM model
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()
    return rows


def get_model_by_id(id_model):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM model
        WHERE id_model = %s
    """, (id_model,))

    row = cursor.fetchone()

    conn.close()
    return row

def update_model(
    id_model,
    nama_model,
    file_model,
    timestep
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE model
        SET
            nama_model = %s,
            file_model = %s,
            timestep = %s
        WHERE id_model = %s
    """, (
        nama_model,
        file_model,
        timestep,
        id_model
    ))

    conn.commit()
    conn.close()


def delete_model(id_model):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM model
        WHERE id_model = %s
    """, (id_model,))

    conn.commit()
    conn.close()


def delete_all_models():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM model")

    conn.commit()
    conn.close()

# ==================================================
# CRUD PREDIKSI
# ==================================================

def save_prediction(
    id_model,
    date_prediksi,
    harga_prediksi
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prediksi_harga (
            id_model,
            date_prediksi,
            harga_prediksi
        )
        VALUES (%s, %s, %s)
    """, (
        id_model,
        date_prediksi,
        harga_prediksi
    ))

    conn.commit()
    conn.close()


def get_prediction_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id_prediksi,
            p.date_prediksi,
            p.harga_prediksi,
            p.created_at,
            m.id_model,
            m.nama_model
        FROM prediksi_harga p
        JOIN model m
            ON p.id_model = m.id_model
        ORDER BY p.created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()
    return rows


def get_prediction_by_id(id_prediksi):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM prediksi_harga
        WHERE id_prediksi = %s
    """, (id_prediksi,))

    row = cursor.fetchone()

    conn.close()
    return row


def delete_prediction(id_prediksi):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM prediksi_harga
        WHERE id_prediksi = %s
    """, (id_prediksi,))

    conn.commit()
    conn.close()


def delete_all_predictions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM prediksi_harga")

    conn.commit()
    conn.close()