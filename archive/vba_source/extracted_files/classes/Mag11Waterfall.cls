VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Mag11Waterfall"
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
    Dim lClassAICDen As Double
    Dim lClassAOCDen As Double
    Dim lClassBICDen As Double
    Dim lClassBOCDen As Double
    Dim lClassCICDen As Double
    Dim lClassCOCDen As Double
    Dim lClassDOCDen As Double
    Dim lIDDen As Double
    Dim lEODDen As Double
    Dim lKey As Variant
    
    
    
    lOCTestNum = iOCNum
    lICTestNum = iICNum
    lEODNuum = iEODNum
    
    
    For Each lKey In clsLiabilityDict.Keys
        Select Case lKey
        
        Case "Class A-1"
            lEODDen = clsLiabilityDict(lKey).CurrBal
            lClassAICDen = lClassAICDen + clsLiabilityDict(lKey).IntDue
            lClassBICDen = lClassBICDen + clsLiabilityDict(lKey).IntDue
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            
            lClassAOCDen = lClassAOCDen + clsLiabilityDict(lKey).CurrBal
            lClassBOCDen = lClassBOCDen + clsLiabilityDict(lKey).CurrBal
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class A-2"
            lEODDen = clsLiabilityDict(lKey).CurrBal
            lClassAICDen = lClassAICDen + clsLiabilityDict(lKey).IntDue
            lClassBICDen = lClassBICDen + clsLiabilityDict(lKey).IntDue
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            
            lClassAOCDen = lClassAOCDen + clsLiabilityDict(lKey).CurrBal
            lClassBOCDen = lClassBOCDen + clsLiabilityDict(lKey).CurrBal
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class B"
            lClassBICDen = lClassBICDen + clsLiabilityDict(lKey).IntDue
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            
            lClassBOCDen = lClassBOCDen + clsLiabilityDict(lKey).CurrBal
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class C"
            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        Case "Class D"
            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
        End Select
    Next
    
    'reduce IC by trustee fee and by management fee
    lICTestNum = lICTestNum - clsFeesDict("Trustee Fee").FeeAccrued - clsFeesDict("Base Manager Fee").FeeAccrued
    
    
    For Each lKey In clsICTriggerDict.Keys
        Select Case lKey
        
        Case "Class A-2 IC Test"
           clsICTriggerDict(lKey).Calc lICTestNum, lClassAICDen, lClassAOCDen

        Case "Class B IC Test"
            clsICTriggerDict(lKey).Calc lICTestNum, lClassBICDen, lClassBOCDen

        Case "Class C IC Test"
            clsICTriggerDict(lKey).Calc lICTestNum, lClassCICDen, lClassCOCDen
        End Select
    Next
    
    For Each lKey In clsOCTriggerDict.Keys
        Select Case lKey

        Case "Class A-2 OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassAOCDen
        Case "Class B OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassBOCDen
        Case "Class C OC Test"
            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassCOCDen
        Case "Class D OC Test"
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
    clsLiabilityDict("Class A-1").PayInterest lTotalProceeds
    clsLiabilityDict("Class A-1").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class A-2").PayInterest lTotalProceeds
    clsLiabilityDict("Class A-2").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class B").PayInterest lTotalProceeds
    clsLiabilityDict("Class B").PayPIKInterest lTotalProceeds
    clsLiabilityDict("Class B").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class C").PayInterest lTotalProceeds
    clsLiabilityDict("Class C").PayPIKInterest lTotalProceeds
    clsLiabilityDict("Class C").PayPrincipal lTotalProceeds
    clsLiabilityDict("Class D").PayInterest lTotalProceeds
    clsLiabilityDict("Class D").PayPIKInterest lTotalProceeds
    clsLiabilityDict("Class D").PayPrincipal lTotalProceeds
    
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
    
    'Pay Class A-1 notes
    clsLiabilityDict("Class A-1").PayInterest lIntAmount
    'Pay Class A-2 Notes
    clsLiabilityDict("Class A-2").PayInterest lIntAmount
    'Coverage test are done in conjuction so pay the one with the largest cure amount.
    'If the larger cure is taken care of the secondary cure will also be solved
    lPreviousAmount = lIntAmount
    If clsICTriggerDict("Class A-2 IC Test").CureAmount > clsOCTriggerDict("Class A-2 OC Test").InterestCureAmount Then
        clsICTriggerDict("Class A-2 IC Test").PayCure lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class A-2 OC Test").AddPriorIntCure lAmountPaid
    Else
        clsOCTriggerDict("Class A-2 OC Test").PayInterest lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class A-2 IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class B OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class C OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    
    
    
    'Pay Class B Notes
    clsLiabilityDict("Class B").PayInterest lIntAmount
    clsLiabilityDict("Class B").PayPIKInterest lIntAmount
    
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
    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class C OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    'Pay Class C Notes
    clsLiabilityDict("Class C").PayInterest lIntAmount
    clsLiabilityDict("Class C").PayPIKInterest lIntAmount
    lPreviousAmount = lIntAmount
    If clsICTriggerDict("Class C IC Test").CureAmount > clsOCTriggerDict("Class C OC Test").InterestCureAmount Then
        clsICTriggerDict("Class C IC Test").PayCure lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class C OC Test").AddPriorIntCure lAmountPaid
    Else
        clsOCTriggerDict("Class C OC Test").PayInterest lIntAmount
        lAmountPaid = lPreviousAmount - lIntAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    End If
    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
    
    'Pay Class C Notes
    clsLiabilityDict("Class D").PayInterest lIntAmount
    clsLiabilityDict("Class D").PayPIKInterest lIntAmount
    
    lPreviousAmount = lIntAmount
    clsOCTriggerDict("Class D OC Test").PayInterest lIntAmount
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
    clsLiabilityDict("Class A-1").PayPrincipal lPayableAmount
    clsLiabilityDict("Class A-2").PayPrincipal lPayableAmount
    clsLiabilityDict("Class B").PayPIKInterest lPayableAmount
    clsLiabilityDict("Class B").PayPrincipal lPayableAmount
    clsLiabilityDict("Class C").PayPIKInterest lPayableAmount
    clsLiabilityDict("Class C").PayPrincipal lPayableAmount
    clsLiabilityDict("Class D").PayPIKInterest lPayableAmount
    clsLiabilityDict("Class D").PayPrincipal lPayableAmount
        'sub Management fee
    clsFeesDict("Junior Manager Fee").PayFee lPayableAmount
    
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
    If clsLiabilityDict("Class A-1").CurrBal > 0 Then
        lControllingClass = "Class A-1"
    ElseIf clsLiabilityDict("Class A-2").CurrBal > 0 Then
         lControllingClass = "Class A-2"
    ElseIf clsLiabilityDict("Class B").CurrBal > 0 Then
         lControllingClass = "Class B"
    ElseIf clsLiabilityDict("Class C").CurrBal > 0 Then
         lControllingClass = "Class C"
    ElseIf clsLiabilityDict("Class D").CurrBal > 0 Then
         lControllingClass = "Class D"
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
    
    'Pay Class A-1 notes
    clsLiabilityDict("Class A-1").PayInterest lPrinAmount
    'Pay Class A-2 Notes
    clsLiabilityDict("Class A-2").PayInterest lPrinAmount
    'Coverage test are done in conjuction so pay the one with the largest cure amount.
    'If the larger cure is taken care of the secondary cure will also be solved
    lPreviousAmount = lPrinAmount
    If clsICTriggerDict("Class A-2 IC Test").CureAmount > clsOCTriggerDict("Class A-2 OC Test").PrincipalCureAmount Then
        clsICTriggerDict("Class A-2 IC Test").PayCure lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class A-2 OC Test").AddPriorPrinCure lAmountPaid
    Else
        clsOCTriggerDict("Class A-2 OC Test").PayPrincipal lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class A-2 IC Test").AddPriorCure lAmountPaid
    End If
    clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class A-2 OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class B OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class C OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    
    If lControllingClass = "Class B" Then
        'Pay Class B Notes
        clsLiabilityDict("Class B").PayInterest lPrinAmount
        clsLiabilityDict("Class B").PayPIKInterest lPrinAmount
    End If
    
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
    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    clsOCTriggerDict("Class C OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    If lControllingClass = "Class C" Then
        'Pay Class C Notes
        clsLiabilityDict("Class C").PayInterest lPrinAmount
        clsLiabilityDict("Class C").PayPIKInterest lPrinAmount
    End If
    
    lPreviousAmount = lPrinAmount
    If clsICTriggerDict("Class C IC Test").CureAmount > clsOCTriggerDict("Class C OC Test").PrincipalCureAmount Then
        clsICTriggerDict("Class C IC Test").PayCure lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsOCTriggerDict("Class C OC Test").AddPriorPrinCure lAmountPaid
    Else
        clsOCTriggerDict("Class C OC Test").PayPrincipal lPrinAmount
        lAmountPaid = lPreviousAmount - lPrinAmount
        oNotePayable = oNotePayable + lAmountPaid
        clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
    End If
    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
     If lControllingClass = "Class D" Then
        'Pay Class C Notes
        clsLiabilityDict("Class D").PayInterest lPrinAmount
        clsLiabilityDict("Class D").PayPIKInterest lPrinAmount
    End If
    
    lPreviousAmount = lPrinAmount
    clsOCTriggerDict("Class D OC Test").PayPrincipal lPrinAmount
    lAmountPaid = lPreviousAmount - lPrinAmount
    oNotePayable = oNotePayable + lAmountPaid
    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
    
    
    
    'Max Reinvestment amount
    lAmountPaid = iMaxReinvestAmount

    If lAmountPaid > lPrinAmount Then lAmountPaid = lPrinAmount
    oReinvestment = oReinvestment + lAmountPaid
    lPrinAmount = lPrinAmount - lAmountPaid
    
    oNotePayable = oNotePayable + lPrinAmount
    lPrinAmount = 0
End Sub


