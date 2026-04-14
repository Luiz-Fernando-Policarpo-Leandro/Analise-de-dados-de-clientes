import pandas as pd

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