# ARQUIVO: otimizador/data_models.py

from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

# Estruturas de dados para a lógica do otimizador
Projeto = namedtuple('Projeto', [
    'nome', 'prog', 'rob', 'duracao',
    'inicio_min', 'inicio_max', 'mes_fim_projeto'
])

Instrutor = namedtuple('Instrutor', [
    'id', 'habilidade', 'capacidade', 'laboratorio_id'
])

Turma = namedtuple('Turma', [
    'id', 'projeto', 'habilidade', 'mes_inicio', 'duracao'
])


@dataclass
class ConfiguracaoProjeto:
    """
    Configuração completa de um projeto educacional.

    Atributos:
        nome: Nome identificador do projeto
        data_inicio: Data de início no formato DD/MM/YYYY
        data_termino: Data de término no formato DD/MM/YYYY
        num_turmas: Número total de turmas do projeto
        duracao_curso: Duração de cada curso em meses
        ondas: Número de ondas para dividir o projeto (padrão: 1)
        turmas_min_por_mes: Número mínimo de turmas a iniciar por mês (usado na persistência)
    """
    nome: str
    data_inicio: str
    data_termino: str
    num_turmas: int
    duracao_curso: int
    ondas: int = 1
    turmas_min_por_mes: int = 1  # Adicionado para compatibilidade com a função de salvar

    # Campos calculados após validação
    mes_inicio_idx: int = field(default=None, init=False)
    mes_termino_idx: int = field(default=None, init=False)

    def __post_init__(self):
        """Valida os dados após inicialização"""
        self._validar_dados()

    def _validar_dados(self):
        """
        Valida todos os campos da configuração.

        Raises:
            ValueError: Se algum campo for inválido
        """
        if not self.nome or not isinstance(self.nome, str):
            raise ValueError(f"Nome do projeto inválido: {self.nome}")

        try:
            dt_inicio = datetime.strptime(self.data_inicio, "%d/%m/%Y")
            dt_termino = datetime.strptime(self.data_termino, "%d/%m/%Y")
        except ValueError as e:
            raise ValueError(f"Formato de data inválido para {self.nome}. Use DD/MM/YYYY. Erro: {e}")

        if dt_termino <= dt_inicio:
            raise ValueError(f"Data de término ({self.data_termino}) deve ser posterior à data de início ({self.data_inicio}) para {self.nome}")

        if not isinstance(self.num_turmas, int) or self.num_turmas <= 0 or self.num_turmas > 500:
            raise ValueError(f"Número de turmas deve ser inteiro entre 1 e 500. Recebido: {self.num_turmas} para {self.nome}")

        if not isinstance(self.duracao_curso, int) or self.duracao_curso <= 0 or self.duracao_curso > 12:
            raise ValueError(f"Duração do curso deve ser inteiro entre 1 e 12. Recebido: {self.duracao_curso} para {self.nome}")

        if not isinstance(self.ondas, int) or self.ondas <= 0 or self.ondas > 10:
            raise ValueError(f"Número de ondas deve ser inteiro entre 1 e 10. Recebido: {self.ondas} para {self.nome}")


@dataclass
class ParametrosOtimizacao:
    """
    Parâmetros globais para otimização.

    Atributos:
        capacidade_max_instrutor: Máximo de turmas por instrutor/mês
        percentual_prog: Percentual de turmas de Programação (0-100)
        spread_maximo: Spread máximo permitido entre instrutores
        meses_ferias: Lista de meses de férias (formato 'Mês/Ano')
        timeout_segundos: Tempo máximo para solver (em segundos)
    """
    capacidade_max_instrutor: int = 8
    percentual_prog: float = 60.0
    spread_maximo: int = 16
    meses_ferias: List[str] = field(default_factory=lambda: ['Jul/26', 'Dez/26'])
    timeout_segundos: int = 180

    def __post_init__(self):
        """Valida os parâmetros após inicialização"""
        self._validar_parametros()

    def _validar_parametros(self):
        """
        Valida todos os parâmetros.

        Raises:
            ValueError: Se algum parâmetro for inválido
        """
        if not isinstance(self.capacidade_max_instrutor, int) or not (1 <= self.capacidade_max_instrutor <= 20):
            raise ValueError(f"Capacidade deve estar entre 1 e 20. Recebido: {self.capacidade_max_instrutor}")

        if not isinstance(self.percentual_prog, (int, float)) or not (0 <= self.percentual_prog <= 100):
            raise ValueError(f"Percentual deve estar entre 0 e 100. Recebido: {self.percentual_prog}")

        if not isinstance(self.spread_maximo, int) or not (0 <= self.spread_maximo <= 50):
            raise ValueError(f"Spread deve estar entre 0 e 50. Recebido: {self.spread_maximo}")

        if not isinstance(self.timeout_segundos, int) or not (10 <= self.timeout_segundos <= 3600):
            raise ValueError(f"Timeout deve estar entre 10 e 3600 segundos. Recebido: {self.timeout_segundos}")

    @property
    def percentual_rob(self) -> float:
        """Calcula percentual de Robótica automaticamente"""
        return 100.0 - self.percentual_prog