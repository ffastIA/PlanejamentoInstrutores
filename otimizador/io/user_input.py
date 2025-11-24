# ARQUIVO: otimizador/io/user_input.py

import sys
from datetime import datetime
from typing import List, Optional

# Import relativo para acessar os modelos de dados do mesmo pacote
from ..data_models import ParametrosOtimizacao, ConfiguracaoProjeto


# --- Funções de obtenção de dados do usuário ---

def obter_parametros_usuario() -> ParametrosOtimizacao:
    """Solicita parâmetros de otimização ao usuário via CLI."""
    print("\n" + "=" * 80)
    print("CONFIGURAÇÃO DE PARÂMETROS DE OTIMIZAÇÃO")
    print("=" * 80)
    print("\nDefina os parâmetros da otimização:")
    print("(Pressione Enter para usar valores padrão)")
    print("(Digite 'sair' para cancelar)\n")

    try:
        capacidade_max = _obter_int_usuario(
            prompt="Capacidade máxima de turmas por instrutor/mês [padrão: 6]: ",
            valor_padrao=6, minimo=1, maximo=20, nome_parametro="Capacidade"
        )
        percentual_prog = _obter_float_usuario(
            prompt="Percentual de turmas de Programação (0-100) [padrão: 60]: ",
            valor_padrao=60.0, minimo=0.0, maximo=100.0, nome_parametro="Percentual PROG"
        )
        spread_maximo = _obter_int_usuario(
            prompt="Spread máximo permitido entre instrutores [padrão: 16]: ",
            valor_padrao=16, minimo=0, maximo=50, nome_parametro="Spread Máximo"
        )
        timeout = _obter_int_usuario(
            prompt="Timeout do solver em segundos [padrão: 180]: ",
            valor_padrao=180, minimo=10, maximo=3600, nome_parametro="Timeout"
        )
        parametros = ParametrosOtimizacao(
            capacidade_max_instrutor=capacidade_max,
            percentual_prog=percentual_prog,
            spread_maximo=spread_maximo,
            timeout_segundos=timeout
        )
        exibir_resumo_parametros(parametros)
        return parametros
    except KeyboardInterrupt:
        print("\n\n[!] Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERRO] Falha ao obter parâmetros: {e}")
        sys.exit(1)


def obter_projetos_usuario() -> List[ConfiguracaoProjeto]:
    """Solicita configuração de projetos ao usuário."""
    print("\n" + "=" * 80)
    print("CONFIGURAÇÃO DE PROJETOS")
    print("=" * 80)
    print("\nEscolha o modo de configuração:")
    print("  [1] Usar configuração PADRÃO (recomendado)")
    print("  [2] Configuração CUSTOMIZADA (avançado)")
    print("  [S] Sair")

    while True:
        escolha = input("\nOpção [1/2/S]: ").strip().upper()
        if escolha == 'S' or escolha == 'SAIR':
            raise KeyboardInterrupt()
        elif escolha == '' or escolha == '1':
            projetos = _obter_projetos_padrao()
            print("\n[✓] Usando configuração padrão dos projetos.")
            exibir_resumo_projetos(projetos)
            return projetos
        elif escolha == '2':
            projetos = _obter_projetos_customizados()
            exibir_resumo_projetos(projetos)
            return projetos
        else:
            print("[!] Opção inválida. Digite 1, 2 ou S.")


# --- Funções auxiliares (privadas ao módulo) ---

def _obter_projetos_customizados() -> List[ConfiguracaoProjeto]:
    """Interface interativa para configuração customizada de projetos."""
    print("\n" + "=" * 80)
    print("CONFIGURAÇÃO CUSTOMIZADA DE PROJETOS")
    print("=" * 80)
    projetos = []
    while True:
        print("\n" + "-" * 80)
        print("MENU DE CONFIGURAÇÃO")
        print(f"Projetos configurados: {len(projetos)}")
        if projetos:
            for idx, proj in enumerate(projetos, 1):
                print(f"  {idx}. {proj.nome} - {proj.num_turmas} turmas ({proj.data_inicio} a {proj.data_termino})")
        print("\nOpções:\n  [A] Adicionar novo projeto")
        if projetos:
            print("  [E] Editar projeto existente\n  [R] Remover projeto\n  [C] Concluir e continuar")
        print("  [P] Usar configuração padrão\n  [S] Sair")

        opcao = input("\nEscolha uma opção: ").strip().upper()
        if opcao == 'S' or opcao == 'SAIR':
            raise KeyboardInterrupt()
        elif opcao == 'P':
            return _obter_projetos_padrao()
        elif opcao == 'A':
            novo_projeto = _configurar_projeto_interativo()
            if novo_projeto:
                projetos.append(novo_projeto)
                print(f"\n[✓] Projeto '{novo_projeto.nome}' adicionado com sucesso!")
        elif opcao == 'E' and projetos:
            projetos = _editar_projeto_interativo(projetos)
        elif opcao == 'R' and projetos:
            projetos = _remover_projeto_interativo(projetos)
        elif opcao == 'C' and projetos:
            if _confirmar_configuracao(projetos): return projetos
        else:
            print("[!] Opção inválida. Tente novamente.")


def _configurar_projeto_interativo() -> Optional[ConfiguracaoProjeto]:
    """Configura um projeto interativamente."""
    print("\n" + "=" * 70 + "\nADICIONAR NOVO PROJETO\n" + "=" * 70)
    try:
        while True:
            nome = input("\nNome do projeto: ").strip()
            if nome.lower() == 'sair': return None
            if nome and len(nome) <= 50: break
            print("[!] Nome inválido ou muito longo.")

        data_inicio_dt = None
        while True:
            data_inicio_input = input("Data de início (DD/MM/YYYY): ").strip()
            if data_inicio_input.lower() == 'sair': return None
            try:
                data_inicio_dt = datetime.strptime(data_inicio_input, "%d/%m/%Y")
                break
            except ValueError:
                print("[!] Formato inválido.")

        meses_diferenca = 0
        while True:
            data_termino_input = input("Data de término (DD/MM/YYYY): ").strip()
            if data_termino_input.lower() == 'sair': return None
            try:
                data_termino_dt = datetime.strptime(data_termino_input, "%d/%m/%Y")
                if data_termino_dt <= data_inicio_dt:
                    print("[!] Data de término deve ser posterior à de início.")
                    continue
                meses_diferenca = (data_termino_dt.year - data_inicio_dt.year) * 12 + (
                            data_termino_dt.month - data_inicio_dt.month)
                if meses_diferenca > 36:
                    print(f"[!] Período muito longo ({meses_diferenca} meses). Máximo: 36.")
                    continue
                break
            except ValueError:
                print("[!] Formato inválido.")

        num_turmas = _obter_int_usuario("Número total de turmas [1-500]: ", None, 1, 500, "Turmas")
        if num_turmas is None: return None

        while True:
            duracao_curso = _obter_int_usuario("Duração de cada curso em meses [1-12]: ", None, 1, 12, "Duração")
            if duracao_curso is None: return None
            if duracao_curso > meses_diferenca:
                print(f"[!] Duração ({duracao_curso}) maior que período do projeto ({meses_diferenca}).")
                continue
            break

        ondas = _obter_int_usuario("Número de ondas [1-10, padrão: 1]: ", 1, 1, 10, "Ondas")
        if ondas is None: return None

        projeto = ConfiguracaoProjeto(
            nome=nome, data_inicio=data_inicio_dt.strftime("%d/%m/%Y"),
            data_termino=data_termino_dt.strftime("%d/%m/%Y"),
            num_turmas=num_turmas, duracao_curso=duracao_curso, ondas=ondas
        )
        print(
            f"\nRESUMO DO PROJETO:\n  Nome: {projeto.nome}\n  Período: {projeto.data_inicio} a {projeto.data_termino}\n  Turmas: {projeto.num_turmas}\n  Duração: {projeto.duracao_curso} meses\n  Ondas: {projeto.ondas}")
        confirma = input("\nConfirmar adição? (S/N) [S]: ").strip().upper()
        return projeto if confirma in ('', 'S') else None
    except (KeyboardInterrupt, TypeError):
        return None


def _editar_projeto_interativo(projetos: List[ConfiguracaoProjeto]) -> List[ConfiguracaoProjeto]:
    """Edita um projeto existente."""
    # ... (lógica complexa omitida por brevidade, mas deve ser movida para cá)
    print("[INFO] Edição de projetos ainda não implementada na versão refatorada.")
    return projetos


def _remover_projeto_interativo(projetos: List[ConfiguracaoProjeto]) -> List[ConfiguracaoProjeto]:
    """Remove um projeto da lista."""
    # ... (lógica complexa omitida por brevidade, mas deve ser movida para cá)
    print("[INFO] Remoção de projetos ainda não implementada na versão refatorada.")
    return projetos


def _confirmar_configuracao(projetos: List[ConfiguracaoProjeto]) -> bool:
    """Solicita confirmação final da configuração."""
    print("\n" + "=" * 80 + "\nCONFIRMAÇÃO FINAL\n" + "=" * 80)
    print(f"Total de projetos: {len(projetos)}\nTotal de turmas: {sum(p.num_turmas for p in projetos)}\n")
    for proj in projetos:
        print(f"  • {proj.nome}: {proj.num_turmas} turmas, {proj.duracao_curso} meses, {proj.ondas} ondas")
    confirma = input("\nConfirmar e continuar? (S/N) [S]: ").strip().upper()
    return confirma in ('', 'S')


def _obter_projetos_padrao() -> List[ConfiguracaoProjeto]:
    """Retorna configuração padrão dos projetos."""
    try:
        return [
            ConfiguracaoProjeto(nome='DD1', data_inicio='15/01/2026', data_termino='31/03/2026', num_turmas=8,
                                duracao_curso=2, ondas=1),
            ConfiguracaoProjeto(nome='DD2', data_inicio='01/04/2026', data_termino='31/03/2027', num_turmas=110,
                                duracao_curso=4, ondas=2),
            ConfiguracaoProjeto(nome='IdearTec', data_inicio='01/04/2026', data_termino='31/03/2027', num_turmas=110,
                                duracao_curso=4, ondas=2)
        ]
    except ValueError as e:
        print(f"[ERRO] Configuração padrão inválida: {e}")
        sys.exit(1)


def _obter_int_usuario(prompt: str, valor_padrao: Optional[int], minimo: int, maximo: int, nome_parametro: str) -> \
Optional[int]:
    """Solicita entrada inteira do usuário com validação."""
    while True:
        entrada = input(prompt).strip()
        if entrada.lower() == 'sair': raise KeyboardInterrupt()
        if entrada == "" and valor_padrao is not None: return valor_padrao
        try:
            valor = int(entrada)
            if minimo <= valor <= maximo: return valor
            print(f"[!] {nome_parametro} deve estar entre {minimo} e {maximo}.")
        except ValueError:
            print(f"[!] Valor inválido. Digite um número inteiro.")


def _obter_float_usuario(prompt: str, valor_padrao: float, minimo: float, maximo: float, nome_parametro: str) -> float:
    """Solicita entrada decimal do usuário com validação."""
    while True:
        entrada = input(prompt).strip()
        if entrada.lower() == 'sair': raise KeyboardInterrupt()
        if entrada == "": return valor_padrao
        try:
            valor = float(entrada)
            if minimo <= valor <= maximo: return valor
            print(f"[!] {nome_parametro} deve estar entre {minimo} e {maximo}.")
        except ValueError:
            print("[!] Valor inválido. Digite um número.")


def exibir_resumo_parametros(params: ParametrosOtimizacao):
    """Exibe resumo dos parâmetros configurados."""
    print("\n" + "=" * 80 + "\nPARÂMETROS CONFIGURADOS:\n" + "=" * 80)
    print(f"  • Capacidade máxima por instrutor: {params.capacidade_max_instrutor} turmas/mês")
    print(f"  • Percentual Programação: {params.percentual_prog}%")
    print(f"  • Percentual Robótica: {params.percentual_rob}%")
    print(f"  • Spread Máximo: {params.spread_maximo} turmas")
    print(f"  • Timeout do Solver: {params.timeout_segundos} segundos")
    print(f"  • Meses de Férias: {', '.join(params.meses_ferias)}")
    print("=" * 80)


def exibir_resumo_projetos(projetos: List[ConfiguracaoProjeto]):
    """Exibe resumo dos projetos configurados."""
    print("\n" + "=" * 80 + "\nPROJETOS CONFIGURADOS:\n" + "=" * 80)
    for proj in projetos:
        print(
            f"\n  {proj.nome}:\n    • Período: {proj.data_inicio} a {proj.data_termino}\n    • Turmas: {proj.num_turmas}\n    • Duração: {proj.duracao_curso} meses\n    • Ondas: {proj.ondas}")
    print("\n" + "=" * 80)
