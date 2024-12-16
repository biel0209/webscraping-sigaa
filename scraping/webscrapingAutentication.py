import sys
from playwright.sync_api import sync_playwright
import json


def main(playwright, params):
    """
    Realiza o login no sistema SIGAA da UFS e captura o valor do cookie JSESSIONID.

    Parâmetros:
    - playwright (Playwright): Instância do Playwright usada para interagir com o navegador.
    - params (dict): Dicionário contendo os parâmetros para o login, incluindo 'login' e 'password'.

    Retorna:
    - dict: Resultado da operação com os seguintes possíveis campos:
        - 'logs': Lista de mensagens de log.
        - 'JSESSIONID': Valor do cookie JSESSIONID se o login for bem-sucedido.
        - 'error': Mensagem de erro se ocorrer um problema.
        - 'status': Código de status HTTP (200 para sucesso, 400 para erro de login, 404 para cookie não encontrado, 500 para erro inesperado).
    """
    logs = []

    try:

        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        # Navega até a página de login do SIGAA
        page.goto('https://www.sigaa.ufs.br/sigaa/verTelaLogin.do')

        # Clicar no botão "Ciente" para aceitar os cookies
        page.locator('text=Ciente').click()
        logs.append("Aceitou os cookies e clicou em Ciente.")

        usuario = params.get('login', '')
        password = params.get('password', '')

        # Preencher o campo de usuário
        page.fill('input[name="user.login"]', usuario)
        # Preencher o campo de senha
        page.fill('input[name="user.senha"]', password)
        # Clicar no botão de login
        page.click('input[type="submit"]')

        # Verifica se o login foi bem-sucedido (você pode ajustar conforme a resposta do site)
        if "Usuário e/ou senha inválidos" in page.content():
            return {
                'error': 'Usuário e/ou senha inválidos',
                'status': 400
            }   
        else:
            logs.append("Login realizado com sucesso!")
        
        # Capturar o valor do cookie JSESSIONID
        cookies = page.context.cookies()
        jsessionid = None
        for cookie in cookies:
            if cookie['name'] == 'JSESSIONID':
                jsessionid = cookie['value']
                break

        if jsessionid == None: 
            return {
                'error': 'Cookie JSESSIONID não encontrado.',
                'status': 404
            }  

        # Fechar o navegador
        browser.close()
        return {
            'logs': logs,
            'JSESSIONID': jsessionid,
            'status': 200
        }
    except Exception as e:
        logs.append(f"Ocorreu um erro: {str(e)}")
        return {
            'error': str(e),
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
        python scraping/webscrapingAutentication.py '{"login": "SEU USER", "password": "SUA SENHA"}'
    
    Dependências:
        - Módulo `json` para carregar os parâmetros de entrada e serializar os resultados para JSON.
        - Módulo `sys` para acessar os argumentos passados via linha de comando.
        - `sync_playwright` é usado para realizar a automação de navegador de maneira síncrona.
    """
    params = json.loads(sys.argv[1])
    with sync_playwright() as playwright:
        resultado = main(playwright, params)
        print(json.dumps(resultado)) 