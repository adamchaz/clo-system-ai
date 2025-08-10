VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Sheet1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Option Explicit

Private Sub Worksheet_BeforeDoubleClick(ByVal Target As Range, Cancel As Boolean)
    Dim lAllSub As Dictionary

    If Target.Address = Range("RunModelButton").Address Then
        'PerfMonStartMonitoring
        Set lAllSub = New Dictionary
        
        
        If Application.UserName = "Freeman, Adam" Or Application.UserName = "adamchaz" Then
            lAllSub.Add "Collateral Cashflow", 1
            lAllSub.Add "Collateral Spreads", 2
            lAllSub.Add "Compliance Test", 3
            lAllSub.Add "Deal Cashflow", 4
            lAllSub.Add "Deal Cashflow All", 5
            lAllSub.Add "Hypothetical Trading", 6
            lAllSub.Add "Portfolio Optimization", 7
            lAllSub.Add "Portfolio Rebalancing", 8
            lAllSub.Add "Rankings", 9
            lAllSub.Add "Rating Mitgration", 10
            lAllSub.Add "Rating Mitgration All Deals", 11
            lAllSub.Add "Apply Filter", 12
        Else
            lAllSub.Add "Compliance Test", 3
            lAllSub.Add "Hypothetical Trading", 6
            lAllSub.Add "Portfolio Optimization", 6
            lAllSub.Add "Portfolio Rebalancing", 6
            lAllSub.Add "Rankings", 7
            lAllSub.Add "Apply Filter", 12
        End If
        
        Set UserForm1.mListofDeals = lAllSub
        UserForm1.initA6
        UserForm1.Caption = "Select Subroutine"
        UserForm1.Show
        
        'ThisWorkbook.Save
        Select Case UserForm1.ListBox1.Value
        
        Case "Deal Cashflow"
            Call ComplianceHypo.RunDealCF
        Case "Collateral Cashflow"
            Call ComplianceHypo.RunCollateralCF
        Case "Collateral Spreads"
            Call ComplianceHypo.RunCollatSpreads
        Case "Rating Mitgration"
            Call ComplianceHypo.RunRatingMigration
        Case "Rankings"
            Call ComplianceHypo.RunRankings
        Case "Compliance Test"
            Call ComplianceHypo.RunCompliance
        Case "Portfolio Rebalancing"
            Call ComplianceHypo.RunRebalancing
        Case "Hypothetical Trading"
            Call ComplianceHypo.RunHypo2
        Case "Portfolio Optimization"
            Call ComplianceHypo.RunOptimization
        Case "Rating Mitgration All Deals"
            Call ComplianceHypo.RunRatingMigrationAll
        Case "Apply Filter"
            Call ComplianceHypo.RunApplyFilter
        Case "Deal Cashflow All"
            Call ComplianceHypo.RunDealCashflowAll
        End Select
        'PerfMonStopMonitoring "C:\Users\adamchaz\Dropbox\ProgramData\Excel\CLO CF Model\CLO Programs\Performance\" & UserForm1.ListBox1.Value & ".txt"
    ElseIf Target.Address = "$A$28" Then
        Call ComplianceHypo.DeleteAll
    ElseIf Target.Address = "$A$30" Then
        If Application.UserName = "Freeman, Adam" Then
            Call LoadData.LoadData
        End If
    End If
    Set UserForm1 = Nothing
End Sub

Private Sub Worksheet_Change(ByVal Target As Range)
    Dim lSheets As Worksheet
    
    If Target.Address = "$C$4" Then
        Application.ScreenUpdating = False
        If Target.Value = "All" Then
            For Each lSheets In ThisWorkbook.Worksheets
                If right(lSheets.Name, 6) = "Inputs" Then
                    lSheets.Visible = xlSheetVisible
                End If
            Next
        Else
            For Each lSheets In ThisWorkbook.Worksheets
                If Left(lSheets.Name, Len(Target.Value)) = Target.Value Then
                    lSheets.Visible = xlSheetVisible
                ElseIf right(lSheets.Name, 6) = "Inputs" Then
                    lSheets.Visible = xlSheetHidden
                End If
            Next
        End If
        Application.ScreenUpdating = True
    End If
    
    If (Target.Column = 13 Or Target.Column = 19) And Target.Cells.Count = 1 Then
    Dim lRow As Long
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
        Case "Moody's Rating"
            With Target.Offset(0, 1).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$G2:$G$8"
            End With
            With Target.Offset(0, 2).Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$B$2:$B$23"
            End With
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
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="='Filter Sheet'!$L$2:$L$44"
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
    End If
End Sub

Private Sub Worksheet_SelectionChange(ByVal Target As Range)

End Sub
