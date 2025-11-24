# ARQUIVO: otimizador/utils.py

from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from collections import defaultdict

# Import relativo para acessar os modelos de dados
from .data_models import Projeto, ConfiguracaoProjeto, ParametrosOtimizacao, Instrutor


def gerar_lista_meses(data_inicio: str, data_fim: str) -> List[str]:
    """Gera lista de meses entre duas datas."""
    try:
        dt_inicio = datetime.strptime(data_inicio, "%d/%m/%Y").replace(day=1)
        dt_fim = datetime.strptime(data_fim, "%d/%m/%Y").replace(day=1)
    except ValueError as e:
        raise ValueError(f"Formato de data inválido. Use DD/MM/YYYY. Erro: {e}")
    if dt_fim < dt_inicio:
        raise ValueError(f"Data final ({data_fim}) deve ser posterior à inicial ({data_inicio})")

    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    lista_meses = []
    data_atual = dt_inicio
    while data_atual <= dt_fim:
        lista_meses.append(f"{meses_nomes[data_atual.month - 1]}/{str(data_atual.year)[2:]}")
        data_atual = data_atual + timedelta(days=32)
        data_atual = data_atual.replace(day=1)
    return lista_meses


def data_para_indice_mes(data: str, meses: List[str]) -> int:
    """Converte data para índice na lista de meses."""
    try:
        dt = datetime.strptime(data, "%d/%m/%Y")
        meses_map = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        mes_procurado = f"{meses_map[dt.month - 1]}/{str(dt.year)[2:]}"
        return meses.index(mes_procurado)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Data {data} ({mes_procurado}) não está no período de análise. Erro: {e}")


def calcular_meses_ativos(mes_inicio: int, duracao: int, meses_ferias: List[int], num_meses: int) -> List[int]:
    """Calcula meses em que a turma está ativa (excluindo férias)."""
    meses_ativos = []
    mes_atual = mes_inicio
    meses_trabalhados = 0
    while meses_trabalhados < duracao and mes_atual < num_meses:
        if mes_atual not in meses_ferias:
            meses_ativos.append(mes_atual)
            meses_trabalhados += 1
        mes_atual += 1
    return meses_ativos


def calcular_janela_inicio(mes_inicio_projeto: int, mes_fim_projeto: int, duracao: int, meses_ferias: List[int],
                           num_meses: int, meses: List[str]) -> Tuple[int, int]:
    """Calcula a janela válida de início garantindo término dentro do prazo."""
    inicio_min, inicio_max, janela_encontrada = mes_inicio_projeto, mes_inicio_projeto, False
    for m_inicio in range(mes_inicio_projeto, min(mes_fim_projeto + 1, num_meses)):
        meses_ativos = calcular_meses_ativos(m_inicio, duracao, meses_ferias, num_meses)
        if len(meses_ativos) == duracao and max(meses_ativos) <= mes_fim_projeto:
            inicio_max = m_inicio
            janela_encontrada = True
    if not janela_encontrada:
        raise ValueError("Não há janela válida de início para um dos projetos. Verifique durações e prazos.")
    print(f"   Janela válida: {meses[inicio_min]} a {meses[inicio_max]}")
    return inicio_min, inicio_max


def calcular_turmas_por_projeto(limite_total: int, percentual_prog: float) -> Tuple[int, int]:
    """Calcula número de turmas PROG e ROB baseado nos percentuais."""
    num_prog = round(limite_total * percentual_prog / 100)
    return num_prog, limite_total - num_prog


def converter_projetos_para_modelo(projetos_config: List[ConfiguracaoProjeto], meses: List[str],
                                   meses_ferias: List[int], parametros: ParametrosOtimizacao) -> List[Projeto]:
    """Converte configurações de projetos para estrutura do modelo."""
    print("\n" + "=" * 80 + "\nCONVERSÃO DE PROJETOS PARA MODELO\n" + "=" * 80)
    projetos_modelo = []
    for config in projetos_config:
        print(f"\nProcessando {config.nome}...")
        config.mes_inicio_idx = data_para_indice_mes(config.data_inicio, meses)
        config.mes_termino_idx = data_para_indice_mes(config.data_termino, meses)
        inicio_min, inicio_max = calcular_janela_inicio(config.mes_inicio_idx, config.mes_termino_idx,
                                                        config.duracao_curso, meses_ferias, len(meses), meses)

        prog_total, rob_total = (config.num_turmas, 0) if config.nome == 'DD1' else calcular_turmas_por_projeto(
            config.num_turmas, parametros.percentual_prog)
        print(f"   Total: {config.num_turmas} turmas (PROG: {prog_total}, ROB: {rob_total}) | Ondas: {config.ondas}")

        if config.ondas == 1:
            projetos_modelo.append(
                Projeto(config.nome, prog_total, rob_total, config.duracao_curso, inicio_min, inicio_max,
                        config.mes_termino_idx))
        else:
            prog_por_onda, rob_por_onda = prog_total // config.ondas, rob_total // config.ondas
            for onda_idx in range(config.ondas):
                prog_onda = prog_total - (
                            prog_por_onda * (config.ondas - 1)) if onda_idx == config.ondas - 1 else prog_por_onda
                rob_onda = rob_total - (
                            rob_por_onda * (config.ondas - 1)) if onda_idx == config.ondas - 1 else rob_por_onda
                nome_onda = f"{config.nome}_Onda{onda_idx + 1}"
                projetos_modelo.append(
                    Projeto(nome_onda, prog_onda, rob_onda, config.duracao_curso, inicio_min, inicio_max,
                            config.mes_termino_idx))
                print(f"   {nome_onda}: PROG={prog_onda}, ROB={rob_onda}")
    print("=" * 80)
    return projetos_modelo


def renumerar_instrutores_ativos(atribuicoes: List[Dict]) -> List[Dict]:
    """Renumera apenas os instrutores que receberam turmas."""
    print("\n--- Renumerando Instrutores Ativos ---")
    instrutores_usados = sorted(list(set(atr['instrutor'] for atr in atribuicoes)),
                                key=lambda i: (i.habilidade, int(i.id.split('_')[1])))
    mapeamento, contador_por_hab = {}, defaultdict(int)

    for inst_antigo in instrutores_usados:
        hab = inst_antigo.habilidade
        contador_por_hab[hab] += 1
        prefixo = 'PROG' if hab == 'PROG' else 'ROB'
        novo_id = f'{prefixo}_{contador_por_hab[hab]}'
        mapeamento[inst_antigo.id] = Instrutor(novo_id, hab, inst_antigo.capacidade, inst_antigo.laboratorio_id)

    for hab, count in sorted(contador_por_hab.items()): print(f"   • {hab}: {count} instrutores")

    return [{'turma': atr['turma'], 'instrutor': mapeamento[atr['instrutor'].id]} for atr in atribuicoes]
