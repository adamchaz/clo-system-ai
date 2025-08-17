VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "OCTrigger"
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
Private clsIntCureAmt() As Double
Private clsIntCurePaid() As Double
Private clsPriorIntCure() As Double
Private clsPriorPrinCure() As Double
Private clsPrinCureAmt() As Double
Private clsPrinCurePaid() As Double
Private clsLastPeriodCalc As Long
Private clsPeriod As Long
Public Property Get Name() As String
    Name = clsName
End Property


Public Function Output() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastPeriodCalc, 10)
    lOutput(0, 0) = "Numerator"
    lOutput(0, 1) = "Denominator"
    lOutput(0, 2) = "Result"
    lOutput(0, 3) = "Threshold"
    lOutput(0, 4) = "Pass/Fail"
    lOutput(0, 5) = "Prior Int Cure"
    lOutput(0, 6) = "Prior Prin Cure"
    lOutput(0, 7) = "Int Cure Amount"
    lOutput(0, 8) = "Tnt Cure Paid"
    lOutput(0, 9) = "Prin Cure Amount"
    lOutput(0, 10) = "Prin Cure Paid"
    
    
    For i = 1 To clsLastPeriodCalc
        lOutput(i, 0) = clsNumerator(i)
        lOutput(i, 1) = clsDenominator(i)
        lOutput(i, 2) = Format(clsResult(i), "0.000%")
        lOutput(i, 3) = Format(clsTrigger, "0.000%")
        lOutput(i, 4) = clsPassFail(i)
        lOutput(i, 5) = clsPriorIntCure(i)
        lOutput(i, 6) = clsPriorPrinCure(i)
        lOutput(i, 7) = clsIntCureAmt(i)
        lOutput(i, 8) = clsIntCurePaid(i)
        lOutput(i, 9) = clsPrinCureAmt(i)
        lOutput(i, 10) = clsPrinCurePaid(i)
    Next i
    
    Output = lOutput
End Function




Public Sub Setup(iName As String, iThresh As Double)
    clsName = iName
    clsTrigger = iThresh
End Sub
Public Sub DealSetup(iNumofPayments As Long)
    ReDim clsResult(iNumofPayments)
    ReDim clsThreshold(iNumofPayments)
    ReDim clsPassFail(iNumofPayments)
    ReDim clsIntCureAmt(iNumofPayments)
    ReDim clsIntCurePaid(iNumofPayments)
    ReDim clsPriorIntCure(iNumofPayments)
    ReDim clsPriorPrinCure(iNumofPayments)
    ReDim clsPrinCureAmt(iNumofPayments)
    ReDim clsPrinCurePaid(iNumofPayments)
    ReDim clsNumerator(iNumofPayments)
    ReDim clsDenominator(iNumofPayments)
    clsPeriod = 1
End Sub


Public Sub Calc(iNum As Double, iDeno As Double)
    Dim lResults As Double
    If iDeno > 0 Then
        clsNumerator(clsPeriod) = iNum
        clsDenominator(clsPeriod) = iDeno
        lResults = iNum / iDeno
        clsResult(clsPeriod) = lResults
        If lResults > clsTrigger Then
            clsPassFail(clsPeriod) = True
        Else
            clsPassFail(clsPeriod) = False
            clsIntCureAmt(clsPeriod) = (1 - lResults / clsTrigger) * clsDenominator(clsPeriod)
            clsPrinCureAmt(clsPeriod) = (clsTrigger * (clsDenominator(clsPeriod)) - clsNumerator(clsPeriod)) / (clsTrigger - 1)
        End If
        clsLastPeriodCalc = clsPeriod
    Else
        clsPassFail(clsPeriod) = True
    End If

End Sub
Public Function PassFail() As Boolean
    PassFail = clsPassFail(clsPeriod)
End Function
Public Function InterestCureAmount() As Double
    InterestCureAmount = clsIntCureAmt(clsPeriod) - clsIntCurePaid(clsPeriod) - clsPriorIntCure(clsPeriod)
End Function


Public Sub AddPriorIntCure(iAmount As Double)
    Dim lCureDue As Double
    lCureDue = clsIntCureAmt(clsPeriod) - clsIntCurePaid(clsPeriod) - clsPriorIntCure(clsPeriod)
    If iAmount >= lCureDue Then
        clsPriorIntCure(clsPeriod) = clsPriorIntCure(clsPeriod) + lCureDue
        'Deal has been cured by IC Test
        clsPrinCureAmt(clsPeriod) = 0
    Else
        clsPriorIntCure(clsPeriod) = clsPriorIntCure(clsPeriod) + iAmount
    End If
    If clsPassFail(clsPeriod) = False And clsPrinCureAmt(clsPeriod) > 0 Then
        clsPrinCureAmt(clsPeriod) = (clsTrigger * (clsDenominator(clsPeriod) - clsIntCurePaid(clsPeriod) - clsPriorIntCure(clsPeriod)) - clsNumerator(clsPeriod)) / (clsTrigger - 1)
    End If
End Sub

Public Sub PayInterest(iAmount As Double)
    Dim lCureDue As Double
    
    lCureDue = clsIntCureAmt(clsPeriod) - clsIntCurePaid(clsPeriod) - clsPriorIntCure(clsPeriod)
    If iAmount >= lCureDue Then
        clsIntCurePaid(clsPeriod) = clsIntCurePaid(clsPeriod) + lCureDue
        iAmount = iAmount - lCureDue
        'OC breach has been cured by Interest proceeds
        clsPrinCureAmt(clsPeriod) = 0
    Else
        clsIntCurePaid(clsPeriod) = clsIntCurePaid(clsPeriod) + iAmount
        iAmount = 0
    End If

    'REcalculate based on any interest payments
    If clsPassFail(clsPeriod) = False And clsPrinCureAmt(clsPeriod) > 0 Then
        clsPrinCureAmt(clsPeriod) = (clsTrigger * (clsDenominator(clsPeriod) - clsIntCurePaid(clsPeriod) - clsPriorIntCure(clsPeriod)) - clsNumerator(clsPeriod)) / (clsTrigger - 1)
    End If
End Sub

Public Function PrincipalCureAmount() As Double
    PrincipalCureAmount = clsPrinCureAmt(clsPeriod) - clsPrinCurePaid(clsPeriod) - clsPriorPrinCure(clsPeriod)
End Function
Public Sub AddPriorPrinCure(iAmount As Double)
    Dim lCureDue As Double
    lCureDue = clsPrinCureAmt(clsPeriod) - clsPrinCurePaid(clsPeriod) - clsPriorPrinCure(clsPeriod)
    If iAmount >= lCureDue Then
        clsPriorPrinCure(clsPeriod) = clsPriorPrinCure(clsPeriod) + lCureDue
    Else
        clsPriorPrinCure(clsPeriod) = clsPriorPrinCure(clsPeriod) + iAmount
    End If

End Sub
Public Sub PayPrincipal(iAmount As Double)
    Dim lCureDue As Double
    
    lCureDue = clsPrinCureAmt(clsPeriod) - clsPrinCurePaid(clsPeriod) - clsPriorPrinCure(clsPeriod)
    If iAmount >= lCureDue Then
        clsPrinCurePaid(clsPeriod) = clsPrinCurePaid(clsPeriod) + lCureDue
        iAmount = iAmount - lCureDue
    Else
        clsPrinCurePaid(clsPeriod) = clsPrinCurePaid(clsPeriod) + iAmount
        iAmount = 0
    End If
End Sub

Public Sub Rollfoward()
    clsPeriod = clsPeriod + 1
End Sub
