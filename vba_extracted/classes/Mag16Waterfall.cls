VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Mag16Waterfall"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
Implements iWaterfall

'Variables that are link to the cloClass
Private clsLiabilityDict As Dictionary
Private clsFeesDict As Dictionary
Private clsOCTriggerDict As Dictionary
Private clsICTriggerDict As Dictionary
Private clsIncentiveFee As IncentiveFee
Private clsPaymentdate() As PaymentDates
Private clsReinvestEndDate As Date

Private Sub Class_Initialize()

End Sub

Private Sub iWaterfall_CalcPeriod(iperiod As Long, iICNum As Double, iOCNum As Double, iEODNum As Double)
    Dim lOCTestNum As Double
    Dim lICTestNum As Double
    Dim lEODNuum As Double
    Dim lClassABICDen As Double
    Dim lClassABOCDen As Double
    
    Dim lClassCOCDen As Double
    Dim lClassCICDen As Double
    
    Dim lClassDICDen As Double
    Dim lClassDOCDen As Double
    
    Dim lClassEOCDen As Double
    
    Dim lIDDen As Double
    Dim lEODDen As Double
    Dim lKey As Variant
    
    
    
    lOCTestNum = iOCNum
    lICTestNum = iICNum
    lEODNuum = iEODNum
    
    
    For Each lKey In clsLiabilityDict.Keys
        Select Case lKey
        
        Case "Class A"
            lEODDen = clsLiabilityDict(lKey).CurrBal
            lClassABICDen = lClassABICDen + clsLiabilityDict(lKey).IntDue
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
            lClassABOCDen = lClassABOCDen + clsLiabilityDict(lKey).CurrBal
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class B"
            lClassABICDen = lClassABICDen + clsLiabilityDict(lKey).IntDue
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
            lClassABOCDen = lClassABOCDen + clsLiabilityDict(lKey).CurrBal
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class C-1"
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class C-2"
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class D"
            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class E"
            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        End Select
    Next
    
    'reduce IC by trustee fee and by management fee
    lICTestNum = lICTestNum - clsFeesDict("Trustee Fee").FeeAccrued - clsFeesDict("Base Manager Fee").FeeAccrued
    
    
    For Each lKey In clsICTriggerDict.Keys
        Select Case lKey
        
        Case "Class B IC Test"
           clsICTriggerDict(lKey).Calc lICTestNum, lClassABICDen, lClassABOCDen

        Case "Class C-2 IC Test"
            clsICTriggerDict(lKey).Calc lICTestNum, lClassCICDen, lClassCOCDen

        Case "Class D IC Test"
            clsICTriggerDict(lKey).Calc lICTestNum, lClassDICDen, lClassDOCDen
        End Select
    Next
    
    For Each lKey In clsOCTriggerDict.Keys
        Select Case lKey

        Case "Class B OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassABOCDen
        Case "Class C-2 OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassCOCDen
        Case "Class D OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassDOCDen
        Case "Class E OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassDOCDen
        Case "Interest Diversion Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lIDDen
        Case "Event of Default"
            clsOCTriggerDict(lKey).Calc lEODNuum, lEODDen
        End Select
    Next
    
End Sub

Private Sub iWaterfall_DealSetup(iPaymentDates() As PaymentDates, iReinvestEndDate As Date, iLiabDict As Scripting.IDictionary, iOCTrig As Scripting.IDictionary, iICTrig As Scripting.IDictionary, iFeeDict As Scripting.IDictionary, iIncFee As IncentiveFee)
    clsPaymentdate = iPaymentDates
    clsReinvestEndDate = iReinvestEndDate
    Set clsLiabilityDict = iLiabDict
    Set clsOCTriggerDict = iOCTrig
    Set clsICTriggerDict = iICTrig
    Set clsFeesDict = iFeeDict
    Set clsIncentiveFee = iIncFee
End Sub

Private Sub iWaterfall_PayEODWaterfall(iperiod As Long, iInt As Double, iPrin As Double)
    Dim lTotalProceeds As Double
    Dim lPrinAmount As Double
    Dim lIntAmount As Double
    Dim lAmountPaid As Double
    


    
    lTotalProceeds = iInt + iPrin
    

    clsFeesDict("Trustee Fee").PayFee lTotalProceeds
    clsFeesDict("Admin Fee").PayFee lTotalProceeds
    clsFeesDict("Base Manager Fee").PayFee lTotalProceeds
    clsLiabilityDict("Class A").PayInterest lTotalProceeds
    clsLiabilityDict("Class A").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class B").PayInterest lTotalProceeds
    clsLiabilityDict("Class B").PayPrincipal lTotalProceeds
    If clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue > lTotalProceeds Then
        lAmountPaid = clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue
        clsLiabilityDict("Class C-1").PayInterest lTotalProceeds * clsLiabilityDict("Class C-1").IntDue / lAmountPaid
        clsLiabilityDict("Class C-2").PayInterest lTotalProceeds * clsLiabilityDict("Class C-2").IntDue / lAmountPaid
        lTotalProceeds = 0
    Else
        clsLiabilityDict("Class C-1").PayInteres lTotalProceeds
        clsLiabilityDict("Class C-2").PayInteres lTotalProceeds
    End If
    If clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal > lTotalProceeds Then
        lAmountPaid = clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal
        clsLiabilityDict("Class C-1").PayPIKInterest lTotalProceeds * clsLiabilityDict("Class C-1").PIKBal / lAmountPaid
        clsLiabilityDict("Class C-2").PayPIKInterest lTotalProceeds * clsLiabilityDict("Class C-2").PIKBal / lAmountPaid
        lTotalProceeds = 0
    Else
        clsLiabilityDict("Class C-1").PayPIKInterest lTotalProceeds
        clsLiabilityDict("Class C-2").PayPIKInterest lTotalProceeds
    End If
    If clsLiabilityDict("Class C-1").CurrBal + clsLiabilityDict("Class C-2").CurrBal > lTotalProceeds Then
        lAmountPaid = clsLiabilityDict("Class C-1").CurrBal + clsLiabilityDict("Class C-2").CurrBal
        clsLiabilityDict("Class C-1").PayPrincipal lTotalProceeds = 0 * clsLiabilityDict("Class C-1").CurrBal / lAmountPaid
        clsLiabilityDict("Class C-2").PayPrincipal lTotalProceeds = 0 * clsLiabilityDict("Class C-2").CurrBal / lAmountPaid
        lTotalProceeds = 0
    Else
        clsLiabilityDict("Class C-1").PayPrincipal lTotalProceeds
        clsLiabilityDict("Class C-2").PayPrincipal lTotalProceeds
    End If
    clsLiabilityDict("Class D").PayInterest lTotalProceeds
    clsLiabilityDict("Class D").PayPIKInterest lTotalProceeds
    clsLiabilityDict("Class D").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class E").PayInterest lTotalProceeds
    clsLiabilityDict("Class E").PayPIKInterest lTotalProceeds
    clsLiabilityDict("Class E").PayPrincipal lTotalProceeds
    
    clsFeesDict("Junior Manager Fee").PayFee lTotalProceeds
    
    'Assuming no administrative fees
    
    'Incentive Fee
    If clsIncentiveFee.IncentiveFeeThreshold > lTotalProceeds Then
        clsIncentiveFee.PaymentToSubNotholder lTotalProceeds
        clsLiabilityDict("Sub Notes").PayPrincipal lTotalProceeds
    Else
        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
        lTotalProceeds = lTotalProceeds - lAmountPaid
        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
        clsLiabilityDict("Sub Notes").PayPrincipal lAmountPaid
    End If
    
    clsIncentiveFee.PayIncentiveFee lTotalProceeds
    clsIncentiveFee.PaymentToSubNotholder lTotalProceeds
    clsLiabilityDict("Sub Notes").PayPrincipal lTotalProceeds
    
End Sub

Private Sub iWaterfall_PayInterestWaterfall(iperiod As Long, iInt As Double, oPrin As Double, oNotePayable As Double)
Dim lIntAmount As Double
    Dim lPrinAmount As Double
    
    Dim lPreviousAmount As Double
    Dim lAmountPaid As Double
    Dim lNotesPayable As Double
    
    lIntAmount = iInt


    'Interest waterfall
    
    'Pay Trustee Fee
    clsFeesDict("Trustee Fee").PayFee lIntAmount
    
    'Pay Admin Fee
    'Dont have admin Fees
    clsFeesDict("Admin Fee").PayFee lIntAmount
    
    'Pay senior Managment Fee
    clsFeesDict("Base Manager Fee").PayFee lIntAmount
    
    'Pay Class A notes
    clsLiabilityDict("Class A").PayInterest lIntAmount
    'Pay Class B Notes
    clsLiabilityDict("Class B").PayInterest lIntAmount
    'Coverage test are done in conjuction so pay the one with the largest cure amount.
    'If the larger cure is taken care of the secondary cure will also be solved
    lPreviousAmount = lIntAmount
    If clsICTriggerDict("Class B IC Test").CureAmount > clsOCTriggerDict("Class B OC Test").InterestCureAmount Then
        clsICTriggerDict("Class B IC Test").PayCure lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class B OC Test").AddPriorIntCure lAmountPaid
    Else
        clsOCTriggerDict("Class B OC Test").PayInterest lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class C-2 IC Test").AddPriorCure lAmountPaid
    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class B OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class C-2 OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    
    
    'Pay Class C Notes
    If clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue > lIntAmount Then
        lAmountPaid = clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue
        clsLiabilityDict("Class C-1").PayInterest lIntAmount * clsLiabilityDict("Class C-1").IntDue / lAmountPaid
        clsLiabilityDict("Class C-2").PayInterest lIntAmount * clsLiabilityDict("Class C-2").IntDue / lAmountPaid
        lIntAmount = 0
    Else
        clsLiabilityDict("Class C-1").PayInterest lIntAmount
        clsLiabilityDict("Class C-2").PayInterest lIntAmount
    End If
    If clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal > lIntAmount Then
        lAmountPaid = clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal
        clsLiabilityDict("Class C-1").PayPIKInterest lIntAmount * clsLiabilityDict("Class C-1").PIKBal / lAmountPaid
        clsLiabilityDict("Class C-2").PayPIKInterest lIntAmount * clsLiabilityDict("Class C-2").PIKBal / lAmountPaid
        lIntAmount = 0
    Else
        clsLiabilityDict("Class C-1").PayPIKInterest lIntAmount
        clsLiabilityDict("Class C-2").PayPIKInterest lIntAmount
    End If
    
    lPreviousAmount = lIntAmount
    If clsICTriggerDict("Class C-2 IC Test").CureAmount > clsOCTriggerDict("Class C-2 OC Test").InterestCureAmount Then
        clsICTriggerDict("Class C-2 IC Test").PayCure lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class C-2 OC Test").AddPriorIntCure lAmountPaid
    Else
        clsOCTriggerDict("Class C-2 OC Test").PayInterest lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class C-2 IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class E OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    'Pay Class D Notes
    clsLiabilityDict("Class D").PayInterest lIntAmount
    clsLiabilityDict("Class D").PayPIKInterest lIntAmount
    lPreviousAmount = lIntAmount
    If clsICTriggerDict("Class D IC Test").CureAmount > clsOCTriggerDict("Class D OC Test").InterestCureAmount Then
        clsICTriggerDict("Class D IC Test").PayCure lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    Else
        clsOCTriggerDict("Class D OC Test").PayInterest lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    End If
    clsOCTriggerDict("Class E OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    'Pay Class E Notes
    clsLiabilityDict("Class E").PayInterest lIntAmount
    clsLiabilityDict("Class E").PayPIKInterest lIntAmount
    
    lPreviousAmount = lIntAmount
    clsOCTriggerDict("Class E OC Test").PayInterest lIntAmount
    lAmountPaid = lPreviousAmount - lIntAmount
    oNotePayable = oNotePayable + lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    
    'Will ignore the the Moody;s Rating Test. Will assume it is satisfied.
    
    If clsPaymentdate(iperiod).PaymentDate <= clsReinvestEndDate Then
        'Interest Diversion
        If clsOCTriggerDict("Interest Diversion Test").PassFail = False Then
            If clsOCTriggerDict("Interest Diversion Test").InterestCureAmount > 0.5 * lIntAmount Then
                oPrin = oPrin + 0.5 * lIntAmount
                lIntAmount = 0.5 * lIntAmount
            Else
                oPrin = oPrin + clsOCTriggerDict("Interest Diversion Test").InterestCureAmount
                lIntAmount = lIntAmount - clsOCTriggerDict("Interest Diversion Test").InterestCureAmount
            End If
        End If
    End If
    
    'sub Management fee
    clsFeesDict("Junior Manager Fee").PayFee lIntAmount
    
    'Assuming no administrative fees
    
    'Incentive Fee
    If clsIncentiveFee.IncentiveFeeThreshold > lIntAmount Then
        clsIncentiveFee.PaymentToSubNotholder lIntAmount
        clsLiabilityDict("Sub Notes").PayInterest lIntAmount
    Else
        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
        lIntAmount = lIntAmount - lAmountPaid
        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
        clsLiabilityDict("Sub Notes").PayInterest lAmountPaid
    End If
    
    clsIncentiveFee.PayIncentiveFee lIntAmount
    clsIncentiveFee.PaymentToSubNotholder lIntAmount
    clsLiabilityDict("Sub Notes").PayInterest lIntAmount
End Sub

Private Sub iWaterfall_PayNotePaymentSequence(iperiod As Long, iNotesPayable As Double)
    Dim lPayableAmount As Double
    Dim lAmountPaid As Double
    
    lPayableAmount = iNotesPayable
    clsLiabilityDict("Class A").PayPrincipal lPayableAmount
    clsLiabilityDict("Class B").PayPrincipal lPayableAmount
    If clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue > lPayableAmount Then
        lAmountPaid = clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue
        clsLiabilityDict("Class C-1").PayInterest lPayableAmount * clsLiabilityDict("Class C-1").IntDue / lAmountPaid
        clsLiabilityDict("Class C-2").PayInterest lPayableAmount * clsLiabilityDict("Class C-2").IntDue / lAmountPaid
        lPayableAmount = 0
    Else
        clsLiabilityDict("Class C-1").PayInterest lPayableAmount
        clsLiabilityDict("Class C-2").PayInterest lPayableAmount
    End If
    If clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal > lPayableAmount Then
        lAmountPaid = clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal
        clsLiabilityDict("Class C-1").PayPIKInterest lPayableAmount * clsLiabilityDict("Class C-1").PIKBal / lAmountPaid
        clsLiabilityDict("Class C-2").PayPIKInterest lPayableAmount * clsLiabilityDict("Class C-2").PIKBal / lAmountPaid
        lPayableAmount = 0
    Else
        clsLiabilityDict("Class C-1").PayPIKInterest lPayableAmount
        clsLiabilityDict("Class C-2").PayPIKInterest lPayableAmount
        
    End If
    If clsLiabilityDict("Class C-1").CurrBal + clsLiabilityDict("Class C-2").CurrBal > lPayableAmount Then
        lAmountPaid = clsLiabilityDict("Class C-1").CurrBal + clsLiabilityDict("Class C-2").CurrBal
        clsLiabilityDict("Class C-1").PayPrincipal lPayableAmount * clsLiabilityDict("Class C-1").CurrBal / lAmountPaid
        clsLiabilityDict("Class C-2").PayPrincipal lPayableAmount * clsLiabilityDict("Class C-2").CurrBal / lAmountPaid
        lPayableAmount = 0
    Else
        clsLiabilityDict("Class C-1").PayPrincipal lPayableAmount
        clsLiabilityDict("Class C-2").PayPrincipal lPayableAmount
    End If
    clsLiabilityDict("Class D").PayInterest lPayableAmount
    clsLiabilityDict("Class D").PayPIKInterest lPayableAmount
    clsLiabilityDict("Class D").PayPrincipal lPayableAmount
    clsLiabilityDict("Class E").PayInterest lPayableAmount
    clsLiabilityDict("Class E").PayPIKInterest lPayableAmount
    clsLiabilityDict("Class E").PayPrincipal lPayableAmount
   
    
    'Assuming no administrative fees
    
    'Incentive Fee
    If clsIncentiveFee.IncentiveFeeThreshold > lPayableAmount Then
        clsIncentiveFee.PaymentToSubNotholder lPayableAmount
        clsLiabilityDict("Sub Notes").PayPrincipal lPayableAmount
    Else
        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
        lPayableAmount = lPayableAmount - lAmountPaid
        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
        clsLiabilityDict("Sub Notes").PayPrincipal lAmountPaid
    End If
    
    clsIncentiveFee.PayIncentiveFee lPayableAmount
    clsIncentiveFee.PaymentToSubNotholder lPayableAmount
    clsLiabilityDict("Sub Notes").PayPrincipal lPayableAmount
End Sub

Private Sub iWaterfall_PayPrincipalWaterfall(iperiod As Long, iPrin As Double, iMaxReinvestAmount As Double, oReinvestment As Double, oNotePayable As Double)
    Dim lPrinAmount As Double
    
    Dim lPreviousAmount As Double
    Dim lAmountPaid As Double
    Dim lNotesPayable As Double
    Dim lControllingClass As String
    Dim lReinvestType As String
    Dim lReinvestPCT As Double
    
    
    lPrinAmount = iPrin
    If clsLiabilityDict("Class A").CurrBal > 0 Then
        lControllingClass = "Class A"
    ElseIf clsLiabilityDict("Class B").CurrBal > 0 Then
         lControllingClass = "Class B"
    ElseIf clsLiabilityDict("Class C-2").CurrBal > 0 Then
         lControllingClass = "Class C"
    ElseIf clsLiabilityDict("Class D").CurrBal > 0 Then
         lControllingClass = "Class D"
    ElseIf clsLiabilityDict("Class E").CurrBal > 0 Then
         lControllingClass = "Class #"
    Else
        lControllingClass = "Sub Notes"
    End If
    
    'Principal Warterfall
    
    'Pay Trustee Fee
    clsFeesDict("Trustee Fee").PayFee lPrinAmount
    
    'Pay Admin Fee
    'Dont have admin Fees
    clsFeesDict("Admin Fee").PayFee lPrinAmount
    
    'Pay senior Managment Fee
    clsFeesDict("Base Manager Fee").PayFee lPrinAmount
    
    'Pay Class A notes
    clsLiabilityDict("Class A").PayInterest lPrinAmount
    'Pay Class B Notes
    clsLiabilityDict("Class B").PayInterest lPrinAmount
    'Coverage test are done in conjuction so pay the one with the largest cure amount.
    'If the larger cure is taken care of the secondary cure will also be solved
    lPreviousAmount = lPrinAmount
    If clsICTriggerDict("Class B IC Test").CureAmount > clsOCTriggerDict("Class B OC Test").PrincipalCureAmount Then
        clsICTriggerDict("Class B IC Test").PayCure lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class B OC Test").AddPriorPrinCure lAmountPaid
    Else
        clsOCTriggerDict("Class B OC Test").PayPrincipal lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class C-2 IC Test").AddPriorCure lAmountPaid
    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class B OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class C-2 OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    
    If lControllingClass = "Class C" Then
        'Pay Class C Notes
        If clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue > lPrinAmount Then
            lAmountPaid = clsLiabilityDict("Class C-1").IntDue + clsLiabilityDict("Class C-2").IntDue
            clsLiabilityDict("Class C-1").PayInterest lPrinAmount * clsLiabilityDict("Class C-1").IntDue / lAmountPaid
            clsLiabilityDict("Class C-2").PayInterest lPrinAmount * clsLiabilityDict("Class C-2").IntDue / lAmountPaid
            lPrinAmount = 0
        Else
            clsLiabilityDict("Class C-1").PayInterest lPrinAmount
            clsLiabilityDict("Class C-2").PayInterest lPrinAmount
        End If
        If clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal > lPrinAmount Then
            lAmountPaid = clsLiabilityDict("Class C-1").PIKBal + clsLiabilityDict("Class C-2").PIKBal
            clsLiabilityDict("Class C-1").PayPIKInterest lPrinAmount * clsLiabilityDict("Class C-1").PIKBal / lAmountPaid
            clsLiabilityDict("Class C-2").PayPIKInterest lPrinAmount * clsLiabilityDict("Class C-2").PIKBal / lAmountPaid
            lPrinAmount = 0
        Else
            clsLiabilityDict("Class C-1").PayPIKInterest lPrinAmount
            clsLiabilityDict("Class C-2").PayPIKInterest lPrinAmount
        End If
    End If
    
    lPreviousAmount = lPrinAmount
    If clsICTriggerDict("Class C-2 IC Test").CureAmount > clsOCTriggerDict("Class C-2 OC Test").PrincipalCureAmount Then
        clsICTriggerDict("Class C-2 IC Test").PayCure lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class C-2 OC Test").AddPriorPrinCure lAmountPaid
    Else
        clsOCTriggerDict("Class C-2 OC Test").PayPrincipal lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class C-2 IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class E OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    If lControllingClass = "Class D" Then
        'Pay Class D Notes
        clsLiabilityDict("Class D").PayInterest lPrinAmount
        clsLiabilityDict("Class D").PayPIKInterest lPrinAmount
    End If
    
    lPreviousAmount = lPrinAmount
    If clsICTriggerDict("Class D IC Test").CureAmount > clsOCTriggerDict("Class D OC Test").PrincipalCureAmount Then
        clsICTriggerDict("Class D IC Test").PayCure lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    Else
        clsOCTriggerDict("Class D OC Test").PayPrincipal lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
    End If
    clsOCTriggerDict("Class E OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
     If lControllingClass = "Class E" Then
        'Pay Class E Notes
        clsLiabilityDict("Class E").PayInterest lPrinAmount
        clsLiabilityDict("Class E").PayPIKInterest lPrinAmount
    End If
    
    lPreviousAmount = lPrinAmount
    clsOCTriggerDict("Class E OC Test").PayPrincipal lPrinAmount
    lAmountPaid = lPreviousAmount - lPrinAmount
    oNotePayable = oNotePayable + lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    'sub Management fee
    clsFeesDict("Junior Manager Fee").PayFee lAmountPaid
    
    
    'Max Reinvestment amount
    lAmountPaid = iMaxReinvestAmount

    If lAmountPaid > lPrinAmount Then lAmountPaid = lPrinAmount
    oReinvestment = oReinvestment + lAmountPaid
    lPrinAmount = lPrinAmount - lAmountPaid
    
    oNotePayable = oNotePayable + lPrinAmount
    lPrinAmount = 0
End Sub


