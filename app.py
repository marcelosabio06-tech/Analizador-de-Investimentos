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
    "Insira os tickers das ações da B3 abaixo para visualizar a análise técnica e operacional em tempo real."
)

# Painel Lateral para Entrada de Ativos
st.sidebar.header("Parâmetros de Entrada")
ticker_1 = st.sidebar.text_input("Ação 1", "PETR4")
ticker_2 = st.sidebar.text_input("Ação 2", "VALE3")
ticker_3 = st.sidebar.text_input("Ação 3", "ITUB4")

tickers_selecionados = [ticker_1, ticker_2, ticker_3]


@st.cache_data(ttl=3600)  # Evita bloqueio no yfinance guardando cache por 1h
def carregar_dados(ticker_symbol):
    ativo = yf.Ticker(ticker_symbol)
    return ativo.history(period="1y")


def analisar_ativo(ticker_user):
    ticker_symbol = ticker_user.strip().upper()
    if not ticker_symbol:
        return None

    if not ticker_symbol.endswith(".SA"):
        ticker_symbol += ".SA"

    try:
        hist = carregar_dados(ticker_symbol)

        if hist.empty or len(hist) < 200:
            return {"erro": f"Dados insuficientes ou ticker inválido: {ticker_symbol}"}

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

        preco_atual = atual["Close"]
        mme21 = atual["MME21"]
        mms200 = atual["MMS200"]
        rsi14 = atual["RSI14"]
        macd_line = atual["MACD_Line"]
        macd_signal = atual["MACD_Signal"]
        macd_hist = atual["MACD_Hist"]
        macd_hist_ant = anterior["MACD_Hist"]
        vol_atual = atual["Volume"]
        vol_media = atual["Vol_Media_20"]

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
            "Ticker": ticker_symbol.replace(".SA", ""),
            "Preço": f"R$ {preco_atual:.2f}",
            "Pontuação": f"{pontos}/{total}",
            "Percentual": (pontos / total) * 100,
            "Detalhes": detalhes,
            "Hist": df,
        }
    except Exception as e:
        return {"erro": f"Erro ao consultar {ticker_symbol}: {str(e)}"}


# Execução automática da análise sem depender do clique de botão
cols = st.columns(3)

for idx, ticker in enumerate(tickers_selecionados):
    if ticker.strip():
        res = analisar_ativo(ticker)

        if res:
            with cols[idx]:
                if "erro" in res:
                    st.error(res["erro"])
                else:
                    st.subheader(f"📌 {res['Ticker']}")
                    st.metric("Preço Atual", res["Preço"])

                    # Veredito Visual
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

                    # Gráfico de Fechamento com MME21
                    st.line_chart(res["Hist"][["Close", "MME21"]].tail(60))
