from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# 🔹 Criar banco e tabela (se não existir)
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

# 🔹 Garante que o banco existe ao iniciar
criar_banco()

# 🔹 Página inicial
@app.route('/')
def index():
    return render_template('index.html', maquina="", status="")

# 🔹 Página da máquina (via QR Code)
@app.route('/maquina/<id_maquina>')
def maquina(id_maquina):
    status = request.args.get("status", "")
    return render_template('index.html', maquina=id_maquina, status=status)

# 🔹 Registro de apontamento
@app.route('/registrar', methods=['POST'])
def registrar():
    maquina = request.form['maquina']
    operador = request.form['operador']
    tipo = request.form['tipo']
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

    # 🔹 Redireciona com confirmação
    return redirect(f'/maquina/{maquina}?status={tipo}')

@app.route('/historico')
def historico():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('SELECT maquina, operador, tipo, data_hora FROM apontamentos ORDER BY id DESC')
    dados = cursor.fetchall()

    conn.close()

    return render_template('historico.html', dados=dados)

@app.route('/limpar')
def limpar():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM apontamentos')
    conn.commit()
    conn.close()
    return "Histórico apagado com sucesso."

# 🔹 Rodar aplicação
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)