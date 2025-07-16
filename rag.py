import pandas as pd

def load_data(path="data/travel_data.xlsx"):
    return pd.read_excel(path)

def search_relevant_places(df, question):
    keywords = [word for word in question.lower().split() if len(word) > 2]
    results = []

    for _, row in df.iterrows():
        combined = f"{row['ชื่อสถานที่']} {row['จังหวัด']} {row['ประเภท']} {row['คำอธิบาย']}".lower()
        if any(kw in combined for kw in keywords):
            results.append(row)

    return results[:5]