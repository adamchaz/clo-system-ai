VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ICTrigger"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Private clsName As String
Private clsTrigger As Double


Private clsResult() As Double
Private clsThreshold() As Double
Private clsPassFail() As Boolean


'Data storage
Private clsNumerator() As Double
Private clsDenominator() As Double
Private clsLiabBal() As Double
Private clsPriorCure() As Double
Private clsCureAmt() As Double
Private clsCureAmtPaid() As Double
Private clsPeriod As Long
Private clsLastPeriodCalc As Long
Public Property Get Name() As String
    Name = clsName
End Property

Public Sub Setup(iName As String, iThresh As Double)
    clsName = iName
    clsTrigger = iThresh
End Sub

Public Function Output() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastPeriodCalc, 8)
    lOutput(0, 0) = "Numerator"
    lOutput(0, 1) = "Denominator"
    lOutput(0, 2) = "Liability Balance"
    lOutput(0, 3) = "Results"
    lOutput(0, 4) = "Threshold"
    lOutput(0, 5) = "Pass/Fail"
    lOutput(0, 6) = "Prior Cure Payments"
    lOutput(0, 7) = "Cure Amount"
    lOutput(0, 8) = "Cure Paid"
    
    
    For i = 1 To clsLastPeriodCalc
        lOutput(i, 0) = clsNumerator(i)
        lOutput(i, 1) = clsDenominator(i)
        lOutput(i, 2) = clsLiabBal(i)
        lOutput(i, 3) = Format(clsResult(i), "0.000%")
        lOutput(i, 4) = Format(clsTrigger, "0.000%")
        lOutput(i, 5) = clsPassFail(i)
        lOutput(i, 6) = clsPriorCure(i)
        lOutput(i, 7) = clsCureAmt(i)
        lOutput(i, 8) = clsCureAmtPaid(i)
    Next i
    
    Output = lOutput
End Function
Public Sub DealSetup(iNumofPayments As Long)
    ReDim clsResult(iNumofPayments)
    ReDim clsThreshold(iNumofPayments)
    ReDim clsPassFail(iNumofPayments)
    ReDim clsNumerator(iNumofPayments)
    ReDim clsDenominator(iNumofPayments)
    ReDim clsPriorCure(iNumofPayments)
    ReDim clsCureAmt(iNumofPayments)
    ReDim clsLiabBal(iNumofPayments)
    ReDim clsCureAmtPaid(iNumofPayments)
    clsPeriod = 1
End Sub


Public Sub Calc(iNum As Double, iDeno As Double, iLiabBal As Double)
    Dim lResults As Double
   If iDeno > 0 Then
        clsNumerator(clsPeriod) = iNum
        clsDenominator(clsPeriod) = iDeno
        clsLiabBal(clsPeriod) = iLiabBal
        lResults = iNum / iDeno
        clsResult(clsPeriod) = lResults
        If lResults > clsTrigger Then
            clsPassFail(clsPeriod) = True
        Else
            clsPassFail(clsPeriod) = False
            clsCureAmt(clsPeriod) = (1 - clsResult(clsPeriod) / clsTrigger) * clsLiabBal(clsPeriod)
        End If
        clsLastPeriodCalc = clsPeriod
    Else
       clsPassFail(clsPeriod) = True
    End If

End Sub
Public Function CureAmount() As Double
    CureAmount = clsCureAmt(clsPeriod) - clsPriorCure(clsPeriod) - clsCureAmtPaid(clsPeriod)
End Function
Public Function PassFail() As Boolean
    PassFail = clsPassFail(clsPeriod)
End Function

Public Sub AddPriorCure(iAmount As Double)
    'Only take the amount you need
    Dim lCureDue As Double
    
    lCureDue = clsCureAmt(clsPeriod) - clsPriorCure(clsPeriod) - clsCureAmtPaid(clsPeriod)
    If lCureDue > iAmount Then
        clsPriorCure(clsPeriod) = clsPriorCure(clsPeriod) + iAmount
    Else
        clsPriorCure(clsPeriod) = clsPriorCure(clsPeriod) + lCureDue
    End If
    

End Sub


Public Sub PayCure(iAmount As Double)
    Dim lCureDue As Double
    
    lCureDue = clsCureAmt(clsPeriod) - clsPriorCure(clsPeriod) - clsCureAmtPaid(clsPeriod)
    If iAmount > lCureDue Then
        clsCureAmtPaid(clsPeriod) = clsCureAmtPaid(clsPeriod) + lCureDue
        iAmount = iAmount - lCureDue
    Else
        clsCureAmtPaid(clsPeriod) = clsCureAmtPaid(clsPeriod) + iAmount
        iAmount = 0
    End If

End Sub

Public Sub Rollfoward()

    clsPeriod = clsPeriod + 1
End Sub

