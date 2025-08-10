VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "RatingMigrationItem"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
Private Type RatingHist
    Upgrades As Long
    Downgrades As Long
    NumAAA As Long
    NumAAp As Long
    NumAAm As Long
    NumAA As Long
    NumAp As Long
    NumA As Long
    NumAm As Long
    NumBBBp As Long
    NumBBB As Long
    NumBBBm As Long
    NumBBp As Long
    NumBB As Long
    numBBm As Long
    NumBp As Long
    NumB As Long
    NumBm As Long
    NumCCCAssets As Long
    NumDefaults As Long
    NumMatures As Long
    NumPeriodDefaults As Long
    NumPerforming As Long
End Type
Private Type RatingHistBal
    BalAAA As Double
    BalAA1 As Double
    BalAA2 As Double
    BalAA3 As Double
    BalA1 As Double
    BalA2 As Double
    BalA3 As Double
    BalBBB1 As Double
    BalBBB2 As Double
    BalBBB3 As Double
    BalBB1 As Double
    BalBB2 As Double
    BalBB3 As Double
    BalB1 As Double
    BalB2 As Double
    BalB3 As Double
    BalCCC As Double
    BalPeriodDefaults  As Double
    BalDefaults As Double
    BalMature As Double
    BalPerforming As Double
    CDR As Double
End Type
Private Enum SPRatings
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
Private Type SimHistory
    RatingHist() As RatingHist
    RatingHistBal() As RatingHistBal
End Type
Private clsNumMonths As Long
Private clsSimHist() As SimHistory
Private clsAnalysisDate As Date
Private clsMaturityDate As Date
Private clsDateDict As Dictionary
Private clsNumPeriods As Long
Private clsName As String

Public Sub Constructor(iName As String, ianalysisDate As Date, iMaturityDate As Date, iNumSims As Long, iperiod As String)
    Dim i As Long
    Dim lmonth As Long
    clsAnalysisDate = ianalysisDate
    clsMaturityDate = ianalysisDate
    clsName = iName
    Set clsDateDict = New Dictionary
    clsDateDict.Add ianalysisDate, 0
    
    If UCase(iperiod) = "ANNUALLY" Then
        lmonth = 12
    ElseIf UCase(iperiod) = "SEMI-ANNUALLY" Then
        lmonth = 6
    Else
        lmonth = 3
    End If
    clsNumMonths = lmonth
    Do While clsMaturityDate < iMaturityDate
        i = i + 1
        clsMaturityDate = DateAdd("M", lmonth, clsMaturityDate)
        clsDateDict.Add clsMaturityDate, i
    Loop
    clsNumPeriods = i
    ReDim clsSimHist(iNumSims - 1)
    For i = 0 To iNumSims - 1
        ReDim clsSimHist(i).RatingHist(clsNumPeriods)
        ReDim clsSimHist(i).RatingHistBal(clsNumPeriods)
    Next i
End Sub
Public Sub AddRatingAndBalance(iSim As Long, iDate As Date, iRating As String, iBalance As Double)
    Call AddRating(iSim, iDate, iRating)
    Call AddBalance(iSim, iDate, iRating, iBalance)
End Sub
Public Sub AddRating(iSim As Long, iDate As Date, iRating As String)
    Dim iIndex As Long
    iIndex = clsDateDict(iDate)
    With clsSimHist(iSim - 1).RatingHist(iIndex)
        Select Case iRating
        Case "AAA"
            .NumAAA = .NumAAA + 1
        Case "AA+"
            .NumAAp = .NumAAp + 1
        Case "AA"
            .NumAA = .NumAA + 1
        Case "AA-"
            .NumAAm = .NumAAm + 1
        Case "A+"
            .NumAp = .NumAp + 1
        Case "A"
            .NumA = .NumA + 1
        Case "A-"
            .NumAm = .NumAm + 1
        Case "BBB+"
            .NumBBBp = .NumBBBp + 1
        Case "BBB"
            .NumBBB = .NumBBB + 1
        Case "BBB-"
            .NumBBBm = .NumBBBm + 1
        Case "BB+"
            .NumBBp = .NumBBp + 1
        Case "BB"
            .NumBB = .NumBB + 1
        Case "BB-"
            .numBBm = .numBBm + 1
        Case "B+"
            .NumBp = .NumBp + 1
        Case "B"
            .NumB = .NumB + 1
        Case "B-"
            .NumBm = .NumBm + 1
        Case "CCC", "CCC+", "CCC-"
            .NumCCCAssets = .NumCCCAssets + 1
        Case "D"
            If iIndex = 0 Then
                .NumDefaults = .NumDefaults + 1
            Else
                .NumPeriodDefaults = .NumPeriodDefaults + 1
            End If
        Case "M"
            .NumMatures = .NumMatures + 1
        Case Else
            Debug.Print "what"
        End Select
    End With
End Sub
Public Sub AddBalance(iSim As Long, iDate As Date, iRating As String, iBalance As Double)
    Dim iIndex As Long
    Dim lLastPerfBalance As Double
    iIndex = clsDateDict(iDate)
    If iIndex > 0 Then
        lLastPerfBalance = clsSimHist(iSim - 1).RatingHistBal(iIndex - 1).BalPerforming
    End If
    With clsSimHist(iSim - 1).RatingHistBal(iIndex)
        Select Case iRating
        Case "AAA"
            .BalAAA = .BalAAA + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "AA+"
            .BalAA1 = .BalAA1 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "AA"
            .BalAA2 = .BalAA2 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "AA-"
            .BalAA3 = .BalAA3 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "A+"
            .BalA1 = .BalA1 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "A"
            .BalA2 = .BalA2 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "A-"
            .BalA3 = .BalA3 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BBB+"
            .BalBBB1 = .BalBBB1 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BBB"
            .BalBBB2 = .BalBBB2 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BBB-"
            .BalBBB3 = .BalBBB3 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BB+"
            .BalBB1 = .BalBB1 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BB"
            .BalBB2 = .BalBB2 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "BB-"
            .BalBB3 = .BalBB3 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "B+"
            .BalB1 = .BalB1 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "B"
            .BalB2 = .BalB2 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "B-"
            .BalB3 = .BalB3 + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "CCC", "CCC+", "CCC-"
            .BalCCC = .BalCCC + iBalance
            .BalPerforming = .BalPerforming + iBalance
        Case "D"
            If iIndex = 0 Then
                .BalDefaults = .BalDefaults + iBalance
            Else
                .BalPeriodDefaults = .BalPeriodDefaults + iBalance
            End If
        Case "M"
            .BalMature = .BalMature + iBalance
        Case Else
            'Debug.Assert 1 <> 1
        End Select
        If lLastPerfBalance > 0 Then
            .CDR = (.BalPeriodDefaults / lLastPerfBalance)
            If clsNumMonths = 3 Then
                .CDR = .CDR * 4
            ElseIf clsNumMonths = 6 Then
                .CDR = .CDR * 2
            End If
        End If
    End With
End Sub
Public Sub UpdateDefaults(iSim As Long)
    Dim lIndex As Long
    For lIndex = 1 To clsNumPeriods
        clsSimHist(iSim - 1).RatingHistBal(lIndex).BalDefaults = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalPeriodDefaults + clsSimHist(iSim - 1).RatingHistBal(lIndex - 1).BalDefaults
        clsSimHist(iSim - 1).RatingHist(lIndex).NumDefaults = clsSimHist(iSim - 1).RatingHist(lIndex).NumPeriodDefaults + clsSimHist(iSim - 1).RatingHist(lIndex - 1).NumDefaults
    Next lIndex
End Sub
Public Sub AddUpgrade(iSim As Long, iDate As Date)
    Dim iIndex As Long
    iIndex = clsDateDict(iDate)
    With clsSimHist(iSim - 1).RatingHist(iIndex)
        .Upgrades = .Upgrades + 1
    End With
End Sub
Public Sub AddDowngrade(iSim As Long, iDate As Date)
    Dim iIndex As Long
    iIndex = clsDateDict(iDate)
    With clsSimHist(iSim - 1).RatingHist(iIndex)
        .Downgrades = .Downgrades + 1
    End With
End Sub
Public Function GeStatData(iStat As String, iField As String, iDate As Date) As Double
    'For a data point get a stat on it
    Dim lOutDBL As Double
    Dim lOUTData() As Double
    lOUTData = GetSimData(UCase(iField), iDate)
    Select Case UCase(iStat)
    Case "MIN"
        lOutDBL = Math.MinDBL(lOUTData)
    Case "MAX"
        lOutDBL = Math.MaxDBL(lOUTData)
    Case "AVERAGE"
        lOutDBL = Math.AverageDBL(lOUTData)
    Case "MEDIAN"
        lOutDBL = Math.MedianDBL(lOUTData)
    Case "STDDEV"
        lOutDBL = Math.STDDBL(lOUTData)
    End Select
    GeStatData = lOutDBL
End Function
Public Function GetSimData(iField As String, iDate As Date) As Double()
    'Get all the simulation for a date
    Dim lOUTData() As Double
    ReDim lOUTData(UBound(clsSimHist))
    Dim i As Long
    For i = 1 To UBound(clsSimHist) + 1
        lOUTData(i - 1) = GetSimDataPoint(i, iDate, UCase(iField))
    Next i
    GetSimData = lOUTData
End Function
Public Function GetSimTimeSeries(iSim As Long, iField) As Double()
    Dim lOUTData() As Double
    Dim lDateKeys As Variant
    Dim i As Long
    lDateKeys = clsDateDict.Keys
    ReDim lOUTData(UBound(lDateKeys))
    For i = 0 To UBound(lDateKeys)
        lOUTData(i) = GetSimDataPoint(iSim, CDate(lDateKeys(i)), UCase(iField))
    Next i
    GetSimTimeSeries = lOUTData
End Function
Public Function GetSimDataPoint(iSim As Long, iDate As Date, iField As String) As Double
    Dim lIndex As Long
    Dim lVal As Double
    lIndex = clsDateDict(iDate)
    Select Case UCase(iField)
    Case "UPGRADES"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).Upgrades
    Case "DOWNGRADES"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).Downgrades
    Case "NUMAAA"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAAA
    Case "NUMAAP"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAAp
    Case "NUMAA"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAA
    Case "NUMAAM"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAAm
    Case "NUMAP"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAp
    Case "NUMA"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumA
    Case "NUMAM"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumAm
    Case "NUMBBBP"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBBBp
    Case "NUMBBB"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBBB
    Case "NUMBBBM"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBBBm
    Case "NUMBBP"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBBp
    Case "NUMBB"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBB
    Case "NUMBBM"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).numBBm
    Case "NUMBP"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBp
    Case "NUMB"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumB
    Case "NUMBM"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumBm
    Case "NUMCCC"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumCCCAssets
    Case "NUMPERDEF"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumPeriodDefaults
    Case "NUMMAT"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumMatures
    Case "NUMPERF"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumPerforming
    Case "NUMDEF"
        lVal = clsSimHist(iSim - 1).RatingHist(lIndex).NumDefaults
    Case "BALAAA"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalAAA
    Case "BALAAP"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalAA1
    Case "BALAA"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalAA2
    Case "BALAAM"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalAA3
    Case "BALAP"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalA1
    Case "BALA"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalA2
    Case "BALAM"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalA3
    Case "BALBBBP"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBBB1
    Case "BALBBB"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBBB2
    Case "BALBBBM"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBBB3
    Case "BALBBP"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBB1
    Case "BALBB"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBB2
    Case "BALBBM"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalBB3
    Case "BALBP"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalB1
    Case "BALB"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalB2
    Case "BALBM"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalB3
    Case "BALCCC"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalCCC
    Case "BALPERDEF"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalPeriodDefaults
    Case "BALMAT"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalMature
    Case "BALPERF"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalPerforming
    Case "BALDEF"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).BalDefaults
    Case "CDR"
        lVal = clsSimHist(iSim - 1).RatingHistBal(lIndex).CDR
    End Select
    GetSimDataPoint = lVal
End Function
