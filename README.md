# ⚙️ EasyMontage

> **Sobre o Projeto:**  
> O **EasyMontage** nasceu da iniciativa de um profissional da produção que identificou gargalos e oportunidades de otimização no processo de montagem e corte de materiais. Utilizando a tecnologia como ferramenta de transformação, o sistema foi pensado, desenhado e desenvolvido do zero para adaptar e simplificar rotinas operacionais, trazendo mais precisão matemática, velocidade e eficiência para o chão de fábrica.

---

## 🌟 Origem e Autoria

**Idealização, Lógica de Negócio e Desenvolvimento:**  
Todo o conceito, algoritmos de cálculo, design de interface e implementação foram 100% idealizados e executados por **Lucas Viana**.

---

## 🔗 Acesso à Aplicação

O aplicativo está hospedado e disponível para uso público de forma online e gratuita:

👉 **[Acessar o EasyMontage](https://easymontage-app.streamlit.app/)**

---

## ✨ Funcionalidades Principais

- **🧮 Calculadora Principal de Cortes:**
  - Cálculo automático para **Corte Vermelho** e **Corte Azul**.
  - Inclusão inteligente de kits de preenchimento com soma total em milímetros.
  - Tratamento dinâmico para espessuras de materiais finos e grossos com alertas visuais.
  - Cálculo opcional de rendimento baseado no tamanho da bobina de entrada.
- **📦 Banco de Montagens Salvas (CRUD):**
  - Armazenamento e consulta rápida de montagens frequentes.
  - Funcionalidade para visualizar detalhadamente, editar nomes e excluir registros.
- **🛠️ Construtor de Montagens Personalizadas:**
  - Interface interativa para testar a combinação de peças a partir de um catálogo predefinido.
  - Validação em tempo real de subtotais para os cortes vermelho e azul.
- **🖨️ Layout Otimizado para Impressão:**
  - Padrão de impressão profissional em formato A4 (retrato), limpo, em preto e branco e livre de elementos desnecessários da interface.
- **🌓 Modo de Visualização (Dark/Light Mode):**
  - Alternância fluida entre o tema claro e escuro conforme a preferência do operador.

---

## 🚀 Tecnologias Utilizadas

- **Python** (Lógica de negócio e algoritmos de combinação matemática)
- **Streamlit** (Interface gráfica web interativa)
- **JSON** (Persistência de dados local das montagens)
- **HTML5 & CSS3** (Estilização personalizada e otimização para impressão)

---

## 📂 Estrutura do Projeto

```text
easymontage/
│
├── app.py                   # Código principal da aplicação (Streamlit)
├── requirements.txt         # Dependências do projeto
├── montagens_pequenas.json  # Banco de dados local para persistência das montagens
└── README.md                # Documentação do projeto

👨‍💻 Autor
Desenvolvido exclusivamente por Lucas Viana.