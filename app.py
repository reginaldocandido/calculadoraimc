import streamlit as st
import requests
import json
import os

# --- Configurações da API Gemini ---
# Para rodar no Streamlit Cloud, defina a chave como um "secret" com o nome GEMINI_API_KEY.
# Você pode obter sua chave aqui: https://aistudio.google.com/app/apikey
API_KEY = os.environ.get("GEMINI_API_KEY", "")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- Funções de Cálculo e Classificação ---

def classify_bmi(bmi):
    """Classifica o IMC de acordo com a tabela da OMS."""
    if bmi < 18.5:
        return "Magreza"
    elif 18.5 <= bmi < 24.9:
        return "Normal (Peso Saudável)"
    elif 25.0 <= bmi < 29.9:
        return "Sobrepeso"
    elif 30.0 <= bmi < 34.9:
        return "Obesidade Grau I"
    elif 35.0 <= bmi < 39.9:
        return "Obesidade Grau II (Severa)"
    else:
        return "Obesidade Grau III (Mórbida)"

def generate_tips(classification):
    """
    Chama a API do Gemini para gerar dicas saudáveis baseadas na classificação do IMC.
    A função utiliza o Google Search grounding para obter informações atualizadas.
    """
    if not API_KEY:
        return "Erro: A chave da API Gemini não foi configurada. Por favor, configure a variável de ambiente ou secret 'GEMINI_API_KEY'."

    st.info("🧠 Gerando dicas de bem-estar personalizadas com Gemini...")

    system_prompt = (
        "Aja como um nutricionista e coach de bem-estar. Forneça dicas saudáveis, "
        "práticas e motivadoras, baseadas em informações recentes, para a classificação "
        "de IMC fornecida. O texto deve ser conciso e amigável, em um único parágrafo."
    )

    user_query = (
        f"Gere dicas saudáveis e motivadoras para uma pessoa com a seguinte classificação "
        f"de IMC: '{classification}'. Foque em passos pequenos, alcançáveis e sustentáveis. "
        "Responda integralmente em português."
    )

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{ "google_search": {} }], # Habilita o Google Search Grounding
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Lança exceção para códigos de erro HTTP
        
        result = response.json()
        candidate = result.get('candidates', [{}])[0]
        
        # 1. Extrair o texto gerado
        text = candidate.get('content', {}).get('parts', [{}])[0].get('text', 'Não foi possível gerar as dicas.')

        # 2. Extrair fontes (grounding)
        sources = []
        grounding_metadata = candidate.get('groundingMetadata')
        if grounding_metadata and grounding_metadata.get('groundingAttributions'):
            sources = [
                f"[{attr.get('web', {}).get('title')}]({attr.get('web', {}).get('uri')})"
                for attr in grounding_metadata['groundingAttributions']
                if attr.get('web') and attr.get('web').get('uri')
            ]
        
        return text, sources

    except requests.exceptions.RequestException as e:
        return f"Erro de conexão com a API Gemini: {e}", []
    except Exception as e:
        return f"Ocorreu um erro ao processar a resposta da API: {e}", []

# --- Interface Streamlit ---

st.set_page_config(
    page_title="Calculadora de IMC & Dicas Gemini",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("Calculadora de IMC Personalizada")
st.markdown("Use esta ferramenta para calcular seu Índice de Massa Corporal e receber dicas saudáveis personalizadas, geradas pela Inteligência Artificial do Gemini.")

# --- Inputs do Usuário ---

col1, col2 = st.columns(2)

with col1:
    peso_kg = st.number_input(
        "Seu Peso (kg)", 
        min_value=1.0, 
        max_value=300.0, 
        value=70.0, 
        step=0.1, 
        format="%.1f"
    )

with col2:
    altura_m = st.number_input(
        "Sua Altura (m)", 
        min_value=0.50, 
        max_value=3.00, 
        value=1.75, 
        step=0.01, 
        format="%.2f"
    )

# --- Botão e Lógica de Processamento ---

if st.button("Calcular IMC e Obter Dicas", type="primary"):
    
    # 1. Cálculo e Classificação
    if altura_m > 0 and peso_kg > 0:
        try:
            imc = peso_kg / (altura_m ** 2)
            classification = classify_bmi(imc)
            
            st.markdown("---")
            
            # 2. Exibição do Resultado
            st.header("Seu Resultado de IMC")
            st.metric(label="Seu IMC", value=f"{imc:.2f}", delta=classification)

            st.subheader(f"Classificação: **{classification}**")
            
            # 3. Geração e Exibição das Dicas
            st.markdown("### Dicas Saudáveis do Gemini")
            tips_text, sources = generate_tips(classification)
            
            st.markdown(tips_text)
            
            # Exibir fontes, se houver
            if sources:
                st.markdown("---")
                st.subheader("Fontes de Informação (Google Search)")
                for source in sources:
                    st.markdown(f"* {source}")

        except OverflowError:
            st.error("Os valores inseridos são muito grandes para calcular o IMC. Por favor, verifique.")
        except Exception as e:
            st.error(f"Ocorreu um erro no cálculo: {e}")

    else:
        st.error("Por favor, insira valores válidos para peso e altura.")

st.markdown("---")
st.caption("Nota: O Índice de Massa Corporal (IMC) é apenas uma referência. Consulte sempre um profissional de saúde para uma avaliação completa.")
