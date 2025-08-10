Attribute VB_Name = "LoadData"

Public mLoaderFile As Workbook
Public Sub LoadData()
    Dim lDealName As String
    Dim lAnalysisDate As Date
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    'Application.Workbooks.Open("H:\My Documents\CLO CF Model\CF_Loader.xlsm")
    
    ThisWorkbook.Activate

    Set mLoaderFile = Application.Workbooks.Open("H:\My Documents\CLO CF Model\CF_Loader.xlsm", 3, True)
    lAnalysisDate = Range("Analysisdate").Value
    Call LoadPositionAndCash
    Call LoadSinkSchedule
    Call LoadIntRates
    Call LoadAssets
    mLoaderFile.Close (False)
    Call Sheet2.UnlockSheet
    ThisWorkbook.Activate
    Range("DealAnalysisDate").Value = lAnalysisDate
    Call RunComplianceAll
    Range("c9").Value = Range("c9").Value
    Call Sheet2.LockSheet
    
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    

End Sub
Private Sub LoadSinkSchedule()
    Dim lOutRange As Range
    Dim lInputRange As Range
    
    ThisWorkbook.Activate
    Set lOutRange = Range("Sink_Schedule").Cells(1, 1)
    Range("Sink_Schedule").ClearContents
    mLoaderFile.Activate
    Set lInputRange = Range(Range("SinkInputs"), Range("SinkInputs").Offset(0, 2).End(xlDown))
    Range(lOutRange, lOutRange.Offset(lInputRange.Rows.Count - 1, lInputRange.Columns.Count - 1)).Value = lInputRange.Value
    
End Sub
Private Sub LoadIntRates()
    Dim lOutRange As Range
    Dim lInputRange As Range
    
    ThisWorkbook.Activate
    Set lOutRange = Range("LiborCurve").Cells(1, 1)
    Range("LiborCurve").ClearContents
    mLoaderFile.Activate
    Set lInputRange = Range(Range("RatesInputs"), Range("RatesInputs").Offset(0, 1).End(xlDown))
    Range(lOutRange, lOutRange.Offset(lInputRange.Rows.Count - 1, lInputRange.Columns.Count - 1)).Value = lInputRange.Value
    
End Sub

Private Sub LoadPositionAndCash()
    Dim lSheets As Worksheet
    Dim lInt As Double
    Dim lPrin As Double
    Dim CFLoaderTab As String
    Dim lVal As Variant


    For Each lSheets In ThisWorkbook.Worksheets
        If right(lSheets.Name, 6) = "Inputs" Then
          lSheets.Range("DealCollateral").ClearContents
          CFLoaderTab = DealNameConv(lSheets.Name)
          mLoaderFile.Sheets(CFLoaderTab).Activate
          lVal = Range(Range("B2:C2"), Range("B2:C2").End(xlDown)).Value
          lPrin = Range("F2").Value
          lInt = Range("E2").Value
          Range(lSheets.Range("DealCollateral"), lSheets.Range("DealCollateral").Offset(UBound(lVal, 1) - 1, 0)).Value = lVal
          lSheets.Range("Accounts").Cells(2, 3).Value = lInt
          lSheets.Range("Accounts").Cells(2, 4).Value = lPrin
        End If
    Next
End Sub
Private Sub LoadAssets()
    Dim lOutRange As Range
    Dim lInputRange As Range
    
    ThisWorkbook.Activate
    Set lOutRange = Sheets("All Assets").Range("A2")
    Range(lOutRange, lOutRange.SpecialCells(xlCellTypeLastCell)).ClearContents
    mLoaderFile.Activate
    Set lInputRange = Sheets("Outputs").Range("A2")
    Set lInputRange = Range(lInputRange, lInputRange.SpecialCells(xlCellTypeLastCell))
    Range(lOutRange, lOutRange.Offset(lInputRange.Rows.Count - 1, lInputRange.Columns.Count - 1)).Value = lInputRange.Value
End Sub

Private Function DealNameConv(ByVal iDealName As String) As String
     iDealName = Replace(iDealName, " ", "")
     iDealName = Replace(iDealName, "Inputs", " Inputs")
     iDealName = Replace(iDealName, "Mag", "MAG")
    DealNameConv = iDealName
End Function

