Attribute VB_Name = "Main"
Option Explicit
Option Private Module

Private mCurrCollateralPool As CollateralPool
Private mPotentialCollateralPool As CollateralPool
Private mHypoCollateralPool As CollateralPool
Private mObjectiveWeights As Dictionary
Private mOpimizationRankings As Dictionary
Private mOptInputs As OptInputs
Private mProgressBar As IProgressBar
Private Sub Cleanup()
    Set mCurrCollateralPool = Nothing
    Set mPotentialCollateralPool = Nothing
    Set mHypoCollateralPool = Nothing
    Set mObjectiveWeights = Nothing
    Set mOpimizationRankings = Nothing
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
End Sub
Public Sub RunCompliance()
    
    Call Setup
    mCurrCollateralPool.CalcConcentrationTest
    Call OutputResults
    Call Cleanup


End Sub

Private Sub Setup()
    Dim lRampUpCash As Double
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False
    ThisWorkbook.Activate
    Call LoadCollateralPool("Existing")
    Call LoadCollateralPool("Potential")
    Call LoadCollateralPool("Hypo")
    Call LoadAccounts
    Call LoadTestInputs
    Call LoadWeights
    Call LoadOptInput
    
    
    'Add all Principal proceeds to collection account
    lRampUpCash = mCurrCollateralPool.CheckAccountBalance(RampUp, Principal)
    mCurrCollateralPool.AddCash RampUp, Principal, -lRampUpCash
    mCurrCollateralPool.AddCash Collection, Principal, lRampUpCash
    
    Set mOpimizationRankings = New Dictionary
    Set mProgressBar = New FProgressBarIFace
End Sub
Private Sub LoadOptInput()
    Dim lVariant As Variant
    Dim i As Long
    
    lVariant = Range("OptInputs").Value

    With mOptInputs
        .MaxAssets = lVariant(1, 1)
        .MaxLoanSize = lVariant(2, 1)
        .IncreaseCurLoan = lVariant(3, 1)
        .RunHypoInd = lVariant(4, 1)
    End With

    
    
End Sub
Private Function CalcObjectiveFunction(iResults() As Results)
    Dim i As Long
    Dim lobjective As Double
    
    For i = LBound(iResults) To UBound(iResults)
        With iResults(i)
            If .PassFail = False And .TestNumber <> 31 Then
                lobjective = 0
                Exit For
            End If
            
            Select Case iResults(i).TestNumber
            
            Case 33, 32, 37
                lobjective = lobjective + .Result / .Threshold * mObjectiveWeights(.TestNumber)
            Case 36, 35
                lobjective = lobjective + .Threshold / .Result * mObjectiveWeights(.TestNumber)
            End Select
        End With
    Next i

    CalcObjectiveFunction = lobjective * 100

End Function
Private Sub LoadWeights()
    Dim lVariant As Variant
    Dim i As Long
    Set mObjectiveWeights = New Dictionary
    lVariant = Range("ObjWeights").Value
    For i = LBound(lVariant) To UBound(lVariant)
        mObjectiveWeights.Add lVariant(i, 1), lVariant(i, 2)
    
    Next i
    
    
End Sub

Private Sub LoadCollateralPool(iPoolType As String)
    Dim i As Long
    Dim lPool As Variant
    Dim loffset As Long
    Dim lAssetUDT As AssetUDT
    Dim lAsset As Asset
    Dim lWorkBookName As String
    'iPoolType=Existing or Potential
    If iPoolType = "Existing" Then
        lWorkBookName = "Existing Collateral Pool"
        Set mCurrCollateralPool = New CollateralPool
    ElseIf iPoolType = "Potential" Then
        lWorkBookName = "Potential Collateral Pool"
        Set mPotentialCollateralPool = New CollateralPool
    ElseIf iPoolType = "Hypo" Then
        lWorkBookName = "Hypo Collateral Pool"
        Set mHypoCollateralPool = New CollateralPool
    End If
    Worksheets(lWorkBookName).Select
    lPool = Range(Range("A2"), Range("A2").SpecialCells(xlLastCell)).Value
    i = LBound(lPool, 1)
    loffset = 1
    Do While i < UBound(lPool, 1) And Len(lPool(i, 1)) > 0
        lAssetUDT.BLKRockID = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssueName = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssuerName = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssuerId = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Tranche = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.BondLoan = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.ParAmount = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Maturity = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CouponType = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.PaymentFreq = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CpnSpread = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.LiborFloor = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Index = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.Coupon = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CommitFee = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.UnfundedAmount = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.FacilitySize = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIndustry = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.SPIndustry = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Country = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.Seniority = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.PikAsset = True
        Else
            lAssetUDT.PikAsset = False
        End If
        loffset = loffset + 1
        
        
        If UCase(Trim(lPool(i, loffset))) = "YES" Then
            lAssetUDT.PIKing = True
        Else
            lAssetUDT.PIKing = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.PIKAmount = lPool(i, loffset)
        loffset = loffset + 1
        
    
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.DefaultAsset = True
        Else
            lAssetUDT.DefaultAsset = False
        End If
        loffset = loffset + 1
    
         
        lAssetUDT.DateofDefault = lPool(i, loffset)
        loffset = loffset + 1
    
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.DelayDrawdown = True
        Else
            lAssetUDT.DelayDrawdown = False
        End If
        loffset = loffset + 1
    
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.Revolver = True
        Else
            lAssetUDT.Revolver = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.LOC = True
        Else
            lAssetUDT.LOC = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.Participation = True
        Else
            lAssetUDT.Participation = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.DIP = True
        Else
            lAssetUDT.DIP = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.Converitable = True
        Else
            lAssetUDT.Converitable = False
        End If
        loffset = loffset + 1
    
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.StructFinance = True
        Else
            lAssetUDT.StructFinance = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.BridgeLoan = True
        Else
            lAssetUDT.BridgeLoan = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.CurrentPay = True
        Else
            lAssetUDT.CurrentPay = False
        End If
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.CovLite = True
        Else
            lAssetUDT.CovLite = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.Currency = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.WAL = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MarketValue = lPool(i, loffset)
        loffset = loffset + 1
        
        If lPool(i, loffset) = "Yes" Then
            lAssetUDT.FLLO = True
        Else
            lAssetUDT.FLLO = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.MDYRating = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.MDYRecoveryRate = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYDPRating = UCase(Trim(lPool(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.MDYFacilityRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYFacilityOutlook = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIssuerRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIssuerOutlook = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSnrSecRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSNRUnSecRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSubRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYCreditEstRating = lPool(i, loffset)
        loffset = loffset + 1
        
        If Len(lPool(i, loffset)) > 0 Then
            lAssetUDT.MDYCreditEstDate = lPool(i, loffset)
        End If
        loffset = loffset + 1
        
        lAssetUDT.SandPFacilityRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPIssuerRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPSnrSecRating = lPool(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPSubordinate = lPool(i, loffset)
        loffset = loffset + 1
        
    
        Set lAsset = New Asset
        lAsset.AddAsset lAssetUDT
        If iPoolType = "Existing" Then
            mCurrCollateralPool.AddAsset lAsset
        ElseIf iPoolType = "Potential" Then
            mPotentialCollateralPool.AddAsset lAsset
        ElseIf iPoolType = "Hypo" Then
            mHypoCollateralPool.AddAsset lAsset
        End If
        i = i + 1
        loffset = 1
    Loop
End Sub


Public Sub RunRankings()

    Call Setup
    mCurrCollateralPool.CalcConcentrationTest
    Call OutputResults
    With mOptInputs
        Call GenericOptimizationRankings(.MaxAssets, .IncreaseCurLoan, .MaxLoanSize, True)
    End With
    Call OutputRankings
    MsgBox "Rankings have finished!", vbOKOnly, "Finish"
    Call Cleanup

End Sub

Public Sub RunOptimizePoolAssets()


    Call Setup
    Call ClearData("Assets to Purchase")
    mCurrCollateralPool.CalcConcentrationTest
    Call OutputResults
    With mOptInputs
        Call GenericOptimizationPool(.MaxAssets, .IncreaseCurLoan, .MaxLoanSize, False)
    End With
    Call Cleanup

End Sub
Private Sub OutputRankings()
    Dim i As Long
    Dim lNumofSecurities As Long
    Dim lBlkRockKeys As Variant
    Dim lOutput As Variant
    
    lNumofSecurities = mOpimizationRankings.Count
    ReDim lOutput(1 To lNumofSecurities + 1, 1 To 2)
    
    Call SortDictionary(mOpimizationRankings, False, True)
    
    lBlkRockKeys = mOpimizationRankings.Keys
    
    lOutput(1, 1) = "BlKRock ID"
    lOutput(1, 2) = "Objective Function"
    
    
    For i = 0 To UBound(lBlkRockKeys)
        lOutput(i + 2, 1) = lBlkRockKeys(i)
        lOutput(i + 2, 2) = mOpimizationRankings(lBlkRockKeys(i))
    Next i
    
    Worksheets("Rankings").Activate
    Cells.Clear
    Range(Range("A1"), Range("A1").Offset(lNumofSecurities, 1)).Value = lOutput
    Range(Range("A1"), Range("A1").Offset(lNumofSecurities, 1)).Columns.AutoFit
End Sub



Public Sub RunHypo()

    ThisWorkbook.Activate
    Dim lBlkRockIDArry As Variant
    Dim lBlKRockIDStr As String
    Dim lAsset As Asset
    Dim lResults() As Results
    Dim i As Long
    Dim lExistAsset As Boolean
    
    Call Setup
    mCurrCollateralPool.CalcConcentrationTest
    Call OutputResults
    lBlkRockIDArry = mHypoCollateralPool.GetBLKRockIDs
    If mOptInputs.RunHypoInd = True Then
        For i = LBound(lBlkRockIDArry) To UBound(lBlkRockIDArry)
            lExistAsset = False
            lBlKRockIDStr = CStr(lBlkRockIDArry(i))
            Set lAsset = mHypoCollateralPool.GetAsset(lBlKRockIDStr)
            If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
                mCurrCollateralPool.AddPar lBlKRockIDStr, lAsset.ParAmount
                lExistAsset = True
            Else
                mCurrCollateralPool.AddAsset lAsset
            End If
            mCurrCollateralPool.AddCash Collection, Principal, -lAsset.ParAmount * lAsset.MarketValue / 100
            mCurrCollateralPool.CalcConcentrationTest
            lResults = mCurrCollateralPool.GetTestResult
            Call OutputOptoResults(lResults, "HYPO-" & lBlKRockIDStr)
            
            'Reset
            mCurrCollateralPool.AddCash Collection, Principal, lAsset.ParAmount * lAsset.MarketValue / 100
            If lExistAsset Then
                mCurrCollateralPool.AddPar lBlKRockIDStr, -lAsset.ParAmount
            Else
                mCurrCollateralPool.RemoveAsset lBlKRockIDStr
            End If
    
        Next i
    
    Else
        For i = LBound(lBlkRockIDArry) To UBound(lBlkRockIDArry)
            lBlKRockIDStr = lBlkRockIDArry(i)
            Set lAsset = mHypoCollateralPool.GetAsset(lBlKRockIDStr)
            If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
                mCurrCollateralPool.AddPar lBlKRockIDStr, lAsset.ParAmount
            Else
                mCurrCollateralPool.AddAsset lAsset
            End If
            mCurrCollateralPool.AddCash Collection, Principal, -lAsset.ParAmount * lAsset.MarketValue / 100
        Next i
        mCurrCollateralPool.CalcConcentrationTest
        lResults = mCurrCollateralPool.GetTestResult
        Call OutputOptoResults(lResults, "HYPO")
    End If
    
    
    
    
    
    
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Worksheets("Inputs").Select
    MsgBox "The Hypo has finishing running. Test results are in the Output Tab", vbOKOnly, "Finished"
    
    Call Cleanup
    
End Sub

Private Sub LoadAccounts()
    Dim lAllAccounts As Variant
    Dim lAccount As Accounts
    Dim i As Long
    lAllAccounts = Range("Accounts").Value
    For i = LBound(lAllAccounts, 1) To UBound(lAllAccounts, 1)
        Set lAccount = New Accounts
        lAccount.Add Interest, CDbl(lAllAccounts(i, 3))
        lAccount.Add Principal, CDbl(lAllAccounts(i, 4))
        mCurrCollateralPool.AddAccount lAccount, CLng(lAllAccounts(i, 1))
    Next i
End Sub


Private Sub LoadTestInputs()
    Dim lTestInputs As Variant
    Dim lTestSetting As TestSettings
    Dim lTestThreshold As TestThresholds
    Dim loffset As Long
    loffset = 1
    
    lTestInputs = Range("QualityTestInputs").Value
    With lTestSetting
        .Libor = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .ReinvestBal = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .WASThreshold = lTestInputs(loffset, 2)
         loffset = loffset + 1
        .SpreadAdjFactor = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .DiversityThreshold = lTestInputs(loffset, 2)
          loffset = loffset + 1
        .WARFAdjFactor = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .WARFThreshould = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .DetermDate = lTestInputs(loffset, 2)
        loffset = loffset + 1
        .WALEndDate = lTestInputs(loffset, 2)
    End With
    lTestInputs = Range("TestThresholds").Value
    
    With lTestSetting
        Set .TestThresholds = New Dictionary
        For loffset = LBound(lTestInputs, 1) To UBound(lTestInputs, 1)
            Set lTestThreshold = New TestThresholds
            lTestThreshold.TestNum = lTestInputs(loffset, 1)
            lTestThreshold.MinMax = UCase(lTestInputs(loffset, 3))
            lTestThreshold.Thresholds = lTestInputs(loffset, 4)
            lTestThreshold.ThresholdOverwrite = lTestInputs(loffset, 5)
            lTestThreshold.PreviousValues = lTestInputs(loffset, 6)
            .TestThresholds.Add lTestThreshold.TestNum, lTestThreshold
            
        Next loffset
    End With
    
    
    
    
    
    mCurrCollateralPool.AddTestSettings lTestSetting
    
End Sub


Private Sub OutputResults()
    Dim i As Long
    Dim lOutputResults As Variant
    Dim lResults() As Results
    Dim lObjectiveResult As Double
    
    
    
    lResults = mCurrCollateralPool.GetTestResult
    ReDim lOutputResults(UBound(lResults) + 1, 8)
    For i = 0 To UBound(lResults)
        lOutputResults(i + 1, 0) = lResults(i).TestNumber
        lOutputResults(i + 1, 1) = lResults(i).TestName
        lOutputResults(i + 1, 2) = lResults(i).Comments
        lOutputResults(i + 1, 3) = lResults(i).Numerator
        lOutputResults(i + 1, 4) = lResults(i).Denominator
        lOutputResults(i + 1, 5) = lResults(i).Result
        lOutputResults(i + 1, 6) = lResults(i).Threshold
        lOutputResults(i + 1, 7) = lResults(i).PassFail
        lOutputResults(i + 1, 8) = lResults(i).PassFailComment
    Next i
    lOutputResults(0, 0) = "Test Number"
    lOutputResults(0, 1) = "Test Name"
    lOutputResults(0, 2) = "Comments"
    lOutputResults(0, 3) = "Numerator"
    lOutputResults(0, 4) = "Denominator"
    lOutputResults(0, 5) = "Result"
    lOutputResults(0, 6) = "Threshold"
    lOutputResults(0, 7) = "Pass/Fail"
    lOutputResults(0, 8) = "Pass/Fail Comments"
    lObjectiveResult = CalcObjectiveFunction(lResults)
    
    Worksheets("Outputs").Activate
    Cells.Clear
   
    Range(Range("A1"), Range("A1").Offset(UBound(lResults) + 1, 8)).Value = lOutputResults
    Range("B1").Offset(UBound(lResults) + 2, 0).Value = "Objective Result"
    Range("F1").Offset(UBound(lResults) + 2, 0).Value = lObjectiveResult
    Range(Range("A1"), Range("A1").Offset(UBound(lResults) + 1, 8)).Columns.AutoFit
    Range(Range("D2"), Range("D2").Offset(35, 1)).Style = "Comma"
    Range(Range("F2"), Range("F2").Offset(31, 1)).NumberFormat = "0.000%"
    Range(Range("F34"), Range("F34").Offset(2, 1)).Style = "Comma"
    Range("F37:G37").NumberFormat = "0.000%"
    Range(Range("A1"), Range("A1").Offset(UBound(lResults) + 1, 8)).Columns.AutoFit
End Sub
Private Sub GenericOptimization()
'    Dim lAsset As Asset
'    Dim lBlkRockID As Variant
'    Dim lAverageParAmount As Double
'    Dim lResults() As Results
'    Dim i As Long
'
'    lAverageParAmount = mCurrCollateralPool.CalcAverageParAmount
'    mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount
'    lBlkRockID = mPotentialCollateralPool.GetBLKRockIDs
'    For i = LBound(lBlkRockID) To UBound(lBlkRockID)
'        If Not (mCurrCollateralPool.AssetExist(CStr(lBlkRockID(i)))) Then
'            Set lAsset = mPotentialCollateralPool.GetAsset(CStr(lBlkRockID(i)))
'            lAsset.AddPar lAverageParAmount
'            mCurrCollateralPool.AddAsset lAsset
'            mCurrCollateralPool.CalcConcentrationTest
'            lResults = mCurrCollateralPool.GetTestResult
'            mCurrCollateralPool.RemoveAsset CStr(lBlkRockID(i))
'            Call OutputOptoResults(lResults, CStr(lBlkRockID(i)))
'        End If
'    Next i
End Sub
Private Sub GenericOptimizationRankings(iMaxAssets As Long, iInclCurrAssets As Boolean, iMaxParAmount As Double, iOutputResults As Boolean)
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim lBlKRockIDStr As String
    Dim lAverageParAmount As Double
    Dim lIncreasePar As Double
    Dim lAssetCurrPar As Double
    Dim lResults() As Results
    Dim i As Long
    Dim lCounter As Long
    Dim lRunTest As Boolean
    Dim lObjectiveResult As Double
    
    If iOutputResults Then
        mProgressBar.Title = "BlackRock CLO Admin"
        mProgressBar.Min = 0
        mProgressBar.Max = iMaxAssets
        mProgressBar.Progress = 1
        mProgressBar.Show
    End If
    Set mOpimizationRankings = New Dictionary
    Do While lCounter < iMaxAssets
        If iOutputResults Then
            mProgressBar.Text = "Running Rankings on " & lCounter + 1 & " of " & iMaxAssets & "."
            mProgressBar.Progress = lCounter
        End If
        lIncreasePar = 0
        'lBlKRockIDStr = GetRandomAsset(iMaxParAmount, iInclCurrAssets)
        lBlKRockIDStr = GetRandomAsset(100000000, iInclCurrAssets)
        Set lAsset = mPotentialCollateralPool.GetAsset(lBlKRockIDStr)
        If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
            'lIncreasePar = iMaxParAmount - CDbl(mCurrCollateralPool.GetAssetParameter(lBlKRockIDStr, "PAR AMOUNT"))
            lIncreasePar = iMaxParAmount
            mCurrCollateralPool.AddPar lBlKRockIDStr, lIncreasePar
            mCurrCollateralPool.AddCash Collection, Principal, -lIncreasePar * lAsset.MarketValue / 100
        Else
            Set lAsset = mPotentialCollateralPool.GetAsset(lBlKRockIDStr)
            lAsset.AddPar iMaxParAmount
            mCurrCollateralPool.AddAsset lAsset
            mCurrCollateralPool.AddCash Collection, Principal, -iMaxParAmount * lAsset.MarketValue / 100
        End If
        mCurrCollateralPool.CalcConcentrationTest
        lResults = mCurrCollateralPool.GetTestResult
        If iOutputResults Then
            Call OutputOptoResults(lResults, lBlKRockIDStr)
        End If
        lObjectiveResult = CalcObjectiveFunction(lResults)
        mOpimizationRankings.Add lBlKRockIDStr, lObjectiveResult
        
        If lIncreasePar > 0 Then
            mCurrCollateralPool.AddPar lBlKRockIDStr, -lIncreasePar
            mCurrCollateralPool.AddCash Collection, Principal, lIncreasePar * lAsset.MarketValue / 100
        Else
            mCurrCollateralPool.RemoveAsset lBlKRockIDStr
            mCurrCollateralPool.AddCash Collection, Principal, iMaxParAmount * lAsset.MarketValue / 100
        End If
        lCounter = lCounter + 1
        mPotentialCollateralPool.RemoveAsset lBlKRockIDStr
    Loop
    If iOutputResults Then
        mProgressBar.Hide
    End If
End Sub






Private Sub GenericOptimization2(iMaxAssets As Long)
'    Dim lAsset As Asset
'    Dim lBlkRockID As Variant
'    Dim lBlKRockIDStr As String
'    Dim lAverageParAmount As Double
'    Dim lIncreasePar As Double
'    Dim lAssetCurrPar As Double
'    Dim lResults() As Results
'    Dim i As Long
'    Dim lcounter As Long
'    Dim lRunTest As Boolean
'
'    lAverageParAmount = mCurrCollateralPool.CalcAverageParAmount
'    mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount
'    Set mOpimizationRankings = New Dictionary
'    Do While lcounter < iMaxAssets
'        lBlkRockID = mPotentialCollateralPool.GetBLKRockIDs
'        i = Rnd() * UBound(lBlkRockID)
'        lBlKRockIDStr = CStr(lBlkRockID(i))
'        lIncreasePar = 0
'        lRunTest = False
'        If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
'
'
'            lAssetCurrPar = CDbl(mCurrCollateralPool.GetAssetParameter(lBlKRockIDStr, "PAR AMOUNT"))
'            If lAverageParAmount > lAssetCurrPar Then
'                lIncreasePar = lAverageParAmount - lAssetCurrPar
'                mCurrCollateralPool.AddPar lBlKRockIDStr, lIncreasePar
'                lRunTest = True
'
'            End If
'        Else
'
'            Set lAsset = mPotentialCollateralPool.GetAsset(lBlKRockIDStr)
'            lAsset.AddPar lAverageParAmount
'            mCurrCollateralPool.AddAsset lAsset
'            lRunTest = True
'        End If
'
'        If lRunTest Then
'            mCurrCollateralPool.CalcConcentrationTest
'            lResults = mCurrCollateralPool.GetTestResult
'            Call OutputOptoResults(lResults, lBlKRockIDStr)
'
'            If lIncreasePar > 0 Then
'                mCurrCollateralPool.AddPar lBlKRockIDStr, -lIncreasePar
'            Else
'                mCurrCollateralPool.RemoveAsset lBlKRockIDStr
'            End If
'            lcounter = lcounter + 1
'        End If
'
'     mPotentialCollateralPool.RemoveAsset lBlKRockIDStr
'
'
'
'    Loop
End Sub

Private Function GetRandomAsset(iMaxParAmount As Double, iIncludeCurAssets As Boolean) As String
'This subroutine will select a random asset from potential assets. I will compare it the the currentpool, a

    Dim lBLKRockIDvar As Variant
    Dim lBlKRockIDStr As String
    Dim lRandID As Long
    Dim lAssetFound As Boolean
    

    Do While lAssetFound = False
        lBLKRockIDvar = mPotentialCollateralPool.GetBLKRockIDs
        lRandID = Rnd() * UBound(lBLKRockIDvar)
        lBlKRockIDStr = CStr(lBLKRockIDvar(lRandID))
        If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
            If iIncludeCurAssets Then
                If iMaxParAmount > CDbl(mCurrCollateralPool.GetAssetParameter(lBlKRockIDStr, "PAR AMOUNT")) Then
                    GetRandomAsset = lBlKRockIDStr
                    lAssetFound = True
                End If
            End If
            If lAssetFound = False Then
                mPotentialCollateralPool.RemoveAsset lBlKRockIDStr
            End If
        Else
            lAssetFound = True
            GetRandomAsset = lBlKRockIDStr
        End If
    Loop


End Function

Private Sub GenericOptimizationPool(iMaxAssets As Long, iInclCurrAssets As Boolean, iMaxParAmount As Double, iOutputResults As Boolean)
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim lBlKRockIDStr As String
    Dim lAverageParAmount As Double
    Dim lResults() As Results
    Dim i As Long
    Dim lCounter As Long
    Dim lRemainingPar As Double
    
    
    Dim lInitialObjectValue As Double
    Dim lLastObjectionValue As Double
    Dim lCurrentObjectValue As Double
    Dim lParToAdd As Double
    
    lResults = mCurrCollateralPool.GetTestResult
    lInitialObjectValue = CalcObjectiveFunction(lResults)
    lLastObjectionValue = lInitialObjectValue
    lCurrentObjectValue = lLastObjectionValue + 0.00000000001
    
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Min = 0
    mProgressBar.Max = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
    mProgressBar.Progress = mProgressBar.Max
    mProgressBar.Progress = 0
    mProgressBar.Show
    lCounter = 1
    lRemainingPar = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
    Do While lCurrentObjectValue > lLastObjectionValue And mCurrCollateralPool.CheckAccountBalance(Collection, Principal) > 0
        lLastObjectionValue = lCurrentObjectValue
        lAverageParAmount = iMaxParAmount
        mOpimizationRankings.RemoveAll
        'mProgressBar.text = "Finding asset # " & lcounter & ". Remaining par is " & Format(lRemainingPar, "###,##0.00") & "."
        mProgressBar.Text = "Finding asset # " & lCounter & "."
        If mCurrCollateralPool.CheckAccountBalance(Collection, Principal) < lAverageParAmount Then
            lAverageParAmount = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
        End If
        Call GenericOptimizationRankings(iMaxAssets, iInclCurrAssets, lAverageParAmount, False)
        
        Call SortDictionary(mOpimizationRankings, False, True)
        lBlKRockIDStr = mOpimizationRankings.Keys()(0)
        lCurrentObjectValue = mOpimizationRankings(lBlKRockIDStr)
        If lCurrentObjectValue > lLastObjectionValue Then
            Set mPotentialCollateralPool = Nothing
            Set mPotentialCollateralPool = New CollateralPool
            Call LoadCollateralPool("Potential")
            Set lAsset = mPotentialCollateralPool.GetAsset(lBlKRockIDStr)
            If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
                'lParToAdd = mCurrCollateralPool.GetAssetParameter(lBlKRockIDStr, "PAR AMOUNT")
                'lAverageParAmount = lAverageParAmount - lParToAdd
                'lAverageParAmount = iMaxParAmount
                mCurrCollateralPool.AddPar lBlKRockIDStr, lAverageParAmount
                mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount * lAsset.MarketValue / 100
                lAsset.AddPar lAverageParAmount
            Else
                 lAsset.AddPar lAverageParAmount
                 mCurrCollateralPool.AddAsset lAsset
                 mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount * lAsset.MarketValue / 100
            End If
            Call OutputAsset(lAsset)
            'mPotentialCollateralPool.RemoveAsset (lBlKRockIDStr)
        End If
        lCounter = lCounter + 1
        mProgressBar.Progress = mProgressBar.Progress + lAverageParAmount
    Loop
    Call OutputOptoResults(mCurrCollateralPool.GetTestResult, "Pool")
    Cells.Columns.AutoFit
    Worksheets("Inputs").Activate
    mProgressBar.Hide
    If lCurrentObjectValue > lLastObjectionValue Then
        MsgBox "Optimization has been completed new objection function is " & Format(lCurrentObjectValue, "Standard") & " previous value was " & Format(lInitialObjectValue, "Standard") & ".", vbOKOnly, "Finished"
    Else
        MsgBox "Optimization has finished before spending all of principal. The remaining principal is " & Format(mProgressBar.Max - mProgressBar.Progress - lAverageParAmount, "Standard"), vbOKOnly, "Break"
    End If
End Sub
Private Function GenericOptimizationPool2343(iMaxAssets As Long, iInclCurrAssets As Boolean, iMaxParAmount As Double, iOutputResults As Boolean) As Double
    Dim lAsset As Asset
    Dim lBlkRockID As Variant
    Dim lBlKRockIDStr As String
    Dim lAverageParAmount As Double
    Dim lResults() As Results
    Dim i As Long
    Dim lCounter As Long
    Dim lRemainingPar As Double
    
    
    Dim lInitialObjectValue As Double
    Dim lLastObjectionValue As Double
    Dim lCurrentObjectValue As Double
    Dim lParToAdd As Double
    
    lResults = mCurrCollateralPool.GetTestResult
    lInitialObjectValue = CalcObjectiveFunction(lResults)
    lLastObjectionValue = lInitialObjectValue
    lCurrentObjectValue = lLastObjectionValue + 0.00000000001
    
'    mProgressBar.Title = "BlackRock CLO Admin"
'    mProgressBar.Min = 0
'    mProgressBar.Max = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
'    mProgressBar.Progress = mProgressBar.Max
'    mProgressBar.Progress = 0
'    mProgressBar.Show
    lCounter = 1
    lRemainingPar = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
    Do While lCurrentObjectValue > lLastObjectionValue And mCurrCollateralPool.CheckAccountBalance(Collection, Principal) > 0
        lLastObjectionValue = lCurrentObjectValue
        lAverageParAmount = iMaxParAmount
        mOpimizationRankings.RemoveAll
        'mProgressBar.text = "Finding asset # " & lcounter & ". Remaining par is " & Format(lRemainingPar, "###,##0.00") & "."
        'mProgressBar.text = "Finding asset # " & lcounter & "."
        If mCurrCollateralPool.CheckAccountBalance(Collection, Principal) < lAverageParAmount Then
            lAverageParAmount = mCurrCollateralPool.CheckAccountBalance(Collection, Principal)
        End If
        Call GenericOptimizationRankings(iMaxAssets, iInclCurrAssets, lAverageParAmount, False)
        
        Call SortDictionary(mOpimizationRankings, False, True)
        lBlKRockIDStr = mOpimizationRankings.Keys()(0)
        lCurrentObjectValue = mOpimizationRankings(lBlKRockIDStr)
        If lCurrentObjectValue > lLastObjectionValue Then
            Set mPotentialCollateralPool = Nothing
            Set mPotentialCollateralPool = New CollateralPool
            Call LoadCollateralPool("Potential")
            Set lAsset = mPotentialCollateralPool.GetAsset(lBlKRockIDStr)
            If mCurrCollateralPool.AssetExist(lBlKRockIDStr) Then
                'lParToAdd = mCurrCollateralPool.GetAssetParameter(lBlKRockIDStr, "PAR AMOUNT")
                'lAverageParAmount = lAverageParAmount - lParToAdd
                'lAverageParAmount = iMaxParAmount
                mCurrCollateralPool.AddPar lBlKRockIDStr, lAverageParAmount
                mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount
                lAsset.AddPar lAverageParAmount
            Else
                 lAsset.AddPar lAverageParAmount
                 mCurrCollateralPool.AddAsset lAsset
                 mCurrCollateralPool.AddCash Collection, Principal, -lAverageParAmount
            End If
            Call OutputAsset(lAsset)
            'mPotentialCollateralPool.RemoveAsset (lBlKRockIDStr)
        End If
        lCounter = lCounter + 1
        'mProgressBar.Progress = mProgressBar.Progress + lAverageParAmount
    Loop
    Call OutputOptoResults(mCurrCollateralPool.GetTestResult, "Pool")
    Cells.Columns.AutoFit
    Worksheets("Inputs").Activate
   ' mProgressBar.Hide
'    If lCurrentObjectValue > lLastObjectionValue Then
'        MsgBox "Optimization has been completed new objection function is " & Format(lCurrentObjectValue, "Standard") & " previous value was " & Format(lInitialObjectValue, "Standard") & ".", vbOKOnly, "Finished"
'    Else
'        MsgBox "Optimization has finished before spending all of principal. The remaining principal is " & Format(mProgressBar.Max - mProgressBar.Progress - lAverageParAmount, "Standard"), vbOKOnly, "Break"
'    End If
    
    GenericOptimizationPool2343 = lCurrentObjectValue
    Call Setup
End Function
Public Sub OptimizationTest()
    Dim i As Long

    
    
    Call Setup
    Call ClearData("Assets to Purchase")
    mCurrCollateralPool.CalcConcentrationTest
    Call OutputResults
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(0, 0).Value = GenericOptimizationPool2343(15, True, 5000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(1, 0).Value = GenericOptimizationPool2343(25, True, 5000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(2, 0).Value = GenericOptimizationPool2343(35, True, 5000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(3, 0).Value = GenericOptimizationPool2343(45, True, 5000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(4, 0).Value = GenericOptimizationPool2343(55, True, 5000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(5, 0).Value = GenericOptimizationPool2343(15, True, 4500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(6, 0).Value = GenericOptimizationPool2343(25, True, 4500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(7, 0).Value = GenericOptimizationPool2343(35, True, 4500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(8, 0).Value = GenericOptimizationPool2343(45, True, 4500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(9, 0).Value = GenericOptimizationPool2343(55, True, 4500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(10, 0).Value = GenericOptimizationPool2343(15, True, 4000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(11, 0).Value = GenericOptimizationPool2343(25, True, 4000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(12, 0).Value = GenericOptimizationPool2343(35, True, 4000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(13, 0).Value = GenericOptimizationPool2343(45, True, 4000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(14, 0).Value = GenericOptimizationPool2343(55, True, 4000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(15, 0).Value = GenericOptimizationPool2343(15, True, 3500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(16, 0).Value = GenericOptimizationPool2343(25, True, 3500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(17, 0).Value = GenericOptimizationPool2343(35, True, 3500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(18, 0).Value = GenericOptimizationPool2343(45, True, 3500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(19, 0).Value = GenericOptimizationPool2343(55, True, 3500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(20, 0).Value = GenericOptimizationPool2343(15, True, 3000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(21, 0).Value = GenericOptimizationPool2343(25, True, 3000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(22, 0).Value = GenericOptimizationPool2343(35, True, 3000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(23, 0).Value = GenericOptimizationPool2343(45, True, 3000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(24, 0).Value = GenericOptimizationPool2343(55, True, 3000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(25, 0).Value = GenericOptimizationPool2343(15, True, 2500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(26, 0).Value = GenericOptimizationPool2343(25, True, 2500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(27, 0).Value = GenericOptimizationPool2343(35, True, 2500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(28, 0).Value = GenericOptimizationPool2343(45, True, 2500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(29, 0).Value = GenericOptimizationPool2343(55, True, 2500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(30, 0).Value = GenericOptimizationPool2343(15, True, 2000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(31, 0).Value = GenericOptimizationPool2343(25, True, 2000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(32, 0).Value = GenericOptimizationPool2343(35, True, 2000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(33, 0).Value = GenericOptimizationPool2343(45, True, 2000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(34, 0).Value = GenericOptimizationPool2343(55, True, 2000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(35, 0).Value = GenericOptimizationPool2343(15, True, 1500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(36, 0).Value = GenericOptimizationPool2343(25, True, 1500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(37, 0).Value = GenericOptimizationPool2343(35, True, 1500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(38, 0).Value = GenericOptimizationPool2343(45, True, 1500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(39, 0).Value = GenericOptimizationPool2343(55, True, 1500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(40, 0).Value = GenericOptimizationPool2343(15, True, 1000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(41, 0).Value = GenericOptimizationPool2343(25, True, 1000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(42, 0).Value = GenericOptimizationPool2343(35, True, 1000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(43, 0).Value = GenericOptimizationPool2343(45, True, 1000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(44, 0).Value = GenericOptimizationPool2343(55, True, 1000000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(45, 0).Value = GenericOptimizationPool2343(15, True, 500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(46, 0).Value = GenericOptimizationPool2343(25, True, 500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(47, 0).Value = GenericOptimizationPool2343(35, True, 500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(48, 0).Value = GenericOptimizationPool2343(45, True, 500000, False)
    ThisWorkbook.Sheets("Sheet4").Range("f2").Offset(49, 0).Value = GenericOptimizationPool2343(55, True, 500000, False)
    Call Cleanup
End Sub


Private Sub OutputAsset(iAsset As Asset)
    Dim lOutputVariant As Variant
    Dim lcolumnoffset As Long
    Dim lRowoffset As Long
    Worksheets("Assets to Purchase").Activate
    Do While Len(Range("A2").Offset(lRowoffset, 0).Value) <> 0
        lRowoffset = lRowoffset + 1
    Loop
    
    ReDim lOutputVariant(1 To 1, 1 To AssetFields)
    lcolumnoffset = 1
    With iAsset
        lOutputVariant(1, lcolumnoffset) = .BLKRockID
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .IssueName
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .IssuerName
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .IssuerId
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Tranche
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .BondLoan
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.ParAmount, "Standard")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Maturity
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .CouponType
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .PaymentFreq
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.CpnSpread, "0.000%")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.LiborFloor, "0.000%")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Index
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.Coupon, "0.000%")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.CommitFee, "0.000%")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .UnfundedAmount
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.FacilitySize, "Standard")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .MDYIndustry
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .SPIndustry
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Country
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Seniority
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .PikAsset
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .PIKing
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = Format(.PIKAmount, "Standard")
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .DefaultAsset
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .DateofDefault
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .DelayDrawdown
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Revolver
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .LOC
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Participation
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .DIP
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .Converitable
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .StructFinance
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .BridgeLoan
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .CurrentPay
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .CovLite
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .AssetCurrency
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .WAL
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .MarketValue
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .FLLO
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .MDYRating
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .MDYRecoveryRate
        lcolumnoffset = lcolumnoffset + 1
        lOutputVariant(1, lcolumnoffset) = .MDYDPRating
        lcolumnoffset = lcolumnoffset + 1
    End With
    Range(Range("A2").Offset(lRowoffset, 0), Range("A2").Offset(lRowoffset, AssetFields - 1)).Value = lOutputVariant

End Sub

Private Sub OutputOptoResults(lResults() As Results, iBLKRockID As String)
    Dim i As Long
    Dim lObjectiveResult As Double
    Static lcolumnoffset As Long
    
    Worksheets("Outputs").Activate
    Do While Len(Range("H2").Offset(0, lcolumnoffset * 2).Value) = 0
        lcolumnoffset = lcolumnoffset - 1
    Loop
    
    ReDim lOutputResults(1 To UBound(lResults) + 1, 1 To 1)
    
    lcolumnoffset = lcolumnoffset + 1
    Worksheets("Outputs").Activate
    For i = 1 To UBound(lResults) + 1
        lOutputResults(i, 1) = lResults(i - 1).Result
    Next i
    
    lObjectiveResult = CalcObjectiveFunction(lResults)
    
    Range("H1").Offset(0, lcolumnoffset * 2).Value = iBLKRockID
    Range("H2").Offset(UBound(lResults) + 1, lcolumnoffset * 2).Value = lObjectiveResult
    Range(Range("H2").Offset(0, lcolumnoffset * 2), Range("H2").Offset(UBound(lResults), lcolumnoffset * 2)).Value = lOutputResults
    Range(Range("H2").Offset(0, lcolumnoffset * 2), Range("H2").Offset(31, lcolumnoffset * 2)).NumberFormat = "0.000%"
    Range(Range("H2").Offset(32, lcolumnoffset * 2), Range("H2").Offset(34, lcolumnoffset * 2)).Style = "Comma"
    Range("H2").Offset(35, lcolumnoffset * 2).NumberFormat = "0.000%"
    Range(Range("H2").Offset(-1, lcolumnoffset * 2), Range("H2").Offset(UBound(lResults) + 1, lcolumnoffset * 2)).Columns.AutoFit
    Range("H2").Offset(0, lcolumnoffset * 2 - 1).ColumnWidth = 4
    Range("A1").Select
End Sub

Private Sub ClearData(iName As String)
'---------------------------------------------------------------------------------------
' Procedure : ClearData
' Author    : Adam C. Freeman
' Date      : 12/9/2011
' Purpose   : Use to clear all the data in the worksheet beside row 1.
'---------------------------------------------------------------------------------------

    ActiveWorkbook.Worksheets(iName).Activate
    Range("A2").Select

    'Just make sure I don't clear the wrong thing
    Dim loriginalcell As String
    Dim loriginalarray() As String
    Dim lendcell As String
    Dim lendcellarray() As String
    loriginalcell = ActiveCell.Offset(0, 0).Address
    loriginalarray = Split(loriginalcell, "$")
    lendcell = ActiveCell.SpecialCells(xlLastCell).Address
    lendcellarray = Split(lendcell, "$")
    Range(Selection, ActiveCell.SpecialCells(xlLastCell)).Select
    If CDec(lendcellarray(UBound(lendcellarray))) > CDec(loriginalarray(UBound(loriginalarray))) Then
        Selection.Clear
    End If
    Range("A1").Select
End Sub

