VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Liability"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit

Private clsName As String
Private clsOrigBalance As Double
Private clsCurrBalance As Double
Private clsDefBalance As Double
Private clsPikable As Boolean
Private clsLiborSpread As Double
Private clsDayCount As DayCount
Private EquityTranche As Boolean
Private clsCpnType As String



'Data storge
Private clsCoupon() As Double
Private clsPaymentdate() As Date
Private clsBegBalance() As Double
Private clsIntAccrued() As Double
Private clsIntPaid() As Double
Private clsPrinPaid() As Double
Private clsEndBalance() As Double
Private clsDefBegBalance() As Double
Private clsDefIntAccrued() As Double
Private clsDefIntPaid() As Double
Private clsDefPrinPaid() As Double
Private clsDefEndBalance() As Double


Private clsPeriod As Long
Private clsLastPeriodCalc As Long

'RiskMeasures
Private clsDM As Double
Private clsPrice As Double
Private clsAnalysisDate As Date
Private clsYieldCurve As YieldCurve
Private clsYieldWPrice As Double
Private clsDMWPrice As Double
Private clsPriceWDM As Double
Private clsWAL As Double
Private clsMACDuration As Double
Private clsModDuration As Double

Public Property Get Name() As String
    Name = clsName
End Property
Public Property Get IsEquity() As Boolean
    IsEquity = EquityTranche
End Property

Public Function Output() As Variant
    Dim i As Long
    Dim lOutput As Variant
    Dim lrowOffsett As Long
    Dim lcolumnoffset As Long
    

    
    If EquityTranche Then
        If clsPeriod <= 10 Then clsPeriod = 10
        ReDim lOutput(0 To clsPeriod - 1, 3 + 2)
        lOutput(0, 0) = "Beg Balance"
        lOutput(0, 1) = "Prin Paid"
        lOutput(0, 2) = "Int Paid"
        lOutput(0, 3) = "Current Percent"
        
        For i = 1 To clsPeriod - 1
            lOutput(i, 0) = clsBegBalance(i)
            lOutput(i, 1) = clsPrinPaid(i)
            lOutput(i, 2) = clsIntPaid(i)
            lOutput(i, 3) = Format((clsPrinPaid(i) + clsIntPaid(i)) / clsOrigBalance, "0.0000%")
        Next i
        lcolumnoffset = 3
    Else
        Dim lNumRows As Long
        If clsLastPeriodCalc <= 10 Then
            lNumRows = 10
        Else
            lNumRows = clsLastPeriodCalc
        End If
        If clsPikable Then
            ReDim lOutput(0 To lNumRows, 10 + 2)
            lcolumnoffset = 10
        Else
            ReDim lOutput(0 To lNumRows, 8 + 2)
            lcolumnoffset = 8
        End If
        lOutput(0, lrowOffsett) = "Coupon"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "Beg Balance"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "Int Accrued"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "Int Paid"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "Prin Paid"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "End Balance"
        lrowOffsett = lrowOffsett + 1
        lOutput(0, lrowOffsett) = "Def Beg Balance"
        lrowOffsett = lrowOffsett + 1
        If clsPikable = True Then
            lOutput(0, lrowOffsett) = "Def Int Accrued"
            lrowOffsett = lrowOffsett + 1
            lOutput(0, lrowOffsett) = "Def Int Paid"
            lrowOffsett = lrowOffsett + 1
           End If
        lOutput(0, lrowOffsett) = "Def Prin Paid"
        lrowOffsett = lrowOffsett + 1
     
        lOutput(0, lrowOffsett) = "Def End Balance"
        lrowOffsett = lrowOffsett + 1
        For i = 1 To clsLastPeriodCalc
            lrowOffsett = 0
            lOutput(i, lrowOffsett) = Format(clsCoupon(i), "0.00000%")
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsBegBalance(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsIntAccrued(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsIntPaid(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsPrinPaid(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsEndBalance(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsDefBegBalance(i)
            lrowOffsett = lrowOffsett + 1
            If clsPikable = True Then
                lOutput(i, lrowOffsett) = clsDefIntAccrued(i)
                lrowOffsett = lrowOffsett + 1
                lOutput(i, lrowOffsett) = clsDefIntPaid(i)
                lrowOffsett = lrowOffsett + 1
            End If
            lOutput(i, lrowOffsett) = clsDefPrinPaid(i)
            lrowOffsett = lrowOffsett + 1
            lOutput(i, lrowOffsett) = clsDefEndBalance(i)
            lrowOffsett = lrowOffsett + 1
        Next i
    End If
    lrowOffsett = 0
    lOutput(lrowOffsett, lcolumnoffset + 1) = "Risk Measures"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "User Price"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "User DM"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "Yield Given Price"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "DM Given Price"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "Price Given DM"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "WAL"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "Mac Duration"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 1) = "Mod Duration"
    lrowOffsett = lrowOffsett + 1
    
    lrowOffsett = 0
    lOutput(lrowOffsett, lcolumnoffset + 2) = "Risk Measures"
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsPrice, "0.0000%")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsDM, "0.0000%")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsYieldWPrice, "0.0000%")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsDMWPrice, "0.0000%")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsPriceWDM, "0.0000%")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsWAL, "0.000")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsMACDuration, "0.000")
    lrowOffsett = lrowOffsett + 1
    lOutput(lrowOffsett, lcolumnoffset + 2) = Format(clsModDuration, "0.000")
    lrowOffsett = lrowOffsett + 1
    
    Output = lOutput
End Function
Public Function CurDistrPct() As Double
    Dim lInt As Double
    Dim lPrin As Double
    
    CurDistrPct = (clsPrinPaid(clsPeriod) + clsIntPaid(clsPeriod)) / clsOrigBalance
    
End Function

Public Sub Calc(iLIBOR As Double, iPrevPay As Date, iNextPay As Date)
    Dim lCoupon As Double
    If EquityTranche = False Then
        If clsCpnType = "Fixed" Then
            lCoupon = clsLiborSpread
        Else
            lCoupon = iLIBOR + clsLiborSpread
        End If
        clsCoupon(clsPeriod) = lCoupon
        clsIntAccrued(clsPeriod) = clsBegBalance(clsPeriod) * DateFraction(iPrevPay, iNextPay, clsDayCount) * lCoupon
        If clsPikable Then
            clsDefIntAccrued(clsPeriod) = clsDefBegBalance(clsPeriod) * DateFraction(iPrevPay, iNextPay, clsDayCount) * lCoupon
        End If
        If clsBegBalance(clsPeriod) > 0 Then
            clsLastPeriodCalc = clsPeriod
        End If
    End If
End Sub

Public Sub Setup(iName As String, iOrgBal As Double, iCurrBal As Double, iDefBal As Double, iPIK As Boolean, iSpead As Double, iCpnType As String, iDM As Double, idaycount As DayCount, IsEquity As Boolean, iPrice As Double)
    clsName = iName
    clsOrigBalance = iOrgBal
    clsCurrBalance = iCurrBal
    clsDefBalance = iDefBal
    clsPikable = iPIK
    clsLiborSpread = iSpead
    clsDayCount = idaycount
    EquityTranche = IsEquity
    clsDM = iDM
    clsPrice = iPrice
    clsCpnType = iCpnType

End Sub
Public Function CurrBal() As Double  'This will include the PikBalance
    CurrBal = clsBegBalance(clsPeriod)
    If clsPikable Then
        CurrBal = CurrBal + clsDefBegBalance(clsPeriod) - clsDefPrinPaid(clsPeriod)
    End If
End Function
Public Function PIKBal() As Double
    If clsPikable Then
        PIKBal = clsDefBegBalance(clsPeriod)
    End If
End Function
Public Function IntDue() As Double
    IntDue = clsIntAccrued(clsPeriod) - clsIntPaid(clsPeriod)
    If clsPikable Then
        IntDue = IntDue + clsDefIntAccrued(clsPeriod) - clsDefIntPaid(clsPeriod)
    End If

End Function
Public Sub DealSetup(iPaymentDate() As PaymentDates, ianalysisDate As Date, iYC As YieldCurve)
    Dim i As Long
    Dim lNumofPayments As Long
    
    lNumofPayments = UBound(iPaymentDate)
    
    ReDim clsBegBalance(lNumofPayments)
    ReDim clsIntAccrued(lNumofPayments)
    ReDim clsIntPaid(lNumofPayments)
    ReDim clsPrinPaid(lNumofPayments)
    ReDim clsEndBalance(lNumofPayments)
    ReDim clsDefBegBalance(lNumofPayments)
    ReDim clsDefIntAccrued(lNumofPayments)
    ReDim clsDefIntPaid(lNumofPayments)
    ReDim clsDefPrinPaid(lNumofPayments)
    ReDim clsDefEndBalance(lNumofPayments)
    ReDim clsCoupon(lNumofPayments)
    ReDim clsPaymentdate(lNumofPayments)
    
    clsPeriod = 1
    clsBegBalance(1) = clsCurrBalance
    clsDefBegBalance(1) = clsDefBalance
    For i = 1 To lNumofPayments
        clsPaymentdate(i) = iPaymentDate(i).PaymentDate
    Next
    clsAnalysisDate = ianalysisDate
    Set clsYieldCurve = iYC

End Sub



Public Sub PayInterest(iAmount As Double)
    Dim lIntDue As Double
    Dim lDefIntDue As Double
    Dim lDefBalDue As Double
    'Dim ldefbal As Double
    
    If EquityTranche Then
        clsIntPaid(clsPeriod) = clsIntPaid(clsPeriod) + iAmount
        iAmount = 0
        clsLastPeriodCalc = clsPeriod
    Else
        lIntDue = clsIntAccrued(clsPeriod) - clsIntPaid(clsPeriod)
        lDefIntDue = clsDefIntAccrued(clsPeriod) - clsDefIntPaid(clsPeriod)
        lDefBalDue = clsDefBegBalance(clsPeriod) - clsDefPrinPaid(clsPeriod)
        
        If iAmount > lIntDue Then
            clsIntPaid(clsPeriod) = clsIntPaid(clsPeriod) + lIntDue
            iAmount = iAmount - lIntDue
        Else
            clsIntPaid(clsPeriod) = clsIntPaid(clsPeriod) + iAmount
            iAmount = 0
        End If
        
        If iAmount > lDefIntDue Then
            clsDefIntPaid(clsPeriod) = clsDefIntPaid(clsPeriod) + lDefIntDue
            iAmount = iAmount - lDefIntDue
        Else
            clsDefIntPaid(clsPeriod) = clsDefIntPaid(clsPeriod) + iAmount
            iAmount = 0
        End If
'        If clsPikable = False Then 'Don't Pay PIK Interest
'            If iAmount > lDefBalDue Then
'                clsDefPrinPaid(clsPeriod) = clsDefPrinPaid(clsPeriod) + lDefBalDue
'                iAmount = iAmount - lDefBalDue
'            Else
'                clsDefPrinPaid(clsPeriod) = clsDefPrinPaid(clsPeriod) + iAmount
'                iAmount = 0
'            End If
'        End If
    End If
    
    
    
End Sub

Public Sub PayPrincipal(iAmount As Double)
    Dim lPrincipalDue As Double
    
    lPrincipalDue = clsBegBalance(clsPeriod) - clsPrinPaid(clsPeriod)
    If EquityTranche Then
        clsPrinPaid(clsPeriod) = clsPrinPaid(clsPeriod) + iAmount
        iAmount = 0
        clsLastPeriodCalc = clsPeriod
    Else
        If iAmount > lPrincipalDue Then
            clsPrinPaid(clsPeriod) = clsPrinPaid(clsPeriod) + lPrincipalDue
            iAmount = iAmount - lPrincipalDue
        Else
            clsPrinPaid(clsPeriod) = clsPrinPaid(clsPeriod) + iAmount
            iAmount = 0
        End If
    End If

End Sub
Public Sub PayPIKInterest(iAmount)
    Dim lDefBalDue As Double
    lDefBalDue = clsDefBegBalance(clsPeriod) - clsDefPrinPaid(clsPeriod) + clsDefIntAccrued(clsPeriod) - clsDefIntPaid(clsPeriod)
    If iAmount > lDefBalDue Then
        clsDefPrinPaid(clsPeriod) = clsDefPrinPaid(clsPeriod) + lDefBalDue
        iAmount = iAmount - lDefBalDue
    Else
        clsDefPrinPaid(clsPeriod) = clsDefPrinPaid(clsPeriod) + iAmount
        iAmount = 0
    End If
End Sub

Public Sub Rollfoward()
    If EquityTranche = False Then
        clsDefEndBalance(clsPeriod) = clsDefBegBalance(clsPeriod) + clsDefIntAccrued(clsPeriod) - clsDefIntPaid(clsPeriod) - clsDefPrinPaid(clsPeriod)
        clsEndBalance(clsPeriod) = clsBegBalance(clsPeriod) - clsPrinPaid(clsPeriod)
        If clsPeriod + 1 <= UBound(clsEndBalance) Then
            clsDefBegBalance(clsPeriod + 1) = clsDefEndBalance(clsPeriod) + clsIntAccrued(clsPeriod) - clsIntPaid(clsPeriod)
            clsBegBalance(clsPeriod + 1) = clsEndBalance(clsPeriod)
        End If
    Else
        If clsPeriod + 1 <= UBound(clsEndBalance) Then
            clsBegBalance(clsPeriod + 1) = clsBegBalance(clsPeriod)
        End If
    End If
    clsPeriod = clsPeriod + 1
End Sub

Public Sub CalcRiskMeasures(iYC As YieldCurve, iPaymentDate() As PaymentDates, ianalysisDate As Date)
    Dim lTotalCF() As Double
    Dim lRates() As Double
    Dim lDates() As Date
    Dim i As Long
    Dim lUserPrice As Double
    Dim lUserDM As Double
    
    Dim lCalcPrice As Double
    Dim lWAL As Double
    Dim lspread As Double
    Dim lYield As Double
    Dim lTotalPrinPaid As Double
    Dim lWeightedPrin As Double
    Dim lMacDuration As Double
    Dim lPartialPeriod As Double

    
    ReDim lTotalCF(clsLastPeriodCalc)
    ReDim lRates(clsLastPeriodCalc)
    ReDim lDates(clsLastPeriodCalc)
    lDates(0) = ianalysisDate
    If clsCurrBalance = 0 Then
        Exit Sub
    End If
    For i = 1 To clsLastPeriodCalc
        lTotalCF(i) = clsIntPaid(i) + clsPrinPaid(i) + clsDefIntPaid(i) + clsDefPrinPaid(i)
        'lRates(i) = iYC.SpotRate(iAnalysisDate, DateDiff("M", iAnalysisDate, iPaymentDate(i).PaymentDate))
        lRates(i) = iYC.ZeroRate(ianalysisDate, iPaymentDate(i).PaymentDate)
        lDates(i) = clsPaymentdate(i)
        lWeightedPrin = lWeightedPrin + (clsPaymentdate(i) - clsAnalysisDate) * clsPrinPaid(i)
        lTotalPrinPaid = lTotalPrinPaid + clsPrinPaid(i)
    Next i
    lCalcPrice = CalcPVwSpread(lTotalCF, lDates, lRates, ianalysisDate, clsDM, clsDayCount, 4)
    lCalcPrice = lCalcPrice / clsBegBalance(1)
    lspread = CalcZSpread(clsPrice * clsBegBalance(1), lTotalCF, lDates, lRates, clsDayCount, 4)
    lYield = Math.CalcYield(clsPrice * clsBegBalance(1), lTotalCF, lDates, clsDayCount, 4)
    lWeightedPrin = lWeightedPrin + (clsBegBalance(1) - lTotalPrinPaid) * (clsPaymentdate(clsLastPeriodCalc) - clsAnalysisDate)
    lWAL = lWeightedPrin / clsOrigBalance / 365
    For i = 1 To clsLastPeriodCalc
        lPartialPeriod = (clsPaymentdate(i) - clsAnalysisDate) / 365
        lMacDuration = lMacDuration + (lPartialPeriod / (clsPrice * clsBegBalance(1))) * (lTotalCF(i) / ((1 + lYield / 4) ^ (lPartialPeriod * 4)))
    Next i
    clsYieldWPrice = lYield
    clsDMWPrice = lspread
    clsPriceWDM = lCalcPrice
    clsWAL = lWAL
    clsMACDuration = lMacDuration
    If lYield > 0 Then clsModDuration = lMacDuration / (1 + lYield / 4)
    
End Sub
Public Function InputPrice() As Double
    InputPrice = clsPrice
End Function
Public Function InputDM() As Double
    InputDM = clsDM
End Function
Public Function CalcYield() As Double
    CalcYield = clsYieldWPrice
End Function
Public Function CalcDM() As Double
    CalcDM = clsDMWPrice
End Function
Public Function CalcPrice() As Double
    CalcPrice = clsPriceWDM
End Function
Public Function CalcWAL() As Double
    CalcWAL = clsWAL
End Function
Public Function CalcMac() As Double
    CalcMac = clsMACDuration
End Function
Public Function CalcMod() As Double
    CalcMod = clsModDuration
End Function
Public Function TotalInterest() As Double
    Dim lTotal As Double
    Dim i As Long
    For i = LBound(clsIntPaid) To UBound(clsIntPaid)
        lTotal = lTotal + clsIntPaid(i) + clsDefIntPaid(i) + clsDefPrinPaid(i)
    Next i
    TotalInterest = lTotal
End Function
Public Function TotalPrincipal() As Double
    Dim lTotal As Double
    Dim i As Long
    For i = LBound(clsIntPaid) To UBound(clsIntPaid)
        lTotal = lTotal + clsPrinPaid(i)
    Next i
    TotalPrincipal = lTotal
End Function

Private Sub Class_Initialize()

End Sub
