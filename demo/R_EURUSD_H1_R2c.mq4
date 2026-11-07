//+------------------------------------------------------------------+
//| R_EURUSD_H1_R2c.mq4                                              |
//| Variante R2c del EA R_EURUSD_H1.mq4: sin salida por RVI, SL/TP   |
//| por ATR diario y filtro de tendencia D1 SMA200.                  |
//| HIPOTESIS para forward en demo: no paso las reglas del protocolo |
//| (solo ~5 trades al anio). Ver backtests/research/RESULTADOS.md.  |
//| No compilado ni probado en MetaTrader: compilar y verificar en   |
//| el Strategy Tester antes de usar.                                |
//+------------------------------------------------------------------+
static input string StrategyProperties__ = "------------"; // ------ Expert Properties ------
static input double Entry_Amount = 0.10; // Entry lots
input int Stop_Loss   = 324; // Stop Loss (pips), solo si SL_ATR_Mult = 0
input int Take_Profit = 328; // Take Profit (pips), solo si TP_ATR_Mult = 0
input double SL_ATR_Mult = 3.438; // SL = mult x ATR(14) diario del dia anterior (0 = usar Stop_Loss)
input double TP_ATR_Mult = 3.481; // TP = mult x ATR(14) diario del dia anterior (0 = usar Take_Profit)
input int ATR_Period_D1 = 14; // Periodo del ATR diario
input int Trend_SMA_D1 = 200; // Filtro D1: largos si Close D1 > SMA, cortos si Close D1 < SMA
static input string Ind0 = "------------";// ----- Williams' Percent Range -----
input int Ind0Param0 = 31; // Period
input int Ind0Param1 = -24; // Level
static input string Ind1 = "------------";// ----- Stochastic -----
input int Ind1Param0 = 3; // %K Period
input int Ind1Param1 = 2; // %D Period
input int Ind1Param2 = 2; // Slowing
input int Ind1Param3 = 20; // Level
static input string Ind2 = "------------";// ----- Alligator -----
input int Ind2Param0 = 33; // Jaws period
input int Ind2Param1 = 17; // Jaws shift
input int Ind2Param2 = 6; // Teeth period
input int Ind2Param3 = 5; // Teeth shift
input int Ind2Param4 = 4; // Lips period
input int Ind2Param5 = 1; // Lips shift
static input string Ind3 = "------------";// ----- RVI -----
input int Ind3Param0 = 14; // Period
input double Ind3Param1 = 0.00; // Level

static input string ExpertSettings__ = "------------"; // ------ Expert Settings ------
static input int Magic_Number = 31422196; // Magic Number

#define TRADE_RETRY_COUNT 4
#define TRADE_RETRY_WAIT  100
#define OP_FLAT           -1

// Session time is set in seconds from 00:00
int sessionSundayOpen           = 0;     // 00:00
int sessionSundayClose          = 86400; // 24:00
int sessionMondayThursdayOpen   = 7200;  // 02:00
int sessionMondayThursdayClose  = 79200; // 22:00
int sessionFridayOpen           = 7200;  // 02:00
int sessionFridayClose          = 79200; // 22:00
bool sessionIgnoreSunday        = true;
bool sessionCloseAtSessionClose = false;
bool sessionCloseAtFridayClose  = false;

const double sigma   = 0.000001;

double posType       = OP_FLAT;
int    posTicket     = 0;
double posLots       = 0;
double posStopLoss   = 0;
double posTakeProfit = 0;

datetime barTime;
int      digits;
double   pip;
double   stopLevel;
bool     isTrailingStop=false;
bool     setProtectionSeparately=false;
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int OnInit()
  {
   barTime        = Time[0];
   digits         = (int) MarketInfo(_Symbol, MODE_DIGITS);
   pip            = GetPipValue(digits);
   stopLevel      = MarketInfo(_Symbol, MODE_STOPLEVEL);
   isTrailingStop = isTrailingStop && Stop_Loss > 0;

   const ENUM_INIT_RETCODE initRetcode = ValidateInit();

   return (initRetcode);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnTick()
  {
   if(Time[0]>barTime)
     {
      barTime=Time[0];
      OnBar();
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnBar()
  {
   UpdatePosition();

   if(posType!=OP_FLAT && IsForceSessionClose())
     {
      ClosePosition();
      return;
     }

   if(IsOutOfSession())
      return;

   if(posType!=OP_FLAT)
     {
      ManageClose();
      UpdatePosition();
     }

   if(posType!=OP_FLAT && isTrailingStop)
     {
      double trailingStop=GetTrailingStop();
      ManageTrailingStop(trailingStop);
      UpdatePosition();
     }

   if(posType==OP_FLAT)
     {
      ManageOpen();
      UpdatePosition();
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void UpdatePosition()
  {
   posType   = OP_FLAT;
   posTicket = 0;
   posLots   = 0;
   int total = OrdersTotal();

   for(int pos=total-1; pos>=0; pos--)
     {
      if(OrderSelect(pos,SELECT_BY_POS) &&
         OrderSymbol()==_Symbol &&
         OrderMagicNumber()==Magic_Number)
        {
         posType       = OrderType();
         posLots       = OrderLots();
         posTicket     = OrderTicket();
         posStopLoss   = OrderStopLoss();
         posTakeProfit = OrderTakeProfit();
         break;
        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ManageOpen()
  {
   double ind0val1 = iWPR(NULL,0,Ind0Param0,1);
   double ind0val2 = iWPR(NULL,0,Ind0Param0,2);
   bool ind0long  = ind0val1 > Ind0Param1 + sigma && ind0val2 < Ind0Param1 - sigma;
   bool ind0short = ind0val1 < -100 - Ind0Param1 - sigma && ind0val2 > -100 - Ind0Param1 + sigma;

   double ind1val1 = iStochastic(NULL,0,Ind1Param0,Ind1Param1,Ind1Param2,MODE_SMA,STO_LOWHIGH,MODE_MAIN,1);
   double ind1val2 = iStochastic(NULL,0,Ind1Param0,Ind1Param1,Ind1Param2,MODE_SMA,STO_LOWHIGH,MODE_MAIN,2);
   bool ind1long  = ind1val1 < ind1val2 - sigma;
   bool ind1short = ind1val1 > ind1val2 + sigma;

   double ind2val1 = iAlligator(NULL,0,Ind2Param0,Ind2Param1,Ind2Param2,Ind2Param3,Ind2Param4,Ind2Param5,MODE_SMMA,PRICE_MEDIAN,MODE_GATORTEETH,1);
   double ind2val2 = iAlligator(NULL,0,Ind2Param0,Ind2Param1,Ind2Param2,Ind2Param3,Ind2Param4,Ind2Param5,MODE_SMMA,PRICE_MEDIAN,MODE_GATORTEETH,2);
   bool ind2long  = ind2val1 < ind2val2 - sigma;
   bool ind2short = ind2val1 > ind2val2 + sigma;

   // R2c: filtro de tendencia diario (dia cerrado anterior)
   double d1Close = iClose(NULL,PERIOD_D1,1);
   double d1Sma   = iMA(NULL,PERIOD_D1,Trend_SMA_D1,0,MODE_SMA,PRICE_CLOSE,1);
   bool trendUp   = d1Close > d1Sma;

   const bool canOpenLong  = ind0long && ind1long && ind2long && trendUp;
   const bool canOpenShort = ind0short && ind1short && ind2short && !trendUp;

   if(canOpenLong && canOpenShort)
      return;

   if(canOpenLong)
      OpenPosition(OP_BUY);
   else if(canOpenShort)
      OpenPosition(OP_SELL);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ManageClose()
  {
   // R2c: sin salida por RVI. La posicion se cierra solo por Stop Loss o Take Profit.
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OpenPosition(int command)
  {
   for(int attempt=0; attempt<TRADE_RETRY_COUNT; attempt++)
     {
      int    ticket     = 0;
      int    lastError  = 0;
      bool   modified   = false;
      double stopLoss   = GetStopLoss(command);
      double takeProfit = GetTakeProfit(command);
      string comment    = IntegerToString(Magic_Number);
      color  arrowColor = command==OP_BUY ? clrGreen : clrRed;

      if(IsTradeContextFree())
        {
         double price=MarketInfo(_Symbol,command==OP_BUY ? MODE_ASK : MODE_BID);
         if(setProtectionSeparately)
           {
            ticket=OrderSend(_Symbol,command,Entry_Amount,price,10,0,0,comment,Magic_Number,0,arrowColor);
            if(ticket>0 && (Stop_Loss>0 || Take_Profit>0))
              {
               modified=OrderModify(ticket,0,stopLoss,takeProfit,0,clrBlue);
              }
           }
         else
           {
            ticket=OrderSend(_Symbol,command,Entry_Amount,price,10,stopLoss,takeProfit,comment,Magic_Number,0,arrowColor);
            lastError=GetLastError();
            if(ticket<=0 && lastError==130)
              {
               ticket=OrderSend(_Symbol,command,Entry_Amount,price,10,0,0,comment,Magic_Number,0,arrowColor);
               if(ticket>0 && (Stop_Loss>0 || Take_Profit>0))
                 {
                  modified=OrderModify(ticket,0,stopLoss,takeProfit,0,clrBlue);
                 }
               if(ticket>0 && modified)
                 {
                  setProtectionSeparately=true;
                  Print("Detected ECN type position protection.");
                 }
              }
           }
        }

      if(ticket>0)
         break;

      lastError=GetLastError();
      if(lastError!=135 && lastError!=136 && lastError!=137 && lastError!=138)
         break;

      Sleep(TRADE_RETRY_WAIT);
      Print("Open Position retry no: "+IntegerToString(attempt+2));
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ClosePosition()
  {
   for(int attempt=0; attempt<TRADE_RETRY_COUNT; attempt++)
     {
      bool closed;
      int lastError=0;

      if(IsTradeContextFree())
        {
         double price=MarketInfo(_Symbol,posType==OP_BUY ? MODE_BID : MODE_ASK);
         closed=OrderClose(posTicket,posLots,price,10,clrYellow);
         lastError=GetLastError();
        }

      if(closed)
         break;

      if(lastError==4108)
         break;

      Sleep(TRADE_RETRY_WAIT);
      Print("Close Position retry no: "+IntegerToString(attempt+2));
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ModifyPosition()
  {
   for(int attempt=0; attempt<TRADE_RETRY_COUNT; attempt++)
     {
      bool modified;
      int lastError=0;

      if(IsTradeContextFree())
        {
         modified=OrderModify(posTicket,0,posStopLoss,posTakeProfit,0,clrBlue);
         lastError=GetLastError();
        }

      if(modified)
         break;

      if(lastError==4108)
         break;

      Sleep(TRADE_RETRY_WAIT);
      Print("Modify Position retry no: "+IntegerToString(attempt+2));
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double GetStopLoss(int command)
  {
   if(Stop_Loss==0 && SL_ATR_Mult<=0)
      return (0);

   double atr      = iATR(NULL,PERIOD_D1,ATR_Period_D1,1);
   double dist     = SL_ATR_Mult>0 && atr>0 ? SL_ATR_Mult*atr : pip*Stop_Loss;
   double delta    = MathMax(dist, _Point*stopLevel);
   double price    = MarketInfo(_Symbol, command==OP_BUY ? MODE_BID : MODE_ASK);
   double stopLoss = command==OP_BUY ? price-delta : price+delta;
   return (NormalizeDouble(stopLoss, digits));
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double GetTakeProfit(int command)
  {
   if(Take_Profit==0 && TP_ATR_Mult<=0)
      return (0);

   double atr        = iATR(NULL,PERIOD_D1,ATR_Period_D1,1);
   double dist       = TP_ATR_Mult>0 && atr>0 ? TP_ATR_Mult*atr : pip*Take_Profit;
   double delta      = MathMax(dist, _Point*stopLevel);
   double price      = MarketInfo(_Symbol, command==OP_BUY ? MODE_BID : MODE_ASK);
   double takeProfit = command==OP_BUY ? price+delta : price-delta;
   return (NormalizeDouble(takeProfit, digits));
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double GetTrailingStop()
  {
   double bid=MarketInfo(_Symbol,MODE_BID);
   double ask=MarketInfo(_Symbol,MODE_ASK);
   double stopLevelPoints=_Point*stopLevel;
   double stopLossPoints=pip*Stop_Loss;

   if(posType==OP_BUY)
     {
      double stopLossPrice=High[1]-stopLossPoints;
      if(posStopLoss<stopLossPrice-pip)
        {
         if(stopLossPrice<bid)
           {
            if(stopLossPrice>=bid-stopLevelPoints)
               return (bid - stopLevelPoints);
            else
               return (stopLossPrice);
           }
         else
           {
            return (bid);
           }
        }
     }

   else if(posType==OP_SELL)
     {
      double stopLossPrice=Low[1]+stopLossPoints;
      if(posStopLoss>stopLossPrice+pip)
        {
         if(stopLossPrice>ask)
           {
            if(stopLossPrice<=ask+stopLevelPoints)
               return (ask + stopLevelPoints);
            else
               return (stopLossPrice);
           }
         else
           {
            return (ask);
           }
        }
     }

   return (posStopLoss);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ManageTrailingStop(double trailingStop)
  {
   double bid=MarketInfo(_Symbol,MODE_BID);
   double ask=MarketInfo(_Symbol,MODE_ASK);

   if(posType==OP_BUY && MathAbs(trailingStop-bid)<_Point)
     {
      ClosePosition();
     }

   else if(posType==OP_SELL && MathAbs(trailingStop-ask)<_Point)
     {
      ClosePosition();
     }

   else if(MathAbs(trailingStop-posStopLoss)>_Point)
     {
      posStopLoss=NormalizeDouble(trailingStop,digits);
      ModifyPosition();
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
datetime Time(int bar)
  {
   return Time[bar];
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Open(int bar)
  {
   return Open[bar];
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double High(int bar)
  {
   return High[bar];
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Low(int bar)
  {
   return Low[bar];
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Close(int bar)
  {
   return Close[bar];
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double GetPipValue(int digit)
  {
   if(digit==4 || digit==5)
      return (0.0001);
   if(digit==2 || digit==3)
      return (0.01);
   if(digit==1)
      return (0.1);
   return (1);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsTradeContextFree()
  {
   if(IsTradeAllowed())
      return (true);

   uint startWait=GetTickCount();
   Print("Trade context is busy! Waiting...");

   while(true)
     {
      if(IsStopped())
         return (false);

      uint diff=GetTickCount()-startWait;
      if(diff>30*1000)
        {
         Print("The waiting limit exceeded!");
         return (false);
        }

      if(IsTradeAllowed())
        {
         RefreshRates();
         return (true);
        }
      Sleep(TRADE_RETRY_WAIT);
     }
   return (true);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsOutOfSession()
  {
   MqlDateTime time0; TimeToStruct(Time[0],time0);
   int weekDay           = time0.day_of_week;
   long timeFromMidnight = Time[0]%86400;
   int periodLength      = PeriodSeconds(_Period);
   bool skipTrade        = false;

   if(weekDay==0)
     {
      if(sessionIgnoreSunday) return true;
      int lastBarFix=sessionCloseAtSessionClose ? periodLength : 0;
      skipTrade=timeFromMidnight<sessionSundayOpen || timeFromMidnight+lastBarFix>sessionSundayClose;
     }
   else if(weekDay<5)
     {
      int lastBarFix=sessionCloseAtSessionClose ? periodLength : 0;
      skipTrade=timeFromMidnight<sessionMondayThursdayOpen || timeFromMidnight+lastBarFix>sessionMondayThursdayClose;
     }
   else
     {
      int lastBarFix=sessionCloseAtFridayClose || sessionCloseAtSessionClose ? periodLength : 0;
      skipTrade=timeFromMidnight<sessionFridayOpen || timeFromMidnight+lastBarFix>sessionFridayClose;
     }

   return (skipTrade);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsForceSessionClose()
  {
   if(!sessionCloseAtFridayClose && !sessionCloseAtSessionClose)
      return (false);

   MqlDateTime time0; TimeToStruct(Time[0],time0);
   int weekDay           = time0.day_of_week;
   long timeFromMidnight = Time[0]%86400;
   int periodLength      = PeriodSeconds(_Period);

   bool forceExit=false;
   if(weekDay==0 && sessionCloseAtSessionClose)
     {
      forceExit=timeFromMidnight+periodLength>sessionSundayClose;
     }
   else if(weekDay<5 && sessionCloseAtSessionClose)
     {
      forceExit=timeFromMidnight+periodLength>sessionMondayThursdayClose;
     }
   else if(weekDay == 5)
     {
      forceExit=timeFromMidnight+periodLength>sessionFridayClose;
     }

   return (forceExit);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
ENUM_INIT_RETCODE ValidateInit()
  {
   return (INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
/*STRATEGY MARKET ICMarkets-Demo02; EURUSD; H1 */
/*STRATEGY CODE {"properties":{"entryLots":0.1,"stopLoss":324,"takeProfit":328,"useStopLoss":true,"useTakeProfit":true,"isTrailingStop":false},"openFilters":[{"name":"Williams' Percent Range","listIndexes":[4,0,0,0,0],"numValues":[31,-24,0,0,0,0]},{"name":"Stochastic","listIndexes":[1,0,0,0,0],"numValues":[3,2,2,20,0,0]},{"name":"Alligator","listIndexes":[3,3,4,0,0],"numValues":[33,17,6,5,4,1]}],"closeFilters":[{"name":"RVI","listIndexes":[6,0,0,0,0],"numValues":[14,0,0,0,0,0]}]} */
