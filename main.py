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

os.makedirs(imgDir, exist_ok=True)
for filename in os.listdir(imgDir):
    file_path = os.path.join(imgDir, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

def save_plot(name):
    path = f"{imgDir}/{name}.png"
    plt.savefig(path, bbox_inches='tight')
    print(f"[✔] Gráfico '{name}' salvo.")

# =========================
# LEITURA
# =========================
df = pd.read_excel(p39Path, usecols="A:K")
df.rename(columns=str.lower, inplace=True)
df = df[df['id'].str.startswith('C')]

if __name__ == "__main__":

    print("\n=== 1. VERIFICAÇÃO DE MÉTRICAS E ESCALAS ===")
    df['consumo_relativo'] = df['fatura'] / df['renda']
    
    # Valores originais antes da normalização
    print(f"Consumo Relativo (Original) -> Min: {df['consumo_relativo'].min():.4f}, Max: {df['consumo_relativo'].max():.4f}")
    
    scaler = MinMaxScaler()
    df['consumo_norm'] = scaler.fit_transform(df[['consumo_relativo']])
    
    df['inverso_log_renda'] = 1 / np.log(df['renda'])
    print(f"Inverso Log Renda (Original) -> Min: {df['inverso_log_renda'].min():.4f}, Max: {df['inverso_log_renda'].max():.4f}")
    
    df['renda_norm'] = scaler.fit_transform(df[['inverso_log_renda']])

    # Verificação da Normalização (Deve ser sempre 0 a 1)
    print(f"Consumo (Normalizado) -> Min: {df['consumo_norm'].min()}, Max: {df['consumo_norm'].max()}")
    print(f"Renda (Normalizada)   -> Min: {df['renda_norm'].min()}, Max: {df['renda_norm'].max()}")

    # Cálculo do Score de Risco:
    # $$score\_risco = (consumo\_norm \times 0.8 + renda\_norm \times 0.2) \times 100$$
    df['score_risco'] = (df['consumo_norm'] * 0.8 + df['renda_norm'] * 0.2) * 100

    def classificar_risco(x):
        if x < 0.1: return 'baixo'
        elif x < 0.2: return 'moderado'
        elif x < 0.25: return 'alto'
        else: return 'critico'

    df['risco'] = df['consumo_relativo'].apply(classificar_risco)

    print("\n=== 2. DISTRIBUIÇÃO DAS CLASSES DE RISCO ===")
    print(df['risco'].value_counts())

    # =========================
    # VISUALIZAÇÃO (SCATTER, HEATMAP, ETC)
    # =========================
    # [Mantendo sua lógica de plots...]
    plt.figure()
    cores = {'baixo': 'blue', 'moderado': 'green', 'alto': 'orange', 'critico': 'red'}
    for risco, cor in cores.items():
        subset = df[df['risco'] == risco]
        plt.scatter(subset['renda'], subset['consumo_relativo'], label=risco, color=cor)
    plt.axhline(y=0.25, linestyle='--')
    plt.xlabel('Renda'); plt.ylabel('Consumo Relativo'); plt.legend()
    save_plot("scatter")
    plt.close()

    # HEATMAP COM MAPEAMENTO CATEGÓRICO
    if 'propria' in df.columns:
        df['propria_num'] = df['propria'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})
    if 'superior' in df.columns:
        df['superior_num'] = df['superior'].astype(str).str.lower().map({'sim': 1, 'nao': 0, 'não': 0})

    colunas_corr = ['renda', 'fatura', 'idade', 'consumo_relativo']
    if 'propria_num' in df.columns: colunas_corr.append('propria_num')
    if 'superior_num' in df.columns: colunas_corr.append('superior_num')

    print("\n=== 3. MATRIZ DE CORRELAÇÃO (VALORES) ===")
    corr = df[colunas_corr].corr()
    print(corr.round(2))

    plt.figure()
    im = plt.imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
    plt.colorbar(im)
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
    plt.yticks(range(len(corr.columns)), corr.columns)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha='center', va='center')
    save_plot("heatmap_corr_corrigido")
    plt.close()

    # OUTROS PLOTS
    df.boxplot(column='consumo_relativo', by='risco', showfliers=False)
    save_plot("boxplot")
    plt.close()

    df['score_risco'].plot(kind='hist', bins=30, density=True)
    df['score_risco'].plot(kind='kde')
    plt.axvline(df['score_risco'].mean(), linestyle='--', color='red')
    save_plot("hist_score")
    plt.close()

    top_risco = df.sort_values('score_risco', ascending=False).head(10)
    plt.figure()
    plt.bar(top_risco['id'], top_risco['score_risco'])
    plt.xticks(rotation=45)
    save_plot("top10")
    plt.close()

    # =========================
    # TESTES ESTATÍSTICOS DETALHADOS
    # =========================
    print("\n=== 4. TESTES DE NORMALIDADE (SHAPIRO-WILK) ===")
    is_normal = True
    for genero in df['sexo'].unique():
        subset = df[df['sexo'] == genero]['consumo_relativo'].dropna()
        if len(subset) >= 3:
            stat, p = shapiro(subset)
            print(f"Gênero {genero}: Estatística={stat:.4f}, p-value={p:.4f}")
            if p < 0.05:
                is_normal = False
                print(f"   -> Resultado: Distribuição NÃO é normal para {genero}.")
            else:
                print(f"   -> Resultado: Distribuição parece normal para {genero}.")

    f = df[df['sexo'] == 'F']['consumo_relativo'].dropna()
    m = df[df['sexo'] == 'M']['consumo_relativo'].dropna()

    print("\n=== 5. COMPARAÇÃO DE GRUPOS (MÉDIAS/MEDIANAS) ===")
    if is_normal:
        stat, p_final = ttest_ind(f, m)
        print(f"Executando T-Test (Paramétrico): Estatística={stat:.4f}, p={p_final:.4f}")
    else:
        stat, p_final = mannwhitneyu(f, m)
        print(f"Executando Mann-Whitney U (Não-Paramétrico): Estatística={stat:.4f}, p={p_final:.4f}")

    if p_final < 0.05:
        print("Conclusão: Existe diferença estatisticamente significativa entre os gêneros.")
    else:
        print("Conclusão: Não há diferença significativa entre os gêneros.")

    # =========================
    # OUTPUT FINAL
    # =========================
    print("\n=== 6. TOP 10 CLIENTES EM RISCO ===")
    print(top_risco[['id', 'renda', 'consumo_relativo', 'score_risco']].to_string(index=False))

    df.drop(columns=['consumo_norm', 'inverso_log_renda', 'renda_norm', 'propria_num', 'superior_num'], inplace=True, errors='ignore')
    df.to_csv(f"{imgDir}/dataset_analisado.csv", index=False)
    print(f"\n[✔] Processo finalizado. CSV salvo em: {imgDir}/dataset_analisado.csv")