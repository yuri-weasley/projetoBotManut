import os
import sys
import json
import streamlit as st

import google.generativeai as genai
from google.cloud import vision
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

# --- Funções de Configuração e Inicialização de APIs ---

# --- 1. Carregar ID do Projeto e Chave API Gemini DOS SEGREDOS DO STREAMLIT ---
# DESCOMENTE E USE DIRETAMENTE OS SEUS SEGREDS PARA ESSAS VARIÁVEIS
app_project_id = st.secrets.get("GCP_PROJECT")
if not app_project_id:
    st.error("ERRO FATAL: O ID do projeto (GCP_PROJECT) não foi encontrado nos segredos do Streamlit. Por favor, configure-o no painel do Streamlit Cloud.")
    st.stop()

gemini_api_key = st.secrets.get("GOOGLE_API_KEY")
if not gemini_api_key:
    st.error("ERRO FATAL: A chave GOOGLE_API_KEY está vazia ou não foi carregada dos segredos do Streamlit. Por favor, verifique a configuração.")
    st.stop()

@st.cache_resource
def get_service_account_info():
    """
    Monta o dicionário de informações da conta de serviço a partir dos segredos do Streamlit.
    """
    service_account_info = {
        "type": st.secrets["GCP_TYPE"],
        "project_id": st.secrets["GCP_PROJECT_ID"],
        "private_key_id": st.secrets["GCP_PRIVATE_KEY_ID"],
        "private_key": st.secrets["GCP_PRIVATE_KEY"], # Já deve estar escapada corretamente
        "client_email": st.secrets["GCP_CLIENT_EMAIL"],
        "client_id": st.secrets["GCP_CLIENT_ID"],
        "auth_uri": st.secrets["GCP_AUTH_URI"],
        "token_uri": st.secrets["GCP_TOKEN_URI"],
        "auth_provider_x509_cert_url": st.secrets["GCP_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": st.secrets["GCP_CLIENT_X509_CERT_URL"],
        "universe_domain": st.secrets["GCP_UNIVERSE_DOMAIN"],
    }
    return service_account_info

# --- 2. Carregar Credenciais da Conta de Serviço ---
# REMOVA OU COMENTE ESTE BLOCO INTEIRO
# service_account_info = st.secrets.get("GCP_SERVICE_ACCOUNT_CREDENTIALS")
# if not service_account_info:
#     st.error("ERRO FATAL: As credenciais da conta de serviço (GCP_SERVICE_ACCOUNT_CREDENTIALS) não foram encontradas nos segredos do Streamlit. Por favor, configure-as.")
#     st.stop()

# try:
#     credentials_json = json.loads(service_account_info)
#     credentials = service_account.Credentials.from_service_account_info(credentials_json)
# except Exception as e:
#     st.error(f"ERRO FATAL: Falha ao carregar credenciais da conta de serviço. Verifique o formato JSON nos segredos do Streamlit: {e}")
#     st.stop()

# --- USE ESTAS DUAS LINHAS PARA OBTER AS CREDENCIAIS ---
credentials_dict = get_service_account_info()
credentials = service_account.Credentials.from_service_account_info(credentials_dict)
# ----------------------------------------------------

# --- 3. Inicialização das APIs (usando st.cache_resource para otimizar) ---
@st.cache_resource
def initialize_api_clients(gemini_key, gcp_credentials):
    """Inicializa os clientes das APIs Google Cloud."""
    try:
        genai.configure(api_key=gemini_key)
        global_text_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Inicializa Vision e Translate com as credenciais da conta de serviço
        vision_client = vision.ImageAnnotatorClient(credentials=gcp_credentials)
        translate_client = translate.Client(credentials=gcp_credentials)

        return global_text_model, vision_client, translate_client
    except Exception as e:
        st.error(f"ERRO FATAL: Falha ao inicializar clientes das APIs Google Cloud. Verifique suas credenciais e permissões de API no GCP. Detalhes: {e}")
        st.stop()

# --- 4. Chama a função de inicialização uma única vez ---
global_text_model, vision_client, translate_client = initialize_api_clients(gemini_api_key, credentials)

# --- Funções de Processamento de Imagem/Texto (Mantidas) ---

def detect_text_from_image(image_content):
    """Detecta texto em uma imagem usando Google Cloud Vision API."""
    image = vision.Image(content=image_content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return None

def detect_and_translate_language(text_content):
    """
    Detecta o idioma de um texto e o traduz para português, se necessário.
    Utiliza a Translation API V2.
    """
    if not text_content:
        return ""

    result = translate_client.detect_language(text_content)
    detected_lang = result['language']

    translated_text = text_content
    if detected_lang and detected_lang != 'pt':
        translation = translate_client.translate(
            text_content,
            target_language='pt',
            source_language=detected_lang
        )
        translated_text = translation['translatedText']
    
    return translated_text

def simplify_text_with_gemini(original_text):
    """
    Simplifica e resume um texto usando a Gemini API.
    Utiliza o modelo de texto global 'global_text_model'.
    """
    if not original_text:
        return "O texto fornecido para simplificação está vazio."

    try:
        prompt = f"""
        Você é um assistente especializado em manutenção de aeronaves, com a tarefa de simplificar instruções técnicas. Recebi a seguinte instrução de manutenção de um manual:

        "{original_text}"

        Por favor, reescreva esta instrução de forma mais simples, clara e sucinta,
        mantendo apenas as informações essenciais para um técnico realizar a tarefa.
        Use linguagem direta e evite jargões desnecessários, se possível.
        """
        response = global_text_model.generate_content(prompt)

        if response and response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            st.warning("A Gemini API retornou resposta vazia ou sem conteúdo gerado na parte esperada.")
            return "A Gemini API não conseguiu gerar uma explicação simplificada para o texto fornecido. O texto é legível e relevante?"
    except Exception as e:
        st.error(f"Ocorreu um erro ao simplificar a instrução: {str(e)}")
        return "Ocorreu um erro ao simplificar a instrução. Por favor, tente novamente."

# --- Interface do Streamlit (Substitui as Rotas Flask) ---

st.set_page_config(page_title="Bot de Manutenção de Aeronaves", layout="centered")

st.title("👨‍✈️ Bot de Manutenção de Aeronaves")
st.markdown("""
Esta ferramenta utiliza **Visão Computacional (OCR)**, **Tradução Automática** e **Inteligência Artificial Generativa (Gemini AI)** para simplificar instruções de manutenção de manuais de aeronaves a partir de imagens.
""")

uploaded_file = st.file_uploader("Envie uma imagem com a instrução de manutenção", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Exibe a imagem carregada
    st.image(uploaded_file, caption='Imagem Carregada.', use_column_width=True)
    st.write("")
    st.info("Processando a imagem... Por favor, aguarde.")

    # Lê o conteúdo da imagem
    image_content = uploaded_file.read()

    try:
        # 1. Detectar texto na imagem (OCR)
        with st.spinner('Detectando texto (OCR) na imagem...'):
            original_text_from_ocr = detect_text_from_image(image_content)
        
        if not original_text_from_ocr:
            st.warning("Não foi possível detectar texto na imagem. Certifique-se de que o texto está legível.")
            st.stop()

        st.subheader("Texto Detectado (OCR):")
        st.write(original_text_from_ocr)

        # 2. Detectar e traduzir idioma
        with st.spinner('Traduzindo texto, se necessário...'):
            processed_text = detect_and_translate_language(original_text_from_ocr)
        
        if original_text_from_ocr != processed_text:
            st.subheader("Texto Traduzido (para Português):")
            st.write(processed_text)
        else:
            st.info("O texto detectado já está em português ou não exigiu tradução.")

        # 3. Simplificar o texto com a Gemini API
        with st.spinner('Simplificando a instrução com Gemini AI...'):
            simplified_explanation = simplify_text_with_gemini(processed_text)
        
        st.subheader("Instrução Simplificada (Gemini AI):")
        st.success(simplified_explanation) # Exibe o resultado em destaque

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o processamento: {str(e)}")
        st.write("Verifique os logs para mais detalhes.")