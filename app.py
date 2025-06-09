import os
import sys
from flask import Flask, render_template, request, jsonify
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPIError

# Agrupando imports de bibliotecas externas e do Google Cloud
import google.generativeai as genai
from google.cloud import vision
from google.cloud import translate_v2 as translate # Usando o alias para V2

# Removendo import de traceback, pois a impressão de traceback completa não é ideal para produção
# e o App Engine já coleta logs de erro.
# import traceback # Pode ser removido

# Removendo logs de depuração de inicialização.
# print("DEBUG: app.py iniciado. Inicializando cliente Secret Manager...", file=sys.stderr)

# --- Configuração do Secret Manager ---
# O cliente deve ser inicializado uma única vez globalmente.
client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id, project_id):
    """Busca um segredo do Google Secret Manager."""
    secret_name = client.secret_version_path(project_id, secret_id, "latest")
    try:
        # Removendo logs de depuração detalhados.
        # print(f"DEBUG: Tentando acessar o segredo '{secret_id}' no projeto '{project_id}'...", file=sys.stderr)
        response = client.access_secret_version(request={"name": secret_name})
        # print(f"DEBUG: Segredo '{secret_id}' acessado com sucesso.", file=sys.stderr)
        return response.payload.data.decode("UTF-8")
    except GoogleAPIError as e:
        # Mantendo um log de erro claro em caso de falha da API.
        print(f"ERRO: Falha da API do Secret Manager ao acessar o segredo '{secret_id}': {e}", file=sys.stderr)
        raise RuntimeError(f"Erro ao carregar o segredo: {secret_id}.")
    except Exception as e:
        # Mantendo um log de erro claro para exceções inesperadas.
        print(f"ERRO: Erro inesperado ao acessar o segredo '{secret_id}': {e}", file=sys.stderr)
        raise RuntimeError(f"Erro genérico ao carregar o segredo: {secret_id}.")

# Removendo logs de depuração de funções definidas.
# print("DEBUG: Funções de carregamento de segredos definidas.", file=sys.stderr)

# --- Obter o ID do Projeto da Aplicação ---
# Priorize GCP_PROJECT, que é o mais confiável no App Engine Standard.
app_project_id = os.getenv('GCP_PROJECT')

if not app_project_id:
    app_project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not app_project_id:
        # Saída fatal se o ID do projeto não puder ser determinado.
        print("ERRO FATAL: O ID do projeto não foi encontrado nas variáveis de ambiente (GCP_PROJECT ou GOOGLE_CLOUD_PROJECT).", file=sys.stderr)
        sys.exit(1)

# Removendo log de depuração do ID do projeto.
# print(f"DEBUG: ID do Projeto da Aplicação detectado: {app_project_id}", file=sys.stderr)

# --- Carregar Chave API Gemini ---
# Removendo log de depuração.
# print("DEBUG: Tentando carregar GOOGLE_API_KEY do Secret Manager...", file=sys.stderr)
try:
    gemini_api_key = get_secret("google-api-key-gemini", app_project_id)
    # Removendo log de depuração.
    # print("DEBUG: GOOGLE_API_KEY carregada com sucesso.", file=sys.stderr)
except RuntimeError as e:
    print(f"ERRO FATAL: Falha ao carregar GOOGLE_API_KEY: {e}", file=sys.stderr)
    sys.exit(1)

# --- Inicialização das APIs ---
# Os clientes de API e modelos devem ser inicializados uma única vez globalmente
# para evitar recriação em cada requisição, o que é ineficiente.

# Removendo log de depuração.
# print("DEBUG: Configurando API Gemini...", file=sys.stderr)
try:
    genai.configure(api_key=gemini_api_key)
    # ATENÇÃO: Havia uma inconsistência aqui.
    # A linha abaixo 'model = genai.GenerativeModel('gemini-pro-vision')'
    # estava inicializando um modelo de visão globalmente,
    # enquanto 'simplify_text_with_gemini' criava seu próprio 'gemini-1.5-flash'.
    # Para consistência e eficiência, inicialize o modelo de texto AQUI,
    # e use-o em simplify_text_with_gemini.
    # Se você também precisar de um modelo de visão em outro lugar, inicialize-o separadamente.
    
    # Modelo para simplificação de texto.
    # Use o mesmo modelo que você confirmou que funciona localmente ('gemini-1.5-flash').
    global_text_model = genai.GenerativeModel('gemini-1.5-flash') 
    
    # Removendo log de depuração.
    # print("DEBUG: API Gemini configurada e modelo inicializado.", file=sys.stderr)
except Exception as e:
    print(f"ERRO FATAL: Falha ao configurar API Gemini ou inicializar modelo: {e}", file=sys.stderr)
    sys.exit(1)

# Removendo log de depuração.
# print("DEBUG: Inicializando clientes Vision e Translate...", file=sys.stderr)
try:
    vision_client = vision.ImageAnnotatorClient()
    translate_client = translate.Client() # Corrigido e padronizado para Translation API V2
    # Removendo log de depuração.
    # print("DEBUG: Clientes Vision e Translate inicializados.", file=sys.stderr)
except Exception as e:
    print(f"ERRO FATAL: Falha ao inicializar clientes Vision ou Translate: {e}", file=sys.stderr)
    sys.exit(1)

# Removendo log de depuração final da inicialização.
# print("DEBUG: Todas as APIs e segredos inicializados. Criando instância Flask...", file=sys.stderr)

# --- Instância da Aplicação Flask (DEVE SER APENAS UMA VEZ) ---
app = Flask(__name__)

# --- Funções de Processamento de Imagem/Texto ---
# Agora, essas funções podem usar as instâncias globais dos clientes de API.

def detect_text_from_image(image_content):
    """Detecta texto em uma imagem usando Google Cloud Vision API."""
    image = vision.Image(content=image_content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description # Retorna o texto completo
    return None

def detect_and_translate_language(text_content):
    """
    Detecta o idioma de um texto e o traduz para português, se necessário.
    Utiliza a Translation API V2.
    """
    if not text_content: # Adição: Verificação para texto vazio
        return ""

    result = translate_client.detect_language(text_content)
    detected_lang = result['language']

    translated_text = text_content
    if detected_lang and detected_lang != 'pt':
        # Removendo log de depuração detalhado.
        # print(f"Idioma detectado: {detected_lang}. Traduzindo para português.", file=sys.stderr)
        translation = translate_client.translate(
            text_content,
            target_language='pt',
            source_language=detected_lang
        )
        translated_text = translation['translatedText']
    else:
        # Removendo log de depuração detalhado.
        # print(f"Idioma já é português ou não detectado: {detected_lang}. Nenhuma tradução necessária.", file=sys.stderr)
        pass # 'pass' é opcional aqui, mas bom para indicar que a condição foi tratada.

    return translated_text

def simplify_text_with_gemini(original_text):
    """
    Simplifica e resume um texto usando a Gemini API.
    Utiliza o modelo de texto global 'global_text_model'.
    """
    if not original_text: # Adição: Verificação para texto vazio
        return "O texto fornecido para simplificação está vazio."

    try:
        # Usando a instância de modelo inicializada globalmente.
        # Removendo a linha 'text_model = genai.GenerativeModel('gemini-1.5-flash')' daqui.
        
        prompt = f"""
        Você é um assistente especializado em manutenção de aeronaves, com a tarefa de simplificar instruções técnicas. Recebi a seguinte instrução de manutenção de um manual:

        "{original_text}"

        Por favor, reescreva esta instrução de forma mais simples, clara e sucinta,
        mantendo apenas as informações essenciais para um técnico realizar a tarefa.
        Use linguagem direta e evite jargões desnecessários, se possível.
        """
        response = global_text_model.generate_content(prompt) # Usando a instância global

        # Removendo TODOS os logs de depuração internos da função.
        # print(f"DEBUG: Resposta completa da Gemini API (objeto): {response}", file=sys.stderr)
        # if hasattr(response, 'text') and response.text:
        #     print(f"DEBUG: Resposta da Gemini API (texto direto): {response.text[:200]}...", file=sys.stderr)
        # else:
        #     print(f"DEBUG: Resposta da Gemini API não tem atributo 'text' ou está vazia.", file=sys.stderr)
        # if response and hasattr(response, 'candidates') and response.candidates:
        #     print(f"DEBUG: Candidates presentes na resposta. Total: {len(response.candidates)}", file=sys.stderr)
        #     if response.candidates[0].content.parts:
        #         print(f"DEBUG: Conteúdo do candidato presente. Tipo: {type(response.candidates[0].content.parts[0])}", file=sys.stderr)
        #     else:
        #         print(f"DEBUG: Conteúdo do candidato vazio ou sem partes.", file=sys.stderr)
        # else:
        #     print(f"DEBUG: Resposta da Gemini API sem candidates ou vazia.", file=sys.stderr)

        if response and response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            # Mantendo um aviso no log caso a Gemini API não retorne conteúdo.
            print("AVISO: Gemini API retornou resposta vazia ou sem conteúdo gerado na parte esperada.", file=sys.stderr)
            return "A Gemini API não conseguiu gerar uma explicação simplificada para o texto fornecido. O texto é legível e relevante?"
    except Exception as e:
        # Mantendo um log de erro claro.
        print(f"ERRO: Exceção capturada na Gemini API. Tipo: {type(e).__name__}. Mensagem: {str(e)}", file=sys.stderr)
        # Removendo a impressão de traceback completa, pois o App Engine já registra erros e tracebacks.
        # print("ERRO: Traceback completa para o erro da Gemini API:", file=sys.stderr)
        # traceback.print_exc(file=sys.stderr)
        return "Ocorreu um erro ao simplificar a instrução. Por favor, tente novamente."
    
# --- Rotas da Aplicação Flask ---

@app.route('/')
def index():
    """Rota para a página inicial da aplicação."""
    return render_template('index.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    """Processa a imagem enviada, extrai, traduz e simplifica o texto."""
    if 'image' not in request.files:
        return jsonify({'error': 'Nenhuma imagem fornecida'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        image_content = image_file.read()

        # 1. Detectar texto na imagem (OCR)
        original_text_from_ocr = detect_text_from_image(image_content)
        if not original_text_from_ocr:
            return jsonify({'error': 'Não foi possível detectar texto na imagem. Certifique-se de que o texto está legível.'}), 400

        # Removendo logs de depuração detalhados.
        # print(f"DEBUG: Texto detectado (OCR): \n{original_text_from_ocr[:100]}...", file=sys.stderr)

        # 2. Detectar e traduzir idioma
        processed_text = detect_and_translate_language(original_text_from_ocr)
        # Removendo logs de depuração detalhados.
        # print(f"DEBUG: Texto processado (após tradução): \n{processed_text[:100]}...", file=sys.stderr)

        # 3. Simplificar o texto com a Gemini API
        simplified_explanation = simplify_text_with_gemini(processed_text)
        # Removendo logs de depuração detalhados.
        # print(f"DEBUG: Explicação simplificada (Gemini): \n{simplified_explanation[:100]}...", file=sys.stderr)

        return jsonify({
            'original_text': original_text_from_ocr,
            'simplified_text': simplified_explanation
        })

    except Exception as e:
        print(f"ERRO: Erro durante o processamento da imagem na rota /process_image: {e}", file=sys.stderr)
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

# --- Bloco de Execução Local ---
# Este bloco é SOMENTE para rodar com `python app.py` fora do App Engine.
# Em App Engine, Gunicorn executa o app.
if __name__ == '__main__':
    # Removendo log de depuração.
    # print("DEBUG: Rodando em ambiente local (fora do App Engine).", file=sys.stderr)
    # As variáveis de ambiente GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT, GOOGLE_API_KEY
    # precisam estar configuradas para o teste local.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))