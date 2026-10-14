import streamlit as st
import math
import json
import os
import streamlit.components.v1 as components
from itertools import combinations_with_replacement

# ==========================================
# CONFIGURAÇÕES INICIAIS E PERSISTÊNCIA
# ==========================================

ARQUIVO_MONTAGENS = "montagens_pequenas.json"

st.set_page_config(page_title="EasyMontage", page_icon="⚙️", layout="wide")

def carregar_montagens():
    if os.path.exists(ARQUIVO_MONTAGENS):
        with open(ARQUIVO_MONTAGENS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_montagem(nome, pecas_verm, pecas_azul, tamanho_total):
    montagens = carregar_montagens()
    novo_id = max([m.get("id", 0) for m in montagens], default=0) + 1
    nova_montagem = {
        "id": novo_id,
        "nome": nome,
        "pecas_vermelho": pecas_verm,
        "pecas_azul": pecas_azul,
        "tamanho": tamanho_total
    }
    montagens.append(nova_montagem)
    with open(ARQUIVO_MONTAGENS, "w", encoding="utf-8") as f:
        json.dump(montagens, f, ensure_ascii=False, indent=4)

def excluir_montagem(montagem_id):
    montagens = carregar_montagens()
    montagens = [m for m in montagens if m["id"] != montagem_id]
    with open(ARQUIVO_MONTAGENS, "w", encoding="utf-8") as f:
        json.dump(montagens, f, ensure_ascii=False, indent=4)

def atualizar_nome_montagem(montagem_id, novo_nome):
    montagens = carregar_montagens()
    for m in montagens:
        if m["id"] == montagem_id:
            m["nome"] = novo_nome
    with open(ARQUIVO_MONTAGENS, "w", encoding="utf-8") as f:
        json.dump(montagens, f, ensure_ascii=False, indent=4)

# ==========================================
# CONTROLO DE ESTADO (SESSION_STATE)
# ==========================================

if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "formulario"
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "builder_vermelho" not in st.session_state:
    st.session_state.builder_vermelho = []
if "builder_azul" not in st.session_state:
    st.session_state.builder_azul = []
if "montagem_selecionada" not in st.session_state:
    st.session_state.montagem_selecionada = None
if "editando_id" not in st.session_state:
    st.session_state.editando_id = None

# ==========================================
# 1. MENU LATERAL E TEMA (DEFINIDOS ANTES DO CSS)
# ==========================================

st.sidebar.markdown("<div style='font-size: 64px; font-weight: bold;'>⚙️ EasyMontage</div>", unsafe_allow_html=True)
st.sidebar.divider()

st.sidebar.title("Opções")
tema_escuro = st.sidebar.toggle("🌓 Trocar Modo de Visualização", value=False)
st.sidebar.divider()

menu_selecionado = st.sidebar.radio(
    "Navegação:",
    ["Calculadora Principal", "Montagens Salvas", "Construtor de Montagem"]
)

# ==========================================
# 2. REGRAS DE NEGÓCIO E LÓGICA MATEMÁTICA
# ==========================================

def calcular_pecas_folga(folga_desejada):
    alvo = int(round(folga_desejada * 100))
    pecas_disponiveis = {10: 2.1, 20: 2.2, 30: 2.3, 50: 2.5, 6: 2.06, 8: 2.08}
    chaves = list(pecas_disponiveis.keys())

    for r in range(1, 5):
        for combo in combinations_with_replacement(chaves, r):
            if sum(combo) == alvo:
                return [pecas_disponiveis[k] for k in combo]
    
    raise ValueError(f"Não foi possível formar a folga exata de {folga_desejada}mm com as peças disponíveis.")

def preenchimento_guloso(espaco_restante, cor_corte):
    espaco_restante = round(espaco_restante, 2)
    pecas_normais = [80, 40, 20, 10, 6, 3, 2, 1]
    pecas_usadas = []
    
    for p in pecas_normais:
        while espaco_restante >= p:
            if p == 40:
                cor_str = "Vermelha" if cor_corte == "vermelho" else "Azul"
                pecas_usadas.append(f"1 Borracha Vulcanizada {cor_str} 20mm + 1 Peça normal de 20mm (Subst. 40mm)")
            else:
                pecas_usadas.append(f"{p}mm")
            espaco_restante = round(espaco_restante - p, 2)
            
    return pecas_usadas, espaco_restante

def calcular_corte_vermelho(tamanho_alvo):
    passos = {"etapa1": [], "etapa2": [], "etapa3_fill": [], "etapa3_end": []}
    
    if tamanho_alvo < 52.5:
        passos["etapa1"] = ["Borracha Vermelha 9mm", "1mm", "borracha de 20mm"]
        tamanho_usado = 30.0
    else:
        passos["etapa1"] = ["Borracha Vermelha 9mm", "10mm", "1mm", "20mm"]
        tamanho_usado = 40.0
        
    passos["etapa3_end"] = ["2.3mm", "Borracha Vermelha 9mm", "1mm"]
    tamanho_final = 12.3
    
    espaco_disponivel = tamanho_alvo - tamanho_usado - tamanho_final
    minimo_necessario = round(tamanho_usado + tamanho_final, 2)
    if espaco_disponivel < 0:
        raise ValueError(f"Tamanho de {tamanho_alvo}mm é inferior ao mínimo para o Corte Vermelho ({minimo_necessario}mm).")
        
    qtd_kits = int(espaco_disponivel // 60)
    if qtd_kits > 0:
        total_kits_mm = qtd_kits * 60
        passos["etapa2"].append(f"**{qtd_kits}x** Kit de Preenchimento (1 Borracha Vermelha 20mm + 1 Peça 40mm) — Total: **{total_kits_mm}mm**")
    tamanho_usado_total = tamanho_usado + (qtd_kits * 60)
    
    restante = round(tamanho_alvo - tamanho_usado_total - tamanho_final, 2)
    pecas_fill, sobra = preenchimento_guloso(restante, "vermelho")
    passos["etapa3_fill"] = pecas_fill
    
    return passos, sobra

def calcular_corte_azul(tamanho_alvo, folga_azul):
    passos = {"etapa1": [], "etapa2": [], "etapa3_fill": [], "etapa3_end": []}
    
    if tamanho_alvo < 52.5:
        passos["etapa1"] = ["Faca 9mm", "1mm", "borracha de 20mm"]
        tamanho_usado = 30.0
    else:
        passos["etapa1"] = ["Faca 9mm", "10mm", "1mm", "20mm"]
        tamanho_usado = 40.0
    
    pecas_folga = calcular_pecas_folga(folga_azul)
    tamanho_folga = sum(pecas_folga)
    
    passos["etapa3_end"] = [f"{p}mm" for p in pecas_folga] + ["1mm", "Faca 9mm"]
    tamanho_final = 10.0 + tamanho_folga
    
    espaco_disponivel = tamanho_alvo - tamanho_usado - tamanho_final
    minimo_necessario = round(tamanho_usado + tamanho_final, 2)
    if espaco_disponivel < 0:
        raise ValueError(f"Tamanho de {tamanho_alvo}mm é inferior ao mínimo para o Corte Azul ({minimo_necessario}mm).")
        
    qtd_kits = int(espaco_disponivel // 60)
    if qtd_kits > 0:
        total_kits_mm = qtd_kits * 60
        passos["etapa2"].append(f"**{qtd_kits}x** Kit de Preenchimento (1 Borracha Azul 20mm + 1 Peça 40mm) — Total: **{total_kits_mm}mm**")
    tamanho_usado_total = tamanho_usado + (qtd_kits * 60)
    
    restante = round(tamanho_alvo - tamanho_usado_total - tamanho_final, 2)
    pecas_fill, sobra = preenchimento_guloso(restante, "azul")
    passos["etapa3_fill"] = pecas_fill
    
    return passos, sobra

# ==========================================
# 3. DESIGN SYSTEM & CSS (CORRIGIDO PARA SELECTBOX E IMPRESSÃO)
# ==========================================

css_geral = f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {'#121212' if tema_escuro else '#F8FAFC'} !important;
        color: {'#F3F4F6' if tema_escuro else '#0F172A'} !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 18px !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {'#1A1A1A' if tema_escuro else '#FFFFFF'} !important;
        border-right: 1px solid {'#333333' if tema_escuro else '#E2E8F0'} !important;
        padding-top: 1rem;
    }}
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div, 
    [data-testid="stSidebar"] .stRadio label {{
        color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important;
        font-size: 18px !important;
    }}

    [data-testid="stSidebar"] [data-testid="stToggle"] {{
        display: flex !important;
        align-items: center !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stToggle"] p,
    [data-testid="stSidebar"] [data-testid="stToggle"] span {{
        color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        margin-bottom: 0 !important;
    }}

    p, span, label, .stMarkdown p, .stMarkdown span, .stMarkdown li {{
        color: {'#F3F4F6' if tema_escuro else '#0F172A'} !important;
        font-size: 18px !important;
    }}

    h2 {{ font-size: 28px !important; font-weight: bold !important; color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important; }}
    h3 {{ font-size: 26px !important; font-weight: bold !important; color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important; }}
    h4 {{ font-size: 20px !important; font-weight: bold !important; color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important; }}

    .titulo-vermelho {{
        color: {'#F87171' if tema_escuro else '#EF4444'} !important;
        font-size: 26px !important;
        font-weight: bold !important;
    }}

    .titulo-azul {{
        color: {'#60A5FA' if tema_escuro else '#3B82F6'} !important;
        font-size: 26px !important;
        font-weight: bold !important;
    }}

    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"] {{
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}

    .stTextInput input, .stNumberInput input {{
        background-color: {'#2A2A2A' if tema_escuro else '#FFFFFF'} !important;
        color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important;
        font-size: 18px !important;
        font-weight: 600 !important;
    }}

    button, .stButton > button, div[data-testid="stNumberInput"] button {{
        background-color: {'#1E293B' if tema_escuro else '#2563EB'} !important;
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
    }}

    button p, .stButton > button p, div[data-testid="stNumberInput"] button p {{
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }}

    button:hover, .stButton > button:hover {{
        background-color: {'#334155' if tema_escuro else '#1D4ED8'} !important;
        color: #FFFFFF !important;
    }}

    .box-vermelha {{
        background-color: {'#1E1E1E' if tema_escuro else '#FFFFFF'} !important;
        border: 1px solid {'#451A03' if tema_escuro else '#FECACA'} !important;
        border-left: 6px solid #EF4444 !important;
        padding: 18px !important; 
        border-radius: 10px !important; 
        margin-top: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        font-size: 18px !important;
    }}
    
    .box-azul {{
        background-color: {'#1E1E1E' if tema_escuro else '#FFFFFF'} !important;
        border: 1px solid {'#1E3A8A' if tema_escuro else '#BFDBFE'} !important;
        border-left: 6px solid #3B82F6 !important;
        padding: 18px !important; 
        border-radius: 10px !important; 
        margin-top: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        font-size: 18px !important;
    }}

    .caixa-titulo {{
        color: {'#FFFFFF' if tema_escuro else '#0F172A'} !important;
        font-size: 18px !important;
        font-weight: bold !important;
        opacity: 1 !important;
    }}

    .caixa-item {{
        color: {'#F3F4F6' if tema_escuro else '#1E293B'} !important;
        font-size: 18px !important;
        opacity: 1 !important;
    }}

    @media print {{
        header, footer, [data-testid="stSidebar"], .stToggle, button, 
        .stButton, [data-testid="stForm"], hr, .nao-imprimir {{ 
            display: none !important; 
        }}
        
        @page {{ 
            size: A4 portrait; 
            margin: 6mm !important; 
        }}
        
        *, html, body, [data-testid="stAppViewContainer"], .main, div, p, span, label, h1, h2, h3, h4, h5, h6, strong, em, li, .stMarkdown, .stText, [data-testid="stMarkdownContainer"] {{
            background-color: #FFFFFF !important; 
            color: #000000 !important;
            -webkit-print-color-adjust: unset !important;
            print-color-adjust: unset !important;
            opacity: 1 !important;
            visibility: visible !important;
            text-shadow: none !important;
            filter: none !important;
        }}
        
        html, body, [data-testid="stAppViewContainer"], .main {{
            font-size: 12pt !important;
            height: auto !important;
            overflow: visible !important;
            padding: 0 !important;
            margin: 0 !important;
        }}

        h2, h3, h4, .titulo-vermelho, .titulo-azul {{
            color: #000000 !important;
            opacity: 1 !important;
            visibility: visible !important;
            -webkit-print-color-adjust: unset !important;
            print-color-adjust: unset !important;
        }}

        h2 {{ font-size: 14pt !important; margin: 4px 0 !important; font-weight: bold !important; color: #000000 !important; }}
        h3, .titulo-vermelho, .titulo-azul {{ font-size: 13pt !important; margin: 4px 0 !important; font-weight: bold !important; color: #000000 !important; }}
        h4 {{ font-size: 12pt !important; margin: 2px 0 !important; font-weight: bold !important; color: #000000 !important; }}
        p, span, li, [data-testid="stMarkdownContainer"] p {{ font-size: 12pt !important; line-height: 1.25 !important; margin-bottom: 2px !important; color: #000000 !important; }}

        .box-vermelha, .box-azul {{
            background-color: #FFFFFF !important; 
            border: 1px solid #000000 !important;
            border-left: 5px solid #000000 !important; 
            box-shadow: none !important;
            padding: 6px 10px !important; 
            margin-top: 4px !important;
            margin-bottom: 4px !important;
            break-inside: avoid;
            page-break-inside: avoid;
        }}
        
        .box-vermelha *, .box-azul *, 
        .box-vermelha .caixa-titulo, .box-azul .caixa-titulo,
        .box-vermelha .caixa-item, .box-azul .caixa-item {{
            color: #000000 !important;
            font-weight: 600 !important;
            font-size: 11pt !important;
            opacity: 1 !important;
            visibility: visible !important;
            -webkit-print-color-adjust: unset !important;
            print-color-adjust: unset !important;
        }}
        
        div[data-testid="stHorizontalBlock"] {{ 
            display: flex !important; 
            width: 100% !important; 
            gap: 12px !important;
        }}
        
        div[data-testid="column"] {{ 
            width: 50% !important; 
            flex: 1 1 50% !important; 
        }}
    }}
    </style>
"""
st.markdown(css_geral, unsafe_allow_html=True)

def renderizar_caixa(titulo, itens, cor, destaque=False):
    if not itens: return
    classe = "box-vermelha" if cor == "vermelho" else "box-azul"
    
    html = f'<div class="{classe}"><strong class="caixa-titulo">{titulo}</strong><br>'
    for item in itens:
        clean = item.replace("**", "")
        strong_tag = f'<strong>{clean}</strong>' if destaque or '**' in item else clean
        html += f"<span class='caixa-item' style='margin-left: 6px;'>&bull; {strong_tag}</span><br>"
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

CATALOGO_PECAS = {
    "Peça 80mm": 80.0, "Peça 40mm": 40.0, "Peça 20mm": 20.0,
    "Peça 10mm": 10.0, "Peça 6mm": 6.0, "Peça 3mm": 3.0,
    "Peça 2mm": 2.0, "Peça 1mm": 1.0,
    "Peça 2.5mm": 2.5, "Peça 2.3mm": 2.3, "Peça 2.2mm": 2.2,
    "Peça 2.1mm": 2.1, "Peça 2.08mm": 2.08, "Peça 2.06mm": 2.06,
    "Borracha 20mm": 20.0, "Borracha 9mm": 9.0,
    "Faca 9mm": 9.0
}

# ==========================================
# 4. MÁQUINA DE ESTADOS E RENDERIZAÇÃO
# ==========================================

# ----------------- TELA 1: CALCULADORA -----------------
if menu_selecionado == "Calculadora Principal":
    
    if st.session_state.tela_atual == "formulario":
        st.markdown("<div style='font-size: 64px; font-weight: bold; text-align: center;'>⚙️ EasyMontage</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Sistema Avançado de Preenchimento de Peças</p>", unsafe_allow_html=True)
        
        col_espaco1, col_centro, col_espaco2 = st.columns([1, 2, 1])
        with col_centro:
            with st.form("main_form"):
                st.subheader("Parâmetros do Cálculo")
                
                tamanho_montagem = st.number_input("1. Tamanho da Montagem (mm):", min_value=0.0, step=1.0, format="%.2f")
                tamanho_entrada = st.number_input("2. Tamanho da Bobina Entrada (mm) (Opcional - Para Cálculo de Cortes):", min_value=0.0, step=1.0, format="%.2f")
                
                qtd_cortes_calc = 1
                if tamanho_entrada > 0 and tamanho_montagem > 0:
                    qtd_cortes_calc = max(1, math.floor(tamanho_entrada / tamanho_montagem))
                    st.info(f"💡 **Quantidade de Cortes calculada:** {qtd_cortes_calc} corte(s) inteiros cabem na entrada.")
                
                espessura_material = st.number_input("3. Espessura do Material (mm):", min_value=0.0, value=1.00, step=0.01, format="%.2f")
                folga_azul = st.number_input("4. Folga Corte Azul (mm):", min_value=0.0, value=0.28, step=0.01)
                
                btn_calcular = st.form_submit_button("⚙️ CALCULAR", use_container_width=True)
                
                if btn_calcular:
                    if tamanho_montagem <= 0:
                        st.error("O tamanho da montagem deve ser maior que zero!")
                    else:
                        st.session_state.form_data = {
                            "tamanho": tamanho_montagem,
                            "entrada": tamanho_entrada,
                            "qtd_cortes": qtd_cortes_calc,
                            "espessura": espessura_material,
                            "folga_azul": folga_azul
                        }
                        st.session_state.tela_atual = "resultado"
                        st.rerun()

    elif st.session_state.tela_atual == "resultado":
        dados = st.session_state.form_data
        
        c_res_titulo, c_res_botoes = st.columns([3, 1])
        with c_res_titulo:
            st.markdown("<h2>Relatório de Montagem Calculada</h2>", unsafe_allow_html=True)
            espessura_fmt = f"{dados['espessura']:.2f}"
            st.write(f"**Tamanho Alvo:** {dados['tamanho']}mm | **Folga Azul:** {dados['folga_azul']}mm | **Material:** {espessura_fmt}mm")
            if dados['entrada'] > 0:
                st.write(f"**Entrada Informada:** {dados['entrada']}mm ➔ Rendimento: **{dados['qtd_cortes']} Corte(s)**")
            else:
                st.write(f"**Rendimento Padrão:** {dados['qtd_cortes']} Corte(s)")
                
        with c_res_botoes:
            st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Novo Cálculo", use_container_width=True):
                st.session_state.tela_atual = "formulario"
                st.rerun()
            if st.button("🖨️ Imprimir", use_container_width=True):
                components.html("<script>window.parent.print();</script>", height=0, width=0)
        
        st.divider()

        if dados['espessura'] > 0.80:
            st.error(f"ESPESSURA:({espessura_fmt}mm) Material grosso inspecionar folga")
        else:
            st.info(f"ESPESSURA:({espessura_fmt}mm) Material fino inspecionar folga")

        try:
            res_vermelho, sobra_verm = calcular_corte_vermelho(dados['tamanho'])
            res_azul, sobra_azul = calcular_corte_azul(dados['tamanho'], dados['folga_azul'])
            
            col_verm, col_azul = st.columns(2)
            with col_verm:
                st.markdown("<div class='titulo-vermelho'>🔴 CORTE VERMELHO</div>", unsafe_allow_html=True)
                renderizar_caixa("Jogo Inicial", res_vermelho['etapa1'], "vermelho")
                renderizar_caixa("Kits de Preenchimento", res_vermelho['etapa2'], "vermelho")
                renderizar_caixa("Peças menores", res_vermelho['etapa3_fill'], "vermelho")
                renderizar_caixa("Finalização", res_vermelho['etapa3_end'], "vermelho", destaque=True)
                if sobra_verm > 0:
                    st.warning(f"Sobra isolada de {sobra_verm}mm ")

            with col_azul:
                st.markdown("<div class='titulo-azul'>🔵 CORTE AZUL</div>", unsafe_allow_html=True)
                renderizar_caixa("Jogo Inicial", res_azul['etapa1'], "azul")
                renderizar_caixa("Kits de Preenchimento", res_azul['etapa2'], "azul")
                renderizar_caixa("Peças menores", res_azul['etapa3_fill'], "azul")
                renderizar_caixa("Finalização", res_azul['etapa3_end'], "azul", destaque=True)
                if sobra_azul > 0:
                    st.warning(f"Sobra isolada de {sobra_azul}mm")

        except Exception as e:
            st.error(f"**Falha no Processamento Matemático:** {str(e)}")

# ----------------- TELA 2: VISUALIZAR SALVAS (COM CRUD) -----------------
elif menu_selecionado == "Montagens Salvas":
    st.markdown("<h3 style='text-align: center;'>📦 Banco de Montagens Pequenas</h3>", unsafe_allow_html=True)
    
    if st.session_state.montagem_selecionada is None:
        montagens = carregar_montagens()
        if not montagens:
            st.warning("Nenhuma montagem pequena cadastrada ainda")
        else:
            cols = st.columns(4)
            for idx, m in enumerate(montagens):
                with cols[idx % 4]:
                    st.markdown(f"**{m['nome']}**")
                    st.markdown(f"📏 {m['tamanho']}mm")
                    if st.button("🔍 Visualizar", key=f"card_{m['id']}", use_container_width=True):
                        st.session_state.montagem_selecionada = m
                        st.rerun()
                    if st.button("🗑️ Excluir", key=f"del_{m['id']}", use_container_width=True):
                        excluir_montagem(m['id'])
                        st.success(f"Montagem '{m['nome']}' excluída com sucesso!")
                        st.rerun()
                    st.divider()
    else:
        m = st.session_state.montagem_selecionada
        
        if st.session_state.editando_id == m['id']:
            novo_nome_input = st.text_input("Novo Nome da Montagem:", value=m['nome'])
            c_ed1, c_ed2 = st.columns(2)
            with c_ed1:
                if st.button("💾 Salvar Montagem"):
                    atualizar_nome_montagem(m['id'], novo_nome_input)
                    m['nome'] = novo_nome_input
                    st.session_state.editando_id = None
                    st.success("Nome atualizado com sucesso!")
                    st.rerun()
            with c_ed2:
                if st.button("Cancelar ❌"):
                    st.session_state.editando_id = None
                    st.rerun()
        else:
            c_t1, c_t2 = st.columns([4, 1])
            c_t1.markdown(f"<h2>Visualização: [{m['nome']}]</h2>", unsafe_allow_html=True)
            if c_t2.button("Editar Nome ✏️"):
                st.session_state.editando_id = m['id']
                st.rerun()

        st.markdown(f"**Tamanho Fixo / Referência:** {m['tamanho']}mm")
        
        c_btn1, c_btn2, c_btn3, c_btn_empty = st.columns([1, 1, 1, 2])
        with c_btn1:
            if st.button("Voltar à Lista ⬅️ ", use_container_width=True):
                st.session_state.montagem_selecionada = None
                st.session_state.editando_id = None
                st.rerun()
        with c_btn2:
            if st.button("Excluir esta 🗑️", use_container_width=True):
                excluir_montagem(m['id'])
                st.session_state.montagem_selecionada = None
                st.success("Montagem excluída!")
                st.rerun()
        with c_btn3:
            if st.button("Imprimir Montagem 🖨️ ", use_container_width=True):
                components.html("<script>window.parent.print();</script>", height=0, width=0)
        
        st.divider()
        
        col_v, col_a = st.columns(2)
        with col_v:
            st.markdown("<div class='titulo-vermelho'>🔴 Corte Vermelho</div>", unsafe_allow_html=True)
            html_verm = f'<div class="box-vermelha"><ul>'
            for peca in m.get('pecas_vermelho', []):
                html_verm += f"<li style='margin-bottom: 4px;'>{peca}</li>"
            html_verm += "</ul></div>"
            st.markdown(html_verm, unsafe_allow_html=True)
            
        with col_a:
            st.markdown("<div class='titulo-azul'>🔵 Corte Azul</div>", unsafe_allow_html=True)
            html_azul = f'<div class="box-azul"><ul>'
            for peca in m.get('pecas_azul', []):
                html_azul += f"<li style='margin-bottom: 4px;'>{peca}</li>"
            html_azul += "</ul></div>"
            st.markdown(html_azul, unsafe_allow_html=True)

# ----------------- TELA 3: CONSTRUTOR DE MONTAGEM -----------------
elif menu_selecionado == "Construtor de Montagem":
    st.markdown("<h3 style='text-align: center;'>🛠️ Adicione uma Nova Montagem</h3>", unsafe_allow_html=True)
    st.info("Adicione peças para **ambos** os cortes (Vermelho e Azul) para habilitar o salvamento da montagem.")
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("<div class='titulo-vermelho'>🔴 Corte Vermelho</div>", unsafe_allow_html=True)
        peca_sel_v = st.selectbox("Catálogo Peças:", list(CATALOGO_PECAS.keys()), key="sel_verm")
        if st.button("➕ Adicionar ao Vermelho"):
            st.session_state.builder_vermelho.append({"nome": peca_sel_v, "tamanho": CATALOGO_PECAS[peca_sel_v]})
            st.rerun()
            
        soma_v = sum(p["tamanho"] for p in st.session_state.builder_vermelho)
        st.write(f"Subtotal Vermelho: **{soma_v:.2f}mm**")
        
        for i, p in enumerate(st.session_state.builder_vermelho):
            col_item, col_del = st.columns([4, 1])
            col_item.write(f"- {p['nome']}")
            if col_del.button("❌", key=f"del_v_{i}"):
                st.session_state.builder_vermelho.pop(i)
                st.rerun()
                break

    with col_b2:
        st.markdown("<div class='titulo-azul'>🔵 Corte Azul</div>", unsafe_allow_html=True)
        peca_sel_a = st.selectbox("Catálogo Peças:", list(CATALOGO_PECAS.keys()), key="sel_azul")
        if st.button("➕ Adicionar ao Azul"):
            st.session_state.builder_azul.append({"nome": peca_sel_a, "tamanho": CATALOGO_PECAS[peca_sel_a]})
            st.rerun()
            
        soma_a = sum(p["tamanho"] for p in st.session_state.builder_azul)
        st.write(f"Subtotal Azul: **{soma_a:.2f}mm**")
        
        for i, p in enumerate(st.session_state.builder_azul):
            col_item, col_del = st.columns([4, 1])
            col_item.write(f"- {p['nome']}")
            if col_del.button("❌", key=f"del_a_{i}"):
                st.session_state.builder_azul.pop(i)
                st.rerun()
                break

    st.divider()

    tem_vermelho = len(st.session_state.builder_vermelho) > 0
    tem_azul = len(st.session_state.builder_azul) > 0

    if tem_vermelho and tem_azul:
        nome_nova = st.text_input("Nome da Montagem (ex: '47.3mm'):")
        tamanho_total_estimado = max(soma_v, soma_a)
        
        if st.button("💾 Salvar Montagem Completa", type="primary", use_container_width=True):
            if nome_nova.strip() == "":
                st.error("Informe um nome para salvar.")
            else:
                salvar_montagem(
                    nome_nova, 
                    [p["nome"] for p in st.session_state.builder_vermelho], 
                    [p["nome"] for p in st.session_state.builder_azul], 
                    tamanho_total_estimado
                )
                st.session_state.builder_vermelho = []
                st.session_state.builder_azul = []
                st.success("Montagem salva com sucesso! Acesse 'Montagens Salvas' para conferir.")
    else:
        st.warning("⚠️ Adicione pelo menos uma peça no **Corte Vermelho** e uma peça no **Corte Azul** para liberar o botão de salvamento.")

# Rodapé Global
st.markdown("<br><hr><div class='nao-imprimir' style='text-align: center; color: #7F8C8D; font-size: 12px;'>Desenvolvido por Lucas Viana</div>", unsafe_allow_html=True)
