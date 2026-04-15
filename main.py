import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, shapiro, ttest_ind
from sklearn.preprocessing import MinMaxScaler

# Configurações de diretório
filesDir = "./src"
imgDir = f"{filesDir}/img"
excelDir = f"{filesDir}/csv"
p39Path = f"{excelDir}/p39.xlsx"

os.makedirs(imgDir, exist_ok=True)
for filename in os.listdir(imgDir):
    file_path = os.path.join(imgDir, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

def save_plot(name):
    path = f"{imgDir}/{name}.png"
    plt.savefig(path, bbox_inches='tight', dpi=120)
    print(f"[✔] Visualização '{name}' exportada com sucesso.")

# =========================
# PROCESSAMENTO DE DADOS
# =========================
df = pd.read_excel(p39Path, usecols="A:K")
df.rename(columns=str.lower, inplace=True)
df = df[df['id'].str.startswith('C')]

if __name__ == "__main__":
    # Métricas e Normalização
    df['consumo_relativo'] = df['fatura'] / df['renda']
    scaler = MinMaxScaler()
    df['consumo_norm'] = scaler.fit_transform(df[['consumo_relativo']])
    #df['renda_norm'] = scaler.fit_transform(1 / np.log(df['renda']))
    df['renda_norm'] = scaler.fit_transform(np.array(1 / np.log(df['renda'])).reshape(-1, 1))
    
    # Score de Risco (Ponderado: 80% Consumo, 20% Renda)
    df['score_risco'] = (df['consumo_norm'] * 0.8 + df['renda_norm'] * 0.2) * 100

    def classificar_risco(x):
        if x < 0.1: return 'baixo'
        elif x < 0.2: return 'moderado'
        elif x < 0.25: return 'alto'
        else: return 'critico'
    df['risco'] = df['consumo_relativo'].apply(classificar_risco)

    # =========================
    # 1. SCATTER PLOT (DISPERSÃO)
    # =========================
    plt.figure(figsize=(10, 6))
    cores = {'baixo': '#2ecc71', 'moderado': '#f1c40f', 'alto': '#e67e22', 'critico': '#e74c3c'}
    
    for risco, cor in cores.items():
        subset = df[df['risco'] == risco]
        plt.scatter(subset['renda'], subset['consumo_relativo'], label=risco.capitalize(), color=cor, alpha=0.7)

    plt.axhline(y=0.25, linestyle='--', color='red', alpha=0.5)
    plt.text(df['renda'].max()*0.8, 0.26, 'Limite de Alerta (25%)', color='red', fontsize=9)
    
    plt.title('Análise de Renda vs. Comprometimento da Fatura', fontsize=14, pad=15)
    plt.xlabel('Renda Mensal (R$)', fontsize=11)
    plt.ylabel('Consumo Relativo (Fatura / Renda)', fontsize=11)
    plt.legend(title='Nível de Risco')
    plt.grid(True, linestyle=':', alpha=0.6)
    
    save_plot("1_dispersao_renda_consumo")
    plt.close()

    # =========================
    # 2. HEATMAP (CORRELAÇÃO)
    # =========================
    df['propria_num'] = df['propria'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})
    df['superior_num'] = df['superior'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})
    
    colunas_corr = ['renda', 'fatura', 'idade', 'consumo_relativo', 'propria_num', 'superior_num']
    corr = df[colunas_corr].corr()

    plt.figure(figsize=(10, 8))
    im = plt.imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
    plt.colorbar(im, label='Força da Correlação')
    
    plt.xticks(range(len(corr.columns)), ['Renda', 'Fatura', 'Idade', 'Consumo Rel.', 'Casa Própria', 'Ensino Sup.'], rotation=45)
    plt.yticks(range(len(corr.columns)), ['Renda', 'Fatura', 'Idade', 'Consumo Rel.', 'Casa Própria', 'Ensino Sup.'])
    
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha='center', va='center', 
                     color='white' if abs(corr.iloc[i, j]) > 0.5 else 'black')

    plt.title('Mapa de Influência: Fatores de Correlação de Risco', fontsize=14, pad=20)
    save_plot("2_heatmap_correlacao")
    plt.close()

    # =========================
    # 3. BOXPLOT (DISTRIBUIÇÃO)
    # =========================
    plt.figure(figsize=(10, 6))
    df.boxplot(column='consumo_relativo', by='risco', grid=False, patch_artist=True)
    
    plt.title('Distribuição do Consumo Relativo por Faixa de Risco', fontsize=14)
    plt.suptitle('') # Remove o título automático do pandas
    plt.xlabel('Categorias de Risco Definidas', fontsize=11)
    plt.ylabel('Percentual de Renda Comprometida', fontsize=11)
    
    save_plot("3_boxplot_distribuicao")
    plt.close()

    # =========================
    # 4. HISTOGRAMA DO SCORE
    # =========================
    plt.figure(figsize=(10, 6))
    df['score_risco'].plot(kind='hist', bins=20, density=True, color='#34495e', alpha=0.7, edgecolor='white')
    df['score_risco'].plot(kind='kde', color='#e74c3c', linewidth=2)
    
    media_score = df['score_risco'].mean()
    plt.axvline(media_score, color='red', linestyle='--')
    plt.text(media_score + 2, 0.02, f'Média: {media_score:.1f}', color='red', fontweight='bold')

    plt.title('Distribuição Geral do Score de Risco (0-100)', fontsize=14)
    plt.xlabel('Pontuação de Risco (Quanto maior, mais crítico)', fontsize=11)
    plt.ylabel('Densidade de Clientes', fontsize=11)
    
    save_plot("4_histograma_score_final")
    plt.close()

    # =========================
    # 5. TOP 10 RANKING
    # =========================
    top_risco = df.sort_values('score_risco', ascending=False).head(10)
    plt.figure(figsize=(12, 6))
    bars = plt.bar(top_risco['id'], top_risco['score_risco'], color='#c0392b')
    
    # Adiciona rótulos de dados no topo das barras
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}', ha='center', va='bottom', fontsize=10)

    plt.title('Ranking de Alerta: Top 10 Clientes com Maior Risco de Inadimplência', fontsize=14)
    plt.xlabel('Identificador do Cliente (ID)', fontsize=11)
    plt.ylabel('Score de Risco Calculado', fontsize=11)
    plt.ylim(0, 110) # Espaço para os rótulos
    
    save_plot("5_ranking_top_10_risco")
    plt.close()

    # =========================
    # RELATÓRIO EXECUTIVO NO CONSOLE
    # =========================
    print("\n" + "="*50)
    print("RESUMO EXECUTIVO DA ANÁLISE DE CRÉDITO")
    print("="*50)
    print(f"Total de Clientes Analisados: {len(df)}")
    print(f"Clientes em Estado Crítico: {len(df[df['risco'] == 'critico'])}")
    print(f"Comprometimento Médio da Carteira: {df['consumo_relativo'].mean()*100:.2f}%")
    
    # Teste de Hipótese (Gênero)
    f = df[df['sexo'] == 'F']['consumo_relativo']
    m = df[df['sexo'] == 'M']['consumo_relativo']
    _, p = mannwhitneyu(f, m)
    
    print("\nVALIAÇÃO ESTATÍSTICA (Gênero vs. Consumo):")
    if p > 0.05:
        print(f"-> p-valor: {p:.4f}. Não há diferença comportamental significativa entre gêneros.")
    else:
        print(f"-> p-valor: {p:.4f}. Existe diferença significativa de consumo entre os gêneros.")
    print("="*50)