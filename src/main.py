import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import shapiro
from scipy.stats import mannwhitneyu

filesDir = "./src"
excelDir = f"{filesDir}/csv"
p39Path = f"{excelDir}/p39.xlsx"

df = pd.read_excel(p39Path)

df.rename(columns=str.lower, inplace=True)

duplicates = df[df.duplicated(subset=['id' ],keep=False)]

nullvalues = df.isnull().sum()

if __name__ == "__main__":
    df.info()
    print(
        f"\n\n # 5 primeiros dados:\n{df.head()}",
        f"\n\n # Valores duplicados:\n{duplicates}",
        f"\n\n # Ha valores nulos/vazios?:\n{nullvalues}")
    
    # Normalização (ESSENCIAL)
    df['consumo_relativo'] = df['fatura'] / df['renda']

    # Boxplot normalizado
    plt.figure()
    df.boxplot(column='consumo_relativo', by='sexo')

    plt.title('Consumo relativo por Gênero')
    plt.suptitle('')
    plt.xlabel('Gênero')
    plt.ylabel('Fatura / Renda')

    plt.show()


    # Separação dos grupos
    f = df[df['sexo'] == 'F']['consumo_relativo']
    m = df[df['sexo'] == 'M']['consumo_relativo']

    # Teste estatístico correto
    stat, p = mannwhitneyu(f, m)

    print(f"P-value (normalizado): {p}")


    for genero in df['sexo'].unique():
        subset = df[df['sexo'] == genero]

        plt.figure()
        subset['fatura'].plot(kind='kde')

        plt.title(f'Densidade da Fatura - {genero}')
        plt.show()



    f = df[df['sexo'] == 'F']['fatura']
    m = df[df['sexo'] == 'M']['fatura']

    stat, p = mannwhitneyu(f, m)

    print(p)