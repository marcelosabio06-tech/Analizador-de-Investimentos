import pandas as pd
importar streamlit como st
importar ta
importar yfinance como yf

# Configuração da Página
st.set_page_config(
    page_title= "Analisador B3 - Swing Trade" , page_icon= "📈" , layout= "wide"
)

st.title( "📈 Analisador de Ações da B3 para Swing Trade" )
st.markdown(
    "Insira até 3 tickers da B3 para analisar os indicadores técnicos e fundamentalistas de forma simultânea."
)

# Painel Lateral para Entrada de Ativos
st.sidebar.header( "Parâmetros de Entrada" )
ticker_1 = st.sidebar.text_input( "Ação 1" , "PETR4" )
ticker_2 = st.sidebar.text_input( "Ação 2" , "VALE3" )
ticker_3 = st.sidebar.text_input( "Ação 3" , "ITUB4" )

tickers_selecionados = [ticker_1, ticker_2, ticker_3]


def  analisar_ativo ( ticker_user ):
    ticker_symbol = ticker_user.strip().upper()
    se  não ticker_symbol.endswith( ".SA" ):
        ticker_symbol += ".SA"

    ativo = yf.Ticker(ticker_symbol)
    hist = ativo.history(period= "1y" )

    se hist.empty ou  len (hist) < 200 :
        return { "erro" : f"Dados insuficientes para {ticker_symbol} ." }

    df = hist.copy()

    #velhos Técnicos
    df[ "MME21" ] = df[ "Close" ].ewm(span= 21 , adjust= False ).mean()
    df[ "MMS200" ] = df[ "Close" ].rolling(window= 200 ).mean()

    # IFR 14
    delta = df[ "Close" ].diff()
    ganho = (delta.where(delta > 0 , 0 )).rolling(window= 14 ).mean()
    perda = (-delta.where(delta < 0 , 0 )).rolling(window= 14 ).mean()
    rs = ganho / perda
    df[ "RSI14" ] = 100 - ( 100 / ( 1 + rs))

    # MACD
    exp1 = df[ "Close" ].ewm(span= 12 , adjust= False ).mean()
    exp2 = df[ "Close" ].ewm(span= 26 , adjust= False ).mean()
    df[ "MACD_Line" ] = exp1 - exp2
    df[ "MACD_Signal" ] = df[ "MACD_Line" ].ewm(span= 9 , adjust= False ).mean()
    df[ "MACD_Hist" ] = df[ "MACD_Line" ] - df[ "MACD_Signal" ]

    # Volume
    df[ "Vol_Media_20" ] = df[ "Volume" ].rolling(window= 20 ).mean()

    atual = df.iloc[- 1 ]
    anterior = df.iloc[- 2 ]

    preco_atual = atual[ "Fechar" ]
    mme21 = atual[ "MME21" ]
    mms200 = atual[ "MMS200" ]
    rsi14 = atual[ "RSI14" ]
    macd_line = atual[ "MACD_Line" ]
    macd_signal = atual[ "MACD_Signal" ]
    macd_hist = atual[ "MACD_Hist" ]
    macd_hist_ant = anterior[ "MACD_Hist" ]
    vol_atual = atual[ "Volume" ]
    vol_media = atual[ "Vol_Media_20" ]

    #
    pontos = 0
    total = 5
    exceto = []

    # Regra 1: MMS 200
    se preco_atual > mms200:
        pontos += 1
        detalhes.append(
            f"✅ **MMS 200:** Preço (R$ {preco_atual: .2 f} ) acima do MMS200 (R$ {mms200: .2 f} )"
        )
    outro :
        detalhes.append(
            f"❌ **MMS 200:** Preço (R$ {preco_atual: .2 f} ) abaixo do MMS200 (R$ {mms200: .2 f} )"
        )

    # Regra 2: MME 21
    se preco_atual >= mme21:
        pontos += 1
        detalhes.append(
            f"✅ **MME 21:** Preço acima da MME21 (R$ {mme21: ​​.2 f} )"
        )
    outro :
        detalhes.append(
            f"⚠️ **MME 21:** Preço abaixo da MME21 (R$ {mme21: ​​.2 f} )"
        )

    # Regra 3: IFR
    se  30 <= rsi14 <= ​​55 :
        pontos += 1
        detalhes.append( f"✅ **IFR 14:** Nível ideal em {rsi14: .1 f} " )
    elif rsi14 > 70 :
        detalhes.append( f"❌ **IFR 14:** Sobrecomprado ( {rsi14: .1 f} )" )
    outro :
        detalhes.append( f"⚠️ **IFR 14:** Nível em {rsi14: .1 f} " )

    # Regra 4: MACD
    se macd_line > macd_signal e macd_hist > macd_hist_ant:
        pontos += 1
        detalhes.append( "✅ **MACD:** Cruzamento altista ativo" )
    outro :
        detalhes.append( "❌ **MACD:** Sem força compradora no momento" )

    # Regra 5: Volume
    se vol_atual >= vol_media:
        pontos += 1
        detalhes.append( "✅ **Volume:** Acima da média de 20 dias" )
    outro :
        detalhes.append( "⚠️ **Volume:** Abaixo da média de 20 dias" )

    retornar {
        "Ticker" : ticker_symbol.replace( ".SA" , "" ),
        "Preço" : f"R$ {preco_atual: .2 f} " ,
        "Pontuação" : f" {pontos} / {total} " ,
        "Percentual" : (pontos/total) * 100 ,
        "Detalhes" : detalhes,
        "Hist" : df,
    }


if st.sidebar.button( "Analisar Ativos" ):
    cols = st.columns( 3 )

    para idx, ticker em  enumerate (tickers_selecionados):
        se ticker.strip():
            res = analisar_ativo(ticker)

            com cols[idx]:
                se  "erro"  em res:
                    st.error(res[ "erro" ])
                outro :
                    st.subheader( f"📌 {res[ 'Ticker' ]} " )
                    st.metric( "Preço Atual" , res[ "Preço" ])

                    # Veredito Visual
                    perc = res[ "Percentual" ]
                    se perc >= 80 :
                        st.sucesso(
                            f"🟢 **IDEAL PARA COMPRA** ( {res[ 'Pontuação' ]} )"
                        )
                    senão se perc >= 60 :
                        aviso de st(
                            f"🟡 **EM OBSERVAÇÃO** ( {res[ 'Pontuação' ]} )"
                        )
                    outro :
                        st.erro(
                            f"🔴 **NÃO RECOMENDADO** ( {res[ 'Pontuação' ]} )"
                        )

                    st.markdown( "### Lista de verificação:" )
                    para d em res[ "Detalhes" ]:
                        st.markdown(d)

                    # Gráfico simples de fechamento com MME21
                    st.line_chart(res[ "Hist" ][[ "Close" , "MME21" ]].tail( 60 ))
