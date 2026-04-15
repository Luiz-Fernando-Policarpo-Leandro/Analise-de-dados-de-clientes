import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, shapiro, ttest_ind
from sklearn.preprocessing import MinMaxScaler

filesDir = "./src"
imgDir = f"{filesDir}/img"
excelDir = f"{filesDir}/csv"
p39Path = f"{excelDir}/p39.xlsx"

# limpar pasta
os.makedirs(imgDir, exist_ok=True)
for filename in os.listdir(imgDir):
    file_path = os.path.join(imgDir, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

def save_plot(name):
    path = f"{imgDir}/{name}.png"
    plt.savefig(path, bbox_inches='tight')
    print(f"[✔] {name} salvo em: {path}")

# =========================
# LEITURA
# =========================
df = pd.read_excel(p39Path, usecols="A:K")
df.rename(columns=str.lower, inplace=True)
df = df[df['id'].str.startswith('C')]

if __name__ == "__main__":

    print("\n=== INFO ===")
    df.info()

    # =========================
    # MÉTRICAS E NORMALIZAÇÃO
    # =========================
    df['consumo_relativo'] = df['fatura'] / df['renda']

    # Normalizando as variáveis antes de calcular o score para alinhar as escalas
    scaler = MinMaxScaler()
    df['consumo_norm'] = scaler.fit_transform(df[['consumo_relativo']])
    
    # Inverso do log da renda (maior renda = menor risco = menor o inverso)
    df['inverso_log_renda'] = 1 / np.log(df['renda'])
    df['renda_norm'] = scaler.fit_transform(df[['inverso_log_renda']])

    # Calculando o score final com os pesos ajustados corretamente na mesma escala
    df['score_risco'] = (
        df['consumo_norm'] * 0.8 +
        df['renda_norm'] * 0.2
    ) * 100

    def classificar_risco(x):
        if x < 0.1:
            return 'baixo'
        elif x < 0.2:
            return 'moderado'
        elif x < 0.25:
            return 'alto'
        else:
            return 'critico'

    df['risco'] = df['consumo_relativo'].apply(classificar_risco)

    print("\n=== DISTRIBUIÇÃO DE RISCO ===")
    print(df['risco'].value_counts())

    # =========================
    # SCATTER
    # =========================
    plt.figure()

    cores = {
        'baixo': 'blue',
        'moderado': 'green',
        'alto': 'orange',
        'critico': 'red'
    }

    for risco, cor in cores.items():
        subset = df[df['risco'] == risco]
        plt.scatter(subset['renda'], subset['consumo_relativo'], label=risco, color=cor)

    plt.axhline(y=0.25, linestyle='--')

    plt.xlabel('Renda')
    plt.ylabel('Consumo Relativo')
    plt.title('Renda vs Consumo')
    plt.legend()

    save_plot("scatter")
    plt.close()

    # =========================
    # HEATMAP CORRIGIDO
    # =========================
    plt.figure()

    # Convertendo colunas categóricas para numéricas para incluí-las na correlação
    if 'propria' in df.columns:
        df['propria_num'] = df['propria'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})
    if 'superior' in df.columns:
        df['superior_num'] = df['superior'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})

    # Selecionando as colunas para o mapa de calor dinamicamente
    colunas_correlacao = ['renda', 'fatura', 'idade', 'consumo_relativo']
    if 'propria_num' in df.columns: colunas_correlacao.append('propria_num')
    if 'superior_num' in df.columns: colunas_correlacao.append('superior_num')

    corr = df[colunas_correlacao].corr()

    im = plt.imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
    plt.colorbar(im)

    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
    plt.yticks(range(len(corr.columns)), corr.columns)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}",
                     ha='center', va='center', fontsize=9)

    plt.title("Correlação (-1 a 1)")

    save_plot("heatmap_corr_corrigido")
    plt.close()

    # =========================
    # BOXPLOT
    # =========================
    plt.figure()

    df.boxplot(column='consumo_relativo', by='risco', showfliers=False)

    plt.title("Consumo por Risco")
    plt.suptitle('')
    plt.ylim(0, 0.3)

    save_plot("boxplot")
    plt.close()

    # =========================
    # HIST + KDE
    # =========================
    plt.figure()

    df['score_risco'].plot(kind='hist', bins=30, density=True)
    df['score_risco'].plot(kind='kde')

    plt.axvline(df['score_risco'].mean(), linestyle='--', color='red')

    plt.title("Distribuição do Score")

    save_plot("hist_score")
    plt.close()

    # =========================
    # TOP RISCO
    # =========================
    top_risco = df.sort_values('score_risco', ascending=False).head(10)

    plt.figure()
    plt.bar(top_risco['id'], top_risco['score_risco'])
    plt.xticks(rotation=45)

    plt.title("Top 10 Risco")

    save_plot("top10")
    plt.close()

    # =========================
    # TESTES ESTATÍSTICOS
    # =========================
    print("\n=== TESTE SHAPIRO ===")
    is_normal = True
    for genero in df['sexo'].unique():
        subset = df[df['sexo'] == genero]['consumo_relativo'].dropna()
        if len(subset) >= 3: # Shapiro requer pelo menos 3 amostras
            _, p = shapiro(subset)
            print(f"{genero}: p-value = {p:.4f}")
            if p < 0.05:
                is_normal = False
        else:
            print(f"{genero}: Amostras insuficientes para Shapiro")
            is_normal = False

    f = df[df['sexo'] == 'F']['consumo_relativo'].dropna()
    m = df[df['sexo'] == 'M']['consumo_relativo'].dropna()

    if is_normal:
        print("\n[!] Dados normais: Aplicando T-Test de Student")
        _, p_final = ttest_ind(f, m)
        print(f"T-Test: p = {p_final:.4f}")
    else:
        print("\n[!] Dados não-normais: Aplicando Mann-Whitney U")
        _, p_final = mannwhitneyu(f, m)
        print(f"Mann-Whitney: p = {p_final:.4f}")

    # =========================
    # OUTPUT FINAL
    # =========================
    print("\n=== TOP 10 RISCO ===")
    print(top_risco[['id', 'renda', 'consumo_relativo', 'score_risco']])

    # Limpando as colunas auxiliares antes de salvar o dataset final
    df.drop(columns=['consumo_norm', 'inverso_log_renda', 'renda_norm'], inplace=True, errors='ignore')

    df.to_csv(f"{imgDir}/dataset_analisado.csv", index=False)
    print(f"\n[✔] Dataset salvo em: {imgDir}/dataset_analisado.csv")