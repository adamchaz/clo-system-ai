VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Asset"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit


Private clsBlkRockID As String
Private clsIssueName As String
Private clsIndex As String
Private clsCoupon As Double
Private clsUnfundedAmount As Double
Private clsPIKing As Boolean
Private clsPIKAmount As Double
Private clsIssuerName As String
Private clsIssuerID As String
Private clsTranche As String
Private clsBondLoan As String
Private clsMaturity As Date
Private clsCouponType As String
Private clsPaymentFreq As Long
Private clsCpnSpread As Double
Private clsLiborFloor As Double
Private clsCommitFee As Double
Private clsFacilitySize As Double
Private clsMDYIndustry As String
Private clsSPIndustry As String
Private clsCountry As String
Private clsSeniority As String
Private clsPikAsset As Boolean
Private clsDefaultAsset As Boolean
Private clsDateofDefault As Date
Private clsDelayDrawdown As Boolean
Private clsRevolver As Boolean
Private clsLOC As Boolean 'Letter of Credit
Private clsParticipation As Boolean
Private clsDIP As Boolean
Private clsConveritable As Boolean
Private clsStructFinance As Boolean
Private clsBridgeLoan As Boolean
Private clsCurrentPay As Boolean
Private clsCovLite As Boolean
Private clsCurrency As String
Private clsWAL As Double
Private clsMarketValue As Double
Private clsFLLO As Boolean 'First Lien Last Out
Private clsMDYRating As String
Private clsMDYDPRating As String
Private clsMDYDPRatingWARF As String
Private clsMDYRecoveryRate As Double
Private clsSPRating As String
Private clsParAmount As Double
Private clsMDYFacilityRating As String
Private clsMDYFacilityOutlook As String
Private clsMDYIssuerRating As String
Private clsMDYIssuerOutlook As String
Private clsMDYSnrSecRating As String
Private clsMDYSNRUnSecRating As String
Private clsMDYSubRating As String
Private clsMDYCreditEstRating As String
Private clsMDYCreditEstDate As Date
Private clsSandPFacilityRating As String
Private clsSandPIssuerRating As String
Private clsSandPSnrSecRating As String
Private clsSandPSubordinate As String
Private clsSPPriorityCategory As String
Private clsMDYAssetCategory As String
Private clsSandPRecRating As String

'CAshflow variables

Private clsDatedDate As Date
Private clsIssueDate As Date
Private clsFirstPaymentDate As Date
Private clsAmType As String
Private clsDayCount As String
Private clsIndexCap As Double
Private clsBussDayConv As String
Private clsPmtEOM As Boolean
Private clsAmtIssued As Double
Private clsSchedDict As Dictionary


'Assumption variables
Private clsPrePayRate As Variant
Private clsDefaultRate As Variant
Private clsSeverity As Variant
Private clsLag As Double
Private clsCF As SimpleCashflow
Private clsUseRM As Boolean

'Calculated on Initialization
Private clsConstructorCalled As Boolean

Private clsAnalystOpinion As String

'Cashflow Calculations
Private clsMonthsbetweenpayments As Long  '
Private clsPaymentsPerYear As Long
Private clsDayCountEnum As Long
Private clsPaymentDates As Dictionary
Private clsIntPaymentDates As Dictionary
Private clsSPRatingHistDict As Dictionary
Private clsMoodyRatingHistDict As Dictionary

'Control Variable for moody and s&P rating. Way too much time is use sorting dictionaries. I don't need this in my life.
Private clsSortMoodys As Boolean
Private clsSortSP As Boolean


Public Property Get UseRM() As Boolean
    UseRM = clsUseRM
End Property
Public Property Let UseRM(iValue As Boolean)
    clsUseRM = iValue
End Property


Public Property Get DatedDate() As Date
    DatedDate = clsDatedDate
End Property

Public Property Get IssueDate() As Date
    IssueDate = clsIssueDate
End Property
Public Property Get FirstPaymentDate() As Date
    FirstPaymentDate = clsFirstPaymentDate
End Property



Public Property Get AmortizationType() As String
    AmortizationType = clsAmType
End Property

Public Property Get DayCount() As String
    DayCount = clsDayCount
End Property

Public Property Get AnalystOpinion() As String
    AnalystOpinion = clsAnalystOpinion
End Property


Public Property Get IndexCap() As Double
    IndexCap = clsIndexCap
End Property
Public Property Get BusinessDayConv() As String
    BusinessDayConv = clsBussDayConv
End Property

Public Property Get PaymentEOMFlag() As String
    PaymentEOMFlag = clsPmtEOM
End Property

Public Property Get AmountIssued() As Double
    AmountIssued = clsAmtIssued
End Property



Public Property Get Index() As String
    Index = clsIndex
End Property

Public Property Get Coupon() As Double
    Coupon = clsCoupon
End Property
Public Property Get UnfundedAmount() As Double
    UnfundedAmount = clsUnfundedAmount
End Property
Public Property Get PIKing() As Boolean
    PIKing = clsPIKing
End Property
Public Property Get PIKAmount() As Double
    PIKAmount = clsPIKAmount
End Property
Public Property Get BLKRockID() As String
    BLKRockID = clsBlkRockID
End Property
Public Property Get IssueName() As String
    IssueName = clsIssueName
End Property
Public Property Get IssuerName() As String
    IssuerName = clsIssuerName
End Property
Public Property Get IssuerId() As String
    IssuerId = clsIssuerID
End Property
Public Property Get Tranche() As String
    Tranche = clsTranche
End Property
Public Property Get BondLoan() As String
    BondLoan = clsBondLoan
End Property
Public Property Get Maturity() As Date
    Maturity = clsMaturity
End Property
Public Property Get CouponType() As String
    CouponType = clsCouponType
End Property
Public Property Get PaymentFreq() As String
    PaymentFreq = clsPaymentFreq
End Property
Public Property Get CpnSpread() As Double
    CpnSpread = clsCpnSpread
End Property
Public Property Get LiborFloor() As Double
    LiborFloor = clsLiborFloor
End Property
Public Property Get CommitFee() As Double
    CommitFee = clsCommitFee
End Property
Public Property Get FacilitySize() As Double
    FacilitySize = clsFacilitySize
End Property
Public Property Get MDYIndustry() As String
    MDYIndustry = clsMDYIndustry
End Property
Public Property Get MDYAssetCategory() As String
    MDYAssetCategory = clsMDYAssetCategory
End Property
Public Property Get SPPriorityCategory() As String
    SPPriorityCategory = clsSPPriorityCategory
End Property
Public Property Get SPIndustry() As String
    SPIndustry = clsSPIndustry
End Property
Public Property Get Country() As String
    Country = clsCountry
End Property
Public Property Get Seniority() As String
    Seniority = clsSeniority
End Property
Public Property Get PikAsset() As Boolean
    PikAsset = clsPikAsset
End Property
Public Property Get DefaultAsset() As Boolean
    DefaultAsset = clsDefaultAsset
End Property
Public Property Get DateofDefault() As Date
    DateofDefault = clsDateofDefault
End Property
Public Property Get DelayDrawdown() As Boolean
    DelayDrawdown = clsDelayDrawdown
End Property
Public Property Get Revolver() As Boolean
    Revolver = clsRevolver
End Property
Public Property Get LOC() As Boolean
    LOC = clsLOC
End Property
Public Property Get Participation() As Boolean
    Participation = clsParticipation
End Property
Public Property Get DIP() As Boolean
    DIP = clsDIP
End Property
Public Property Get Converitable() As Boolean
    Converitable = clsConveritable
End Property
Public Property Get StructFinance() As Boolean
    StructFinance = clsStructFinance
End Property
Public Property Get BridgeLoan() As Boolean
    BridgeLoan = clsBridgeLoan
End Property
Public Property Get CurrentPay() As Boolean
    CurrentPay = clsCurrentPay
End Property
Public Property Get CovLite() As Boolean
    CovLite = clsCovLite
End Property
Public Property Get AssetCurrency() As String
    AssetCurrency = clsCurrency
End Property
Public Property Get WAL() As String
    WAL = clsWAL
End Property
Public Property Get MarketValue() As Double
    MarketValue = clsMarketValue
End Property
Public Property Get FLLO() As Double
    FLLO = clsFLLO
End Property
Public Property Get MDYRating() As String
    MDYRating = clsMDYRating
End Property
Public Property Let MDYRating(iRating As String)
    clsMDYRating = iRating
End Property
Public Property Let MDYDPRating(iRating As String)
    clsMDYDPRating = iRating
End Property

Public Property Get MDYDPRating() As String
    MDYDPRating = clsMDYDPRating
End Property


Public Property Let MDYDPRatingWARF(iRating As String)
    clsMDYDPRatingWARF = iRating
End Property

Public Property Get MDYDPRatingWARF() As String
    MDYDPRatingWARF = clsMDYDPRatingWARF
End Property

Public Property Get MDYRecoveryRate() As Double
    MDYRecoveryRate = clsMDYRecoveryRate
End Property
Public Property Let MDYRecoveryRate(iRate As Double)
    clsMDYRecoveryRate = iRate
End Property
Public Property Get SPRating() As String
    SPRating = clsSPRating
End Property
Public Property Let SPRating(iValue As String)
     clsSPRating = iValue
End Property
Public Property Get ParAmount() As Double
    ParAmount = clsParAmount
End Property
Public Property Get MDYFacilityRating() As String
    MDYFacilityRating = clsMDYFacilityRating
End Property
Public Property Get MDYFacilityOutlook() As String
    MDYFacilityOutlook = clsMDYFacilityOutlook
End Property
Public Property Get MDYIssuerRating() As String
    MDYIssuerRating = clsMDYIssuerRating
End Property
Public Property Get MDYIssuerOutlook() As String
    MDYIssuerOutlook = clsMDYIssuerOutlook
End Property
Public Property Get MDYSnrSecRating() As String
    MDYSnrSecRating = clsMDYSnrSecRating
End Property
Public Property Get MDYSNRUnSecRating() As String
    MDYSNRUnSecRating = clsMDYSNRUnSecRating
End Property
Public Property Get MDYSubRating() As String
    MDYSubRating = clsMDYSubRating
End Property
Public Property Get MDYCreditEstRating() As String
    MDYCreditEstRating = clsMDYCreditEstRating
End Property
Public Property Get MDYCreditEstDate() As Date
    MDYCreditEstDate = clsMDYCreditEstDate
End Property
Public Property Get SandPFacilityRating() As String
    SandPFacilityRating = clsSandPFacilityRating
End Property
Public Property Get SandPIssuerRating() As String
    SandPIssuerRating = clsSandPIssuerRating
End Property
Public Property Get SandPSnrSecRating() As String
    SandPSnrSecRating = clsSandPSnrSecRating
End Property
Public Property Get SandPSubordinate() As String
    SandPSubordinate = clsSandPSubordinate
End Property
Public Property Get SandPRecRating() As String
    SandPRecRating = clsSandPRecRating
End Property
Public Sub AddPar(iParAmount As Double)
    clsParAmount = clsParAmount + iParAmount
    If clsParAmount < 0 Then clsParAmount = 0  'Par amount of a loan can't be less than zero
End Sub

Public Sub UpdatePar(iParAmount As Double)
    'This subroutine replaces the current par amount.
    If iParAmount >= 0 Then
        clsParAmount = iParAmount
    Else
        clsParAmount = 0
    End If
    
End Sub

Public Sub AddAsset(iAssetUDT As AssetUDT, Optional iPrinSched As Dictionary, Optional iRunCF As Boolean)

    With iAssetUDT
        clsBlkRockID = .BLKRockID
        clsIssueName = .IssueName
        clsIssuerName = .IssuerName
        clsIssuerID = .IssuerId
        clsTranche = .Tranche
        clsBondLoan = .BondLoan
        clsMaturity = .Maturity
        clsCouponType = .CouponType
        clsPaymentFreq = .PaymentFreq
        clsCpnSpread = .CpnSpread
        clsLiborFloor = .LiborFloor
        clsCommitFee = .CommitFee
        clsFacilitySize = .FacilitySize
        clsMDYIndustry = .MDYIndustry
        clsSPIndustry = .SPIndustry
        clsCountry = .Country
        clsSeniority = .Seniority
        clsPikAsset = .PikAsset
        clsDefaultAsset = .DefaultAsset
        clsDateofDefault = .DateofDefault
        clsDelayDrawdown = .DelayDrawdown
        clsRevolver = .Revolver
        clsLOC = .LOC
        clsParticipation = .Participation
        clsDIP = .DIP
        clsConveritable = .Converitable
        clsStructFinance = .StructFinance
        clsBridgeLoan = .BridgeLoan
        clsCurrentPay = .CurrentPay
        clsCovLite = .CovLite
        clsCurrency = .Currency
        clsWAL = .WAL
        clsMarketValue = .MarketValue
        clsFLLO = .FLLO
        clsMDYRating = .MDYRating
        clsMDYDPRating = .MDYDPRating
        clsMDYRecoveryRate = .MDYRecoveryRate
        clsMDYDPRatingWARF = .MDYDPRatingWARF
        clsSPRating = .SPRating
        clsParAmount = .ParAmount
        clsIndex = .Index
        clsCoupon = .Coupon
        clsUnfundedAmount = .UnfundedAmount
        clsPIKing = .PIKing
        clsPIKAmount = .PIKAmount
        clsMDYFacilityRating = .MDYFacilityRating
        clsMDYFacilityOutlook = .MDYFacilityOutlook
        clsMDYIssuerRating = .MDYIssuerRating
        clsMDYIssuerOutlook = .MDYIssuerOutlook
        clsMDYSnrSecRating = .MDYSnrSecRating
        clsMDYSNRUnSecRating = .MDYSNRUnSecRating
        clsMDYSubRating = .MDYSubRating
        clsMDYCreditEstRating = .MDYCreditEstRating
        clsMDYCreditEstDate = .MDYCreditEstDate
        clsSandPFacilityRating = .SandPFacilityRating
        clsSandPIssuerRating = .SandPIssuerRating
        clsSandPSnrSecRating = .SandPSnrSecRating
        clsSandPSubordinate = .SandPSubordinate
        clsSandPRecRating = .SandPRecRating
        
        clsDatedDate = .DatedDate
        clsIssueDate = .IssueDate
        clsFirstPaymentDate = .FirstPaymentDate
        clsAmType = .AmortizationType
        clsDayCount = .DayCount
        clsIndexCap = .LiborFloor
        clsBussDayConv = .BusinessDayConvention
        clsPmtEOM = .EOMFlag
        clsAmtIssued = .AmtIssued
        clsPrePayRate = .PrePayRate
        clsDefaultRate = .DefaultRate
        clsSeverity = .Severity
        clsLag = .Lag
        clsMDYAssetCategory = .MDYAssetCategory
        clsSPPriorityCategory = .SPPriorityCategory
        clsAnalystOpinion = .AnalystOpinion
        Set clsSchedDict = iPrinSched
    End With
    If clsSchedDict Is Nothing Then
        Set clsSchedDict = New Dictionary
        clsSchedDict.Add clsMaturity, 1
    End If
    
    Call SetLoanConstant
    Call CalcPaymentDates
End Sub

Public Function Copy() As Asset
    Dim lAsset As Asset
    Dim lAssetUDT As AssetUDT
    Dim lPaySched As Dictionary
    Dim i As Long
    Set lAsset = New Asset
    
    With lAssetUDT
     .BLKRockID = clsBlkRockID
     .IssueName = clsIssueName
     .IssuerName = clsIssuerName
     .IssuerId = clsIssuerID
     .Tranche = clsTranche
     .BondLoan = clsBondLoan
     .Maturity = clsMaturity
     .CouponType = clsCouponType
     .PaymentFreq = clsPaymentFreq
     .CpnSpread = clsCpnSpread
     .LiborFloor = clsLiborFloor
     .CommitFee = clsCommitFee
     .FacilitySize = clsFacilitySize
     .MDYIndustry = clsMDYIndustry
     .SPIndustry = clsSPIndustry
     .Country = clsCountry
     .Seniority = clsSeniority
     .PikAsset = clsPikAsset
     .DefaultAsset = clsDefaultAsset
     .DateofDefault = clsDateofDefault
     .DelayDrawdown = clsDelayDrawdown
     .Revolver = clsRevolver
     .LOC = clsLOC
     .Participation = clsParticipation
     .DIP = clsDIP
     .Converitable = clsConveritable
     .StructFinance = clsStructFinance
     .BridgeLoan = clsBridgeLoan
     .CurrentPay = clsCurrentPay
     .CovLite = clsCovLite
     .Currency = clsCurrency
     .WAL = clsWAL
     .MarketValue = clsMarketValue
     .FLLO = clsFLLO
     .MDYRating = clsMDYRating
     .MDYDPRating = clsMDYDPRating
     .MDYRecoveryRate = clsMDYRecoveryRate
     .SPRating = clsSPRating
     .ParAmount = clsParAmount
     .Index = clsIndex
     .Coupon = clsCoupon
     .UnfundedAmount = clsUnfundedAmount
     .PIKing = clsPIKing
     .PIKAmount = clsPIKAmount
     .MDYFacilityRating = clsMDYFacilityRating
     .MDYFacilityOutlook = clsMDYFacilityOutlook
     .MDYIssuerRating = clsMDYIssuerRating
     .MDYIssuerOutlook = clsMDYIssuerOutlook
     .MDYSnrSecRating = clsMDYSnrSecRating
     .MDYSNRUnSecRating = clsMDYSNRUnSecRating
     .MDYSubRating = clsMDYSubRating
     .MDYCreditEstRating = clsMDYCreditEstRating
     .MDYCreditEstDate = clsMDYCreditEstDate
     .SandPFacilityRating = clsSandPFacilityRating
     .SandPIssuerRating = clsSandPIssuerRating
     .SandPSnrSecRating = clsSandPSnrSecRating
     .SandPSubordinate = clsSandPSubordinate
     .SPPriorityCategory = clsSPPriorityCategory
     .MDYAssetCategory = clsMDYAssetCategory
     .DatedDate = clsDatedDate
     .IssueDate = clsIssueDate
     .FirstPaymentDate = clsFirstPaymentDate
     .AmortizationType = clsAmType
     .DayCount = clsDayCount
     .LiborFloor = clsIndexCap
     .BusinessDayConvention = clsBussDayConv
     .EOMFlag = clsPmtEOM
     .AmtIssued = clsAmtIssued
     .PrePayRate = clsPrePayRate
     .DefaultRate = clsDefaultRate
     .Severity = clsSeverity
     .Lag = clsLag
     .MDYDPRatingWARF = clsMDYDPRatingWARF
     .SandPRecRating = clsSandPRecRating
     .AnalystOpinion = clsAnalystOpinion
    End With
    
    Dim lkeys As Variant
    Dim lItems As Variant
    Set lPaySched = New Dictionary
    lkeys = clsSchedDict.Keys
    lItems = clsSchedDict.Items
    For i = LBound(lkeys) To UBound(lkeys)
        lPaySched.Add lkeys(i), lItems(i)
    Next
    
    
    
    lAsset.AddAsset lAssetUDT, lPaySched
    For Each lkeys In clsMoodyRatingHistDict.Keys
        lAsset.AddMoodyRating CDate(lkeys), clsMoodyRatingHistDict(lkeys)
    Next
    For Each lkeys In clsSPRatingHistDict.Keys
        lAsset.AddSPRating CDate(lkeys), clsSPRatingHistDict(lkeys)
    Next
    Set Copy = lAsset
End Function
Public Function CashflowOutput() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsCF.Count + 1, 0 To 15)
    lOutput(0, 0) = "Payment Date"
    lOutput(0, 1) = "Moody's Rating"
    lOutput(0, 2) = "S&P's Rating"
    lOutput(0, 3) = "Accrual Beg Date"
    lOutput(0, 4) = "Accrual End Date"
    lOutput(0, 5) = "Beg Balance"
    lOutput(0, 6) = "Defaults"
    lOutput(0, 7) = "MV Defaults"
    lOutput(0, 8) = "Interest"
    lOutput(0, 9) = "Scheduled Principal"
    lOutput(0, 10) = "Unscheduled Principal"
    lOutput(0, 11) = "Recoveies"
    lOutput(0, 12) = "Cash Total"
    lOutput(0, 13) = "Loss"
    lOutput(0, 14) = "Default Balance"
    lOutput(0, 15) = "MV of Default Balance"
    For i = 0 To clsCF.Count
        lOutput(i + 1, 0) = clsCF.PaymentDate(i)
        lOutput(i + 1, 1) = GetMoodyRating(clsCF.PaymentDate(i))
        lOutput(i + 1, 2) = GetSPRating(clsCF.PaymentDate(i))
        lOutput(i + 1, 3) = clsCF.AccBegDate(i)
        lOutput(i + 1, 4) = clsCF.AccEndDate(i)
        lOutput(i + 1, 5) = clsCF.BegBalance(i)
        lOutput(i + 1, 6) = clsCF.Default(i)
        lOutput(i + 1, 7) = clsCF.MVDefault(i)
        lOutput(i + 1, 8) = clsCF.Interest(i)
        lOutput(i + 1, 9) = clsCF.SchedPrincipal(i)
        lOutput(i + 1, 10) = clsCF.UnSchedPrincipal(i)
        lOutput(i + 1, 11) = clsCF.Recoveries(i)
        lOutput(i + 1, 12) = clsCF.Total(i)
        lOutput(i + 1, 13) = clsCF.Netloss(i)
        lOutput(i + 1, 14) = clsCF.DefaultBal(i)
        lOutput(i + 1, 15) = clsCF.MVDefaultBal(i)
    Next i
    CashflowOutput = lOutput
End Function


Private Sub CalcPaymentDates()
    Dim lPaymentDateDict As Dictionary
    Dim lFirstPaymentDate As Date
    Set lPaymentDateDict = New Dictionary
    Dim i As Long
    Dim lPrincipalPayments As Variant
    Dim lCounter As Long
    
    lFirstPaymentDate = clsFirstPaymentDate
    lCounter = 1
    Do While lFirstPaymentDate < clsMaturity
        clsPaymentDates.Add CLng(lFirstPaymentDate), 1
        clsIntPaymentDates.Add CLng(lFirstPaymentDate), 1
        lFirstPaymentDate = DateAddBusiness("M", clsMonthsbetweenpayments * lCounter, clsFirstPaymentDate, clsBussDayConv, clsPmtEOM)
        
        If lFirstPaymentDate >= clsMaturity Then
            clsPaymentDates.Add CLng(clsMaturity), 1
            clsIntPaymentDates.Add clsMaturity, 1
            Exit Do
        End If
        lCounter = lCounter + 1
    Loop

    lPrincipalPayments = clsSchedDict.Keys
    For i = 0 To UBound(lPrincipalPayments)
        If Not (clsPaymentDates.Exists(CLng(CDate(lPrincipalPayments(i))))) Then
            clsPaymentDates.Add CLng(CDate(lPrincipalPayments(i))), 1
        End If
    Next i

    Call SortDictionary(clsPaymentDates, True, , vbTextCompare)


End Sub


Private Sub SetLoanConstant()
'    Select Case UCase(clsPaymentFreq)
'
'    Case "ANNUALLY"
'        clsPaymentsPerYear = 1
'        clsMonthsBetweenPayments = 12
'    Case "SEMI-ANNUALLY"
'        clsPaymentsPerYear = 2
'        clsMonthsBetweenPayments = 6
'    Case "QUARTERLY"
'        clsPaymentsPerYear = 4
'        clsMonthsBetweenPayments = 3
'    Case "MONTHLY"
'        clsPaymentsPerYear = 12
'        clsMonthsBetweenPayments = 1
'    End Select

    clsPaymentsPerYear = clsPaymentFreq
    clsMonthsbetweenpayments = 12 / clsPaymentFreq

    Select Case UCase(clsDayCount)
    Case "30/360"
        clsDayCountEnum = 0
    Case "ACTUAL/ACTUAL"
        clsDayCountEnum = 1
    Case "ACTUAL/365", "ACT365"
        clsDayCountEnum = 3
    Case "ACTUAL/360", "ACT360"
        clsDayCountEnum = 2
    Case "30/360EU"
        clsDayCountEnum = 4
    End Select
End Sub
Private Function GetIntAccrualStartDate(iInialSettleDate As Date, ianalysisDate As Date) As Date
    Dim lPaymentDates As Variant
    Dim lPaymentDate As Date
    Dim lPreviousStartdate As Date
    Dim i As Long
    
    lPaymentDates = clsIntPaymentDates.Keys
    lPaymentDate = CDate(CLng(lPaymentDates(0)))
    lPreviousStartdate = clsDatedDate
    Do While lPaymentDate < ianalysisDate
    
        lPreviousStartdate = lPaymentDate
        i = i + 1
        lPaymentDate = CDate(CLng(lPaymentDates(i)))
    Loop
    If iInialSettleDate > lPreviousStartdate Then
        GetIntAccrualStartDate = iInialSettleDate
    Else
        GetIntAccrualStartDate = lPreviousStartdate
    End If
    
    
    
    
End Function


Public Function CalcCF(Optional ByVal iCurrBalance As Double, Optional ByVal iInitalSettlementDate As Date, Optional ByVal ianalysisDate As Date, Optional ByVal iPrepay As Variant, Optional ByVal iDefault As Variant, Optional ByVal iSeverity As Variant, Optional ByVal iLagMonth As Long, Optional ByVal iEndCFDate As Date, Optional ByVal iYC As YieldCurve) As SimpleCashflow

    'iAnalysisDate should be greater or eaqual to inital setllmentdate
    'CurrBalance on ianalysisdate
    Dim i As Long
    Dim lPaymentDates As Variant
    Dim lLastIntDate As Date
    Dim lCurrBalance As Double
    Dim lNumofPayments As Long
    Dim lPaymentDate As Date
    Dim lNumCashflows As Long
    Dim lPeriodLag As Long
    Dim lDefaultDict  As Dictionary
    Dim lIntCounter As Long
    Dim lCF As SimpleCashflow
    Set lCF = New SimpleCashflow
    Dim lPeriodPrepay As Double
    Dim lPeriodDefault As Double
    Dim lPeriodSev As Double
    Dim lDefault() As Double
    Dim lMVDefault() As Double
    
    
    
    
    'Set optional variable
    If iCurrBalance = 0 Then iCurrBalance = clsParAmount
    If clsParAmount = 0 Then iCurrBalance = 1000000
    If ianalysisDate = 0 Then ianalysisDate = Now()
    If IsMissing(iPrepay) Then iPrepay = clsPrePayRate
    If IsMissing(iDefault) Then iDefault = clsDefaultRate
    If IsMissing(iSeverity) Then iSeverity = clsSeverity
    If iLagMonth = 0 Then iLagMonth = clsLag
    If iEndCFDate = 0 Then iEndCFDate = clsMaturity
    
    
    'Set to hold Dfaults and marketvaules
    ReDim lDefault(clsIntPaymentDates.Count)
    ReDim lMVDefault(clsIntPaymentDates.Count)
    
    If ianalysisDate > clsMaturity Then
        'tHE ANALYSIS DATE IS AFTER MATURITY DATE. CaN'T RUN CASHFLOWS
        Set CalcCF = lCF
        Set clsCF = lCF
        Exit Function
    End If


    lPeriodLag = iLagMonth / clsMonthsbetweenpayments
    Set lDefaultDict = New Dictionary

    lPaymentDates = clsPaymentDates.Keys
    lLastIntDate = GetIntAccrualStartDate(iInitalSettlementDate, ianalysisDate)
    Dim lSchedprin As Double
    Dim lBalAfterDefault As Double
    
    lNumofPayments = clsPaymentDates.Count
    

 
    'Debug.Assert Me.BLKRockID <> "BRSLZGT09"
    lCurrBalance = iCurrBalance
    For i = 0 To clsPaymentDates.Count - 1
        With lCF
            lPaymentDate = lPaymentDates(i)
            'If this is a principal and interest date then
            If lPaymentDate > ianalysisDate Then
                If lPaymentDate > iEndCFDate Or lCurrBalance < 1 Then
                    If lNumCashflows < 1 Then
                        Exit For
                    ElseIf .DefaultBal(lNumCashflows - 1) < 1 Then
                        Exit For
                    End If
                End If
                .PaymentDate(lNumCashflows) = lPaymentDate
                .AccBegDate(lNumCashflows) = lLastIntDate
                .AccEndDate(lNumCashflows) = lPaymentDate
                If lNumCashflows = 0 And clsDefaultAsset = True Then
                    .DefaultBal(0) = lCurrBalance
                    .MVDefaultBal(0) = lCurrBalance * clsMarketValue / 100
                    .MVDefault(0) = lCurrBalance * clsMarketValue / 100
                    lDefault(0) = .DefaultBal(0)
                    lMVDefault(0) = .MVDefaultBal(0)
                    lCurrBalance = 0
                End If
                If lNumCashflows > 0 Then
                    .DefaultBal(lNumCashflows) = .DefaultBal(lNumCashflows - 1)
                    .MVDefaultBal(lNumCashflows) = .MVDefaultBal(lNumCashflows - 1)
    
                End If
                
                If clsIntPaymentDates.Exists(CLng(lPaymentDate)) Then
                    lIntCounter = lIntCounter + 1
                    If IsArray(iPrepay) Then
                        If UBound(iPrepay) < lIntCounter Then
                            lPeriodPrepay = UBound(iPrepay)
                        Else
                            lPeriodPrepay = iPrepay(lIntCounter)
                        End If
                    Else
                        lPeriodPrepay = iPrepay
                    End If
                    If IsArray(iDefault) Then
                        If UBound(iDefault) < lIntCounter Then
                            lPeriodDefault = UBound(iDefault)
                        Else
                            lPeriodDefault = iDefault(lIntCounter)
                        End If
                    ElseIf IsNumeric(iDefault) Then
                        lPeriodDefault = iDefault
                    End If
                    If IsArray(iSeverity) Then
                        If UBound(iSeverity) < lIntCounter Then
                            lPeriodSev = UBound(iSeverity)
                        Else
                            lPeriodSev = iPrepay(lIntCounter)
                        End If
                    Else
                        lPeriodSev = iSeverity
                    End If
                
                    .BegBalance(lNumCashflows) = lCurrBalance
                    
                    If VarType(iDefault) = vbString Or clsUseRM Then
                        If GetMoodyRating(lPaymentDate) = "D" Or GetSPRating(lPaymentDate) = "D" Then
                            .Default(lNumCashflows) = lCurrBalance
                        End If
                    Else
                        .Default(lNumCashflows) = lCurrBalance * ConvertAnnualRates(lPeriodDefault, lLastIntDate, lPaymentDate)
                    End If
                    lDefault(lIntCounter) = .Default(lNumCashflows)
                    .MVDefault(lNumCashflows) = .Default(lNumCashflows) * (1 - lPeriodSev)
                    lMVDefault(lIntCounter) = .MVDefault(lNumCashflows)
                    .DefaultBal(lNumCashflows) = .DefaultBal(lNumCashflows) + .Default(lNumCashflows)
                    .MVDefaultBal(lNumCashflows) = .MVDefaultBal(lNumCashflows) + .Default(lNumCashflows) * (1 - lPeriodSev)
                    
                    lBalAfterDefault = lCurrBalance - .Default(lNumCashflows)
                    .Interest(lNumCashflows) = DateFraction(lLastIntDate, lPaymentDate, clsDayCountEnum) * clsCoupon * lBalAfterDefault
                    If clsSchedDict.Exists(CLng(lPaymentDate)) Then
                        .SchedPrincipal(lNumCashflows) = lBalAfterDefault * clsSchedDict(CLng(lPaymentDate))
                    End If
                    .UnSchedPrincipal(lNumCashflows) = (lBalAfterDefault - .SchedPrincipal(lNumCashflows)) * ConvertAnnualRates(lPeriodPrepay, lLastIntDate, lPaymentDate)
                    If lIntCounter - lPeriodLag >= 0 And lPeriodLag > 0 Then
                        .Recoveries(lNumCashflows) = lMVDefault(lIntCounter - lPeriodLag)
                        .Netloss(lNumCashflows) = lDefault(lIntCounter - lPeriodLag) - lMVDefault(lIntCounter - lPeriodLag)
                        .DefaultBal(lNumCashflows) = .DefaultBal(lNumCashflows) - lDefault(lIntCounter - lPeriodLag)
                        .MVDefaultBal(lNumCashflows) = .MVDefaultBal(lNumCashflows) - .Recoveries(lNumCashflows)
                    ElseIf lPeriodLag = 0 Then
                        .Recoveries(lNumCashflows) = .MVDefault(lNumCashflows)
                        .Netloss(lNumCashflows) = .Default(lNumCashflows) - .MVDefault(lNumCashflows)
                        .DefaultBal(lNumCashflows) = .DefaultBal(lNumCashflows) - .Default(lNumCashflows)
                        .MVDefaultBal(lNumCashflows) = .MVDefaultBal(lNumCashflows) - .Recoveries(lNumCashflows)
                    End If
                    .Total(lNumCashflows) = .Interest(lNumCashflows) + .UnSchedPrincipal(lNumCashflows) + .SchedPrincipal(lNumCashflows) + .Recoveries(lNumCashflows)
                    lCurrBalance = lCurrBalance - .Default(lNumCashflows) - .SchedPrincipal(lNumCashflows) - .UnSchedPrincipal(lNumCashflows)
                    lLastIntDate = lPaymentDate
                    If Not (iYC Is Nothing) Then
                        If clsCouponType = "FLOAT" Then
                            clsCoupon = Round(iYC.SpotRate(lLastIntDate, clsMonthsbetweenpayments), 5)
                            If clsCoupon < clsLiborFloor Then
                                clsCoupon = clsLiborFloor
                            End If
                            clsCoupon = clsCoupon + clsCpnSpread
                        End If
                    End If
                Else
                    If Not (VarType(iDefault) = vbString And (GetMoodyRating(lPaymentDate) = "D" Or GetSPRating(lPaymentDate) = "D")) Then
                        .BegBalance(lNumCashflows) = lCurrBalance
                        .SchedPrincipal(lNumCashflows) = clsSchedDict(CLng(lPaymentDate)) * lCurrBalance
                        .Interest(lNumCashflows) = DateFraction(lLastIntDate, lPaymentDate, clsDayCountEnum) * clsCoupon * .SchedPrincipal(lNumCashflows)
                        lCurrBalance = lCurrBalance - .SchedPrincipal(lNumCashflows)
                        .Total(lNumCashflows) = .Interest(lNumCashflows) + .UnSchedPrincipal(lNumCashflows) + .SchedPrincipal(lNumCashflows) + .Recoveries(lNumCashflows)
                    Else
                        .BegBalance(lNumCashflows) = lCurrBalance
                        .Default(lNumCashflows) = lCurrBalance
                        lDefault(lIntCounter) = lDefault(lIntCounter) + .Default(lNumCashflows)
                        .MVDefault(lNumCashflows) = .Default(lNumCashflows) * (1 - lPeriodSev)
                        lMVDefault(lIntCounter) = lMVDefault(lIntCounter) + .MVDefault(lNumCashflows)
                        .DefaultBal(lNumCashflows) = .DefaultBal(lNumCashflows) + .Default(lNumCashflows)
                        .MVDefaultBal(lNumCashflows) = .MVDefaultBal(lNumCashflows) + .Default(lNumCashflows) * (1 - lPeriodSev)
                        lCurrBalance = lCurrBalance - .Default(lNumCashflows)
                    End If
                End If
            .EndBalance(lNumCashflows) = lCurrBalance
            If lCurrBalance < 1 And lCF.DefaultBal(lNumCashflows) < 1 Then
                'Debug.Print "take loss"
                lCF.Netloss(lNumCashflows) = lCF.Netloss(lNumCashflows) + lCF.DefaultBal(lNumCashflows) + lCurrBalance
                lCurrBalance = 0
                lCF.MVDefaultBal(lNumCashflows) = 0
                lCF.DefaultBal(lNumCashflows) = 0
            End If

            lNumCashflows = lNumCashflows + 1
            End If
        End With
    Next i
    If lCF.DefaultBal(lNumCashflows - 1) > 0 Then
        lCF.Netloss(lNumCashflows - 1) = lCF.Netloss(lNumCashflows - 1) + lCF.DefaultBal(lNumCashflows - 1)
        lCF.DefaultBal(lNumCashflows - 1) = 0
        lCF.MVDefaultBal(lNumCashflows - 1) = 0
    End If
    
    Set CalcCF = lCF
    Set clsCF = lCF
    
End Function


Private Sub Class_Initialize()
    Set clsPaymentDates = New Dictionary
    Set clsIntPaymentDates = New Dictionary
    Set clsSPRatingHistDict = New Dictionary
    Set clsMoodyRatingHistDict = New Dictionary
End Sub
Public Sub AddMoodyRating(iDate As Date, iRating As String)
    If clsMoodyRatingHistDict.Exists(CLng(iDate)) Then
        clsMoodyRatingHistDict.Remove (CLng(iDate))
    End If
    clsMoodyRatingHistDict.Add CLng(iDate), iRating
    clsSortMoodys = True
    '
End Sub
Public Sub AddSPRating(iDate As Date, iRating As String)
    If clsSPRatingHistDict.Exists(CLng(iDate)) Then
        clsSPRatingHistDict.Remove CLng(iDate)
    End If
    clsSPRatingHistDict.Add CLng(iDate), iRating
    clsSortSP = True
    
    'Call SortDictionary(clsSPRatingHistDict, True, True)
    
    
End Sub

Public Function GetMoodyRating(iDate As Date) As String
    Dim lMoodyRating As String
    Dim lDate As Variant
    
    If clsSortMoodys Then
        Call SortDictionary(clsMoodyRatingHistDict, True, True)
        clsSortMoodys = False
    End If
    If clsMoodyRatingHistDict.Count <= 1 Then
        lMoodyRating = clsMDYRating
    Else
        For Each lDate In clsMoodyRatingHistDict.Keys
            If lDate <= iDate Then
                lMoodyRating = clsMoodyRatingHistDict(CLng(lDate))
                Exit For
            End If
        Next
    End If
    GetMoodyRating = lMoodyRating
End Function
Public Function GetSPRating(iDate As Date) As String
    Dim lSPRating As String
    Dim lDate As Variant
    
    Dim licecream As Variant
    If clsSortSP Then
        Call SortDictionary(clsSPRatingHistDict, True, True)
        clsSortSP = False
    End If
    'licecream = clsSPRatingHistDict.Keys
    If clsSPRatingHistDict.Count <= 1 Then
        lSPRating = clsSPRating
    ElseIf clsSPRatingHistDict.Exists(CLng(iDate)) Then
        lSPRating = clsSPRatingHistDict(CLng(iDate))
    
    Else
        For Each lDate In clsSPRatingHistDict.Keys
            If lDate <= iDate Then
                lSPRating = clsSPRatingHistDict(CLng(lDate))
                Exit For
            End If
        Next
    End If
    GetSPRating = lSPRating
End Function
Public Function GetBegBalance(iDate As Date) As Double
    If clsCF Is Nothing Then
        Set clsCF = CalcCF
    End If
    GetBegBalance = clsCF.GetBegBlance(iDate)
End Function


Public Function GetDefaults(iBegDate As Date, iEndDate As Date, Optional isfirstperiod As Boolean) As Double
    
    If clsCF Is Nothing Then
        Set clsCF = CalcCF
    End If
    GetDefaults = clsCF.GetDefaults(iBegDate, iEndDate, isfirstperiod)
End Function

Public Function GetMVDefaults(iBegDate As Date, iEndDate As Date, Optional isfirstperiod As Boolean) As Double
    If clsCF Is Nothing Then
        Set clsCF = CalcCF
    End If
    GetMVDefaults = clsCF.GetMVDefaults(iBegDate, iEndDate, isfirstperiod)
End Function
Public Function GetSchedPrin(iBegDate As Date, iEndDate As Date) As Double
    If clsCF Is Nothing Then
        Set clsCF = CalcCF
    End If
    GetSchedPrin = clsCF.GetSchedPrin(iBegDate, iEndDate)
End Function
Public Sub ResetForSimulation(ianalysisDate As Date)
    clsParAmount = 0
    clsSPRatingHistDict.RemoveAll
    clsMoodyRatingHistDict.RemoveAll
    clsSPRatingHistDict.Add ianalysisDate, clsSPRating
    clsMoodyRatingHistDict.Add ianalysisDate, clsMDYRating
End Sub


Public Function CountOperator(iFilter As String, iOperator As String) As Long
    Dim lNum As Long
    Dim lChar As Long
    
    Do While lChar < Len(iFilter)
        If InStr(lChar, iFilter, iOperator) = 0 Then
        
            Exit Do
        Else
            lNum = lNum + 1
            lChar = lChar + Len(iOperator)
        End If
    Loop
End Function



Private Function Compare(iField As String, iOperator As String, iValue As Variant) As Boolean
    Dim lValue1 As Variant
    Dim lValue2 As Variant
    
    Select Case Trim(UCase(iField))
    Case "MOODY'S INDUSTRY"
        lValue1 = Me.MDYIndustry
        lValue2 = UCase(iValue)
    Case "S&P INDUSTRY"
        lValue1 = UCase(Me.SPIndustry)
        lValue2 = UCase(iValue)
    Case "MOODY'S RATING"
        lValue1 = ConverRatingToEnumMoody(Me.MDYRating)
        lValue2 = ConverRatingToEnumMoody(CStr(iValue))
    Case "MOODY'S RATING WARF"
        lValue1 = ConverRatingToEnumMoody(Me.MDYDPRatingWARF)
        lValue2 = ConverRatingToEnumMoody(CStr(iValue))
    Case "MOODY'S RATING DPR"
        lValue1 = ConverRatingToEnumMoody(Me.MDYDPRating)
        lValue2 = ConverRatingToEnumMoody(CStr(iValue))
    Case "S&P RATING"
        lValue1 = ConvertRatingToEnum(Me.SPRating)
        lValue2 = ConvertRatingToEnum(CStr(iValue))
    Case "WAL"
        lValue1 = Me.WAL
        lValue2 = iValue
    Case "COV-LITE"
        lValue1 = Me.CovLite
        lValue2 = CBool(iValue)
    Case "COUNTRY"
        lValue1 = Me.Country
        lValue2 = UCase(iValue)
    Case "FACILITY SIZE"
        lValue1 = Me.FacilitySize
        lValue2 = CDbl(iValue)
    Case "MARKET VALUE"
        lValue1 = Me.MarketValue
        lValue2 = CDbl(iValue)
    Case "ANALYST OPINION"
        lValue1 = Me.AnalystOpinion
        lValue2 = UCase(iValue)
    End Select
    
    Select Case iOperator
    Case Is = "="
        Compare = lValue1 = lValue2
    Case Is = "!="
        Compare = lValue1 <> lValue2
    Case Is = "<"
        Compare = lValue1 < lValue2
    Case Is = ">"
        Compare = lValue1 > lValue2
    Case Is = ">="
        Compare = lValue1 >= lValue2
    Case Is = "<="
        Compare = lValue1 <= lValue2
    End Select
    
End Function
Private Function ApplyCompareFilter(iFilter As String) As Boolean
    Dim lField As String
    Dim lOper As String
    Dim lOperNum As Long
    Dim lValue As Variant
    
    Call GetComparisonOperator(iFilter, lOperNum, lOper)
    lField = Trim(Left(iFilter, lOperNum - 1))
    lValue = Trim(Mid(iFilter, lOperNum + Len(lOper)))
    ApplyCompareFilter = Compare(lField, lOper, lValue)
End Function

Private Sub GetComparisonOperator(iField As String, oCharNum As Long, oOperator As String)

    If InStr(1, iField, "<=") > 0 Then
        oCharNum = InStr(1, iField, "<=")
        oOperator = "<="
    ElseIf InStr(1, iField, "!=") > 0 Then
        oCharNum = InStr(1, iField, "!=")
        oOperator = "!="
    ElseIf InStr(1, iField, ">=") > 0 Then
        oCharNum = InStr(1, iField, ">=")
        oOperator = ">="
    ElseIf InStr(1, iField, "<") > 0 Then
        oCharNum = InStr(1, iField, "<")
        oOperator = "<"
    ElseIf InStr(1, iField, "=") > 0 Then
        oCharNum = InStr(1, iField, "=")
        oOperator = "="
    ElseIf InStr(1, iField, ">") > 0 Then
        oCharNum = InStr(1, iField, ">")
        oOperator = ">"
    End If
End Sub
Public Function ApplyFilter(ByVal iFilter As String) As Boolean
    Dim lLeft As Long
    Dim lRight As Long
    Dim lSubFilter As String
    Dim lResult As String
    Dim lLHS As Variant
    Dim lRHS As Variant
    Dim lNextOperator As String
    Dim lNextChar As Long
    Dim lCurrOperator As String
    Dim lCurrChar As Long
    
    'Replace Everything
    Do While InStrRev(iFilter, "(") > 0
        lLeft = InStrRev(iFilter, "(")
        lRight = InStr(lLeft, iFilter, ")")
        lSubFilter = Mid(iFilter, lLeft + 1, lRight - lLeft - 1)
        lResult = ApplyFilter(lSubFilter)
        iFilter = Replace(iFilter, "(" & lSubFilter & ")", lResult)
    Loop
    'Find logical operator
    Call FindNextOperator(1, iFilter, lNextOperator, lNextChar)
    If lNextChar = 0 Then
        If UCase(iFilter) = "TRUE" Then
            ApplyFilter = True
        ElseIf UCase(iFilter) = "FALSE" Then
            ApplyFilter = False
        Else
            ApplyFilter = ApplyCompareFilter(iFilter)
        End If
    Else
        lLHS = ApplyFilter(Trim(Left(iFilter, lNextChar - 1)))
        lCurrChar = lNextChar
        lCurrOperator = lNextOperator
        Call FindNextOperator(lNextChar + 1, iFilter, lNextOperator, lNextChar)
        Do While lNextChar > 0
            lSubFilter = Trim(Mid(iFilter, lCurrChar + 1 + Len(lCurrOperator), lNextChar - lCurrChar - Len(lCurrOperator)))
            lRHS = ApplyFilter(lSubFilter)
            lLHS = ApplyLogical(lLHS, lCurrOperator, lRHS)
            lCurrChar = lNextChar
            lCurrOperator = lNextOperator
            Call FindNextOperator(lNextChar + 1, iFilter, lNextOperator, lNextChar)
        Loop
        lRHS = ApplyFilter(Trim(Mid(iFilter, lCurrChar + Len(lCurrOperator) + 2, Len(iFilter) + 1 - lCurrChar - Len(lCurrOperator) + 2)))
        ApplyFilter = ApplyLogical(lLHS, lCurrOperator, lRHS)
    End If
End Function

Private Function ApplyLogical(iLHS As Variant, iOperator As String, iRHS As Variant) As Boolean
    Select Case Trim(UCase(iOperator))
    Case "AND"
        ApplyLogical = iLHS And iRHS
    Case "OR"
        ApplyLogical = iLHS Or iRHS
    Case "NOT OR"
        'ApplyLogical = iLHS not or iRHS
    Case "NOT And"
    
        
    End Select
End Function


Private Sub Class_Terminate()
    Set clsPaymentDates = Nothing
    Set clsIntPaymentDates = Nothing
    Set clsSPRatingHistDict = Nothing
    Set clsMoodyRatingHistDict = Nothing
    Set clsSchedDict = Nothing
    Set clsCF = Nothing
End Sub
