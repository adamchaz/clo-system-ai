VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Reinvest"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Private clsDealCF As SimpleCashflow
Private clsReinvestInfo As ReinvestInfo
Private clsPeriod As Long
Private clsMoBetPay As Long 'Months between payments
Private clsYieldCurve As YieldCurve
Private clsLastperiod As Long
Public Sub DealSetup(iDealDates() As PaymentDates, ireinvestinfo As ReinvestInfo, iMoBetPay As Long, iYC As YieldCurve)
    Dim i As Long
     Set clsDealCF = New SimpleCashflow
     For i = 1 To UBound(iDealDates)
         clsDealCF.PaymentDate(i) = iDealDates(i).PaymentDate
         clsDealCF.AccBegDate(i) = iDealDates(i).CollBegDate
         clsDealCF.AccEndDate(i) = iDealDates(i).CollEndDate
     Next i
     clsPeriod = 1
    clsReinvestInfo = ireinvestinfo
    clsMoBetPay = iMoBetPay
    Set clsYieldCurve = iYC
End Sub
Public Function PrinBallAllAssets() As Double
    Dim lNumerator As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallAllAssets = clsDealCF.BegBalance(clsPeriod + 1) + clsDealCF.DefaultBal(clsPeriod + 1)
    End If
End Function
Public Function PrinBallExDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallExDefaults = clsDealCF.BegBalance(clsPeriod + 1)
    End If
End Function
Public Function PrinBallDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallDefaults = clsDealCF.DefaultBal(clsPeriod + 1)
    End If
End Function
Public Function MVDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        MVDefaults = clsDealCF.MVDefaultBal(clsPeriod + 1)
    End If
End Function
Public Function UnSchedPrin() As Double
    If clsPeriod <= clsDealCF.Count Then
        UnSchedPrin = clsDealCF.UnSchedPrincipal(clsPeriod)
    End If
End Function

Public Function AddReinvestment(iAmount As Double)
    Dim lBegBal As Double
    Dim lDefaultBal As Double
    Dim lMVDefaultBal As Double
    Dim lEndDefaultBal As Double
    Dim lEndMVDefaultBal As Double
    Dim lDefault As Double
    Dim lMVDefault As Double
    Dim lInterest As Double
    Dim lSchedprin As Double
    Dim lUnschedprin As Double
    Dim lRecoveries As Double
    Dim lNetLoss As Double
    Dim lEndBal As Double
    Dim i As Long
    Dim lNumofPayments As Long
    Dim lPeriodLag As Long
    Dim lCoupon As Double
    Dim lDefaultArr() As Double
    Dim lMVDefaultArr() As Double
    Dim lLIborRate As Double
    Dim lSold As Double
    Dim lPeriodPrepay As Double
    Dim lPeriodDefault As Double
    Dim lPeriodSev As Double
    
    
    lNumofPayments = clsReinvestInfo.Maturity / clsMoBetPay
    lPeriodLag = clsReinvestInfo.Lag / clsMoBetPay
    ReDim lDefaultArr(lNumofPayments)
    ReDim lMVDefaultArr(lNumofPayments)
    
    lBegBal = iAmount / clsReinvestInfo.ReinvestPrice
    For i = 1 To lNumofPayments
        If IsArray(clsReinvestInfo.Prepayment) Then
            If UBound(clsReinvestInfo.Prepayment) < i Then
                lPeriodPrepay = UBound(clsReinvestInfo.Prepayment)
            Else
                lPeriodPrepay = clsReinvestInfo.Prepayment(i)
            End If
        Else
            lPeriodPrepay = clsReinvestInfo.Prepayment
        End If
        If IsArray(clsReinvestInfo.Default) Then
            If UBound(clsReinvestInfo.Default) < i Then
                lPeriodDefault = UBound(clsReinvestInfo.Default)
            Else
                lPeriodDefault = clsReinvestInfo.Default(i)
            End If
        Else
            lPeriodDefault = clsReinvestInfo.Default
        End If
        If IsArray(clsReinvestInfo.Severity) Then
            If UBound(clsReinvestInfo.Severity) < i Then
                lPeriodSev = UBound(clsReinvestInfo.Severity)
            Else
                lPeriodSev = clsReinvestInfo.Severity(i)
            End If
        Else
            lPeriodSev = clsReinvestInfo.Severity
        End If
    
        lDefault = lBegBal * ConvertAnnualRates(lPeriodDefault, clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i))
        lDefaultArr(i) = lDefault
        lMVDefault = lDefault * (1 - lPeriodSev)
        lMVDefaultArr(i) = lMVDefault
        lLIborRate = clsYieldCurve.SpotRate(clsDealCF.PaymentDate(clsPeriod + i - 1), clsMoBetPay)
        If lLIborRate > clsReinvestInfo.Floor Then
            lCoupon = lLIborRate + clsReinvestInfo.Spread
        Else
          lCoupon = clsReinvestInfo.Spread + clsReinvestInfo.Floor
        End If
        lInterest = DateFraction(clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i), US30_360) * lCoupon * (lBegBal - lDefault)
        If i = lNumofPayments Then
            lSchedprin = (lBegBal - lDefault)
        End If
        lUnschedprin = (lBegBal - lDefault - lSchedprin) * ConvertAnnualRates(lPeriodPrepay, clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i))
        If i - lPeriodLag > 0 Then
            lRecoveries = lMVDefaultArr(i - lPeriodLag)
            lNetLoss = lDefaultArr(i - lPeriodLag) - lMVDefaultArr(i - lPeriodLag)
        End If
        'Last period
        lEndBal = lBegBal - lDefault - lSchedprin - lUnschedprin
        lEndDefaultBal = lDefaultBal + lDefault - lRecoveries - lNetLoss
        lEndMVDefaultBal = lMVDefaultBal + lMVDefault - lRecoveries
        If i = lNumofPayments Then
            'last reinvestmentperiod
            lNetLoss = lNetLoss + lEndDefaultBal
            lEndDefaultBal = 0
            lEndMVDefaultBal = 0
            If clsLastperiod < i + clsPeriod Then clsLastperiod = i + clsPeriod
        End If
'        If clsPeriod + i + 1 > clsDealCF.Count Then
'            'liquidate
'            lSold = lEndBal * clsReinvestInfo.Liquidation
'            lSold = lSold + lEndMVDefaultBal
'            lNetLoss = lNetLoss + (lEndDefaultBal - lEndMVDefaultBal)
'            lNetLoss = lNetLoss + (1 - clsReinvestInfo.Liquidation) * lEndBal
'        End If
        'Debug.Assert lNetLoss = 0
        clsDealCF.BegBalance(clsPeriod + i) = clsDealCF.BegBalance(clsPeriod + i) + lBegBal
        clsDealCF.MVDefaultBal(clsPeriod + i) = clsDealCF.MVDefaultBal(clsPeriod + i) + lMVDefaultBal
        clsDealCF.DefaultBal(clsPeriod + i) = clsDealCF.DefaultBal(clsPeriod + i) + lDefaultBal
        clsDealCF.Default(clsPeriod + i) = clsDealCF.Default(clsPeriod + i) + lDefault
        clsDealCF.MVDefault(clsPeriod + i) = clsDealCF.MVDefault(clsPeriod + i) + lMVDefault
        clsDealCF.Interest(clsPeriod + i) = clsDealCF.Interest(clsPeriod + i) + lInterest
        clsDealCF.SchedPrincipal(clsPeriod + i) = clsDealCF.SchedPrincipal(clsPeriod + i) + lSchedprin
        clsDealCF.UnSchedPrincipal(clsPeriod + i) = clsDealCF.UnSchedPrincipal(clsPeriod + i) + lUnschedprin
        clsDealCF.Recoveries(clsPeriod + i) = clsDealCF.Recoveries(clsPeriod + i) + lRecoveries
        clsDealCF.Netloss(clsPeriod + i) = clsDealCF.Netloss(clsPeriod + i) + lNetLoss
        clsDealCF.Sold(clsPeriod + i) = clsDealCF.Sold(clsPeriod + i) + lSold
        lBegBal = lEndBal
        lDefaultBal = lEndDefaultBal
        lMVDefaultBal = lEndMVDefaultBal
        lDefault = 0
        lMVDefault = 0
        lInterest = 0
        lSchedprin = 0
        lUnschedprin = 0
        lRecoveries = 0
        lNetLoss = 0
        lSold = 0
        
        
        If clsPeriod + i + 1 > clsDealCF.Count Or lEndBal = 0 Then
            Exit For
        End If
    Next i
    
End Function


Public Function GetProceeds(iProceeds As String)
    Dim lNumerator As Double

    If iProceeds = "INTEREST" Then
        lNumerator = lNumerator + clsDealCF.Interest(clsPeriod)
    ElseIf iProceeds = "PRINCIPAL" Then
        lNumerator = lNumerator + clsDealCF.SchedPrincipal(clsPeriod) + clsDealCF.UnSchedPrincipal(clsPeriod) + clsDealCF.Recoveries(clsPeriod)
    End If

    GetProceeds = lNumerator
End Function

Public Sub Rollfoward()
    clsPeriod = clsPeriod + 1
End Sub
Public Function GetCollatCF() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    'if clslastperiod=0 then clastperiod=1
    
    ReDim lOutput(0 To clsLastperiod, 10)
    
    lOutput(0, 0) = "Beg Performing Balance"
    lOutput(0, 1) = "Beg Default Balance"
    lOutput(0, 2) = "Beg MV Default Balance"
    lOutput(0, 3) = "Period Default"
    lOutput(0, 4) = "Period MV Default"
    lOutput(0, 5) = "Interest"
    lOutput(0, 6) = "Scheduled Principal"
    lOutput(0, 7) = "Unscheduled Principal"
    lOutput(0, 8) = "Recoveries"
    lOutput(0, 9) = "Net loss"
    lOutput(0, 10) = "Sold"
    
    
    
    For i = 1 To clsLastperiod
        lOutput(i, 0) = clsDealCF.BegBalance(i)
        lOutput(i, 1) = clsDealCF.DefaultBal(i)
        lOutput(i, 2) = clsDealCF.MVDefaultBal(i)
        lOutput(i, 3) = clsDealCF.Default(i)
        lOutput(i, 4) = clsDealCF.MVDefault(i)
        lOutput(i, 5) = clsDealCF.Interest(i)
        lOutput(i, 6) = clsDealCF.SchedPrincipal(i)
        lOutput(i, 7) = clsDealCF.UnSchedPrincipal(i)
        lOutput(i, 8) = clsDealCF.Recoveries(i)
        lOutput(i, 9) = clsDealCF.Netloss(i)
        lOutput(i, 10) = clsDealCF.Sold(i)
    Next i
    
    GetCollatCF = lOutput



End Function

Public Function Liquidate(iLiquidPrice As Double) As Double
    Dim lSold As Double
    Dim i As Long
    Dim lLoss As Double
    Dim lEndBal As Double
    Dim lEndDefaultBal As Double
    Dim lEndMVDefaultBal As Double
    
    
    lEndBal = clsDealCF.BegBalance(clsPeriod) - clsDealCF.Default(clsPeriod) - clsDealCF.UnSchedPrincipal(clsPeriod) - clsDealCF.SchedPrincipal(clsPeriod)
    lEndDefaultBal = clsDealCF.DefaultBal(clsPeriod) + clsDealCF.Default(clsPeriod) - clsDealCF.Recoveries(clsPeriod) - clsDealCF.Netloss(clsPeriod)
    lEndMVDefaultBal = clsDealCF.MVDefaultBal(clsPeriod) + clsDealCF.MVDefault(clsPeriod) - clsDealCF.Recoveries(clsPeriod)
    
    lSold = lEndBal * iLiquidPrice + lEndMVDefaultBal
    lLoss = (1 - iLiquidPrice) * lEndBal + (lEndDefaultBal - lEndMVDefaultBal)
    
    For i = clsPeriod + 1 To clsDealCF.Count
        clsDealCF.BegBalance(i) = 0
        clsDealCF.Default(i) = 0
        clsDealCF.DefaultBal(i) = 0
        clsDealCF.EndBalance(i) = 0
        clsDealCF.Interest(i) = 0
        clsDealCF.MVDefault(i) = 0
        clsDealCF.MVDefaultBal(i) = 0
        clsDealCF.Netloss(i) = 0
        clsDealCF.Recoveries(i) = 0
        clsDealCF.SchedPrincipal(i) = 0
        clsDealCF.Total(i) = 0
        clsDealCF.UnSchedPrincipal(i) = 0
    Next i
    
    clsDealCF.Netloss(clsPeriod) = clsDealCF.Netloss(clsPeriod) + lLoss
    clsDealCF.Sold(clsPeriod) = clsDealCF.Sold(clsPeriod) + lSold
    Liquidate = lSold
    clsLastperiod = clsPeriod
End Function
