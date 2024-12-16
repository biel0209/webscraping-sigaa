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
        'alunosAptos': 0
    }

    try:
        tabela = page.locator("table:has-text('Matriz Curricular')")
        if tabela.count() > 0:
            tbody = tabela.locator("tbody")
            quantidade_tr = tbody.locator("tr").count()
            resultado['alunosAptos'] = quantidade_tr
        else:
            logs.append("Tabela 'Matriz Curricular' não encontrada.")
        logs.append("Quantidade de alunos aptos extraída com sucesso.")
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
    componenteCurricular = params.get('componenteCurricular', '')
    anoPeriodoIngresso = params.get('anoPeriodoIngresso', '')
    ano, periodo = anoPeriodoIngresso.split('.')
    
    try:
        
        # Selecionar componente curricular
        row = page.locator("tr:has(label:text('Componente Curricular'))")
        select_element = row.locator("td >> nth=1 select")
        # Obtém todas as opções do <select>
        options = select_element.locator("option")
        count = options.count()
        # Itera pelas opções e verifica se o texto contém o valor desejado
        for i in range(count):
            option_text = options.nth(i).text_content()
            if componenteCurricular in option_text:  # Verifica se contém o texto
                options.nth(i).click()  # Seleciona a opção
                logs.append(f"Filtro 'Componente Curricular' selecionado com valor '{componenteCurricular}'.")
                break
        
        # Preencher ano e período
        page.locator(f'input[id="form:inputAno"]').fill(ano)
        logs.append(f"Campo 'form:inputAno' preenchido com valor '{ano}'.")
        page.locator(f'input[id="form:inputPeriodo"]').fill(periodo)
        logs.append(f"Campo 'form:inputPeriodo' preenchido com valor '{periodo}'.")
        
        # Marcar checkbox de Listar Apenas Alunos Habilitados a Cursar o Componente
        tr_element= page.locator("tr:has-text('Listar Apenas Alunos Habilitados a Cursar o Componente')")
        checkbox_td = tr_element.locator("td").nth(0)
        checkbox_td.locator("input[type='checkbox']").check()
        logs.append(f"Checkbox 'Listar Apenas Alunos Habilitados a Cursar o Componente' marcado.")
    
    
    except Exception as e:
            logs.append(f"Erro ao preencher filtros: {e}")
    

    # Clicar no botão "Gerar Relatório"
    try:
        page.locator("input[value='Gerar Relatório']").click()
        logs.append("Botão 'Gerar Relatório' clicado.")
    except Exception as e:
        logs.append(f"Erro ao clicar no botão 'Gerar Relatório': {e}")


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
        
        # Se entrar na página de vínculo, clicar em "Chefia/Diretoria"
        if page.locator('a:has-text("Chefia/Diretoria")').count() > 0:
            page.locator('a:has-text("Chefia/Diretoria")').click()
            logs.append("Entrou na página de vínculos e clicou em 'Chefia/Diretoria'.")

        # Se aparecer a página de aviso de férias de docentes, clicar em
        # "Entrar no Portal Docente"
        if page.locator(':has-text("Entrar no Portal Docente")').count() > 0:
            page.locator(':has-text("Entrar no Portal Docente")').click()
            logs.append("Entrou na página de aviso de férias de docentes e clicou em 'Entrar no Portal Docente'.")

        # Se não aparecer a opção de "Portal Coord. Graduação" na página,
        # clica em "Módulos" e depois em ""Portal Coord. Graduação""
        if page.locator(':has-text("Portal Coord. Graduação")').count() == 0:
            page.locator(':has-text("Módulos")').click()
            page.locator(':has-text("Portal Coord. Graduação")').click()
            logs.append("Clicou em Módulos e depois em 'Portal Coord. Graduação'.")
        else:
            page.locator(':has-text("Portal Coord. Graduação")').click()
            logs.append("Clicou em 'Portal Coord. Graduação'.")
            

        # Passar o mouse sobre o item do menu "Relatórios"
        menu_item = page.locator('td.ThemeOfficeMainItem:has-text("Relatórios")')
        menu_item.hover()
        logs.append("Passou o mouse sobre 'Relatórios'.")
        
        # Passar o mouse sobre o item do menu "Discentes"
        menu_item = page.locator('td.ThemeOfficeMainItem:has-text("Discentes")')
        menu_item.hover()
        logs.append("Passou o mouse sobre 'Discentes'.")

        # Clicar no item do menu "Alunos Aptos a Cursar Determinado Componente Curricular"
        sub_menu_item = page.locator('td.ThemeOfficeMenuItemText:has-text("Alunos Aptos a Cursar Determinado Componente Curricular")')
        sub_menu_item.click()
        logs.append("Clicou em 'Alunos Aptos a Cursar Determinado Componente Curricular'.")

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