import sys
from playwright.sync_api import sync_playwright
import json


def obter_erros(page):
    """
    Obtém as mensagens de erro ou aviso exibidas em um painel da página.

    A função tenta localizar um painel de erros representado por um <div> com o id 'painel-erros' e contendo uma 
    lista desordenada (<ul>) com a classe 'erros' ou 'warning'. Se encontrar essas mensagens, as concatena em uma única string.

    Parâmetros:
        page (objeto): Objeto da página web que permite a interação com o conteúdo.

    Retorno:
        str: Mensagens de erro ou aviso concatenadas em uma string. Retorna "Nenhum erro encontrado." se nenhum erro for localizado.
    
    Exceções:
        Retorna "Nenhum erro encontrado." em caso de exceção durante a execução.
    """
    try:
        # Esperar até que uma <ul> com a classe "erros" ou "warning" esteja visível
        page.locator("div[id='painel-erros'] ul.erros, div[id='painel-erros'] ul.warning").wait_for(state='visible', timeout=1000) 

        # Tentar localizar a <ul> com a classe "erros"
        ul_element = page.locator("div[id='painel-erros'] ul.erros")
        
        # Se não encontrar, tentar localizar a <ul> com a classe "warning"
        if ul_element.count() == 0:
            ul_element = page.locator("div[id='painel-erros'] ul.warning")
        
        # Verificar se a <ul> foi encontrada e se contém itens <li>
        if ul_element.count() > 0:
            erros_texto = [li.inner_text() for li in ul_element.locator('li').all()]
            if erros_texto:
                # Concatenar erros em uma única string, separados por ". "
                return '. '.join(erros_texto)
        return "Nenhum erro encontrado."
    
    except Exception as e:
        # Caso ocorra algum erro, retornar uma mensagem padrão
        return "Nenhum erro encontrado."


def obterProfessoresCargaHoraria(docentes):
    """
    Extrai uma lista de professores e suas respectivas cargas horárias a partir de uma string fornecida.

    A função divide a string de docentes, identificando professores e a carga horária associada, se presente.
    Quando múltiplos professores são mencionados, eles podem ser separados por vírgulas ou pela palavra "e".
    Se algum docente for identificado como "A DEFINIR", esse valor será incluído na lista de professores.

    Parâmetros:
        docentes (str): String contendo nomes de professores, com a possível carga horária entre parênteses.

    Retorno:
        tuple: Uma tupla contendo:
            - professores (list): Lista de dicionários contendo os professores com chave "id" (sempre None) e "nome".
            - cargaHoraria (str or None): A carga horária encontrada na string, ou None se não estiver presente.

    Exemplo de uso:
        docentes = "Prof. A (30h), Prof. B (40h) e Prof. C (20h)"
        retorno = obterProfessoresCargaHoraria(docentes)
        # retorno será: ([{'id': None, 'nome': 'Prof. A'}, {'id': None, 'nome': 'Prof. B'}, {'id': None, 'nome': 'Prof. C'}], '30h')
    """
    professores_arr = [prof.strip() for prof in docentes.split(',')]
    if ' e ' in professores_arr[-1]:
        professores_arr = [prof for part in professores_arr for prof in part.split(' e ')]

    professores = []
    cargaHoraria = None

    for professor in professores_arr:
        if '(' in professor and ')' in professor:
            nome = professor.split('(')[0].strip()
            if cargaHoraria is None:
                cargaHoraria = professor.split('(')[1].strip(')')
            professores.append({
                "id": None, 
                "nome": nome
            })
        elif "A DEFINIR" in professor:
            professores.append({
                "id": None,
                "nome": "A DEFINIR"
            })
    
    return professores, cargaHoraria


def extrair_dados_tabela(page, logs):
    """
    Extrai dados de uma tabela HTML de turmas eletivas em uma página web, organizando os resultados em um dicionário.

    A função busca por uma tabela de turmas no HTML da página, percorre suas linhas e extrai informações como nome da disciplina, código, semestre, professores, carga horária, horário e número de alunos. O resultado final é armazenado em um dicionário, que inclui as turmas encontradas e os logs de execução.

    Parâmetros:
        page (object): Instância da página onde a tabela está localizada, fornecida por um framework de automação como Playwright.
        logs (list): Lista para armazenar mensagens de log durante a execução da função.

    Retorno:
        dict: Um dicionário contendo:
            - logs (list): Lista com mensagens de log.
            - turmasEletivas (list): Lista de dicionários contendo os dados de cada turma extraída da tabela.

    Exemplo de uso:
        resultado = extrair_dados_tabela(page, logs)
        # retorno será um dicionário com logs e uma lista de turmas, cada uma contendo:
        # 'nome_da_disciplina', 'codigo_da_disciplina', 'semestre', 'codigo_da_turma',
        # 'professores', 'cargaHoraria', 'horario', e 'alunos'.

    Tratamento de exceções:
        - Em caso de erro durante a extração dos dados, uma mensagem de erro é adicionada aos logs e o resultado parcial é retornado.
    """
    resultado = {
        'logs': logs,
        'turmasEletivas': []
    }

    try:
        tabela = page.locator("table[id='lista-turmas']")  
        headTabela = tabela.locator('thead')
        linhasHead = headTabela.locator('tr').element_handles() 
        corpoTabela = tabela.locator('tbody')
        linhasCorpo = corpoTabela.locator('tr').element_handles() 
        
        disciplina = ""
        
        for linha in linhasCorpo:
            disciplina_element = linha.query_selector('td[colspan="17"]')
            if disciplina_element:
                codDisciplina = disciplina_element.inner_text().split(' - ')[0].strip()
                disciplina = disciplina_element.inner_text().split(' - ')[1].strip()
                continue  

            dados_turma = linha.query_selector_all('td')

            if dados_turma and len(dados_turma) >= 9:
                docentes = dados_turma[2].inner_text().strip()
                professores, cargaHoraria = obterProfessoresCargaHoraria(docentes)
                turma_data = {
                    'id': None,
                    'nome_da_disciplina': disciplina,
                    'codigo_da_disciplina': codDisciplina,
                    'semestre': dados_turma[0].inner_text().strip(),
                    'codigo_da_turma': dados_turma[1].inner_text().strip().split(' ')[1],
                    'professores': professores,
                    'cargaHoraria': cargaHoraria,
                    'horario': dados_turma[6].inner_text().strip(),
                    'alunos': dados_turma[8].inner_text().strip()
                    # 'situacao': dados_turma[3].inner_text().strip(),
                    # 'modalidade': dados_turma[4].inner_text().strip(),
                    # 'status': dados_turma[5].inner_text().strip(),
                    # 'local': dados_turma[7].inner_html().strip().replace('<br>', ' / ')
                }
                resultado['turmasEletivas'].append(turma_data)

        logs.append("Dados extraídos com sucesso")
      
        return resultado

    except Exception as e:
        logs.append(f"Ocorreu um erro ao extrair os dados: {e}")
        return resultado


def aplicar_filtros(page, logs, params):
    """
    Aplica filtros na página de consulta de turmas com base nos parâmetros fornecidos e executa a busca.

    A função preenche campos de seleção e de texto conforme os parâmetros recebidos, marcando checkboxes relacionados e executando a pesquisa na página web. O progresso da execução e eventuais erros são registrados nos logs.

    Parâmetros:
        page (object): Instância da página onde os filtros devem ser aplicados, fornecida por um framework de automação como Playwright.
        logs (list): Lista para armazenar mensagens de log durante a execução da função.
        params (dict): Dicionário contendo os parâmetros de filtro a serem aplicados, com possíveis chaves:
            - 'modalidadeCurso' (str): Modalidade do curso.
            - 'modalidadeTurma' (str): Modalidade da turma.
            - 'centroOuCampus' (str): Centro ou campus de referência.
            - 'departamento' (str): Departamento responsável.
            - 'cursoReservado' (str): Curso ao qual a turma é reservada.
            - 'horario' (str): Horário da turma.
            - 'codigoComponente' (str): Código do componente curricular (disciplina).
            - 'nomeComponente' (str): Nome do componente curricular.
            - 'nomeDocente' (str): Nome do docente responsável.

    Retorno:
        None: A função não retorna um valor explícito, mas preenche os filtros na página e clica no botão "Buscar".

    Exemplo de uso:
        aplicar_filtros(page, logs, {
            'modalidadeCurso': 'Presencial',
            'departamento': 'Matemática',
            'horario': 'Noturno'
        })
        # Isso aplicará os filtros de curso presencial, departamento de matemática e horário noturno.

    Tratamento de exceções:
        - Logs são gerados para cada filtro aplicado com sucesso.
        - Em caso de erro ao marcar checkboxes, preencher campos ou clicar no botão "Buscar", os erros são registrados nos logs.
    """
    modalidade_curso = params.get('modalidadeCurso', '')
    modalidade_turma = params.get('modalidadeTurma', '')
    centro_campus = params.get('centroOuCampus', '')
    departamento = params.get('departamento', '')
    cursoReservado = params.get('cursoReservado', '')
    horario = params.get('horario', '')
    codigo_componente = params.get('codigoComponente', '')
    nome_componente = params.get('nomeComponente', '')
    nome_docente = params.get('nomeDocente', '')
    codigo_turma = params.get('codigoTurma', '')

    # Filtros a serem aplicados
    # As propriedades representam os IDs dos selects da página de consultar turmas.
    # Os valores das propriedades representam a opção a ser escolhida naquele select.
    filtros = {
        'form:checkModalidade': {  
            'form:selectModalidadeEducacao': modalidade_curso,
        },
        'form:checkModalidadeTurma': {
            'form:selectModalidadeTurmaEducacao': modalidade_turma,
        },
        'form:checkCentro': {
            'form:centros': centro_campus,
        },
        'form:checkDepartamento': {
            'form:departamentos': departamento,
        },
        'form:checkCurso': {
            'form:selectCurso': cursoReservado,
        },
        'form:checkHorario': {
            'form:inputHorario': horario,
        },
        'form:checkCodigo': {
            'form:inputCodDisciplina': codigo_componente,
        },
        'form:checkDisciplina': {
            'form:inputNomeDisciplina': nome_componente,
        },
        'form:checkDocente': {
            'form:inputNomeDocente': nome_docente,
        },
        'form:checkCodigoTurma': {
            'form:inputCodTurma': codigo_turma,
        }
    }

    for check_id, fields in filtros.items():
        try:
            # Verifica se há algum valor não vazio para o filtro
            if any(v for v in fields.values() if v):  # Verifica se há algum valor não vazio
                checkbox_seletor = f'input[id="{check_id}"]'
                if not page.locator(checkbox_seletor).is_checked():
                    page.locator(checkbox_seletor).check()
                    logs.append(f"Checkbox '{check_id}' marcado.")
                else:
                    logs.append(f"Checkbox '{check_id}' já estava marcado.")
                
                # Preencher os campos relacionados ao checkbox
                for field_id, valor in fields.items():
                    if valor:  # Verifica se o valor não está vazio
                        try:
                            if 'input' in field_id:  # Trata como campo de texto
                                page.locator(f'input[id="{field_id}"]').fill(valor)
                                logs.append(f"Campo '{field_id}' preenchido com valor '{valor}'.")
                            else:  # Trata como campo de seleção
                                page.locator(f'select[id="{field_id}"]').select_option(label=valor)
                                logs.append(f"Filtro '{field_id}' selecionado com valor '{valor}'.")
                        except Exception as e:
                            logs.append(f"Erro ao preencher o campo '{field_id}': {e}")

        except Exception as e:
            logs.append(f"Erro ao marcar checkbox '{check_id}': {e}")

    # Clicar no botão "Buscar"
    try:
        page.locator('input[id="form:buttonBuscar"]').click()
        logs.append("Botão 'Buscar' clicado.")
    except Exception as e:
        logs.append(f"Erro ao clicar no botão 'Buscar': {e}")


def main(playwright, params):
    """
    Executa a automação de navegação no sistema SIGAA, aplicando filtros e extraindo dados de turmas.

    A função abre um navegador usando Playwright, navega até o portal SIGAA, faz login usando cookies,
    aplica filtros de turmas conforme os parâmetros fornecidos e extrai dados das turmas disponíveis.

    Parâmetros:
        playwright (object): Instância do Playwright para automação de navegador.
        params (dict): Dicionário contendo os parâmetros para a execução, com possíveis chaves:
            - 'userData' (str): Cookie de autenticação JSESSIONID do usuário no SIGAA.
            - Demais parâmetros usados para a função `aplicar_filtros`.

    Retorno:
        dict: Um dicionário com os resultados da extração de dados das turmas e os logs da operação. 
        Em caso de erro, retorna um dicionário com a mensagem de erro e o status HTTP 500.

    Exemplo de uso:
        resultado = main(playwright, {
            'userData': 'cookie_value',
            'modalidadeCurso': 'Presencial',
            'nomeComponente': 'Matemática'
        })

    Funcionalidades:
        - Abre o navegador em modo "headless" para execução em segundo plano.
        - Adiciona cookies de autenticação para navegar no portal SIGAA como usuário logado.
        - Navega até a página "Consultar Turma" através do menu.
        - Aplica filtros de busca com base nos parâmetros fornecidos.
        - Extrai dados da tabela de turmas após a aplicação dos filtros.
        - Fecha o navegador após a execução.

    Tratamento de exceções:
        - Em caso de falha, retorna uma mensagem de erro e o código de status 500.
        - Todas as ações importantes e erros são registrados nos logs para facilitar o diagnóstico.

    Dependências:
        - Funções `aplicar_filtros`, `obter_erros` e `extrair_dados_tabela` são chamadas durante o processo.
    """
    logs = []

    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        userData = params.get('userData', '')
        context.add_cookies([
            {
                'name': 'JSESSIONID',
                'value': userData,
                'domain': 'www.sigaa.ufs.br',
                'path': '/'
            }
        ])

        # Criar uma nova página e navegar para o site com os cookies
        page = context.new_page()
        logs.append("Abriu o navegador.")

        # Navega até a do menu principal de um usuário logado no SIGAA
        page.goto('https://www.sigaa.ufs.br/sigaa/verMenuPrincipal.do')
        logs.append("Acessou a página de Menu Principal do SIGAA.")

        # Clicar no botão "Ciente" para aceitar os cookies
    
        page.locator('text=Ciente').click()
        logs.append("Aceitou os cookies.")

        # Clicar no link "Portal Discente"
    
        page.locator('a:has-text("Portal Discente")').click()
        logs.append("Clicou em Portal Discente.")

        # Passar o mouse sobre o item do menu "Ensino"
        
        menu_item = page.locator('td.ThemeOfficeMainItem:has-text("Ensino")')
        menu_item.hover()
        logs.append("Passou o mouse sobre 'Ensino'.")

        # Clicar no item do menu "Consultar Turma"
        
        sub_menu_item = page.locator('td.ThemeOfficeMenuItemText:has-text("Consultar Turma")')
        sub_menu_item.click()
        logs.append("Clicou em 'Consultar Turma'.")

        # Aplicar filtros
        aplicar_filtros(page, logs, params)

        # Obter erros
        resultadoFiltros = obter_erros(page)

        # Verificar se há erros e decidir o resultado
        if resultadoFiltros != 'Nenhum erro encontrado.':
            logs.append(f"Erro ao aplicar filtros: {resultadoFiltros}")
            resultado = { 'logs': logs }
        else:
            logs.append("Nenhum erro encontrado ao aplicar os filtros.")
            resultado = extrair_dados_tabela(page, logs)

        # Fechar o navegador
        browser.close()

        return {
            'resultado': resultado,
            'status': 200
        }

    except Exception as e:
        logs.append(f"Ocorreu um erro: {str(e)}")
        return {
            'resultado': str(e),
            'status': 500
        }

   
if __name__ == "__main__":
    """
    Função principal que será executada quando o script for rodado diretamente.

    Descrição:
        - A função obtém os parâmetros passados via linha de comando (CLI) e os utiliza para chamar a função `main`.
        - Usa `sync_playwright` para iniciar a automação com Playwright.
        - Os resultados da função `main` são convertidos para JSON e impressos na saída padrão (normalmente o console).

    Parâmetros:
        Nenhum parâmetro direto. Os parâmetros são passados como argumento via linha de comando no formato JSON.

    Exemplo de uso via CLI:
        python scraping/webscraping.py '{"userData": "JSSESSION COOKIE AQUI", "modalidadeCurso": "PRESENCIAL", "modalidadeTurma": "PRESENCIAL", "centroOuCampus": "CENTRO DE CIÊNCIAS EXATAS E TECNOLOGIA", "departamento": "DEPARTAMENTO DE COMPUTAÇÃO - São Cristóvão", "nomeComponente": "ARQUITETURA DE COMPUTADORES"}'
    
    Dependências:
        - Módulo `json` para carregar os parâmetros de entrada e serializar os resultados para JSON.
        - Módulo `sys` para acessar os argumentos passados via linha de comando.
        - `sync_playwright` é usado para realizar a automação de navegador de maneira síncrona.
    """
    params = json.loads(sys.argv[1])
    with sync_playwright() as playwright:
        resultado = main(playwright, params)
        print(json.dumps(resultado)) 