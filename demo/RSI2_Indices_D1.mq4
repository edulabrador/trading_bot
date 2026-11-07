//+------------------------------------------------------------------+
//| RSI2_Indices_D1.mq4                                              |
//| S2: reversion a la media en indices (RSI(2) de Connors).         |
//| Reglas registradas antes del backtest en                         |
//| backtests/research/NUEVAS_ESTRATEGIAS.md; resultados en          |
//| backtests/reports/s2_indices_rsi2.md.                            |
//|                                                                  |
//| Grafico: D1 de un CFD de indice (S&P 500, Nasdaq 100 o DAX; el   |
//| nombre depende del broker: US500, US100, GER40...).              |
//| Entrada (solo largos), al abrir la vela diaria:                  |
//|   Close[1] > SMA(200)[1]  y  RSI(2)[1] < 10                      |
//| Salida (v2, mejora M1), al abrir la vela diaria: RSI(2)[1] > 70  |
//| (Exit_Mode=0 vuelve a la salida original: Close[1] > SMA(5)[1]). |
//| Sin stop ni take profit (version clasica). Tamano por riesgo:    |
//| Risk_Percent del balance por cada ATR(20) diario.                |
//|                                                                  |
//| No compilado ni probado en MetaTrader: compilar en MetaEditor y  |
//| verificar en el Strategy Tester antes de usar. SOLO DEMO.        |
//+------------------------------------------------------------------+
#property strict

input double Risk_Percent   = 0.5;   // % del balance por cada ATR(20) diario
input int    RSI_Period     = 2;
input double RSI_Entry      = 10.0;  // compra si RSI(2) < este nivel
input int    SMA_Trend      = 200;
input int    Exit_Mode      = 1;     // 1 = RSI(2) > RSI_Exit (M1, validada); 0 = Close > SMA(5) (original)
input double RSI_Exit       = 70.0;
input int    SMA_Exit       = 5;
input int    ATR_Period     = 20;
input double Max_Lots       = 1.0;   // tope de seguridad
input int    Magic_Number   = 22001; // usa uno distinto por indice (22001 S&P, 22002 Nasdaq, 22003 DAX)

datetime lastBar = 0;

int OnInit()
  {
   if(Period() != PERIOD_D1)
      Print("Aviso: este EA esta pensado para el grafico D1.");
   lastBar = iTime(NULL, PERIOD_D1, 0);
   return(INIT_SUCCEEDED);
  }

int FindPosition()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS) && OrderSymbol() == _Symbol && OrderMagicNumber() == Magic_Number)
         return(OrderTicket());
   return(-1);
  }

double LotsByRisk()
  {
   double atr       = iATR(NULL, PERIOD_D1, ATR_Period, 1);
   double tickValue = MarketInfo(_Symbol, MODE_TICKVALUE);
   double tickSize  = MarketInfo(_Symbol, MODE_TICKSIZE);
   double step      = MarketInfo(_Symbol, MODE_LOTSTEP);
   double minLot    = MarketInfo(_Symbol, MODE_MINLOT);
   double maxLot    = MathMin(MarketInfo(_Symbol, MODE_MAXLOT), Max_Lots);
   if(atr <= 0 || tickValue <= 0 || tickSize <= 0 || step <= 0)
      return(0);
   double moneyPerLotPerAtr = atr / tickSize * tickValue;
   double lots = AccountBalance() * Risk_Percent / 100.0 / moneyPerLotPerAtr;
   lots = MathFloor(lots / step) * step;
   if(lots < minLot)
     {
      Print("Lote calculado por debajo del minimo (", DoubleToString(lots, 2), "): se usa el minimo ", minLot);
      lots = minLot;
     }
   return(MathMin(lots, maxLot));
  }

void OnTick()
  {
   datetime bar = iTime(NULL, PERIOD_D1, 0);
   if(bar == lastBar)
      return;
   lastBar = bar;

   double close1 = iClose(NULL, PERIOD_D1, 1);
   double rsi1   = iRSI(NULL, PERIOD_D1, RSI_Period, PRICE_CLOSE, 1);
   double smaT1  = iMA(NULL, PERIOD_D1, SMA_Trend, 0, MODE_SMA, PRICE_CLOSE, 1);
   double smaE1  = iMA(NULL, PERIOD_D1, SMA_Exit, 0, MODE_SMA, PRICE_CLOSE, 1);

   int ticket = FindPosition();
   if(ticket > 0)
     {
      bool exitNow = Exit_Mode == 1 ? rsi1 > RSI_Exit : close1 > smaE1;
      if(exitNow && OrderSelect(ticket, SELECT_BY_TICKET))
        {
         RefreshRates();
         if(!OrderClose(ticket, OrderLots(), Bid, 30, clrYellow))
            Print("Error al cerrar: ", GetLastError());
        }
      return;
     }

   if(close1 > smaT1 && rsi1 < RSI_Entry)
     {
      double lots = LotsByRisk();
      if(lots <= 0)
         return;
      RefreshRates();
      int t = OrderSend(_Symbol, OP_BUY, lots, Ask, 30, 0, 0, "RSI2 " + IntegerToString(Magic_Number), Magic_Number, 0, clrGreen);
      if(t < 0)
         Print("Error al abrir: ", GetLastError());
     }
  }
