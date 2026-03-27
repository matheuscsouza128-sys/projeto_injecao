from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

def criar_banco():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apontamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina TEXT,
            operador TEXT,
            tipo TEXT,
            descricao TEXT,
            data_hora TEXT
        )
    ''')

    conn.commit()
    conn.close()

# cria o banco também quando o app for iniciado pelo gunicorn no Render
criar_banco()

@app.route('/')
def index():
    return render_template('index.html', maquina="")

@app.route('/maquina/<id_maquina>')
def maquina(id_maquina):
    return render_template('index.html', maquina=id_maquina)

@app.route('/registrar', methods=['POST'])
def registrar():
    maquina = request.form['maquina']
    tipo = request.form['tipo']
    operador = "Operador"
    descricao = ""
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO apontamentos (maquina, operador, tipo, descricao, data_hora)
        VALUES (?, ?, ?, ?, ?)
    ''', (maquina, operador, tipo, descricao, data_hora))

    conn.commit()
    conn.close()

    return redirect(f'/maquina/{maquina}')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)