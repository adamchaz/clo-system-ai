VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "SimpleCashflow"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit
'The assumption is going be that paymentdates go up


Private clsPaymentdate() As Date
Private clsPurchase() As Double
Private clsSold() As Double
Private clsAccBegDate() As Date
Private clsAccEndDate() As Date
Private clsBegBal() As Double
Private clsDefaultBal() As Double
Private clsMVDefaultBal() As Double
Private clsDefault() As Double
Private clsMVDefault() As Double
Private clsInt() As Double
Private clsSchedPrin() As Double
Private ClsUnschedPrin() As Double
Private clsEndBal() As Double
Private clsRecoveries() As Double
Private clsNetLoss() As Double
Private clsTotal() As Double
Private clsLargestIndex As Long
Public Property Get MVDefaultBal(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    MVDefaultBal = clsMVDefaultBal(iIndex)
End Property
Public Property Let MVDefaultBal(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsMVDefaultBal(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get DefaultBal(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    DefaultBal = clsDefaultBal(iIndex)
End Property
Public Property Let DefaultBal(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsDefaultBal(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property



Public Property Get PaymentDate(iIndex As Long) As Date
    If iIndex > clsLargestIndex Then Exit Property
    PaymentDate = clsPaymentdate(iIndex)
End Property
Public Property Let PaymentDate(iIndex As Long, iDate As Date)
    Call Redimension(iIndex)
    clsPaymentdate(iIndex) = iDate
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get AccBegDate(iIndex As Long) As Date
    If iIndex > clsLargestIndex Then Exit Property
    AccBegDate = clsAccBegDate(iIndex)
End Property
Public Property Let AccBegDate(iIndex As Long, iDate As Date)
    Call Redimension(iIndex)
    clsAccBegDate(iIndex) = iDate
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get AccEndDate(iIndex As Long) As Date
    If iIndex > clsLargestIndex Then Exit Property
    AccEndDate = clsAccEndDate(iIndex)
    
End Property
Public Property Let AccEndDate(iIndex As Long, iDate As Date)
    Call Redimension(iIndex)
    clsAccEndDate(iIndex) = iDate
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get BegBalance(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    BegBalance = clsBegBal(iIndex)
End Property
Public Property Let BegBalance(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsBegBal(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get Default(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Default = clsDefault(iIndex)
End Property
Public Property Let Default(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsDefault(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get MVDefault(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    MVDefault = clsMVDefault(iIndex)
End Property
Public Property Let MVDefault(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsMVDefault(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get Interest(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Interest = clsInt(iIndex)
End Property
Public Property Let Interest(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsInt(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get SchedPrincipal(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    SchedPrincipal = clsSchedPrin(iIndex)
End Property
Public Property Let SchedPrincipal(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsSchedPrin(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get UnSchedPrincipal(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    UnSchedPrincipal = ClsUnschedPrin(iIndex)
End Property
Public Property Let UnSchedPrincipal(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    ClsUnschedPrin(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get Recoveries(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Recoveries = clsRecoveries(iIndex)
End Property
Public Property Let Recoveries(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsRecoveries(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get EndBalance(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    EndBalance = clsEndBal(iIndex)
End Property
Public Property Let EndBalance(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsEndBal(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get Netloss(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Netloss = clsNetLoss(iIndex)
End Property
Public Property Let Netloss(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsNetLoss(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property

Public Property Get Total(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Total = clsTotal(iIndex)
End Property
Public Property Let Total(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsTotal(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Property Get Sold(iIndex As Long) As Double
    If iIndex > clsLargestIndex Then Exit Property
    Sold = clsSold(iIndex)
End Property
Public Property Let Sold(iIndex As Long, iValue As Double)
    Call Redimension(iIndex)
    clsSold(iIndex) = iValue
    If iIndex > clsLargestIndex Then clsLargestIndex = iIndex
End Property
Public Function Count() As Long
    Count = clsLargestIndex
End Function
Private Sub Redimension(iIndex As Long)
    If iIndex > UBound(clsPaymentdate) Then
        ReDim Preserve clsPaymentdate(iIndex + 10)
        ReDim Preserve clsAccBegDate(iIndex + 10)
        ReDim Preserve clsAccEndDate(iIndex + 10)
        ReDim Preserve clsBegBal(iIndex + 10)
        ReDim Preserve clsDefault(iIndex + 10)
        ReDim Preserve clsInt(iIndex + 10)
        ReDim Preserve clsSchedPrin(iIndex + 10)
        ReDim Preserve ClsUnschedPrin(iIndex + 10)
        ReDim Preserve clsEndBal(iIndex + 10)
        ReDim Preserve clsRecoveries(iIndex + 10)
        ReDim Preserve clsNetLoss(iIndex + 10)
        ReDim Preserve clsTotal(iIndex + 10)
        ReDim Preserve clsDefaultBal(iIndex + 10)
        ReDim Preserve clsMVDefaultBal(iIndex + 10)
        ReDim Preserve clsMVDefault(iIndex + 10)
        ReDim Preserve clsPurchase(iIndex + 10)
        ReDim Preserve clsSold(iIndex + 10)
    End If

End Sub

Private Sub Class_Initialize()
    ReDim clsPaymentdate(0)
    ReDim clsAccBegDate(0)
    ReDim clsAccEndDate(0)
    ReDim clsBegBal(0)
    ReDim clsDefault(0)
    ReDim clsMVDefault(0)
    ReDim clsInt(0)
    ReDim clsSchedPrin(0)
    ReDim ClsUnschedPrin(0)
    ReDim clsEndBal(0)
    ReDim clsRecoveries(0)
    ReDim clsNetLoss(0)
    ReDim clsTotal(0)
    ReDim clsDefaultBal(0)
    ReDim clsMVDefaultBal(0)
    ReDim clsPurchase(0)
    ReDim clsSold(0)
End Sub





Public Function GetDefaults(iBegDate As Date, iEndDate As Date, Optional isfirstperiod As Boolean) As Double
    'Defaults happen at the beginning of the period. So any default happens at the beginning of an accrual period not on a paymentdate
    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If isfirstperiod And clsAccBegDate(i) <= iEndDate Then
            lNumerator = clsDefault(i) + lNumerator
        ElseIf clsAccBegDate(i) > iBegDate And clsAccBegDate(i) <= iEndDate Then
            lNumerator = clsDefault(i) + lNumerator
        End If
    Next i
    
    GetDefaults = lNumerator
End Function

Public Function GetMVDefaults(iBegDate As Date, iEndDate As Date, Optional isfirstperiod As Boolean) As Double
    'Defaults happen at the beginning of the period. So any default happens at the beginning of an accrual period not on a paymentdate
    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If isfirstperiod And clsAccBegDate(i) <= iEndDate Then
            lNumerator = clsMVDefault(i) + lNumerator
        ElseIf clsAccBegDate(i) > iBegDate And clsAccBegDate(i) <= iEndDate Then
            lNumerator = clsMVDefault(i) + lNumerator
        End If
    Next i
    
    GetMVDefaults = lNumerator
End Function
Public Function GetInterest(iBegDate As Date, iEndDate As Date) As Double

    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If clsPaymentdate(i) > iBegDate And clsPaymentdate(i) <= iEndDate Then
            lNumerator = clsInt(i) + lNumerator
        End If
    Next i
    
    GetInterest = lNumerator
End Function
Public Function GetUnschedPrin(iBegDate As Date, iEndDate As Date) As Double

    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If clsPaymentdate(i) > iBegDate And clsPaymentdate(i) <= iEndDate Then
            lNumerator = ClsUnschedPrin(i) + lNumerator
        End If
    Next i
    
    GetUnschedPrin = lNumerator
End Function
Public Function GetSchedPrin(iBegDate As Date, iEndDate As Date) As Double

    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If clsPaymentdate(i) > iBegDate And clsPaymentdate(i) <= iEndDate Then
            lNumerator = clsSchedPrin(i) + lNumerator
        End If
    Next i
    
    GetSchedPrin = lNumerator
End Function

Public Function GetRecoveries(iBegDate As Date, iEndDate As Date) As Double

    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If clsPaymentdate(i) > iBegDate And clsPaymentdate(i) <= iEndDate Then
            lNumerator = clsRecoveries(i) + lNumerator
        End If
    Next i
    
    GetRecoveries = lNumerator
End Function
Public Function GetNetLoss(iBegDate As Date, iEndDate As Date) As Double

    Dim i As Long
    Dim lNumerator As Double
    
    For i = LBound(clsPaymentdate) To UBound(clsPaymentdate)
        If clsPaymentdate(i) > iBegDate And clsPaymentdate(i) <= iEndDate Then
            lNumerator = clsNetLoss(i) + lNumerator
        End If
    Next i
    
    GetNetLoss = lNumerator
End Function

Public Function GetBegBlance(iDate As Date) As Double
    Dim i As Long
    Dim lBalance As Double
    If iDate > clsPaymentdate(clsLargestIndex) Then
        lBalance = 0
    ElseIf iDate < clsPaymentdate(0) Then
        lBalance = clsBegBal(0)
    Else
        For i = clsLargestIndex To LBound(clsPaymentdate) Step -1
            If clsPaymentdate(i) = iDate Then
                lBalance = clsBegBal(i) - clsDefault(i) - clsSchedPrin(i) - ClsUnschedPrin(i)
                Exit For
            ElseIf clsPaymentdate(i) < iDate Then
                lBalance = clsBegBal(i + 1)
                Exit For
            End If
        Next i
    End If
    GetBegBlance = lBalance
End Function
Public Function CalcZSpread(iYC As YieldCurve, iPrice As Double) As Double
    Dim lspread As Double
    Dim lTotalCFs() As Double
    Dim lDates() As Date
    Dim lRates() As Double
    Dim i As Long
    'lSpread = CalcZSpread(clsPrice * clsBegBalance(1), lTotalCF, lDates, lRates, clsDayCount, 4)
    Dim lAnalysisDate As Date
    
    lAnalysisDate = clsAccBegDate(0)
    ReDim lTotalCFs(clsLargestIndex + 1)
    ReDim lDates(clsLargestIndex + 1)
    ReDim lRates(clsLargestIndex + 1)
    lDates(0) = lAnalysisDate
    For i = 0 To clsLargestIndex
        lTotalCFs(i + 1) = clsTotal(i)
        lDates(i + 1) = clsPaymentdate(i)
        lRates(i + 1) = iYC.ZeroRate(lAnalysisDate, clsPaymentdate(i))
        
    Next i
    lspread = Math.CalcZSpread(iPrice * clsBegBal(0), lTotalCFs, lDates, lRates, actual_360, 4)
    CalcZSpread = lspread
End Function
'Public Function CalcYield(ianalysisDate, iPrice As Double) As Double
'    Dim lspread As Double
'    Dim lTotalCFs() As Double
'    Dim lDates() As Date
'    Dim lRates() As Double
'    Dim i As Long
'    Dim lAnalysisDate As Date
'
'    lAnalysisDate = clsAccBegDate(0)
'    ReDim lTotalCFs(clsLargestIndex + 1)
'    ReDim lDates(clsLargestIndex + 1)
'    ReDim lRates(clsLargestIndex + 1)
'    lDates(0) = lAnalysisDate
'    For i = 0 To clsLargestIndex
'        lTotalCFs(i + 1) = clsTotal(i)
'        lDates(i + 1) = clsPaymentdate(i)
'    Next i
'    lYield = Math.CalcYield(iPrice * clsBegBal, lTotalCFs, lDates, actual_360, 4)
'    CalcYield = lspread
'End Function
