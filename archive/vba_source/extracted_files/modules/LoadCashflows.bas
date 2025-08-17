Attribute VB_Name = "LoadCashflows"
Option Explicit
Option Private Module

Private mProgressBar As IProgressBar
Private mAssumptions As Variant
Private mPrinSched As Variant
Private mCollateralPool As Variant
Private mAssets As Dictionary  'List of Assets by blackrockids

Public Sub DeleteBRSSheet()
    Dim lsheet As Worksheet
    Application.DisplayAlerts = False
    For Each lsheet In ThisWorkbook.Sheets
        If lsheet.Name = "ALL" Or UCase(Left(lsheet.Name, 3)) = "BRS" Then
            lsheet.Delete
        End If
    Next
    Application.DisplayAlerts = True
    
End Sub


Public Sub OutputCF(iCF As SimpleCashflow, Optional iBLKRockID As String)
    Dim i As Long
    Dim lcolumnoffset As Long
    Dim lLocalColumnoffset As Long
    Dim lRange As Range
    Dim lsheet As Worksheet
    Dim lsheetfound As Boolean
    
    
    If Len(iBLKRockID) = 0 Then
        iBLKRockID = "ALL"
    End If
    
    For Each lsheet In ThisWorkbook.Sheets
        If UCase(lsheet.Name) = UCase(iBLKRockID) Then
            lsheetfound = True
            ThisWorkbook.Sheets(iBLKRockID).Cells.Clear
            Exit For
        End If
    Next lsheet
    If lsheetfound = False Then
        Call ThisWorkbook.Sheets.Add(, Sheets(Sheets.Count), , "Worksheet")
        ActiveSheet.Name = iBLKRockID
        ActiveSheet.Tab.Color = 5287936
    End If
    
    Set lRange = ThisWorkbook.Sheets(iBLKRockID).Range("A1").Offset(0, lcolumnoffset)
    

    lRange.Offset(0, lLocalColumnoffset).Value = "Payment Date"

    lLocalColumnoffset = lLocalColumnoffset + 1
    If UCase(iBLKRockID) <> "ALL" Then
        lRange.Offset(0, lLocalColumnoffset).Value = "Accrual Beg Date"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "Accrual End Date"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "Beg Balance"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "Default Balance"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "MV of Default Balance"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "Default"
        lLocalColumnoffset = lLocalColumnoffset + 1
        lRange.Offset(0, lLocalColumnoffset).Value = "MV Default"
        lLocalColumnoffset = lLocalColumnoffset + 1

    End If
    lRange.Offset(0, lLocalColumnoffset).Value = "Interest"
    lLocalColumnoffset = lLocalColumnoffset + 1
    lRange.Offset(0, lLocalColumnoffset).Value = "Scheduled Principal"
    lLocalColumnoffset = lLocalColumnoffset + 1
    lRange.Offset(0, lLocalColumnoffset).Value = "UnScheduled Principal"
    lLocalColumnoffset = lLocalColumnoffset + 1
    lRange.Offset(0, lLocalColumnoffset).Value = "Recoveries"
    lLocalColumnoffset = lLocalColumnoffset + 1
    If UCase(iBLKRockID) <> "ALL" Then
        lRange.Offset(0, lLocalColumnoffset).Value = "Net loss"
        lLocalColumnoffset = lLocalColumnoffset + 1
    End If
    lRange.Offset(0, lLocalColumnoffset).Value = "Total"
    lLocalColumnoffset = lLocalColumnoffset + 1
    For i = 0 To iCF.Count
        lLocalColumnoffset = 0
        With iCF
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .PaymentDate(i)
            lRange.Offset(i + 1, lLocalColumnoffset).NumberFormat = "m/d/yyyy"
            lLocalColumnoffset = lLocalColumnoffset + 1
            If UCase(iBLKRockID) <> "ALL" Then
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .AccBegDate(i)
                lRange.Offset(i + 1, lLocalColumnoffset).NumberFormat = "m/d/yyyy"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .AccEndDate(i)
                lRange.Offset(i + 1, lLocalColumnoffset).NumberFormat = "m/d/yyyy"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .BegBalance(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .DefaultBal(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .MVDefaultBal(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .Default(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .MVDefault(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1

            End If
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .Interest(i)
            lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
            lLocalColumnoffset = lLocalColumnoffset + 1
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .SchedPrincipal(i)
            lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
            lLocalColumnoffset = lLocalColumnoffset + 1
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .UnSchedPrincipal(i)
            lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
            lLocalColumnoffset = lLocalColumnoffset + 1
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .Recoveries(i)
            lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
            lLocalColumnoffset = lLocalColumnoffset + 1
            If UCase(iBLKRockID) <> "ALL" Then
                lRange.Offset(i + 1, lLocalColumnoffset).Value = .Netloss(i)
                lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
                lLocalColumnoffset = lLocalColumnoffset + 1
            End If
            lRange.Offset(i + 1, lLocalColumnoffset).Value = .Total(i)
            lRange.Offset(i + 1, lLocalColumnoffset).Style = "Comma"
            lLocalColumnoffset = lLocalColumnoffset + 1
        
        End With
    Next i
    
    
    ThisWorkbook.Sheets(iBLKRockID).Cells.Columns.AutoFit

End Sub


Private Sub Setup()
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    ThisWorkbook.Activate
    Set mAssets = New Dictionary
    Worksheets("All Assets").Select
    mCollateralPool = Range(Range("A2"), Range("A2").SpecialCells(xlLastCell)).Value
    mPrinSched = Range("Sink_Schedule").Value
    mAssumptions = Range("CFAssumptions").Value
    Call DeleteBRSSheet
    
End Sub
Private Sub Cleanup()
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    Set mAssets = Nothing
    
    ThisWorkbook.Activate
    
    Set mAssets = Nothing
    Set mProgressBar = Nothing
    mAssumptions = Empty
    mPrinSched = Empty
    mCollateralPool = Empty
    Sheets("Inputs").Activate
    Range("A1").Select
End Sub
Public Sub RunCollateralCashflows()
    Dim lBlkRockIDs As Variant
    Dim i As Long
    Dim lLoan As Asset
    Dim lCF As SimpleCashflow
    Dim lCashFlowColl As CashflowClass
    
    Call Setup
    Call LoadListofDeals
    lBlkRockIDs = mAssets.Keys
    Set lCashFlowColl = New CashflowClass
    For i = LBound(lBlkRockIDs) To UBound(lBlkRockIDs)
        Set lLoan = mAssets(lBlkRockIDs(i))
        lLoan.AddPar 1000000
        Set lCF = lLoan.CalcCF
        If mAssets.Count <= 20 Then
            Call OutputCF(lCF, lLoan.BLKRockID)

'
        Else
            lCashFlowColl.AddSimpleCashflow lCF
            
        End If
    Next i
    If mAssets.Count > 10 Then
    
        Set lCF = lCashFlowColl.GetSimpleCashflow
        Call OutputCF(lCF)
    End If
    
    
    Call Cleanup
    MsgBox "Cashflows have finish running." & vbCr & "They are on last tabs.", vbOKOnly, "Done"

End Sub
Private Sub LoadListofDeals()
    Dim lDeals As Variant
    Dim lCUSIPandName As Variant
    Dim i As Long
    ThisWorkbook.Activate
    Sheets("ALL Assets").Activate
    lCUSIPandName = Range(Range("A2:B2"), Range("A2:B2").End(xlDown)).Value
    Dim lNames As Dictionary
    Set lNames = New Dictionary
    
    For i = LBound(lCUSIPandName, 1) To UBound(lCUSIPandName, 1)
        If Len(lCUSIPandName(i, 1)) > 0 Then
            lNames.Add lCUSIPandName(i, 1) & vbTab & lCUSIPandName(i, 2), i
        End If
    Next i
    
    Set UserForm1.mListofDeals = lNames
    UserForm1.init
    UserForm1.Show
    If UserForm1.mSelectListofDeals.Count > 0 Then
        lDeals = UserForm1.mSelectListofDeals.Keys
        For i = LBound(lDeals) To UBound(lDeals)
            Call AddAsset(Left(lDeals(i), InStr(lDeals(i), vbTab) - 1))
        Next i
    End If
    
End Sub

Private Sub AddAsset(iBLKRockID As String)
    On Error GoTo ErrorTrap
    Dim i, j As Long
    Dim lLoanSchedDict As Dictionary
    Dim lSchedMatDate As Date
    Dim loffset As Long
    Dim lAssetUDT As AssetUDT
    Dim lAsset As Asset
    Dim lSchedNum As Long
    'iPoolType=Existing or Potential

    i = LBound(mCollateralPool, 1)
    loffset = 1
    Do While i < UBound(mCollateralPool, 1) And Len(mCollateralPool(i, 1)) > 0
    
        If mCollateralPool(i, loffset) = iBLKRockID Then
            lAssetUDT.BLKRockID = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.IssueName = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.IssuerName = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.IssuerId = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.Tranche = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.BondLoan = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.ParAmount = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.Maturity = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.CouponType = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.PaymentFreq = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.CpnSpread = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.LiborFloor = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.Index = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.Coupon = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.CommitFee = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.UnfundedAmount = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.FacilitySize = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYIndustry = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.SPIndustry = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.Country = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.Seniority = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.PikAsset = True
            Else
                lAssetUDT.PikAsset = False
            End If
            loffset = loffset + 1
            
            
            If UCase(Trim(mCollateralPool(i, loffset))) = "YES" Then
                lAssetUDT.PIKing = True
            Else
                lAssetUDT.PIKing = False
            End If
            loffset = loffset + 1
            
            lAssetUDT.PIKAmount = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
        
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.DefaultAsset = True
            Else
                lAssetUDT.DefaultAsset = False
            End If
            loffset = loffset + 1
        
             If Len(mCollateralPool(i, loffset)) > 0 Then lAssetUDT.DateofDefault = mCollateralPool(i, loffset)
                                
            loffset = loffset + 1
        
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.DelayDrawdown = True
            Else
                lAssetUDT.DelayDrawdown = False
            End If
            loffset = loffset + 1
        
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.Revolver = True
            Else
                lAssetUDT.Revolver = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.LOC = True
            Else
                lAssetUDT.LOC = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.Participation = True
            Else
                lAssetUDT.Participation = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.DIP = True
            Else
                lAssetUDT.DIP = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.Converitable = True
            Else
                lAssetUDT.Converitable = False
            End If
            loffset = loffset + 1
        
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.StructFinance = True
            Else
                lAssetUDT.StructFinance = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.BridgeLoan = True
            Else
                lAssetUDT.BridgeLoan = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.CurrentPay = True
            Else
                lAssetUDT.CurrentPay = False
            End If
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.CovLite = True
            Else
                lAssetUDT.CovLite = False
            End If
            loffset = loffset + 1
            
            lAssetUDT.Currency = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.WAL = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MarketValue = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            If mCollateralPool(i, loffset) = "Yes" Then
                lAssetUDT.FLLO = True
            Else
                lAssetUDT.FLLO = False
            End If
            loffset = loffset + 1
            
            lAssetUDT.MDYRating = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.MDYRecoveryRate = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYDPRating = UCase(Trim(mCollateralPool(i, loffset)))
            loffset = loffset + 1
            
            lAssetUDT.MDYFacilityRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYFacilityOutlook = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYIssuerRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYIssuerOutlook = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYSnrSecRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYSNRUnSecRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYSubRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.MDYCreditEstRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            If Len(mCollateralPool(i, loffset)) > 0 Then
                lAssetUDT.MDYCreditEstDate = mCollateralPool(i, loffset)
            End If
            loffset = loffset + 1
            
            lAssetUDT.SandPFacilityRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.SandPIssuerRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.SandPSnrSecRating = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.SandPSubordinate = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.DatedDate = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.IssueDate = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.FirstPaymentDate = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.AmortizationType = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.DayCount = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.LIBORCap = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.BusinessDayConvention = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.EOMFlag = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            lAssetUDT.AmtIssued = mCollateralPool(i, loffset)
            loffset = loffset + 1
            
            
            Dim lamBalance As Double
            Dim lSchedDate As Date
            Dim lTotalBalance As Double
            
            ''GetSchedule
            Set lLoanSchedDict = New Dictionary
            If UCase(lAssetUDT.AmortizationType) = "SCHEDULED" Then
                For lSchedNum = LBound(mPrinSched, 1) To UBound(mPrinSched, 1)
                    If UCase(lAssetUDT.BLKRockID) = UCase(Trim(mPrinSched(lSchedNum, 1))) Then
                        lamBalance = mPrinSched(lSchedNum, 3)
                        lSchedDate = CDate(mPrinSched(lSchedNum, 2))
                        lTotalBalance = lTotalBalance + lamBalance
                        If lSchedDate > lSchedMatDate Then lSchedMatDate = lSchedDate
                        If lLoanSchedDict.Exists(lSchedDate) Then
                            lLoanSchedDict(lSchedDate) = lLoanSchedDict(lSchedDate) + lamBalance
                        Else
                            lLoanSchedDict.Add lSchedDate, lamBalance
                        End If
                    End If
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
            
            For j = LBound(mAssumptions, 1) To UBound(mAssumptions, 1)
                If UCase(lAssetUDT.BLKRockID) = UCase(Trim(mAssumptions(j, 1))) Or UCase(Trim(mAssumptions(j, 1))) = "ALL" Then
                    If IsNumeric(mAssumptions(j, 2)) Then
                        lAssetUDT.PrePayRate = mAssumptions(j, 2)
                    Else
                        lAssetUDT.PrePayRate = GetCFVector(CStr(mAssumptions(j, 2)))
                    End If
                
                    
                    If IsNumeric(mAssumptions(j, 3)) Then
                        lAssetUDT.DefaultRate = mAssumptions(j, 3)
                    Else
                        lAssetUDT.DefaultRate = GetCFVector(CStr(mAssumptions(j, 3)))
                    End If
                    If IsNumeric(mAssumptions(j, 4)) Then
                        lAssetUDT.Severity = mAssumptions(j, 4)
                    Else
                        lAssetUDT.Severity = GetCFVector(CStr(mAssumptions(j, 4)))
                    End If
                    lAssetUDT.Lag = mAssumptions(j, 5)
                End If
            Next j
            Set lAsset = New Asset
            lAsset.AddAsset lAssetUDT, lLoanSchedDict
            mAssets.Add iBLKRockID, lAsset
            Exit Do
            
        End If
        'lasset.

        i = i + 1
        loffset = 1
    Loop
    Exit Sub
ErrorTrap:
    'Dont add asset

    
End Sub
