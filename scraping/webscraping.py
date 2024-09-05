import time  # Para usar o sleep
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

def aplicar_filtros(page, filtros):
    for check_id, selects in filtros.items():
        try:
            # Marcar o checkbox
            checkbox_seletor = f'input[id="{check_id}"]'
            if not page.locator(checkbox_seletor).is_checked():
                page.locator(checkbox_seletor).check()
                print(f"Checkbox '{check_id}' marcado.")
            else:
                print(f"Checkbox '{check_id}' já estava marcado.")
            
            # Preencher os selects relacionados ao checkbox
            for select_id, valor in selects.items():
                try:
                    seletor_select = f'select[id="{select_id}"]'
                    page.locator(seletor_select).select_option(label=valor)
                    print(f"Filtro '{select_id}' selecionado com valor '{valor}'.")
                except Exception as e:
                    print(f"Erro ao selecionar filtro '{select_id}': {e}")
                
        except Exception as e:
            print(f"Erro ao marcar checkbox '{check_id}': {e}")

    # Clicar no botão "Buscar"
    try:
        page.locator('input[id="form:buttonBuscar"]').click()
        print("Botão 'Buscar' clicado.")
    except Exception as e:
        print(f"Erro ao clicar no botão 'Buscar': {e}")

def login_sigaa(playwright):

    usuario = os.getenv('SIGAA_USUARIO')
    senha = os.getenv('SIGAA_SENHA')

    # browser = playwright.chromium.launch(headless=True)  # Bom para headless
    browser = playwright.firefox.launch(headless=False)
    page = browser.new_page()

    # Navega até a página de login do SIGAA
    page.goto('https://www.sigaa.ufs.br/sigaa/verTelaLogin.do')

    # Clicar no botão "Ciente" para aceitar os cookies
    try:
        page.locator('text=Ciente').click()
        print("Aceitou os cookies.")
    except:
        print("Botão 'Ciente' não encontrado ou já aceito.")

    # Preencher o campo de usuário
    page.fill('input[name="user.login"]', usuario)
    
    # Preencher o campo de senha
    page.fill('input[name="user.senha"]', senha)
    
    # Clicar no botão de login
    page.click('input[type="submit"]')

    # Verifica se o login foi bem-sucedido (você pode ajustar conforme a resposta do site)
    if "Login ou senha inválido" in page.content():
        print("Login falhou. Verifique as credenciais.")
    else:
        print("Login realizado com sucesso!")


     # Esperar que a página carregue completamente antes de clicar no link
    page.wait_for_load_state('domcontentloaded')

    # Clicar no link "Portal Discente"
    try:
        page.locator('a:has-text("Portal Discente")').click()
        print("Clicou em Portal Discente.")
    except Exception as e:
        print(f"Erro ao clicar em 'Portal Discente': {e}")

   # Passar o mouse sobre o item do menu "Ensino"
    try:
        menu_item = page.locator('td.ThemeOfficeMainItem:has-text("Ensino")')
        menu_item.hover()
        print("Passou o mouse sobre 'Ensino'.")
    except Exception as e:
        print(f"Erro ao passar o mouse sobre 'Ensino': {e}")

    # Clicar no item do menu "Consultar Turma"
    try:
        sub_menu_item = page.locator('td.ThemeOfficeMenuItemText:has-text("Consultar Turma")')
        sub_menu_item.click()
        print("Clicou em 'Consultar Turma'.")
    except Exception as e:
        print(f"Erro ao clicar em 'Consultar Turma': {e}")

    # Filtros a serem aplicados
    # As propriedades representam os IDs dos selects da página de consultar turmas.
    # Os valores das propriedades representam a opção a ser escolhida naquele select.
    filtros = {
        'form:checkModalidade': {  
            'form:selectModalidadeEducacao': 'PRESENCIAL',
        },
        'form:checkModalidadeTurma': {
            'form:selectModalidadeTurmaEducacao': 'PRESENCIAL',
        },
        'form:checkCentro': {
            'form:centros': 'CENTRO DE CIÊNCIAS EXATAS E TECNOLOGIA',  
        },
        'form:checkDepartamento': {
            'form:departamentos': 'DEPARTAMENTO DE COMPUTAÇÃO - São Cristóvão' 
        }
    }
    # Aplicar filtros
    aplicar_filtros(page, filtros)


    time.sleep(60)

    # Fecha o navegador
    browser.close()

def main():
    with sync_playwright() as playwright:
        login_sigaa(playwright)

if __name__ == "__main__":
    main()