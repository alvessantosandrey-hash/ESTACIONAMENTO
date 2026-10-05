# ============================================================
# SISTEMA COMPLETO DE ESTACIONAMENTO
# PYTHON + FLASK + SQLITE + SQL + HTML + CSS + DATETIME
# TUDO EM UM ÚNICO ARQUIVO: app.py
# ============================================================

import sqlite3
import math
import time
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    flash
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

app = Flask(__name__)
app.secret_key = "sistema-estacionamento-2026"

PASTA_PROJETO = Path(__file__).resolve().parent

# IMPORTANTE:
# CONTINUA USANDO O MESMO BANCO
BANCO = PASTA_PROJETO / "estacionamento.db"


# ============================================================
# DATETIME
# ============================================================

def agora():
    """
    Retorna data e hora atual no formato:
    2026-10-05 14:30:00
    """

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def formatar_data(data):
    """
    Transforma:
    2026-10-05 14:30:00

    em:
    05/10/2026 14:30:00
    """

    if not data:
        return "-"

    try:

        data_obj = datetime.strptime(
            data,
            "%Y-%m-%d %H:%M:%S"
        )

        return data_obj.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    except:
        return data


# ============================================================
# CONEXÃO COM SQLITE
# ============================================================

def conectar():

    conexao = sqlite3.connect(
        str(BANCO),
        timeout=60
    )

    conexao.row_factory = sqlite3.Row

    conexao.execute(
        "PRAGMA foreign_keys = ON"
    )

    conexao.execute(
        "PRAGMA busy_timeout = 60000"
    )

    return conexao


# ============================================================
# EVITAR DATABASE IS LOCKED
# ============================================================

def executar_com_retry(
    funcao,
    tentativas=10
):

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            return funcao()

        except sqlite3.OperationalError as erro:

            ultimo_erro = erro

            if "locked" not in str(
                erro
            ).lower():

                raise

            print(
                f"Banco ocupado. "
                f"Tentativa "
                f"{tentativa}/{tentativas}"
            )

            time.sleep(1)

    raise ultimo_erro


# ============================================================
# VERIFICAR SE COLUNA EXISTE
# ============================================================

def coluna_existe(
    conexao,
    tabela,
    coluna
):

    campos = conexao.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    for campo in campos:

        if campo["name"] == coluna:

            return True

    return False


# ============================================================
# ADICIONAR COLUNA NO BANCO ANTIGO
# ============================================================

def adicionar_coluna_se_precisar(
    conexao,
    tabela,
    coluna
):

    if not coluna_existe(
        conexao,
        tabela,
        coluna
    ):

        conexao.execute(
            f"""
            ALTER TABLE {tabela}
            ADD COLUMN {coluna} DATETIME
            """
        )


# ============================================================
# CRIAR / ATUALIZAR BANCO
# ============================================================

def criar_banco():

    def operacao():

        conexao = conectar()

        try:

            cursor = conexao.cursor()

            # =================================================
            # CLIENTES
            # =================================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (

                    id INTEGER
                    PRIMARY KEY
                    AUTOINCREMENT,

                    nome VARCHAR(80)
                    NOT NULL,

                    fone VARCHAR(20),

                    cpf VARCHAR(14)
                    NOT NULL
                    UNIQUE,

                    criado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    atualizado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP

                )
            """)

            # =================================================
            # VEÍCULOS
            # =================================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS veiculos (

                    id INTEGER
                    PRIMARY KEY
                    AUTOINCREMENT,

                    placa VARCHAR(10)
                    NOT NULL
                    UNIQUE,

                    modelo VARCHAR(50)
                    NOT NULL,

                    marca VARCHAR(50),

                    cor VARCHAR(30),

                    cliente_id INTEGER
                    NOT NULL,

                    criado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    atualizado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (
                        cliente_id
                    )

                    REFERENCES clientes(id)

                )
            """)

            # =================================================
            # PREÇOS
            # =================================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS precos (

                    id INTEGER
                    PRIMARY KEY
                    AUTOINCREMENT,

                    tipo_veiculo VARCHAR(30)
                    NOT NULL,

                    valor_hora DECIMAL(10,2)
                    NOT NULL,

                    valor_diaria DECIMAL(10,2)
                    NOT NULL,

                    criado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    atualizado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP

                )
            """)

            # =================================================
            # ESTADIAS
            # =================================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estadias (

                    id INTEGER
                    PRIMARY KEY
                    AUTOINCREMENT,

                    veiculo_id INTEGER
                    NOT NULL,

                    horario_entrada DATETIME
                    NOT NULL,

                    horario_saida DATETIME,

                    valor_total DECIMAL(10,2)
                    DEFAULT 0,

                    status VARCHAR(20)
                    NOT NULL
                    DEFAULT 'ABERTA',

                    criado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    atualizado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (
                        veiculo_id
                    )

                    REFERENCES veiculos(id)

                )
            """)

            # =================================================
            # PAGAMENTOS
            # =================================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamentos (

                    id INTEGER
                    PRIMARY KEY
                    AUTOINCREMENT,

                    estadia_id INTEGER
                    NOT NULL,

                    forma_pagamento VARCHAR(30)
                    NOT NULL,

                    valor_pago DECIMAL(10,2)
                    NOT NULL,

                    data_pago DATETIME
                    NOT NULL,

                    criado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    atualizado_em DATETIME
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (
                        estadia_id
                    )

                    REFERENCES estadias(id)

                )
            """)

            # =================================================
            # ATUALIZAR BANCO ANTIGO
            # =================================================

            adicionar_coluna_se_precisar(
                conexao,
                "clientes",
                "criado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "clientes",
                "atualizado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "veiculos",
                "criado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "veiculos",
                "atualizado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "precos",
                "criado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "precos",
                "atualizado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "estadias",
                "criado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "estadias",
                "atualizado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "pagamentos",
                "criado_em"
            )

            adicionar_coluna_se_precisar(
                conexao,
                "pagamentos",
                "atualizado_em"
            )

            # =================================================
            # PREENCHER DATETIME EM REGISTROS ANTIGOS
            # =================================================

            data = agora()

            tabelas = [
                "clientes",
                "veiculos",
                "precos",
                "estadias",
                "pagamentos"
            ]

            for tabela in tabelas:

                cursor.execute(
                    f"""
                    UPDATE {tabela}

                    SET criado_em = ?

                    WHERE
                        criado_em IS NULL
                        OR criado_em = ''
                    """,
                    (
                        data,
                    )
                )

                cursor.execute(
                    f"""
                    UPDATE {tabela}

                    SET atualizado_em = ?

                    WHERE
                        atualizado_em IS NULL
                        OR atualizado_em = ''
                    """,
                    (
                        data,
                    )
                )

            # =================================================
            # PREÇOS PADRÃO
            # =================================================

            quantidade = cursor.execute("""
                SELECT COUNT(*)
                FROM precos
            """).fetchone()[0]

            if quantidade == 0:

                data = agora()

                cursor.executemany("""
                    INSERT INTO precos
                    (
                        tipo_veiculo,
                        valor_hora,
                        valor_diaria,
                        criado_em,
                        atualizado_em
                    )

                    VALUES (?, ?, ?, ?, ?)
                """, [

                    (
                        "Carro",
                        10.00,
                        60.00,
                        data,
                        data
                    ),

                    (
                        "Moto",
                        5.00,
                        30.00,
                        data,
                        data
                    ),

                    (
                        "Caminhonete",
                        15.00,
                        90.00,
                        data,
                        data
                    )

                ])

            conexao.commit()

        except Exception:

            conexao.rollback()

            raise

        finally:

            conexao.close()

    executar_com_retry(
        operacao
    )


# ============================================================
# CALCULAR PREÇO
# ============================================================

def calcular_valor(
    horario_entrada,
    horario_saida,
    valor_hora,
    valor_diaria
):

    diferenca = (
        horario_saida
        -
        horario_entrada
    )

    segundos = (
        diferenca.total_seconds()
    )

    if segundos < 0:

        segundos = 0

    horas = math.ceil(
        segundos / 3600
    )

    if horas < 1:

        horas = 1

    dias = horas // 24

    horas_restantes = (
        horas % 24
    )

    valor_total = (
        dias
        *
        valor_diaria
    )

    if horas_restantes > 0:

        valor_restante = (
            horas_restantes
            *
            valor_hora
        )

        valor_total += min(
            valor_restante,
            valor_diaria
        )

    if dias == 0:

        valor_total = min(
            horas * valor_hora,
            valor_diaria
        )

    return (
        horas,
        round(
            valor_total,
            2
        )
    )


# ============================================================
# HTML + CSS
# ============================================================

PAGINA = """
<!DOCTYPE html>

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
Sistema de Estacionamento
</title>


<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        #0f172a;

    color:
        #e2e8f0;
}


header {

    background:
        linear-gradient(
            135deg,
            #020617,
            #172554,
            #0f172a
        );

    padding: 25px;

    border-bottom:
        1px solid #334155;
}


header h1 {

    margin: 0;

    color:
        #38bdf8;
}


header p {

    color:
        #94a3b8;
}


.container {

    max-width: 1500px;

    margin: auto;

    padding: 25px;
}


.relogio {

    background:
        #1e293b;

    padding: 15px;

    border-radius: 10px;

    border:
        1px solid #334155;

    margin-bottom: 20px;

    font-size: 18px;

    color:
        #38bdf8;
}


.cards {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(180px, 1fr)
        );

    gap: 15px;

    margin-bottom: 25px;
}


.card {

    background:
        #1e293b;

    border:
        1px solid #334155;

    border-radius: 12px;

    padding: 20px;
}


.card span {

    display: block;

    color:
        #94a3b8;

    font-size: 13px;

    text-transform:
        uppercase;

    margin-bottom: 8px;
}


.card strong {

    color:
        #38bdf8;

    font-size: 30px;
}


.grid {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(350px, 1fr)
        );

    gap: 20px;
}


.box {

    background:
        #1e293b;

    border:
        1px solid #334155;

    border-radius: 12px;

    padding: 20px;

    margin-bottom: 20px;

    overflow-x: auto;
}


h2 {

    color:
        #38bdf8;

    margin-top: 0;
}


label {

    display: block;

    margin-top: 12px;

    margin-bottom: 6px;

    font-weight: bold;
}


input,
select {

    width: 100%;

    padding: 11px;

    border-radius: 7px;

    border:
        1px solid #475569;

    background:
        #0f172a;

    color:
        white;
}


button {

    border: 0;

    border-radius: 7px;

    padding: 11px 17px;

    margin-top: 14px;

    background:
        #0284c7;

    color:
        white;

    font-weight: bold;

    cursor: pointer;
}


button:hover {

    filter:
        brightness(1.15);
}


.verde {
    background: #16a34a;
}


.vermelho {
    background: #dc2626;
}


table {

    width: 100%;

    border-collapse:
        collapse;

    margin-top: 15px;
}


th {

    background:
        #334155;

    color:
        #38bdf8;

    padding: 11px;

    text-align: left;

    white-space: nowrap;
}


td {

    padding: 11px;

    border-bottom:
        1px solid #334155;
}


.alerta {

    background:
        #14532d;

    border:
        1px solid #22c55e;

    padding: 14px;

    border-radius: 8px;

    margin-bottom: 20px;
}


.data {

    color:
        #fbbf24;

    white-space:
        nowrap;
}


.valor {

    color:
        #4ade80;

    font-weight:
        bold;
}


.aberta {

    color:
        #4ade80;

    font-weight:
        bold;
}


.finalizada {

    color:
        #fbbf24;

    font-weight:
        bold;
}


.vazio {

    text-align:
        center;

    color:
        #94a3b8;
}


@media(max-width:700px) {

    .grid {

        grid-template-columns:
            1fr;

    }

}

</style>

</head>


<body>


<header>

<h1>
🚗 Sistema de Estacionamento
</h1>

<p>
Python + SQLite + SQL + Flask + DATETIME
</p>

</header>


<div class="container">


<div class="relogio">

🕐 Data e hora do sistema:

<strong>
{{ data_atual }}
</strong>

</div>


{% with mensagens = get_flashed_messages() %}

{% for mensagem in mensagens %}

<div class="alerta">

{{ mensagem }}

</div>

{% endfor %}

{% endwith %}


<!-- ====================================================== -->
<!-- DASHBOARD -->
<!-- ====================================================== -->


<div class="cards">


<div class="card">

<span>
Clientes
</span>

<strong>
{{ total_clientes }}
</strong>

</div>


<div class="card">

<span>
Veículos
</span>

<strong>
{{ total_veiculos }}
</strong>

</div>


<div class="card">

<span>
Estacionados
</span>

<strong>
{{ total_estacionados }}
</strong>

</div>


<div class="card">

<span>
Finalizados
</span>

<strong>
{{ total_finalizadas }}
</strong>

</div>


<div class="card">

<span>
Total recebido
</span>

<strong>

R$
{{ "%.2f"|format(total_recebido) }}

</strong>

</div>


</div>


<!-- ====================================================== -->
<!-- CADASTROS -->
<!-- ====================================================== -->


<div class="grid">


<div class="box">

<h2>
👤 Cadastrar cliente
</h2>


<form
    method="POST"
    action="/cliente"
>


<label>
Nome
</label>

<input
    type="text"
    name="nome"
    required
>


<label>
Telefone
</label>

<input
    type="text"
    name="fone"
>


<label>
CPF
</label>

<input
    type="text"
    name="cpf"
    required
>


<button type="submit">

Cadastrar cliente

</button>


</form>

</div>


<div class="box">

<h2>
🚘 Cadastrar veículo
</h2>


<form
    method="POST"
    action="/veiculo"
>


<label>
Proprietário
</label>


<select
    name="cliente_id"
    required
>


<option value="">

Selecione

</option>


{% for cliente in clientes %}


<option value="{{ cliente.id }}">

{{ cliente.nome }}

-

{{ cliente.cpf }}

</option>


{% endfor %}


</select>


<label>
Placa
</label>

<input
    name="placa"
    required
>


<label>
Modelo
</label>

<input
    name="modelo"
    required
>


<label>
Marca
</label>

<input
    name="marca"
>


<label>
Cor
</label>

<input
    name="cor"
>


<button type="submit">

Cadastrar veículo

</button>


</form>

</div>


</div>


<!-- ====================================================== -->
<!-- ENTRADA -->
<!-- ====================================================== -->


<div class="box">

<h2>
🟢 Registrar entrada
</h2>


<form
    method="POST"
    action="/entrada"
>


<label>
Veículo
</label>


<select
    name="veiculo_id"
    required
>


<option value="">

Selecione o veículo

</option>


{% for veiculo in veiculos %}


<option value="{{ veiculo.id }}">

{{ veiculo.placa }}
-
{{ veiculo.modelo }}
-
{{ veiculo.cliente }}

</option>


{% endfor %}


</select>


<button
    class="verde"
    type="submit"
>

Registrar entrada

</button>


</form>

</div>


<!-- ====================================================== -->
<!-- ESTACIONADOS -->
<!-- ====================================================== -->


<div class="box">

<h2>
🅿️ Veículos estacionados
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Cliente
</th>

<th>
Placa
</th>

<th>
Modelo
</th>

<th>
Entrada
</th>

<th>
Criado em
</th>

<th>
Preço
</th>

<th>
Ação
</th>

</tr>


{% for e in estacionados %}


<tr>


<td>
{{ e.id }}
</td>


<td>
{{ e.cliente }}
</td>


<td>
{{ e.placa }}
</td>


<td>
{{ e.modelo }}
</td>


<td class="data">

{{ e.horario_entrada }}

</td>


<td class="data">

{{ e.criado_em }}

</td>


<td>


<form
    method="POST"
    action="/saida/{{ e.id }}"
>


<select
    name="preco_id"
    required
>


{% for preco in precos %}


<option value="{{ preco.id }}">

{{ preco.tipo_veiculo }}

-

R$
{{ "%.2f"|format(preco.valor_hora) }}/h

</option>


{% endfor %}


</select>


</td>


<td>


<button
    class="vermelho"
    type="submit"
>

Registrar saída

</button>


</form>


</td>


</tr>


{% else %}


<tr>

<td
    colspan="8"
    class="vazio"
>

Nenhum veículo estacionado.

</td>

</tr>


{% endfor %}


</table>

</div>


<!-- ====================================================== -->
<!-- PAGAMENTOS PENDENTES -->
<!-- ====================================================== -->


<div class="box">

<h2>
💰 Pagamentos pendentes
</h2>


<table>


<tr>

<th>
Estadia
</th>

<th>
Cliente
</th>

<th>
Placa
</th>

<th>
Entrada
</th>

<th>
Saída
</th>

<th>
Valor
</th>

<th>
Pagamento
</th>

</tr>


{% for e in pendentes %}


<tr>


<td>
{{ e.id }}
</td>


<td>
{{ e.cliente }}
</td>


<td>
{{ e.placa }}
</td>


<td class="data">

{{ e.horario_entrada }}

</td>


<td class="data">

{{ e.horario_saida }}

</td>


<td class="valor">

R$
{{ "%.2f"|format(e.valor_total) }}

</td>


<td>


<form
    method="POST"
    action="/pagar/{{ e.id }}"
>


<select
    name="forma_pagamento"
    required
>


<option value="PIX">
PIX
</option>


<option value="Dinheiro">
Dinheiro
</option>


<option value="Cartão de débito">
Cartão de débito
</option>


<option value="Cartão de crédito">
Cartão de crédito
</option>


</select>


<button
    class="verde"
    type="submit"
>

Pagar

</button>


</form>


</td>


</tr>


{% else %}


<tr>

<td
    colspan="7"
    class="vazio"
>

Nenhum pagamento pendente.

</td>

</tr>


{% endfor %}


</table>

</div>


<!-- ====================================================== -->
<!-- PREÇOS -->
<!-- ====================================================== -->


<div class="grid">


<div class="box">

<h2>
💲 Preços
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Tipo
</th>

<th>
Hora
</th>

<th>
Diária
</th>

<th>
Criado em
</th>

<th>
Atualizado em
</th>

</tr>


{% for preco in precos %}


<tr>


<td>
{{ preco.id }}
</td>


<td>
{{ preco.tipo_veiculo }}
</td>


<td>

R$
{{ "%.2f"|format(preco.valor_hora) }}

</td>


<td>

R$
{{ "%.2f"|format(preco.valor_diaria) }}

</td>


<td class="data">

{{ preco.criado_em }}

</td>


<td class="data">

{{ preco.atualizado_em }}

</td>


</tr>


{% endfor %}


</table>

</div>


<div class="box">

<h2>
➕ Cadastrar preço
</h2>


<form
    method="POST"
    action="/preco"
>


<label>
Tipo de veículo
</label>

<input
    name="tipo"
    required
>


<label>
Valor por hora
</label>

<input
    type="number"
    step="0.01"
    name="valor_hora"
    required
>


<label>
Valor da diária
</label>

<input
    type="number"
    step="0.01"
    name="valor_diaria"
    required
>


<button type="submit">

Cadastrar preço

</button>


</form>

</div>


</div>


<!-- ====================================================== -->
<!-- CLIENTES -->
<!-- ====================================================== -->


<div class="box">

<h2>
👥 Clientes
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Nome
</th>

<th>
Telefone
</th>

<th>
CPF
</th>

<th>
Criado em
</th>

<th>
Atualizado em
</th>

</tr>


{% for cliente in clientes %}


<tr>


<td>
{{ cliente.id }}
</td>


<td>
{{ cliente.nome }}
</td>


<td>
{{ cliente.fone or "-" }}
</td>


<td>
{{ cliente.cpf }}
</td>


<td class="data">

{{ cliente.criado_em }}

</td>


<td class="data">

{{ cliente.atualizado_em }}

</td>


</tr>


{% else %}


<tr>

<td
    colspan="6"
    class="vazio"
>

Nenhum cliente cadastrado.

</td>

</tr>


{% endfor %}


</table>

</div>


<!-- ====================================================== -->
<!-- VEÍCULOS -->
<!-- ====================================================== -->


<div class="box">

<h2>
🚗 Veículos
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Placa
</th>

<th>
Modelo
</th>

<th>
Marca
</th>

<th>
Cor
</th>

<th>
Proprietário
</th>

<th>
Criado em
</th>

<th>
Atualizado em
</th>

</tr>


{% for veiculo in veiculos %}


<tr>


<td>
{{ veiculo.id }}
</td>


<td>
{{ veiculo.placa }}
</td>


<td>
{{ veiculo.modelo }}
</td>


<td>
{{ veiculo.marca or "-" }}
</td>


<td>
{{ veiculo.cor or "-" }}
</td>


<td>
{{ veiculo.cliente }}
</td>


<td class="data">

{{ veiculo.criado_em }}

</td>


<td class="data">

{{ veiculo.atualizado_em }}

</td>


</tr>


{% else %}


<tr>

<td
    colspan="8"
    class="vazio"
>

Nenhum veículo cadastrado.

</td>

</tr>


{% endfor %}


</table>

</div>


<!-- ====================================================== -->
<!-- HISTÓRICO DE ESTADIAS -->
<!-- ====================================================== -->


<div class="box">

<h2>
📋 Histórico de estadias
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Cliente
</th>

<th>
Placa
</th>

<th>
Entrada
</th>

<th>
Saída
</th>

<th>
Valor
</th>

<th>
Status
</th>

<th>
Criado em
</th>

<th>
Atualizado em
</th>

</tr>


{% for e in historico %}


<tr>


<td>
{{ e.id }}
</td>


<td>
{{ e.cliente }}
</td>


<td>
{{ e.placa }}
</td>


<td class="data">

{{ e.horario_entrada }}

</td>


<td class="data">

{{ e.horario_saida or "-" }}

</td>


<td class="valor">

R$
{{ "%.2f"|format(e.valor_total) }}

</td>


<td>


{% if e.status == "ABERTA" %}

<span class="aberta">

ABERTA

</span>

{% else %}

<span class="finalizada">

FINALIZADA

</span>

{% endif %}


</td>


<td class="data">

{{ e.criado_em }}

</td>


<td class="data">

{{ e.atualizado_em }}

</td>


</tr>


{% else %}


<tr>

<td
    colspan="9"
    class="vazio"
>

Nenhuma estadia registrada.

</td>

</tr>


{% endfor %}


</table>

</div>


<!-- ====================================================== -->
<!-- PAGAMENTOS -->
<!-- ====================================================== -->


<div class="box">

<h2>
💳 Histórico de pagamentos
</h2>


<table>


<tr>

<th>
ID
</th>

<th>
Estadia
</th>

<th>
Cliente
</th>

<th>
Placa
</th>

<th>
Forma
</th>

<th>
Valor
</th>

<th>
Data pagamento
</th>

<th>
Criado em
</th>

<th>
Atualizado em
</th>

</tr>


{% for p in pagamentos %}


<tr>


<td>
{{ p.id }}
</td>


<td>
{{ p.estadia_id }}
</td>


<td>
{{ p.cliente }}
</td>


<td>
{{ p.placa }}
</td>


<td>
{{ p.forma_pagamento }}
</td>


<td class="valor">

R$
{{ "%.2f"|format(p.valor_pago) }}

</td>


<td class="data">

{{ p.data_pago }}

</td>


<td class="data">

{{ p.criado_em }}

</td>


<td class="data">

{{ p.atualizado_em }}

</td>


</tr>


{% else %}


<tr>

<td
    colspan="9"
    class="vazio"
>

Nenhum pagamento registrado.

</td>

</tr>


{% endfor %}


</table>

</div>


</div>

</body>

</html>
"""


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def inicio():

    conexao = conectar()

    try:

        # =====================================================
        # CLIENTES
        # =====================================================

        clientes = conexao.execute("""
            SELECT
                id,
                nome,
                fone,
                cpf,
                criado_em,
                atualizado_em

            FROM clientes

            ORDER BY nome
        """).fetchall()


        # =====================================================
        # VEÍCULOS
        # =====================================================

        veiculos = conexao.execute("""
            SELECT
                v.id,
                v.placa,
                v.modelo,
                v.marca,
                v.cor,
                v.cliente_id,
                v.criado_em,
                v.atualizado_em,

                c.nome AS cliente

            FROM veiculos v

            INNER JOIN clientes c
            ON c.id = v.cliente_id

            ORDER BY v.placa
        """).fetchall()


        # =====================================================
        # PREÇOS
        # =====================================================

        precos = conexao.execute("""
            SELECT
                id,
                tipo_veiculo,
                valor_hora,
                valor_diaria,
                criado_em,
                atualizado_em

            FROM precos

            ORDER BY id
        """).fetchall()


        # =====================================================
        # ESTACIONADOS
        # =====================================================

        estacionados = conexao.execute("""
            SELECT
                e.id,
                e.veiculo_id,
                e.horario_entrada,
                e.horario_saida,
                e.valor_total,
                e.status,
                e.criado_em,
                e.atualizado_em,

                v.placa,
                v.modelo,
                v.marca,

                c.nome AS cliente

            FROM estadias e

            INNER JOIN veiculos v
            ON v.id = e.veiculo_id

            INNER JOIN clientes c
            ON c.id = v.cliente_id

            WHERE
                e.status = 'ABERTA'

            ORDER BY
                e.horario_entrada DESC
        """).fetchall()


        # =====================================================
        # PAGAMENTOS PENDENTES
        # =====================================================

        pendentes = conexao.execute("""
            SELECT
                e.id,
                e.horario_entrada,
                e.horario_saida,
                e.valor_total,
                e.criado_em,
                e.atualizado_em,

                v.placa,

                c.nome AS cliente

            FROM estadias e

            INNER JOIN veiculos v
            ON v.id = e.veiculo_id

            INNER JOIN clientes c
            ON c.id = v.cliente_id

            WHERE
                e.status = 'FINALIZADA'

            AND NOT EXISTS (

                SELECT 1

                FROM pagamentos p

                WHERE
                    p.estadia_id = e.id

            )

            ORDER BY
                e.id DESC
        """).fetchall()


        # =====================================================
        # HISTÓRICO
        # =====================================================

        historico = conexao.execute("""
            SELECT
                e.id,
                e.horario_entrada,
                e.horario_saida,
                e.valor_total,
                e.status,
                e.criado_em,
                e.atualizado_em,

                v.placa,

                c.nome AS cliente

            FROM estadias e

            INNER JOIN veiculos v
            ON v.id = e.veiculo_id

            INNER JOIN clientes c
            ON c.id = v.cliente_id

            ORDER BY
                e.id DESC
        """).fetchall()


        # =====================================================
        # PAGAMENTOS
        # =====================================================

        pagamentos = conexao.execute("""
            SELECT
                p.id,
                p.estadia_id,
                p.forma_pagamento,
                p.valor_pago,
                p.data_pago,
                p.criado_em,
                p.atualizado_em,

                v.placa,

                c.nome AS cliente

            FROM pagamentos p

            INNER JOIN estadias e
            ON e.id = p.estadia_id

            INNER JOIN veiculos v
            ON v.id = e.veiculo_id

            INNER JOIN clientes c
            ON c.id = v.cliente_id

            ORDER BY
                p.id DESC
        """).fetchall()


        # =====================================================
        # DASHBOARD
        # =====================================================

        total_clientes = conexao.execute("""
            SELECT COUNT(*)
            FROM clientes
        """).fetchone()[0]


        total_veiculos = conexao.execute("""
            SELECT COUNT(*)
            FROM veiculos
        """).fetchone()[0]


        total_estacionados = conexao.execute("""
            SELECT COUNT(*)

            FROM estadias

            WHERE
                status = 'ABERTA'
        """).fetchone()[0]


        total_finalizadas = conexao.execute("""
            SELECT COUNT(*)

            FROM estadias

            WHERE
                status = 'FINALIZADA'
        """).fetchone()[0]


        total_recebido = conexao.execute("""
            SELECT
                COALESCE(
                    SUM(valor_pago),
                    0
                )

            FROM pagamentos
        """).fetchone()[0]


    finally:

        conexao.close()


    return render_template_string(

        PAGINA,

        data_atual=agora(),

        clientes=clientes,

        veiculos=veiculos,

        precos=precos,

        estacionados=estacionados,

        pendentes=pendentes,

        historico=historico,

        pagamentos=pagamentos,

        total_clientes=total_clientes,

        total_veiculos=total_veiculos,

        total_estacionados=total_estacionados,

        total_finalizadas=total_finalizadas,

        total_recebido=total_recebido

    )


# ============================================================
# CADASTRAR CLIENTE
# ============================================================

@app.route(
    "/cliente",
    methods=["POST"]
)
def cadastrar_cliente():

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    fone = request.form.get(
        "fone",
        ""
    ).strip()

    cpf = request.form.get(
        "cpf",
        ""
    ).strip()


    if not nome:

        flash(
            "Informe o nome do cliente."
        )

        return redirect(
            url_for("inicio")
        )


    if not cpf:

        flash(
            "Informe o CPF."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            data = agora()

            conexao.execute("""
                INSERT INTO clientes
                (
                    nome,
                    fone,
                    cpf,
                    criado_em,
                    atualizado_em
                )

                VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                fone,
                cpf,
                data,
                data
            ))

            conexao.commit()

        except:

            conexao.rollback()

            raise

        finally:

            conexao.close()


    try:

        executar_com_retry(
            operacao
        )

        flash(
            "Cliente cadastrado com sucesso!"
        )

    except sqlite3.IntegrityError:

        flash(
            "Esse CPF já está cadastrado."
        )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# CADASTRAR VEÍCULO
# ============================================================

@app.route(
    "/veiculo",
    methods=["POST"]
)
def cadastrar_veiculo():

    cliente_id = request.form.get(
        "cliente_id"
    )

    placa = request.form.get(
        "placa",
        ""
    ).strip().upper()

    modelo = request.form.get(
        "modelo",
        ""
    ).strip()

    marca = request.form.get(
        "marca",
        ""
    ).strip()

    cor = request.form.get(
        "cor",
        ""
    ).strip()


    if not cliente_id:

        flash(
            "Selecione o proprietário."
        )

        return redirect(
            url_for("inicio")
        )


    if not placa:

        flash(
            "Informe a placa."
        )

        return redirect(
            url_for("inicio")
        )


    if not modelo:

        flash(
            "Informe o modelo."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            data = agora()

            conexao.execute("""
                INSERT INTO veiculos
                (
                    placa,
                    modelo,
                    marca,
                    cor,
                    cliente_id,
                    criado_em,
                    atualizado_em
                )

                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                placa,
                modelo,
                marca,
                cor,
                cliente_id,
                data,
                data
            ))

            conexao.commit()

        except:

            conexao.rollback()

            raise

        finally:

            conexao.close()


    try:

        executar_com_retry(
            operacao
        )

        flash(
            "Veículo cadastrado com sucesso!"
        )

    except sqlite3.IntegrityError:

        flash(
            "Essa placa já está cadastrada."
        )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# CADASTRAR PREÇO
# ============================================================

@app.route(
    "/preco",
    methods=["POST"]
)
def cadastrar_preco():

    tipo = request.form.get(
        "tipo",
        ""
    ).strip()


    try:

        valor_hora = float(
            request.form.get(
                "valor_hora",
                0
            )
        )

        valor_diaria = float(
            request.form.get(
                "valor_diaria",
                0
            )
        )

    except ValueError:

        flash(
            "Digite valores válidos."
        )

        return redirect(
            url_for("inicio")
        )


    if not tipo:

        flash(
            "Informe o tipo do veículo."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            data = agora()

            conexao.execute("""
                INSERT INTO precos
                (
                    tipo_veiculo,
                    valor_hora,
                    valor_diaria,
                    criado_em,
                    atualizado_em
                )

                VALUES (?, ?, ?, ?, ?)
            """, (
                tipo,
                valor_hora,
                valor_diaria,
                data,
                data
            ))

            conexao.commit()

        except:

            conexao.rollback()

            raise

        finally:

            conexao.close()


    executar_com_retry(
        operacao
    )


    flash(
        "Preço cadastrado com sucesso!"
    )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# REGISTRAR ENTRADA
# ============================================================

@app.route(
    "/entrada",
    methods=["POST"]
)
def registrar_entrada():

    veiculo_id = request.form.get(
        "veiculo_id"
    )


    if not veiculo_id:

        flash(
            "Selecione um veículo."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            existente = conexao.execute("""
                SELECT id

                FROM estadias

                WHERE
                    veiculo_id = ?

                AND
                    status = 'ABERTA'
            """, (
                veiculo_id,
            )).fetchone()


            if existente:

                return False


            data = agora()


            conexao.execute("""
                INSERT INTO estadias
                (
                    veiculo_id,
                    horario_entrada,
                    horario_saida,
                    valor_total,
                    status,
                    criado_em,
                    atualizado_em
                )

                VALUES
                (
                    ?,
                    ?,
                    NULL,
                    0,
                    'ABERTA',
                    ?,
                    ?
                )
            """, (
                veiculo_id,
                data,
                data,
                data
            ))


            conexao.commit()


            return data


        except:

            conexao.rollback()

            raise


        finally:

            conexao.close()


    resultado = executar_com_retry(
        operacao
    )


    if resultado is False:

        flash(
            "Esse veículo já está estacionado."
        )

    else:

        flash(
            f"Entrada registrada em {resultado}."
        )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# REGISTRAR SAÍDA
# ============================================================

@app.route(
    "/saida/<int:estadia_id>",
    methods=["POST"]
)
def registrar_saida(
    estadia_id
):

    preco_id = request.form.get(
        "preco_id"
    )


    if not preco_id:

        flash(
            "Selecione uma tabela de preço."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            estadia = conexao.execute("""
                SELECT *

                FROM estadias

                WHERE
                    id = ?

                AND
                    status = 'ABERTA'
            """, (
                estadia_id,
            )).fetchone()


            if estadia is None:

                return None


            preco = conexao.execute("""
                SELECT *

                FROM precos

                WHERE
                    id = ?
            """, (
                preco_id,
            )).fetchone()


            if preco is None:

                return None


            entrada = datetime.strptime(
                estadia[
                    "horario_entrada"
                ],
                "%Y-%m-%d %H:%M:%S"
            )


            saida = datetime.now()


            horas, total = calcular_valor(

                entrada,

                saida,

                preco[
                    "valor_hora"
                ],

                preco[
                    "valor_diaria"
                ]

            )


            horario_saida = saida.strftime(
                "%Y-%m-%d %H:%M:%S"
            )


            conexao.execute("""
                UPDATE estadias

                SET
                    horario_saida = ?,

                    valor_total = ?,

                    status = 'FINALIZADA',

                    atualizado_em = ?

                WHERE
                    id = ?
            """, (
                horario_saida,
                total,
                horario_saida,
                estadia_id
            ))


            conexao.commit()


            return {
                "horas": horas,
                "total": total,
                "saida": horario_saida
            }


        except:

            conexao.rollback()

            raise


        finally:

            conexao.close()


    resultado = executar_com_retry(
        operacao
    )


    if resultado is None:

        flash(
            "Não foi possível registrar a saída."
        )

    else:

        flash(
            f"Saída registrada em "
            f"{resultado['saida']} | "
            f"{resultado['horas']} hora(s) | "
            f"Total R$ "
            f"{resultado['total']:.2f}"
        )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# PAGAMENTO
# ============================================================

@app.route(
    "/pagar/<int:estadia_id>",
    methods=["POST"]
)
def registrar_pagamento(
    estadia_id
):

    forma = request.form.get(
        "forma_pagamento"
    )


    if not forma:

        flash(
            "Selecione a forma de pagamento."
        )

        return redirect(
            url_for("inicio")
        )


    def operacao():

        conexao = conectar()

        try:

            estadia = conexao.execute("""
                SELECT *

                FROM estadias

                WHERE
                    id = ?

                AND
                    status = 'FINALIZADA'
            """, (
                estadia_id,
            )).fetchone()


            if estadia is None:

                return None


            pagamento_existente = conexao.execute("""
                SELECT id

                FROM pagamentos

                WHERE
                    estadia_id = ?
            """, (
                estadia_id,
            )).fetchone()


            if pagamento_existente:

                return False


            data = agora()


            conexao.execute("""
                INSERT INTO pagamentos
                (
                    estadia_id,
                    forma_pagamento,
                    valor_pago,
                    data_pago,
                    criado_em,
                    atualizado_em
                )

                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                estadia_id,
                forma,
                estadia[
                    "valor_total"
                ],
                data,
                data,
                data
            ))


            conexao.commit()


            return {
                "valor":
                    estadia[
                        "valor_total"
                    ],

                "data":
                    data
            }


        except:

            conexao.rollback()

            raise


        finally:

            conexao.close()


    resultado = executar_com_retry(
        operacao
    )


    if resultado is False:

        flash(
            "Essa estadia já foi paga."
        )

    elif resultado is None:

        flash(
            "Estadia não encontrada."
        )

    else:

        flash(
            f"Pagamento realizado! "
            f"Valor: R$ "
            f"{resultado['valor']:.2f} | "
            f"Data/Hora: "
            f"{resultado['data']}"
        )


    return redirect(
        url_for("inicio")
    )


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)

    print(
        "SISTEMA DE ESTACIONAMENTO".center(
            65
        )
    )

    print("=" * 65)


    try:

        criar_banco()

    except sqlite3.OperationalError as erro:

        print()
        print(
            "ERRO NO BANCO:"
        )

        print(
            erro
        )

        print()

        print(
            "Feche qualquer programa que "
            "esteja usando estacionamento.db."
        )

        raise SystemExit


    print()
    print(
        "Banco conectado e atualizado!"
    )

    print()
    print(
        "Banco usado:"
    )

    print(
        BANCO
    )

    print()
    print(
        "Data/Hora atual:"
    )

    print(
        agora()
    )

    print()
    print(
        "Abra no navegador:"
    )

    print()
    print(
        "http://127.0.0.1:5000"
    )

    print()


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=False
    )