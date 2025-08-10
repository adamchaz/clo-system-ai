VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CollateralPoolForCLO"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit
'The main difference between the collateralpoolforclo and collateralpool classees. Is that collateralPoolclass alows for other parmeters such as compliance test and accounts
'Most people would think that these are mebers of the clodeal and not the collateral cashflow. The collateralpool can stand alone for compliance test and hypo purpuses the
'collateralpoolforclo class can't
Private clsAssetsDict As Dictionary
Private clsRatingsDeriv As RatingDerivations
Private clsDealCFDict As Dictionary
Private clsDealCF As SimpleCashflow  'Combined Cashflows
Private clsPeriod As Long
Private clsLastperiod As Long

Private clsAnalysisDate As Date
Private clsRatingMigration As Boolean
Public Sub SetAnalysisDate(iDate As Date, iRating As Boolean)
    clsAnalysisDate = iDate
    clsRatingMigration = iRating
    Call SetUseRM(iRating)
End Sub

'Stores Asset level CF based upon deal accrual schedule
Public Sub ResetParAmount()
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim lParAmount As Double
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        lParAmount = lAsset.ParAmount
        lAsset.AddPar -lParAmount
    Next
End Sub

Public Function GetBLKRockIDs() As Variant()
    GetBLKRockIDs = clsAssetsDict.Keys
End Function
Public Function GetProceeds(iProceeds As String)
    Dim lBlkRockID As Variant
    Dim lNumerator As Double
    Dim lCF As SimpleCashflow
    
    For Each lBlkRockID In clsDealCFDict.Keys
        Set lCF = clsDealCFDict(lBlkRockID)
        If iProceeds = "INTEREST" Then
            lNumerator = lNumerator + lCF.Interest(clsPeriod)
        ElseIf iProceeds = "PRINCIPAL" Then
            lNumerator = lNumerator + lCF.SchedPrincipal(clsPeriod) + lCF.UnSchedPrincipal(clsPeriod) + lCF.Recoveries(clsPeriod)
        End If
    Next
    GetProceeds = lNumerator
End Function

Public Sub CalcCF(Optional iCurrBalance As Double, Optional iInitalSettlementDate As Date, Optional ianalysisDate As Date, Optional iPrepay As Variant, Optional iDefault As Variant, Optional iSeverity As Variant, Optional iLagMonth As Long, Optional iEndCFDate As Date, Optional iYC As YieldCurve)
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        lAsset.CalcCF iCurrBalance, iInitalSettlementDate, ianalysisDate, iPrepay, iDefault, iSeverity, iLagMonth, iEndCFDate, iYC
    Next
End Sub



Public Function GetCollatCF() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastperiod, 10)
    
    lOutput(0, 0) = "Beg Performing Balance"
    lOutput(0, 1) = "Beg Default Balance"
    lOutput(0, 2) = "Beg MV Default Balance"
    lOutput(0, 3) = "Period Default"
    lOutput(0, 4) = "Period MV Default"
    lOutput(0, 5) = "Interest"
    lOutput(0, 6) = "Scheduled Principal"
    lOutput(0, 7) = "Unscheduled Principal"
    lOutput(0, 8) = "Recoveries"
    lOutput(0, 9) = "Net loss"
    lOutput(0, 10) = "Sold"
    
    
    
    For i = 1 To clsLastperiod
        lOutput(i, 0) = clsDealCF.BegBalance(i)
        lOutput(i, 1) = clsDealCF.DefaultBal(i)
        lOutput(i, 2) = clsDealCF.MVDefaultBal(i)
        lOutput(i, 3) = clsDealCF.Default(i)
        lOutput(i, 4) = clsDealCF.MVDefault(i)
        lOutput(i, 5) = clsDealCF.Interest(i)
        lOutput(i, 6) = clsDealCF.SchedPrincipal(i)
        lOutput(i, 7) = clsDealCF.UnSchedPrincipal(i)
        lOutput(i, 8) = clsDealCF.Recoveries(i)
        lOutput(i, 9) = clsDealCF.Netloss(i)
        lOutput(i, 10) = clsDealCF.Sold(i)
    Next i
    
    GetCollatCF = lOutput



End Function


Public Sub DealSetup(iDealDates() As PaymentDates, iYC As YieldCurve)
'Setup Cashflows that conform to the deal
    Dim lDealCF As SimpleCashflow
    Dim lAssetCF As SimpleCashflow
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim i As Long

    Set clsDealCFDict = New Dictionary
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        If clsRatingMigration Then
            Set lAssetCF = lAsset.CalcCF(ianalysisDate:=clsAnalysisDate, iYC:=iYC, iDefault:="Rating")
        Else
            Set lAssetCF = lAsset.CalcCF(ianalysisDate:=clsAnalysisDate, iYC:=iYC)
        End If
        Set lDealCF = New SimpleCashflow
        'lAsset.BLKRockID
        For i = 1 To UBound(iDealDates)
            lDealCF.PaymentDate(i) = iDealDates(i).PaymentDate
            lDealCF.AccBegDate(i) = iDealDates(i).CollBegDate
            lDealCF.AccEndDate(i) = iDealDates(i).CollEndDate
            If i = 1 Then
                If lAsset.DefaultAsset = True Then
                    lDealCF.MVDefaultBal(i) = lAsset.ParAmount * lAsset.MarketValue / 100
                    lDealCF.DefaultBal(i) = lAsset.ParAmount
                    lDealCF.BegBalance(i) = 0
                Else
                    lDealCF.BegBalance(i) = lAsset.ParAmount
                    lDealCF.MVDefault(i) = 0
                    lDealCF.DefaultBal(i) = 0
                End If
                lDealCF.Default(i) = lAssetCF.GetDefaults(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate, True)
                lDealCF.MVDefault(i) = lAssetCF.GetMVDefaults(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate, True)
            Else
                lDealCF.Default(i) = lAssetCF.GetDefaults(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
                lDealCF.MVDefault(i) = lAssetCF.GetMVDefaults(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
                lDealCF.BegBalance(i) = lDealCF.BegBalance(i - 1) - lDealCF.Default(i - 1) - lDealCF.SchedPrincipal(i - 1) - lDealCF.UnSchedPrincipal(i - 1)
                lDealCF.DefaultBal(i) = lDealCF.DefaultBal(i - 1) + lDealCF.Default(i - 1) - lDealCF.Recoveries(i - 1) - lDealCF.Netloss(i - 1)
                lDealCF.MVDefaultBal(i) = lDealCF.MVDefaultBal(i - 1) + lDealCF.MVDefault(i - 1) - lDealCF.Recoveries(i - 1)
            End If
            lDealCF.Interest(i) = lAssetCF.GetInterest(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
            lDealCF.UnSchedPrincipal(i) = lAssetCF.GetUnschedPrin(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
            lDealCF.SchedPrincipal(i) = lAssetCF.GetSchedPrin(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
            lDealCF.Recoveries(i) = lAssetCF.GetRecoveries(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
            lDealCF.Netloss(i) = lAssetCF.GetNetLoss(iDealDates(i).CollBegDate, iDealDates(i).CollEndDate)
            If lDealCF.BegBalance(i) < 1 And lDealCF.DefaultBal(i) < 1 Then
                lDealCF.UnSchedPrincipal(i) = lDealCF.UnSchedPrincipal(i)
                lDealCF.BegBalance(i) = 0
                lDealCF.DefaultBal(i) = 0
                lDealCF.MVDefaultBal(i) = 0
                If clsLastperiod < i Then clsLastperiod = i
                Exit For
            End If
        Next i
        clsDealCFDict.Add lBlkRockID, lDealCF
    Next
    clsPeriod = 1
    Set clsDealCF = GetDealCF
End Sub

Public Function GetDealCF() As SimpleCashflow
    Dim lBlkRockID As Variant
    Dim lAssetCF As SimpleCashflow
    Dim lCF As SimpleCashflow
    Dim i As Long
    
    Set lCF = New SimpleCashflow
    For Each lBlkRockID In clsDealCFDict.Keys
        Set lAssetCF = clsDealCFDict(lBlkRockID)
        For i = 1 To lAssetCF.Count
            lCF.AccBegDate(i) = lAssetCF.AccBegDate(i)
            lCF.AccEndDate(i) = lAssetCF.AccEndDate(i)
            lCF.PaymentDate(i) = lAssetCF.PaymentDate(i)
            lCF.BegBalance(i) = lCF.BegBalance(i) + lAssetCF.BegBalance(i)
            lCF.MVDefaultBal(i) = lCF.MVDefaultBal(i) + lAssetCF.MVDefaultBal(i)
            lCF.DefaultBal(i) = lCF.DefaultBal(i) + lAssetCF.DefaultBal(i)
            lCF.Default(i) = lCF.Default(i) + lAssetCF.Default(i)
            lCF.MVDefault(i) = lCF.MVDefault(i) + lAssetCF.MVDefault(i)
            lCF.Interest(i) = lCF.Interest(i) + lAssetCF.Interest(i)
            lCF.SchedPrincipal(i) = lCF.SchedPrincipal(i) + lAssetCF.SchedPrincipal(i)
            lCF.UnSchedPrincipal(i) = lCF.UnSchedPrincipal(i) + lAssetCF.UnSchedPrincipal(i)
            lCF.Recoveries(i) = lCF.Recoveries(i) + lAssetCF.Recoveries(i)
            lCF.Netloss(i) = lCF.Netloss(i) + lAssetCF.Netloss(i)
        Next i
    Next
    Set GetDealCF = lCF
End Function
Public Sub Rollfoward()
    clsPeriod = clsPeriod + 1
End Sub

Public Sub AddAsset(iAsset As Asset)
    
    If clsAssetsDict.Exists(iAsset.BLKRockID) Then
        clsAssetsDict(iAsset.BLKRockID).AddPar iAsset.ParAmount
    Else
        If Len(iAsset.MDYRating) = 0 Then
            clsRatingsDeriv.GetMoodysRating iAsset
        End If
        If Len(iAsset.MDYDPRating) = 0 Then
            clsRatingsDeriv.GetMoodysDefProbRating iAsset
        End If
        If Len(iAsset.MDYDPRatingWARF) = 0 Then
            clsRatingsDeriv.GetMoodysDefProbRatingWARF iAsset
        End If
        If Len(iAsset.SPRating) = 0 Then
            clsRatingsDeriv.GetSnPRatings iAsset
        End If
        clsAssetsDict.Add iAsset.BLKRockID, iAsset
    End If
End Sub
Public Sub RemoveAsset(iBLKRockID As String)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict.Remove (iBLKRockID)
    End If
End Sub
Public Function GetAsset(iBLKRockID As String) As Asset
    If clsAssetsDict.Exists(iBLKRockID) Then
        Set GetAsset = clsAssetsDict(iBLKRockID).Copy
    End If
End Function
Public Function GetAssetParameter(iBLKRockID As String, iParameter As String) As Variant
    If clsAssetsDict.Exists(iBLKRockID) Then
        Select Case UCase(iParameter)
        
        
        Case "PAR AMOUNT"
            GetAssetParameter = clsAssetsDict(iBLKRockID).ParAmount
        Case "S & P RATING"
            GetAssetParameter = clsAssetsDict(iBLKRockID).SPRating
        Case "DEFAULTED"
            GetAssetParameter = clsAssetsDict(iBLKRockID).DefaultAsset
        Case "MATURITY"
            GetAssetParameter = clsAssetsDict(iBLKRockID).Maturity
        End Select
        
    End If
End Function



Public Function AssetExist(iBLKRockID As String) As Boolean
    If clsAssetsDict.Exists(iBLKRockID) Then
        AssetExist = True
    End If
End Function

Public Sub AddPar(iBLKRockID As String, iAmount As Double)
    If clsAssetsDict.Exists(iBLKRockID) Then
        clsAssetsDict(iBLKRockID).AddPar iAmount
    End If

End Sub


Private Sub Class_Initialize()
    Set clsAssetsDict = New Dictionary
    Set clsRatingsDeriv = New RatingDerivations
End Sub

Private Sub Class_Terminate()
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        Set lAsset = Nothing
    Next

    Set clsAssetsDict = Nothing
    Set clsRatingsDeriv = Nothing
End Sub

Public Function CalcCCCExcessAdjustment(iCollPrinAmt As Double, iPercent As Double, iDate As Date, iCCCMV As Double) As Double
    Dim lBlkRockID As Variant
    Dim CCCExcessBalance As Double
    Dim CaaExcessBalance As Double
    Dim lCCCDict As Dictionary
    Dim lCaaDict As Dictionary
    Dim lSecDict As Dictionary
    Dim lBalance As Double
    Dim lExcessAdjustment As Double
    Dim lExcessThresholds As Double
    Dim lCurrThreshold As Double
    Dim lSumBalance As Double
    Dim lMVBalance As Double
    Dim lAsset As Asset
    
    lExcessThresholds = iCollPrinAmt * iPercent
    
    Set lCCCDict = New Dictionary
    Set lCaaDict = New Dictionary
    For Each lBlkRockID In clsAssetsDict.Keys
        Set lAsset = clsAssetsDict(lBlkRockID)
        If clsRatingsDeriv.ReturnRatingsRank(lAsset.GetSPRating(iDate)) > 16 Then
            CCCExcessBalance = CCCExcessBalance + clsDealCFDict(lBlkRockID).BegBalance(clsPeriod)
            If Not lCCCDict.Exists(lBlkRockID) Then
                lCCCDict.Add lBlkRockID, clsAssetsDict(lBlkRockID).MarketValue
            End If
        End If
        If clsRatingsDeriv.ReturnRatingsRank(lAsset.GetMoodyRating(iDate)) > 16 Then
            CaaExcessBalance = CaaExcessBalance + clsDealCFDict(lBlkRockID).BegBalance(clsPeriod)
            If Not lCaaDict.Exists(lBlkRockID) Then
                lCaaDict.Add lBlkRockID, clsAssetsDict(lBlkRockID).MarketValue
            End If
        End If
    Next
    
    If CCCExcessBalance > (iCollPrinAmt * iPercent) Or CaaExcessBalance > iCollPrinAmt * iPercent Then
        If CCCExcessBalance > CaaExcessBalance Then
            Set lSecDict = lCCCDict
        Else
            Set lSecDict = lCaaDict
        End If
        Call SortDictionary(lSecDict, False, True)
        'lExcessThresholds = iCollPrinAmt * iPercent
        For Each lBlkRockID In clsAssetsDict.Keys
            If clsDealCFDict(lBlkRockID).BegBalance(clsPeriod) + lCurrThreshold > lExcessThresholds Then
                lBalance = clsDealCFDict(lBlkRockID).BegBalance(clsPeriod)
                lBalance = lBalance - (lExcessThresholds - lCurrThreshold)
                lCurrThreshold = lExcessThresholds
                lSumBalance = lSumBalance + lBalance
                lMVBalance = lMVBalance + lBalance * iCCCMV
            Else
                lCurrThreshold = lCurrThreshold + clsDealCFDict(lBlkRockID).BegBalance(clsPeriod)
            End If
        Next
    End If
    
    If lSumBalance > lMVBalance Then
        CalcCCCExcessAdjustment = lSumBalance - lMVBalance
    End If
    
    

End Function

Public Function PrinBallAllAssets() As Double
    Dim lNumerator As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallAllAssets = clsDealCF.BegBalance(clsPeriod + 1) + clsDealCF.DefaultBal(clsPeriod + 1)
    End If
End Function
Public Function PrinBallExDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallExDefaults = clsDealCF.BegBalance(clsPeriod + 1)
    End If
End Function
Public Function PrinBallDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        PrinBallDefaults = clsDealCF.DefaultBal(clsPeriod + 1)
    End If
End Function
Public Function MVDefaults() As Double
    If clsPeriod + 1 <= clsDealCF.Count Then
        MVDefaults = clsDealCF.MVDefaultBal(clsPeriod + 1)
    End If
End Function
Public Function UnSchedPrin() As Double
    If clsPeriod <= clsDealCF.Count Then
        UnSchedPrin = clsDealCF.UnSchedPrincipal(clsPeriod)
    End If
End Function
Public Function Liquidate(iLiquidPrice As Double) As Double
    Dim lSold As Double
    Dim i As Long
    Dim lLoss As Double
    Dim lEndBal As Double
    Dim lEndDefaultBal As Double
    Dim lEndMVDefaultBal As Double
    
    
    lEndBal = clsDealCF.BegBalance(clsPeriod) - clsDealCF.Default(clsPeriod) - clsDealCF.UnSchedPrincipal(clsPeriod) - clsDealCF.SchedPrincipal(clsPeriod)
    lEndDefaultBal = clsDealCF.DefaultBal(clsPeriod) + clsDealCF.Default(clsPeriod) - clsDealCF.Recoveries(clsPeriod) - clsDealCF.Netloss(clsPeriod)
    lEndMVDefaultBal = clsDealCF.MVDefaultBal(clsPeriod) + clsDealCF.MVDefault(clsPeriod) - clsDealCF.Recoveries(clsPeriod)
    
    lSold = lEndBal * iLiquidPrice + lEndMVDefaultBal
    lLoss = (1 - iLiquidPrice) * lEndBal + (lEndDefaultBal - lEndMVDefaultBal)
    If lEndBal > 0 Then
        clsLastperiod = clsPeriod
    End If
    For i = clsPeriod + 1 To clsDealCF.Count
        clsDealCF.BegBalance(i) = 0
        clsDealCF.Default(i) = 0
        clsDealCF.DefaultBal(i) = 0
        clsDealCF.EndBalance(i) = 0
        clsDealCF.Interest(i) = 0
        clsDealCF.MVDefault(i) = 0
        clsDealCF.MVDefaultBal(i) = 0
        clsDealCF.Netloss(i) = 0
        clsDealCF.Recoveries(i) = 0
        clsDealCF.SchedPrincipal(i) = 0
        clsDealCF.Total(i) = 0
        clsDealCF.UnSchedPrincipal(i) = 0
    Next i
    
    clsDealCF.Netloss(clsPeriod) = clsDealCF.Netloss(clsPeriod) + lLoss
    clsDealCF.Sold(clsPeriod) = clsDealCF.Sold(clsPeriod) + lSold
    Liquidate = lSold
End Function
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
Public Sub SetUseRM(iValue As Boolean)
    Dim lBlkRockID As Variant
    
    For Each lBlkRockID In clsAssetsDict.Keys
        clsAssetsDict(lBlkRockID).UseRM = iValue
    Next
End Sub

