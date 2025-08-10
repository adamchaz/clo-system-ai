Attribute VB_Name = "UDTandEnum"
'Option Explicit
Public Const AssetFields As Long = 43

Public Enum CashType
    Interest = 1
    Principal = 2
    Total = 3
End Enum

Public Type Results
    TestNumber As TestNum
    TestName As String
    Result As Double
    Threshold As Double
    PassFail As Boolean 'Pass equals true
    Comments As String
    Numerator As Double
    Denominator As Double
    PassFailComment As String
End Type

Public Enum AccountType
    Payment = 1
    Collection = 2
    RampUp = 3
    RevolverFunding = 4
    ExpenseReserve = 5
    Custodial = 6
    SupplementalReserve = 7
    InterestReserve = 8
    FundingNote = 9
End Enum


Public Enum TestNum
    LimitationOnSeniorSecuredLoans = 1
    LimitationOnAssetNotSeniorSecuredLoans = 2
    LimitationOn6LargestObligor = 3
    LimitationOn1LagestObligor = 4
    LimitationOnObligorDIP = 5
    LimitationOnObligornotSeniorSecured = 6
    LimitationonCasAssets = 7
    LimitationonAssetspaylessFrequentlyQuarterly = 8
    LimitationOnFixedRateAssets = 9
    LimitationonCurrentPayAssets = 10
    LimitationOnDIPAssets = 11
    LimmitationOnUnfundedcommitments = 12
    LimitationOnParticipationInterest = 13
    LimitationOnCountriesNotUS = 14
    LimitationOnCountriesCanadaandTaxJurisdictions = 15
    LimitationonCountriesNotUSCanadaUK = 16
    LimitationOnGroupCountries = 17
    LimitationOnGroupICountries = 18
    LimitationOnIndividualGroupICountries = 19
    LimitationOnGroupIICountries = 20
    LimitationonIndividualGroupIICountries = 21
    LimitationOnGroupIIICountries = 22
    LimitationonIndividualGroupIIICountries = 23
    LimitationOnTaxJurisdictions = 24
    LimitationOn4SPIndustryClassification = 25
    LimitationOn2SPClassification = 26
    LimitationOn1SPClassification = 27
    LimitationOnBridgeLoans = 28
    LimitationOnCovLite = 29
    LimitationonDeferrableSecuriies = 30
    LimitationonFacilitiySize = 31
    WeightedAverateSpread = 32
    WeightedAverageMoodyRecoveryRate = 33
    WeightedAverageCoupon = 34
    WeightedAverageLife = 35
    WeightedAverageRatingFactor = 36
    MoodysDiversity = 37
    JROCTEST = 38
    WeightedAverageSpreadMag14 = 39
    LimitationonCCCObligations = 40
    LimitationOnCanada = 41
    LimitationOnLetterOfCredit = 42
    LimitationOnLongDated = 43
    LimitationOnUnsecuredLoans = 44
    LimitationOnSwapNonDiscount = 45
    WeightedAverageSpreadMag06 = 46
    LimitationOnNonEmergingMarketObligors = 47
    LimitationOnSPCriteria = 48
    LimitationOn1MoodyIndustry = 49
    LimitationOn2MoodyIndustry = 50
    LimitationOn3MoodyIndustry = 51
    LimitationOn4MoodyIndustry = 52
    LimitationonFacilitiySizeMAG08 = 53
    WeightedAverageRatingFactorMAG14 = 54
End Enum

Public Type TestThresholds
    TestNumber As TestNum
    Threshold As Double
    Overwrites As Double
    PreviousValues As Double
End Type


Public Type AssetUDT
    'This is so I can write cleaner code when getting data from spreadsheet.I didn't want a intialization routine with
    '30 different arguments
    
    BLKRockID As String
    ParAmount As Double
    IssueName As String
    IssuerName As String
    IssuerId As String
    Tranche As String
    PIKing As Boolean
    PIKAmount As Double
    Index As String
    Coupon As Double
    BondLoan As String
    UnfundedAmount As Double
    Maturity As Date
    CouponType As String
    PaymentFreq As String
    CpnSpread As Double
    LiborFloor As Double
    CommitFee As Double
    FacilitySize As Double
    MDYIndustry As String
    SPIndustry As String
    Country As String
    Seniority As String
    PikAsset As Boolean
    DefaultAsset As Boolean
    DateofDefault As Date
    DelayDrawdown As Boolean
    Revolver As Boolean
    LOC As Boolean
    Participation As Boolean
    DIP As Boolean
    Converitable As Boolean
    StructFinance As Boolean
    BridgeLoan As Boolean
    CurrentPay As Boolean
    CovLite As Boolean
    Currency As String
    WAL As Double
    MarketValue As Double
    FLLO As Double
    MDYRating As String
    MDYDPRating As String
    MDYRecoveryRate As Double
    SPRating As String
    MDYFacilityRating As String
    MDYFacilityOutlook As String
    MDYIssuerRating As String
    MDYIssuerOutlook As String
    MDYSnrSecRating As String
    MDYSNRUnSecRating As String
    MDYSubRating As String
    MDYCreditEstRating As String
    MDYCreditEstDate As Date
    SandPFacilityRating As String
    SandPIssuerRating As String
    SandPSnrSecRating As String
    SandPSubordinate As String
    DatedDate As Date
    IssueDate As Date
    FirstPaymentDate As Date
    AmortizationType As String
    DayCount As String
    LIBORCap As Double
    BusinessDayConvention As String
    EOMFlag As Boolean
    AmtIssued As Double
    PrePayRate As Variant
    DefaultRate As Variant
    Severity As Variant
    Lag As Double
    MDYAssetCategory As String
    SPPriorityCategory As String
    MDYDPRatingWARF As String
    SandPRecRating As String
    AnalystOpinion As String
End Type
Public Type TestSettings
    Libor As Double
    ReinvestBal As Double
    WASThreshold As Double
    DiversityThreshold As Long
    WARFAdjFactor As Long
    SpreadAdjFactor As Double
    WARFThreshould As Long
    DetermDate As Date
    WALEndDate As Date
    TestThresholds As Dictionary
End Type

Public Type OptInputs
    MaxAssets As Long
    MaxLoanSize As Double
    IncreaseCurLoan As Boolean
    RunHypoInd As Boolean
End Type

Public Enum RatingAgencies
    SandP = 0
    Moodys = 1
    Fitch = 2
End Enum



Public Type MoodysInputRating
    BondorLoan As String
    Senority As String
    MoodyFacilityRating As String
    MoodyCFRRating As String
    MoodySenionUnsecuredRating As String
    MoodySubordinateRating As String
End Type

Public Enum DayCount
    US30_360 = 0
    Actual_Actual = 1
    actual_360 = 2
    Actual_365 = 3
    EU30_360 = 4
End Enum

Public Type Cashflows    'The user can determine which arrays to populate
    PaymentDate() As Date
    AccrualBegDate() As Date
    AccrualEndDate() As Date
    Balance() As Double
    Interest() As Double
    Principal() As Double
    Prepayment() As Double  'Not toally sure why I have prepayment but I'm a mortgage guy and i like it
    Default() As Double
    Recoveries() As Double
    Netloss() As Double
    Total() As Double
End Type

Public Type DealDates
    AnalysisDate As Date
    PricingDate As Date
    ClosingDate As Date
    EffDate As Date
    FirstPayDate As Date
    NoCallDate As Date
    ReinvestDate As Date
    MatDate As Date
    PayDay As Long
    MonthsBetwPay As Long
    IntDeterDate As Long
    DeterDate As Long
    BussConv As String
End Type

Public Type Fees
    UpFrontFee As Double
    RunnTaxes As Double
    TrusteeFee As Double
    TrustType As String
    FixedCostPerYear As Double
    AdminCap As Double
    RunAdamExpCap As Double
    SenManagFee As Double
    JurManagFee As Double
    ManagFeeType As String
    IntOnManagFee As Boolean
    IntSpreadManagFee As Double
    IncentManagFee As Double
    IncenManagFeeHurd As Double
End Type

Public Type CLOInputs
    AnalysisDate As Date
    BegFeeBasis As Double
    Libor As Double
    PurFinanceAccInt As Double
    TargetParAmount As Double
    EventOfDefault As Boolean
    CallPercent As Double
    Liquidation As Double
End Type
Public Type PaymentDates
    PaymentDate As Date
    IntDeterDate As Date
    CollBegDate As Date
    CollEndDate As Date
End Type
Public Type ReinvestInfo
    Spread As Double
    Floor As Double
    Maturity As Long
    AmType As String
    ReinvestPrice As Double
    PreReinvType As String
    PostReinvType As String
    PreRinvestPct As Double
    PostReinvestPct As Double
    Prepayment As Variant
    Default As Variant
    Severity As Variant
    Lag As Long
End Type
Public Type HypoInputs
    Asset As Asset
    Transaction As String
    ParAmount As Double
    Price As Double
End Type
Public Enum SPRatings
    Aaa = 1
    AAplus = 2
    Aa = 3
    AAminus = 4
    Aplus = 5
    A = 6
    Aminus = 7
    BBBplus = 8
    BBB = 9
    BBBminus = 10
    BBplus = 11
    BB = 12
    BBminus = 13
    Bplus = 14
    b = 15
    Bmiuns = 16
    CCC = 17
    D = 18
End Enum
Public Enum MoodyRating
    Aaa = 1
    Aa1 = 2
    Aa2 = 3
    Aa3 = 4
    A1 = 5
    A2 = 6
    A3 = 7
    Baa1 = 8
    Baa2 = 9
    Baa3 = 10
    Ba1 = 11
    Ba2 = 12
    Ba3 = 13
    B1 = 14
    B2 = 15
    B3 = 16
    Caa1 = 17
    Caa2 = 18
    Caa3 = 19
    Ca = 20
    C = 21
End Enum
Public Enum RMOutputFields
    BALA
    BALAA
    BalAAA
    BALAAM
    BALAAP
    BALAM
    BALAP
    BALB
    BALBB
    BALBBB
    BALBBBM
    BALBBBP
    BALBBM
    BALBBP
    BALBM
    BALBP
    BalCCC
    BALDEF
    BALMAT
    BALPERDEF
    BALPERF
    CDR
    Downgrades
    NumA
    NumAA
    NumAAA
    NumAAm
    NumAAp
    NumAm
    NumAp
    NumB
    NumBB
    NumBBB
    NumBBBm
    NumBBBp
    numBBm
    NumBBp
    NumBm
    NumBp
    NUMCCC
    NUMDEF
    NUMMAT
    NUMPERDEF
    NUMPERF
    Upgrades
    EnumCount
End Enum
Public Enum TransactionType
    Buy = 1
    Sale = -1
End Enum
Public Type RankandRebalInputs  'This UDT will hold the user inputs for the Rebalancing & ranking subroutines
    TranType As TransactionType
    BuyFilter As String
    SaleFilter As String
    BuyPar As Double
    SalePar As Double
    InclDealLoans As Boolean
    IncPar As Double
    Libor As Double
End Type
Public Type Trades
    Deal As String
    BRSID As String
    TrnsType As TransactionType
    Price As Double
    Par As Double
End Type
Public Type HypoUserInputs
    PoolMode As Boolean
    Libor As Double
    Trades() As Trades
End Type
Public Type RMandCFInputs
    AnalysisDate As String
    DealName As String
    RMCF As Boolean
    CorrMatrix As String
    NumOfSims As Long
    RMFreq As String
    StaticRndNum As Boolean
    RandomizeSeed As Long
End Type

Public Function ConvertRatingToEnum(iString As String) As SPRatings
    Select Case iString
    Case "AAA"
        ConvertRatingToEnum = SPRatings.Aaa
    Case "AA+"
        ConvertRatingToEnum = AAplus
    Case "AA"
        ConvertRatingToEnum = Aa
    Case "AA-"
        ConvertRatingToEnum = AAminus
    Case "A+"
        ConvertRatingToEnum = AAplus
    Case "A"
        ConvertRatingToEnum = A
    Case "A-"
        ConvertRatingToEnum = Aminus
    Case "BBB+"
        ConvertRatingToEnum = BBBplus
    Case "BBB"
        ConvertRatingToEnum = BBB
    Case "BBB-"
        ConvertRatingToEnum = BBBminus
    Case "BB+"
        ConvertRatingToEnum = BBplus
    Case "BB"
        ConvertRatingToEnum = BB
    Case "BB-"
        ConvertRatingToEnum = BBminus
    Case "B+"
        ConvertRatingToEnum = Bplus
    Case "B"
        ConvertRatingToEnum = b
    Case "B-"
        ConvertRatingToEnum = Bmiuns
    Case "CCC", "CCC+", "CCC-"
        ConvertRatingToEnum = CCC
    Case Else
        ConvertRatingToEnum = D
    End Select
End Function

Public Function ConvertRatingtoSTR(iRatingEnum As SPRatings) As String
    Select Case iRatingEnum
    Case SPRatings.Aaa
        ConvertRatingtoSTR = "AAA"
    Case SPRatings.AAplus
        ConvertRatingtoSTR = "AA+"
    Case SPRatings.Aa
        ConvertRatingtoSTR = "AA"
    Case SPRatings.AAminus
        ConvertRatingtoSTR = "AA-"
    Case SPRatings.Aplus
        ConvertRatingtoSTR = "A+"
    Case SPRatings.A
        ConvertRatingtoSTR = "A"
    Case SPRatings.Aminus
        ConvertRatingtoSTR = "A-"
    Case SPRatings.BBBplus
        ConvertRatingtoSTR = "BBB+"
    Case SPRatings.BBB
        ConvertRatingtoSTR = "BBB"
    Case SPRatings.BBBminus
        ConvertRatingtoSTR = "BBB-"
    Case SPRatings.BBplus
        ConvertRatingtoSTR = "BB+"
    Case SPRatings.BB
        ConvertRatingtoSTR = "BB"
    Case SPRatings.BBminus
        ConvertRatingtoSTR = "BB-"
    Case SPRatings.Bplus
        ConvertRatingtoSTR = "B+"
    Case SPRatings.b
        ConvertRatingtoSTR = "B"
    Case SPRatings.Bmiuns
        ConvertRatingtoSTR = "B-"
    Case SPRatings.CCC
        ConvertRatingtoSTR = "CCC"
    Case SPRatings.D
        ConvertRatingtoSTR = "D"
    End Select

End Function

Public Function ConverRatingToEnumMoody(iRating As String) As MoodyRating
    Select Case Trim(UCase(iRating))
        Case "AAA"
            ConverRatingToEnumMoody = MoodyRating.Aaa
        Case "AA1"
            ConverRatingToEnumMoody = MoodyRating.Aa1
        Case "AA2"
            ConverRatingToEnumMoody = MoodyRating.Aa2
        Case "AA3"
            ConverRatingToEnumMoody = MoodyRating.Aa3
        Case "A1"
            ConverRatingToEnumMoody = MoodyRating.A1
        Case "A2"
            ConverRatingToEnumMoody = MoodyRating.A2
        Case "A3"
            ConverRatingToEnumMoody = MoodyRating.A3
        Case "BAA1"
            ConverRatingToEnumMoody = MoodyRating.Baa1
        Case "BAA2"
            ConverRatingToEnumMoody = MoodyRating.Baa2
        Case "BAA3"
            ConverRatingToEnumMoody = MoodyRating.Baa3
        Case "BA1"
            ConverRatingToEnumMoody = MoodyRating.Ba1
        Case "BA2"
            ConverRatingToEnumMoody = MoodyRating.Ba2
        Case "BA3"
            ConverRatingToEnumMoody = MoodyRating.Ba3
        Case "B1"
            ConverRatingToEnumMoody = MoodyRating.B1
        Case "B2"
            ConverRatingToEnumMoody = MoodyRating.B2
        Case "B3"
            ConverRatingToEnumMoody = MoodyRating.B3
        Case "CAA1"
            ConverRatingToEnumMoody = MoodyRating.Caa1
        Case "CAA2"
            ConverRatingToEnumMoody = MoodyRating.Caa2
        Case "CAA3"
            ConverRatingToEnumMoody = MoodyRating.Caa3
        Case "CA"
            ConverRatingToEnumMoody = MoodyRating.Ca
        Case "C"
            ConverRatingToEnumMoody = MoodyRating.C
    End Select
End Function
Public Function ConverRatingToFactor(iRating As String) As Long
    Select Case Trim(UCase(iRating))
        Case "AAA"
            ConverRatingToFactor = 1
        Case "AA1"
            ConverRatingToFactor = 10
        Case "AA2"
            ConverRatingToFactor = 20
        Case "AA3"
            ConverRatingToFactor = 40
        Case "A1"
            ConverRatingToFactor = 70
        Case "A2"
            ConverRatingToFactor = 120
        Case "A3"
            ConverRatingToFactor = 180
        Case "BAA1"
            ConverRatingToFactor = 260
        Case "BAA2"
            ConverRatingToFactor = 360
        Case "BAA3"
            ConverRatingToFactor = 610
        Case "BA1"
            ConverRatingToFactor = 940
        Case "BA2"
            ConverRatingToFactor = 1350
        Case "BA3"
            ConverRatingToFactor = 1766
        Case "B1"
            ConverRatingToFactor = 2220
        Case "B2"
            ConverRatingToFactor = 2720
        Case "B3"
            ConverRatingToFactor = 3490
        Case "CAA1"
            ConverRatingToFactor = 4770
        Case "CAA2"
            ConverRatingToFactor = 6500
        Case "CAA3"
            ConverRatingToFactor = 8070
        Case "CA"
            ConverRatingToFactor = 10000
        Case "C"
            ConverRatingToFactor = 10000
    End Select
End Function
