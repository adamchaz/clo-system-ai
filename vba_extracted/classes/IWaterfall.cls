VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "IWaterfall"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
'This is going to be the interface off the waterfall class. Each Waterfall class will be made up of 5 subroutines
'WaterfallSetup-This will pass the CLO objects by ref. This will allow each subsequent warterfall
'CalcPeriod Run calcuation for the warterfall
'Run InterestWarterfall
'Run principal Waterfall
'Run Evnt of default Waterfall


Public Sub CalcPeriod(ByRef iperiod As Long, iICNum As Double, iOCNum As Double, iEODNum As Double)
'This is responsible for calculating the denominator and liability for the for the OC, IC, and EOD test

End Sub

Public Sub DealSetup(iPaymentDates() As PaymentDates, iReinvestEndDate As Date, ByRef iLiabDict As Dictionary, ByRef iOCTrig As Dictionary, ByRef iICTrig As Dictionary, ByRef iFeeDict As Dictionary, ByRef iIncFee As IncentiveFee)
'Pass all the variable from CLO.

End Sub
Public Sub PayEODWaterfall(iperiod As Long, iInt As Double, iPrin As Double)

End Sub
Public Sub PayInterestWaterfall(iperiod As Long, iInt As Double, ByRef oPrin As Double, ByRef oNotePayable As Double)
    'InterestWaterfall takes in interest

End Sub
Public Sub PayPrincipalWaterfall(iperiod As Long, iPrin As Double, iMaxReinvestAmount As Double, ByRef oReinvestment As Double, ByRef oNotePayable As Double)

End Sub
Public Sub PayNotePaymentSequence(iperiod As Long, iNotesPayable As Double)

End Sub
