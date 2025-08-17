Attribute VB_Name = "ComplianceHypo"
Option Explicit
Option Private Module
Private mProgressBar As IProgressBar
Private mAllCollateral As CollateralPool
Private mDealCollat As CollateralPool
Private mDealCollatCLO As CollateralPoolForCLO
Private mCancelFlag As Boolean
Private mDealName As String

Private Sub Setup(Optional iLoadCFData As Boolean)
    Dim lsheet As Worksheet
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Call UnlockWorkbook
    mCancelFlag = False
    ThisWorkbook.Activate
    Set mAllCollateral = New CollateralPool
    Set mProgressBar = New FProgressBarIFace
    Set mDealCollat = New CollateralPool
    Set mDealCollatCLO = New CollateralPoolForCLO
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Loading All Assets"
    Call mProgressBar.HideCancelButton
    Call LoadAllAssets(iLoadCFData)
    Sheets("Run Model").Activate
    mDealName = Range("C9").Value
    mProgressBar.Hide
    
End Sub
Private Sub Cleanup()
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    mCancelFlag = False
    
    Set mProgressBar = Nothing
    Set mAllCollateral = Nothing
    Set mDealCollat = Nothing
    Set mDealCollatCLO = Nothing
    Call LockWorkbook
 
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    Range("A1").Select
End Sub
Private Sub LoadAllAssets(Optional iLoadCFData As Boolean)
    On Error GoTo ErrorTrap
    Dim i, j As Long
    Dim lLoanSchedDict As Dictionary
    Dim loffset As Long
    Dim lAssetUDT As AssetUDT
    Dim lAsset As Asset
    Dim lSchedNum As Long
    Dim lPoolInput As Variant
    Dim lPrinSched As Variant
    Dim lAssumptions As Variant
    Dim lNumPoolsAssets As Long
    Dim lSchedMatDate As Date
    Dim lAnalysisDate As Date
    
    Worksheets("All Assets").Select
    'lPoolInput = Range(Range("A2"), Range("A2").SpecialCells(xlLastCell)).Value
    lPoolInput = Range("AllAssets").Value
    lPrinSched = Range("Sink_Schedule").Value
    lAssumptions = Range("CFAssumptions").Value
    'lAnalysisDate = Range("AnalysisDate").Value
    lNumPoolsAssets = UBound(lPoolInput, 1)  'Don't want to use a variable that can cause a potential error in an error trap.
    mAllCollateral.SetAnalysisDate lAnalysisDate
    mProgressBar.Min = LBound(lPoolInput, 1)
    mProgressBar.Max = UBound(lPoolInput, 1)
    
    For i = LBound(lPoolInput, 1) To UBound(lPoolInput, 1)
        mProgressBar.Progress = i
        loffset = 1
        lSchedMatDate = 0
        If Len(lPoolInput(i, loffset)) = 0 Then
            Exit For
        End If
        
        
        lAssetUDT.BLKRockID = lPoolInput(i, loffset)
        loffset = loffset + 1

        lAssetUDT.IssueName = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssuerName = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssuerId = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Tranche = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.BondLoan = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        'lAssetUDT.ParAmount = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Maturity = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CouponType = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.PaymentFreq = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CpnSpread = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.LiborFloor = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.Index = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.Coupon = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.CommitFee = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.UnfundedAmount = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.FacilitySize = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIndustry = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.SPIndustry = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYAssetCategory = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.SPPriorityCategory = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.Country = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.Seniority = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.PikAsset = True
        Else
            lAssetUDT.PikAsset = False
        End If
        loffset = loffset + 1
        
        
        If UCase(Trim(lPoolInput(i, loffset))) = "YES" Then
            lAssetUDT.PIKing = True
        Else
            lAssetUDT.PIKing = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.PIKAmount = lPoolInput(i, loffset)
        loffset = loffset + 1
        
    
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.DefaultAsset = True
        Else
            lAssetUDT.DefaultAsset = False
        End If
        loffset = loffset + 1
    
         If Len(lPoolInput(i, loffset) = 0) Then
         
         Else
            lAssetUDT.DateofDefault = lPoolInput(i, loffset)
        End If
        loffset = loffset + 1
    
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.DelayDrawdown = True
        Else
            lAssetUDT.DelayDrawdown = False
        End If
        loffset = loffset + 1
    
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.Revolver = True
        Else
            lAssetUDT.Revolver = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.LOC = True
        Else
            lAssetUDT.LOC = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.Participation = True
        Else
            lAssetUDT.Participation = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.DIP = True
        Else
            lAssetUDT.DIP = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.Converitable = True
        Else
            lAssetUDT.Converitable = False
        End If
        loffset = loffset + 1
    
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.StructFinance = True
        Else
            lAssetUDT.StructFinance = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.BridgeLoan = True
        Else
            lAssetUDT.BridgeLoan = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.CurrentPay = True
        Else
            lAssetUDT.CurrentPay = False
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.CovLite = True
        Else
            lAssetUDT.CovLite = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.Currency = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.WAL = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        If IsNumeric(lPoolInput(i, loffset)) Then
        lAssetUDT.MarketValue = CDbl(lPoolInput(i, loffset))
        End If
        loffset = loffset + 1
        
        If lPoolInput(i, loffset) = "Yes" Then
            lAssetUDT.FLLO = True
        Else
            lAssetUDT.FLLO = False
        End If
        loffset = loffset + 1
        
        lAssetUDT.MDYRating = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.MDYRecoveryRate = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYDPRating = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.MDYDPRatingWARF = UCase(Trim(lPoolInput(i, loffset)))
        loffset = loffset + 1
        
        lAssetUDT.MDYFacilityRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYFacilityOutlook = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIssuerRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYIssuerOutlook = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSnrSecRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSNRUnSecRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYSubRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.MDYCreditEstRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        If Len(lPoolInput(i, loffset)) > 0 Then
            lAssetUDT.MDYCreditEstDate = lPoolInput(i, loffset)
        End If
        loffset = loffset + 1
        
        lAssetUDT.SandPFacilityRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPIssuerRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPSnrSecRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPSubordinate = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.SandPRecRating = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.DatedDate = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.IssueDate = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.FirstPaymentDate = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.AmortizationType = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.DayCount = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.LIBORCap = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.BusinessDayConvention = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.EOMFlag = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        lAssetUDT.AmtIssued = lPoolInput(i, loffset)
        loffset = loffset + 1
        
        If Len(lPoolInput(i, loffset)) > 0 Then
            lAssetUDT.AnalystOpinion = UCase(lPoolInput(i, loffset))
        Else
            lAssetUDT.AnalystOpinion = "HOLD"
        End If
        loffset = loffset + 1
        
        lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
        Dim lamBalance As Double
        Dim lSchedDate As Date
        Dim lTotalBalance As Double
        
        ''GetSchedule
        Set lLoanSchedDict = Nothing
        Set lLoanSchedDict = New Dictionary
        If iLoadCFData Then
            If UCase(lAssetUDT.AmortizationType) = "SCHEDULED" Then
                lSchedMatDate = 0
                lTotalBalance = 0
                For lSchedNum = LBound(lPrinSched, 1) To UBound(lPrinSched, 1)
                    If UCase(lAssetUDT.BLKRockID) = UCase(Trim(lPrinSched(lSchedNum, 1))) Then
                        lamBalance = lPrinSched(lSchedNum, 3)
                        lSchedDate = CDate(lPrinSched(lSchedNum, 2))
                        lTotalBalance = lTotalBalance + lamBalance
                        If lLoanSchedDict.Exists(lSchedDate) Then
                            lLoanSchedDict(lSchedDate) = lLoanSchedDict(lSchedDate) + lamBalance
                        Else
                            lLoanSchedDict.Add lSchedDate, lamBalance
                        End If
                    End If
                    If lSchedDate > lSchedMatDate Then lSchedMatDate = lSchedDate
                Next lSchedNum
                Call SortDictionary(lLoanSchedDict, True)
                Dim lkeys As Variant
                Dim lItems As Variant
                lkeys = lLoanSchedDict.Keys
                lItems = lLoanSchedDict.Items
                lLoanSchedDict.RemoveAll
                For j = LBound(lkeys) To UBound(lkeys)
                    lamBalance = lItems(j)
                    lLoanSchedDict.Add CLng(CheckBusinessDate(CDate(lkeys(j)), lAssetUDT.BusinessDayConvention)), lamBalance / lTotalBalance
                    'Debug.Print CDate(lKeys(j)) & vbTab & lamBalance / lTotalBalance
                    lTotalBalance = lTotalBalance - lamBalance
                Next j
            End If
            lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
            If lSchedMatDate > lAssetUDT.Maturity Then
                lAssetUDT.Maturity = CheckBusinessDate(lSchedMatDate, lAssetUDT.BusinessDayConvention)
            End If
            
           
            For j = LBound(lAssumptions, 1) To UBound(lAssumptions, 1)
                If UCase(lAssetUDT.BLKRockID) = UCase(Trim(lAssumptions(j, 1))) Or UCase(Trim(lAssumptions(j, 1))) = "ALL" Then
                    If IsNumeric(lAssumptions(j, 2)) Then
                        lAssetUDT.PrePayRate = lAssumptions(j, 2)
                    Else
                        lAssetUDT.PrePayRate = GetCFVector(CStr(lAssumptions(j, 2)))
                    End If
    
                    If IsNumeric(lAssumptions(j, 3)) Then
                        lAssetUDT.DefaultRate = lAssumptions(j, 3)
                    ElseIf UCase(lAssumptions(j, 3)) = "RATING" Then
                        lAssetUDT.DefaultRate = "RATING"
                    Else
                        lAssetUDT.DefaultRate = GetCFVector(CStr(lAssumptions(j, 3)))
                    End If
                    If IsNumeric(lAssumptions(j, 4)) Then
                        lAssetUDT.Severity = lAssumptions(j, 4)
                    Else
                        lAssetUDT.Severity = GetCFVector(CStr(lAssumptions(j, 4)))
                    End If
                    lAssetUDT.Lag = lAssumptions(j, 5)
                End If
            Next j
        End If
        If lLoanSchedDict.Count = 0 Then
            lLoanSchedDict.Add CLng(lAssetUDT.Maturity), 1
        End If
        Set lAsset = Nothing
        Set lAsset = New Asset
        lAsset.AddAsset lAssetUDT, lLoanSchedDict
        mAllCollateral.AddAsset lAsset
        lSchedDate = 0
        lSchedMatDate = 0
NextAsset:
    Next i
    
    
    Exit Sub
ErrorTrap:
    'Dont add asset

    If i < lNumPoolsAssets Then
        Resume NextAsset
    End If
End Sub

Private Sub LoadDealCollat(iDealName As String)
    On Error GoTo ErrorTrap
    Dim lAsset As Asset
    Dim lAssetCopy As Asset
    Dim lDealAssets As Variant

    Dim i As Long
    Set mDealCollatCLO = Nothing
    Set mDealCollat = Nothing
    Set mDealCollatCLO = New CollateralPoolForCLO
    Set mDealCollat = New CollateralPool
    lDealAssets = Sheets(iDealName & " Inputs").Range("DealCollateral").Value
    For i = LBound(lDealAssets, 1) To UBound(lDealAssets, 1)
        Set lAsset = mAllCollateral.GetAsset(Trim(CStr(lDealAssets(i, 1))))
        lAsset.AddPar CDbl(lDealAssets(i, 2))
        mDealCollat.AddAsset lAsset
        mDealCollatCLO.AddAsset lAsset
NextAsset:
    Next i
Exit Sub
ErrorTrap:
    If i < UBound(lDealAssets, 1) Then
        Debug.Print CStr(lDealAssets(i, 1))
        Resume NextAsset
    End If
End Sub
Private Sub LoadDealCollatNonCopy(iDealName As String)
    On Error GoTo ErrorTrap
    Dim lAsset As Asset
    Dim lAssetCopy As Asset
    Dim lDealAssets As Variant

    Dim i As Long
    Set mDealCollatCLO = Nothing
    Set mDealCollat = Nothing
    Set mDealCollatCLO = New CollateralPoolForCLO
    Set mDealCollat = New CollateralPool
    lDealAssets = Sheets(iDealName & " Inputs").Range("DealCollateral").Value
    For i = LBound(lDealAssets, 1) To UBound(lDealAssets, 1)
        Set lAsset = mAllCollateral.GetAssetNonCopy(Trim(CStr(lDealAssets(i, 1))))
        lAsset.UpdatePar CDbl(lDealAssets(i, 2))
        mDealCollat.AddAsset lAsset
        mDealCollatCLO.AddAsset lAsset
NextAsset:
    Next i
Exit Sub
ErrorTrap:
    If i < UBound(lDealAssets, 1) Then
        Debug.Print CStr(lDealAssets(i, 1))
        Resume NextAsset
    End If
End Sub
Private Sub LoadAccounts(iDealName As String)
    Dim lAllAccounts As Variant
    Dim lAccount As Accounts
    Dim i As Long
    lAllAccounts = Sheets(iDealName & " Inputs").Range("Accounts").Value
    For i = LBound(lAllAccounts, 1) To UBound(lAllAccounts, 1)
        Set lAccount = New Accounts
        lAccount.Add Interest, CDbl(lAllAccounts(i, 3))
        lAccount.Add Principal, CDbl(lAllAccounts(i, 4))
        mDealCollat.AddAccount lAccount, CLng(lAllAccounts(i, 1))
    Next i
End Sub
Private Sub LoadTestInputs(iDealName As String)
    Dim lSheetInputs As Variant
    Dim lTestInputDict As Dictionary
    Dim lTestThreshDict As Dictionary
    Dim lobjWeights As Dictionary
    Dim lConsAndQualityTest As ConcentrationTest
    Dim lTestThreshold As TestThresholds
    Dim loffset As Long
    loffset = 1
    
    Set lTestInputDict = New Dictionary
    lSheetInputs = Sheets(iDealName & " Inputs").Range("QualityTestInputs").Value
    For loffset = LBound(lSheetInputs, 1) To UBound(lSheetInputs, 1)
        lTestInputDict.Add lSheetInputs(loffset, 1), lSheetInputs(loffset, 2)
    Next loffset

    lSheetInputs = Sheets(iDealName & " Inputs").Range("TestThresholds").Value
    Set lTestThreshDict = New Dictionary
    For loffset = LBound(lSheetInputs, 1) To UBound(lSheetInputs, 1)
        Set lTestThreshold = New TestThresholds
        lTestThreshold.TestNum = lSheetInputs(loffset, 1)
        lTestThreshold.MinMax = UCase(lSheetInputs(loffset, 3))
        
        If IsNumeric(lSheetInputs(loffset, 4)) Then
            lTestThreshold.Thresholds = lSheetInputs(loffset, 4)
        End If
        lTestThreshold.ThresholdOverwrite = lSheetInputs(loffset, 5)
        lTestThreshold.PreviousValues = lSheetInputs(loffset, 6)
        lTestThreshDict.Add lTestThreshold.TestNum, lTestThreshold
    Next loffset
    
    Set lobjWeights = New Dictionary
    lSheetInputs = Sheets(iDealName & " Inputs").Range("ObjWeights").Value
    For loffset = LBound(lSheetInputs) To UBound(lSheetInputs)
        lobjWeights.Add lSheetInputs(loffset, 1), lSheetInputs(loffset, 2)
    Next loffset

    
    
    
    Set lConsAndQualityTest = New ConcentrationTest
    lConsAndQualityTest.Setup lTestInputDict, lTestThreshDict, lobjWeights
    
    mDealCollat.SetTest lConsAndQualityTest
    'mDealCollat.CalcConcentrationTest

End Sub

Public Sub RunCompliance()
    Dim lOutput As Variant
    
    Call Setup
    Call DeleteOutputTab("Compliance-")
    Call LoadDealCollat(mDealName)
    Call LoadAccounts(mDealName)
    Call LoadTestInputs(mDealName)
    mDealCollat.CalcConcentrationTest
    lOutput = mDealCollat.GetTestResultsOutput
    Call UpdateOBJTestResults(mDealName)
    Call OutputDataToSheet(mDealName, lOutput, True, "Compliance-")
    Call Cleanup
    MsgBox "Compliance test have finish running"
    
End Sub

Public Sub RunDealAssets()
    Dim lBLKID As Variant
    Dim lAssets As Dictionary
    Dim lOutput As Variant
    Call Setup
    Call DeleteOutputTab("Deal Assets-")
    Call LoadDealCollat(mDealName)
    Set lAssets = New Dictionary
    For Each lBLKID In mDealCollat.GetBLKRockIDs
        lAssets.Add lBLKID, mDealCollat.GetAssetNonCopy(CStr(lBLKID))
    Next lBLKID
    lOutput = GetAssetDataOutput(lAssets, "")
    Call OutputDataToSheet(mDealName, lOutput, True, "Deal Assets-")
    Call Cleanup
    MsgBox "Deal Assets have finish running"
    
End Sub



Public Sub UpdateOBJTestResults(iDealName As String)
    Dim lTestResults() As Results
    Dim lObjDict As Dictionary
    Dim lTestNum As Variant
    Dim i, k As Long
    Dim lOutput As Variant
    
    lTestResults = mDealCollat.GetTestResult
    Set lObjDict = mDealCollat.GetObjectiveDict
    ReDim lOutput(1 To lObjDict.Count, 1 To 1)
    k = 1
    For Each lTestNum In lObjDict.Keys
        For i = LBound(lTestResults) To UBound(lTestResults)
            If lTestNum = lTestResults(i).TestNumber Then
                lOutput(k, 1) = lTestResults(i).Result
                If lOutput(k, 1) < 2 Then
                    lOutput(k, 1) = Format(lOutput(k, 1), "0.00%")
                ElseIf lOutput(k, 1) > 1000 Then
                    lOutput(k, 1) = Format(lOutput(k, 1), "0,000.00")
                Else
                    lOutput(k, 1) = Format(lOutput(k, 1), "00.00")
                End If
                k = k + 1
                Exit For
            End If
        Next i
    Next lTestNum
    Call OutputObjResults(iDealName, lOutput)
End Sub

Public Sub RunOBjectiveTest()
    Dim lDealName As String
    Dim lResults() As Results
    Dim lObjectDict As Dictionary
    Dim lResultDict As Dictionary
    Dim lTestNum As Variant
    Dim lBRSID As Variant
    Dim lAsset As Asset
    Dim i As Long
    Dim lAssetOBjective As Double
    Dim lTestResult As Double
    Dim lLIBOR As Double
    Dim lAssetLevelOBJ As Dictionary
    Dim lOutput As Variant
    Dim lCounter As Long
    Dim lTempObjective As Double
    
    
    Sheets("Run Model").Activate
    lDealName = Range("C4").Value
    Call Setup
    Call LoadDealCollat(lDealName)
    Call LoadAccounts(lDealName)
    Call LoadTestInputs(lDealName)
    mDealCollat.CalcConcentrationTest
    lResults = mDealCollat.GetTestResult
    Set lObjectDict = mDealCollat.GetObjectiveDict
    Set lResultDict = New Dictionary
    Set lAssetLevelOBJ = New Dictionary
    For Each lTestNum In lObjectDict.Keys
        For i = 0 To UBound(lResults)
            If lResults(i).TestNumber = lTestNum Then
                lResultDict.Add lTestNum, lResults(i).Result
                Exit For
            End If
        Next i
    Next lTestNum
    lLIBOR = 0.006211
    lTempObjective = mDealCollat.GetObjectiveValue
    For Each lBRSID In mAllCollateral.GetBLKRockIDs
        Set lAsset = mAllCollateral.GetAssetNonCopy(CStr(lBRSID))
        Debug.Assert lBRSID <> "BRSM75FQ0"
        lAssetOBjective = lTempObjective
        For Each lTestNum In lObjectDict.Keys
            If lObjectDict.Item(lTestNum) <> 0 Then
                Select Case lTestNum
                Case 39
'                    lTestResult = lAsset.LiborFloor - lLIBOR
'                    If lTestResult < 0 Then lTestResult = 0
'                    lTestResult = lTestResult + lAsset.CpnSpread
'                    lTestResult = lTestResult / lResultDict(lTestNum)
                    lTestResult = -0.50206014
                    lTestResult = lTestResult + 5.353602711 * lAsset.CpnSpread
                    lTestResult = lTestResult + 3.457850893 * lAsset.LiborFloor
                    lTestResult = lTestResult + 0.557032303 * lAsset.MDYRecoveryRate
                Case 36
                    'lTestResult = lResultDict(lTestNum) / ConverRatingToFactor(lAsset.MDYDPRatingWARF)
                    lTestResult = -0.001414198
                    lTestResult = lTestResult + -0.0000825597 * ConverRatingToFactor(lAsset.MDYDPRatingWARF)
                Case 38
                    If lAsset.MarketValue <> 0 Then
                       ' lTestResult = 100 / lAsset.MarketValue
                       lTestResult = 0.196923465
                       lTestResult = lTestResult + -0.001969235 * lAsset.MarketValue
                    End If
                End Select
                lAssetOBjective = lAssetOBjective + lTestResult * lObjectDict(lTestNum)
            End If
        Next lTestNum
        If lAsset.MarketValue < 30 Then lAssetOBjective = 0
        lAssetLevelOBJ.Add lBRSID, lAssetOBjective
    Next lBRSID
    
    ReDim lOutput(0 To mAllCollateral.NumOfAssets, 0 To 9)
    lOutput(lCounter, 0) = "BLKRockID"
    lOutput(lCounter, 1) = "Objective"
    lOutput(lCounter, 2) = "Issue Name"
    lOutput(lCounter, 3) = "Market Value"
    lOutput(lCounter, 4) = "Coupon Spread"
    lOutput(lCounter, 5) = "LIBOR Floor"
    lOutput(lCounter, 6) = "Maturity"
    lOutput(lCounter, 7) = "Moody's Rating"
    lOutput(lCounter, 8) = "Analyst Opinion"
    lOutput(lCounter, 9) = "Moody's Recovery Rate"
    
    lCounter = 1
    For Each lBRSID In mAllCollateral.GetBLKRockIDs
        lOutput(lCounter, 0) = lBRSID
        lOutput(lCounter, 1) = lAssetLevelOBJ.Item(lBRSID)
        lOutput(lCounter, 2) = mAllCollateral.GetAssetParameter(CStr(lBRSID), "ISSUE NAME")
        lOutput(lCounter, 3) = mAllCollateral.GetAssetParameter(CStr(lBRSID), "MARKET VALUE")
        lOutput(lCounter, 4) = Format(mAllCollateral.GetAssetParameter(CStr(lBRSID), "SPREAD"), "0.000%")
        lOutput(lCounter, 5) = Format(mAllCollateral.GetAssetParameter(CStr(lBRSID), "LIBOR FLOOR"), "0.000%")
        lOutput(lCounter, 6) = mAllCollateral.GetAssetParameter(CStr(lBRSID), "MATURITY")
        lOutput(lCounter, 7) = ConverRatingToFactor(mAllCollateral.GetAssetParameter(CStr(lBRSID), "MOODY'S RATING WARF"))
        lOutput(lCounter, 8) = mAllCollateral.GetAssetParameter(CStr(lBRSID), "ANALYST OPINION")
        lOutput(lCounter, 9) = Format(mAllCollateral.GetAssetParameter(CStr(lBRSID), "MOODY's RECOVERY RATE"), "0.00%")
        lCounter = lCounter + 1
    Next lBRSID
    Call OutputDataToSheet("OBjectives", lOutput, False, "Collat Object-")
    
    Call Cleanup
End Sub



Public Sub RunApplyFilter()
    Dim lDealName As String
    Dim lOutput As Variant
    Dim lOutput2 As Variant
    Dim i As Long
    Dim j As Long
    Dim lFilter As String
    Dim lFilterarry() As String
    Dim lNumRows As Long
    Dim lFilterPool As CollateralPool
    
    Call Setup
    Call DeleteOutputTab("Filter-")
    Sheets("Run Model").Activate
    lDealName = Range("C4").Value
    If lDealName = "All" Then
        Set lFilterPool = mAllCollateral
    Else
        Call LoadDealCollat(lDealName)
        Set lFilterPool = mDealCollat
    End If
    
    lFilter = LoadFilter
    If Len(lFilter) > 0 Then
        lOutput = lFilterPool.ApplyFilter(lFilter).Keys
    End If
    If Len(lFilter) = 0 Then
        MsgBox "The filter conditions isempty"
    ElseIf IsArray(lOutput) = False Then
        MsgBox "There were no assets that meet the filter conditions"
    Else
        lFilterarry = FilterFields(lFilter)
        lNumRows = 3 + UBound(lFilterarry)
        ReDim lOutput2(0 To UBound(lOutput) + 1, 0 To lNumRows)
        lOutput2(0, 0) = "Blackrock ID"
        lOutput2(0, 1) = "Issue Name"
        lOutput2(0, 2) = "Par Amount"
        For j = 0 To UBound(lFilterarry)
            lOutput2(0, 3 + j) = lFilterarry(j)
        Next j
        For i = 0 To UBound(lOutput)
            lOutput2(i + 1, 0) = lOutput(i)
            lOutput2(i + 1, 1) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), "ISSUE NAME")
            lOutput2(i + 1, 2) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), "PAR AMOUNT")
            For j = 0 To UBound(lFilterarry)
                lOutput2(i + 1, 3 + j) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), lFilterarry(j))
            Next j
        Next i
        Call OutputDataToSheet(lDealName, lOutput2, True, "Filter-")
    End If
    Call Cleanup
    MsgBox "Portfolio filtering have finish running"
End Sub

Public Sub RunApplyFilter2()
    'Same as filter one but I want to add asset objective
    Dim lDealName As String
    Dim lOutput As Variant
    Dim lOutput2 As Variant
    Dim i As Long
    Dim j As Long
    Dim lFilter As String
    Dim lFilterarry() As String
    Dim lNumRows As Long
    Dim lFilterPool As CollateralPool
    Dim lAssetDict As Dictionary
    Dim lObjDict As Dictionary
    
    
    Call Setup
    Call DeleteOutputTab("Filter-")
    Sheets("Run Model").Activate
    lDealName = Range("C4").Value
    If lDealName = "All" Then
        Set lFilterPool = mAllCollateral
    Else
        Call LoadDealCollat(lDealName)
        Set lFilterPool = mDealCollat
    End If
    
    lFilter = LoadFilter
    If Len(lFilter) > 0 Then
        lOutput = lFilterPool.ApplyFilter(lFilter).Keys
    End If
    If Len(lFilter) = 0 Then
        MsgBox "The filter conditions isempty"
    ElseIf IsArray(lOutput) = False Then
        MsgBox "There were no assets that meet the filter conditions"
    Else
        lFilterarry = FilterFields(lFilter)
        If lDealName <> "All" Then
            Set lAssetDict = New Dictionary
            Set lObjDict = New Dictionary
            Call LoadAccounts(lDealName)
            Call LoadTestInputs(lDealName)
            For i = 0 To UBound(lOutput)
                lAssetDict.Add lOutput(i), lFilterPool.GetAssetNonCopy(CStr(lOutput(i)))
            Next i
            Set lObjDict = lFilterPool.GetAssetObjective(lAssetDict, Buy)
            lNumRows = 4 + UBound(lFilterarry)
        Else
            lNumRows = 3 + UBound(lFilterarry)
        End If
        
        ReDim lOutput2(0 To UBound(lOutput) + 1, 0 To lNumRows)
        lOutput2(0, 0) = "Blackrock ID"
        lOutput2(0, 1) = "Issue Name"
        lOutput2(0, 2) = "Par Amount"
        For j = 0 To UBound(lFilterarry)
            lOutput2(0, 3 + j) = lFilterarry(j)
        Next j
        If lDealName <> "All" Then
            lOutput2(0, 3 + j) = "Asset Objective"
        End If
        For i = 0 To UBound(lOutput)
            lOutput2(i + 1, 0) = lOutput(i)
            lOutput2(i + 1, 1) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), "ISSUE NAME")
            lOutput2(i + 1, 2) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), "PAR AMOUNT")
            For j = 0 To UBound(lFilterarry)
                lOutput2(i + 1, 3 + j) = lFilterPool.GetAssetParameter(CStr(lOutput(i)), lFilterarry(j))
            Next j
            If lDealName <> "All" Then
                lOutput2(i + 1, 3 + j) = lObjDict(lOutput(i))
            End If
        Next i
        Call OutputDataToSheet(lDealName, lOutput2, True, "Filter-")
    End If
    Call Cleanup
    MsgBox "Portfolio filtering have finish running"
End Sub

Public Sub RunRankings()
    Call Setup
    Call DeleteOutputTab("Rankings-")
    Call UpdaeObjeWeights
    Call LoadDealCollat(mDealName)
    Call LoadAccounts(mDealName)
    Call LoadTestInputs(mDealName)
    Call CalcRankings
    Call Cleanup
    MsgBox "Rankings have finish running"
End Sub
Public Sub RunCollateralCF()
    Dim lDealName As String
    Dim lOutput As Variant
    Dim lUSERM As Boolean
    Dim lCorrMatrx As String
    Dim lDeals As Variant
    Dim lDeal As Variant
    Dim lAsset As Asset
    Dim lAnalysisDate As Date
    Dim lYC As YieldCurve
    Dim lUseStatic As Boolean
    Dim lRndSeed As Long
    
    Call Setup
    Call DeleteOutputTab("Collat CF-")
    Sheets("Run Model").Activate
    lDealName = Range("C4").Value
    lUSERM = Range("C5").Value
    lCorrMatrx = Range("C6").Value
    lAnalysisDate = Range("C3").Value
    lUseStatic = Range("C8").Value
    lRndSeed = Range("C9").Value
    
    
    Set lYC = LoadYieldCurve(lAnalysisDate)
    If lUSERM = True Then
        If lUseStatic Then
            Rnd (-10)
            Randomize (lRndSeed)
        End If
        If lCorrMatrx = "System Defined" Then
            Call CreditMigrationSetup(1, False, mAllCollateral)
        Else
            Call CreditMigrationSetup(1, False)
        End If
        Call RunRatingHistory(lAnalysisDate, mAllCollateral)
    End If
    

    
    If UCase(lDealName) = "ALL" Then
    
    Else
        Call LoadDealCollat(lDealName)
        lDeals = LoadListofDeals(mDealCollat)
        If Not IsEmpty(lDeals) Then
            For Each lDeal In lDeals
                Set lAsset = mDealCollat.GetAssetNonCopy(CStr(lDeal))
                If lUSERM Then
                    lAsset.CalcCF , , lAnalysisDate, , "Rating", , , , lYC
                Else
                    lAsset.CalcCF , , lAnalysisDate, , , , , , lYC
                End If
                Call OutputDataToSheet(lAsset.BLKRockID & "    " & lAsset.IssuerName, lAsset.CashflowOutput, False, "Collat CF-")
            Next
        End If
    End If
    MsgBox "Collateral CF is Finished Running", vbOKOnly, "Finished"
    Call Cleanup

End Sub
Public Sub RunCollatSpreads()
    Dim lOutput As Variant
    Dim lDeal As Variant
    Dim lAsset As Asset
    Dim lAnalysisDate As Date
    Dim lYC As YieldCurve
    Dim lCF As SimpleCashflow
    Dim lspread As Double
    Dim lDict As Dictionary
    Dim lCounter As Long
    
    
    Call Setup(True)
    Call DeleteOutputTab("Collat Spreads-")
    Sheets("Run Model").Activate
    lAnalysisDate = Range("C8").Value
    
    
    Set lYC = LoadYieldCurve(lAnalysisDate)
    Debug.Print lYC.ZeroRate("01/29/2016", "03/18/2016")
    Set lDict = New Dictionary
    For Each lDeal In mAllCollateral.GetBLKRockIDs
        Set lAsset = mAllCollateral.GetAssetNonCopy(CStr(lDeal))
        If lAsset.DefaultAsset = False And lAsset.MarketValue > 0 Then
            Set lCF = lAsset.CalcCF(, lAnalysisDate, lAnalysisDate, 0, 0, 0, 0, , lYC)
            lspread = lCF.CalcZSpread(lYC, lAsset.MarketValue / 100)
            lDict.Add lAsset.BLKRockID, lspread
        End If
    Next
    ReDim lOutput(0 To lDict.Count, 0 To 8)
        lOutput(lCounter, 0) = "BLKRockID"
        lOutput(lCounter, 1) = "Z-Spread"
        lOutput(lCounter, 2) = "Issue Name"
        lOutput(lCounter, 3) = "Market Value"
        lOutput(lCounter, 4) = "Coupon Spread"
        lOutput(lCounter, 5) = "LIBOR Floor"
        lOutput(lCounter, 6) = "Maturity"
        lOutput(lCounter, 7) = "Moody's Rating"
        lOutput(lCounter, 8) = "Analyst Opinion"
    
    
    lCounter = 1
    For Each lDeal In lDict.Keys
        lOutput(lCounter, 0) = lDeal
        lOutput(lCounter, 1) = Format(lDict.Item(lDeal), "0.000%")
        lOutput(lCounter, 2) = mAllCollateral.GetAssetParameter(CStr(lDeal), "ISSUE NAME")
        lOutput(lCounter, 3) = mAllCollateral.GetAssetParameter(CStr(lDeal), "MARKET VALUE")
        lOutput(lCounter, 4) = Format(mAllCollateral.GetAssetParameter(CStr(lDeal), "SPREAD"), "0.000%")
        lOutput(lCounter, 5) = Format(mAllCollateral.GetAssetParameter(CStr(lDeal), "LIBOR FLOOR"), "0.000%")
        lOutput(lCounter, 6) = mAllCollateral.GetAssetParameter(CStr(lDeal), "MATURITY")
        lOutput(lCounter, 7) = mAllCollateral.GetAssetParameter(CStr(lDeal), "MOODY'S RATING")
        lOutput(lCounter, 8) = mAllCollateral.GetAssetParameter(CStr(lDeal), "ANALYST OPINION")
        lCounter = lCounter + 1
    Next lDeal
    Call OutputDataToSheet("Spreads", lOutput, False, "Collat Spreads-")
    MsgBox "Collateral Spread is Finished Running", vbOKOnly, "Finished"
    Call Cleanup

End Sub


Private Function LoadListofDeals(iCollatPool As CollateralPool) As Variant
    Dim lDeals As Variant
    Dim lBlkRockID As Variant
    Dim lNamesDict As Dictionary
    Dim i As Long
    Dim lAsset As Asset
    
    Set lNamesDict = New Dictionary
    For Each lBlkRockID In iCollatPool.GetBLKRockIDs
        Set lAsset = iCollatPool.GetAssetNonCopy(CStr(lBlkRockID))
        lNamesDict.Add lAsset.BLKRockID & vbTab & lAsset.IssueName, 0
    Next
    
    
    Set UserForm1.mListofDeals = lNamesDict
    UserForm1.init
    UserForm1.Show
    If UserForm1.mSelectListofDeals.Count > 0 Then
        lDeals = UserForm1.mSelectListofDeals.Keys
        For i = LBound(lDeals) To UBound(lDeals)
            lDeals(i) = Left(lDeals(i), InStr(lDeals(i), vbTab) - 1)
        Next i
    End If
    LoadListofDeals = lDeals
End Function
Public Sub RunRatingMigration()
On Error GoTo ErrorTrap
    Dim lDealName As String
    Dim lNumSimulation As Long
    Dim lAnalysisDate As Date
    Dim lDealCollatDict As Dictionary
    Dim lCorrMatrix As String
    Dim lUseStatic As Boolean
    Dim lRndSeed As Long
    Dim lperiod As String
    Dim i As Long
    Dim lRMInputs As RMandCFInputs
    
    
    Call Setup(True)
    Call DeleteOutputTab("RM-")
    lRMInputs = LoadRMandCFInputs()
    With lRMInputs
        lDealName = .DealName
        lNumSimulation = .NumOfSims
        lAnalysisDate = .AnalysisDate
        lCorrMatrix = .CorrMatrix
        lUseStatic = .StaticRndNum
        lRndSeed = .RandomizeSeed
        lperiod = .RMFreq
    End With
    Set lDealCollatDict = LoadDealCollateral(lDealName)
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Creating Cholskey Decomposition"
    
    If lUseStatic Then
        Rnd (-10)
        Randomize (lRndSeed)
    End If
    If lCorrMatrix = "System Defined" Then
        Call CreditMigrationSetup(lNumSimulation, False, mAllCollateral, lperiod)
    Else
        Call CreditMigrationSetup(lNumSimulation, False, , lperiod)
    End If

    mProgressBar.Min = 0
    mProgressBar.Max = lNumSimulation
    mProgressBar.Progress = 1
    mProgressBar.ShowCancelButton
    mProgressBar.Show
    For i = 1 To lNumSimulation
        If mCancelFlag Then Exit For
        mProgressBar.Text = "Running Simulation " & i & " of " & lNumSimulation & "."
        mProgressBar.Progress = i
        mAllCollateral.ReesetAssets
        Call RunRatingHistory(lAnalysisDate, mAllCollateral, lDealCollatDict, lperiod)
        Call OutputDataToSheet("Credit Migration: Simulation " & i, CreditMigrationOutput, False, "RM-")
    Next i
    If mCancelFlag = False Then
        Call OutputDataToSheet("Credit Migration Stats", SimulationResultOutput, True, "RM-")
        ActiveWindow.FreezePanes = False
    End If
    Call CreditMigrationCleanup
    mProgressBar.Hide
    Call Cleanup
    'Call GetAverages
    'Sheets("CM-Output").Activate
    MsgBox "Rating Migration is Finished", vbOKOnly, "Finished"
Exit Sub
ErrorTrap:
    MsgBox "There was an error in running rating migration", vbOKOnly, "Error!"
    Call Cleanup
End Sub
Public Sub RunRatingMigrationAll()
On Error GoTo ErrorTrap
    Dim lDealName As String
    Dim lNumSimulation As Long
    Dim lAnalysisDate As Date
    Dim lCorrMatrix As String
    Dim lUseStatic As Boolean
    Dim lRndSeed As Long
    Dim lDeals() As String
    Dim lLastMat As Date
    Dim lperiod As String
    Dim lSimlong As Long
    Dim lRMInputs As RMandCFInputs
    Dim i As Long
    Dim j As Long
    
    Call Setup
    Call DeleteOutputTab("RM-")
    lRMInputs = LoadRMandCFInputs()
    With lRMInputs
        lDealName = .DealName
        lNumSimulation = .NumOfSims
        lAnalysisDate = .AnalysisDate
        lCorrMatrix = .CorrMatrix
        lUseStatic = .StaticRndNum
        lRndSeed = .RandomizeSeed
        lperiod = .RMFreq
    End With
    
    'GetDealArrString
    lDeals = LoadDealNames
    
    'GetLastMaturityDate as date
    lLastMat = GetLastMaturityAllDeals(lDeals)
    
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Creating Cholskey Decomposition"
    
    If lUseStatic Then
        Rnd (-10)
        Randomize (lRndSeed)
    End If
    If lCorrMatrix = "System Defined" Then
        Call CreditMigrationSetup(lNumSimulation, False, mAllCollateral, lperiod)
    Else
        Call CreditMigrationSetup(lNumSimulation, False, , lperiod)
    End If
    
    Call CMAllSetup(lDeals, lNumSimulation, lAnalysisDate, lLastMat, lperiod)
    
    mProgressBar.Min = 0
    mProgressBar.Max = lNumSimulation * (UBound(lDeals) + 1)
    mProgressBar.Progress = 0
    mProgressBar.ShowCancelButton
    mProgressBar.Show
    For i = 1 To lNumSimulation
        If mProgressBar.Cancel Then Exit For
        mAllCollateral.ReesetAssets
        Call RunRatingHistory(lAnalysisDate, mAllCollateral)
        For j = 0 To UBound(lDeals)
            If mProgressBar.Cancel Then Exit For
            mProgressBar.Text = "Run Sim " & i & " of " & lNumSimulation & "." & "For " & lDeals(j) & "."
            mProgressBar.Progress = mProgressBar.Progress + 1
           Set mDealCollatCLO = New CollateralPoolForCLO
           Set mDealCollat = New CollateralPool
           Call LoadDealCollat(lDeals(j))
           Call CMAllAddDeal(lDeals(j), mDealCollat, i)
        Next j
    Next i
    If mProgressBar.Cancel = False Then
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("AVERAGE", "CDR"), False, "RM-Averages-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("AVERAGE", "NUMPERDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("AVERAGE", "BALPERDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Number of CCC", GetSimStatTimeSeries("AVERAGE", "NUMCCC"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("AVERAGE", "BALCCC"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of Performing", GetSimStatTimeSeries("AVERAGE", "BALPERF"), False, "RM-Averages-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("AVERAGE", "BALDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("AVERAGE", "BALMAT"), False, "RM-Averages-")
        
        
        lSimlong = GetSimNum("Max")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MAX", "CDR"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MAX", "NUMPERDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MAX", "BALPERDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Number of CCC", GetSimStatTimeSeries("MAX", "NUMCCC"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MAX", "BALCCC"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MAX", "BALPERF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MAX", "BALDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MAX", "BALMAT"), False, "RM-MAX-" & lSimlong & "-")
        
        lSimlong = GetSimNum("MIN")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MIN", "CDR"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MIN", "NUMPERDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MIN", "BALPERDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of CCC", GetSimStatTimeSeries("MIN", "NUMCCC"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MIN", "BALPERF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MIN", "BALPERF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MIN", "BALDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MIN", "BALMAT"), False, "RM-MIN-" & lSimlong & "-")
        
        lSimlong = GetSimNum("MEDIAN")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MEDIAN", "CDR"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MEDIAN", "NUMPERDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MEDIAN", "BALPERDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of CCC", GetSimStatTimeSeries("MEDIAN", "NUMCCC"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MEDIAN", "BALCCC"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MEDIAN", "BALPERF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MEDIAN", "BALDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MEDIAN", "BALMAT"), False, "RM-MEDIAN-" & lSimlong & "-")
    End If
    Call CreditMigrationCleanup
    mProgressBar.Hide
    Call Cleanup
    'Call GetAverages
    'Sheets("CM-Output").Activate
    MsgBox "Rating Migration is Finished", vbOKOnly, "Finished"
    Call Cleanup
    Exit Sub
ErrorTrap:
    MsgBox "There was an error in running rating migration", vbOKOnly, "Error!"
    Call Cleanup
End Sub

Public Sub RunOptimization()
    Dim lOutput As Variant
    
    Call Setup
    Call DeleteOutputTab("Optimization-")
    Call LoadDealCollat(mDealName)
    Call LoadAccounts(mDealName)
    Call LoadTestInputs(mDealName)
    Call CalcOptimization
    Call Cleanup
    MsgBox "Optimization have finish running"
    
End Sub
Public Sub RunRebalancing()
    Dim lDealName As String
    Dim lOutput As Variant
    Call Setup
    Call DeleteOutputTab("Rebalance-")
    Call UpdaeObjeWeights
    Call LoadDealCollat(mDealName)
    Call LoadAccounts(mDealName)
    Call LoadTestInputs(mDealName)
    'Call CalcRebalancing
    Call CalcRebalancing2
    Call Cleanup
    MsgBox "Rebalancing have finish running"
End Sub
Public Sub RunHypo2()
    Dim lDealName As String
    Dim lOutput As Variant
    Call Setup
    Call DeleteOutputTab("HYPO-")
    Call LoadDealCollat(mDealName)
    Call LoadAccounts(mDealName)
    Call LoadTestInputs(mDealName)
    Call CalcHypo(mDealName)
    Call Cleanup
    MsgBox "Hypo have finish running"
End Sub
Private Sub CalcHypo(iDealName As String)
    Dim lHypoAssets() As HypoInputs
    Dim lRunAssetsIndividually As Boolean
    Dim lCounter As Long
    Dim lHypoOutPut As Variant
    Dim i As Long
    Dim lBRSID As Variant
    Dim lHypoInputs As HypoUserInputs
    
    
    lHypoInputs = LoadHypoUserInputs(iDealName)
    lRunAssetsIndividually = Not lHypoInputs.PoolMode
    If lRunAssetsIndividually Then
        ReDim lHypoAssets(0)
    Else
        ReDim lHypoAssets(UBound(lHypoInputs.Trades))
    End If
    If lRunAssetsIndividually Then
        For i = LBound(lHypoInputs.Trades) To UBound(lHypoInputs.Trades)
            With lHypoInputs.Trades(i)
                Set lHypoAssets(0).Asset = mAllCollateral.GetAsset(.BRSID)
                If Not (lHypoAssets(0).Asset Is Nothing) Then
                    If .TrnsType = Buy Then
                        lHypoAssets(0).Transaction = "Buy"
                    ElseIf .TrnsType = Sale Then
                        lHypoAssets(0).Transaction = "Sale"
                    End If
                    lHypoAssets(0).ParAmount = .Par
                    lHypoAssets(0).Price = .Price
                    lHypoAssets(0).Asset.AddPar .Par
                    lHypoOutPut = mDealCollat.GetHypoOutputs(lHypoAssets)
                    Call OutputDataToSheet(lHypoAssets(0).Asset.BLKRockID & "     " & lHypoAssets(0).Asset.IssueName, lHypoOutPut, False, "HYPO-" & iDealName & "-")
                End If
            End With
        Next i
    Else
        Dim lHypo As CollateralPool
        
        For i = LBound(lHypoInputs.Trades) To UBound(lHypoInputs.Trades)
            With lHypoInputs.Trades(i)
                Set lHypoAssets(i).Asset = mAllCollateral.GetAsset(.BRSID)
                If Not (lHypoAssets(i).Asset Is Nothing) Then
                    If .TrnsType = Buy Then
                        lHypoAssets(i).Transaction = "Buy"
                    ElseIf .TrnsType = Sale Then
                        lHypoAssets(i).Transaction = "Sale"
                    End If
                    lHypoAssets(i).ParAmount = .Par
                    lHypoAssets(i).Price = .Price
                    lHypoAssets(i).Asset.AddPar .Par
                End If
            End With
        Next i
        lHypoOutPut = mDealCollat.GetHypoOutputs(lHypoAssets)
        Call OutputDataToSheet("Pool", lHypoOutPut, False, "HYPO-" & iDealName & "-")
        Call OutputDataToSheet("Hypothetical Trade's Attributes", GetHypoAttributes(lHypoAssets, lHypoInputs.Libor), False, "HYPO-" & iDealName & "-")
    End If

End Sub
Private Sub CalcRankings()
    Dim lCObjective As Double
    Dim lNumofAllAssets As Long
    Dim lType As String
    Dim lIncExistLoan As Boolean
    Dim lNumAssets As Long
    Dim lRankInfo As Variant
    Dim lLoanSize As Double
    Dim lBlkRockIDs As Variant
    Dim lBlkRockID As String
    Dim lRandNum As Long
    Dim lCounter As Long
    Dim lIncLoan As Boolean
    Dim lRankDict As Dictionary
    Dim lRankInputs() As HypoInputs
    Dim lOutputVar As Variant
    Dim lkeys As Variant
    Dim lAsset As Asset
    Dim j As Long
    Dim lFilter As String
    Dim i As Long
    

'    lRankInfo = Range("OPTInfo").Value
'    For i = LBound(lRankInfo, 1) To UBound(lRankInfo, 1)
'        If UCase(lRankInfo(i, 1)) = "TRANSACTION TYPE" Then
'            lType = lRankInfo(i, 2)
'        ElseIf UCase(lRankInfo(i, 1)) = "ALLOW PAR INCREASE TO EXISTING LOANS" Then
'            lIncExistLoan = lRankInfo(i, 2)
'        ElseIf UCase(lRankInfo(i, 1)) = "MAX NUM ASSETS" Then
'            lNumAssets = lRankInfo(i, 2)
'        ElseIf UCase(lRankInfo(i, 1)) = "INCREMENTAL LOAN SIZE" Then
'            lLoanSize = lRankInfo(i, 2)
'        End If
'    Next i
    Dim lRandR As RankandRebalInputs
    lRandR = LoadRebalandRankInfo()
    With lRandR
        lIncExistLoan = .InclDealLoans
        lLoanSize = .IncPar
        If .TranType = Buy Then
            lType = "Buy"
        ElseIf .TranType = Sale Then
            lType = "Sale"
        End If
    End With
    
    If lType = "" Then
        MsgBox "For Rankings transaction type most be buy or sale.", vbOKOnly
        Exit Sub
    ElseIf lType = "Buy" Then
        lFilter = lRandR.BuyFilter
    Else
        lFilter = lRandR.SaleFilter
    End If
    
    'Call ReturnRankings(lType, lIncExistLoan, lNumAssets, lLoanSize, lRankDict, lRankInputs, lFilter)
    Call ReturnRankings2(lType, lIncExistLoan, lNumAssets, lLoanSize, lRankDict, lRankInputs, lFilter)
    Call OutputRankings(lType, lRankDict, lRankInputs, lFilter)

End Sub
Private Sub OutputRankings(iRankType As String, iRankDict As Dictionary, iRankInputs() As HypoInputs, iFilter As String)
    Dim lFilterField() As String
    Dim lNumColumns As Long
    Dim lNumRows As Long
    Dim lBlkRockIDs As Variant
    Dim lOutputVar As Variant
    Dim i, j As Long
    Dim lIsFilterFields As Boolean
    Dim lAsset As Asset
    Dim lIncFilter As Dictionary
    
    lIsFilterFields = Len(iFilter) > 0
    'Get the Number of Columns
    
    
    If lIsFilterFields Then
        Set lIncFilter = New Dictionary
        lIncFilter.Add "MARKET VALUE", 1
        lIncFilter.Add "Moody's Rating", 2
        lIncFilter.Add "S&P Rating", 3
        lIncFilter.Add "Coupon", 4
        lIncFilter.Add "WAS", 5
        lIncFilter.Add "LIBOR Floor", 6
        lIncFilter.Add "WAL", 7
        lIncFilter.Add "Moody's Recovery Rate", 8
        lFilterField = FilterFields(iFilter, lIncFilter)
        If UBound(lFilterField) = 0 Then
            If Len(lFilterField(0)) > 0 Then
                lNumColumns = 12
            Else
                lIsFilterFields = False
                lNumColumns = 11
            End If
        Else
            lNumColumns = 11 + UBound(lFilterField) + 1
        End If
    Else
        lNumColumns = 11
    End If
    
    If iRankDict.Count = 0 Then
        lNumRows = 1
    Else
        lNumRows = iRankDict.Count
        lBlkRockIDs = iRankDict.Keys
    End If
    
    ReDim lOutputVar(0 To lNumRows, 0 To lNumColumns)
    lOutputVar(0, 0) = "Objective Function"
    lOutputVar(0, 1) = "BlackRock ID"
    lOutputVar(0, 2) = "Issue Name"
    lOutputVar(0, 3) = "Par"
    lOutputVar(0, 4) = "Market Value"
    lOutputVar(0, 5) = "Moody's Rating"
    lOutputVar(0, 6) = "S&P's Rating"
    lOutputVar(0, 7) = "Coupon"
    lOutputVar(0, 8) = "WAS"
    lOutputVar(0, 9) = "LIBOR Floor"
    lOutputVar(0, 10) = "WAL"
    lOutputVar(0, 11) = "Moody's Recovery Rate"
    If lIsFilterFields Then
        For i = LBound(lFilterField) To UBound(lFilterField)
            lOutputVar(0, 12 + i) = lFilterField(i)
        Next i
    End If
    
    If lNumRows = 1 Then
        lOutputVar(1, 0) = "Unable to find any assets that increases the objective function"
    Else
        For i = LBound(lBlkRockIDs) To UBound(lBlkRockIDs)
            Set lAsset = mAllCollateral.GetAssetNonCopy(CStr(lBlkRockIDs(i)))
            lOutputVar(i + 1, 0) = iRankDict(lBlkRockIDs(i))
            lOutputVar(i + 1, 1) = lBlkRockIDs(i)
            lOutputVar(i + 1, 2) = lAsset.IssueName
            For j = 0 To UBound(iRankInputs)
                If iRankInputs(j).Asset.BLKRockID = lBlkRockIDs(i) Then
                    lOutputVar(i + 1, 3) = iRankInputs(j).Asset.ParAmount
                    Exit For
                End If
            Next j
            If lAsset.MarketValue = 0 Then
                lOutputVar(i + 1, 4) = Format(1, "0.000%")
            Else
                lOutputVar(i + 1, 4) = Format(lAsset.MarketValue / 100, "0.000%")
            End If
            lOutputVar(i + 1, 5) = lAsset.MDYRating
            lOutputVar(i + 1, 6) = lAsset.SPRating
            lOutputVar(i + 1, 7) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i + 1, 8) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i + 1, 9) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i + 1, 10) = lAsset.WAL
            lOutputVar(i + 1, 11) = Format(lAsset.MDYRecoveryRate, "0.000%")
            If lIsFilterFields Then
                For j = 0 To UBound(lFilterField)
                    lOutputVar(i + 1, 12 + j) = mAllCollateral.GetAssetParameter(lAsset.BLKRockID, lFilterField(j))
                Next j
            End If
        Next i
    End If
    If UCase(iRankType) = "BUY" Then
        Call OutputDataToSheet("Assets to Purchase", lOutputVar, False, "Rankings-")
    Else
        Call OutputDataToSheet("Assets to Sale", lOutputVar, False, "Rankings-")
    End If
    

End Sub
Private Sub SetRandomizeSeed()
    Rnd (-10)
    Randomize (12)
End Sub
Private Function GetRankableAssets(iBuySale As String, iInclExtLoans As Boolean, Optional iFilter As String) As Variant
    Dim lOutKeys As Variant
    Dim lAssetColl As CollateralPool
    Dim lAssetKeys As Variant
    Dim lBlkRockID As Variant
    Dim lIncl As Boolean
    Dim lCounter As Long
    
    If UCase(iBuySale) = "BUY" Then
        Set lAssetColl = mAllCollateral
    Else
        Set lAssetColl = mDealCollat
    End If
    
    If Len(iFilter) > 0 Then
        lAssetKeys = lAssetColl.ApplyFilter(iFilter).Keys
    Else
        lAssetKeys = lAssetColl.GetBLKRockIDs
    End If
    If UBound(lAssetKeys) = -1 Then
        'This means nothing matched the filter
        GetRankableAssets = lAssetKeys
        Exit Function
    End If
    ReDim lOutKeys(UBound(lAssetKeys))
    For Each lBlkRockID In lAssetKeys
        lIncl = True
        If UCase(iBuySale) = "BUY" Then
            If iInclExtLoans = False Then
                If mDealCollat.AssetExist(CStr(lBlkRockID)) Then
                    lIncl = False
                End If
            End If
            If lIncl = False Then
            
            ElseIf mAllCollateral.GetAssetParameter(CStr(lBlkRockID), "DEFAULTED") Then
                lIncl = False
            ElseIf mAllCollateral.GetAssetParameter(CStr(lBlkRockID), "MARKET VALUE") < 75 Then
                lIncl = False
            End If
        End If
        If lIncl Then
            lOutKeys(lCounter) = lBlkRockID
            lCounter = lCounter + 1
        End If
    Next lBlkRockID
    If lCounter > 0 Then
        ReDim Preserve lOutKeys(lCounter - 1)
    Else
        lOutKeys = -1
    End If

    GetRankableAssets = lOutKeys
End Function
Private Sub ReturnRankings(iType As String, ByVal iIncExtLoan As Boolean, iNumAssets As Long, iLoanSize As Double, oRankDict As Dictionary, oRankInputs() As HypoInputs, Optional iFilter As String)
    'This uses an random algothrim to select loans to rank.
    Dim lBlkRockIDs As Variant
    Dim lNumofAllAssets As Long
    Dim lCounter As Long
    Dim lIncLoan As Boolean
    Dim lRandNum As Long
    Dim lBlkRockID As String
    Dim i As Long
    
    
    lBlkRockIDs = GetRankableAssets(iType, iIncExtLoan, iFilter)
    lNumofAllAssets = UBound(lBlkRockIDs)
    Set oRankDict = New Dictionary
    If iNumAssets > lNumofAllAssets Then
        ReDim oRankInputs(lNumofAllAssets)
    Else
        ReDim oRankInputs(iNumAssets - 1)
    End If

    Do While lCounter < iNumAssets
        lIncLoan = True
        If iNumAssets > lNumofAllAssets Then
            'If the number of random aassets to select is greater numbe of available assets
            'Just loop through available assets
            If i > lNumofAllAssets Then
                Exit Do
            Else
                lRandNum = i
            End If
        Else
            lRandNum = Rnd() * lNumofAllAssets
        End If
        lBlkRockID = CStr(lBlkRockIDs(lRandNum))
        If oRankDict.Exists(lBlkRockID) Then
            lIncLoan = False
        End If
        If lIncLoan Then
            Set oRankInputs(lCounter).Asset = mAllCollateral.GetAsset(lBlkRockID)
            oRankInputs(lCounter).Asset.AddPar (iLoanSize)
            oRankInputs(lCounter).ParAmount = iLoanSize
            oRankInputs(lCounter).Transaction = iType
'            If oRankInputs(lCounter).Asset.MarketValue = 0 Then
'                oRankInputs(lCounter).Price = 1
'            End If
            oRankDict.Add lBlkRockID, 0
            lCounter = lCounter + 1
        End If
        i = i + 1
    Loop
    Set oRankDict = Nothing
    Set oRankDict = mDealCollat.GetRankings(oRankInputs)
    SortDictionary oRankDict, False, True
    
End Sub
Private Sub ReturnRankings2(iType As String, ByVal iIncExtLoan As Boolean, iNumAssets As Long, iLoanSize As Double, oRankDict As Dictionary, oRankInputs() As HypoInputs, Optional iFilter As String)
    'This ranks assets randaomly
    Dim lBlkRockIDs As Variant
    Dim lNumofAllAssets As Long
    Dim lCounter As Long
    Dim lIncLoan As Boolean
    Dim lRandNum As Long
    Dim lBlkRockID As String
    Dim i As Long
    Dim lAssetDict As Dictionary
    Dim lTransType As TransactionType
    
    
    
    lBlkRockIDs = GetRankableAssets(iType, iIncExtLoan, iFilter)
    If Not IsArray(lBlkRockIDs) Then
        Set oRankDict = New Dictionary
        Exit Sub
    ElseIf UBound(lBlkRockIDs) = -1 Then
        Set oRankDict = New Dictionary
        Exit Sub
    End If
    ReDim oRankInputs(LBound(lBlkRockIDs) To UBound(lBlkRockIDs))
    Set lAssetDict = New Dictionary
    For i = LBound(lBlkRockIDs) To UBound(lBlkRockIDs)
        lBlkRockID = CStr(lBlkRockIDs(i))
        Set oRankInputs(i).Asset = mAllCollateral.GetAssetNonCopy(lBlkRockID)
        oRankInputs(i).Asset.UpdatePar (iLoanSize)
        oRankInputs(i).ParAmount = iLoanSize
        oRankInputs(i).Transaction = iType
        lAssetDict.Add lBlkRockID, mAllCollateral.GetAssetNonCopy(lBlkRockID)
    Next i
    If UCase(iType) = "BUY" Then
        lTransType = Buy
    Else
        lTransType = Sale
    End If
    Set oRankDict = mDealCollat.GetAssetObjective(lAssetDict, lTransType)
    If UCase(iType) = "BUY" Then
        SortDictionary oRankDict, False, True
    ElseIf UCase(iType) = "SALE" Then
        SortDictionary oRankDict, False, False
    End If
End Sub
Private Sub CalcOptimization()
    Dim lType As String
    Dim lNumAssets As Long
    Dim lIncLoanSize As Double
    Dim lParIncrease As Boolean
    Dim lOptDict As Dictionary
    Dim lOptInput() As HypoInputs
    Dim lOptInputVar As Variant
    Dim i As Long
    Dim lCurrOBJ As Double
    Dim lSaleAssetsDict As Dictionary
    Dim lPurchAssetsDict As Dictionary
    Dim lObjDict As Dictionary
    Dim lkeys As Variant
    Dim lAsset As Asset
    Dim lLastBuyorSale As String
    Dim lCurrentBuyorSale As String
    Dim lIterator As Long
    Dim lMaxIterations As Long
    Dim lOptType As String
    Dim lFilter As String
    
    lOptInputVar = Range("OPTInfo").Value
    For i = LBound(lOptInputVar, 1) To UBound(lOptInputVar, 1)
        If UCase(lOptInputVar(i, 1)) = "MAX NUM ASSETS" Then
            lNumAssets = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "INCREMENTAL LOAN SIZE" Then
            lIncLoanSize = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "ALLOW PAR INCREASE TO EXISTING LOAN" Then
            lParIncrease = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "TRANSACTION TYPE" Then
            lOptType = lOptInputVar(i, 2)
        End If
    Next i
    lFilter = LoadFilter()
    Set lPurchAssetsDict = New Dictionary
    Set lSaleAssetsDict = New Dictionary
    lCurrOBJ = mDealCollat.GetObjectiveValue
    Set lObjDict = New Dictionary

    mProgressBar.Max = mDealCollat.CheckAccountBalance(Collection, Principal)
    mProgressBar.Text = "Running Optimization"
    mProgressBar.Show
    mProgressBar.ShowCancelButton
    lMaxIterations = mDealCollat.CheckAccountBalance(Collection, Principal) / lIncLoanSize * 2
    Do While mDealCollat.CheckAccountBalance(Collection, Principal) > 0
        mProgressBar.Progress = mProgressBar.Max - mDealCollat.CheckAccountBalance(Collection, Principal)
        If mCancelFlag Then Exit Do
        If lOptType = "All" Then
            If Rnd() > 0.5 Then lCurrentBuyorSale = "BUY" Else lCurrentBuyorSale = "SALE"
        ElseIf lOptType = "Buy" Then
            lCurrentBuyorSale = "BUY"
        ElseIf lOptType = "Sale" Then
            lCurrentBuyorSale = "SALE"
        End If
        
        Call ReturnRankings(lCurrentBuyorSale, lParIncrease, lNumAssets, lIncLoanSize, lOptDict, lOptInput, lFilter)
        If mDealCollat.CheckAccountBalance(Collection, Principal) < 1# Then
            Exit Do
        ElseIf lOptDict.Count = 0 And lLastBuyorSale = lCurrentBuyorSale And lIterator > lMaxIterations * 0.5 Then
            MsgBox "Unable to find anymore assets that fit the optimization criteria." & vbCr & "Amount of Principal Remaining is " & Format(mDealCollat.CheckAccountBalance(Collection, Principal), "$##.00")
            Exit Do
        ElseIf (lIterator > lMaxIterations And lOptDict.Count = 0) Or lIterator > 1000 Then
            MsgBox "Optimization has reached max iteration." & vbCr & "Amount of Principal Remaining is " & Format(mDealCollat.CheckAccountBalance(Collection, Principal), "$##.00")
            Exit Do
        ElseIf lOptDict.Count = 0 Then
        
        
        ElseIf mProgressBar.Cancel = True Then
            Exit Do
        Else
            lkeys = lOptDict.Keys
            If lOptDict(lkeys(0)) > lCurrOBJ Then
                For i = LBound(lOptInput) To UBound(lOptInput)
                    If lkeys(0) = lOptInput(i).Asset.BLKRockID Then
                        Set lAsset = lOptInput(i).Asset.Copy
                        'Debug.Print mDealCollat.CheckAccountBalance(Collection, Principal)
                        
                        If lCurrentBuyorSale = "BUY" Then
                            If lAsset.MarketValue = 0 Then
                                mDealCollat.PurchaseAsset lAsset, 100
                            Else
                                mDealCollat.PurchaseAsset lAsset
                            End If
                            'Debug.Print mDealCollat.CheckAccountBalance(Collection, Principal)
                            If lPurchAssetsDict.Exists(lkeys(0)) Then
                               lPurchAssetsDict(lkeys(0)).AddPar lAsset.ParAmount
                            Else
                                lPurchAssetsDict.Add lkeys(0), lAsset
                            End If
                        Else
                            If lAsset.MarketValue = 0 Then
                                mDealCollat.SaleAsset lAsset, 100
                            Else
                                mDealCollat.SaleAsset lAsset
                            End If
                            'Debug.Print mDealCollat.CheckAccountBalance(Collection, Principal)
                            If lSaleAssetsDict.Exists(lkeys(0)) Then
                               lSaleAssetsDict(lkeys(0)).AddPar lAsset.ParAmount
                            Else
                                lSaleAssetsDict.Add lkeys(0), lAsset
                            End If
                        
                        End If
                        lCurrOBJ = mDealCollat.GetObjectiveValue
                        lObjDict.Add lCurrOBJ, lAsset.Copy
                        Exit For
                    End If
                Next i
            Else
                Exit Do
            End If
        End If
        lIterator = lIterator + 1
        lLastBuyorSale = lCurrentBuyorSale
    Loop
    mProgressBar.Hide
    
    If lObjDict.Count > 0 Then
        ReDim lOutputVar(0 To lObjDict.Count, 0 To 11)
        'Call SortDictionary(lOBJDict, True, False)
        lkeys = lObjDict.Keys
        lOutputVar(0, 0) = "Objective Function"
        lOutputVar(0, 1) = "BlackRock ID"
        lOutputVar(0, 2) = "Issue Name"
        lOutputVar(0, 3) = "Par"
        lOutputVar(0, 4) = "Market Value"
        lOutputVar(0, 5) = "Moody's Rating"
        lOutputVar(0, 6) = "S&P's Rating"
        lOutputVar(0, 7) = "Coupon"
        lOutputVar(0, 8) = "WAS"
        lOutputVar(0, 9) = "LIBOR Floor"
        lOutputVar(0, 10) = "WAL"
        lOutputVar(0, 11) = "Moody's Recovery rate"
        For i = 1 To lObjDict.Count
            Set lAsset = lObjDict(lkeys(i - 1))
            lOutputVar(i, 0) = lkeys(i - 1)
            lOutputVar(i, 1) = lAsset.BLKRockID
            lOutputVar(i, 2) = lAsset.IssueName
            
            If lPurchAssetsDict.Exists(lAsset.BLKRockID) = True Then
                lOutputVar(i, 3) = lAsset.ParAmount
            Else
                lOutputVar(i, 3) = -lAsset.ParAmount
            End If
            lOutputVar(i, 4) = lAsset.MarketValue
            lOutputVar(i, 5) = lAsset.MDYRating
            lOutputVar(i, 6) = lAsset.SPRating
            lOutputVar(i, 7) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 9) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 10) = lAsset.WAL
            lOutputVar(i, 11) = Format(lAsset.MDYRecoveryRate, "0.000%")
        Next i
        Call OutputDataToSheet("Objective Function", lOutputVar, False, "Optimization-")
    End If
    If lPurchAssetsDict.Count > 0 Then
        ReDim lOutputVar(0 To lPurchAssetsDict.Count, 0 To 10)
        lkeys = lPurchAssetsDict.Keys
        lOutputVar(0, 0) = "BlackRock ID"
        lOutputVar(0, 1) = "Issue Name"
        lOutputVar(0, 2) = "Par"
        lOutputVar(0, 3) = "Market Value"
        lOutputVar(0, 4) = "Moody's Rating"
        lOutputVar(0, 5) = "S&P's Rating"
        lOutputVar(0, 6) = "Coupon"
        lOutputVar(0, 7) = "WAS"
        lOutputVar(0, 8) = "LIBOR Floor"
        lOutputVar(0, 9) = "WAL"
        lOutputVar(0, 10) = "Moody's Recovery rate"
        For i = 1 To lPurchAssetsDict.Count
            Set lAsset = lPurchAssetsDict(lkeys(i - 1))
            lOutputVar(i, 0) = lAsset.BLKRockID
            lOutputVar(i, 1) = lAsset.IssuerName
            lOutputVar(i, 2) = lAsset.ParAmount
            lOutputVar(i, 3) = lAsset.MarketValue
            lOutputVar(i, 4) = lAsset.MDYRating
            lOutputVar(i, 5) = lAsset.SPRating
            lOutputVar(i, 6) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 7) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 9) = lAsset.WAL
            lOutputVar(i, 10) = Format(lAsset.MDYRecoveryRate, "0.000%")
        Next i
        Call OutputDataToSheet("Assets To Purchase", lOutputVar, False, "Optimization-")
    End If
    
    If lSaleAssetsDict.Count > 0 Then
        ReDim lOutputVar(0 To lSaleAssetsDict.Count, 0 To 10)
        lkeys = lSaleAssetsDict.Keys
        lOutputVar(0, 0) = "BlackRock ID"
        lOutputVar(0, 1) = "Issue Name"
        lOutputVar(0, 2) = "Par"
        lOutputVar(0, 3) = "Market Value"
        lOutputVar(0, 4) = "Moody's Rating"
        lOutputVar(0, 5) = "S&P's Rating"
        lOutputVar(0, 6) = "Coupon"
        lOutputVar(0, 7) = "WAS"
        lOutputVar(0, 8) = "LIBOR Floor"
        lOutputVar(0, 9) = "WAL"
        lOutputVar(0, 10) = "Moody's Recovery rate"
        For i = 1 To lSaleAssetsDict.Count
            Set lAsset = lSaleAssetsDict(lkeys(i - 1))
            lOutputVar(i, 0) = lAsset.BLKRockID
            lOutputVar(i, 1) = lAsset.IssueName
            lOutputVar(i, 2) = lAsset.ParAmount
            lOutputVar(i, 3) = lAsset.MarketValue
            lOutputVar(i, 4) = lAsset.MDYRating
            lOutputVar(i, 5) = lAsset.SPRating
            lOutputVar(i, 6) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 7) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 9) = lAsset.WAL
            lOutputVar(i, 10) = Format(lAsset.MDYRecoveryRate, "0.000%")
        Next i
        Call OutputDataToSheet("Assets To Sale", lOutputVar, False, "Optimization-")
    End If
    
    
End Sub
Private Sub CalcRebalancing()
    Dim lType As String
    Dim lNumAssets As Long
    Dim lIncLoanSize As Double
    Dim lParIncrease As Boolean
    Dim lOptDict As Dictionary
    Dim lOptInput() As HypoInputs
    Dim lOptInputVar As Variant
    Dim i As Long
    Dim lCurrOBJ As Double
    Dim lSaleAssetsDict As Dictionary
    Dim lPurchAssetsDict As Dictionary
    Dim lObjDict As Dictionary
    Dim lkeys As Variant
    Dim lAsset As Asset
    Dim lLastBuyorSale As String
    Dim lCurrentBuyorSale As String
    Dim lIterator As Long
    Dim lMaxIterations As Long
    Dim lOptType As String
    Dim lBuyFilter As String
    Dim lSaleFilter As String
    Dim lBuyAmount As Double
    Dim lSaleAmount As Double
    Dim lBefore As Variant
    Dim lAfterSale As Variant
    Dim lAfterBuy As Variant
    Dim lTempParSize As Double
    Dim lTempNumAssets As Long
    
    
    Set lPurchAssetsDict = New Dictionary
    Set lSaleAssetsDict = New Dictionary
    Set lObjDict = New Dictionary
    
    lOptInputVar = Range("OPTInfo").Value
    For i = LBound(lOptInputVar, 1) To UBound(lOptInputVar, 1)
        If UCase(lOptInputVar(i, 1)) = "MAX NUM ASSETS" Then
            lNumAssets = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "INCREMENTAL LOAN SIZE" Then
            lIncLoanSize = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "ALLOW PAR INCREASE TO EXISTING LOANS" Then
            lParIncrease = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "TRANSACTION TYPE" Then
            lOptType = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "SALE PAR AMOUNT" Then
            lSaleAmount = lOptInputVar(i, 2)
        ElseIf UCase(lOptInputVar(i, 1)) = "BUY PAR AMOUNT" Then
            lBuyAmount = lOptInputVar(i, 2)
        End If
    Next i
    lBuyFilter = LoadFilter("BUY")
    lSaleFilter = LoadFilter("SALE")
    
    lCurrOBJ = mDealCollat.GetObjectiveValue
    lBefore = mDealCollat.GetTestResultsOutput
  
    'Check Sale Amount
    Dim lFilterParAmount As Double
    lFilterParAmount = mDealCollat.GetCollatParAmount(lSaleFilter)
    If lSaleAmount > lFilterParAmount Then
        lSaleAmount = lFilterParAmount
    End If
    lFilterParAmount = 0
    lTempParSize = lIncLoanSize
    lTempNumAssets = lNumAssets
    
    
    mProgressBar.Max = lSaleAmount
    mProgressBar.Text = "Running Rebalancing Sale"
    mProgressBar.Show
    mProgressBar.ShowCancelButton
    
    Do While lFilterParAmount < lSaleAmount
        mProgressBar.Progress = lFilterParAmount
        If mProgressBar.Cancel Then Exit Do
        lCurrentBuyorSale = "SALE"
        If lTempParSize > lSaleAmount - lFilterParAmount Then
            lTempParSize = (lSaleAmount - lFilterParAmount)
        End If
        Call ReturnRankings(lCurrentBuyorSale, lParIncrease, lTempNumAssets, lTempParSize, lOptDict, lOptInput, lSaleFilter)
        If lOptDict.Count = 0 Then
            'Debug.Assert 1 <> 1
            If mDealCollat.NumOfAssets(lSaleFilter) = 0 Then
                'non of the remaining assets match the filter
                Exit Do
            Else
                If mDealCollat.NumOfAssets(lSaleFilter) > lTempNumAssets Then
                    'Expand serach speace
                    lTempNumAssets = lTempNumAssets + 5
                Else
                    'None of the filtered assets increase the objective
                    'What now
                    Exit Do
                End If
            End If
        ElseIf mProgressBar.Cancel = True Then
            Exit Do
        Else
            lkeys = lOptDict.Keys
            'If lOptDict(lKeys(0)) > lCurrOBJ Then
                For i = LBound(lOptInput) To UBound(lOptInput)
                    If lkeys(0) = lOptInput(i).Asset.BLKRockID Then
                        Set lAsset = lOptInput(i).Asset.Copy
      
                        mDealCollat.SaleAsset lAsset
                        If lSaleAssetsDict.Exists(lkeys(0)) Then
                           lSaleAssetsDict(lkeys(0)).AddPar lAsset.ParAmount
                        Else
                            lSaleAssetsDict.Add lkeys(0), lAsset
                        End If
                        lFilterParAmount = lFilterParAmount + lAsset.ParAmount
                        
                        lCurrOBJ = mDealCollat.GetObjectiveValue
                        'mDealCollat.CalcConcentrationTest.UpdatePreviousValues
                        lObjDict.Add lCurrOBJ, lAsset.Copy
                        
                        Exit For
                    End If
                Next i
            'End If
        End If
    Loop
    'Now Buy
    lFilterParAmount = 0
    lTempParSize = lIncLoanSize
    lTempNumAssets = lNumAssets
    mProgressBar.Text = "Running Rebalancing Buy"
    mProgressBar.Max = lBuyAmount
    lAfterSale = mDealCollat.GetTestResultsOutput
    Do While lFilterParAmount < lBuyAmount And mDealCollat.CheckAccountBalance(Collection, Principal) > 0
        mProgressBar.Progress = lFilterParAmount
        If mProgressBar.Cancel Then Exit Do
        lCurrentBuyorSale = "BUY"
        Call ReturnRankings(lCurrentBuyorSale, lParIncrease, lTempNumAssets, lTempParSize, lOptDict, lOptInput, lBuyFilter)

        If lOptDict.Count = 0 Then
            'Debug.Assert 1 <> 1
            
            lTempNumAssets = lTempNumAssets + 5
            
        ElseIf mProgressBar.Cancel = True Then
            Exit Do
        Else
            lkeys = lOptDict.Keys
            If lOptDict(lkeys(0)) > lCurrOBJ Then
                For i = LBound(lOptInput) To UBound(lOptInput)
                    If lkeys(0) = lOptInput(i).Asset.BLKRockID Then
                        Set lAsset = lOptInput(i).Asset.Copy
                        'Check to see if you have enough cash
      
                        mDealCollat.PurchaseAsset lAsset
                        If lPurchAssetsDict.Exists(lkeys(0)) Then
                           lPurchAssetsDict(lkeys(0)).AddPar lAsset.ParAmount
                        Else
                            lPurchAssetsDict.Add lkeys(0), lAsset
                        End If
                        lFilterParAmount = lFilterParAmount + lAsset.ParAmount
                        
                        lCurrOBJ = mDealCollat.GetObjectiveValue
                        lObjDict.Add lCurrOBJ, lAsset.Copy
                        Exit For
                    End If
                Next i
                
            Else
                Exit Do
            End If
        End If
    Loop
    
    
    
    mProgressBar.Hide
    lAfterBuy = mDealCollat.GetTestResultsOutput
    Call OutputDataToSheet("Before", lBefore, False, "Rebalance-")
    Call OutputDataToSheet("After Sale", lAfterSale, False, "Rebalance-")
    Call OutputDataToSheet("After Buy", lAfterBuy, False, "Rebalance-")
    If lObjDict.Count > 0 Then
        ReDim lOutputVar(0 To lObjDict.Count, 0 To 12)
        'Call SortDictionary(lOBJDict, True, False)
        lkeys = lObjDict.Keys
        lOutputVar(0, 0) = "Objective Function"
        lOutputVar(0, 1) = "BlackRock ID"
        lOutputVar(0, 2) = "Issue Name"
        lOutputVar(0, 3) = "Par"
        lOutputVar(0, 4) = "Market Value"
        lOutputVar(0, 5) = "Moody's Rating"
        lOutputVar(0, 6) = "S&P's Rating"
        lOutputVar(0, 7) = "Coupon"
        lOutputVar(0, 8) = "WAS"
        lOutputVar(0, 9) = "LIBOR Floor"
        lOutputVar(0, 10) = "WAL"
        lOutputVar(0, 11) = "Moody's Recovery rate"
        lOutputVar(0, 12) = "Analyst Opinion"
        For i = 1 To lObjDict.Count
            Set lAsset = lObjDict(lkeys(i - 1))
            lOutputVar(i, 0) = lkeys(i - 1)
            lOutputVar(i, 1) = lAsset.BLKRockID
            lOutputVar(i, 2) = lAsset.IssueName
            
            If lPurchAssetsDict.Exists(lAsset.BLKRockID) = True Then
                lOutputVar(i, 3) = lAsset.ParAmount
            Else
                lOutputVar(i, 3) = -lAsset.ParAmount
            End If
            lOutputVar(i, 4) = lAsset.MarketValue
            lOutputVar(i, 5) = lAsset.MDYRating
            lOutputVar(i, 6) = lAsset.SPRating
            lOutputVar(i, 7) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 9) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 10) = lAsset.WAL
            lOutputVar(i, 11) = Format(lAsset.MDYRecoveryRate, "0.000%")
            lOutputVar(0, 12) = lAsset.AnalystOpinion
        Next i
        Call OutputDataToSheet("Objective Function", lOutputVar, False, "Rebalance-")
    End If
    If lPurchAssetsDict.Count > 0 Then
        ReDim lOutputVar(0 To lPurchAssetsDict.Count, 0 To 11)
        lkeys = lPurchAssetsDict.Keys
        lOutputVar(0, 0) = "BlackRock ID"
        lOutputVar(0, 1) = "Issue Name"
        lOutputVar(0, 2) = "Par"
        lOutputVar(0, 3) = "Market Value"
        lOutputVar(0, 4) = "Moody's Rating"
        lOutputVar(0, 5) = "S&P's Rating"
        lOutputVar(0, 6) = "Coupon"
        lOutputVar(0, 7) = "WAS"
        lOutputVar(0, 8) = "LIBOR Floor"
        lOutputVar(0, 9) = "WAL"
        lOutputVar(0, 10) = "Moody's Recovery rate"
        lOutputVar(0, 11) = "Analyst Opinion"
        For i = 1 To lPurchAssetsDict.Count
            Set lAsset = lPurchAssetsDict(lkeys(i - 1))
            lOutputVar(i, 0) = lAsset.BLKRockID
            lOutputVar(i, 1) = lAsset.IssuerName
            lOutputVar(i, 2) = lAsset.ParAmount
            lOutputVar(i, 3) = lAsset.MarketValue
            lOutputVar(i, 4) = lAsset.MDYRating
            lOutputVar(i, 5) = lAsset.SPRating
            lOutputVar(i, 6) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 7) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 9) = lAsset.WAL
            lOutputVar(i, 10) = Format(lAsset.MDYRecoveryRate, "0.000%")
            lOutputVar(i, 11) = lAsset.AnalystOpinion
        Next i
        Call OutputDataToSheet("Assets To Purchase", lOutputVar, False, "Rebalance-")
    End If
    
    If lSaleAssetsDict.Count > 0 Then
        ReDim lOutputVar(0 To lSaleAssetsDict.Count, 0 To 11)
        lkeys = lSaleAssetsDict.Keys
        lOutputVar(0, 0) = "BlackRock ID"
        lOutputVar(0, 1) = "Issue Name"
        lOutputVar(0, 2) = "Par"
        lOutputVar(0, 3) = "Market Value"
        lOutputVar(0, 4) = "Moody's Rating"
        lOutputVar(0, 5) = "S&P's Rating"
        lOutputVar(0, 6) = "Coupon"
        lOutputVar(0, 7) = "WAS"
        lOutputVar(0, 8) = "LIBOR Floor"
        lOutputVar(0, 9) = "WAL"
        lOutputVar(0, 10) = "Moody's Recovery rate"
        lOutputVar(0, 11) = "Analyst Opinion"
        For i = 1 To lSaleAssetsDict.Count
            Set lAsset = lSaleAssetsDict(lkeys(i - 1))
            lOutputVar(i, 0) = lAsset.BLKRockID
            lOutputVar(i, 1) = lAsset.IssueName
            lOutputVar(i, 2) = lAsset.ParAmount
            lOutputVar(i, 3) = lAsset.MarketValue
            lOutputVar(i, 4) = lAsset.MDYRating
            lOutputVar(i, 5) = lAsset.SPRating
            lOutputVar(i, 6) = Format(lAsset.Coupon, "0.000%")
            lOutputVar(i, 7) = Format(lAsset.CpnSpread, "0.000%")
            lOutputVar(i, 8) = Format(lAsset.LiborFloor, "0.000%")
            lOutputVar(i, 9) = lAsset.WAL
            lOutputVar(i, 10) = Format(lAsset.MDYRecoveryRate, "0.000%")
            lOutputVar(i, 11) = lAsset.AnalystOpinion
        Next i
        Call OutputDataToSheet("Assets To Sale", lOutputVar, False, "Rebalance-")
    End If

    
    
End Sub

Private Function LoadYieldCurve(iAnalaysisDate As Date) As YieldCurve
    Dim lRates As Variant
    Dim lYC As YieldCurve
    Dim lDict As Dictionary
    Dim lItem As Double
    Dim i As Long

    lRates = Range("LIBORCurve").Value
    Set lDict = New Dictionary
    For i = LBound(lRates, 1) To UBound(lRates, 1)
        lDict.Add CLng(lRates(i, 1)), lRates(i, 2)
    Next i
    Set lYC = New YieldCurve
    lYC.Setup "LIBOR", iAnalaysisDate, lDict
    Set LoadYieldCurve = lYC
    
End Function

Public Sub RunDealCF()
    Dim lNumSimulations As Long
    Dim lDealName As String
    Dim lUSERM As Boolean
    Dim lCorrMatrix As String
    Dim lDeals As Variant
    Dim lDeal As Variant
    Dim lAnalysisDate As Date
    Dim lYC As YieldCurve
    Dim lCLO As CLODeal
    Dim lUseStatic As Boolean
    Dim lRndSeed As Long
    Dim lRMInputs As RMandCFInputs
    
    Call Setup(True)
    Call DeleteOutputTab("Deal CF-")
    lRMInputs = LoadRMandCFInputs()
    With lRMInputs
        lDealName = .DealName
        lNumSimulations = .NumOfSims
        lAnalysisDate = .AnalysisDate
        lCorrMatrix = .CorrMatrix
        lUseStatic = .StaticRndNum
        lRndSeed = .RandomizeSeed
        'lperiod = .RMFreq
        lUSERM = .RMCF
    End With
    
    
    If lUseStatic Then
        Rnd (-10)
        Randomize (lRndSeed)
    End If
    If lUSERM = True Then
        Call RunDealCFSimulation(lNumSimulations, lAnalysisDate, lDealName, lCorrMatrix)
    Else
        Set lYC = LoadYieldCurve(lAnalysisDate)
        Set lCLO = New CLODeal
        Call LoadCLOWaterfall(lDealName, lCLO)
        Call lCLO.LoadYieldCurve(lYC)
        Call LoadDates(lDealName, lCLO)
        Call LoadCLOAccounts(lDealName, lCLO)
        Call LoadLiabTrigs(lDealName, lCLO)
        Call LoadFees(lDealName, lCLO)
        Call LoadCLOInputs(lDealName, lCLO)
        Call LoadCFInputs(lDealName, lCLO)
        Call LoadDealCollat(lDealName)
        Call mDealCollatCLO.SetAnalysisDate(lAnalysisDate, lUSERM)
        Call lCLO.LoadCollateralPool(mDealCollatCLO)
        lCLO.Calc2
        lCLO.CalcRiskMeasures
        Call OutputCLOResults(lDealName, lCLO)
    End If
    
    Call Cleanup
    MsgBox "Deal Cashflows have finish running", vbOKOnly, "Finished"
End Sub
Private Sub RunDealCFSimulation(iNumSimulation As Long, ianalysisDate As Date, iDealName As String, iCorrMatrx As String)
    Dim i As Long
    Dim lCLO As CLODeal
    Dim lYC As YieldCurve
    Dim lSimOutput As Variant
    Dim lColumn As Long
    Dim lProgressbar As IProgressBar
    
    Set lProgressbar = New FProgressBarIFace
    
    If iCorrMatrx = "System Defined" Then
        Call CreditMigrationSetup(iNumSimulation, False, mAllCollateral)
    Else
        Call CreditMigrationSetup(iNumSimulation, False)
    End If
    mAllCollateral.SetAnalysisDate (ianalysisDate)

    lProgressbar.Min = 0
    lProgressbar.Max = iNumSimulation
    lProgressbar.Title = "BlackRock CLO Admin"
    
    
    ReDim lSimOutput(0 To iNumSimulation, 0 To 114)
    lSimOutput(0, 0) = "Simulation #"
    lColumn = lColumn + 1
    lSimOutput(0, lColumn) = "Deal Name"
    lColumn = lColumn + 1
    For i = 1 To 8
        lSimOutput(0, lColumn) = "Class Name"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Total Interest"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Total Principal"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Total Cashflow"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Inputed Price"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Inputed DM"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Yield Given Price"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "DM Given Price"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Price Given DM"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "WAL"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Mac Duration"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Mod Duration"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = ""
        lColumn = lColumn + 1
    Next i
    For i = 1 To 3
        lSimOutput(0, lColumn) = "Fee Name"
        lColumn = lColumn + 1
        lSimOutput(0, lColumn) = "Fee Paid"
        lColumn = lColumn + 1
        lColumn = lColumn + 1
    Next i
    lProgressbar.Show
    Set lYC = LoadYieldCurve(ianalysisDate)
    For i = 1 To iNumSimulation
        mAllCollateral.ReesetAssets
        lProgressbar.Text = "Running Simulation " & i & " of " & iNumSimulation & "."
        lProgressbar.Progress = i
        If lProgressbar.Cancel Then Exit For
        Call RunRatingHistory(ianalysisDate, mAllCollateral)
        Set lCLO = Nothing
        Set lCLO = New CLODeal
        
        Call lCLO.LoadYieldCurve(lYC)
        Call LoadCLOWaterfall(iDealName, lCLO)
        Call LoadDates(iDealName, lCLO)
        Call LoadCLOAccounts(iDealName, lCLO)
        Call LoadLiabTrigs(iDealName, lCLO)
        Call LoadFees(iDealName, lCLO)
        Call LoadCLOInputs(iDealName, lCLO)
        Call LoadCFInputs(iDealName, lCLO)
        Call LoadDealCollat(iDealName)
        Call mDealCollatCLO.SetUseRM(True)
        Call mDealCollatCLO.SetAnalysisDate(ianalysisDate, True)
        Call lCLO.LoadCollateralPool(mDealCollatCLO)
        lCLO.Calc2
        lCLO.CalcRiskMeasures
        If i <= 20 Then
            Call OutputCLOResults(iDealName & " Sim " & i, lCLO)
        End If
        Call UpdateDealCFSimOUtput(i, lCLO, lSimOutput)
    Next i
    lProgressbar.Hide
    If lProgressbar.Cancel = False Then
        Call OutputDataToSheet("Sim Stats", lSimOutput, True, "Deal CF-" & iDealName & "-")
    End If
    Call CreditMigrationCleanup
    Set lProgressbar = Nothing
End Sub


Private Sub LoadCLOAccounts(iDealName As String, iCLO As CLODeal)
    Dim lAllAccounts As Variant
    Dim lAccount As Accounts
    Dim lAccDict As Dictionary
    Dim i As Long
    lAllAccounts = Sheets(iDealName & " Inputs").Range("Accounts").Value
    Set lAccDict = New Dictionary
    For i = LBound(lAllAccounts, 1) To UBound(lAllAccounts, 1)
        Set lAccount = New Accounts
        lAccount.Add Interest, CDbl(lAllAccounts(i, 3))
        lAccount.Add Principal, CDbl(lAllAccounts(i, 4))
        lAccDict.Add CLng(lAllAccounts(i, 1)), lAccount
    Next i
    iCLO.LoadAccounts lAccDict
End Sub
Private Sub LoadCLOWaterfall(iDealName As String, iCLO As CLODeal)
    Dim lWaterfall As iWaterfall
    
    Select Case iDealName
    Case "Mag 12"
        Set lWaterfall = New Mag12Waterfall
    Case "Mag 14"
        Set lWaterfall = New MAG14Waterfall
    Case "Mag 11"
        Set lWaterfall = New Mag11Waterfall
    Case "Mag 9"
        Set lWaterfall = New Mag9Waterfall
    Case "Mag 7"
        Set lWaterfall = New Mag7Waterfall
    Case "Mag 8"
        Set lWaterfall = New Mag8Waterfall
    Case "Mag 6"
        Set lWaterfall = New Mag6Waterfall
    Case "Mag 15", "Mag 17"
        Set lWaterfall = New Mag15Waterfall
    Case "Mag 16"
        Set lWaterfall = New Mag16Waterfall
    End Select
    iCLO.LoadWaterfall lWaterfall
End Sub


Private Sub LoadDates(iDealName As String, iCLO As CLODeal)
    Dim lDealDate As Variant
    Dim lAnalsDate As Date
    Dim lDateUDT As DealDates
    
    lAnalsDate = Sheets(iDealName & " Inputs").Range("AnalysisDate").Value
    lDealDate = Sheets(iDealName & " Inputs").Range("DateInputs").Value
    With lDateUDT
        .AnalysisDate = lAnalsDate
        .PricingDate = lDealDate(1, 1)
        .ClosingDate = lDealDate(2, 1)
        .EffDate = lDealDate(3, 1)
        .FirstPayDate = lDealDate(4, 1)
        .NoCallDate = lDealDate(5, 1)
        .ReinvestDate = lDealDate(6, 1)
        .MatDate = lDealDate(7, 1)
        .PayDay = lDealDate(8, 1)
        .MonthsBetwPay = lDealDate(9, 1)
        .IntDeterDate = lDealDate(10, 1)
        .DeterDate = lDealDate(11, 1)
        .BussConv = lDealDate(12, 1)
    End With
    
    iCLO.LoadDealDates lDateUDT
    
    
End Sub
Private Sub LoadLiabTrigs(iDealName As String, iCLO As CLODeal)
    Dim lLiabInput As Variant
    Dim lLiability As Liability
    Dim lICTrig As ICTrigger
    Dim lOCTrig As OCTrigger
    
    Dim lICTrigDict As Dictionary
    Dim lOCTrigDict As Dictionary
    Dim lLiabDict As Dictionary
    Dim lPIkable As Boolean
    Dim lEquityTranche As Boolean
    Dim ldefbal As Double
    Dim lDefSpread As Double
    Dim i As Long
    
    lLiabInput = Sheets(iDealName & " Inputs").Range("Liability").Value

    Set lLiabDict = New Dictionary
    Set lICTrigDict = New Dictionary
    Set lOCTrigDict = New Dictionary
    
    For i = LBound(lLiabInput, 1) To UBound(lLiabInput, 2)
        Set lLiability = New Liability
        If lLiabInput(8, i) = 0 Then
            lPIkable = False
        Else
            lPIkable = True
        End If
        If lLiabInput(12, i) = False Then
            ldefbal = CDbl(lLiabInput(5, i))
            lDefSpread = CDbl(lLiabInput(6, i))
        End If
        
        lLiability.Setup CStr(lLiabInput(1, i)), CDbl(lLiabInput(2, i)), CDbl(lLiabInput(4, i)), ldefbal, lPIkable, lDefSpread, CStr(lLiabInput(13, i)), CDbl(lLiabInput(7, i)), GetDayCountEnum(CStr(lLiabInput(11, i))), CBool(lLiabInput(12, i)), CDbl(lLiabInput(3, i))
        lLiabDict.Add CStr(lLiabInput(1, i)), lLiability
        
        If lLiabInput(9, i) <> "NA" Then
            Set lOCTrig = New OCTrigger
            lOCTrig.Setup CStr(lLiabInput(1, i)) & " OC Test", CDbl(lLiabInput(9, i))
            lOCTrigDict.Add CStr(lLiabInput(1, i)) & " OC Test", lOCTrig
        End If
        If lLiabInput(10, i) <> "NA" Then
            Set lICTrig = New ICTrigger
            lICTrig.Setup CStr(lLiabInput(1, i)) & " IC Test", CDbl(lLiabInput(10, i))
            lICTrigDict.Add CStr(lLiabInput(1, i)) & " IC Test", lICTrig
        End If
    Next i
    
    
    'Interest Diversion Test
    lLiabInput = Sheets(iDealName & " Inputs").Range("CLOInputs").Value
    Set lOCTrig = New OCTrigger
    lOCTrig.Setup "Interest Diversion Test", CDbl(lLiabInput(1, 2))
    lOCTrigDict.Add "Interest Diversion Test", lOCTrig
    
    'Event of Default Trigger
    Set lOCTrig = New OCTrigger
    lOCTrig.Setup "Event Of Default Trigger", CDbl(lLiabInput(2, 2))
    lOCTrigDict.Add "Event of Default", lOCTrig
    
    iCLO.LoadLiabilities lLiabDict
    iCLO.LoadOCTriggers lOCTrigDict
    iCLO.LoadICTriggers lICTrigDict
    
End Sub
Private Sub LoadFees(iDealName As String, iCLO As CLODeal)
    Dim lFee As Fees
    Dim lFeeDict As Dictionary
    Dim lFeeinput As Variant

    Dim i As Long
    
    Set lFeeDict = New Dictionary
    lFeeinput = Sheets(iDealName & " Inputs").Range("Fees").Value
    
    For i = LBound(lFeeinput, 1) To UBound(lFeeinput, 1)
        Set lFee = New Fees
        lFee.Setup CStr(lFeeinput(i, 1)), CStr(lFeeinput(i, 2)), CDbl(lFeeinput(i, 6)), CDbl(lFeeinput(i, 4)), GetDayCountEnum(CStr(lFeeinput(i, 5))), CBool(lFeeinput(i, 7)), CDbl(lFeeinput(i, 8)), CDbl(lFeeinput(i, 3))
        lFeeDict.Add CStr(lFeeinput(i, 1)), lFee
    Next i
    iCLO.LoadFees lFeeDict
    

    
    
End Sub
Private Function LoadFilter(Optional iFilterType As String) As String
    Dim lVar As Variant
    Dim i As Long
    Dim j As Long
    Dim lFilter As String
    If UCase(iFilterType) = "SALE" Then
        lVar = Range("SaleFilter").Value
    Else
        lVar = Range("Filter").Value
    End If
    For i = 1 To UBound(lVar, 1)
        For j = 1 To UBound(lVar, 2)
            If j = 1 Then
                If Len(Trim(lVar(i, j))) > 0 Then
                    lFilter = lFilter & " " & Trim(lVar(i, j)) & " "
                End If
            Else
                lFilter = lFilter & Trim(lVar(i, j))
            End If
        Next j
    Next i
    'Debug.Print lFilter
    LoadFilter = lFilter
End Function
Private Function FilterFields(iFilter As String, Optional iFieldDict As Dictionary) As String()
    Dim lVar As Variant
    Dim i As Long
    Dim lString() As String
    Dim lCounter As Long
    
    lVar = Range("FilterFields").Value
    ReDim lString(UBound(lVar, 1) - 1)
    If iFieldDict Is Nothing Then Set iFieldDict = New Dictionary
    
    For i = 1 To UBound(lVar, 1) - 1
        If InStr(1, iFilter, lVar(i, 1)) > 0 And iFieldDict.Exists(lVar(i, 1)) = False Then
            lString(lCounter) = UCase(lVar(i, 1))
            lCounter = lCounter + 1
        End If
    Next i
    If lCounter = 0 Then
        ReDim Preserve lString(0)
    Else
        ReDim Preserve lString(lCounter - 1)
    End If
    FilterFields = lString
End Function

Private Sub LoadCLOInputs(iDealName As String, iCLO As CLODeal)
    Dim lCLOInputDict As Dictionary
    Dim lIncenive As IncentiveFee
    Dim lCLoInputVar As Variant
    Dim lFeeinput As Variant
    Dim lInceHurdle As Double
    Dim lInceRate As Double
    Dim lSubNote As Dictionary
    Dim i As Long
    
    Set lCLOInputDict = New Dictionary
    lCLoInputVar = Sheets(iDealName & " Inputs").Range("CLOInputs").Value
    For i = LBound(lCLoInputVar, 1) To UBound(lCLoInputVar, 1)
         lCLOInputDict.Add Trim(lCLoInputVar(i, 1)), lCLoInputVar(i, 2)
    Next i
    iCLO.LoadCLOInputs lCLOInputDict
    

    Set lIncenive = New IncentiveFee
    Set lSubNote = New Dictionary
    lInceHurdle = lCLOInputDict("Incentive Management Fee Hurdle")
    lInceRate = lCLOInputDict("Incentive Management Fee")
    lFeeinput = Sheets(iDealName & " Inputs").Range("PaySubNotes").Value 'Payment to subordinate not holders
    For i = LBound(lFeeinput, 1) To UBound(lFeeinput, 1)
        If lFeeinput(i, 2) <> 0 Then
            lSubNote.Add CLng(CDate(lFeeinput(i, 1))), CDbl(lFeeinput(i, 2))
        End If
    Next i
    lIncenive.Setup lInceHurdle, lInceRate, lSubNote
    iCLO.LoadIncentiveFee lIncenive
    
End Sub

Private Sub LoadCFInputs(iDealName As String, iCLO As CLODeal)
    Dim lCFInputDict As Dictionary
    Dim lCFInputVar As Variant
    Dim lReInvestinfo As ReinvestInfo
    Dim i As Long
    
    Set lCFInputDict = New Dictionary
    lCFInputVar = Sheets(iDealName & " Inputs").Range("CFInputs").Value
    For i = LBound(lCFInputVar, 1) To UBound(lCFInputVar, 1)
         lCFInputDict.Add lCFInputVar(i, 1), lCFInputVar(i, 2)
    Next i

    With lReInvestinfo
        .AmType = lCFInputDict("Reinvestment Amortization Type")
        .Default = lCFInputDict("Reinvestment CDR")
        .Floor = lCFInputDict("Reinvestment Floor")
        .Lag = lCFInputDict("Reinvestment Lag")
        .Maturity = lCFInputDict("Reinvestment Maturity")
        .PostReinvestPct = lCFInputDict("Post Reinvestment%")
        .PostReinvType = lCFInputDict("Post Reinvestment")
        .Prepayment = lCFInputDict("Reinvestment CPR")
        .PreReinvType = lCFInputDict("Pre Reinvestment Type")
        .PreRinvestPct = lCFInputDict("Pre Reinvestment %")
        .ReinvestPrice = lCFInputDict("Reinvestment Price")
        .Severity = lCFInputDict("Reinverstment Severity")
        .Spread = lCFInputDict("Reinvestment Spread")
    End With

    iCLO.LoadReinvestInfo lReInvestinfo
    iCLO.LoadCFInputs lCFInputDict
End Sub

Private Sub OutputCLOResults(iDealName As String, iCLO As CLODeal, Optional ByVal iSimNum As Long)
    Dim lDict As Dictionary
    Dim lKey As Variant
    Dim lOutput As Variant
    Set lDict = iCLO.GetLiabDict
    
    If iSimNum = 0 Then
        iSimNum = 1
    End If
    'Deal outputs
    lOutput = iCLO.DealOutputs
    Call OutputDataToSheet("Deal Info" & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    
    'Original Collateral
    lOutput = iCLO.OutputsOrigCollat
    Call OutputDataToSheet("Original Collateral Pool" & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    'Reinvestment collaterlal
    
    lOutput = iCLO.OutputsReinvetCollat
    Call OutputDataToSheet("Reinvest Collateral Pool" & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    
    'Liabilities
    Set lDict = iCLO.GetLiabDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Liabilities" & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'Fees
    Set lDict = iCLO.GetFeeDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'Incentive Fee
    lOutput = iCLO.OutputIncentiveFee
    Call OutputDataToSheet("Incentive Fee" & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    
    'ic tRIGGERS
    Set lDict = iCLO.GetICTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'OC Trigger
    Set lDict = iCLO.GetOCTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Sim #" & iSimNum, lOutput, False, "Deal CF-" & iDealName & "-")
    Next

End Sub
Private Sub OutputCLOResults2(iDealName As String, iCLO As CLODeal, iSimulation As Long)
    Dim lDict As Dictionary
    Dim lKey As Variant
    Dim lOutput As Variant
    Set lDict = iCLO.GetLiabDict
    

    
    'Deal outputs
    lOutput = iCLO.DealOutputs
    Call OutputDataToSheet("Deal Info", lOutput, False, "Deal CF-" & iDealName & "-")
    
    'Original Collateral
    lOutput = iCLO.OutputsOrigCollat
    Call OutputDataToSheet("Original Collateral Pool", lOutput, False, "Deal CF-" & iDealName & "-")
    'Reinvestment collaterlal
    
    lOutput = iCLO.OutputsReinvetCollat
    Call OutputDataToSheet("Reinvest Collateral Pool", lOutput, False, "Deal CF-" & iDealName & "-")
    
    'Liabilities
    Set lDict = iCLO.GetLiabDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Liabilities", lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'Fees
    Set lDict = iCLO.GetFeeDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'Incentive Fee
    lOutput = iCLO.OutputIncentiveFee
    Call OutputDataToSheet("Incentive Fee", lOutput, False, "Deal CF-" & iDealName & "-")
    
    'ic tRIGGERS
    Set lDict = iCLO.GetICTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, False, "Deal CF-" & iDealName & "-")
    Next
    
    'OC Trigger
    Set lDict = iCLO.GetOCTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, False, "Deal CF-" & iDealName & "-")
    Next

End Sub

Private Sub UpdateDealCFSimOUtput(iSim As Long, iCLO As CLODeal, ioSimOutPut As Variant, Optional iRow As Long)
    'This assumes that ioSimOutPUt has already been dimmention properly. Will add liability risk meaures and fee output
    Dim lColumn As Long
    Dim lDict As Dictionary
    Dim lKey As Variant
    Dim lSIM As Long
    If iRow = 0 Then
        lSIM = iSim
    Else
        lSIM = iRow
    End If
    
    ioSimOutPut(lSIM, lColumn) = iSim
    lColumn = lColumn + 1
    ioSimOutPut(lSIM, lColumn) = iCLO.DealName
    lColumn = lColumn + 1
    Set lDict = iCLO.GetLiabDict
    For Each lKey In lDict.Keys
        
        If lDict(lKey).IsEquity Then
            lColumn = 93
        End If
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).Name
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).TotalInterest
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).TotalPrincipal
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).TotalPrincipal + lDict(lKey).TotalInterest
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).InputPrice, "0.000%")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).InputDM, "0.000%")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).CalcYield, "0.000%")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).CalcDM, "0.000%")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).CalcPrice, "0.000%")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).CalcWAL, "###,##0.00")
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).CalcMac
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = lDict(lKey).CalcMod
        lColumn = lColumn + 1
        ioSimOutPut(lSIM, lColumn) = ""
        lColumn = lColumn + 1
    Next
    lColumn = 106
    Set lDict = iCLO.GetFeeDict
    For Each lKey In lDict.Keys
        If lDict(lKey).Name = "Base Manager Fee" Or lDict(lKey).Name = "Junior Manager Fee" Then
            ioSimOutPut(lSIM, lColumn) = lDict(lKey).Name
            lColumn = lColumn + 1
            ioSimOutPut(lSIM, lColumn) = Format(lDict(lKey).FeePaid, "###,##0.00")
            lColumn = lColumn + 1
            lColumn = lColumn + 1
        End If
    Next
    ioSimOutPut(lSIM, lColumn) = "Incentive Fee"
    lColumn = lColumn + 1
    ioSimOutPut(lSIM, lColumn) = iCLO.GetIcentiveFee.FeePaid
    lColumn = lColumn + 1
    
End Sub


Public Sub SetCancel()
    Dim lResult As VbMsgBoxResult
    
    lResult = MsgBox("Would you like to cancel current simulation", vbYesNo, "Cancel")
    If lResult = vbYes Then
        mCancelFlag = True
    End If
    
End Sub
Public Function LoadDealNames() As String()
    Dim lVariant As Variant
    Dim lOutSTR() As String
    Dim i As Long
    lVariant = Range("Deals").Value
    ReDim lOutSTR(UBound(lVariant, 1) - 2)
    For i = 0 To UBound(lOutSTR)
        lOutSTR(i) = lVariant(i + 2, 1)
    Next i
    LoadDealNames = lOutSTR
End Function
Public Function GetLastMaturityAllDeals(iDealNames() As String) As Date
    Dim loutDate As Date
    Dim i As Long
    For i = 0 To UBound(iDealNames)
        Set mDealCollat = New CollateralPool
        Set mDealCollatCLO = New CollateralPoolForCLO
        Call LoadDealCollat(iDealNames(i))
        If mDealCollat.LastMaturityDate > loutDate Then
            loutDate = mDealCollat.LastMaturityDate
        End If
    Next i
    Set mDealCollat = New CollateralPool
    Set mDealCollatCLO = New CollateralPoolForCLO
    GetLastMaturityAllDeals = loutDate
End Function

Public Sub RunDealCashflowAll()
    Dim lDealName As String
    Dim lNumSimulation As Long
    Dim lAnalysisDate As Date
    Dim lCorrMatrix As String
    Dim lUseStatic As Boolean
    Dim lRndSeed As Long
    Dim lDeals() As String
    Dim lLastMat As Date
    Dim lperiod As String
    Dim lYC As YieldCurve
    Dim lCLO As CLODeal
    Dim lSimOutput As Variant
    Dim lSimlong As Long
    Dim i As Long
    Dim j As Long
    Dim lRow As Long
    Dim lRMInputs As RMandCFInputs
    
    
    
    Call Setup(True)
    Call DeleteOutputTab("RM-")
    Call DeleteOutputTab("Deal CF-")

    lRMInputs = LoadRMandCFInputs()
    With lRMInputs
        lDealName = .DealName
        lNumSimulation = .NumOfSims
        lAnalysisDate = .AnalysisDate
        lCorrMatrix = .CorrMatrix
        lUseStatic = .StaticRndNum
        lRndSeed = .RandomizeSeed
        lperiod = .RMFreq
    End With
    
    
    
    'GetDealArrString
    lDeals = LoadDealNames
    
    'temporaty remval of Mag 17
    'Waterfall model isn't ready
    If lDeals(UBound(lDeals)) = "Mag 17" Then
        ReDim Preserve lDeals(UBound(lDeals) - 1)
    End If
    
    
    
    
    'GetLastMaturityDate as date
    lLastMat = GetLastMaturityAllDeals(lDeals)
    
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Creating Cholskey Decomposition"
    
    If lUseStatic Then
        Rnd (-10)
        Randomize (lRndSeed)
    End If
    If lCorrMatrix = "System Defined" Then
        Call CreditMigrationSetup(lNumSimulation, False, mAllCollateral, lperiod)
    Else
        Call CreditMigrationSetup(lNumSimulation, False, , lperiod)
    End If
    
    Call CMAllSetup(lDeals, lNumSimulation, lAnalysisDate, lLastMat, lperiod)
    Set lYC = LoadYieldCurve(lAnalysisDate)
    Call SetupCFSimOutput(lSimOutput, UBound(lDeals) + 1, lNumSimulation)
    mProgressBar.Min = 0
    mProgressBar.Max = lNumSimulation * (UBound(lDeals) + 1)
    mProgressBar.Progress = 0
    mProgressBar.ShowCancelButton
    mProgressBar.Show
    For i = 1 To lNumSimulation
        If mProgressBar.Cancel Then Exit For
        mAllCollateral.ReesetAssets
        Call RunRatingHistory(lAnalysisDate, mAllCollateral)
        For j = 0 To UBound(lDeals)
            If mProgressBar.Cancel Then Exit For
            mProgressBar.Text = "Run Sim " & i & " of " & lNumSimulation & "." & "For " & lDeals(j) & "."
            mProgressBar.Progress = mProgressBar.Progress + 1
            
            
            Call LoadDeal(lCLO, lDeals(j), lAnalysisDate, True)
            Call lCLO.LoadYieldCurve(lYC)
            lCLO.Calc2
            lCLO.CalcRiskMeasures
            If i <= 40 Then
                Call OutputCLOResults(lDeals(j), lCLO, i)
            End If
            lRow = lRow + 1
            Call UpdateDealCFSimOUtput(i, lCLO, lSimOutput, lRow)
            
            
            
           Call CMAllAddDeal(lDeals(j), mDealCollat, i)
           
        Next j
    Next i
    If mProgressBar.Cancel = False Then
        Call OutputDataToSheet("Sim Stats", lSimOutput, True, "Deal CF-" & "ALL" & "-")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("AVERAGE", "CDR"), False, "RM-Averages-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("AVERAGE", "NUMPERDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("AVERAGE", "BALPERDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of Performing", GetSimStatTimeSeries("AVERAGE", "BALPERF"), False, "RM-Averages-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("AVERAGE", "BALCCC"), False, "RM-Averages-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("AVERAGE", "BALDEF"), False, "RM-Averages-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("AVERAGE", "BALMAT"), False, "RM-Averages-")
        
        lSimlong = GetSimNum("Max")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MAX", "CDR"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MAX", "NUMPERDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MAX", "BALPERDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MAX", "BALPERF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MAX", "BALCCC"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MAX", "BALDEF"), False, "RM-MAX-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MAX", "BALMAT"), False, "RM-MAX-" & lSimlong & "-")
        
        lSimlong = GetSimNum("MIN")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MIN", "CDR"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MIN", "NUMPERDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MIN", "BALPERDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MIN", "BALPERF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MIN", "BALPERF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MIN", "BALDEF"), False, "RM-MIN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MIN", "BALMAT"), False, "RM-MIN-" & lSimlong & "-")
        
        lSimlong = GetSimNum("MEDIAN")
        Call OutputDataToSheet("Period CDR", GetSimStatTimeSeries("MEDIAN", "CDR"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Number of Defaults in Period", GetSimStatTimeSeries("MEDIAN", "NUMPERDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Defaults in Period", GetSimStatTimeSeries("MEDIAN", "BALPERDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of Performance", GetSimStatTimeSeries("MEDIAN", "BALPERF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Balance of CCC", GetSimStatTimeSeries("MEDIAN", "BALCCC"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Defaults", GetSimStatTimeSeries("MEDIAN", "BALDEF"), False, "RM-MEDIAN-" & lSimlong & "-")
        Call OutputDataToSheet("Cumulative Balance of Matures", GetSimStatTimeSeries("MEDIAN", "BALMAT"), False, "RM-MEDIAN-" & lSimlong & "-")
    End If
    Call CreditMigrationCleanup
    mProgressBar.Hide
    Call Cleanup
    'Call GetAverages
    'Sheets("CM-Output").Activate
    MsgBox "Rating Migration is Finished", vbOKOnly, "Finished"
    Call Cleanup
End Sub
Private Sub LoadDeal(iCLO As CLODeal, iDealName As String, ianalysisDate As Date, iUseRM As Boolean)
    
    Set iCLO = Nothing
    Set iCLO = New CLODeal

    Call LoadCLOWaterfall(iDealName, iCLO)
    Call LoadDates(iDealName, iCLO)
    Call LoadCLOAccounts(iDealName, iCLO)
    Call LoadLiabTrigs(iDealName, iCLO)
    Call LoadFees(iDealName, iCLO)
    Call LoadCLOInputs(iDealName, iCLO)
    Call LoadCFInputs(iDealName, iCLO)
    Call LoadDealCollatNonCopy(iDealName)
    Call mDealCollatCLO.SetAnalysisDate(ianalysisDate, iUseRM)
    Call iCLO.LoadCollateralPool(mDealCollatCLO)
End Sub
Public Sub SetupCFSimOutput(iSimOutput As Variant, iNumDeal As Long, iNumSims As Long)
    Dim lColumn As Long
    Dim i As Long
    ReDim iSimOutput(0 To iNumDeal * iNumSims, 0 To 114)
    iSimOutput(0, 0) = "Simulation #"
    lColumn = lColumn + 1
    iSimOutput(0, lColumn) = "Deal Name"
    lColumn = lColumn + 1
    For i = 1 To 8
        iSimOutput(0, lColumn) = "Class Name"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Total Interest"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Total Principal"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Total Cashflow"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Inputed Price"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Inputed DM"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Yield Given Price"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "DM Given Price"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Price Given DM"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "WAL"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Mac Duration"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Mod Duration"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = ""
        lColumn = lColumn + 1
    Next i
    For i = 1 To 3
        iSimOutput(0, lColumn) = "Fee Name"
        lColumn = lColumn + 1
        iSimOutput(0, lColumn) = "Fee Paid"
        lColumn = lColumn + 1
        lColumn = lColumn + 1
    Next i
End Sub
Private Sub CalcRebalancing2()
    Dim lType As String
    Dim lNumAssets As Long
    Dim lIncLoanSize As Double
    Dim lParIncrease As Boolean
    Dim lOptDict As Dictionary
    Dim lOptInput() As HypoInputs
    Dim lOptInputVar As Variant
    Dim i As Long
    Dim lBeforeOBJ As Double
    Dim lCurrOBJ As Double
    Dim lSaleAssetsDict As Dictionary
    Dim lPurchAssetsDict As Dictionary
    Dim lObjDict As Dictionary
    Dim lkeys As Variant
    Dim lAsset As Asset
    Dim lLastBuyorSale As String
    Dim lCurrentBuyorSale As String
    Dim lIterator As Long
    Dim lMaxIterations As Long
    Dim lOptType As String
    Dim lBuyFilter As String
    Dim lSaleFilter As String
    Dim lBuyAmount As Double
    Dim lSaleAmount As Double
    Dim lBefore() As Results
    Dim lAfterSale As Variant
    Dim lAfterBuy() As Results
    Dim lTempParSize As Double
    Dim lTempNumAssets As Long
    Dim lRanR As RankandRebalInputs
    Dim lDoNotPurchase As Dictionary
    
    Set lDoNotPurchase = New Dictionary
    Set lPurchAssetsDict = New Dictionary
    Set lSaleAssetsDict = New Dictionary
    Set lObjDict = New Dictionary
    
    Dim lRandR As RankandRebalInputs
    lRandR = LoadRebalandRankInfo()
    With lRandR
        lParIncrease = .InclDealLoans
        lIncLoanSize = .IncPar
        lSaleAmount = .SalePar
        lBuyAmount = .BuyPar
        lSaleFilter = lRandR.SaleFilter
        lBuyFilter = lRandR.BuyFilter
    End With
    

    lCurrOBJ = mDealCollat.GetObjectiveValue
    lBefore = mDealCollat.GetTestResult
    lBeforeOBJ = lCurrOBJ
  
    'Check Sale Amount
    Dim lFilterParAmount As Double
    lFilterParAmount = mDealCollat.GetCollatParAmount(lSaleFilter)
    If lSaleAmount > lFilterParAmount Then
        MsgBox "Unable to sale " & Format(lSaleAmount, "$0,000") & " of par. Only " & Format(lFilterParAmount, "$0,000") & " available."
        lSaleAmount = lFilterParAmount
    End If
    lFilterParAmount = 0
    lTempParSize = lIncLoanSize
    lTempNumAssets = 50
    
    
    mProgressBar.Max = lSaleAmount
    mProgressBar.Text = "Running Rebalancing Sale"
    mProgressBar.Show
    mProgressBar.ShowCancelButton
    
    Do While lFilterParAmount < lSaleAmount
        mProgressBar.Progress = lFilterParAmount
        If mProgressBar.Cancel Then Exit Do
        lCurrentBuyorSale = "SALE"
        If lTempParSize > lSaleAmount - lFilterParAmount Then
            lTempParSize = (lSaleAmount - lFilterParAmount)
        End If
        Call ReturnRankings2(lCurrentBuyorSale, lParIncrease, lTempNumAssets, lTempParSize, lOptDict, lOptInput, lSaleFilter)
        If lOptDict.Count = 0 Then
            'Debug.Assert 1 <> 1
            If mDealCollat.NumOfAssets(lSaleFilter) = 0 Then
                MsgBox "The model was unable to sale a par amount of " & lSaleAmount, vbOKOnly
                Exit Do
            End If
        ElseIf mProgressBar.Cancel = True Then
            Exit Do
        Else
            lkeys = lOptDict.Keys
            'If lOptDict(lKeys(0)) > lCurrOBJ Then
                For i = LBound(lOptInput) To UBound(lOptInput)
                    If lkeys(0) = lOptInput(i).Asset.BLKRockID Then
                        Set lAsset = lOptInput(i).Asset.Copy
      
                        mDealCollat.SaleAsset lAsset
                        If lSaleAssetsDict.Exists(lkeys(0)) Then
                           lSaleAssetsDict(lkeys(0)).AddPar lAsset.ParAmount
                        Else
                            lSaleAssetsDict.Add lkeys(0), lAsset
                        End If
                        lFilterParAmount = lFilterParAmount + lAsset.ParAmount
                        
                        lCurrOBJ = mDealCollat.GetObjectiveValue
                        'mDealCollat.CalcConcentrationTest.UpdatePreviousValues
                        
                        'lObjDict.Add lCurrOBJ, lAsset.Copy
                        
                        Exit For
                    End If
                Next i
            'End If
        End If
    Loop
    'Now Buy
    lFilterParAmount = 0
    lTempParSize = lIncLoanSize
    lTempNumAssets = lNumAssets
    mProgressBar.Text = "Running Rebalancing Buy"
    mProgressBar.Max = lBuyAmount
    lAfterSale = mDealCollat.GetTestResultsOutput
    Do While lFilterParAmount < lBuyAmount And mDealCollat.CheckAccountBalance(Collection, Principal) > 0
        mProgressBar.Progress = lFilterParAmount
        If mProgressBar.Cancel Then Exit Do
        lCurrentBuyorSale = "BUY"
        Call ReturnRankings2(lCurrentBuyorSale, lParIncrease, lTempNumAssets, lTempParSize, lOptDict, lOptInput, lBuyFilter)

        If lOptDict.Count = 0 Then
            'exit do No assets meet filter criteria.
            Exit Do
        ElseIf mProgressBar.Cancel = True Then
            Exit Do
        Else
            lkeys = lOptDict.Keys
            For i = LBound(lkeys) To UBound(lkeys)
                Set lAsset = mAllCollateral.GetAsset(CStr(lkeys(i)))
                'Debug.Assert lkeys(i) <> "BRSJL0SB1"
'                If lTempParSize > mDealCollat.CheckAccountBalance(Collection, Principal) Then
'                    lAsset.UpdatePar (mDealCollat.CheckAccountBalance(Collection, Principal))
'                Else
'                    lAsset.UpdatePar (lTempParSize)
'                End If
                
                If Not (lDoNotPurchase.Exists(lkeys(i))) Then
                'If Not (lPurchAssetsDict.Exists(lkeys(i))) Then
                'If True Then
                    mDealCollat.PurchaseAsset lAsset
                    lCurrOBJ = mDealCollat.GetObjectiveValue 'Don't want to add more then 2% of value
                    If lPurchAssetsDict.Exists(lkeys(i)) Then
                        If (lPurchAssetsDict(lkeys(i)).ParAmount + lAsset.ParAmount) / lBuyAmount > 0.05 Then
                            lCurrOBJ = 0
                            lDoNotPurchase.Add lkeys(i), 1
                         End If
                    End If
                    'Debug.Assert lCurrOBJ > 0
                    If lCurrOBJ > 0 Then
                        If lPurchAssetsDict.Exists(lkeys(i)) Then
                           lPurchAssetsDict(lkeys(i)).AddPar lAsset.ParAmount
                        Else
                            lPurchAssetsDict.Add lkeys(i), lAsset
                        End If
                        lFilterParAmount = lFilterParAmount + lAsset.ParAmount
                        'lObjDict.Add lCurrOBJ, lAsset.Copy
                        Exit For
                    Else
                        mDealCollat.SaleAsset lAsset
                        'lDoNotPurchase.Add lkeys(i), 1
                        If i = UBound(lkeys) Then
                            Exit Do
                        End If
                    End If
                End If
            Next i
            If i > UBound(lkeys) Then
                'Portfolio rebalance has ran out of unique assets.
                Exit Do
            End If
        End If
    Loop
    
    
    mProgressBar.Hide
    lAfterBuy = mDealCollat.GetTestResult
    Dim lOutput As Variant
    ReDim lOutput(0 To UBound(lAfterBuy) + 2, 0 To 10)
    lOutput(0, 1) = "Test Num"
    lOutput(0, 2) = "Test Name"
    lOutput(0, 3) = "Threshold"
    lOutput(0, 4) = "Before Results"
    lOutput(0, 5) = "Before Pass/Fail"
    lOutput(0, 7) = "After Results"
    lOutput(0, 8) = "After Pass/Fail"
    lOutput(0, 10) = "Differences"
    For i = 0 To UBound(lAfterBuy)
        lOutput(i + 1, 1) = lBefore(i).TestNumber
        lOutput(i + 1, 2) = lBefore(i).TestName
        lOutput(i + 1, 8) = lAfterBuy(i).PassFail
        lOutput(i + 1, 5) = lBefore(i).PassFail
        lOutput(i + 1, 3) = lBefore(i).Threshold
        lOutput(i + 1, 4) = lBefore(i).Result
        lOutput(i + 1, 7) = lAfterBuy(i).Result
        lOutput(i + 1, 10) = lOutput(i + 1, 7) - lOutput(i + 1, 4)
        Select Case lBefore(i).TestNumber
        
        Case 36, 37, 35, 40, 54
            lOutput(i + 1, 3) = Format(lOutput(i + 1, 3), "0.00")
            lOutput(i + 1, 4) = Format(lOutput(i + 1, 4), "0.00")
            lOutput(i + 1, 7) = Format(lOutput(i + 1, 7), "0.00")
            lOutput(i + 1, 10) = Format(lOutput(i + 1, 10), "0.00")
        Case Else
            lOutput(i + 1, 3) = Format(lOutput(i + 1, 3), "0.00%")
            lOutput(i + 1, 4) = Format(lOutput(i + 1, 4), "0.00%")
            lOutput(i + 1, 7) = Format(lOutput(i + 1, 7), "0.00%")
            lOutput(i + 1, 10) = Format(lOutput(i + 1, 10), "0.00%")
        End Select
        
    Next i
    lOutput(i + 1, 3) = "Ojective Function"
    lOutput(i + 1, 4) = lBeforeOBJ
    lOutput(i + 1, 7) = lCurrOBJ
    lOutput(i + 1, 10) = lOutput(i + 1, 7) - lOutput(i + 1, 4)
    Call OutputDataToSheet("Compliance Test", lOutput, False, "Rebalance-")
    Call OutputDataToSheet("Rebalance Trades' Attributes", GetRebalanceAttributes(lPurchAssetsDict, lSaleAssetsDict, lRandR.Libor), False, "Rebalance-")
    If lPurchAssetsDict.Count > 0 Then
        lOutput = GetAssetDataOutput(lPurchAssetsDict, lRandR.BuyFilter)
        Call OutputDataToSheet("Assets To Purchase", lOutput, False, "Rebalance-")
    End If
    
    If lSaleAssetsDict.Count > 0 Then
        lOutput = GetAssetDataOutput(lSaleAssetsDict, lRandR.SaleFilter)
        Call OutputDataToSheet("Assets To Sale", lOutput, False, "Rebalance-")
    End If

    
    
End Sub
Public Function GetAssetDataOutput(iAssetDict As Dictionary, iFilter As String) As Variant
    Dim lOutputVar As Variant
    Dim lAsset As Asset
    Dim lkeys As Variant
    Dim lFilterField() As String
    Dim lIsFilterFields As String
    Dim lIncFilter As Dictionary
    Dim lNumColumns As Long
    Dim i As Long
    Dim j As Long
    
    lIsFilterFields = Len(iFilter) > 0
    If lIsFilterFields Then
        Set lIncFilter = New Dictionary
        lIncFilter.Add "MARKET VALUE", 1
        lIncFilter.Add "Moody's Rating", 2
        lIncFilter.Add "S&P Rating", 3
        lIncFilter.Add "Coupon", 4
        lIncFilter.Add "WAS", 5
        lIncFilter.Add "LIBOR Floor", 6
        lIncFilter.Add "WAL", 7
        lIncFilter.Add "Moody's Recovery Rate", 8
        lIncFilter.Add "Analyst Opinion", 9
        lFilterField = FilterFields(iFilter, lIncFilter)
        If UBound(lFilterField) = 0 Then
            If Len(lFilterField(0)) > 0 Then
                lNumColumns = 12
            Else
                lIsFilterFields = False
                lNumColumns = 11
            End If
        Else
            lNumColumns = 11 + UBound(lFilterField) + 1
        End If
    Else
        lNumColumns = 11
    End If
    
    
    ReDim lOutputVar(0 To iAssetDict.Count, 0 To lNumColumns)
    lkeys = iAssetDict.Keys
    lOutputVar(0, 0) = "BlackRock ID"
    lOutputVar(0, 1) = "Issue Name"
    lOutputVar(0, 2) = "Par"
    lOutputVar(0, 3) = "Market Value"
    lOutputVar(0, 4) = "Moody's Rating"
    lOutputVar(0, 5) = "S&P's Rating"
    lOutputVar(0, 6) = "Coupon"
    lOutputVar(0, 7) = "WAS"
    lOutputVar(0, 8) = "LIBOR Floor"
    lOutputVar(0, 9) = "WAL"
    lOutputVar(0, 10) = "Moody's Recovery rate"
    lOutputVar(0, 11) = "Analyst Opinion"
    If lIsFilterFields Then
        For i = LBound(lFilterField) To UBound(lFilterField)
            lOutputVar(0, 12 + i) = lFilterField(i)
        Next i
    End If
    
    For i = 1 To iAssetDict.Count
        Set lAsset = iAssetDict(lkeys(i - 1))
        lOutputVar(i, 0) = lAsset.BLKRockID
        lOutputVar(i, 1) = lAsset.IssueName
        lOutputVar(i, 2) = lAsset.ParAmount
        lOutputVar(i, 3) = lAsset.MarketValue
        lOutputVar(i, 4) = lAsset.MDYRating
        lOutputVar(i, 5) = lAsset.SPRating
        lOutputVar(i, 6) = Format(lAsset.Coupon, "0.000%")
        lOutputVar(i, 7) = Format(lAsset.CpnSpread, "0.000%")
        lOutputVar(i, 8) = Format(lAsset.LiborFloor, "0.000%")
        lOutputVar(i, 9) = lAsset.WAL
        lOutputVar(i, 10) = Format(lAsset.MDYRecoveryRate, "0.000%")
        lOutputVar(i, 11) = lAsset.AnalystOpinion
        If lIsFilterFields Then
            For j = 0 To UBound(lFilterField)
                lOutputVar(i, 12 + j) = mAllCollateral.GetAssetParameter(lAsset.BLKRockID, lFilterField(j))
            Next j
        End If
    Next i
    GetAssetDataOutput = lOutputVar
End Function



Public Sub RunComplianceAll()
    On Error GoTo ErrorTrap
    Dim lDeals As Variant
    Dim i As Long
    Dim lDealName As String
    lDeals = Range("Deals").Value
    Call Setup
    For i = 2 To UBound(lDeals, 1)
        lDealName = lDeals(i, 1)
        Call LoadDealCollat(lDealName)
        Call LoadAccounts(lDealName)
        Call LoadTestInputs(lDealName)
        mDealCollat.CalcConcentrationTest
        Call UpdateOBJTestResults(lDealName)
    Next i
    Call Cleanup
Exit Sub
ErrorTrap:
    Call Cleanup
End Sub

Public Function GetHypoAttributes(iHypoAssets() As HypoInputs, Optional iLIBOR As Double) As Variant
    On Error GoTo ErrorTrap
    Dim lWASDen(1) As Double
    Dim lWASwFlDen(1) As Double
    Dim lWARFDen(1) As Double
    Dim lWALDen(1) As Double
    Dim lRecoveryDen(1) As Double
    Dim lMVDen(1) As Double
    Dim lPriceDen(1) As Double
    Dim lAsset As Asset
    Dim lParAmount(1) As Double
    Dim lBuyOrSale As Long '0 if buy 1 if sale
    Dim i As Long
    Dim lOut As Variant
    
    For i = LBound(iHypoAssets) To UBound(iHypoAssets)
        Set lAsset = iHypoAssets(i).Asset
        If iHypoAssets(i).Transaction = "Buy" Then
            lBuyOrSale = 0
        ElseIf iHypoAssets(i).Transaction = "Sale" Then
            lBuyOrSale = 1
        End If
        lWASDen(lBuyOrSale) = lWASDen(lBuyOrSale) + lAsset.CpnSpread * lAsset.ParAmount
        If lAsset.LiborFloor > iLIBOR Then
            lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.LiborFloor - iLIBOR + lAsset.CpnSpread) * lAsset.ParAmount
        Else
            lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.CpnSpread) * lAsset.ParAmount
        End If
        lWARFDen(lBuyOrSale) = lWARFDen(lBuyOrSale) + ConverRatingToFactor(lAsset.MDYDPRatingWARF) * lAsset.ParAmount
        lRecoveryDen(lBuyOrSale) = lRecoveryDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MDYRecoveryRate
        lMVDen(lBuyOrSale) = lMVDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MarketValue
        lPriceDen(lBuyOrSale) = lPriceDen(lBuyOrSale) + iHypoAssets(i).Price * lAsset.ParAmount
        lWALDen(lBuyOrSale) = lWALDen(lBuyOrSale) + lAsset.WAL * lAsset.ParAmount
        lParAmount(lBuyOrSale) = lParAmount(lBuyOrSale) + lAsset.ParAmount
    Next i
    ReDim lOut(0 To 8, 0 To 2)
    lOut(1, 0) = "Par Amount"
    lOut(2, 0) = "Weighted Average Spread"
    lOut(3, 0) = "Weighted Average Spread with LIBOR Floor"
    lOut(4, 0) = "Weighted Average Rating"
    lOut(5, 0) = "Weighted Average Life"
    lOut(6, 0) = "Weighted Average Recovery Rate"
    lOut(7, 0) = "Weighted Average Market Value"
    lOut(8, 0) = "Weighted Average Trade Price"
    lOut(0, 1) = "Purchases"
    lOut(0, 2) = "Sales"
    If lParAmount(0) > 0 Then
        lOut(1, 1) = Format(lParAmount(0), "$0,0000")
        lOut(2, 1) = Format(lWASDen(0) / lParAmount(0), "0.000%")
        lOut(3, 1) = Format(lWASwFlDen(0) / lParAmount(0), "0.000%")
        lOut(4, 1) = Format(lWARFDen(0) / lParAmount(0), "0,000.00")
        lOut(5, 1) = Format(lWALDen(0) / lParAmount(0), "0.00")
        lOut(6, 1) = Format(lRecoveryDen(0) / lParAmount(0), "0.000%")
        lOut(7, 1) = Format(lMVDen(0) / lParAmount(0) / 100, "0.000%")
        lOut(8, 1) = Format(lPriceDen(0) / lParAmount(0) / 100, "0.000%")
    Else
        lOut(1, 1) = "N/A"
        lOut(2, 1) = "N/A"
        lOut(3, 1) = "N/A"
        lOut(4, 1) = "N/A"
        lOut(5, 1) = "N/A"
        lOut(6, 1) = "N/A"
        lOut(7, 1) = "N/A"
        lOut(8, 1) = "N/A"
    End If
    If lParAmount(1) > 0 Then
        lOut(1, 2) = Format(lParAmount(1), "$0,0000")
        lOut(2, 2) = Format(lWASDen(1) / lParAmount(1), "0.000%")
        lOut(3, 2) = Format(lWASwFlDen(1) / lParAmount(1), "0.000%")
        lOut(4, 2) = Format(lWARFDen(1) / lParAmount(1), "0,000.00")
        lOut(5, 2) = Format(lWALDen(1) / lParAmount(1), "0.00")
        lOut(6, 2) = Format(lRecoveryDen(1) / lParAmount(1), "0.000%")
        lOut(7, 2) = Format(lMVDen(1) / lParAmount(1) / 100, "0.000%")
        lOut(8, 2) = Format(lPriceDen(1) / lParAmount(1) / 100, "0.000%")
    Else
        lOut(1, 2) = "N/A"
        lOut(2, 2) = "N/A"
        lOut(3, 2) = "N/A"
        lOut(4, 2) = "N/A"
        lOut(5, 2) = "N/A"
        lOut(6, 2) = "N/A"
        lOut(7, 2) = "N/A"
        lOut(8, 2) = "N/A"
    End If
    
    GetHypoAttributes = lOut
    
    

Exit Function
ErrorTrap:
End Function
Public Function GetRebalanceAttributes(iBuys As Dictionary, iSales As Dictionary, Optional iLIBOR As Double) As Variant
    On Error GoTo ErrorTrap
    Dim lWASDen(1) As Double
    Dim lWASwFlDen(1) As Double
    Dim lWARFDen(1) As Double
    Dim lWALDen(1) As Double
    Dim lRecoveryDen(1) As Double
    Dim lMVDen(1) As Double
    Dim lPriceDen(1) As Double
    Dim lAsset As Asset
    Dim lParAmount(1) As Double
    Dim lBuyOrSale As Long '0 if buy 1 if sale
    Dim i As Long
    Dim lOut As Variant
    Dim lBRSIDS As Variant

    If iBuys.Count > 0 Then
        lBRSIDS = iBuys.Keys
        For i = LBound(lBRSIDS) To UBound(lBRSIDS)
            Set lAsset = iBuys(lBRSIDS(i))
            lBuyOrSale = 0

            lWASDen(lBuyOrSale) = lWASDen(lBuyOrSale) + lAsset.CpnSpread * lAsset.ParAmount
            If lAsset.LiborFloor > iLIBOR Then
                lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.LiborFloor - iLIBOR + lAsset.CpnSpread) * lAsset.ParAmount
            Else
                lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.CpnSpread) * lAsset.ParAmount
            End If
            lWARFDen(lBuyOrSale) = lWARFDen(lBuyOrSale) + ConverRatingToFactor(lAsset.MDYDPRatingWARF) * lAsset.ParAmount
            lRecoveryDen(lBuyOrSale) = lRecoveryDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MDYRecoveryRate
            lMVDen(lBuyOrSale) = lMVDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MarketValue
            'lPriceDen(lBuyOrSale) = lPriceDen(lBuyOrSale) + iHypoAssets(i).Price * lAsset.ParAmount
            lWALDen(lBuyOrSale) = lWALDen(lBuyOrSale) + lAsset.WAL * lAsset.ParAmount
            lParAmount(lBuyOrSale) = lParAmount(lBuyOrSale) + lAsset.ParAmount
        Next i
    End If
    If iSales.Count > 0 Then
        lBRSIDS = iSales.Keys
        For i = LBound(lBRSIDS) To UBound(lBRSIDS)
            Set lAsset = iSales(lBRSIDS(i))
            lBuyOrSale = 1
            lWASDen(lBuyOrSale) = lWASDen(lBuyOrSale) + lAsset.CpnSpread * lAsset.ParAmount
            If lAsset.LiborFloor > iLIBOR Then
                lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.LiborFloor - iLIBOR + lAsset.CpnSpread) * lAsset.ParAmount
            Else
                lWASwFlDen(lBuyOrSale) = lWASwFlDen(lBuyOrSale) + (lAsset.CpnSpread) * lAsset.ParAmount
            End If
            lWARFDen(lBuyOrSale) = lWARFDen(lBuyOrSale) + ConverRatingToFactor(lAsset.MDYDPRatingWARF) * lAsset.ParAmount
            lRecoveryDen(lBuyOrSale) = lRecoveryDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MDYRecoveryRate
            lMVDen(lBuyOrSale) = lMVDen(lBuyOrSale) + lAsset.ParAmount * lAsset.MarketValue
            'lPriceDen(lBuyOrSale) = lPriceDen(lBuyOrSale) + iHypoAssets(i).Price * lAsset.ParAmount
            lWALDen(lBuyOrSale) = lWALDen(lBuyOrSale) + lAsset.WAL * lAsset.ParAmount
            lParAmount(lBuyOrSale) = lParAmount(lBuyOrSale) + lAsset.ParAmount
        Next i
    End If
    ReDim lOut(0 To 7, 0 To 2)
    lOut(1, 0) = "Par Amount"
    lOut(2, 0) = "Weighted Average Spread"
    lOut(3, 0) = "Weighted Average Spread with LIBOR Floor"
    lOut(4, 0) = "Weighted Average Rating"
    lOut(5, 0) = "Weighted Average Life"
    lOut(6, 0) = "Weighted Average Recovery Rate"
    lOut(7, 0) = "Weighted Average Market Value"
    lOut(0, 1) = "Purchases"
    lOut(0, 2) = "Sales"
    If lParAmount(0) > 0 Then
        lOut(1, 1) = Format(lParAmount(0), "$0,0000")
        lOut(2, 1) = Format(lWASDen(0) / lParAmount(0), "0.000%")
        lOut(3, 1) = Format(lWASwFlDen(0) / lParAmount(0), "0.000%")
        lOut(4, 1) = Format(lWARFDen(0) / lParAmount(0), "0,000.00")
        lOut(5, 1) = Format(lWALDen(0) / lParAmount(0), "0.00")
        lOut(6, 1) = Format(lRecoveryDen(0) / lParAmount(0), "0.000%")
        lOut(7, 1) = Format(lMVDen(0) / lParAmount(0) / 100, "0.000%")
    Else
        lOut(1, 1) = "N/A"
        lOut(2, 1) = "N/A"
        lOut(3, 1) = "N/A"
        lOut(4, 1) = "N/A"
        lOut(5, 1) = "N/A"
        lOut(6, 1) = "N/A"
        lOut(7, 1) = "N/A"
    End If
    If lParAmount(1) > 0 Then
        lOut(1, 2) = Format(lParAmount(1), "$0,0000")
        lOut(2, 2) = Format(lWASDen(1) / lParAmount(1), "0.000%")
        lOut(3, 2) = Format(lWASwFlDen(1) / lParAmount(1), "0.000%")
        lOut(4, 2) = Format(lWARFDen(1) / lParAmount(1), "0,000.00")
        lOut(5, 2) = Format(lWALDen(1) / lParAmount(1), "0.00")
        lOut(6, 2) = Format(lRecoveryDen(1) / lParAmount(1), "0.000%")
        lOut(7, 2) = Format(lMVDen(1) / lParAmount(1) / 100, "0.000%")
    Else
        lOut(1, 2) = "N/A"
        lOut(2, 2) = "N/A"
        lOut(3, 2) = "N/A"
        lOut(4, 2) = "N/A"
        lOut(5, 2) = "N/A"
        lOut(6, 2) = "N/A"
        lOut(7, 2) = "N/A"
    End If

    GetRebalanceAttributes = lOut



Exit Function
ErrorTrap:
End Function
