import streamlit as st
import pandas as pd
import json
import os
import re

# --- Funções para Carregar e Salvar Dados ---

def load_data(file_path="treino_data.json"):
    """Carrega os dados de um arquivo JSON."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def save_data(data, file_path="treino_data.json"):
    """Salva os dados em um arquivo JSON."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# --- Carregar Dados da Planilha ---

# Nome do arquivo Excel
excel_file = "EXERCICIOS.xlsx"

try:
    # Tenta ler o arquivo Excel
    df_treinos = pd.read_excel(excel_file)
except FileNotFoundError:
    st.error(f"Erro: O arquivo '{excel_file}' não foi encontrado.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler o arquivo Excel: {e}")
    st.warning("Verifique se o arquivo está no formato .xlsx e se a biblioteca 'openpyxl' está instalada.")
    st.stop()

# Limpa os nomes das colunas, removendo espaços em branco
df_treinos.columns = df_treinos.columns.str.strip()

# Prepara a estrutura de dados de treinos
treinos = {}
for _, row in df_treinos.iterrows():
    dia = row['Dia da semana']
    
    exercicio_info = {
        "exercicio": row['EXERCICIO'],
        "preparatoria": row['PREPARATORIA'],
        "valida": row['VALIDA'],
        "estrategia": row['ESTRATEGIA'],
        "tipo_estrategia": row['TIPO ESTRATEGIA']
    }

    if dia not in treinos:
        treinos[dia] = {
            "titulo": f"Treino de {dia}",
            "exercicios": [],
            "cardio": row['CARDIO']
        }
    treinos[dia]["exercicios"].append(exercicio_info)

# --- Inicialização ---
treino_data = load_data()

# --- Interface do Streamlit ---

st.title("Aplicativo de Acompanhamento de Treino")

# Seleção do dia da semana
dias_da_semana = list(treinos.keys())
dia_semana_selecionado = st.selectbox("Escolha o dia da semana:", dias_da_semana)

# --- Exibir o Treino ---

if dia_semana_selecionado in treinos:
    treino = treinos[dia_semana_selecionado]
    
    st.header(treino["titulo"])
    
    # Exibir exercícios
    st.subheader("Exercícios")
    
    # Dicionário para armazenar os pesos da sessão atual
    pesos_sessao = {}
    
    for exercicio_info in treino["exercicios"]:
        
        exercicio_nome = exercicio_info['exercicio']
        
        st.markdown(f"**{exercicio_nome}**")
        
        # Cria um id único para o widget para evitar conflitos
        ex_key = f"{dia_semana_selecionado}_{exercicio_nome}"
        
        # Garante que os dados do exercício existem
        if ex_key not in treino_data:
            treino_data[ex_key] = {
                "preparatoria_peso": "",
                "valida_peso": "",
                "estrategia_peso": "",
                "historico": []
            }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**Preparatória:** {exercicio_info['preparatoria']}")
            peso_prep = st.text_input(f"Peso:", value=treino_data[ex_key]["preparatoria_peso"], key=f"{ex_key}_prep")
        with col2:
            st.markdown(f"**Valida:** {exercicio_info['valida']}")
            peso_val = st.text_input(f"Peso:", value=treino_data[ex_key]["valida_peso"], key=f"{ex_key}_val")
        with col3:
            st.markdown(f"**Estratégia:** {exercicio_info['estrategia']}")
            peso_estr = st.text_input(f"Peso:", value=treino_data[ex_key]["estrategia_peso"], key=f"{ex_key}_estr")
        with col4:
            st.markdown(f"**Tipo de Estratégia:**")
            st.markdown(f"> **{exercicio_info['tipo_estrategia']}**")
            
        pesos_sessao[ex_key] = {
            "preparatoria_peso": peso_prep,
            "valida_peso": peso_val,
            "estrategia_peso": peso_estr
        }
        
        # Atualiza o dicionário de dados do treino para a sessão atual
        treino_data[ex_key]["preparatoria_peso"] = peso_prep
        treino_data[ex_key]["valida_peso"] = peso_val
        treino_data[ex_key]["estrategia_peso"] = peso_estr

    # Espaço para cardio
    st.markdown("---")
    st.subheader("Cardio")
    st.write(f"**{treino['cardio']}**")

    # Espaço para calorias e tempo
    st.markdown("---")
    st.subheader("Anotações do Treino")
    
    calorias = st.text_input("Calorias gastas (kcal):", key="calorias_input")
    tempo = st.text_input("Tempo do treino (min):", key="tempo_input")
    
    # Botão para salvar dados e adicionar ao histórico
    if st.button("Salvar Treino"):
        for exercicio_info in treino["exercicios"]:
            exercicio_nome = exercicio_info['exercicio']
            ex_key = f"{dia_semana_selecionado}_{exercicio_nome}"
            
            peso_prep = pesos_sessao[ex_key]["preparatoria_peso"]
            peso_val = pesos_sessao[ex_key]["valida_peso"]
            peso_estr = pesos_sessao[ex_key]["estrategia_peso"]
            
            # Valida se os pesos são numéricos antes de salvar
            try:
                historico_item = {
                    "data": pd.Timestamp.now().strftime("%Y-%m-%d"),
                    "preparatoria_peso": float(peso_prep) if peso_prep else None,
                    "valida_peso": float(peso_val) if peso_val else None,
                    "estrategia_peso": float(peso_estr) if peso_estr else None
                }
                treino_data[ex_key]["historico"].append(historico_item)
            except ValueError:
                st.warning(f"Aviso: Os pesos para '{exercicio_nome}' não são números válidos. Dados não salvos para este exercício.")
                continue
        
        # Salva as anotações de calorias e tempo
        treino_data[f"{dia_semana_selecionado}_anotacoes"] = {
            "calorias": calorias,
            "tempo": tempo
        }
        
        save_data(treino_data)
        st.success("Treino salvo com sucesso!")

    # --- Gráfico de Histórico de Pesos ---
    st.markdown("---")
    st.subheader("Histórico de Cargas")
    
    for exercicio_info in treino["exercicios"]:
        exercicio_nome = exercicio_info['exercicio']
        ex_key = f"{dia_semana_selecionado}_{exercicio_nome}"
        if ex_key in treino_data and treino_data[ex_key]["historico"]:
            historico_df = pd.DataFrame(treino_data[ex_key]["historico"])
            historico_df["data"] = pd.to_datetime(historico_df["data"])
            
            # Converte as colunas de peso para numéricas, ignorando erros
            for col in ["preparatoria_peso", "valida_peso", "estrategia_peso"]:
                historico_df[col] = pd.to_numeric(historico_df[col], errors='coerce')
            
            st.markdown(f"#### {exercicio_nome}")
            
            # Cria o gráfico
            st.line_chart(historico_df.set_index("data"))