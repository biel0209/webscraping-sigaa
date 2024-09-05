from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Usando Chromium
        browser = p.chromium.launch(headless=False)
    
        # Usando Firefox
        # browser = p.firefox.launch(headless=False)
        
        # Usando WebKit
        # browser = p.webkit.launch(headless=False)
        page = browser.new_page()
        
        # Navega até um site
        page.goto('https://example.com')
        
        # Captura o título da página
        titulo = page.title()
        print(f"Título da página: {titulo}")
        
        # Captura o conteúdo da página
        conteudo = page.content()
        print(conteudo)
        
        # Fecha o navegador
        browser.close()

if __name__ == "__main__":
    main()
