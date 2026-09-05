import pandas as pd
import streamlit as st
import ta
import yfinance as yf

# Configuração da Página
st.set_page_config(
    page_title="Analisador B3 - Swing Trade", page_icon="📈", layout="wide"
)

st.title("📈 Analisador de Ações da B3 para Swing Trade")
st.markdown(
    "Digite os códigos das ações abaixo e clique no botão para executar uma nova análise."
)

# Formulário na barra lateral para travar o envio dos novos tickers
with st.sidebar.form(key="form_tickers"):
    st.header("Parâmetros de Entrada")
    ticker_1 = st.text_input("Ação 1", value="PETR4")
    ticker_2 = st.text_input("Ação 2", value="VALE3")
    ticker_3 = st.text_input("Ação 3", value="ITUB4")

    # Botão do formulário
    btn_submeter = st.form_submit_button("🚀 Analisar Novos Ativos")


def analisar_ativo(ticker_user):
    ticker_clean = ticker_user.strip().upper()
    if not ticker_clean:
        return None

    if not ticker_clean.endswith(".SA"):
        ticker_symbol = ticker_clean + ".SA"
    else:
        ticker_symbol = ticker_clean

    try:
        # Força o download atualizado ignorando o cache interno
        hist = yf.download(ticker_symbol, period="1y", progress=False)

        if hist.empty or len(hist) < 200:
            return {
                "erro": f"Dados insuficientes ou ticker não encontrado: {ticker_clean}"
            }

        # Trata coluna de preços para séries do yfinance
        if isinstance(hist.columns, pd.MultiIndex):
            df = hist.xs(ticker_symbol, level=1, axis=1).copy()
        else:
            df = hist.copy()

        # Indicadores Técnicos
        df["MME21"] = df["Close"].ewm(span=21, adjust=False).mean()
        df["MMS200"] = df["Close"].rolling(window=200).mean()

        # IFR 14
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI14"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD_Line"] = exp1 - exp2
        df["MACD_Signal"] = df["MACD_Line"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD_Line"] - df["MACD_Signal"]

        # Volume
        df["Vol_Media_20"] = df["Volume"].rolling(window=20).mean()

        atual = df.iloc[-1]
        anterior = df.iloc[-2]

        preco_atual = float(atual["Close"])
        mme21 = float(atual["MME21"])
        mms200 = float(atual["MMS200"])
        rsi14 = float(atual["RSI14"])
        macd_line = float(atual["MACD_Line"])
        macd_signal = float(atual["MACD_Signal"])
        macd_hist = float(atual["MACD_Hist"])
        macd_hist_ant = float(anterior["MACD_Hist"])
        vol_atual = float(atual["Volume"])
        vol_media = float(atual["Vol_Media_20"])

        # Avaliações
        pontos = 0
        total = 5
        detalhes = []

        # Regra 1: MMS 200
        if preco_atual > mms200:
            pontos += 1
            detalhes.append(
                f"✅ **MMS 200:** Preço (R$ {preco_atual:.2f}) acima da MMS200 (R$ {mms200:.2f})"
            )
        else:
            detalhes.append(
                f"❌ **MMS 200:** Preço (R$ {preco_atual:.2f}) abaixo da MMS200 (R$ {mms200:.2f})"
            )

        # Regra 2: MME 21
        if preco_atual >= mme21:
            pontos += 1
            detalhes.append(
                f"✅ **MME 21:** Preço acima da MME21 (R$ {mme21:.2f})"
            )
        else:
            detalhes.append(
                f"⚠️ **MME 21:** Preço abaixo da MME21 (R$ {mme21:.2f})"
            )

        # Regra 3: IFR
        if 30 <= rsi14 <= 55:
            pontos += 1
            detalhes.append(f"✅ **IFR 14:** Nível ideal em {rsi14:.1f}")
        elif rsi14 > 70:
            detalhes.append(f"❌ **IFR 14:** Sobrecomprado ({rsi14:.1f})")
        else:
            detalhes.append(f"⚠️ **IFR 14:** Nível em {rsi14:.1f}")

        # Regra 4: MACD
        if macd_line > macd_signal and macd_hist > macd_hist_ant:
            pontos += 1
            detalhes.append("✅ **MACD:** Cruzamento altista ativo")
        else:
            detalhes.append("❌ **MACD:** Sem força compradora no momento")

        # Regra 5: Volume
        if vol_atual >= vol_media:
            pontos += 1
            detalhes.append("✅ **Volume:** Acima da média de 20 dias")
        else:
            detalhes.append("⚠️ **Volume:** Abaixo da média de 20 dias")

        return {
            "Ticker": ticker_clean,
            "Preço": f"R$ {preco_atual:.2f}",
            "Pontuação": f"{pontos}/{total}",
            "Percentual": (pontos / total) * 100,
            "Detalhes": detalhes,
            "Hist": df,
        }
    except Exception as e:
        return {"erro": f"Erro ao processar {ticker_clean}: {str(e)}"}


# A análise roda sempre que o botão do formulário for clicado ou na abertura inicial
tickers_para_analisar = [ticker_1, ticker_2, ticker_3]

cols = st.columns(3)

for idx, ticker in enumerate(tickers_para_analisar):
    if ticker.strip():
        res = analisar_ativo(ticker)

        if res:
            with cols[idx]:
                if "erro" in res:
                    st.error(res["erro"])
                else:
                    st.subheader(f"📌 {res['Ticker']}")
                    st.metric("Preço Atual", res["Preço"])

                    perc = res["Percentual"]
                    if perc >= 80:
                        st.success(
                            f"🟢 **IDEAL PARA COMPRA** ({res['Pontuação']})"
                        )
                    elif perc >= 60:
                        st.warning(
                            f"🟡 **EM OBSERVAÇÃO** ({res['Pontuação']})"
                        )
                    else:
                        st.error(
                            f"🔴 **NÃO RECOMENDADO** ({res['Pontuação']})"
                        )

                    st.markdown("### Checklist:")
                    for d in res["Detalhes"]:
                        st.markdown(d)

                    st.line_chart(res["Hist"][["Close", "MME21"]].tail(60))
