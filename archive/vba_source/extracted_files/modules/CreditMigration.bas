Attribute VB_Name = "CreditMigration"
Option Explicit
Option Private Module
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
    BalDefaults As Double
    BalMature As Double
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
Private mTranMatrix() As Double  'TransitionMatrix with z-thresholds. This makes comparison faster
Private mCorrMatrix() As Double  'This will hold the cholskey decomposition of the asset correlation matrix
Private mAssetOrder() As String  'This will show the order of assets in the asset Matrix
Private mNumAssets As Long
Private mNumPeriods As Long
Private mAnalysisDate As Date
Private mRatingHist() As RatingHist 'This will holdd the Number of assets for each rating, defaults, and matrurity
Private mRatingHistBal() As RatingHistBal 'This will holdd the balances for each rating, defaults, and matrurity for each period
Private mSimHist() As SimHistory
Private mSimCount As Long
Private mRatingOutput As RatingMigrationOutput
Private mPeriodType As String

Public Sub CreditMigrationCleanup()
    Erase mTranMatrix
    Erase mCorrMatrix
    Erase mAssetOrder
    Erase mRatingHist
    Erase mSimHist
    Set mRatingOutput = Nothing
End Sub


Private Sub SetupTranMatrix(Optional iperiod As String)
    Dim lAnnualMatrix() As Double
    Dim lSemiAnualMatrix() As Double
    Dim lQuarterMatrix() As Double
    Dim lCumulativeMatrix() As Double
    Dim lsum As Double
    Dim i As Long
    Dim j As Long
    Dim k As Long
    Dim lNumRows As Long
    
    
    lAnnualMatrix = ConvertToArry(Range("SpTransMat").Value)
    lNumRows = UBound(lAnnualMatrix, 1)
    
    ReDim lCumulativeMatrix(1 To lNumRows, 1 To lNumRows)
    ReDim mTranMatrix(1 To lNumRows, 1 To lNumRows)
    
    If iperiod = "Annually" Then
        lQuarterMatrix = lAnnualMatrix
    ElseIf iperiod = "Semi-Annually" Then
        lSemiAnualMatrix = MatrixSQRT(lAnnualMatrix)
        lQuarterMatrix = MatrixQOM(lSemiAnualMatrix)
    Else
    
        lSemiAnualMatrix = MatrixSQRT(lAnnualMatrix)
        lSemiAnualMatrix = MatrixQOM(lSemiAnualMatrix)
        lQuarterMatrix = MatrixSQRT(lSemiAnualMatrix)
        lQuarterMatrix = MatrixQOM(lQuarterMatrix)
    End If
    For i = 1 To lNumRows
        For j = 1 To lNumRows
            lsum = 0
            For k = 1 To j
                lsum = lQuarterMatrix(i, k) + lsum
            Next k
            lCumulativeMatrix(i, j) = lsum
        Next j
    Next i
'    For i = 1 To lNumRows
'        For j = 1 To lNumRows
'            If lCumulativeMatrix(i, j) >= 1 Then
'                lCumulativeMatrix(i, j) = 5000
'            ElseIf lCumulativeMatrix(i, j) < 1E-20 Then
'                lCumulativeMatrix(i, j) = Application.WorksheetFunction.Norm_S_Inv(1E-20)
'            Else
'                lCumulativeMatrix(i, j) = Application.WorksheetFunction.Norm_S_Inv(lCumulativeMatrix(i, j))
'            End If
'        Next j
'    Next i
    mTranMatrix = lCumulativeMatrix
    
End Sub

Private Sub SetupCorrMatrix(Optional iCollatPool As CollateralPool)
    Dim lMat() As Double
    Dim lAssetStr As Variant
    Dim i As Long
    If iCollatPool Is Nothing Then
        lMat = MatrixMath.ConvertToArry(Range("AssetCorrelation").Value)
        Sheets("Asset Correlation").Activate
        lAssetStr = Range(Range("A2"), Range("A2").End(xlDown)).Value
        ReDim mAssetOrder(UBound(lAssetStr, 1))
        For i = 1 To UBound(lAssetStr, 1)
            mAssetOrder(i) = lAssetStr(i, 1)
        Next i
    Else
        lMat = CreateCorrMatrix(iCollatPool)
        lAssetStr = iCollatPool.GetBLKRockIDs
        ReDim mAssetOrder(UBound(lAssetStr) + 1)
        For i = 1 To UBound(mAssetOrder)
            mAssetOrder(i) = lAssetStr(i - 1)
        Next i
    End If
    mCorrMatrix = MatrixMath.MatrixCholesky(lMat)

    mNumAssets = UBound(mAssetOrder)
End Sub
Private Function CreateCorrMatrix(iCollatPool As CollateralPool) As Double()
    Dim lBlkRockIDs As Variant
    Dim lCorrTable As Variant
    Dim lMatrix() As Double
    Dim lIAsset As Asset
    Dim lJAsset As Asset
    Dim lRating As RatingDerivations
    Dim i As Long
    Dim j As Long
    
    Call DeleteOutputTab("RM-")
    Set lRating = New RatingDerivations
    lCorrTable = Range("CorrData").Value
    'Sheets("AM-Output").Activate
    lBlkRockIDs = iCollatPool.GetBLKRockIDs
    ReDim lMatrix(1 To UBound(lBlkRockIDs) + 1, 1 To UBound(lBlkRockIDs) + 1)
    For i = 1 To UBound(lMatrix, 1)
        Set lIAsset = iCollatPool.GetAssetNonCopy(CStr(lBlkRockIDs(i - 1)))
        For j = i To UBound(lMatrix, 1)
            Set lJAsset = iCollatPool.GetAssetNonCopy(CStr(lBlkRockIDs(j - 1)))
            If lIAsset.BLKRockID = lJAsset.BLKRockID Then
                lMatrix(i, j) = 1
            ElseIf lIAsset.IssuerId = lJAsset.IssuerId Then
                lMatrix(i, j) = lCorrTable(2, 2) - Abs(lRating.ReturnRatingsRank(lJAsset.SPRating) - lRating.ReturnRatingsRank(lIAsset.SPRating)) * lCorrTable(2, 3)
            ElseIf lIAsset.SPIndustry = lJAsset.SPIndustry Then
                lMatrix(i, j) = lCorrTable(3, 2) - Abs(lRating.ReturnRatingsRank(lJAsset.SPRating) - lRating.ReturnRatingsRank(lIAsset.SPRating)) * lCorrTable(3, 3)
            Else
                lMatrix(i, j) = lCorrTable(4, 2) - Abs(lRating.ReturnRatingsRank(lJAsset.SPRating) - lRating.ReturnRatingsRank(lIAsset.SPRating)) * lCorrTable(4, 3)
            End If
            If lMatrix(i, j) < 0 Then
                lMatrix(i, j) = 0
            End If
            lMatrix(j, i) = lMatrix(i, j)
'            Range("A1").Offset(i, j) = lMatrix(i, j)
'            Range("A1").Offset(j, i) = lMatrix(j, i)
        Next j
    Next i
    
    Call OutputDataToSheet("Asset Correlation", AssetCorrOutput(lBlkRockIDs, lMatrix), True, "RM-")
    CreateCorrMatrix = lMatrix
    Set lRating = Nothing
End Function
Private Function AssetCorrOutput(iBlkRocks As Variant, iMat() As Double) As Variant
    Dim lOutput As Variant
    Dim i As Long
    Dim j As Long
    Dim lNumAssets As Long
    lNumAssets = UBound(iMat, 1)
    
    ReDim lOutput(0 To lNumAssets, 0 To lNumAssets)
    For i = 0 To lNumAssets
        For j = 0 To lNumAssets
            If i = 0 And j = 0 Then
            
            ElseIf i = 0 Then
                lOutput(i, j) = iBlkRocks(j - 1)
            ElseIf j = 0 Then
                lOutput(i, j) = iBlkRocks(i - 1)
            Else
                lOutput(i, j) = iMat(i, j)
            End If
        Next j
    Next i
    AssetCorrOutput = lOutput
End Function



Private Function GetCorrelatdRandom() As Double()
    Dim i As Long
    Dim lRandom() As Double
    ReDim lRandom(1 To mNumAssets, 1 To 1)
    For i = 1 To mNumAssets
        'lRandom(i, 1) = ((-2 * Log(Rand())) ^ 0.5) * Cos(2 * 3.141592654 * Rand())
        lRandom(i, 1) = Application.WorksheetFunction.Norm_S_Inv(Rnd())
    Next i
    lRandom = MatrixMath.MatrixMultiply(mCorrMatrix, lRandom)
    For i = 1 To mNumAssets
        lRandom(i, 1) = Application.WorksheetFunction.Norm_S_Dist(lRandom(i, 1), True)
    Next i
    GetCorrelatdRandom = lRandom
End Function

Private Sub SetRandomizeSeed()
    Rnd (-10)
    Randomize (12)
End Sub
Public Sub CreditMigrationSetup(Optional iNumSim As Long, Optional iDebugMode As Boolean, Optional iCollatPool As CollateralPool, Optional iperiod As String)
    Call SetupTranMatrix(iperiod)
    Call SetupCorrMatrix(iCollatPool)
    If iDebugMode Then
        Call SetRandomizeSeed
    End If
    ReDim mSimHist(iNumSim)
    mSimCount = 0
    mPeriodType = iperiod
End Sub
Public Sub CMAllSetup(iNumDeals() As String, iNumSims As Long, ianalysisDate As Date, iLastMatDate As Date, iperiod As String)
    Set mRatingOutput = New RatingMigrationOutput
    Call mRatingOutput.Constructor(iNumDeals, iNumSims, ianalysisDate, iLastMatDate, iperiod)
End Sub
Public Sub CMAllAddDeal(iDealName As String, iDealCollat As CollateralPool, iSim As Long)
    Call mRatingOutput.AddDeal(iDealName, iDealCollat, iSim)
End Sub


Public Sub RunRatingHistory(iAnalysiDate As Date, iCollatPool As CollateralPool, Optional iDealCollat As Dictionary, Optional iperiod As String)
    'there is no error checking. Assumes the collateral pool and the correlation matrix has the same number of assets.
    Dim lCurrentRating() As String
    Dim lPreviousRating As String
    Dim lNextRating As String
    Dim lNumPeriods As Long
    Dim lTempDate As Date
    Dim lLastMatDate As Date
    Dim lCorrelatedRandom() As Double
    Dim lDifference As Long
    Dim i As Long
    Dim j As Long
    Dim lAddAsset As Boolean
    Dim lBlkRockID As Variant
    Dim lmonth As Long
    
    
    If UCase(iperiod) = "ANNUALLY" Then
        lmonth = 12
    ElseIf UCase(iperiod) = "SEMI-ANNUALLY" Then
        lmonth = 6
    Else
        lmonth = 3
    End If

    
    lTempDate = iAnalysiDate
    If iDealCollat Is Nothing Then
        lLastMatDate = iCollatPool.LastMaturityDate
    Else
        For Each lBlkRockID In iDealCollat.Keys
            If iCollatPool.GetAssetParameter(CStr(lBlkRockID), "MATURITY") > lLastMatDate Then
                lLastMatDate = iCollatPool.GetAssetParameter(CStr(lBlkRockID), "MATURITY")
            End If
        Next
    End If
    
    
    Do While lTempDate < lLastMatDate
        lNumPeriods = lNumPeriods + 1
        lTempDate = DateAdd("M", lmonth, lTempDate)
    Loop
    
    mAnalysisDate = iAnalysiDate
    mNumPeriods = lNumPeriods
    lTempDate = iAnalysiDate
    ReDim lCurrentRating(mNumAssets)
    ReDim mRatingHist(lNumPeriods)
    
    
    
    For i = 1 To mNumAssets
        If iCollatPool.GetAssetParameter(mAssetOrder(i), "DEFAULTED") Then
            lCurrentRating(i) = "D"
        Else
            lCurrentRating(i) = iCollatPool.GetAssetParameter(mAssetOrder(i), "S & P RATING")
            If lCurrentRating(i) = "CCC+" Or lCurrentRating(i) = "CCC-" Or lCurrentRating(i) = "CC" Or lCurrentRating(i) = "C" Or lCurrentRating(i) = "CCC" Then
                lCurrentRating(i) = "CCC"
            End If
        End If
        If iDealCollat Is Nothing Then
            lAddAsset = True
        ElseIf iDealCollat.Exists(mAssetOrder(i)) Then
            lAddAsset = True
        Else
            lAddAsset = False
        End If
        If lAddAsset Then Call UpdateRatingHist(0, lCurrentRating(i))
    Next i
    
    For j = 1 To lNumPeriods
        lCorrelatedRandom = GetCorrelatdRandom
        lTempDate = DateAdd("M", lmonth, lTempDate)
        For i = 1 To mNumAssets
            If iDealCollat Is Nothing Then
                lAddAsset = True
            ElseIf iDealCollat.Exists(mAssetOrder(i)) Then
                lAddAsset = True
            Else
                lAddAsset = False
            End If
            If lAddAsset Then
                If lCurrentRating(i) = "D" Then
                    'Do nothing asset is default
                ElseIf lCurrentRating(i) = "M" Then
                
                ElseIf lTempDate > iCollatPool.GetAssetParameter(mAssetOrder(i), "MATURITY") Then
                    lCurrentRating(i) = "M"
                    iCollatPool.AddSPRating mAssetOrder(i), lTempDate, lCurrentRating(i)
                Else
                    lPreviousRating = lCurrentRating(i)
                    lNextRating = GetNextRating(lPreviousRating, lCorrelatedRandom(i, 1))
                    Select Case ConvertRatingToEnum(lPreviousRating) - ConvertRatingToEnum(lNextRating)
                    Case Is < 0
                        mRatingHist(j).Downgrades = 1 + mRatingHist(j).Downgrades
                        lCurrentRating(i) = lNextRating
                    Case 0
                        
                    Case Is > 0
                        mRatingHist(j).Upgrades = 1 + mRatingHist(j).Upgrades
                        lCurrentRating(i) = lNextRating
                    End Select
                    iCollatPool.AddSPRating mAssetOrder(i), lTempDate, lCurrentRating(i)
                End If
                Call UpdateRatingHist(j, lCurrentRating(i))
            End If
        Next i
        mRatingHist(j).NumPeriodDefaults = mRatingHist(j).NumDefaults - mRatingHist(j - 1).NumDefaults
    Next j
    
    Call CalcRatingHistBal(mAnalysisDate, iCollatPool, iDealCollat)
    
    
    
    If mSimCount < UBound(mSimHist) Then
        mSimHist(mSimCount).RatingHist = mRatingHist
        mSimHist(mSimCount).RatingHistBal = mRatingHistBal
        mSimCount = mSimCount + 1
    End If
End Sub

Private Sub CalcRatingHistBal(ianalysisDate As Date, iCollatPool As CollateralPool, Optional iDealCollat As Dictionary)
    'This Sub will run after the migration simulation. This is to update the balance history.
    Dim lAddAsset As Boolean
    Dim lCurrentDate As Date
    Dim lCurrentRating() As String
    Dim lNextRating As String
    Dim lBalance As Double
    Dim lMaturity As Double
    Dim lParAmount As Double
    Dim lAssetInPool() As Boolean
    Dim lAsset As Asset
    Dim i As Long
    Dim j As Long
    Dim lOrigBal As Double
    Dim lmonth As Long
    
    ReDim lCurrentRating(mNumAssets)
    ReDim lAssetInPool(mNumAssets)
    ReDim mRatingHistBal(mNumPeriods)
    
    
    If UCase(mPeriodType) = "ANNUALLY" Then
        lmonth = 12
    ElseIf UCase(mPeriodType) = "SEMI-ANNUALLY" Then
        lmonth = 6
    Else
        lmonth = 3
    End If
    
    
    For i = 1 To mNumAssets
        If iDealCollat Is Nothing Then
            lAssetInPool(i) = True
            lParAmount = 1000000   'This is the default par amount for if the asset dosen't have a par amount. Might want to change this to a constant and store in UDT module
            'iCollatpool.AddPar mAssetOrder(i), lParAmount
        ElseIf iDealCollat.Exists(mAssetOrder(i)) Then
            lAssetInPool(i) = True
            lParAmount = iDealCollat(mAssetOrder(i))
            iCollatPool.AddPar mAssetOrder(i), lParAmount
        End If
        If lAssetInPool(i) Then
            If iCollatPool.GetAssetParameter(mAssetOrder(i), "DEFAULTED") Then
                lCurrentRating(i) = "D"
            Else
                lCurrentRating(i) = iCollatPool.GetAssetParameter(mAssetOrder(i), "S & P RATING")
                If lCurrentRating(i) = "CCC+" Or lCurrentRating(i) = "CCC-" Or lCurrentRating(i) = "CC" Or lCurrentRating(i) = "C" Or lCurrentRating(i) = "CCC" Then
                    lCurrentRating(i) = "CCC"
                End If
            End If
            Call UpdateRatingHistBal(0, lCurrentRating(i), lParAmount)
            lOrigBal = lOrigBal + lParAmount
        End If
    Next i
    iCollatPool.CalcCF , , ianalysisDate, 0, "MIGRATION"
    
    For j = 1 To mNumPeriods
        lCurrentDate = DateAdd("M", j * lmonth, mAnalysisDate)
        mRatingHistBal(j).BalDefaults = mRatingHistBal(j - 1).BalDefaults
        For i = 1 To mNumAssets
            If lAssetInPool(i) Then
                lBalance = 0
                lMaturity = 0
                'lNextRating = ""
                Set lAsset = iCollatPool.GetAssetNonCopy(mAssetOrder(i))
                lBalance = lAsset.GetBegBalance(lCurrentDate)
                'Debug.Assert lBalance > 0
                lNextRating = lAsset.GetSPRating(lCurrentDate)
                If lNextRating = "D" And lBalance = 0 And lCurrentRating(i) <> "D" Then
                    'It defaulted on a payment date
                    lBalance = lAsset.GetBegBalance(lCurrentDate - 1)
                End If
                lMaturity = lAsset.GetSchedPrin(mAnalysisDate, lCurrentDate)
                mRatingHistBal(j).BalMature = mRatingHistBal(j).BalMature + lMaturity
                If lCurrentRating(i) = "D" Then
                    'Don't do anything because everything has happen
                    
                ElseIf lCurrentRating(i) = "M" Then
                    'Don't do anything
                Else
'                    Select Case ConvertRatingToEnum(lCurrentRating) - ConvertRatingToEnum(lNextRating)
'                    Case Is < 0
'                        mRatingHistBal(j).Downgrades = 1 + mRatingHist(j).Downgrades
'
'                    Case Is > 0
'                        mRatingHist(j).Upgrades = 1 + mRatingHist(j).Upgrades
'                    End Select
                    If lNextRating <> "M" Then
                        Call UpdateRatingHistBal(j, lNextRating, lBalance)
                    End If
                    lCurrentRating(i) = lNextRating
                End If
            End If
        Next i
        If (lOrigBal - mRatingHistBal(j - 1).BalMature - mRatingHistBal(j - 1).BalDefaults) = 0 Then
            Exit For
        Else
            mRatingHistBal(j).CDR = 4 * ((mRatingHistBal(j).BalDefaults - mRatingHistBal(j - 1).BalDefaults) / (lOrigBal - mRatingHistBal(j - 1).BalMature - mRatingHistBal(j - 1).BalDefaults))
        End If
    Next j
    
End Sub




Private Function GetNextRating(iCurrentRating As String, iZValue As Double) As String
    Dim lRow As Long
    Dim lNextRating As String
    Dim i As Long
    lRow = ConvertRatingToEnum(iCurrentRating)

    For i = 1 To 18
        If mTranMatrix(lRow, i) > 0 And iZValue < mTranMatrix(lRow, i) Then
            lNextRating = ConvertRatingtoSTR(i)
            Exit For
        End If
    Next i
    GetNextRating = lNextRating
End Function

Private Function ConvertRatingToEnum(iString As String) As SPRatings
    Select Case iString
    Case "AAA"
        ConvertRatingToEnum = Aaa
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

Private Function ConvertRatingtoSTR(iRatingEnum As SPRatings) As String
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
Public Function SimulationResultOutput() As Variant
    Dim lNumSims As Long
    Dim lNumPeriods As Long
    Dim lColumn As Long
    Dim i As Long
    Dim j As Long
    Dim lNumArray() As Long
    Dim lNumArrayDbl() As Double
    Dim lOutput As Variant
    
    lNumPeriods = UBound(mSimHist(0).RatingHist)
    
    lNumSims = UBound(mSimHist)

    
    ReDim lOutput(0 To (lNumPeriods) * 11 + 1, 0 To 23)
    ReDim lNumArray(lNumSims - 1)
    ReDim lNumArrayDbl(lNumSims - 1)
    
    lOutput(0, lColumn) = "Period"
    lOutput(1, lColumn) = 0
    lOutput(2, lColumn) = 0
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Stat"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Upgrades this Period"
    lOutput(1, lColumn) = 0
    lOutput(2, lColumn) = 0
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Downgrades this Period"
    lOutput(1, lColumn) = 0
    lOutput(2, lColumn) = 0
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AAA"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAAA
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalAAA, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA+"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAAp
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalAA1, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAA
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalAA2, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA-"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAAm
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalAA3, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A+"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAp
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalA1, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumA
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalA2, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A-"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumAm
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalA3, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB+"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBBBp
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBBB1, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBBB
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBBB2, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB-"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBBBm
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBBB3, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB+"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBBp
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBB1, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBB
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBB2, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB-"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).numBBm
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalBB3, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B+"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBp
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalB1, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumB
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalB2, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B-"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumBm
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalB3, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of CCC"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumCCCAssets
    lOutput(2, lColumn) = Format(mSimHist(0).RatingHistBal(0).BalCCC, "#,##0.00")
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of Defaults"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumDefaults
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of Matures"
    lOutput(1, lColumn) = mSimHist(0).RatingHist(0).NumMatures
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Period CDR"
    lOutput(1, lColumn) = 0
    lColumn = lColumn + 1

    
    
    Dim lCurentPeriod As Long
    lCurentPeriod = 1
    For i = 1 To (lNumPeriods) * 11 Step 11
        lColumn = 0
'        loutput(i + 1, lColumn) = DateAdd("M", lCurentPeriod * 3, mAnalysisDate)
'        loutput(i + 2, lColumn) = DateAdd("M", lCurentPeriod * 3, mAnalysisDate)
'        loutput(i + 3, lColumn) = DateAdd("M", lCurentPeriod * 3, mAnalysisDate)
'        loutput(i + 4, lColumn) = DateAdd("M", lCurentPeriod * 3, mAnalysisDate)
'        loutput(i + 5, lColumn) = DateAdd("M", lCurentPeriod * 3, mAnalysisDate)
        lOutput(i + 2, lColumn) = lCurentPeriod
        lOutput(i + 3, lColumn) = lCurentPeriod
        lOutput(i + 4, lColumn) = lCurentPeriod
        lOutput(i + 5, lColumn) = lCurentPeriod
        lOutput(i + 6, lColumn) = lCurentPeriod
        lOutput(i + 7, lColumn) = lCurentPeriod
        lOutput(i + 8, lColumn) = lCurentPeriod
        lOutput(i + 9, lColumn) = lCurentPeriod
        lOutput(i + 10, lColumn) = lCurentPeriod
        lOutput(i + 11, lColumn) = lCurentPeriod
        lColumn = lColumn + 1
        lOutput(i + 2, lColumn) = "Max"
        lOutput(i + 3, lColumn) = "Min"
        lOutput(i + 4, lColumn) = "Average"
        lOutput(i + 5, lColumn) = "Median"
        lOutput(i + 6, lColumn) = "Standard Deviation"
        lOutput(i + 7, lColumn) = "Max"
        lOutput(i + 8, lColumn) = "Min"
        lOutput(i + 9, lColumn) = "Average"
        lOutput(i + 10, lColumn) = "Median"
        lOutput(i + 11, lColumn) = "Standard Deviation"
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).Upgrades
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).Downgrades
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAAA
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalAAA
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAAp
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalAA1
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
        
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAA
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalAA2
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAAm
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalAA3
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAp
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalA1
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumA
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalA2
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
        
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumAm
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalA3
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBBBp
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBBB1
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBBB
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBBB2
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBBBm
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBBB3
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBBp
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBB1
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBB
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBB2
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).numBBm
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalBB3
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBp
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalB1
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumB
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalB2
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumBm
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalB3
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumCCCAssets
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalCCC
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumDefaults
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalDefaults
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = mSimHist(j).RatingHist(lCurentPeriod).NumMatures
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).BalMature
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "#,##0.00")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "#,##0.00")
        lColumn = lColumn + 1
        For j = 0 To lNumSims - 1
            lNumArray(j) = 0
            lNumArrayDbl(j) = mSimHist(j).RatingHistBal(lCurentPeriod).CDR
        Next j
        lOutput(i + 2, lColumn) = Max(lNumArray)
        lOutput(i + 3, lColumn) = Min(lNumArray)
        lOutput(i + 4, lColumn) = Round(Average(lNumArray), 2)
        lOutput(i + 5, lColumn) = Median(lNumArray)
        lOutput(i + 6, lColumn) = Round(STD(lNumArray), 2)
                
        lOutput(i + 7, lColumn) = Format(MaxDBL(lNumArrayDbl), "0.000%")
        lOutput(i + 8, lColumn) = Format(MinDBL(lNumArrayDbl), "0.000%")
        lOutput(i + 9, lColumn) = Format(AverageDBL(lNumArrayDbl), "0.000%")
        lOutput(i + 10, lColumn) = Format(MedianDBL(lNumArrayDbl), "0.000%")
        lOutput(i + 11, lColumn) = Format(STDDBL(lNumArrayDbl), "0.000%")
        
        
        lCurentPeriod = lCurentPeriod + 1
    Next i
    SimulationResultOutput = lOutput
End Function

Public Function CreditMigrationOutput() As Variant
    Dim lOutput As Variant
    Dim mNumPeriods As Long
    Dim lColumn As Long
    Dim i As Long
    Dim lCurrPeriod As Long
    Dim lOriginalBalance As Double
    Dim lOriginalCount As Double
    Dim lTotalBalance As Double
    Dim lTotalCount As Double
    Dim lmonth As Long
    mNumPeriods = UBound(mRatingHist)
    
    
    If UCase(mPeriodType) = "ANNUALLY" Then
        lmonth = 12
    ElseIf UCase(mPeriodType) = "SEMI-ANNUALLY" Then
        lmonth = 6
    Else
        lmonth = 3
    End If
    
    ReDim lOutput(0 To (mNumPeriods + 1) * 2, 0 To 24)
    lOutput(0, lColumn) = "Period"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Period"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Upgrades this Period"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Downgrades this Period"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AAA"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA+"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of AA-"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A+"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of A-"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB+"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BBB-"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB+"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of BB-"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B+"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of B-"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of CCC"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of Defaults"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Number of Payoffs"
    lColumn = lColumn + 1
'    lOutput(0, lColumn) = "Check"
'    lColumn = lColumn + 1
'    lOutput(0, lColumn) = ""
'    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Period Defaults"
    lColumn = lColumn + 1
    lOutput(0, lColumn) = "Period CDR"
    lColumn = lColumn + 1
    
    'Get Orginal Balance
    
    
    

    For i = 0 To mNumPeriods * 2 Step 2
        lColumn = 0
        lTotalCount = 0
        lTotalBalance = 0
        lOutput(i + 1, lColumn) = DateAdd("M", lCurrPeriod * lmonth, mAnalysisDate)
        lOutput(i + 2, lColumn) = DateAdd("M", lCurrPeriod * lmonth, mAnalysisDate)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = lCurrPeriod
        lOutput(i + 2, lColumn) = lCurrPeriod
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).Upgrades
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).Downgrades
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAAA
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalAAA, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAAp
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalAA1, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAA
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalAA2, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAAm
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalAA3, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAp
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalA1, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumA
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalA2, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumAm
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalA3, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBBBp
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBBB1, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBBB
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBBB2, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBBBm
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBBB3, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBBp
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBB1, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBB
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBB2, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).numBBm
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalBB3, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBp
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalB1, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumB
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalB2, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumBm
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalB3, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumCCCAssets
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalCCC, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumDefaults
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalDefaults, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
        lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumMatures
        lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalMature, "#,##0.00")
        lTotalCount = lTotalCount + lOutput(i + 1, lColumn)
        lTotalBalance = lTotalBalance + lOutput(i + 2, lColumn)
        lColumn = lColumn + 1
'        lOutput(i + 1, lColumn) = lTotalCount
'        lOutput(i + 2, lColumn) = lTotalBalance
'        lColumn = lColumn + 1
'        If i = 0 Then
'            lOriginalBalance = lTotalBalance
'            lOriginalCount = lTotalCount
'        Else
'            If Abs(lOriginalBalance - lTotalBalance) > 1 Then
'                lOutput(i + 2, lColumn) = Abs(lOriginalBalance - lTotalBalance)
'            Else
'                lOutput(i + 2, lColumn) = 0
'            End If
'            lOutput(i + 1, lColumn) = Abs(lTotalCount - lOriginalCount)
'        End If
'        lColumn = lColumn + 1
        If i > 0 Then
            lOutput(i + 1, lColumn) = mRatingHist(lCurrPeriod).NumPeriodDefaults
            lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).BalDefaults - mRatingHistBal(lCurrPeriod - 1).BalDefaults, "#,##0.00")
            lColumn = lColumn + 1
            lOutput(i + 2, lColumn) = Format(mRatingHistBal(lCurrPeriod).CDR, "0.000%")
            lColumn = lColumn + 1
        End If
        
        lCurrPeriod = lCurrPeriod + 1
    Next i
    CreditMigrationOutput = lOutput
End Function

Private Sub UpdateRatingHist(iperiod As Long, iRating As String)
    
    With mRatingHist(iperiod)
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
            .NumDefaults = .NumDefaults + 1
        Case "M"
            .NumMatures = .NumMatures + 1
        Case Else
            Debug.Print "what"
        End Select
    End With
End Sub
Private Sub UpdateRatingHistBal(iperiod As Long, iRating As String, iBalance As Double)
    
    With mRatingHistBal(iperiod)
        Select Case iRating
        Case "AAA"
            .BalAAA = .BalAAA + iBalance
        Case "AA+"
            .BalAA1 = .BalAA1 + iBalance
        Case "AA"
            .BalAA2 = .BalAA2 + iBalance
        Case "AA-"
            .BalAA3 = .BalAA3 + iBalance
        Case "A+"
            .BalA1 = .BalA1 + iBalance
        Case "A"
            .BalA2 = .BalA2 + iBalance
        Case "A-"
            .BalA3 = .BalA3 + iBalance
        Case "BBB+"
            .BalBBB1 = .BalBBB1 + iBalance
        Case "BBB"
            .BalBBB2 = .BalBBB2 + iBalance
        Case "BBB-"
            .BalBBB3 = .BalBBB3 + iBalance
        Case "BB+"
            .BalBB1 = .BalBB1 + iBalance
        Case "BB"
            .BalBB2 = .BalBB2 + iBalance
        Case "BB-"
            .BalBB3 = .BalBB3 + iBalance
        Case "B+"
            .BalB1 = .BalB1 + iBalance
        Case "B"
            .BalB2 = .BalB2 + iBalance
        Case "B-"
            .BalB3 = .BalB3 + iBalance
        Case "CCC", "CCC+", "CCC-"
            .BalCCC = .BalCCC + iBalance
        Case "D"
            .BalDefaults = .BalDefaults + iBalance
        Case "M"
            .BalMature = .BalMature + iBalance
        Case Else
            'Debug.Assert 1 <> 1
        End Select
    End With
End Sub
Public Function GetSimStatTimeSeries(iStat As String, iField As String) As Variant
    GetSimStatTimeSeries = mRatingOutput.StatTimeSeries(iStat, iField)
      
End Function

Public Function GetSimNum(iStat As String) As Long
    Select Case UCase(iStat)
    Case "MIN"
        GetSimNum = mRatingOutput.GetSimMinDefaults
    Case "MAX"
        GetSimNum = mRatingOutput.GetSimMaxDefaults
    Case "MEDIAN"
        GetSimNum = mRatingOutput.GetSimMedianDefaults
    End Select
End Function
