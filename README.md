# 🤖 projetoBotManut (Chatbot para Auxílio Técnico)

---

## 💡 Sobre o Projeto

Este projeto consiste em um **chatbot inteligente** desenvolvido para auxiliar técnicos de manutenção de aeronaves no dia a dia. Utilizando o poder das APIs de Inteligência Artificial do Google Cloud, o chatbot é capaz de analisar imagens de manuais técnicos (ou outros documentos relacionados) e fornecer **explicações simplificadas e concisas** sobre os procedimentos ou informações contidas nelas.

O objetivo é agilizar a consulta de informações complexas, tornando o trabalho dos técnicos mais eficiente e minimizando o tempo gasto na busca por detalhes em documentações extensas.

---

## ✨ Funcionalidades

* **Análise de Imagens:** Capacidade de receber imagens contendo texto (ex: páginas de manuais, diagramas, cartões de inspeção).
* **Extração de Texto (OCR):** Utiliza a **Google Cloud Vision API** para reconhecer e extrair o texto presente nas imagens.
* **Tradução Inteligente:** Se necessário, o texto extraído pode ser traduzido para o português utilizando a **Google Cloud Translation API**.
* **Simplificação de Conteúdo:** Emprega a **Google Gemini API** para processar o texto e gerar explicações claras, concisas e fáceis de entender para os técnicos.
* **Interface Web Intuitiva:** Chatbot acessível via navegador, facilitando o uso em diversos dispositivos.

---

## 🚀 Como Acessar o Chatbot (Em Produção)

O bot de Manutenção está atualmente hospedado no Google Cloud App Engine.

**Acesse o Chatbot:** https://botmanut78gav.streamlit.app/
---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.12
* **Framework Web:** Flask
* **Servidor WSGI:** Gunicorn
* **Hospedagem:** Google Cloud App Engine (Standard Environment)
* **APIs de IA do Google Cloud:**
    * Google Gemini API (para geração de texto simplificado)
    * Google Cloud Vision API (para OCR e análise de imagens)
    * Google Cloud Translation API (para tradução de texto)

---

## 📚 Notebook de Desenvolvimento (Exploração da Lógica de IA)

Você pode encontrar o notebook original do Google Colab que foi utilizado para desenvolver e testar a lógica de extração de texto, tradução e simplificação com as APIs do Google. Este notebook demonstra o processo de experimentação e a integração das APIs:

* [projetoBotManut.ipynb](projetoBotManut.ipynb)

---

## 📂 Estrutura de Pastas

A organização do projeto segue uma estrutura clara para facilitar o desenvolvimento e a manutenção:

```
.
├── app.py                      # Código principal da aplicação Flask
├── app.yaml                    # Configurações de deploy para o Google Cloud App Engine
├── requirements.txt            # Lista de dependências Python do projeto
├── static/                     # Pasta para arquivos estáticos (CSS, JavaScript, imagens do frontend)
│   ├── css/
│   │   └── style.css           # Estilos CSS da aplicação
│   └── js/
│       └── script.js           # Lógica JavaScript do frontend
├── templates/                  # Pasta para os arquivos HTML (templates Jinja2 do Flask)
│   └── index.html              # Página principal da interface do chatbot
└── .gcloudignore               # Arquivo que lista itens a serem ignorados no deploy para o GCP
```

---


## ⚙️ Como Rodar Localmente (Para Desenvolvedores)

Se você deseja configurar o ambiente de desenvolvimento e testar o chatbot localmente, siga os passos abaixo:

1.  **Clone o Repositório:**
    ```bash
    git clone (https://github.com/yuri-weasley/projetoBotManut.git)
    cd projetoBotManut
    ```

2.  **Crie e Ative um Ambiente Virtual (Recomendado Python 3.12):**
    ```bash
    # Crie o ambiente virtual (substitua 'python3.12' pela versão instalada em seu sistema)
    python3.12 -m venv venv_chatbot

    # Ative o ambiente virtual
    # No Windows:
    .\venv_chatbot\Scripts\activate
    # No macOS/Linux:
    source venv_chatbot/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto (ou configure diretamente no seu shell) com suas chaves de API do Google Cloud:

    ```
    # .env
    GOOGLE_API_KEY="SUA_CHAVE_DA_GEMINI_API"
    GOOGLE_CLOUD_PROJECT_ID="SEU_ID_DO_PROJETO_GCP"
    ```
    *Para carregar variáveis de um arquivo `.env`, você pode precisar instalar a biblioteca `python-dotenv`: `pip install python-dotenv` e adicionar `from dotenv import load_dotenv; load_dotenv()` no início do seu `app.py`.*

5.  **Execute a Aplicação Flask:**
    ```bash
    python app.py
    ```
    O chatbot estará disponível em `http://127.0.0.1:8080` (ou na porta que o Flask indicar).

---

## ☁️ Deploy no Google Cloud App Engine

Este projeto é configurado para deploy contínuo no Google Cloud App Engine (Standard Environment).

1.  **Configure as Variáveis de Ambiente no `app.yaml`:**
    Certifique-se de que o seu arquivo `app.yaml` na raiz do projeto contém suas chaves de API e ID do projeto na seção `env_variables`:

    ```yaml
    # app.yaml (trecho relevante)
    env_variables:
      GOOGLE_API_KEY: "SUA_CHAVE_DA_GEMINI_API"
      GOOGLE_CLOUD_PROJECT_ID: "SEU_ID_DO_PROJETO_GCP"
    ```

2.  **Realize o Deploy:**
    Certifique-se de ter a `gcloud CLI` configurada e autenticada. No diretório raiz do projeto, execute:

    ```bash
    gcloud app deploy
    ```
    Para forçar um novo build e evitar cache:
    ```bash
    gcloud app deploy --no-cache --version nova-versao
    ```

---

## 🐛 Desafios Enfrentados e Soluções

Durante o desenvolvimento e deploy deste chatbot, alguns desafios foram encontrados, e suas soluções são documentadas aqui para referência futura:

1.  **"Service Unavailable" no Deploy Inicial:**
    * **Problema:** O App Engine retornava "Service Unavailable" e falhava na "readiness check" durante o deploy, sem logs claros da aplicação Python.
    * **Solução:** Foi identificado que a versão do Python no ambiente local (Python 3.13) era incompatível com a especificada inicialmente no `app.yaml` (`python39`). A solução envolveu:
        * Alterar o `runtime` no `app.yaml` para `python312` (a versão mais recente suportada pelo App Engine Standard compatível).
        * Recriar o ambiente virtual local com Python 3.12 e gerar um novo `requirements.txt` a partir dele, garantindo a compatibilidade das dependências.

2.  **`ModuleNotFoundError: No module named 'main'`:**
    * **Problema:** O servidor Gunicorn não conseguia encontrar o módulo principal da aplicação Flask.
    * **Solução:** A entrada `entrypoint` no `app.yaml` foi configurada explicitamente para `gunicorn --worker-class gthread --workers=1 --threads=8 app:app`, instruindo o Gunicorn a carregar a instância `app` do arquivo `app.py`.

3.  **Variáveis de Ambiente não Carregadas:**
    * **Problema:** As chaves de API e o ID do projeto não estavam disponíveis para a aplicação no ambiente do App Engine, causando falhas na inicialização das APIs.
    * **Solução:** As variáveis `GOOGLE_API_KEY` e `GOOGLE_CLOUD_PROJECT_ID` foram adicionadas à seção `env_variables` no `app.yaml`, garantindo que fossem injetadas no ambiente da aplicação.

4.  **"API key not valid" durante o Processamento de Imagens:**
    * **Problema:** Após o deploy bem-sucedido e a aplicação no ar, o chatbot falhava ao processar imagens com a mensagem "API key not valid".
    * **Solução:** A chave da Gemini API configurada no `app.yaml` havia sido copiada incorretamente ou estava inválida. A solução foi gerar uma nova chave de API no Google AI Studio (ou verificar a existente) e garantir que ela fosse colada corretamente no `app.yaml` (entre aspas duplas e sem restrições de IP).

---

## 🤝 Contribuição

Contribuições são bem-vindas! Se você tiver sugestões, melhorias ou encontrar algum bug, sinta-se à vontade para:

1.  Abrir uma [Issue](https://github.com/yuri-weasley/projetoBotManut/issues) no GitHub.
2.  Criar um [Pull Request](https://github.com/yuri-weasley/projetoBotManut/pulls) com suas alterações.

---

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](https://opensource.org/licenses/MIT) - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## ✍️ Autoria

Este projeto foi concebido e desenvolvido por:

* **Weslley Yuri Ferreira dos Santos** - Estudante de Ciência da Computação 

---

## 🌟 Agradecimentos Especiais

* À comunidade Python: Pelo ecossistema robusto e flexível de bibliotecas e ferramentas.
* À comunidade de código aberto e aos desenvolvedores do [Flask](https://flask.palletsprojects.com/en/stable/), [Gunicorn](https://gunicorn.org/) e bibliotecas do [Google Cloud](https://cloud.google.com).
* Um agradecimento especial à comunidade do [Projeto Jupyter](https://jupyter.org/) e ao [Google Colab](https://colab.research.google.com/), cujas ferramentas foram essenciais para o desenvolvimento, prototipagem e experimentação inicial das funcionalidades de IA deste projeto. A facilidade de uso e o ambiente colaborativo do Colab aceleraram significativamente o progresso.
* À seção de Célula do 7°/8° GAv pelo valioso feedback durante a fase de testes.