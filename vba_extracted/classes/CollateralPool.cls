VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CollateralPool"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit

Private clsAccountsDict As Dictionary
Private clsAssetsDict As Dictionary

Private clsConcentrationTest As ConcentrationTest
Private clsRatingsDeriv As RatingDerivations
Private clsTestSetting As TestSettings
Private clsReRunTest As Boolean
Private clsAnalysisDate As Date
Public Function CheckAccountBalance(iType As AccountType, icash As CashType) As Double
    If icash = Principal Then
        CheckAccountBalance = clsAccountsDict(iType).PrincipalProceeds
    ElseIf icash = Interest Then
        CheckAccountBalance = clsAccountsDict(iType).InterestProceeds
    ElseIf icash = Total Then
        CheckAccountBalance = clsAccountsDict(iType).TotalProceeds
    End If
End Function

Public Function GetBLKRockIDs() As Variant()
    GetBLKRockIDs = clsAssetsDict.Keys
End Function
Public Function GetObjectiveDict() As Dictionary
    Set GetObjectiveDict = clsConcentrationTest.GetObjectiveDict
End Function
Public Function GetObjectiveValue() As Double
    If clsReRunTest Then Call CalcConcentrationTest
    GetObjectiveValue = clsConcentrationTest.CalcObjectiveFunction
End Function
Public Function GetAssetObjective(iAssetDict As Dictionary, iTransType As TransactionType) As Dictionary
    If clsReRunTest Then Call CalcConcentrationTest
    Set GetAssetObjective = clsConcentrationTest.CalcAssetObject2(iAssetDict, iTransType)
End Function

Public Function GetCollatParAmount(Optional iFilter As String) As Double
    Dim lBlkRockID As Variant
    Dim lParAmount As Double
    For Each lBlkRockID In clsAssetsDict.Keys
        If Len(iFilter) = 0 Then
            lParAmount = lParAmount + clsAssetsDict(lBlkRockID).ParAmount
        ElseIf clsAssetsDict(lBlkRockID).ApplyFilter(iFilter) Then
            lParAmount = lParAmount + clsAssetsDict(lBlkRockID).ParAmount
        End If
    Next
    GetCollatParAmount = lParAmount
End Function

Public Sub SetAnalysisDate(iDate As Date)
    clsAnalysisDate = iDate
End Sub

Public Sub AddAsset(iAsset As Asset, Optional iReduceCash As Boolean, Optional iType As AccountType)
    Dim lAsset As Asset
    
    If clsAssetsDict.Exists(iAsset.BLKRockID) Then
        clsAssetsDict(iAsset.BLKRockID).AddPar iAsset.ParAmount
    Else
        Set lAsset = iAsset.Copy
        If Len(iAsset.MDYRating) = 0 Then
            clsRatingsDeriv.GetMoodysRating lAsset
        End If
        If Len(iAsset.MDYDPRating) = 0 Then
            clsRatingsDeriv.GetMoodysDefProbRating lAsset
        End If
        If Len(iAsset.MDYDPRatingWARF) = 0 Then
            clsRatingsDeriv.GetMoodysDefProbRatingWARF lAsset
        End If
        
        If Len(iAsset.SPRating) = 0 Then
            clsRatingsDeriv.GetSnPRatings lAsset
        End If
        If iAsset.MDYRecoveryRate = 0 Then
            clsRatingsDeriv.MoodyRecoveryRate lAsset
        End If
        If clsAnalysisDate > 0 Then
            lAsset.AddMoodyRating clsAnalysisDate, lAsset.MDYRating
            lAsset.AddSPRating clsAnalysisDate, lAsset.SPRating
        End If
        clsAssetsDict.Add lAsset.BLKRockID, lAsset
    End If
    clsReRunTest = True
End Sub
Public Sub RemoveAsset(iBLKRockID As String)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict.Remove (iBLKRockID)
    End If
    clsReRunTest = True
End Sub
Public Function GetAsset(iBLKRockID As String) As Asset
    'This gets a copy
    If clsAssetsDict.Exists(iBLKRockID) Then
        Set GetAsset = clsAssetsDict(iBLKRockID).Copy
    End If
End Function
Public Function GetAssetNonCopy(iBLKRockID As String) As Asset
    If clsAssetsDict.Exists(iBLKRockID) Then
        Set GetAssetNonCopy = clsAssetsDict(iBLKRockID)
    End If
End Function
Public Function GetAssetParameter(iBLKRockID As String, iParameter As String) As Variant
    If clsAssetsDict.Exists(iBLKRockID) Then
        Select Case UCase(iParameter)
        Case "MARKET VALUE"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MarketValue
        Case "PAR AMOUNT"
            GetAssetParameter = clsAssetsDict(iBLKRockID).ParAmount
        Case "S & P RATING", "S&P RATING"
            GetAssetParameter = clsAssetsDict(iBLKRockID).SPRating
        Case "S&P INDUSTRY"
            GetAssetParameter = clsAssetsDict(iBLKRockID).SPIndustry
        Case "MOODY'S INDUSTRY"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MDYIndustry
        Case "MOODY'S RATING"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MDYRating
        Case "MOODY'S RATING WARF"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MDYDPRatingWARF
         Case "MOODY'S RATING DPR"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MDYDPRating
        Case "DEFAULTED"
            GetAssetParameter = clsAssetsDict(iBLKRockID).DefaultAsset
        Case "MATURITY"
            GetAssetParameter = clsAssetsDict(iBLKRockID).Maturity
        Case "WAL"
            GetAssetParameter = clsAssetsDict(iBLKRockID).WAL
        Case "ISSUE NAME"
            GetAssetParameter = clsAssetsDict(iBLKRockID).IssuerName
        Case "COV-LITE"
            GetAssetParameter = clsAssetsDict(iBLKRockID).CovLite
        Case "COUNTRY"
            GetAssetParameter = clsAssetsDict(iBLKRockID).Country
        Case "FACILITY SIZE"
            GetAssetParameter = clsAssetsDict(iBLKRockID).FacilitySize
        Case "ANALYST OPINION"
            GetAssetParameter = clsAssetsDict(iBLKRockID).AnalystOpinion
        Case "SPREAD"
            GetAssetParameter = clsAssetsDict(iBLKRockID).CpnSpread
        Case "LIBOR FLOOR"
            GetAssetParameter = clsAssetsDict(iBLKRockID).LiborFloor
        Case "MOODY'S RECOVERY RATE"
            GetAssetParameter = clsAssetsDict(iBLKRockID).MDYRecoveryRate
        End Select
    End If
End Function
Public Function GetRankings(iRankInputs() As HypoInputs) As Dictionary
    Dim lRankDict As Dictionary
    Dim lOutputVar As Variant
    Dim lBResult() As Results
    Dim lAResult() As Results
    Dim lBObject As Double
    Dim lAObject As Double
    Dim i As Long
    
    If clsReRunTest Then
        Call CalcConcentrationTest
    End If
    lBObject = clsConcentrationTest.CalcObjectiveFunction
    
    Set lRankDict = New Dictionary
    For i = LBound(iRankInputs) To UBound(iRankInputs)
        If UCase(iRankInputs(i).Transaction) = "BUY" Then
            Call PurchaseAsset(iRankInputs(i).Asset, iRankInputs(i).Price)
        ElseIf UCase(iRankInputs(i).Transaction) = "SALE" Or UCase(iRankInputs(i).Transaction) = "SELL" Then
            Call SaleAsset(iRankInputs(i).Asset, iRankInputs(i).Price)
        End If
    
        Call CalcConcentrationTest(True)
        lAObject = clsConcentrationTest.CalcObjectiveFunction
        

        'If lAObject > lBObject Then
            lRankDict.Add iRankInputs(i).Asset.BLKRockID, lAObject
        'End If

        If UCase(iRankInputs(i).Transaction) = "BUY" Then
            Call SaleAsset(iRankInputs(i).Asset, iRankInputs(i).Price)
        ElseIf UCase(iRankInputs(i).Transaction) = "SALE" Or UCase(iRankInputs(i).Transaction) = "SELL" Then
            Call PurchaseAsset(iRankInputs(i).Asset, iRankInputs(i).Price)
        End If
      Next i

    Set GetRankings = lRankDict
End Function


Public Function CalcAverageParAmount() As Double
    Dim lBlkRockID As Variant
    Dim lNumerator As Double
    
    For Each lBlkRockID In clsAssetsDict.Keys
        lNumerator = lNumerator + clsAssetsDict(lBlkRockID).ParAmount
    Next
    CalcAverageParAmount = lNumerator / clsAssetsDict.Count
End Function

Public Sub AddAccount(iAccount As Accounts, iType As AccountType)
    clsAccountsDict.Add iType, iAccount
    clsReRunTest = True
End Sub
Public Sub AddCash(iType As AccountType, icash As CashType, iAmount As Double)
    clsAccountsDict(iType).Add icash, iAmount
    clsReRunTest = True
End Sub

Public Sub AddTestSettings(iTestSet As TestSettings)
    clsTestSetting = iTestSet
End Sub

Public Function AssetExist(iBLKRockID As String) As Boolean
    If clsAssetsDict.Exists(iBLKRockID) Then
        AssetExist = True
    End If
End Function

Public Sub AddPar(iBLKRockID As String, iAmount As Double)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict(iBLKRockID).AddPar iAmount
    End If
    If Abs(clsAssetsDict(iBLKRockID).ParAmount) <= 1 Then
        clsAssetsDict.Remove iBLKRockID
    End If
End Sub

Public Sub CalcConcentrationTest(Optional iNotUpdate As Boolean)
    Dim lPrincipalProceeds As Double
    
    lPrincipalProceeds = clsAccountsDict(AccountType.Collection).PrincipalProceeds
    clsConcentrationTest.RunTest clsAssetsDict, lPrincipalProceeds
    If Not (iNotUpdate = True) Then
        clsConcentrationTest.UpdatePreviousValues
    End If
    clsReRunTest = False
 
      

End Sub
Public Function GetTestResult() As Results()
    If clsReRunTest Then Call CalcConcentrationTest
    GetTestResult = clsConcentrationTest.GetResults
End Function
Public Sub PurchaseAsset(iAsset As Asset, Optional iPrice As Double)
    Dim lCashOnHand As Double
    Dim lAmount As Double
    Dim lPrice As Double
    Dim lRedParAmount As Double ' Amount to reduce par by.
    
    If iPrice = 0 Then
        lPrice = iAsset.MarketValue / 100
    Else
        If iPrice > 1 Then
            lPrice = iPrice / 100
        Else
            lPrice = iPrice
        End If
    End If
    
    lAmount = lPrice * iAsset.ParAmount
    lCashOnHand = clsAccountsDict(AccountType.Collection).PrincipalProceeds
    If lAmount > lCashOnHand Then
        'The purchase is greater then the cash amount reduce cash and par amount of the asset
        lRedParAmount = lCashOnHand / lPrice
        lRedParAmount = lRedParAmount - iAsset.ParAmount
        iAsset.AddPar lRedParAmount
        lAmount = lCashOnHand
    End If
    clsAccountsDict(AccountType.Collection).Add CashType.Principal, -lAmount
    Call AddAsset(iAsset)
    
    clsReRunTest = True
End Sub
Public Sub SaleAsset(iAsset As Asset, Optional iPrice As Double)
    Dim lAmount As Double
    Dim lPrice As Double
    Dim lReducePar As Double
    If clsAssetsDict.Exists(iAsset.BLKRockID) Then
        If iPrice = 0 Then
            lPrice = iAsset.MarketValue / 100
        Else
            If iPrice > 1 Then
                lPrice = iPrice / 100
            Else
                lPrice = iPrice
            End If
        End If
        If iAsset.ParAmount > clsAssetsDict(iAsset.BLKRockID).ParAmount Then
            lReducePar = clsAssetsDict(iAsset.BLKRockID).ParAmount - iAsset.ParAmount
            iAsset.AddPar lReducePar
        End If
        lAmount = iAsset.ParAmount * lPrice
        clsAccountsDict(AccountType.Collection).Add CashType.Principal, lAmount
        Call AddPar(iAsset.BLKRockID, -iAsset.ParAmount)
        
    End If
    
    clsReRunTest = True
End Sub

Private Sub Class_Initialize()
    Set clsAccountsDict = New Dictionary
    Set clsAssetsDict = New Dictionary
    Set clsRatingsDeriv = New RatingDerivations
    clsReRunTest = True
End Sub

Private Sub Class_Terminate()
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        Set lAsset = Nothing
    Next

    Set clsAccountsDict = Nothing
    Set clsAssetsDict = Nothing
    Set clsConcentrationTest = Nothing
    Set clsRatingsDeriv = Nothing
End Sub

Public Sub AddSPRating(iBLKRockID As String, iDate As Date, iRating As String)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict(iBLKRockID).AddSPRating iDate, iRating
    End If
End Sub
Public Sub AddMoodyRating(iBLKRockID As String, iDate As Date, iRating As String)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict(iBLKRockID).AddMoodyRating iDate, iRating
    End If
End Sub
Public Sub CalcCF(Optional iCurrBalance As Double, Optional iInitalSettlementDate As Date, Optional ianalysisDate As Date, Optional iPrepay As Variant, Optional iDefault As Variant, Optional iSeverity As Variant, Optional iLagMonth As Long, Optional iEndCFDate As Date, Optional iYC As YieldCurve)
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        lAsset.CalcCF iCurrBalance, iInitalSettlementDate, ianalysisDate, iPrepay, iDefault, iSeverity, iLagMonth, iEndCFDate, iYC
    Next
End Sub
Public Sub ReesetAssets()
    'use doing simulations
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim lParAmount As Double
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = Nothing
        Set lAsset = clsAssetsDict(lBlkRockID)
        lAsset.ResetForSimulation clsAnalysisDate
    Next
End Sub

Public Function LastMaturityDate() As Date
    Dim lBlkRockID As Variant
    Dim lLastDate As Date
    
    
    For Each lBlkRockID In clsAssetsDict.Keys
        If clsAssetsDict(lBlkRockID).Maturity > lLastDate Then
            lLastDate = clsAssetsDict(lBlkRockID).Maturity
        End If
    Next
    LastMaturityDate = lLastDate
End Function

Public Sub SetTest(iConTest As ConcentrationTest)
    Set clsConcentrationTest = iConTest
End Sub

Public Function GetTestResultsOutput() As Variant
    If clsReRunTest Then Call CalcConcentrationTest
    GetTestResultsOutput = clsConcentrationTest.GetResultOutput
End Function


'Public Sub SetHypoInputs(iHypoAssets() As HypoInputs)
'     clsHypoAssets() = iHypoAssets
'End Sub
Public Function NumOfAssets(Optional iFilter As String) As Long
    Dim lBlkRockID As Variant
    Dim lCounter As Long
    If Len(iFilter) = 0 Then
        NumOfAssets = clsAssetsDict.Count
    Else
        For Each lBlkRockID In clsAssetsDict.Keys
            If clsAssetsDict(lBlkRockID).ApplyFilter(iFilter) Then
                lCounter = lCounter + 1
            End If
        Next
    End If
End Function
Public Function GetHypoOutputs(iHypoAssets() As HypoInputs) As Variant
    Dim lOutputVar As Variant
    Dim lBResult() As Results
    Dim lAResult() As Results
    Dim lBObject As Double
    Dim lAObject As Double
    Dim i As Long
    
    lBResult = GetTestResult
    lBObject = clsConcentrationTest.CalcObjectiveFunction
    For i = LBound(iHypoAssets) To UBound(iHypoAssets)
        If UCase(iHypoAssets(i).Transaction) = "BUY" Then
            Call PurchaseAsset(iHypoAssets(i).Asset, iHypoAssets(i).Price)
        ElseIf UCase(iHypoAssets(i).Transaction) = "SALE" Or UCase(iHypoAssets(i).Transaction) = "SELL" Then
            Call SaleAsset(iHypoAssets(i).Asset, iHypoAssets(i).Price)
        End If
    Next i
    lAResult = GetTestResult
    lAObject = clsConcentrationTest.CalcObjectiveFunction
    clsConcentrationTest.UpdatePreviousValues
    For i = LBound(iHypoAssets) To UBound(iHypoAssets)
        If UCase(iHypoAssets(i).Transaction) = "BUY" Then
            Call SaleAsset(iHypoAssets(i).Asset, iHypoAssets(i).Price)
        ElseIf UCase(iHypoAssets(i).Transaction) = "SALE" Or UCase(iHypoAssets(i).Transaction) = "SELL" Then
            Call PurchaseAsset(iHypoAssets(i).Asset, iHypoAssets(i).Price)
        End If
    Next i
    ReDim lOutputVar(0 To UBound(lBResult) + 2, 0 To 9)
    lOutputVar(0, 0) = "Test Num"
    lOutputVar(0, 1) = "Test Name"
    lOutputVar(0, 2) = "Threshold"
    lOutputVar(0, 3) = "Results"
    lOutputVar(0, 4) = "Pass/Fail"
    lOutputVar(0, 5) = ""
    lOutputVar(0, 6) = "Hypo Result"
    lOutputVar(0, 7) = "Hypo Pass/Fail"
    lOutputVar(0, 8) = "Differences"
    lOutputVar(0, 9) = "Hypo Comments"
    For i = 0 To UBound(lBResult)
        lOutputVar(i + 1, 0) = lBResult(i).TestNumber
        lOutputVar(i + 1, 1) = lBResult(i).TestName
        lOutputVar(i + 1, 2) = lBResult(i).Threshold
        lOutputVar(i + 1, 3) = lBResult(i).Result
        lOutputVar(i + 1, 4) = lBResult(i).PassFail
        lOutputVar(i + 1, 5) = ""
        lOutputVar(i + 1, 6) = lAResult(i).Result
        lOutputVar(i + 1, 7) = lAResult(i).PassFail
        lOutputVar(i + 1, 8) = lOutputVar(i + 1, 6) - lOutputVar(i + 1, 3)
        lOutputVar(i + 1, 9) = lAResult(i).PassFailComment
        'formatting
        Select Case lBResult(i).TestNumber
        
        Case 36, 37, 35, 40, 54
            lOutputVar(i + 1, 2) = Format(lOutputVar(i + 1, 2), "0.00")
            lOutputVar(i + 1, 3) = Format(lOutputVar(i + 1, 3), "0.00")
            lOutputVar(i + 1, 6) = Format(lOutputVar(i + 1, 6), "0.00")
            lOutputVar(i + 1, 8) = Format(lOutputVar(i + 1, 8), "0.00")
        Case Else
            lOutputVar(i + 1, 2) = Format(lOutputVar(i + 1, 2), "0.000%")
            lOutputVar(i + 1, 3) = Format(lOutputVar(i + 1, 3), "0.000%")
            lOutputVar(i + 1, 6) = Format(lOutputVar(i + 1, 6), "0.000%")
            lOutputVar(i + 1, 8) = Format(lOutputVar(i + 1, 8), "0.000%")
        End Select
    Next i
    lOutputVar(UBound(lBResult) + 2, 2) = "Objective Function"
    lOutputVar(UBound(lBResult) + 2, 3) = lBObject
    lOutputVar(UBound(lBResult) + 2, 6) = lAObject
     lOutputVar(UBound(lBResult) + 2, 8) = Format(lAObject - lBObject, "0.00")
    GetHypoOutputs = lOutputVar
End Function

Public Sub SetUseRM(iValue As Boolean)
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        clsAssetsDict(lBlkRockID).UseRM = iValue
    Next
End Sub

Public Function ApplyFilter(iFilter As String) As Dictionary
    Dim lDictionary As Dictionary
    Dim lBlkRockID As Variant
    Set lDictionary = New Dictionary
    For Each lBlkRockID In clsAssetsDict.Keys
        If clsAssetsDict(lBlkRockID).ApplyFilter(iFilter) Then
            lDictionary.Add lBlkRockID, 1
        End If
    Next
    Set ApplyFilter = lDictionary
End Function
