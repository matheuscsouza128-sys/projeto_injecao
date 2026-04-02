from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# 🔹 Criar banco e tabelas (se não existirem)
def criar_banco():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # tabela de apontamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apontamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina TEXT,
            operador TEXT,
            tipo TEXT,
            detalhe TEXT,
            data_hora TEXT
        )
    ''')

    # tabela para status atual de cada máquina
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinas_status (
            maquina TEXT PRIMARY KEY,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 🔹 Garante que o banco existe ao iniciar
criar_banco()

# 🔹 Página inicial
@app.route('/')
def index():
    return render_template('index.html', maquina="", status="", status_maquina="Parada")

# 🔹 Página da máquina (via QR Code)
@app.route('/maquina/<id_maquina>')
def maquina(id_maquina):
    status = request.args.get("status", "")

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('SELECT status FROM maquinas_status WHERE maquina = ?', (id_maquina,))
    resultado = cursor.fetchone()

    conn.close()

    status_maquina = resultado[0] if resultado else "Parada"

    return render_template(
        'index.html',
        maquina=id_maquina,
        status=status,
        status_maquina=status_maquina
    )

# 🔹 Histórico
@app.route('/historico')
def historico():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('SELECT maquina, operador, tipo, detalhe, data_hora FROM apontamentos ORDER BY id DESC')
    dados = cursor.fetchall()

    conn.close()

    return render_template('historico.html', dados=dados)

# 🔹 Limpar histórico (temporário)
@app.route('/limpar')
def limpar():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM apontamentos')
    cursor.execute('DELETE FROM maquinas_status')
    conn.commit()
    conn.close()
    return "Histórico apagado com sucesso."

# 🔹 Registro de apontamento
@app.route('/registrar', methods=['POST'])
def registrar():
    maquina = request.form['maquina']
    operador = request.form['operador']
    tipo = request.form['tipo']
    detalhe = request.form.get('detalhe', '')
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # verifica status atual da máquina
    cursor.execute('SELECT status FROM maquinas_status WHERE maquina = ?', (maquina,))
    resultado = cursor.fetchone()
    status_atual = resultado[0] if resultado else "Parada"

    # regra: só pode finalizar / NC / intercorrência / pausa se já tiver iniciado
    if status_atual != "Em produção" and tipo != "Início de Produção":
        conn.close()
        return redirect(f'/maquina/{maquina}?status=Erro: primeiro registre o início da produção')

    # registra apontamento
    cursor.execute('''
        INSERT INTO apontamentos (maquina, operador, tipo, detalhe, data_hora)
        VALUES (?, ?, ?, ?, ?)
    ''', (maquina, operador, tipo, detalhe, data_hora))

    # atualiza status da máquina
    if tipo == "Início de Produção":
        cursor.execute('''
            INSERT INTO maquinas_status (maquina, status)
            VALUES (?, ?)
            ON CONFLICT(maquina) DO UPDATE SET status = excluded.status
        ''', (maquina, "Em produção"))

    elif tipo == "Fim de Produção":
        cursor.execute('''
            INSERT INTO maquinas_status (maquina, status)
            VALUES (?, ?)
            ON CONFLICT(maquina) DO UPDATE SET status = excluded.status
        ''', (maquina, "Parada"))

    conn.commit()
    conn.close()

    return redirect(f'/maquina/{maquina}?status={tipo}')

# 🔹 Rodar aplicação
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)