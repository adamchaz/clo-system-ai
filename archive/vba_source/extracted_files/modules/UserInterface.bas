Attribute VB_Name = "UserInterface"

Option Explicit
Option Private Module
Private mCLO As CLODeal
Private mProgressBar As IProgressBar
Private mAllCollateral As CollateralPool

Private Sub LoadYieldCurve()
    Dim lRates As Variant
    Dim lYC As YieldCurve
    Dim lDict As Dictionary
    Dim lAnalysisDate As Date
    Dim lItem As Double
    Dim i As Long

    lAnalysisDate = Range("AnalysisDate").Value
    lRates = Range("LIBORCurve").Value
    Set lDict = New Dictionary
    For i = LBound(lRates, 1) To UBound(lRates, 1)
        lDict.Add CLng(lRates(i, 1)), lRates(i, 2)
    Next i
    Set lYC = New YieldCurve
    lYC.Setup "LIBOR", lAnalysisDate, lDict
    mCLO.LoadYieldCurve lYC
    
End Sub
Public Function LoadDealCollateral(iDeal As String) As Dictionary
    Dim lDict As Dictionary
    Dim i As Long
    Dim linput As Variant
    
    linput = Sheets(iDeal & " Inputs").Range("DealCollateral").Value
    Set lDict = New Dictionary
    For i = LBound(linput, 1) To UBound(linput, 1)
        If lDict.Exists(Trim(linput(i, 1))) Then
            lDict(Trim(linput(i, 1))) = lDict(linput(i, 1)) + linput(i, 2)
        Else
            lDict.Add Trim(linput(i, 1)), linput(i, 2)
        End If
    Next i
    
    Set LoadDealCollateral = lDict
    
End Function


Private Sub LoadAccounts()
    Dim lAllAccounts As Variant
    Dim lAccount As Accounts
    Dim lAccDict As Dictionary
    Dim i As Long
    lAllAccounts = Range("Accounts").Value
    Set lAccDict = New Dictionary
    For i = LBound(lAllAccounts, 1) To UBound(lAllAccounts, 1)
        Set lAccount = New Accounts
        lAccount.Add Interest, CDbl(lAllAccounts(i, 3))
        lAccount.Add Principal, CDbl(lAllAccounts(i, 4))
        lAccDict.Add CLng(lAllAccounts(i, 1)), lAccount
    Next i
    mCLO.LoadAccounts lAccDict
End Sub
Private Sub LoadLiabTrigs()
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
    
    lLiabInput = Range("Liability").Value

    Set lLiabDict = New Dictionary
    Set lICTrigDict = New Dictionary
    Set lOCTrigDict = New Dictionary
    
    For i = LBound(lLiabInput, 1) To UBound(lLiabInput, 2)
        Set lLiability = New Liability
        If lLiabInput(11, i) = 0 Then
            lPIkable = False
        Else
            lPIkable = True
        End If
        If lLiabInput(22, i) = False Then
            ldefbal = CDbl(lLiabInput(5, i))
            lDefSpread = CDbl(lLiabInput(9, i))
        End If
        
        lLiability.Setup CStr(lLiabInput(1, i)), CDbl(lLiabInput(2, i)), CDbl(lLiabInput(4, i)), ldefbal, lPIkable, lDefSpread, CStr(lLiabInput(13, i)), CDbl(lLiabInput(10, i)), GetDayCountEnum(CStr(lLiabInput(21, i))), CBool(lLiabInput(22, i)), CDbl(lLiabInput(3, i))
        lLiabDict.Add CStr(lLiabInput(1, i)), lLiability
        
        If lLiabInput(13, i) <> "NA" Then
            Set lOCTrig = New OCTrigger
            lOCTrig.Setup CStr(lLiabInput(1, i)) & " OC Test", CDbl(lLiabInput(13, i))
            lOCTrigDict.Add CStr(lLiabInput(1, i)) & " OC Test", lOCTrig
        End If
        If lLiabInput(16, i) <> "NA" Then
            Set lICTrig = New ICTrigger
            lICTrig.Setup CStr(lLiabInput(1, i)) & " IC Test", CDbl(lLiabInput(16, i))
            lICTrigDict.Add CStr(lLiabInput(1, i)) & " IC Test", lICTrig
        End If
    Next i
    
    
    'Interest Diversion Test
    lLiabInput = Range("CLOInputs").Value
    Set lOCTrig = New OCTrigger
    lOCTrig.Setup "Interest Diversion Test", CDbl(lLiabInput(1, 1))
    lOCTrigDict.Add "Interest Diversion Test", lOCTrig
    
    'Event of Default Trigger
    Set lOCTrig = New OCTrigger
    lOCTrig.Setup "Event Of Default Trigger", CDbl(lLiabInput(2, 1))
    lOCTrigDict.Add "Event of Default", lOCTrig
    
    mCLO.LoadLiabilities lLiabDict
    mCLO.LoadOCTriggers lOCTrigDict
    mCLO.LoadICTriggers lICTrigDict
    
    
    
End Sub
Private Function LoadListofDeals(Optional iCollatDict As Dictionary) As Variant
    Dim lDeals As Variant
    Dim lCUSIPandName As Variant
    Dim lAddAsset As Boolean
    Dim i As Long
    ThisWorkbook.Activate
    Sheets("ALL Assets").Activate
    lCUSIPandName = Range(Range("A2:B2"), Range("A2:B2").End(xlDown)).Value
    Dim lNames As Dictionary
    Set lNames = New Dictionary
    
    For i = LBound(lCUSIPandName, 1) To UBound(lCUSIPandName, 1)
        If iCollatDict Is Nothing Then
            lAddAsset = True
        Else
            If iCollatDict.Exists(lCUSIPandName(i, 1)) Then
                lAddAsset = True
            Else
                lAddAsset = False
            End If
        End If
        If Len(lCUSIPandName(i, 1)) > 0 And lAddAsset Then
            lNames.Add lCUSIPandName(i, 1) & vbTab & lCUSIPandName(i, 2), i
        End If
    Next i
    
    Set UserForm1.mListofDeals = lNames
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


Private Sub Setup()
    Dim lsheet As Worksheet
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    ThisWorkbook.Activate
    Set mCLO = New CLODeal
    Set mAllCollateral = New CollateralPool
    Set mProgressBar = New FProgressBarIFace
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Loading Assets"
    Call LoadAllAssets
    mProgressBar.Hide
    
End Sub
Public Sub DeleteOutputTab(iPrefix As String)
    On Error Resume Next
    Dim lsheet As Worksheet
    Dim lObject As Object
    Application.DisplayAlerts = False
    For Each lObject In ThisWorkbook.Worksheets
        'Debug.Print lObject.Name
        If UCase(Left(lObject.Name, Len(iPrefix))) = UCase(iPrefix) Then
            lObject.Delete
        End If
    Next lObject
    Application.DisplayAlerts = True
End Sub
Public Sub RunCollatCFwRatings()
    Dim lAnalysisDate As Date
    Dim lDeals As Variant
    Dim lDeal As Variant
    Dim lAsset As Asset
    Dim lCF As SimpleCashflow
    Dim lCFColl As CashflowClass
    Dim lDealCollatDict As Dictionary
    
    Call Setup
    Call DeleteOutputTab("Collat-")
    Set lCFColl = New CashflowClass
    lAnalysisDate = "05/15/2015"
    Call CreditMigrationSetup(1, True)
    Set lDealCollatDict = LoadDealCollateral("MAG 12")
    
    Call RunRatingHistory(lAnalysisDate, mAllCollateral, lDealCollatDict)
    lDeals = LoadListofDeals(lDealCollatDict)
    For Each lDeal In lDeals
        Set lAsset = mAllCollateral.GetAsset(CStr(lDeal))
        lAsset.AddPar lDealCollatDict(lDeal)
        lAsset.CalcCF , , lAnalysisDate, 0, "Rating"
        
        Call OutputDataToSheet(lAsset.BLKRockID & "    " & lAsset.IssuerName, lAsset.CashflowOutput, False, "Collat-")

    Next
    
    Call CreditMigrationCleanup
    Call Cleanup
    
End Sub


Private Sub LoadAllAssets()
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
    lPoolInput = Range(Range("A2"), Range("A2").SpecialCells(xlLastCell)).Value
    lPrinSched = Range("Sink_Schedule").Value
    lAssumptions = Range("CFAssumptions").Value
    lAnalysisDate = Range("AnalysisDate").Value
    lNumPoolsAssets = UBound(lPoolInput, 1)  'Don't want to use a variable that can cause a potential error in an error trap.
    mAllCollateral.SetAnalysisDate lAnalysisDate
    
    For i = LBound(lPoolInput, 1) To UBound(lPoolInput, 1)
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
        
        lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
        Dim lamBalance As Double
        Dim lSchedDate As Date
        Dim lTotalBalance As Double
        
        ''GetSchedule
        Set lLoanSchedDict = New Dictionary
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
                lTotalBalance = lTotalBalance - lamBalance
            Next j
        End If
        lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
        If lSchedMatDate > lAssetUDT.Maturity Then
            lAssetUDT.Maturity = CheckBusinessDate(lSchedMatDate, lAssetUDT.BusinessDayConvention)
        End If
        
        If lLoanSchedDict.Count = 0 Then
            lLoanSchedDict.Add CLng(lAssetUDT.Maturity), 1
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



'Public Sub Start()
'    Dim lCF As SimpleCashflow
'    Dim lAnalysisDate As Date
'
'    Call Setup
'    Call DeleteOutputTab("CF-")
'
'    Call LoadDates
'    Call LoadAccounts
'    Call LoadLiabTrigs
'    Call LoadFees
'    If True Then
'        lAnalysisDate = Range("AnalysisDate").Value
'        Call CreditMigrationSetup(1, False)
'        Call RunRatingHistory(lAnalysisDate, mAllCollateral)
'
'    End If
'
'    Call LoadCollateralPool2
'    Call LoadCLOInputs
'    Call LoadReinvestInfo
'    Call LoadYieldCurve
'
'    mCLO.Calc
'    mCLO.CalcRiskMeasures
'    Call GetResults
'
'    Call Cleanup
'    MsgBox "Deal level cashflows have finished running", vbOKOnly, "Finished"
'
'End Sub
Public Sub CreditMigration()
    Dim lAnalysisDate As Date
    Dim lOutput As Variant
    Dim lNumSimulations As Long
    Dim lDealCollatDict As Dictionary
    Dim lVarinat As Variant
    Dim i As Long
    
    Call Setup
    Call DeleteOutputTab("CM-")

    lNumSimulations = 5

    lAnalysisDate = Range("Analysisdate").Value
    Set lDealCollatDict = LoadDealCollateral("MAG 12")
    mProgressBar.Show
    mProgressBar.Title = "BlackRock CLO Admin"
    mProgressBar.Text = "Creating Cholskey Decomposition"
    Call CreditMigrationSetup(lNumSimulations, False)

    mProgressBar.Min = 0
    mProgressBar.Max = lNumSimulations
    mProgressBar.Progress = 1
    mProgressBar.Show
    For i = 1 To lNumSimulations
        mProgressBar.Text = "Running Simulation " & i & " of " & lNumSimulations & "."
        mProgressBar.Progress = i
        mAllCollateral.ReesetAssets
        Call RunRatingHistory(lAnalysisDate, mAllCollateral, lDealCollatDict)
        lOutput = CreditMigrationOutput
        Call OutputDataToSheet("Credit Migration: Simulation " & i, lOutput, False, "CM-")
    Next i
    lOutput = SimulationResultOutput
    Call OutputDataToSheet("Credit Migration Stats", lOutput, True, "CM-")
    ActiveWindow.FreezePanes = False
    Call CreditMigrationCleanup
    mProgressBar.Hide
    Call Cleanup
    Sheets("CM-Output").Activate
    MsgBox "Credit Migration is Finished", vbOKOnly, "Finished"
End Sub


Private Sub LoadReinvestInfo()
    Dim lReInvestinfo As ReinvestInfo
    Dim linput As Variant
    Dim lAssumptions As Variant
    Dim j As LoadPictureConstants
    
    linput = Range("Reinvest").Value
    lAssumptions = Range("CFAssumptions").Value
    
    With lReInvestinfo
        .Spread = CDbl(linput(1, 1))
        .Floor = CDbl(linput(2, 1))
        .Maturity = CLng(linput(3, 1))
        .AmType = CStr(linput(4, 1))
        .ReinvestPrice = CDbl(linput(5, 1))
        .PreReinvType = CStr(linput(6, 1))
        .PostReinvType = CStr(linput(7, 1))
        .PreRinvestPct = CDbl(linput(8, 1))
        .PostReinvestPct = CDbl(linput(9, 1))
        For j = LBound(lAssumptions, 1) To UBound(lAssumptions, 1)
            If UCase(Trim(lAssumptions(j, 1))) = "REINVEST" Then
                If IsNumeric(lAssumptions(j, 2)) Then
                    .Prepayment = CDbl(lAssumptions(j, 2))
                Else
                    .Prepayment = GetCFVector(CStr(lAssumptions(j, 2)))
                End If
            
                If IsNumeric(lAssumptions(j, 3)) Then
                    .Default = CDbl(lAssumptions(j, 3))
                Else
                    .Default = GetCFVector(CStr(lAssumptions(j, 3)))
                End If
                If IsNumeric(lAssumptions(j, 4)) Then
                    .Severity = CDbl(lAssumptions(j, 4))
                Else
                    .Severity = GetCFVector(CStr(lAssumptions(j, 4)))
                End If
                .Lag = lAssumptions(j, 5)
            End If
        Next j
    End With
    mCLO.LoadReinvestInfo lReInvestinfo
End Sub
Private Sub LoadFees()
    Dim lFee As Fees
    Dim lIncenive As IncentiveFee
    Dim lFeeDict As Dictionary
    Dim lFeeinput As Variant
    Dim lInceHurdle As Double
    Dim lInceRate As Double
    Dim lSubNote As Dictionary
    Dim linput As Variant
    linput = Range("CLOINputs").Value
    Dim i As Long
    
    Set lFeeDict = New Dictionary
    lFeeinput = Range("Fees").Value
    
    For i = LBound(lFeeinput, 1) To UBound(lFeeinput, 1)
        Set lFee = New Fees
        lFee.Setup CStr(lFeeinput(i, 1)), CStr(lFeeinput(i, 2)), CDbl(lFeeinput(i, 6)), CDbl(lFeeinput(i, 4)), GetDayCountEnum(CStr(lFeeinput(i, 5))), CBool(lFeeinput(i, 7)), CDbl(lFeeinput(i, 8)), CDbl(lFeeinput(i, 3))
        lFeeDict.Add CStr(lFeeinput(i, 1)), lFee
    Next i
    mCLO.LoadFees lFeeDict
    
    Set lIncenive = New IncentiveFee
    Set lSubNote = New Dictionary
    lInceHurdle = linput(10, 1)
    lInceRate = linput(9, 1)
    lFeeinput = Range("PaySubNotes").Value
    For i = LBound(lFeeinput, 1) To UBound(lFeeinput, 1)
        If lFeeinput(i, 2) <> 0 Then
            lSubNote.Add CLng(CDate(lFeeinput(i, 1))), CDbl(lFeeinput(i, 2))
        End If
    Next i
    lIncenive.Setup lInceHurdle, lInceRate, lSubNote
    mCLO.LoadIncentiveFee lIncenive
    'mclo.
    
    
End Sub

Private Sub GetResults()
    Dim lDict As Dictionary
    Dim lKey As Variant
    Dim lOutput As Variant
    Set lDict = mCLO.GetLiabDict
    Dim lNewTab As Boolean
    
    If Range("Output_on_One_tabe").Value = False Then
        lNewTab = True
    End If
    
    'Deal outputs
    lOutput = mCLO.DealOutputs
    Call OutputDataToSheet("Deal Info", lOutput, lNewTab, "CF-")
    
    'Original Collateral
    lOutput = mCLO.OutputsOrigCollat
    Call OutputDataToSheet("Original Collateral Pool", lOutput, lNewTab, "CF-")
    'Reinvestment collaterlal
    
    lOutput = mCLO.OutputsReinvetCollat
    Call OutputDataToSheet("Reinvest Collateral Pool", lOutput, lNewTab, "CF-")
    
    'Liabilities
    Set lDict = mCLO.GetLiabDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name & " Liabilities", lOutput, lNewTab, "CF-")
    Next
    
    'Fees
    Set lDict = mCLO.GetFeeDict
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, lNewTab, "CF-")
    Next
    
    'Incentive Fee
    lOutput = mCLO.OutputIncentiveFee
    Call OutputDataToSheet("Incentive Fee", lOutput, lNewTab, "CF-")
    
    'ic tRIGGERS
    Set lDict = mCLO.GetICTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, lNewTab, "CF-")
    Next
    
    'OC Trigger
    Set lDict = mCLO.GetOCTriggers
    For Each lKey In lDict.Keys
        lOutput = lDict(lKey).Output
        Call OutputDataToSheet(lDict(lKey).Name, lOutput, lNewTab, "CF-")
    Next

End Sub
Public Sub OutputDataToSheet(iName As String, lOutput As Variant, iNewTab As Boolean, iPrefix As String)
    Static lColumn As Long
    Dim lRange As Range
    Dim lRowoffset As Long
    Dim lsheet As Worksheet
    Dim lTabName As String
    Dim lsheetfound As Boolean
    Dim lObject As Object
    Dim i As Long
    Dim j As Long
        
    Set lRange = Range("A1").Offset(0, lColumn)
    
    If iNewTab Then
        lTabName = iPrefix & iName
    Else
        lTabName = iPrefix & "Output"
    End If
    
    
    'Find Tab or create tab
    For Each lObject In ThisWorkbook.Sheets
        If TypeName(lObject) = "Worksheet" Then
        Set lsheet = lObject
         If UCase(lsheet.Name) = UCase(lTabName) Then
             lsheetfound = True
             Exit For
        End If
       End If
    Next lObject
    If lsheetfound = False Then
        Call ThisWorkbook.Sheets.Add(, Sheets(Sheets.Count), , "Worksheet")
        ActiveSheet.Name = lTabName
        ActiveSheet.Tab.Color = 5287936
        'Range("F3").Activate
        'ActiveWindow.FreezePanes = True
        lColumn = 1
    Else
        With ThisWorkbook.Sheets(lTabName)
            lColumn = .Cells.Find("*", After:=.Cells(1), _
                        LookIn:=xlFormulas, LookAt:=xlWhole, _
                        SearchDirection:=xlPrevious, _
                        SearchOrder:=xlByColumns).Column
        End With
        lColumn = lColumn + 1
    End If
    If iNewTab Then
        ThisWorkbook.Sheets(lTabName).Cells.Clear
        lRowoffset = 0
    Else
        lRowoffset = 1
    End If
    
    Set lRange = ThisWorkbook.Sheets(lTabName).Range("A1").Offset(lRowoffset, lColumn)
    
    Dim lRows As Long
    Dim lColumns As Long
    lRows = UBound(lOutput, 1) - LBound(lOutput, 1)
    lColumns = UBound(lOutput, 2) - LBound(lOutput, 2)
    
    Range(lRange, lRange.Offset(lRows, lColumns)).Value = lOutput
'    For i = 0 To lRows
'        For j = 0 To lColumns
'            lRange.Offset(i, j).Value = lOutput(i, j)
'        Next j
'    Next i
    
    For i = LBound(lOutput, 2) To UBound(lOutput, 2)
        Select Case VarType(lOutput(1, i))


        Case vbDouble
            'lrange.Offset(0, i).Columns.Style = "Comma"

            'lrange.Offset(0, 1).Columns
            'thisworkbook.Sheets(itabname).
            ThisWorkbook.Sheets(lTabName).Columns(lRange.Offset(1, i).Column).Style = "Comma"
        Case vbDate
        
        End Select
    Next i
    If iNewTab = False Then
        lColumn = lColumn + UBound(lOutput, 2) + 2
        lRange.Offset(-lRowoffset, 0).Value = iName
        Range(lRange.Offset(-lRowoffset, 0), lRange.Offset(-lRowoffset, UBound(lOutput, 2))).HorizontalAlignment = xlCenterAcrossSelection
        Range(lRange.Offset(-lRowoffset, 0), lRange.Offset(-lRowoffset, UBound(lOutput, 2))).Borders(xlEdgeRight).LineStyle = xlContinuous
        Range(lRange.Offset(-lRowoffset, 0), lRange.Offset(-lRowoffset, UBound(lOutput, 2))).Borders(xlEdgeRight).Weight = xlMedium
        Range(lRange.Offset(-lRowoffset, 0), lRange.Offset(-lRowoffset, UBound(lOutput, 2))).Borders(xlEdgeLeft).LineStyle = xlContinuous
        Range(lRange.Offset(-lRowoffset, 0), lRange.Offset(-lRowoffset, UBound(lOutput, 2))).Borders(xlEdgeLeft).Weight = xlMedium
        
    Else
        
    End If
    With Range(lRange, lRange.Offset(UBound(lOutput, 1), UBound(lOutput, 2)))
        .Borders(xlEdgeRight).LineStyle = xlContinuous
        .Borders(xlEdgeRight).Weight = xlMedium
        .Borders(xlEdgeLeft).LineStyle = xlContinuous
        .Borders(xlEdgeLeft).Weight = xlMedium
        .Borders(xlEdgeBottom).LineStyle = xlContinuous
        .Borders(xlEdgeBottom).Weight = xlMedium
        .Borders(xlEdgeTop).LineStyle = xlContinuous
        .Borders(xlEdgeTop).Weight = xlMedium
        
    End With
    

    ThisWorkbook.Sheets(lTabName).Cells.Columns.AutoFit
End Sub


Private Sub LoadDates()
    Dim lDealDate As Variant
    Dim lAnalsDate As Date
    Dim lDateUDT As DealDates
    
    lAnalsDate = Range("AnalysisDate").Value
    lDealDate = Range("DateInputs").Value
    With lDateUDT
        .AnalysisDate = Range("AnalysisDate").Value
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
    
    mCLO.LoadDealDates lDateUDT
    
    
End Sub

Private Sub LoadCollateralPool2()
    On Error GoTo ErrorTrap
    Dim lCollatPool As CollateralPoolForCLO
    Dim lAsset As Asset
    Dim lAssetCopy As Asset
    Dim lDealAssets As Variant
    Dim lAnalysisDate As Date
    Dim lRunRatingMigration As Boolean
    Dim i As Long
    
    lAnalysisDate = Range("AnalysisDate").Value
    lRunRatingMigration = True
    lDealAssets = Sheets("Inputs").Range("DealCollateral").Value
    Set lCollatPool = New CollateralPoolForCLO
    For i = LBound(lDealAssets, 1) To UBound(lDealAssets, 1)
        Set lAsset = mAllCollateral.GetAsset(CStr(lDealAssets(i, 1)))
        Set lAssetCopy = lAsset.Copy
        lAssetCopy.AddPar CDbl(lDealAssets(i, 2))
        lCollatPool.AddAsset lAssetCopy
NextAsset:
    Next i
    lCollatPool.SetAnalysisDate lAnalysisDate, lRunRatingMigration
    mCLO.LoadCollateralPool lCollatPool
    
Exit Sub
ErrorTrap:
    If i < UBound(lDealAssets, 1) Then
        Resume NextAsset
    End If

End Sub

Private Sub LoadCollateralPool()
    On Error GoTo ErrorTrap
    Dim lCollPool As CollateralPoolForCLO
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
    
    Worksheets("Existing Collateral Pool").Select
    lPoolInput = Range(Range("A2"), Range("A2").SpecialCells(xlLastCell)).Value
    lPrinSched = Range("Sink_Schedule").Value
    lAssumptions = Range("CFAssumptions").Value
    lNumPoolsAssets = UBound(lPoolInput, 1)  'Don't want to use a variable that can cause a potential error in an error trap.
    Set lCollPool = New CollateralPoolForCLO
    
    For i = LBound(lPoolInput, 1) To UBound(lPoolInput, 1)
        loffset = 1
        lSchedMatDate = 0
        If Len(lPoolInput(i, loffset)) = 0 Then
            Exit For
        End If
        
        
        lAssetUDT.BLKRockID = lPoolInput(i, loffset)
        loffset = loffset + 1
        'Debug.Assert lAssetUDT.BLKRockID <> "BRSSDAQQ7"
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
        
        lAssetUDT.ParAmount = lPoolInput(i, loffset)
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
    
         
        lAssetUDT.DateofDefault = lPoolInput(i, loffset)
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
        
        lAssetUDT.MarketValue = lPoolInput(i, loffset)
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
        
        lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
        Dim lamBalance As Double
        Dim lSchedDate As Date
        Dim lTotalBalance As Double
        
        ''GetSchedule
        Set lLoanSchedDict = New Dictionary
        If UCase(lAssetUDT.AmortizationType) = "SCHEDULED" Then
            lSchedMatDate = 0
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
                lTotalBalance = lTotalBalance - lamBalance
            Next j
        End If
        lAssetUDT.Maturity = CheckBusinessDate(lAssetUDT.Maturity, lAssetUDT.BusinessDayConvention)
        If lSchedMatDate > lAssetUDT.Maturity Then
            lAssetUDT.Maturity = CheckBusinessDate(lSchedMatDate, lAssetUDT.BusinessDayConvention)
        End If
        
        If lLoanSchedDict.Count = 0 Then
            lLoanSchedDict.Add CLng(lAssetUDT.Maturity), 1
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
        Set lAsset = New Asset
        lAsset.AddAsset lAssetUDT, lLoanSchedDict
        lCollPool.AddAsset lAsset
        lSchedDate = 0
        lSchedMatDate = 0
NextAsset:
    Next i
    
    mCLO.LoadCollateralPool lCollPool
    
    Exit Sub
ErrorTrap:
    'Dont add asset

    If i < lNumPoolsAssets Then
        Resume NextAsset
    End If
    
    
End Sub


'Private Sub LoadCLOInputs()
'    Dim lCLOInputs As CLOInputs
'    Dim lInput As Variant
'
'    lInput = Range("CLOINputs").Value
'
'    With lCLOInputs
'        .AnalysisDate = CDate(lInput(7, 1))
'        .BegFeeBasis = CDbl(lInput(5, 1))
'        .LIBOR = CDbl(lInput(4, 1))
'        .PurFinanceAccInt = CDbl(lInput(3, 1))
'        .TargetParAmount = CDbl(lInput(6, 1))
'        .EventOfDefault = CBool(lInput(8, 1))
'        .CallPercent = CDbl(lInput(11, 1))
'        .Liquidation = CDbl(lInput(12, 1))
'    End With
'
'    mCLO.LoadInputs lCLOInputs
'End Sub


Private Sub Cleanup()
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    Set mCLO = Nothing
    Set mProgressBar = Nothing
 
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    Range("A1").Select
End Sub
Public Function GetCFVector(iVectorName As String) As Variant
    Dim lAllCFVectors As Variant
    Dim lOutputVector As Variant
    Dim lNumVectors As Long
    Dim lNumValues As Long
    Dim i As Long
    Dim j As Long
    
    
    lAllCFVectors = Range("CF_Vectors").Value
    lNumValues = UBound(lAllCFVectors, 1)
    lNumVectors = UBound(lAllCFVectors, 2)
    
    ReDim lOutputVector(1 To lNumValues - 1)
    For i = 1 To lNumVectors
        If UCase(lAllCFVectors(1, i)) = UCase(iVectorName) Then
            Exit For
        End If
    Next i
    If i <= lNumVectors Then
        For j = 2 To lNumValues
            If IsNumeric(lAllCFVectors(j, i)) Then
                lOutputVector(j - 1) = CDbl(lAllCFVectors(j, i))
            Else
                lOutputVector(j - 1) = 0
            End If
        Next j
    Else
        For j = 1 To lNumVectors - 1
            lOutputVector(j) = 0
        Next j
    End If
    
    GetCFVector = lOutputVector
    
End Function
Public Sub OutputObjResults(iDealName As String, ioutput As Variant)
    'This subrountine copies the results from the deal tabs to the run model tabs.
    Dim lOut As Range
    Set lOut = Sheets(iDealName & " Inputs").Range("ObjWeights").Cells(1, 0)
    Range(lOut, lOut.Offset(UBound(ioutput) - 1, 0)).Value = ioutput
End Sub
Public Sub UpdaeObjeWeights()
    'This subroutine updates the deal tab with the user defined objective results from the run model tab.
    Dim lDealName As String
    Dim lOut As Range
    Dim lValues As Variant
    
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    lValues = Range(Range("I31"), Range("I31").Offset(7, 0)).Value
    lDealName = Range("C9").Value
    Set lOut = Sheets(lDealName & " Inputs").Range("ObjWeights").Cells(1, 2)
    Range(lOut, lOut.Offset(UBound(lValues) - 1, 0)).Value = lValues
End Sub
Private Function LoadFilter(Optional iFilterType As String) As String
    Dim lVar As Variant
    Dim i As Long
    Dim j As Long
    Dim lFilter As String
    If UCase(iFilterType) = "SALE" Then
        lVar = Range("SaleFilter").Value
    Else
        lVar = Range("BuyFilter").Value
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
    LoadFilter = lFilter
End Function
Public Function LoadRebalandRankInfo() As RankandRebalInputs
    Dim linput As Variant
    Dim lRandR As RankandRebalInputs
    Dim lDealName As String
    
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    linput = Range("E8:E12").Value
    lDealName = Range("C9").Value
    With lRandR
        .BuyFilter = LoadFilter("BUY")
        .BuyPar = linput(5, 1)
        .InclDealLoans = linput(2, 1)
        .IncPar = linput(1, 1)
        .SaleFilter = LoadFilter("SALE")
        .SalePar = linput(4, 1)
        If linput(3, 1) = "Buy" Then
            .TranType = Buy
        ElseIf linput(3, 1) = "Sale" Then
            .TranType = Sale
        End If
        .Libor = Sheets(lDealName & " Inputs").Range("K4").Value
    End With
    LoadRebalandRankInfo = lRandR
End Function
Public Function LoadRMandCFInputs() As RMandCFInputs
On Error GoTo ErrorTrap
    Dim lOut As RMandCFInputs
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    With lOut
        .AnalysisDate = Range("C8").Value
        .DealName = Range("C9").Value
        .RMCF = Range("C15").Value
        .CorrMatrix = Range("C16").Value
        .NumOfSims = Range("C17").Value
        .RMFreq = Range("C18").Value
        .StaticRndNum = Range("c19").Value
        .RandomizeSeed = Range("C20").Value
    End With
    LoadRMandCFInputs = lOut
Exit Function
ErrorTrap:

End Function
Public Function LoadHypoUserInputs(iDealName As String) As HypoUserInputs
    On Error GoTo ErrorTrap
    Dim lTrades As Variant
    Dim lHypoInputs As HypoUserInputs
    Dim lNumTrades As Long
    Dim lCounter As Long
    Dim i As Long
    
    ThisWorkbook.Activate
    Sheets("Run Model").Activate
    lHypoInputs.PoolMode = Range("N8").Value
    lTrades = Range("HypoAssets").Value
    lNumTrades = UBound(lTrades, 1)
    ReDim lHypoInputs.Trades(lNumTrades - 1)
    lHypoInputs.Libor = Sheets(iDealName & " Inputs").Range("K4").Value
    For i = 1 To lNumTrades
        If lTrades(i, 1) = iDealName Then
            With lHypoInputs.Trades(lCounter)
                .Deal = lTrades(i, 1)
                .BRSID = lTrades(i, 2)
                If lTrades(i, 3) = "Sale" Then
                    .TrnsType = Sale
                ElseIf lTrades(i, 3) = "Buy" Then
                    .TrnsType = Buy
                End If
                .Price = lTrades(i, 5)
                .Par = lTrades(i, 4)
            End With
            lCounter = lCounter + 1
        End If
    Next i
    If lCounter > 0 Then
        ReDim Preserve lHypoInputs.Trades(lCounter - 1)
    Else
        Err.Raise vbObjectError, , "No Trades for " & iDealName
    End If
    LoadHypoUserInputs = lHypoInputs
    Exit Function
ErrorTrap:
    Err.Raise Err.Number, Err.Source, Err.Description
End Function
Public Sub UnlockWorkbook()
    ThisWorkbook.Unprotect ("BlackRock")
End Sub

Public Sub LockWorkbook()
    ThisWorkbook.Protect ("BlackRock")
End Sub
Public Sub DeleteAll()
    Call UnlockWorkbook
    Call DeleteOutputTab("HYPO-")
    Call DeleteOutputTab("Rankings-")
    Call DeleteOutputTab("Compliance-")
    Call DeleteOutputTab("Collat CF-")
    Call DeleteOutputTab("Collat Spreads-")
    Call DeleteOutputTab("Optimization-")
    Call DeleteOutputTab("Deal CF-")
    Call DeleteOutputTab("RM-")
    Call DeleteOutputTab("Filter-")
    Call DeleteOutputTab("Rebalance-")
    Call DeleteOutputTab("Deal Assets-")
    Call LockWorkbook
End Sub
