import os
import sys
import streamlit as st # Importa a biblioteca Streamlit

# from google.cloud import secretmanager
# from google.api_core.exceptions import GoogleAPIError

import google.generativeai as genai
from google.cloud import vision
from google.cloud import translate_v2 as translate

# --- Funções de Configuração e Inicialização de APIs (Mantidas) ---

# --- Não precisamos mais da função get_secret ou do client do Secret Manager ---
# client = secretmanager.SecretManagerServiceClient()
# def get_secret(secret_id, project_id):
#     # ... código removido ...

# --- Obter o ID do Projeto da Aplicação (ainda necessário para algumas APIs) ---
# Primeiro, tenta pegar da variável de ambiente que o Streamlit Cloud vai passar

# Obter o ID do Projeto da Aplicação
app_project_id = os.getenv('GCP_PROJECT')

if not app_project_id:
    app_project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not app_project_id:
        st.error("ERRO FATAL: O ID do projeto não foi encontrado nas variáveis de ambiente (GCP_PROJECT ou GOOGLE_CLOUD_PROJECT).")
        st.stop()

# Inicialização das APIs (usando st.cache_resource para otimizar)
# st.cache_resource armazena em cache o resultado da função,
# garantindo que ela seja executada apenas uma vez.
@st.cache_resource
def initialize_api_clients(api_key):
    """Inicializa os clientes das APIs Google Cloud."""
    try:
        genai.configure(api_key=api_key)
        # Modelo para simplificação de texto
        global_text_model = genai.GenerativeModel('gemini-1.5-flash')
        
        vision_client = vision.ImageAnnotatorClient()
        translate_client = translate.Client()

        return global_text_model, vision_client, translate_client
    except Exception as e:
        st.error(f"ERRO FATAL: Falha ao inicializar clientes das APIs Google Cloud: {e}")
        st.stop()

# Chama a função de inicialização uma única vez
global_text_model, vision_client, translate_client = initialize_api_clients(gemini_api_key)


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