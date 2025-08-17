VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Sheet2"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Option Explicit

Private Sub Worksheet_Activate()
    Call UnlockSheet
    ActiveWindow.FreezePanes = False
    Range("a1").Activate
    'Application.DisplayFormulaBar = False
    'ActiveWindow.DisplayHeadings = False
    Range("A2:O40").Select
    ActiveWindow.Zoom = True
    Range("O40").Select
    'ActiveWindow.FreezePanes = True
    Range("a1").Activate
    Call LockSheet
End Sub

Private Sub Worksheet_BeforeDoubleClick(ByVal Target As Range, Cancel As Boolean)
    Select Case Target.Address
    Case "$B$27:$B$31"
        Call RunModel
    Case "$B$33"
        Call DeleteAll
    End Select
End Sub

Private Sub Worksheet_Deactivate()
    'Application.DisplayFormulaBar = True
End Sub

Private Sub Worksheet_Change(ByVal Target As Range)
    
    If Target.Address = "$C$9" Then
        Call UpdateDealInfo(Target)
    ElseIf Target.Column = 6 And ((Target.Row >= 15 And Target.Row <= 20) Or (Target.Row >= 23 And Target.Row <= 28)) Then
        Call FormatFilters(Target)
    ElseIf Target.Address = "$C$14" Then
        Call UpdateCFandRatingSettings
    ElseIf Target.Address = "" Then
    
    ElseIf Target.Column = 8 Then
        Call UnlockSheet
        Range("H:H").Columns.AutoFit
        Call LockSheet
    End If
   
End Sub

Public Sub UpdateDealInfo(ByVal Target As Range)
    Dim lDealName As String
    Dim lAcc As Variant
    Dim lobjWeights As Variant
    Dim lWeighOut As Variant
    Dim lOut As Range
    Dim i As Long
    
    Call UnlockSheet
    lDealName = Target.Value
    If lDealName = "All" Then Exit Sub
    Range("C10").Value = Application.WorksheetFunction.sum(Sheets(lDealName & " Inputs").Range("DealCollateral").Value)
    lAcc = Sheets(lDealName & " Inputs").Range("Accounts").Value
    For i = LBound(lAcc, 1) To UBound(lAcc, 1)
        If UCase(lAcc(i, 2)) = "COLLECTION" Then
            Range("C11").Value = CDbl(lAcc(i, 4))
            Range("C12").Value = CDbl(lAcc(i, 3))
            Exit For
        End If
    Next i
    Set lOut = Range("D31")
    Range(lOut, lOut.Offset(7, 5)).ClearContents
    lobjWeights = Sheets(lDealName & " Inputs").Range("OBjWeights").Value
    ReDim lWeighOut(1 To UBound(lobjWeights), 1 To 6)
    For i = 1 To UBound(lobjWeights)
        lWeighOut(i, 1) = Sheets(lDealName & " Inputs").Range("OBjWeights").Cells(i, -1)
        lWeighOut(i, 4) = Sheets(lDealName & " Inputs").Range("OBjWeights").Cells(i, 0)
        lWeighOut(i, 5) = Sheets(lDealName & " Inputs").Range("OBjWeights").Cells(i, 1)
        lWeighOut(i, 6) = Sheets(lDealName & " Inputs").Range("OBjWeights").Cells(i, 2)
    Next i
    Range(lOut, lOut.Offset(UBound(lobjWeights) - 1, 5)).Value = lWeighOut
    Call LockSheet
End Sub
Public Sub FormatFilters(Target As Range)
    Dim lRow As Long
    
    Call UnlockSheet
    Select Case Target.Value
    Case "Moody's Industry"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$h$2:$h$3"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$D$2:$D$34"
        End With
    Case "S&P Industry"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$h$2:$h$3"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$C$2:$C$43"
        End With
    Case "S&P Rating"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$G2:$G$8"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$A$2:$A$21"
        End With
    Case "Moody's Rating", "Moody's Rating WARF", "Moody's Rating DPR"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$G2:$G$8"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$B$2:$B$23"
        End With
        'Target.Offset(0, 2).Value = ""
    Case "WAL", "Facility Size", "Market Value"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$G2:$G$8"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateDecimal, AlertStyle:=xlValidAlertStop, Operator:=xlGreaterEqual, Formula1:="0"
        End With
    Case "Cov-Lite"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$H2:$H$3"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$K$2:$K$3"
        End With
    Case "Country"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$H2:$H$3"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$L$2:$L$9"
        End With
    Case "Analyst Opinion"
        With Target.Offset(0, 1).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$H2:$H$3"
        End With
        With Target.Offset(0, 2).Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$M2:$M$4"
        End With
    Case ""
        Target.Offset(0, -2).ClearContents
        Target.Offset(0, -1).ClearContents
        Target.Offset(0, 1).ClearContents
        Target.Offset(0, 2).ClearContents
        Target.Offset(0, 3).ClearContents
    End Select
   'Target.Offset(0, 2).Columns.AutoFit
    Range("F:F").Columns.AutoFit
    Call LockSheet
End Sub
Public Sub RunModel()
    Dim lAllSub As Dictionary
    Dim lInclCFandRating As Boolean
    'PerfMonStartMonitoring
    
    lInclCFandRating = Range("C14").Value
    Set lAllSub = New Dictionary
    lAllSub.Add "Asset Rankings", 1
    lAllSub.Add "Deal Compliance", 2
    lAllSub.Add "Hypotherical Trades", 2
    lAllSub.Add "Portfolio Rebalancing", 3
    lAllSub.Add "View Deal Assets", 4
    lAllSub.Add "Collateral Spreads", 5
    If lInclCFandRating Then
        lAllSub.Add "Collateral Cashflows Projections", 4
        lAllSub.Add "Deal Cashflows Projections", 5
        lAllSub.Add "Rating Migration Projections", 6
    End If
    
    Set UserForm1.mListofDeals = lAllSub
    UserForm1.initA6
    UserForm1.Caption = "Select Subroutine"
    UserForm1.Show
    

    Select Case UserForm1.ListBox1.Value
    Case "Collateral Spreads"
        ComplianceHypo.RunCollatSpreads
    Case "Asset Rankings"
        ComplianceHypo.RunRankings
    Case "Deal Compliance"
        ComplianceHypo.RunCompliance
    Case "Hypotherical Trades"
        ComplianceHypo.RunHypo2
    Case "Portfolio Rebalancing"
        ComplianceHypo.RunRebalancing
    Case "View Deal Assets"
        ComplianceHypo.RunDealAssets
    Case "Collateral Cashflows Projections"
    Case "Deal Cashflows Projections"
        If Range("C9").Value = "All" Then
            ComplianceHypo.RunDealCashflowAll
        Else
            ComplianceHypo.RunDealCF
        End If
    Case "Rating Migration Projections"
        If Range("C9").Value = "All" Then
            ComplianceHypo.RunRatingMigrationAll
        Else
            ComplianceHypo.RunRatingMigration
        End If
    End Select
    'PerfMonStopMonitoring "C:\Users\adamchaz\Dropbox\ProgramData\Excel\CLO CF Model\CLO Programs\Performance\" & UserForm1.ListBox1.Value & ".txt"
End Sub
Public Sub UnlockSheet()
    ThisWorkbook.Activate
    Sheets("Run Model").Unprotect "BlackRock"
End Sub
Public Sub LockSheet()
    ThisWorkbook.Activate
    Sheets("Run Model").Protect "BlackRock"
End Sub
Public Sub UpdateCFandRatingSettings()
    Dim lDealName As String
    Call UnlockSheet
    Call UnlockWorkbook
    If Range("C14").Value Then
        With Range("B13:C20").Font
            .ColorIndex = xlAutomatic
            .TintAndShade = 0
        End With
        Sheets("Reference Table").Visible = xlSheetVisible
    Else
        With Range("B13:C20").Font
            .ThemeColor = xlThemeColorDark1
            .TintAndShade = -4.99893185216834E-02
        End With
        Sheets("Reference Table").Visible = xlSheetHidden
    End If
    Call LockSheet
    Call LockWorkbook
End Sub
