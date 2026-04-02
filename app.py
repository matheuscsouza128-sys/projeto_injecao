from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os
from collections import Counter

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

def calcular_duracao(inicio_str, fim_str):
    formato = "%d/%m/%Y %H:%M:%S"
    inicio = datetime.strptime(inicio_str, formato)
    fim = datetime.strptime(fim_str, formato)
    duracao = fim - inicio

    total_segundos = int(duracao.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def obter_mais_frequente(lista):
    if not lista:
        return ("-", 0)
    contador = Counter(lista)
    return contador.most_common(1)[0]

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

# 🔹 Histórico com filtros, resumo e rankings
@app.route('/historico')
def historico():
    filtro_maquina = request.args.get('maquina', '')
    filtro_operador = request.args.get('operador', '')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    query = '''
        SELECT id, maquina, operador, tipo, detalhe, data_hora
        FROM apontamentos
        WHERE 1=1
    '''
    params = []

    if filtro_maquina:
        query += ' AND maquina = ?'
        params.append(filtro_maquina)

    if filtro_operador:
        query += ' AND operador = ?'
        params.append(filtro_operador)

    query += ' ORDER BY id DESC'

    cursor.execute(query, params)
    dados_brutos = cursor.fetchall()

    # listas para filtros
    cursor.execute('SELECT DISTINCT maquina FROM apontamentos ORDER BY maquina')
    maquinas = [linha[0] for linha in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT operador FROM apontamentos ORDER BY operador')
    operadores = [linha[0] for linha in cursor.fetchall()]

    # resumo
    total_registros = len(dados_brutos)
    total_nc = sum(1 for item in dados_brutos if item[3] == "Não Conformidade")
    total_intercorrencias = sum(1 for item in dados_brutos if item[3] == "Intercorrência")
    total_pausas = sum(1 for item in dados_brutos if item[3] == "Pausa")

    # cálculo de duração por ciclo
    ultimos_inicios = {}
    dados = []

    dados_ordenados = list(reversed(dados_brutos))

    for item in dados_ordenados:
        id_registro, maq, op, tipo, detalhe, data_hora = item
        duracao = ""

        if tipo == "Início de Produção":
            ultimos_inicios[maq] = data_hora

        elif tipo == "Fim de Produção" and maq in ultimos_inicios:
            duracao = calcular_duracao(ultimos_inicios[maq], data_hora)
            del ultimos_inicios[maq]

        dados.append((maq, op, tipo, detalhe, data_hora, duracao))

    dados.reverse()

    # rankings
    maquinas_nc = [item[1] for item in dados_brutos if item[3] == "Não Conformidade"]
    maquinas_inter = [item[1] for item in dados_brutos if item[3] == "Intercorrência"]

    # cuidado: item[1] = maquina? não, na query é:
    # item = (id, maquina, operador, tipo, detalhe, data_hora)
    maquinas_nc = [item[1] for item in dados_brutos if item[3] == "Não Conformidade"]
    maquinas_inter = [item[1] for item in dados_brutos if item[3] == "Intercorrência"]

    causas_nc = [item[4] for item in dados_brutos if item[3] == "Não Conformidade" and item[4]]
    causas_inter = [item[4] for item in dados_brutos if item[3] == "Intercorrência" and item[4]]
    causas_pausa = [item[4] for item in dados_brutos if item[3] == "Pausa" and item[4]]

    maquina_mais_nc, qtd_maquina_mais_nc = obter_mais_frequente(maquinas_nc)
    maquina_mais_inter, qtd_maquina_mais_inter = obter_mais_frequente(maquinas_inter)
    causa_mais_nc, qtd_causa_mais_nc = obter_mais_frequente(causas_nc)
    causa_mais_inter, qtd_causa_mais_inter = obter_mais_frequente(causas_inter)
    causa_mais_pausa, qtd_causa_mais_pausa = obter_mais_frequente(causas_pausa)

    conn.close()

    return render_template(
        'historico.html',
        dados=dados,
        maquinas=maquinas,
        operadores=operadores,
        filtro_maquina=filtro_maquina,
        filtro_operador=filtro_operador,
        total_registros=total_registros,
        total_nc=total_nc,
        total_intercorrencias=total_intercorrencias,
        total_pausas=total_pausas,
        maquina_mais_nc=maquina_mais_nc,
        qtd_maquina_mais_nc=qtd_maquina_mais_nc,
        maquina_mais_inter=maquina_mais_inter,
        qtd_maquina_mais_inter=qtd_maquina_mais_inter,
        causa_mais_nc=causa_mais_nc,
        qtd_causa_mais_nc=qtd_causa_mais_nc,
        causa_mais_inter=causa_mais_inter,
        qtd_causa_mais_inter=qtd_causa_mais_inter,
        causa_mais_pausa=causa_mais_pausa,
        qtd_causa_mais_pausa=qtd_causa_mais_pausa
    )

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