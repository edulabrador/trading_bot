//+------------------------------------------------------------------+
//| ExportTrades.mq4  (script)                                       |
//| Exporta el historial de operaciones cerradas de la cuenta a      |
//| MQL4/Files/forward_trades.csv para analizarlo con                |
//| forward/check_forward.py.                                        |
//| Uso: en MetaTrader, pestana "Historial de cuenta" > clic derecho |
//| > "Todo el historial"; despues arrastra este script al grafico.  |
//| No compilado ni probado aqui: compilar en MetaEditor.            |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input string FileName = "forward_trades.csv";

void OnStart()
  {
   int h = FileOpen(FileName, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(h == INVALID_HANDLE)
     {
      Print("No se pudo crear ", FileName, " error ", GetLastError());
      return;
     }
   FileWrite(h, "ticket", "magic", "symbol", "type", "lots", "open_time", "open_price",
             "close_time", "close_price", "sl", "tp", "profit", "swap", "commission", "digits");
   int n = 0;
   for(int i = 0; i < OrdersHistoryTotal(); i++)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
         continue;
      if(OrderType() != OP_BUY && OrderType() != OP_SELL)
         continue;  // ignora depositos, pendientes cancelados, etc.
      int digits = (int)MarketInfo(OrderSymbol(), MODE_DIGITS);
      FileWrite(h, OrderTicket(), OrderMagicNumber(), OrderSymbol(),
                OrderType() == OP_BUY ? "BUY" : "SELL", DoubleToString(OrderLots(), 2),
                TimeToString(OrderOpenTime(), TIME_DATE | TIME_SECONDS), DoubleToString(OrderOpenPrice(), digits),
                TimeToString(OrderCloseTime(), TIME_DATE | TIME_SECONDS), DoubleToString(OrderClosePrice(), digits),
                DoubleToString(OrderStopLoss(), digits), DoubleToString(OrderTakeProfit(), digits),
                DoubleToString(OrderProfit(), 2), DoubleToString(OrderSwap(), 2),
                DoubleToString(OrderCommission(), 2), digits);
      n++;
     }
   FileClose(h);
   Print("Exportadas ", n, " operaciones a MQL4/Files/", FileName);
  }
