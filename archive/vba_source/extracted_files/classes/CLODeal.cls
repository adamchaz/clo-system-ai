VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CLODeal"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit


Private clsConTest As ConcentrationTest
Private clsTestSetting As TestSettings



Private clsAccountDict As Dictionary
Private clsLiabilityDict As Dictionary
Private clsFeesDict As Dictionary
Private clsICTriggerDict As Dictionary
Private clsOCTriggerDict As Dictionary
Private clsIncentiveFee As IncentiveFee
Private clsDealDate As DealDates
Private clsCLOInput As Dictionary
Private clsCFInput As Dictionary
Private clsCollateralPool As CollateralPoolForCLO
Private clsReinvest As Reinvest
Private clsReinvestInfo As ReinvestInfo
Private clsYieldCurve As YieldCurve
Private clsWaterfall As iWaterfall


Private clsIntProceeds() As Double
Private clsPrinProceeds() As Double
Private clsNotesPayable() As Double
Private clsReinvestment() As Double
Private clsLIBOR() As Double
Private clsDealName As String


Private clsPaymentdate() As PaymentDates
Private clsLastperiod As Long
Public Property Get DealName() As String
    DealName = clsDealName
End Property

Private Function CalcReinvestAmount(iperiod As Long, iLiquidate As Boolean) As Double
    Dim lReinvestType As String
    Dim lReinvestPCT As Double
    Dim lAmountPaid As Double
    
    If iLiquidate Then
        lReinvestType = "None"
        lReinvestPCT = 0
    ElseIf clsPaymentdate(iperiod).PaymentDate <= clsDealDate.ReinvestDate Then
        lReinvestType = clsReinvestInfo.PreReinvType
        lReinvestPCT = clsReinvestInfo.PreRinvestPct
    ElseIf clsPaymentdate(iperiod).PaymentDate < clsDealDate.MatDate Then
        lReinvestType = clsReinvestInfo.PostReinvType
        lReinvestPCT = clsReinvestInfo.PostReinvestPct
    End If
    Select Case UCase(lReinvestType)
    
    Case "ALL PRINCIPAL"
        lAmountPaid = clsPrinProceeds(iperiod)
    Case "UNSCHEDULED PRINCIPAL"
        lAmountPaid = clsCollateralPool.UnSchedPrin + clsReinvest.UnSchedPrin
    Case Else
        lAmountPaid = 0
    End Select
    lAmountPaid = lAmountPaid * lReinvestPCT
    CalcReinvestAmount = lAmountPaid
    
End Function

Public Sub LoadReinvestInfo(ireinvestinfo As ReinvestInfo)
    clsReinvestInfo = ireinvestinfo
End Sub
Public Sub LoadWaterfall(iWaterfall As iWaterfall)
    Set clsWaterfall = iWaterfall
End Sub

Public Function DealOutputs() As Variant
    Dim i As Long
    Dim lOutput As Variant
    Dim lNumPayment As Long
    
    lNumPayment = UBound(clsPaymentdate)
    ReDim lOutput(0 To clsLastperiod, 8)
    lOutput(0, 0) = "Period"
    lOutput(0, 1) = "Payment Date"
    lOutput(0, 2) = "Coll Beg Date"
    lOutput(0, 3) = "Coll End Date"
    lOutput(0, 4) = "Int Proceeds"
    lOutput(0, 5) = "Prin Proceeds"
    lOutput(0, 6) = "Payment of Principal"
    lOutput(0, 7) = "Procceds Reinvest"
    lOutput(0, 8) = "LIBOR"
    For i = 1 To clsLastperiod
        lOutput(i, 0) = i
        lOutput(i, 1) = clsPaymentdate(i).PaymentDate
        lOutput(i, 2) = clsPaymentdate(i).CollBegDate
        lOutput(i, 3) = clsPaymentdate(i).CollEndDate
        lOutput(i, 4) = clsIntProceeds(i)
        lOutput(i, 5) = clsPrinProceeds(i)
        lOutput(i, 6) = clsNotesPayable(i)
        lOutput(i, 7) = clsReinvestment(i)
        lOutput(i, 8) = Format(clsLIBOR(i), "0.00000%")
    Next i
    DealOutputs = lOutput
End Function
Public Function OutputsOrigCollat() As Variant
    OutputsOrigCollat = clsCollateralPool.GetCollatCF
End Function
Public Function OutputsReinvetCollat() As Variant
    OutputsReinvetCollat = clsReinvest.GetCollatCF
End Function
Public Function OutputIncentiveFee() As Variant
    OutputIncentiveFee = clsIncentiveFee.Output
End Function
Private Sub CalcPaymentDates()
    Dim i As Long
    Dim lCounter As Long
    Dim lIntDeterDate As Date
    Dim lPaymentDate As Date
    Dim lCollBegDae As Date
    Dim lNextPaymentDate As Date
    Dim lPreviousPaymentDate As Date
    Dim lFirstPaydate As Date 'Non Holiday Adjusted
    
    
    lFirstPaydate = DateSerial(Year(clsDealDate.FirstPayDate), Month(clsDealDate.FirstPayDate), clsDealDate.PayDay)
    lCounter = DateDiff("Q", lFirstPaydate, clsDealDate.MatDate)
    ReDim clsPaymentdate(lCounter + 5)
    lCounter = 1
    i = 1
    
    lNextPaymentDate = lFirstPaydate
    Do While lNextPaymentDate <= clsDealDate.MatDate
        If lNextPaymentDate > clsDealDate.AnalysisDate Then
            If lNextPaymentDate = lFirstPaydate Then
                clsPaymentdate(lCounter).CollBegDate = clsDealDate.ClosingDate
                clsPaymentdate(lCounter).IntDeterDate = clsDealDate.ClosingDate
            Else
                
                If lCounter = 1 Then
                    clsPaymentdate(lCounter - 1).PaymentDate = CheckBusinessDate(lPreviousPaymentDate, clsDealDate.BussConv)
                    clsPaymentdate(lCounter - 1).CollEndDate = GetPreviousBusinessDate(clsPaymentdate(lCounter - 1).PaymentDate, clsDealDate.DeterDate)
                End If
                clsPaymentdate(lCounter).IntDeterDate = GetPreviousBusinessDate(clsPaymentdate(lCounter - 1).PaymentDate, clsDealDate.IntDeterDate)
                clsPaymentdate(lCounter).CollBegDate = clsPaymentdate(lCounter - 1).CollEndDate
                
            End If
            clsPaymentdate(lCounter).PaymentDate = CheckBusinessDate(lNextPaymentDate, clsDealDate.BussConv)
            clsPaymentdate(lCounter).CollEndDate = GetPreviousBusinessDate(clsPaymentdate(lCounter).PaymentDate, clsDealDate.DeterDate)
            lCounter = lCounter + 1
        End If
        lPreviousPaymentDate = lNextPaymentDate
        lNextPaymentDate = DateAdd("M", i * clsDealDate.MonthsBetwPay, lFirstPaydate)
        i = i + 1
    Loop
    ReDim Preserve clsPaymentdate(lCounter - 1)

End Sub


Public Sub Calc2()
    'This will use the waterfall class instead of subroutines stored in CLO Deal

    Dim i As Long
    Dim lLIBOR As Double
    Dim lLiquidate As Boolean
    Dim lMaxReinvestAmount As Double
    
    
    Call CalcPaymentDates
    Call DealSetup
    Call clsWaterfall.DealSetup(clsPaymentdate, clsDealDate.ReinvestDate, clsLiabilityDict, clsOCTriggerDict, clsICTriggerDict, clsFeesDict, clsIncentiveFee)
    For i = 1 To UBound(clsPaymentdate)
        Call CalcPeriod2(i, lLiquidate)
        If clsCLOInput("Event of Default") = True Or clsOCTriggerDict("Event of Default").PassFail = False Then
            Call clsWaterfall.PayEODWaterfall(i, clsIntProceeds(i), clsPrinProceeds(i))
        Else
            Call clsWaterfall.PayInterestWaterfall(i, clsIntProceeds(i), clsPrinProceeds(i), clsNotesPayable(i))
            lMaxReinvestAmount = CalcReinvestAmount(i, lLiquidate)
            Call clsWaterfall.PayPrincipalWaterfall(i, clsPrinProceeds(i), lMaxReinvestAmount, clsReinvestment(i), clsNotesPayable(i))
            Call clsWaterfall.PayNotePaymentSequence(i, clsNotesPayable(i))
            clsReinvest.AddReinvestment clsReinvestment(i)
        End If
        If clsLiabilityDict("Sub Notes").CurDistrPct < clsCFInput("Call when Quarterly Sub Dist <") And i < UBound(clsPaymentdate) Then
            'Next period liquidate
            If clsPaymentdate(i + 1).PaymentDate >= clsDealDate.NoCallDate Then
                lLiquidate = True
            End If
        ElseIf i = UBound(clsPaymentdate) - 1 Then
            'Period before Stated Maturity
            lLiquidate = True
        End If
        
        If clsCollateralPool.PrinBallAllAssets + clsReinvest.PrinBallAllAssets <= 0.01 Then
            clsLastperiod = i
            Call Rollfoward
            Exit For
        Else
            Call Rollfoward
        End If
    Next i
End Sub

Public Sub CalcRiskMeasures()
    Dim lLiabName As Variant
    Dim lLiab As Liability
    
    For Each lLiabName In clsLiabilityDict
        Set lLiab = clsLiabilityDict(lLiabName)
        'If lLiab.InputDM > 0 Then
            lLiab.CalcRiskMeasures clsYieldCurve, clsPaymentdate, clsCLOInput("Analysis Date")
        'End If
    Next
    
End Sub


Private Sub CalcPeriod2(iperiod As Long, Optional iLiquidate As Boolean)
    '1. Deposit interest and proceeds into collection account.
    '2. Calc Liabilities
    '3. Calc Inputs
        'a. Fee Basis Amount
        'b. Event of Default Numerator
        'c. Adjusted Collateral Principal amount
        
    Dim lLastPay As Date
    Dim lNextPay As Date
    Dim lBegColl As Date
    Dim lEndColl As Date
    Dim lAmount As Double
    Dim lLIBOR As Double
    
    lLastPay = clsPaymentdate(iperiod - 1).PaymentDate
    If lLastPay = 0 Then lLastPay = clsDealDate.ClosingDate
    lNextPay = clsPaymentdate(iperiod).PaymentDate
    lBegColl = clsPaymentdate(iperiod).CollBegDate
    lEndColl = clsPaymentdate(iperiod).CollEndDate
    If iperiod = 1 Then
        lLIBOR = clsCLOInput("Current LIBOR")
    Else
        lLIBOR = clsYieldCurve.SpotRate(clsPaymentdate(iperiod).IntDeterDate, clsDealDate.MonthsBetwPay)
    End If
    
    
    clsLIBOR(iperiod) = lLIBOR
    
    'Add cash to the collection account
    lAmount = clsCollateralPool.GetProceeds("INTEREST") + clsReinvest.GetProceeds("INTEREST")
    clsAccountDict(AccountType.Collection).Add CashType.Interest, lAmount
    
    lAmount = clsCollateralPool.GetProceeds("PRINCIPAL") + clsReinvest.GetProceeds("PRINCIPAL")
    clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
    
    
    lAmount = clsCLOInput("Purchase Finance Accrued Interest")
    If clsAccountDict(AccountType.Collection).InterestProceeds > lAmount Then
        clsAccountDict(AccountType.Collection).Add CashType.Interest, -lAmount
        clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
        clsCLOInput("Purchase Finance Accrued Interest") = 0
    Else
        lAmount = clsAccountDict(AccountType.Collection).InterestProceeds
        clsAccountDict(AccountType.Collection).Add CashType.Interest, -lAmount
        clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
        clsCLOInput("Purchase Finance Accrued Interest") = clsCLOInput("Purchase Finance Accrued Interest") - lAmount
    End If
    
    'Calc  Liabilitis
    Dim lKey As Variant
    For Each lKey In clsLiabilityDict.Keys
        clsLiabilityDict(lKey).Calc lLIBOR, lLastPay, lNextPay
    Next
    
    'CalcFeeeBais
    Dim lFeeBasis As Double
    Dim lPrinBalAllAssets As Double
    Dim lPrinBalExDefaults As Double
    Dim lPrinBalDefauts As Double
    Dim lMVDefaults As Double
    Dim lIntProceeds As Double
    Dim lPrinProceeds As Double
    Dim lCCCCaaAdj As Double
    Dim lWithdrawl As Double
    
    lWithdrawl = clsAccountDict(AccountType.Collection).InterestProceeds
    clsAccountDict(AccountType.Collection).Add CashType.Interest, -lWithdrawl
    lIntProceeds = lWithdrawl
    
    lWithdrawl = clsAccountDict(AccountType.Collection).PrincipalProceeds
    clsAccountDict(AccountType.Collection).Add CashType.Principal, -lWithdrawl
    lPrinProceeds = lWithdrawl
    
    lWithdrawl = clsAccountDict(AccountType.InterestReserve).PrincipalProceeds
    clsAccountDict(AccountType.InterestReserve).Add CashType.Principal, -lWithdrawl
    
    lIntProceeds = lIntProceeds + lWithdrawl
    
    clsIntProceeds(iperiod) = lIntProceeds
    clsPrinProceeds(iperiod) = lPrinProceeds
    
    lPrinBalAllAssets = clsCollateralPool.PrinBallAllAssets + clsReinvest.PrinBallAllAssets
    lPrinBalExDefaults = clsCollateralPool.PrinBallExDefaults + clsReinvest.PrinBallExDefaults
    lPrinBalDefauts = clsCollateralPool.PrinBallDefaults + clsReinvest.PrinBallDefaults
    lMVDefaults = clsCollateralPool.MVDefaults + clsReinvest.MVDefaults
    lCCCCaaAdj = clsCollateralPool.CalcCCCExcessAdjustment(lPrinBalExDefaults + lPrinProceeds, clsCLOInput("CCC Asset Haircut Percent"), lEndColl, clsCFInput("CCC Liquidation Price"))
    
    
    lFeeBasis = lPrinBalAllAssets + lPrinProceeds + clsCLOInput("Purchase Finance Accrued Interest")
    For Each lKey In clsFeesDict.Keys
        clsFeesDict(lKey).Calc lLastPay, lNextPay, lFeeBasis, lLIBOR
    Next
    clsIncentiveFee.Calc lNextPay
    


    Dim lOCTestNum As Double
    Dim lICTestNum As Double
    Dim lEODNum As Double
    
    lICTestNum = lIntProceeds
    lOCTestNum = lPrinBalExDefaults + lMVDefaults - lCCCCaaAdj + lPrinProceeds + clsCLOInput("Purchase Finance Accrued Interest")
    lEODNum = lPrinBalExDefaults + lMVDefaults + lPrinProceeds
    
    Call clsWaterfall.CalcPeriod(iperiod, lICTestNum, lOCTestNum, lEODNum)
    
    If iLiquidate Then
        'Liquidation
        clsPrinProceeds(iperiod) = clsPrinProceeds(iperiod) + clsCollateralPool.Liquidate(clsCFInput("Liquidation Price"))
        clsPrinProceeds(iperiod) = clsPrinProceeds(iperiod) + clsReinvest.Liquidate(clsCFInput("Liquidation Price"))
    End If
End Sub


Public Function GetLiabDict() As Dictionary
    Set GetLiabDict = clsLiabilityDict
End Function

Public Function GetFeeDict() As Dictionary
    Set GetFeeDict = clsFeesDict
End Function
Public Function GetCollatCF() As SimpleCashflow
    Set GetCollatCF = clsCollateralPool.GetDealCF
End Function
Public Function GetICTriggers() As Dictionary
    Set GetICTriggers = clsICTriggerDict
End Function
Public Function GetOCTriggers() As Dictionary
    Set GetOCTriggers = clsOCTriggerDict
End Function
Public Function GetIcentiveFee() As IncentiveFee
    Set GetIcentiveFee = clsIncentiveFee
End Function
Public Sub LoadCLOInputs(iCLOInputs As Dictionary)
    Set clsCLOInput = iCLOInputs
End Sub
Public Sub LoadCFInputs(iCFInputs As Dictionary)
    Set clsCFInput = iCFInputs
End Sub
Public Sub LoadDealDates(iDate As DealDates)
    clsDealDate = iDate
End Sub
Public Sub LoadAccounts(IAccountsDict As Dictionary)
    Set clsAccountDict = IAccountsDict
End Sub
Public Sub LoadFees(iFeeDict As Dictionary)
    Set clsFeesDict = iFeeDict
End Sub
Public Sub LoadLiabilities(iLibal As Dictionary)
    Set clsLiabilityDict = iLibal
End Sub

Public Sub LoadICTriggers(iTrigDict As Dictionary)
    Set clsICTriggerDict = iTrigDict
End Sub
Public Sub LoadOCTriggers(iTrigDict As Dictionary)
    Set clsOCTriggerDict = iTrigDict
End Sub

Public Sub LoadIncentiveFee(iInceFee As IncentiveFee)
    Set clsIncentiveFee = iInceFee
End Sub
Public Sub LoadCollateralPool(iPool As CollateralPoolForCLO)
    Set clsCollateralPool = iPool
End Sub
Public Sub LoadYieldCurve(iYC As YieldCurve)
    Set clsYieldCurve = iYC
End Sub

Private Sub CalcConcentrationTest()
    Dim lPrincipalProceeds As Double
    
    lPrincipalProceeds = clsAccountDict(AccountType.Collection).PrincipalProceeds
    lPrincipalProceeds = lPrincipalProceeds + clsAccountDict(AccountType.RampUp).PrincipalProceeds
    'clsConcentrationTest.RunTest clsAssetsDict, lPrincipalProceeds, clsTestSetting
    'clsReRunTest = False
    
End Sub
'Public Function GetTestResult() As Results()
'    If clsReRunTest Then Call CalcConcentrationTest
'    GetTestResult = clsConcentrationTest.GetResults
'End Function

'Public Function CCC_CaaExcess() As Double
'    Dim lAssetDict As Dictionary
'    Dim lBLKRockID As Variant
'
'
'    Set lAssetDict = clsCollateralPool.GetCCCAsset
'End Function

'Public Function CalcCollateralPrincipalAmount(idate As Date)
'    Dim lNumerator As Double
'    Dim lPrincipalProceed As Double
'    lNumerator = clsCollateralPool.CollatPerfomingBalance(idate)
'    lNumerator clsAccountDict(AccountType.Collection).PrincipalProceeds
'
'End Function
Private Sub DealSetup()
    Dim lNumofPayments As Long
    Dim lKey As Variant
    Dim lLiability As Liability
    
    lNumofPayments = UBound(clsPaymentdate)
    ReDim clsIntProceeds(lNumofPayments)
    ReDim clsPrinProceeds(lNumofPayments)
    ReDim clsNotesPayable(lNumofPayments)
    ReDim clsReinvestment(lNumofPayments)
    ReDim clsLIBOR(lNumofPayments)
    
    For Each lKey In clsLiabilityDict.Keys
        Set lLiability = clsLiabilityDict(lKey)
        lLiability.DealSetup clsPaymentdate, clsCLOInput("Analysis Date"), clsYieldCurve
    Next
    For Each lKey In clsFeesDict.Keys
        clsFeesDict(lKey).DealSetup lNumofPayments, clsCLOInput("Beg Fee Basis")
    Next
    For Each lKey In clsICTriggerDict.Keys
        clsICTriggerDict(lKey).DealSetup lNumofPayments
    Next
    For Each lKey In clsOCTriggerDict.Keys
        clsOCTriggerDict(lKey).DealSetup lNumofPayments
    Next
    
    clsIncentiveFee.DealSetup lNumofPayments, clsDealDate.ClosingDate, clsCLOInput("Analysis Date")
    
    clsCollateralPool.DealSetup clsPaymentdate, clsYieldCurve
    
    Set clsReinvest = New Reinvest
    clsReinvest.DealSetup clsPaymentdate, clsReinvestInfo, clsDealDate.MonthsBetwPay, clsYieldCurve
    
    'Any money in the ramp up account place in collection account
    Dim lAmount As Double
    lAmount = clsAccountDict(AccountType.RampUp).PrincipalProceeds
    clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
    clsAccountDict(AccountType.RampUp).Add CashType.Principal, -lAmount
    clsDealName = clsCLOInput("Deal Name")

End Sub

Private Sub Rollfoward()
    Dim lKey As Variant
    
    For Each lKey In clsLiabilityDict.Keys
        clsLiabilityDict(lKey).Rollfoward
    Next
    For Each lKey In clsFeesDict.Keys
        clsFeesDict(lKey).Rollfoward
    Next
    For Each lKey In clsICTriggerDict.Keys
        clsICTriggerDict(lKey).Rollfoward
    Next
    For Each lKey In clsOCTriggerDict.Keys
        clsOCTriggerDict(lKey).Rollfoward
    Next
    
    clsIncentiveFee.Rollfoward
    
    clsCollateralPool.Rollfoward
    
    clsReinvest.Rollfoward
End Sub

'Public Sub Calc()
'    Dim i As Long
'    Dim lLibor As Double
'    Dim lLiquidate As Boolean
'
'    'Call clsWaterfall.DealSetup(clsLiabilityDict, clsOCTriggerDict, clsICTriggerDict, clsFeeDict, clsincentivvefee)
'    Call CalcPaymentDates
'    Call DealSetup
'    For i = 1 To UBound(clsPaymentdate)
'        Call CalcPeriod(i, lLiquidate)
'        If clsCLOInput("Event of Default") = True Or clsOCTriggerDict("Event of Default").PassFail = False Then
'            Call PayEODWarterfall(i)
'        Else
'            Call PayInterestWaterfall(i)
'            Call PayPrincipalWaterfall(i, lLiquidate)
'            Call PayNotePaymentSequence(i)
'            clsReinvest.AddReinvestment clsReinvestment(i)
'        End If
'        If clsLiabilityDict("Sub Notes").CurDistrPct < clsCFInput("Call when Quarterly Sub Dist <") And i < UBound(clsPaymentdate) Then
'            'Next period liquidate
'            If clsPaymentdate(i + 1).PaymentDate >= clsDealDate.NoCallDate Then
'                lLiquidate = True
'            End If
'        ElseIf i = UBound(clsPaymentdate) - 1 Then
'            'Period before Stated Maturity
'            lLiquidate = True
'        End If
'
'        If clsCollateralPool.PrinBallAllAssets + clsReinvest.PrinBallAllAssets <= 0.01 Then
'            clsLastperiod = i
'            Call Rollfoward
'            Exit For
'        Else
'            Call Rollfoward
'        End If
'    Next i
'End Sub
'Private Sub PayPrincipalWaterfall(iPeriod As Long, Optional iLquidate As Boolean)
'    Dim lPrinAmount As Double
'
'    Dim lPreviousAmount As Double
'    Dim lAmountPaid As Double
'    Dim lNotesPayable As Double
'    Dim lControllingClass As String
'    Dim lReinvestType As String
'    Dim lReinvestPCT As Double
'
'
'    lPrinAmount = clsPrinProceeds(iPeriod)
'    If clsLiabilityDict("Class A").CurrBal > 0 Then
'        lControllingClass = "Class A"
'    ElseIf clsLiabilityDict("Class B").CurrBal > 0 Then
'         lControllingClass = "Class B"
'    ElseIf clsLiabilityDict("Class C").CurrBal > 0 Then
'         lControllingClass = "Class C"
'    ElseIf clsLiabilityDict("Class D").CurrBal > 0 Then
'         lControllingClass = "Class D"
'    ElseIf clsLiabilityDict("Class E").CurrBal > 0 Then
'         lControllingClass = "Class e"
'    ElseIf clsLiabilityDict("Class F").CurrBal > 0 Then
'         lControllingClass = "Class F"
'    Else
'        lControllingClass = "Sub Notes"
'    End If
'
'    'Principal Warterfall
'
'    'Pay Trustee Fee
'    clsFeesDict("Trustee Fee").PayFee lPrinAmount
'
'    'Pay Admin Fee
'    'Dont have admin Fees
'    clsFeesDict("Admin Fee").PayFee lPrinAmount
'
'    'Pay senior Managment Fee
'    clsFeesDict("Base Manager Fee").PayFee lPrinAmount
'
'    'Pay Class A notes
'    clsLiabilityDict("Class A").PayInterest lPrinAmount
'    'Pay Class B Notes
'    clsLiabilityDict("Class B").PayInterest lPrinAmount
'    'Coverage test are done in conjuction so pay the one with the largest cure amount.
'    'If the larger cure is taken care of the secondary cure will also be solved
'    lPreviousAmount = lPrinAmount
'    If clsICTriggerDict("Class B IC Test").CureAmount > clsOCTriggerDict("Class B OC Test").PrincipalCureAmount Then
'        clsICTriggerDict("Class B IC Test").PayCure lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class B OC Test").AddPriorPrinCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class B OC Test").PayPrincipal lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
'    End If
'    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
'    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    clsOCTriggerDict("Class B OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Class C OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
'
'
'    If lControllingClass = "Class C" Then
'        'Pay Class C Notes
'        clsLiabilityDict("Class C").PayInterest lPrinAmount
'        clsLiabilityDict("Class C").PayPIKInterest lPrinAmount
'    End If
'
'    lPreviousAmount = lPrinAmount
'    If clsICTriggerDict("Class C IC Test").CureAmount > clsOCTriggerDict("Class C OC Test").PrincipalCureAmount Then
'        clsICTriggerDict("Class C IC Test").PayCure lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class C OC Test").AddPriorPrinCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class C OC Test").PayPrincipal lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
'    End If
'    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Class E OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
'
'    If lControllingClass = "Class D" Then
'        'Pay Class D Notes
'        clsLiabilityDict("Class D").PayInterest lPrinAmount
'        clsLiabilityDict("Class D").PayPIKInterest lPrinAmount
'    End If
'
'    lPreviousAmount = lPrinAmount
'    If clsICTriggerDict("Class D IC Test").CureAmount > clsOCTriggerDict("Class D OC Test").PrincipalCureAmount Then
'        clsICTriggerDict("Class D IC Test").PayCure lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class D OC Test").AddPriorPrinCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class D OC Test").PayPrincipal lPrinAmount
'        lAmountPaid = lPreviousAmount - lPrinAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    End If
'    clsOCTriggerDict("Class E OC Test").AddPriorPrinCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
'
'     If lControllingClass = "Class E" Then
'        'Pay Class E Notes
'        clsLiabilityDict("Class E").PayInterest lPrinAmount
'        clsLiabilityDict("Class E").PayPIKInterest lPrinAmount
'    End If
'
'    lPreviousAmount = lPrinAmount
'    clsOCTriggerDict("Class E OC Test").PayPrincipal lPrinAmount
'    lAmountPaid = lPreviousAmount - lPrinAmount
'    clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorPrinCure lAmountPaid
'
'    If lControllingClass = "Class F" Then
'        'Pay Class F Notes
'        clsLiabilityDict("Class F").PayInterest lPrinAmount
'        clsLiabilityDict("Class F").PayPIKInterest lPrinAmount
'    End If
'
'
'    If iLquidate Then
'        lReinvestType = "None"
'        lReinvestPCT = 0
'    ElseIf clsPaymentdate(iPeriod).PaymentDate <= clsDealDate.ReinvestDate Then
'        lReinvestType = clsReinvestInfo.PreReinvType
'        lReinvestPCT = clsReinvestInfo.PreRinvestPct
'    ElseIf clsPaymentdate(iPeriod).PaymentDate < clsDealDate.MatDate Then
'        lReinvestType = clsReinvestInfo.PostReinvType
'        lReinvestPCT = clsReinvestInfo.PostReinvestPct
'    End If
'    Select Case UCase(lReinvestType)
'
'    Case "ALL PRINCIPAL"
'        lAmountPaid = lPrinAmount
'    Case "UNSCHEDULED PRINCIPAL"
'        lAmountPaid = clsCollateralPool.UnSchedPrin + clsReinvest.UnSchedPrin
'    Case Else
'        lAmountPaid = 0
'    End Select
'    lAmountPaid = lAmountPaid * lReinvestPCT
'
'    If lAmountPaid > lPrinAmount Then lAmountPaid = lPrinAmount
'    clsReinvestment(iPeriod) = clsReinvestment(iPeriod) + lAmountPaid
'    lPrinAmount = lPrinAmount - lAmountPaid
'
'    clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lPrinAmount
'    lPrinAmount = 0
'End Sub
'Private Sub PayInterestWaterfall(iPeriod As Long)
'    Dim lIntAmount As Double
'    Dim lPrinAmount As Double
'
'    Dim lPreviousAmount As Double
'    Dim lAmountPaid As Double
'    Dim lNotesPayable As Double
'
'    lIntAmount = clsIntProceeds(iPeriod)
'
'
'    'Interest waterfall
'
'    'Pay Trustee Fee
'    clsFeesDict("Trustee Fee").PayFee lIntAmount
'
'    'Pay Admin Fee
'    'Dont have admin Fees
'    clsFeesDict("Admin Fee").PayFee lIntAmount
'
'    'Pay senior Managment Fee
'    clsFeesDict("Base Manager Fee").PayFee lIntAmount
'
'    'Pay Class A notes
'    clsLiabilityDict("Class A").PayInterest lIntAmount
'    'Pay Class B Notes
'    clsLiabilityDict("Class B").PayInterest lIntAmount
'    'Coverage test are done in conjuction so pay the one with the largest cure amount.
'    'If the larger cure is taken care of the secondary cure will also be solved
'    lPreviousAmount = lIntAmount
'    If clsICTriggerDict("Class B IC Test").CureAmount > clsOCTriggerDict("Class B OC Test").InterestCureAmount Then
'        clsICTriggerDict("Class B IC Test").PayCure lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class B OC Test").AddPriorIntCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class B OC Test").PayInterest lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class B IC Test").AddPriorCure lAmountPaid
'    End If
'    clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
'    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    clsOCTriggerDict("Class B OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Class C OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
'
'
'
'
'    'Pay Class C Notes
'    clsLiabilityDict("Class C").PayInterest lIntAmount
'    clsLiabilityDict("Class C").PayPIKInterest lIntAmount
'
'    lPreviousAmount = lIntAmount
'    If clsICTriggerDict("Class C IC Test").CureAmount > clsOCTriggerDict("Class C OC Test").InterestCureAmount Then
'        clsICTriggerDict("Class C IC Test").PayCure lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class C OC Test").AddPriorIntCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class C OC Test").PayInterest lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class C IC Test").AddPriorCure lAmountPaid
'    End If
'    clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Class E OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
'
'    'Pay Class D Notes
'    clsLiabilityDict("Class D").PayInterest lIntAmount
'    clsLiabilityDict("Class D").PayPIKInterest lIntAmount
'    lPreviousAmount = lIntAmount
'    If clsICTriggerDict("Class D IC Test").CureAmount > clsOCTriggerDict("Class D OC Test").InterestCureAmount Then
'        clsICTriggerDict("Class D IC Test").PayCure lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsOCTriggerDict("Class D OC Test").AddPriorIntCure lAmountPaid
'    Else
'        clsOCTriggerDict("Class D OC Test").PayInterest lIntAmount
'        lAmountPaid = lPreviousAmount - lIntAmount
'        clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'        clsICTriggerDict("Class D IC Test").AddPriorCure lAmountPaid
'    End If
'    clsOCTriggerDict("Class E OC Test").AddPriorIntCure lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
'
'    'Pay Class E Notes
'    clsLiabilityDict("Class E").PayInterest lIntAmount
'    clsLiabilityDict("Class E").PayPIKInterest lIntAmount
'
'    lPreviousAmount = lIntAmount
'    clsOCTriggerDict("Class E OC Test").PayInterest lIntAmount
'    lAmountPaid = lPreviousAmount - lIntAmount
'    clsNotesPayable(iPeriod) = clsNotesPayable(iPeriod) + lAmountPaid
'    clsOCTriggerDict("Interest Diversion Test").AddPriorIntCure lAmountPaid
'
'    'Pay Class F Notes
'    clsLiabilityDict("Class F").PayInterest lIntAmount
'    clsLiabilityDict("Class F").PayPIKInterest lIntAmount
'
'
'    'Will ignore the the Moody;s Rating Test. Will assume it is satisfied.
'
'    If clsPaymentdate(iPeriod).PaymentDate <= clsDealDate.ReinvestDate Then
'        'Interest Diversion
'        If clsOCTriggerDict("Interest Diversion Test").PassFail = False Then
'            If clsOCTriggerDict("Interest Diversion Test").InterestCureAmount > 0.5 * lIntAmount Then
'                clsPrinProceeds(iPeriod) = clsPrinProceeds(iPeriod) + 0.5 * lIntAmount
'                lIntAmount = 0.5 * lIntAmount
'            Else
'                clsPrinProceeds(iPeriod) = clsPrinProceeds(iPeriod) + clsOCTriggerDict("Interest Diversion Test").InterestCureAmount
'                lIntAmount = lIntAmount - clsOCTriggerDict("Interest Diversion Test").InterestCureAmount
'            End If
'        End If
'    End If
'
'    'sub Management fee
'    clsFeesDict("Junior Manager Fee").PayFee lIntAmount
'
'    'Assuming no administrative fees
'
'    'Incentive Fee
'    If clsIncentiveFee.IncentiveFeeThreshold > lIntAmount Then
'        clsIncentiveFee.PaymentToSubNotholder lIntAmount
'        clsLiabilityDict("Sub Notes").PayInterest lIntAmount
'    Else
'        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
'        lIntAmount = lIntAmount - lAmountPaid
'        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
'        clsLiabilityDict("Sub Notes").PayInterest lAmountPaid
'    End If
'
'    clsIncentiveFee.PayIncentiveFee lIntAmount
'    clsIncentiveFee.PaymentToSubNotholder lIntAmount
'    clsLiabilityDict("Sub Notes").PayInterest lIntAmount
'
'
'
'
'End Sub
'Private Sub PayNotePaymentSequence(iPeriod As Long)
'    Dim lPayableAmount As Double
'    Dim lAmountPaid As Double
'
'    lPayableAmount = clsNotesPayable(iPeriod)
'    clsLiabilityDict("Class A").PayPrincipal lPayableAmount
'    clsLiabilityDict("Class B").PayPrincipal lPayableAmount
'    clsLiabilityDict("Class C").PayPIKInterest lPayableAmount
'    clsLiabilityDict("Class C").PayPrincipal lPayableAmount
'    clsLiabilityDict("Class D").PayPIKInterest lPayableAmount
'    clsLiabilityDict("Class D").PayPrincipal lPayableAmount
'    clsLiabilityDict("Class E").PayPIKInterest lPayableAmount
'    clsLiabilityDict("Class E").PayPrincipal lPayableAmount
'    clsLiabilityDict("Class F").PayPIKInterest lPayableAmount
'    clsLiabilityDict("Class F").PayPrincipal lPayableAmount
'        'sub Management fee
'    clsFeesDict("Junior Manager Fee").PayFee lPayableAmount
'
'    'Assuming no administrative fees
'
'    'Incentive Fee
'    If clsIncentiveFee.IncentiveFeeThreshold > lPayableAmount Then
'        clsIncentiveFee.PaymentToSubNotholder lPayableAmount
'        clsLiabilityDict("Sub Notes").PayPrincipal lPayableAmount
'    Else
'        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
'        lPayableAmount = lPayableAmount - lAmountPaid
'        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
'        clsLiabilityDict("Sub Notes").PayPrincipal lAmountPaid
'    End If
'
'    clsIncentiveFee.PayIncentiveFee lPayableAmount
'    clsIncentiveFee.PaymentToSubNotholder lPayableAmount
'    clsLiabilityDict("Sub Notes").PayPrincipal lPayableAmount
'
'
'
'End Sub
'Private Sub PayEODWarterfall(iPeriod As Long)
'    Dim lTotalProceeds As Double
'    Dim lPrinAmount As Double
'    Dim lIntAmount As Double
'    Dim lAmountPaid As Double
'
'    'lTotalProceeds= clsAccountDict(AccountType.Collection).Add CashType.Principal, -lPrinAmount
'
'    lPrinAmount = clsPrinProceeds(iPeriod)
'    lIntAmount = clsIntProceeds(iPeriod)
'
'
'    lTotalProceeds = lPrinAmount + lIntAmount
'
'    'No admin Fee
'    'Pay Trustee
'    'Pay Trustee Fee
'    clsFeesDict("Trustee Fee").PayFee lTotalProceeds
'    clsFeesDict("Admin Fee").PayFee lTotalProceeds
'    clsFeesDict("Base Manager Fee").PayFee lTotalProceeds
'    clsLiabilityDict("Class A").PayInterest lTotalProceeds
'    clsLiabilityDict("Class A").PayPrincipal lTotalProceeds
'    clsLiabilityDict("Class B").PayInterest lTotalProceeds
'    clsLiabilityDict("Class B").PayPrincipal lTotalProceeds
'    clsLiabilityDict("Class C").PayInterest lTotalProceeds
'    clsLiabilityDict("Class C").PayPIKInterest lTotalProceeds
'    clsLiabilityDict("Class C").PayPrincipal lTotalProceeds
'    clsLiabilityDict("Class D").PayInterest lTotalProceeds
'    clsLiabilityDict("Class D").PayPIKInterest lTotalProceeds
'    clsLiabilityDict("Class D").PayPrincipal lTotalProceeds
'    clsLiabilityDict("Class E").PayInterest lTotalProceeds
'    clsLiabilityDict("Class E").PayPIKInterest lTotalProceeds
'    clsLiabilityDict("Class E").PayPrincipal lTotalProceeds
'    clsLiabilityDict("Class F").PayInterest lTotalProceeds
'    clsLiabilityDict("Class F").PayPIKInterest lTotalProceeds
'    clsLiabilityDict("Class F").PayPrincipal lTotalProceeds
'
'    clsFeesDict("Junior Manager Fee").PayFee lTotalProceeds
'
'    'Assuming no administrative fees
'
'    'Incentive Fee
'    If clsIncentiveFee.IncentiveFeeThreshold > lTotalProceeds Then
'        clsIncentiveFee.PaymentToSubNotholder lTotalProceeds
'        clsLiabilityDict("Sub Notes").PayPrincipal lTotalProceeds
'    Else
'        lAmountPaid = clsIncentiveFee.IncentiveFeeThreshold
'        lTotalProceeds = lTotalProceeds - lAmountPaid
'        clsIncentiveFee.PaymentToSubNotholder lAmountPaid
'        clsLiabilityDict("Sub Notes").PayPrincipal lAmountPaid
'    End If
'
'    clsIncentiveFee.PayIncentiveFee lTotalProceeds
'    clsIncentiveFee.PaymentToSubNotholder lTotalProceeds
'    clsLiabilityDict("Sub Notes").PayPrincipal lTotalProceeds
'
'
'
'End Sub
'Private Sub CalcPeriod(iPeriod As Long, Optional iLiquidate As Boolean)
'    '1. Deposit interest and proceeds into collection account.
'    '2. Calc Liabilities
'    '3. Calc Inputs
'        'a. Fee Basis Amount
'        'b. Event of Default Numerator
'        'c. Adjusted Collateral Principal amount
'
'    Dim lLastPay As Date
'    Dim lNextPay As Date
'    Dim lBegColl As Date
'    Dim lEndColl As Date
'    Dim lAmount As Double
'    Dim lLibor As Double
'
'    lLastPay = clsPaymentdate(iPeriod - 1).PaymentDate
'    If lLastPay = 0 Then lLastPay = clsDealDate.ClosingDate
'    lNextPay = clsPaymentdate(iPeriod).PaymentDate
'    lBegColl = clsPaymentdate(iPeriod).CollBegDate
'    lEndColl = clsPaymentdate(iPeriod).CollEndDate
'    If iPeriod = 1 Then
'        lLibor = clsCLOInput("Current LIBOR")
'    Else
'        lLibor = clsYieldCurve.SpotRate(clsPaymentdate(iPeriod).IntDeterDate, clsDealDate.MonthsBetwPay)
'    End If
'
'
'    clsLIBOR(iPeriod) = lLibor
'
'    'Add cash to the collection account
'    lAmount = clsCollateralPool.GetProceeds("INTEREST") + clsReinvest.GetProceeds("INTEREST")
'    clsAccountDict(AccountType.Collection).Add CashType.Interest, lAmount
'
'    lAmount = clsCollateralPool.GetProceeds("PRINCIPAL") + clsReinvest.GetProceeds("PRINCIPAL")
'    clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
'
'
'    lAmount = clsCLOInput("Purchase Finance Accrued Interest")
'    If clsAccountDict(AccountType.Collection).InterestProceeds > lAmount Then
'        clsAccountDict(AccountType.Collection).Add CashType.Interest, -lAmount
'        clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
'        clsCLOInput("Purchase Finance Accrued Interest") = 0
'    Else
'        lAmount = clsAccountDict(AccountType.Collection).InterestProceeds
'        clsAccountDict(AccountType.Collection).Add CashType.Interest, -lAmount
'        clsAccountDict(AccountType.Collection).Add CashType.Principal, lAmount
'        clsCLOInput("Purchase Finance Accrued Interest") = clsCLOInput("Purchase Finance Accrued Interest") - lAmount
'    End If
'
'    'Calc  Liabilitis
'    Dim lKey As Variant
'    For Each lKey In clsLiabilityDict.Keys
'        clsLiabilityDict(lKey).Calc lLibor, lLastPay, lNextPay
'    Next
'
'    'CalcFeeeBais
'    Dim lFeeBasis As Double
'    Dim lPrinBalAllAssets As Double
'    Dim lPrinBalExDefaults As Double
'    Dim lPrinBalDefauts As Double
'    Dim lMVDefaults As Double
'    Dim lIntProceeds As Double
'    Dim lPrinProceeds As Double
'    Dim lCCCCaaAdj As Double
'    Dim lWithdrawl As Double
'
'    lWithdrawl = clsAccountDict(AccountType.Collection).InterestProceeds
'    clsAccountDict(AccountType.Collection).Add CashType.Interest, -lWithdrawl
'    lIntProceeds = lWithdrawl
'
'    lWithdrawl = clsAccountDict(AccountType.Collection).PrincipalProceeds
'    clsAccountDict(AccountType.Collection).Add CashType.Principal, -lWithdrawl
'    lPrinProceeds = lWithdrawl
'
'    lWithdrawl = clsAccountDict(AccountType.InterestReserve).PrincipalProceeds
'    clsAccountDict(AccountType.InterestReserve).Add CashType.Principal, -lWithdrawl
'
'    lIntProceeds = lIntProceeds + lWithdrawl
'
'    clsIntProceeds(iPeriod) = lIntProceeds
'    clsPrinProceeds(iPeriod) = lPrinProceeds
'
'    lPrinBalAllAssets = clsCollateralPool.PrinBallAllAssets + clsReinvest.PrinBallAllAssets
'    lPrinBalExDefaults = clsCollateralPool.PrinBallExDefaults + clsReinvest.PrinBallExDefaults
'    lPrinBalDefauts = clsCollateralPool.PrinBallDefaults + clsReinvest.PrinBallDefaults
'    lMVDefaults = clsCollateralPool.MVDefaults + clsReinvest.PrinBallDefaults
'    lCCCCaaAdj = clsCollateralPool.CalcCCCExcessAdjustment(lPrinBalExDefaults + lPrinProceeds, clsCLOInput("CCC Asset Haircut Percent"), lEndColl, clsCFInput("CCC Liquidation Price"))
'
'
'    lFeeBasis = lPrinBalAllAssets + lPrinProceeds + clsCLOInput("Purchase Finance Accrued Interest")
'    For Each lKey In clsFeesDict.Keys
'        clsFeesDict(lKey).Calc lLastPay, lNextPay, lFeeBasis, lLibor
'    Next
'    clsIncentiveFee.Calc lNextPay
'
'    Dim lOCTestNum As Double
'    Dim lICTestNum As Double
'    Dim lEODNuum As Double
'    Dim lClassABICDen As Double
'    Dim lClassABOCDen As Double
'    Dim lClassCICDen As Double
'    Dim lClassDICDen As Double
'    Dim lClassCOCDen As Double
'    Dim lClassDOCDen As Double
'    Dim lClassEOCDen As Double
'    Dim lIDDen As Double
'    Dim lEODDen As Double
'
'    lICTestNum = lIntProceeds
'    lICTestNum = lICTestNum - clsFeesDict("Trustee Fee").FeeAccrued - clsFeesDict("Base Manager Fee").FeeAccrued
'    lOCTestNum = lPrinBalExDefaults + lMVDefaults - lCCCCaaAdj + lPrinProceeds + clsCLOInput("Purchase Finance Accrued Interest")
'    lEODNuum = lPrinBalExDefaults + lMVDefaults + lPrinProceeds
'
'    For Each lKey In clsLiabilityDict.Keys
'        Select Case lKey
'
'        Case "Class A"
'            lEODDen = clsLiabilityDict(lKey).CurrBal
'            lClassABICDen = lClassABICDen + clsLiabilityDict(lKey).IntDue
'            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
'            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
'            lClassABOCDen = lClassABOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        Case "Class B"
'            lClassABICDen = lClassABICDen + clsLiabilityDict(lKey).IntDue
'            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
'            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
'            lClassABOCDen = lClassABOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        Case "Class C"
'            lClassCICDen = lClassCICDen + clsLiabilityDict(lKey).IntDue
'            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
'            lClassCOCDen = lClassCOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        Case "Class D"
'            lClassDICDen = lClassDICDen + clsLiabilityDict(lKey).IntDue
'            lClassDOCDen = lClassDOCDen + clsLiabilityDict(lKey).CurrBal
'            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        Case "Class E"
'            lClassEOCDen = lClassEOCDen + clsLiabilityDict(lKey).CurrBal
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        Case "Class F"
'            lIDDen = lIDDen + clsLiabilityDict(lKey).CurrBal
'        End Select
'    Next
'
'    For Each lKey In clsICTriggerDict.Keys
'        Select Case lKey
'
'        Case "Class B IC Test"
'           clsICTriggerDict(lKey).Calc lICTestNum, lClassABICDen, lClassABOCDen
'
'        Case "Class C IC Test"
'            clsICTriggerDict(lKey).Calc lICTestNum, lClassCICDen, lClassCOCDen
'
'        Case "Class D IC Test"
'            clsICTriggerDict(lKey).Calc lICTestNum, lClassDICDen, lClassDOCDen
'        End Select
'    Next
'
'    For Each lKey In clsOCTriggerDict.Keys
'        Select Case lKey
'
'        Case "Class B OC Test"
'            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassABOCDen
'        Case "Class C OC Test"
'            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassCOCDen
'        Case "Class D OC Test"
'            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassDOCDen
'        Case "Class E OC Test"
'            clsOCTriggerDict(lKey).Calc lOCTestNum, lClassDOCDen
'        Case "Interest Diversion Test"
'            clsOCTriggerDict(lKey).Calc lOCTestNum, lIDDen
'        Case "Event of Default"
'            clsOCTriggerDict(lKey).Calc lEODNuum, lEODDen
'        End Select
'    Next
'
'    If iLiquidate Then
'        'Liquidation
'        clsPrinProceeds(iPeriod) = clsPrinProceeds(iPeriod) + clsCollateralPool.Liquidate(clsCFInput("Liquidation Price"))
'        clsPrinProceeds(iPeriod) = clsPrinProceeds(iPeriod) + clsReinvest.Liquidate(clsCFInput("Liquidation Price"))
'
'    End If
'
'
'
'End Sub
