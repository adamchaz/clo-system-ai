VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CashflowClass"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit

Private clsCashflowDict As Dictionary 'Storeas a list of cashflow item by payment dates. Payment dates are stored as long variables
'It only stores paymentdates, interest, schedprin, unschedprin, recoveries, net loss, total


Private Sub Class_Initialize()
    Set clsCashflowDict = New Dictionary
End Sub

Private Sub Class_Terminate()
    Set clsCashflowDict = Nothing
End Sub

Private Sub AddCashflowItem(iCFI As CashFlowItem)
    Dim lCashflowitem As CashFlowItem
    With iCFI
        If clsCashflowDict.Exists(CLng(.PaymentDate)) Then
            clsCashflowDict(.PaymentDate).Interest = clsCashflowDict(.PaymentDate).Interest + .Interest
            clsCashflowDict(.PaymentDate).SchedPrincipal = clsCashflowDict(.PaymentDate).SchedPrincipal + .SchedPrincipal
            clsCashflowDict(.PaymentDate).UnSchedPrincipal = clsCashflowDict(.PaymentDate).UnSchedPrincipal + .UnSchedPrincipal
            clsCashflowDict(.PaymentDate).Recoveries = clsCashflowDict(.PaymentDate).Recoveries + .Recoveries
            clsCashflowDict(.PaymentDate).Total = clsCashflowDict(.PaymentDate).Total + .Total
            'clsCashflowDict(.PaymentDate).Default = clsCashflowDict(.PaymentDate).Default + .Default
            clsCashflowDict(.PaymentDate).Netloss = clsCashflowDict(.PaymentDate).Netloss + .Netloss
        Else
            Set lCashflowitem = New CashFlowItem
            lCashflowitem.PaymentDate = .PaymentDate
            lCashflowitem.Interest = .Interest
            lCashflowitem.SchedPrincipal = .SchedPrincipal
            'lCashflowitem.Default = .Default
            lCashflowitem.Netloss = .Netloss
            lCashflowitem.UnSchedPrincipal = .UnSchedPrincipal
            lCashflowitem.Recoveries = .Recoveries
            lCashflowitem.Total = .Total
            clsCashflowDict.Add CLng(.PaymentDate), lCashflowitem
        End If
    End With
End Sub

Private Sub AddCashflowUDT(iCF As Cashflows)
    Dim lNum As Long
    
    Dim lCFItem As CashFlowItem
    
    For lNum = LBound(iCF.PaymentDate) To UBound(iCF.PaymentDate)
        Set lCFItem = New CashFlowItem
        lCFItem.PaymentDate = iCF.PaymentDate(lNum)
        lCFItem.Interest = iCF.Interest(lNum)
        lCFItem.SchedPrincipal = iCF.Principal(lNum)
        lCFItem.UnSchedPrincipal = iCF.Prepayment(lNum)
        lCFItem.Recoveries = iCF.Recoveries(lNum)
        lCFItem.Total = iCF.Total(lNum)
        Call AddCashflowItem(lCFItem)
    Next lNum
End Sub
Public Sub AddSimpleCashflow(iCF As SimpleCashflow)
    Dim lNum As Long
    
    Dim lCFItem As CashFlowItem
    
    For lNum = 0 To iCF.Count
        
        
        'Set lCFItem = clsCashflowDict(CLng(42205))
        Set lCFItem = New CashFlowItem
        lCFItem.PaymentDate = iCF.PaymentDate(lNum)
        lCFItem.Interest = iCF.Interest(lNum)
        lCFItem.SchedPrincipal = iCF.SchedPrincipal(lNum)
        lCFItem.UnSchedPrincipal = iCF.UnSchedPrincipal(lNum)
        'lCFItem.Default = iCF.Default(lNum)
        lCFItem.Netloss = iCF.Netloss(lNum)
        lCFItem.Recoveries = iCF.Recoveries(lNum)
        lCFItem.Total = iCF.Total(lNum)
        Call AddCashflowItem(lCFItem)
    Next lNum
    Call SortDictionary(clsCashflowDict, True)
End Sub
Public Function GetSimpleCashflow() As SimpleCashflow
    Dim lCount As Long
    Dim lCF As SimpleCashflow
    Dim lKey As Variant
    Dim i As Long
    Set lCF = New SimpleCashflow
    Dim lCashflowitem As CashFlowItem
    If clsCashflowDict.Count > 0 Then
        lCount = clsCashflowDict.Count
        Call SortDictionary(clsCashflowDict, True)
        lKey = clsCashflowDict.Keys
        For i = LBound(lKey) To UBound(lKey)
            Set lCashflowitem = clsCashflowDict(CLng(lKey(i)))
            lCF.PaymentDate(i) = lCashflowitem.PaymentDate
            lCF.SchedPrincipal(i) = lCashflowitem.SchedPrincipal
            lCF.UnSchedPrincipal(i) = lCashflowitem.UnSchedPrincipal
            'lCF.Default(i) = lCashflowitem.Default
            lCF.Interest(i) = lCashflowitem.Interest
            lCF.Recoveries(i) = lCashflowitem.Recoveries
            lCF.Total(i) = lCashflowitem.Total
        Next i
        
    End If
    Set GetSimpleCashflow = lCF
End Function
Public Function GetInterestProceeds(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).Interest
        End If
    Next
    GetInterestProceeds = lNumerator
End Function
Public Function GetPrincipalProceeds(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).SchedPrincipal + clsCashflowDict(CLng(lPaymentDate)).UnSchedPrincipal + clsCashflowDict(CLng(lPaymentDate)).Recoveries
        End If
    Next
    GetPrincipalProceeds = lNumerator
End Function

Public Function GetDefaults(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).Default
        End If
    Next
    GetDefaults = lNumerator
End Function

Public Function GetRecoveries(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).Recoveries
        End If
    Next
    GetRecoveries = lNumerator
End Function
Public Function GetSchedPrincipal(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).SchedPrincipal
        End If
    Next
    GetSchedPrincipal = lNumerator
End Function
Public Function GetUnSchedPrincipal(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).UnSchedPrincipal
        End If
    Next
    GetUnSchedPrincipal = lNumerator
End Function

Public Function GetNetLoss(iBegDate As Date, iEndDate As Date) As Double
    Dim lPaymentDate As Variant
    Dim lNumerator As Double
    
    For Each lPaymentDate In clsCashflowDict.Keys
        If CDate(lPaymentDate) > iBegDate And CDate(lPaymentDate) <= iEndDate Then
            lNumerator = lNumerator + clsCashflowDict(CLng(lPaymentDate)).Netloss
        End If
    Next
    GetNetLoss = lNumerator
End Function

