VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "IncentiveFee"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
'Set up
Private clsFeeHurdleRate As Double
Private clsIncentFee As Double


Private clsThresholdReach As Boolean
Private clsSubPaymentsDict As Dictionary 'Set Payments and dates
Private clsClosingDate As Date

Private clsCurrentThreshold As Double

Private clsCurrIncetivePayments As Double
Private clsCurrSubPayments As Double
Private clsCurrDate As Date

Private clsPeriod As Long
Private clsCumDicountedSubPayments As Double  'Cumulative Subordinated payments discounted at the hurdle rate

'Date Storage
Private clsThreshold() As Double
Private clsIRR() As Double
Private clsFeePaid() As Double

Public Function Output() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsPeriod - 1, 2)
    lOutput(0, 0) = "Threshold"
    lOutput(0, 1) = "Fee Paid"
    lOutput(0, 2) = "IRR"
    
    For i = 1 To clsPeriod - 1
        lOutput(i, 0) = clsThreshold(i)
        lOutput(i, 1) = clsFeePaid(i)
        lOutput(i, 2) = Format(clsIRR(i), "0.000%")
    Next i
    Output = lOutput
End Function

Public Sub Setup(iFeeThreshold As Double, iIncentiveFee As Double, iPaytoSubNotholder As Dictionary)
    clsFeeHurdleRate = iFeeThreshold
    clsIncentFee = iIncentiveFee
    Set clsSubPaymentsDict = iPaytoSubNotholder
End Sub
Public Sub DealSetup(iNumofPayments As Long, iCloseDate As Date, ianalysisDate As Date)
    ReDim clsThreshold(iNumofPayments)
    ReDim clsIRR(iNumofPayments)
    ReDim clsFeePaid(iNumofPayments)
    clsPeriod = 1
    Dim lDate As Variant
    clsClosingDate = iCloseDate
    For Each lDate In clsSubPaymentsDict.Keys
        If CDate(lDate) > ianalysisDate Then
            clsSubPaymentsDict.Remove lDate
        End If
    Next
    For Each lDate In clsSubPaymentsDict.Keys
        clsCumDicountedSubPayments = clsCumDicountedSubPayments + (clsSubPaymentsDict(lDate) / ((1 + clsFeeHurdleRate) ^ ((lDate - clsClosingDate) / 365)))
        If clsCumDicountedSubPayments > 0 Then
           clsThresholdReach = True
           Exit For
        End If
    Next
    
End Sub


Public Sub Calc(iNextPay As Date)
    clsCurrDate = iNextPay
    If clsThresholdReach Then
        clsCurrentThreshold = 0
    Else
        clsCurrentThreshold = clsCumDicountedSubPayments * (1 + clsFeeHurdleRate) ^ ((iNextPay - clsClosingDate) / 365)
        clsCurrentThreshold = -1 * clsCurrentThreshold
    End If
    clsThreshold(clsPeriod) = clsCurrentThreshold
End Sub
Public Function IncentiveFeeThreshold() As Double
    If clsThresholdReach Then
        IncentiveFeeThreshold = 0
    Else
        IncentiveFeeThreshold = clsThreshold(clsPeriod) - clsCurrSubPayments
    End If
End Function

Public Sub PaymentToSubNotholder(iAmount As Double)
    clsCurrSubPayments = clsCurrSubPayments + iAmount
    If clsCurrSubPayments >= clsCurrentThreshold Then clsThresholdReach = True
End Sub
Public Sub PayIncentiveFee(iAmount As Double)
    If clsThresholdReach Then
        clsCurrIncetivePayments = clsCurrIncetivePayments + iAmount * clsIncentFee
        iAmount = iAmount * (1 - clsIncentFee)
    End If
End Sub


Public Sub Rollfoward()
    Dim lDates As Variant
    Dim lValues As Variant
    Dim lValue As Variant
    Dim i As Long

    clsThreshold(clsPeriod) = clsCurrentThreshold
    clsFeePaid(clsPeriod) = clsCurrIncetivePayments
    clsCumDicountedSubPayments = clsCumDicountedSubPayments + (clsCurrSubPayments / ((1 + clsFeeHurdleRate) ^ ((clsCurrDate - clsClosingDate) / 365)))
    clsSubPaymentsDict.Add clsCurrDate, clsCurrSubPayments
    lDates = clsSubPaymentsDict.Keys
    lValues = clsSubPaymentsDict.Items
    For i = LBound(lDates) To UBound(lDates)
        lDates(i) = CDate(lDates(i))
    Next i
    lValue = Application.Xirr(lValues, lDates)
    If VarType(lValue) = vbDouble Then
        clsIRR(clsPeriod) = CDbl(lValue)
    End If
    clsPeriod = clsPeriod + 1
    clsCurrSubPayments = 0
    clsCurrIncetivePayments = 0
End Sub

Public Function FeePaid() As Double
    Dim lTotal As Double
    Dim i As Long
    For i = LBound(clsFeePaid) To UBound(clsFeePaid)
        lTotal = lTotal + clsFeePaid(i)
    Next i
    FeePaid = lTotal
End Function
