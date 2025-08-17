VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "RatingMigrationOutput"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
'this will be used to hold asset from CreditMigration Module.
'It should only be called through this module
Private clsDealDict As Dictionary 'Just a convientwau to find information
Private clsDateDict As Dictionary
Private clsNumSims As Long
Private clsNumDeals As Long
Private clsLastMatDate As Date
Private clsAnalysisDate As Date
Public Sub Constructor(iNumDeals() As String, iNumSims As Long, ianalysisDate As Date, iLastMatDate As Date, iperiod As String)
    Dim i As Long
    Dim lRateItem As RatingMigrationItem
    Dim lmonth As Long
    
    Set clsDealDict = New Dictionary
        
    If UCase(iperiod) = "ANNUALLY" Then
        lmonth = 12
    ElseIf UCase(iperiod) = "SEMI-ANNUALLY" Then
        lmonth = 6
    Else
        lmonth = 3
    End If
    
    
    For i = 0 To UBound(iNumDeals)
        Set lRateItem = New RatingMigrationItem
        Call lRateItem.Constructor(iNumDeals(i), ianalysisDate, iLastMatDate, iNumSims, iperiod)
        Call clsDealDict.Add(iNumDeals(i), lRateItem)
    Next i
    
    i = 0
    clsAnalysisDate = ianalysisDate
    clsLastMatDate = ianalysisDate
    Set clsDateDict = New Dictionary
    clsNumSims = iNumSims
    Call clsDateDict.Add(clsLastMatDate, i)
    Do While clsLastMatDate < iLastMatDate
        i = i + 1
        clsLastMatDate = DateAdd("M", lmonth, clsLastMatDate)
        Call clsDateDict.Add(clsLastMatDate, i)
    Loop
End Sub
Public Sub AddDeal(iDealName As String, iDealCollat As CollateralPool, iSim As Long)
    Dim lRatingItem As RatingMigrationItem
    Dim lCurDate As Date
    Dim lCurrRating As String
    Dim lPrevRating As String
    Dim lAssetKeys As Variant
    Dim lDateKeys As Variant
    Dim lAsset As Asset
    Dim lBal As Double
    Dim lMat As Double
    Dim i As Long
    Dim j As Long
    
    lAssetKeys = iDealCollat.GetBLKRockIDs
    lDateKeys = clsDateDict.Keys
    iDealCollat.CalcCF , , clsAnalysisDate, 0, "MIGRATION"
    Set lRatingItem = clsDealDict(iDealName)
    For i = 0 To UBound(lAssetKeys)
        Set lAsset = iDealCollat.GetAssetNonCopy(CStr(lAssetKeys(i)))
        lBal = lAsset.ParAmount
        If lAsset.DefaultAsset Then
            lCurrRating = "D"
        Else
            lCurrRating = lAsset.SPRating
            If lCurrRating = "CCC+" Or lCurrRating = "CCC-" Or lCurrRating = "CC" Or lCurrRating = "C" Or lCurrRating = "CCC" Then
                lCurrRating = "CCC"
            End If
        End If
        Call lRatingItem.AddRatingAndBalance(iSim, clsAnalysisDate, lCurrRating, lBal)
        'If lCurrRating = "D" Then continue
        For j = 1 To UBound(lDateKeys)
            lPrevRating = lCurrRating
            lCurDate = CDate(lDateKeys(j))
            lCurrRating = lAsset.GetSPRating(lCurDate)
            lBal = lAsset.GetBegBalance(lCurDate)
            lMat = lAsset.GetSchedPrin(clsAnalysisDate, lCurDate)
            If lCurrRating = "D" And lBal = 0 And lPrevRating <> "D" Then 'It defaulted on a payment date
                lBal = lAsset.GetBegBalance(lCurDate - 1)
            End If
            
            Call lRatingItem.AddBalance(iSim, lCurDate, "M", lMat)
            If lCurrRating = "D" And lPrevRating <> "D" Then
                Call lRatingItem.AddRatingAndBalance(iSim, lCurDate, lCurrRating, lBal)
            ElseIf lCurrRating = "M" And lPrevRating <> "M" Then
                Call lRatingItem.AddRatingAndBalance(iSim, lCurDate, lCurrRating, lBal)
            ElseIf lCurrRating = "M" Or lCurrRating = "D" Then
                'Debug.Print "adam"
            ElseIf lCurrRating <> "D" And lCurrRating <> "M" Then
                Call lRatingItem.AddRatingAndBalance(iSim, lCurDate, lCurrRating, lBal)
                Select Case ConvertRatingToEnum(lPrevRating) - ConvertRatingToEnum(lCurrRating)
                Case Is < 0
                    Call lRatingItem.AddDowngrade(iSim, lCurDate)
                Case Is > 0
                    Call lRatingItem.AddUpgrade(iSim, lCurDate)
                End Select
            End If
        Next j
    Next i
    lRatingItem.UpdateDefaults (iSim)
End Sub
Public Function GetSimTimeSeries(iSim As Long, iField As String) As Variant
    Dim lOutput As Variant
    Dim lDealName As Variant
    Dim lRatingItem As RatingMigrationItem
    Dim lDate As Variant
    Dim lRow As Long
    Dim lColumn As Long
    ReDim lOutput(0 To clsDateDict.Count, 0 To clsDealDict.Count)
    lOutput(lRow, lColumn) = "Period"
    lRow = 1
    For Each lDate In clsDateDict.Keys
        lOutput(lRow, lColumn) = lDate
        lRow = lRow + 1
    Next lDate
    lColumn = 1
    For Each lDealName In clsDealDict.Keys
        lOutput(0, lColumn) = CStr(lDealName)
        lRow = 1
        Set lRatingItem = clsDealDict(lDealName)
        For Each lDate In clsDateDict.Keys
            lOutput(lRow, lColumn) = lRatingItem.GetSimDataPoint(iSim, CDate(lDate), UCase(iField))
            Select Case UCase(iField)
            Case "CDR"
                lOutput(lRow, lColumn) = Format(lOutput(lRow, lColumn), "0.000%")
            Case "NUMPERDEF"
                lOutput(lRow, lColumn) = Format(lOutput(lRow, lColumn), "0.000")
            End Select
            lRow = lRow + 1
        Next lDate
        lColumn = lColumn + 1
    Next lDealName
    GetSimTimeSeries = lOutput
End Function

Public Function StatTimeSeries(iStat As String, iField As String) As Variant
    Dim iSim As Long
    Select Case UCase(iStat)
    Case "MIN"
        iSim = GetSimMinDefaults
    Case "MAX"
        iSim = GetSimMaxDefaults
    Case "MEDIAN"
        iSim = GetSimMedianDefaults
    Case "AVERAGE"
        StatTimeSeries = AVGTimeSeries(iStat, iField)
    End Select
    If UCase(iStat) <> "AVERAGE" Then
        StatTimeSeries = GetSimTimeSeries(iSim, UCase(iField))
    End If
End Function
Public Function AVGTimeSeries(iStat As String, iField As String) As Variant

    Dim lOutput As Variant
    Dim lDealName As Variant
    Dim lRatingItem As RatingMigrationItem
    Dim lDate As Variant
    Dim lRow As Long
    Dim lColumn As Long
    ReDim lOutput(0 To clsDateDict.Count, 0 To clsDealDict.Count)
    lOutput(lRow, lColumn) = "Period"
    lRow = 1
    For Each lDate In clsDateDict.Keys
        lOutput(lRow, lColumn) = lDate
        lRow = lRow + 1
    Next lDate
    lColumn = 1
    For Each lDealName In clsDealDict.Keys
        lOutput(0, lColumn) = CStr(lDealName)
        lRow = 1
        Set lRatingItem = clsDealDict(lDealName)
        For Each lDate In clsDateDict.Keys
            lOutput(lRow, lColumn) = lRatingItem.GeStatData(UCase(iStat), UCase(iField), CDate(lDate))
            Select Case UCase(iField)
            Case "CDR"
                lOutput(lRow, lColumn) = Format(lOutput(lRow, lColumn), "0.000%")
            Case "NUMPERDEF", "BALPERDEF"
                lOutput(lRow, lColumn) = Format(lOutput(lRow, lColumn), "0.000")
            End Select
            lRow = lRow + 1
        Next lDate
        lColumn = lColumn + 1
    Next lDealName
    AVGTimeSeries = lOutput
End Function
Public Function GetSimMinDefaults() As Long
    'This Gets the Series with MIN Balance of Defaults across all time series
    Dim lTotalBalDefaults As Double
    Dim lPreviousBal As Double
    Dim lRatingItem As RatingMigrationItem
    Dim lSIM As Long
    Dim lDeal As Variant
    Dim i As Long
    
    
    For i = 1 To clsNumSims
        lTotalBalDefaults = 0
        For Each lDeal In clsDealDict.Keys
            Set lRatingItem = clsDealDict(lDeal)
            lTotalBalDefaults = lTotalBalDefaults + lRatingItem.GetSimDataPoint(i, clsLastMatDate, "BALDEF")
        Next lDeal
        If i = 1 Then
            lSIM = 1
            lPreviousBal = lTotalBalDefaults
        ElseIf lPreviousBal > lTotalBalDefaults Then
            lSIM = i
            lPreviousBal = lTotalBalDefaults
        End If
    Next i
    GetSimMinDefaults = lSIM
    
End Function
Public Function GetSimMedianDefaults() As Long
    Dim lTotalBalDefaults As Double
    Dim lRatingItem As RatingMigrationItem
    Dim lDeal As Variant
    Dim lSimBal As Dictionary
    Dim lMedian As Long
    Dim lBalance As Variant
    Dim i As Long
    Set lSimBal = New Dictionary
    
    For i = 1 To clsNumSims
        lTotalBalDefaults = 0
        For Each lDeal In clsDealDict.Keys
            Set lRatingItem = clsDealDict(lDeal)
            lTotalBalDefaults = lTotalBalDefaults + lRatingItem.GetSimDataPoint(i, clsLastMatDate, "BALDEF")
        Next lDeal
        'Debug.Print lTotalBalDefaults
        Call lSimBal.Add(lTotalBalDefaults, i)
    Next i
    Call modCollectionAndDictionaries.SortDictionary(lSimBal, True)
    lBalance = lSimBal.Keys
    If clsNumSims = 1 Then
        lMedian = 0
    ElseIf clsNumSims = 3 Then
        lMedian = 1
    Else
        lMedian = clsNumSims / 2
        'lMedian = lMedian + 1
    End If
    GetSimMedianDefaults = lSimBal(lBalance(lMedian))
End Function

Public Function GetSimMaxDefaults() As Long
    'This Gets the Series with MIN Balance of Defaults across all time series
    Dim lTotalBalDefaults As Double
    Dim lPreviousBal As Double
    Dim lRatingItem As RatingMigrationItem
    Dim lSIM As Long
    Dim lDeal As Variant
    Dim i As Long
    
    
    For i = 1 To clsNumSims
        lTotalBalDefaults = 0
        For Each lDeal In clsDealDict.Keys
            Set lRatingItem = clsDealDict(lDeal)
            lTotalBalDefaults = lTotalBalDefaults + lRatingItem.GetSimDataPoint(i, clsLastMatDate, "BALDEF")
        Next lDeal
        If i = 1 Then
            lSIM = 1
            lPreviousBal = lTotalBalDefaults
        ElseIf lPreviousBal < lTotalBalDefaults Then
            lSIM = i
            lPreviousBal = lTotalBalDefaults
        End If
    Next i
    GetSimMaxDefaults = lSIM
    
End Function

Private Sub Class_Initialize()

End Sub

Private Sub Class_Terminate()
    Set clsDealDict = Nothing
    Set clsDateDict = Nothing
End Sub
