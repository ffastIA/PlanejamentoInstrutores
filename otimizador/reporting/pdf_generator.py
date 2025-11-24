# ARQUIVO: otimizador/reporting/pdf_generator.py

import os
from pathlib import Path  # <<< Adicionado para lidar com caminhos de arquivo
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import pandas as pd
from typing import List, Dict

# Import relativo
from ..data_models import ConfiguracaoProjeto


class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alias_nb_pages()
        self.font_family = 'Helvetica'  # Define um fallback inicial
        self.bullet = '-'  # Define um marcador de fallback

        # <<< ALTERAÇÃO 1: Lógica para encontrar e carregar as fontes do projeto >>>
        try:
            # Constrói o caminho para a pasta de fontes dentro do projeto
            # Path(__file__) é o caminho para este arquivo (pdf_generator.py)
            # .parent.parent leva para a pasta 'otimizador'
            font_dir = Path(__file__).parent.parent / "assets/fonts"

            # Registra as fontes usando o caminho completo
            self.add_font('DejaVu', '', font_dir / 'DejaVuSans.ttf')
            self.add_font('DejaVu', 'B', font_dir / 'DejaVuSans-Bold.ttf')
            self.add_font('DejaVu', 'I', font_dir / 'DejaVuSans-Italic.ttf')

            self.font_family = 'DejaVu'
            self.bullet = '•'
            print("[PDF] Fonte Unicode 'DejaVu' carregada com sucesso do projeto.")

        # <<< ALTERAÇÃO 2: Capturando o erro correto >>>
        except FileNotFoundError:
            # Este erro acontecerá se o usuário não seguir as instruções e os arquivos .ttf não estiverem na pasta.
            print("\n[AVISO PDF] Arquivos de fonte (.ttf) não encontrados na pasta 'otimizador/assets/fonts/'.")
            print("             Usando fonte básica (caracteres especiais podem não ser exibidos).")
            print("             Por favor, siga as instruções para baixar e adicionar as fontes ao projeto.\n")
            pass  # A execução continua usando Helvetica e '-' como marcador.

    def header(self):
        self.set_font(self.font_family, 'B', 16)
        self.cell(0, 10, 'Relatório Executivo de Otimização', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font(self.font_family, '', 10)
        self.cell(0, 8, 'Planejamento de Alocação de Instrutores', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    # ... (o resto da classe PDF permanece exatamente o mesmo) ...
    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family, 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} de {{nb}}', align='C')

    def chapter_title(self, title: str):
        self.set_font(self.font_family, 'B', 12)
        self.set_fill_color(224, 235, 255)
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L', fill=True)
        self.ln(4)

    def chapter_body(self, body: str):
        self.set_font(self.font_family, '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def metric_box(self, title: str, value: str, interpretation: str = ''):
        self.set_font(self.font_family, 'B', 11)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font(self.font_family, 'B', 18)
        self.cell(0, 10, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if interpretation:
            self.set_font(self.font_family, 'I', 9)
            self.multi_cell(0, 5, interpretation)
        self.ln(5)

    def add_image_section(self, title: str, image_path: str):
        if not image_path or not os.path.exists(image_path): return
        self.add_page()
        self.chapter_title(title)
        self.image(image_path, x=10, w=self.w - 20)
        self.ln(5)

    def add_table_from_dataframe(self, df: pd.DataFrame, title: str, max_rows: int = 25):
        if df.empty: return
        self.add_page()
        self.chapter_title(title)

        self.set_font(self.font_family, 'B', 8)
        self.set_fill_color(230, 230, 230)
        col_widths = {col: (self.w - 20) / len(df.columns) for col in df.columns}

        for col in df.columns: self.cell(col_widths[col], 7, str(col), border=1, align='C', fill=True)
        self.ln()

        self.set_font(self.font_family, '', 7)
        for _, row in df.head(max_rows).iterrows():
            for col in df.columns:
                cell_text = str(row[col])
                if len(cell_text) > 30:
                    cell_text = cell_text[:27] + '...'
                align = 'L' if isinstance(row[col], str) else 'R'
                self.cell(col_widths[col], 6, cell_text, border=1, align=align)
            self.ln()
        if len(df) > max_rows: self.cell(0, 6, f"... (mostrando {max_rows} de {len(df)} linhas)", align='C')


# A função gerar_relatorio_pdf permanece a mesma, mas agora usará o 'bullet' correto
def gerar_relatorio_pdf(projetos_config: List[ConfiguracaoProjeto],
                        resultados_estagio1: Dict,
                        resultados_estagio2: Dict,
                        graficos_paths: Dict,
                        serie_temporal_df: pd.DataFrame,
                        df_consolidada_instrutor: pd.DataFrame):
    """Gera o relatório executivo final em PDF."""
    print("\n--- Gerando Relatório Executivo PDF ---")
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()

    bullet = pdf.bullet

    # 1. SUMÁRIO EXECUTIVO
    pdf.chapter_title('1. Sumário Executivo (Principais Resultados)')
    # ... (resto da função igual)
    total_instrutores = resultados_estagio2.get('total_instrutores_flex', 'N/A')
    spread = resultados_estagio2.get('spread_carga', 'N/A')
    pico_max = resultados_estagio1.get('pico_max', 'N/A')

    spread_interpretacao = ''
    if isinstance(spread, int):
        if spread <= 5:
            spread_interpretacao = "Indica excelente balanceamento de carga de trabalho entre os instrutores."
        elif spread <= 15:
            spread_interpretacao = "Indica bom balanceamento, com pequenas variações na carga de trabalho."
        else:
            spread_interpretacao = "Indica desequilíbrio significativo, sugerindo revisão dos parâmetros."

    pdf.metric_box("Total de Instrutores Necessários", str(total_instrutores),
                   "Número de profissionais a serem alocados para cobrir toda a demanda do projeto.")
    pdf.metric_box("Balanceamento de Carga (Spread)", str(spread), spread_interpretacao)
    pdf.metric_box("Pico Máximo de Demanda", f"{pico_max} Turmas/Mês",
                   "Número máximo de turmas ativas simultaneamente em um único mês. Dimensiona a necessidade máxima de infraestrutura.")

    # 2. PREMISSAS
    pdf.chapter_title('2. Premissas e Parâmetros da Otimização')
    params = resultados_estagio1.get('parametros')
    premissas_body = (
        f"{bullet} Capacidade Máxima por Instrutor: {params.capacidade_max_instrutor} turmas/mês\n"
        f"{bullet} Proporção Alvo: {params.percentual_prog}% PROG / {params.percentual_rob}% ROB\n"
        f"{bullet} Spread Máximo Configurado: {params.spread_maximo} turmas\n"
        f"{bullet} Meses de Férias: {', '.join(params.meses_ferias)}"
    )
    pdf.chapter_body(premissas_body)

    # 3. CONFIGURAÇÃO DOS PROJETOS
    pdf.chapter_title('3. Configuração dos Projetos Analisados')
    for proj in projetos_config:
        pdf.set_font(pdf.font_family, 'B', 10)
        pdf.cell(0, 6, f"  {bullet} Projeto: {proj.nome}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(pdf.font_family, '', 10)
        pdf.multi_cell(0, 5, f"    - Período: {proj.data_inicio} a {proj.data_termino}\n"
                             f"    - Turmas: {proj.num_turmas} | Duração: {proj.duracao_curso} meses | Ondas: {proj.ondas}")
        pdf.ln(2)

    # 4. ANÁLISE GRÁFICA
    pdf.add_image_section("4.1. Carga Total por Instrutor e Balanceamento (Spread)",
                          graficos_paths.get('carga_instrutor'))
    pdf.add_image_section("4.2. Demanda Mensal por Habilidade (Programação vs. Robótica)",
                          graficos_paths.get('prog_rob'))
    pdf.add_image_section("4.3. Demanda Consolidada por Projeto ao Longo do Tempo", graficos_paths.get('projeto_mes'))
    pdf.add_image_section("4.4. Alocação Detalhada de Turmas por Instrutor e Projeto",
                          graficos_paths.get('instrutor_projeto'))

    # 5. APÊNDICE
    pdf.add_table_from_dataframe(serie_temporal_df, title="Apêndice A: Série Temporal da Demanda Mensal")
    pdf.add_table_from_dataframe(df_consolidada_instrutor, title="Apêndice B: Tabela Consolidada - Instrutor x Projeto")

    pdf_filename = 'Relatorio_Otimizacao_Completo.pdf'
    pdf.output(pdf_filename)
    print(f"\n[✓] Relatório Executivo PDF gerado com sucesso: {pdf_filename}")
    return pdf_filename