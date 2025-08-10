Attribute VB_Name = "Test"
'
''Private Declare Function WaitMessage Lib "user32" () As Long
''
''Private Declare Function PeekMessage Lib "user32" _
''Alias "PeekMessageA" _
''(ByRef lpMsg As MSG, ByVal hwnd As Long, _
''ByVal wMsgFilterMin As Long, _
''ByVal wMsgFilterMax As Long, _
''ByVal wRemoveMsg As Long) As Long
''
''Private Declare Function TranslateMessage Lib "user32" _
''(ByRef lpMsg As MSG) As Long
''
''Private Declare Function PostMessage Lib "user32" _
''Alias "PostMessageA" _
''(ByVal hwnd As Long, _
''ByVal wMsg As Long, _
''ByVal wParam As Long, _
''lParam As Any) As Long
''
''Private Declare Function FindWindow Lib "user32" _
''Alias "FindWindowA" _
''(ByVal lpClassName As String, _
''ByVal lpWindowName As String) As Long
'
'Private Type POINTAPI
'    x As Long
'    y As Long
'End Type
'
'Private Type MSG
'    hwnd As Long
'    Message As Long
'    wParam As Long
'    lParam As Long
'    time As Long
'    pt As POINTAPI
'End Type
'
'Private Const WM_KEYDOWN As Long = &H100
'Private Const PM_REMOVE  As Long = &H1
'Private Const WM_CHAR    As Long = &H102
'Private bExitLoop As Boolean
'
'Public Sub Test()
'Dim lRates As Variant
'Dim lYC As YieldCurve
'Dim lDict As Dictionary
'Dim lAnalysisDate As Date
'Dim lItem As Double
'Dim i As Long
'
'    lRates = Range("LIBORCurve").Value
'    Set lDict = New Dictionary
'    For i = LBound(lRates, 1) To UBound(lRates, 1)
'        lDict.Add CLng(lRates(i, 1)), lRates(i, 2)
'    Next i
'    Set lYC = New YieldCurve
'    lYC.Setup "LIBOR", "05/15/2015", lDict
'    lItem = lYC.SpotRate("05/16/2015", 1)
'End Sub
'
'Public Sub MatrixTest()
'    Dim lTransVariant As Variant
'    Dim lTranMatrix() As Double
'    Dim lSemiMat() As Double
'    Dim lQTRMat() As Double
'    Dim i As Long
'    Dim j As Long
'
'    lTransVariant = Range("SpTransMat").Value
'    lTranMatrix = ConvertToArry(lTransVariant)
'    lSemiMat = MatrixSQRT(lTranMatrix)
'    lSemiMat = MatrixQOM(lSemiMat)
'    lQTRMat = MatrixSQRT(lSemiMat)
'    lQTRMat = MatrixQOM(lQTRMat)
'
'    Debug.Print MatrixABS(MatrixSub(MatrixMultiply(lSemiMat, lSemiMat), lTranMatrix))
'    Debug.Print MatrixABS(MatrixSub(MatrixMultiply(MatrixMultiply(lQTRMat, lQTRMat), MatrixMultiply(lQTRMat, lQTRMat)), lTranMatrix))
'
'End Sub
'Public Sub OutputCorrelationMatrix()
'    Dim i As Long
'    Dim j As Long
'    Dim loutput As Variant
'    Dim lRange As Range
'    Dim lNumAssets As Long
'
'    lNumAssets = 488
'    ReDim loutput(1 To lNumAssets, 1 To lNumAssets)
'    For i = 1 To lNumAssets
'        For j = 1 To lNumAssets
'            If i = j Then
'                loutput(i, j) = 1
'            Else
'                loutput(i, j) = 0.3
'            End If
'        Next j
'    Next i
'    Set lRange = ThisWorkbook.Sheets("Asset Correlation").Range("B2")
'
'    Range(lRange, lRange.Offset(UBound(loutput, 1) - 1, UBound(loutput, 2) - 1)).Value = loutput
'
'End Sub
'Public Sub TestCholesky()
'    Dim lMat() As Double
'    Dim lTestMat() As Double
'    Dim lRandom() As Double
'    Dim lChockeyDeecom() As Double
'    Dim lCorrelated() As Double
'    Dim lNumRows As Long
'    Dim i As Long
'
'    lMat = MatrixMath.ConvertToArry(Range("AssetCorrelation").Value)
'    lNumRows = UBound(lMat, 1)
'    ReDim lRandom(1 To lNumRows, 1 To 1)
'    lTestMat = MatrixMath.MatrixCholesky(lMat)
'    For i = 1 To lNumRows
'        lRandom(i, 1) = Application.WorksheetFunction.Norm_S_Inv(Rnd())
'    Next i
'    lCorrelated = MatrixMultiply(lTestMat, lRandom)
'
'End Sub
'
'Public Sub omg()
'Dim lsheet As Worksheet
'
'For Each lsheet In ActiveWorkbook.Worksheets
'    Debug.Print lsheet.Name
'
'Next
''lsheet.Name =
'End Sub
'Public Function CountOperator(iFilter As String, iOperator As String) As Long
'    Dim lNum As Long
'    Dim lChar As Long
'
'    lChar = 1
'    Do While lChar < Len(iFilter)
'        If InStr(lChar, iFilter, iOperator) = 0 Then
'
'            Exit Do
'        Else
'            lChar = InStr(lChar, iFilter, iOperator)
'            lNum = lNum + 1
'            lChar = lChar + Len(iOperator)
'        End If
'    Loop
'    CountOperator = lNum
'End Function
Public Sub FindNextOperator(ByVal iStartChar As Long, ByVal iText As String, oOperator As String, oCharNum As Long)
    Dim lAnd As Long
    Dim lOR As Long
    Dim lNot As Long
    Dim lNotOr As Long
    Dim lNotAnd As Long
    Dim lNum As Long

    oCharNum = 0
    oOperator = ""
    lAnd = InStr(iStartChar, UCase(iText), " AND ")
    If lNum < lAnd Then
        oCharNum = lAnd
        oOperator = "AND"
    End If
    lOR = InStr(iStartChar, UCase(iText), " OR ")
    If lNum < lOR Then
        oCharNum = lOR
        oOperator = "OR"
    End If
    lNot = InStr(iStartChar, UCase(iText), " NOT ")
    If lNum < lNot Then
        oCharNum = lNot
        oOperator = "NOT"
    End If
    lNotAnd = InStr(iStartChar, UCase(iText), " NOT AND ")
    If lNum < lNotAnd Then
        oCharNum = lNotAnd
        oOperator = "NOT AND"
    End If
    lNotOr = InStr(iStartChar, UCase(iText), " NOT OR ")
    If lNum < lNotOr Then
        oCharNum = lNotOr
        oOperator = "NOT OR"
    End If



End Sub
'
'
'Public Sub Test34()
'    Dim lFilter As String
'    lFilter = "S&P Rating>BBB+andS&P Industry!=Oil & gasandS&P Industry!=Utilities"
'    'lfilter = "S&P Rating>BBB+and(S&P Industry=Oil & gasorS&P Industry=Utilities)"
'    'Debug.Print CountOperator(UCase(lfilter), UCase("and"))
'    Debug.Print ApplyFilter(lFilter)
'End Sub
'
'Public Function ApplyFilter(ByVal iFilter As String) As Boolean
'    Dim lLeft As Long
'    Dim lRight As Long
'    Dim lSubFilter As String
'    Dim lResult As String
'    Dim lLHS As Variant
'    Dim lRHS As Variant
'    Dim lNextOperator As String
'    Dim lNextChar As Long
'    Dim lCurrOperator As String
'    Dim lCurrChar As Long
'
'    'Replace Everything
'    Do While InStrRev(iFilter, "(") > 0
'        lLeft = InStrRev(iFilter, "(")
'        lRight = InStr(lLeft, iFilter, ")")
'        lSubFilter = Mid(iFilter, lLeft + 1, lRight - lLeft - 1)
'        lResult = ApplyFilter(lSubFilter)
'        iFilter = Replace(iFilter, "(" & lSubFilter & ")", lResult)
'    Loop
'    'Find logical operator
'    Call FindNextOperator(1, iFilter, lNextOperator, lNextChar)
'    If lNextChar = 0 Then
'        If UCase(iFilter) = "TRUE" Then
'            ApplyFilter = True
'        ElseIf UCase(iFilter) = "FALSE" Then
'            ApplyFilter = False
'        Else
'            ApplyFilter = Comparison(iFilter)
'        End If
'    Else
'        lLHS = ApplyFilter(Trim(Left(iFilter, lNextChar - 1)))
'        lCurrChar = lNextChar
'        lCurrOperator = lNextOperator
'        Call FindNextOperator(lNextChar + 1, iFilter, lNextOperator, lNextChar)
'        Do While lNextChar > 0
'            lSubFilter = Trim(Mid(iFilter, lCurrChar + Len(lCurrOperator), lNextChar - lCurrChar - Len(lCurrOperator)))
'            lRHS = ApplyFilter(lSubFilter)
'            lLHS = ApplyLogical(lLHS, lCurrOperator, lRHS)
'            lCurrChar = lNextChar
'            lCurrOperator = lNextOperator
'            Call FindNextOperator(lNextChar + 1, iFilter, lNextOperator, lNextChar)
'        Loop
'        lRHS = ApplyFilter(Trim(Mid(iFilter, lCurrChar + Len(lCurrOperator), Len(iFilter) + 1 - lCurrChar - Len(lCurrOperator))))
'        ApplyFilter = ApplyLogical(lLHS, lCurrOperator, lRHS)
'    End If
'End Function
'
'Public Function ApplyLogical(iLHS As Variant, iOperator As String, iRHS As Variant) As Boolean
'    Select Case Trim(UCase(iOperator))
'    Case "AND"
'        ApplyLogical = iLHS And iRHS
'    Case "OR"
'        ApplyLogical = iLHS Or iRHS
'    Case "NOT OR"
'        'ApplyLogical = iLHS not or iRHS
'    Case "NOT And"
'
'
'    End Select
'End Function
'
'Public Function Comparison(iFilter As String) As Boolean
'    Debug.Print iFilter
'
'   Comparison = True
'End Function
'
'
'Public Sub Testdatediff()
'    'debug.Print datediff("M","01/29/2016","01/
'End Sub
'
'Sub ListLinks()
''Updateby20140529
'Dim wb As Workbook
'Dim xindex As Long
'Dim link As Variant
'Set wb = Application.ActiveWorkbook
'If Not IsEmpty(wb.LinkSources(xlExcelLinks)) Then
'    wb.Sheets.Add
'    xindex = 1
'    For Each link In wb.LinkSources(xlExcelLinks)
'        Application.ActiveSheet.Cells(xindex, 1).Value = link
'        xindex = xindex + 1
'    Next link
'End If
'
'End Sub
'
'
'
'
'
'
'
'Sub StartKeyWatch()
'
'    Dim msgMessage As MSG
'    Dim bCancel As Boolean
'    Dim iKeyCode As Integer
'    Dim lXLhwnd As Long
'
'    'handle the ESC key.
'    On Error GoTo errHandler:
'    Application.EnableCancelKey = xlErrorHandler
'   'initialize this boolean flag.
'    bExitLoop = False
'    'get the app hwnd.
'    lXLhwnd = FindWindow("XLMAIN", Application.Caption)
'    Do
'        WaitMessage
'        'check for a key press and remove it from the msg queue.
'        If PeekMessage _
'            (msgMessage, lXLhwnd, WM_KEYDOWN, WM_KEYDOWN, PM_REMOVE) Then
'            'strore the virtual key code for later use.
'            iKeyCode = msgMessage.wParam
'           'translate the virtual key code into a char msg.
'            TranslateMessage msgMessage
'            PeekMessage msgMessage, lXLhwnd, WM_CHAR, _
'            WM_CHAR, PM_REMOVE
'           'for some obscure reason, the following
'          'keys are not trapped inside the event handler
'            'so we handle them here.
'            If iKeyCode = vbKeyBack Then SendKeys "{BS}"
'            If iKeyCode = vbKeyReturn Then SendKeys "{ENTER}"
'           'assume the cancel argument is False.
'            bCancel = False
'            'the VBA RaiseEvent statement does not seem to return ByRef arguments
'            'so we call a KeyPress routine rather than a propper event handler.
'            Sheet_KeyPress _
'            ByVal msgMessage.wParam, ByVal iKeyCode, ByVal Selection, bCancel
'            'if the key pressed is allowed post it to the application.
'            If bCancel = False Then
'                PostMessage _
'                lXLhwnd, msgMessage.Message, msgMessage.wParam, 0
'            End If
'        End If
'errHandler:
'        'allow the processing of other msgs.
'        DoEvents
'    Loop Until bExitLoop
'
'End Sub
'
'Sub StopKeyWatch()
'
'    'set this boolean flag to exit the above loop.
'    bExitLoop = True
'
'End Sub
'
'
''\\This example illustrates how to catch worksheet
''\\Key strokes in order to prevent entering numeric
''\\characters in the Range "A1:D10" .
'Private Sub Sheet_KeyPress _
'(ByVal KeyAscii As Integer, ByVal KeyCode As Integer, _
'ByVal Target As Range, Cancel As Boolean)
'
'    Const MSG As String = _
'    "Numeric Characters are not allowed in" & _
'    vbNewLine & "the Range:  """
'    Const Title As String = "Invalid Entry !"
'
'    If Not Intersect(Target, Range("A1:D10")) Is Nothing Then
'        If Chr(KeyAscii) Like "[0-9]" Then
'            MsgBox MSG & Range("A1:D10").Address(False, False) _
'            & """ .", vbCritical, Title
'            Cancel = True
'        End If
'    End If
'
'End Sub
'
'
''\\This example illustrates how to catch a worksheet
''\\KeyPress to prevent entering Alpha characters in
''\\the range "A1:D10" .
'
''Private Sub Sheet_KeyPress _
''(ByVal KeyAscii As Integer, ByVal KeyCode As Integer, _
''ByVal Target As Range, Cancel As Boolean)
''
''    Const MSG As String = "No Alpha-Characters are allowed in" & _
''    vbNewLine & "Range:  """
''    Const TITLE As String = "Invalid Entry !"
''
''    If Not Intersect(Target, Range("A1:D10")) Is Nothing Then
''        If Chr(KeyAscii) Like "[a-z]" Or _
''        Chr(KeyAscii) Like "[A-Z]" Then
''            MsgBox MSG & Range("A1:D10").Address(False, False) _
''            & """ .", vbCritical, TITLE
''            Cancel = True
''        End If
''    End If
''
''End Sub
'Public Sub DeleteAll()
'    Call DeleteOutputTab("Deal CF-")
'    Call DeleteOutputTab("HYPO-")
'    Call DeleteOutputTab("Rankings-")
'    Call DeleteOutputTab("RM-")
'    Call DeleteOutputTab("Compliance-")
'    Sheets("Run Model").Activate
'End Sub
'
'
'Public Sub GetAverages()
'    Dim lInputRange As Range
'    Dim lOutputrange As Range
'    Dim lInputRow As Long
'    Dim lOutputRow As Long
'    Dim lWorksheet As Worksheet
'    Dim i As Long
'    Dim lChart As Chart
'
'
'
'
'    Set lInputRange = ThisWorkbook.Sheets("RM-Credit Migration Stats").Range("B11")
'    Set lWorksheet = ThisWorkbook.Sheets.Add(After:=Sheets(Sheets.Count), Count:=1, Type:=xlWorksheet)
'    lWorksheet.Name = "RM-Chart Data"
'    lWorksheet.Tab.Color = 5287936
'    Set lOutputrange = lWorksheet.Range("B3")
'
'    Do While Len(lInputRange.Offset(lInputRow, 0).Value) > 0
'        Range(lOutputrange.Offset(lOutputRow, 0), lOutputrange.Offset(lOutputRow, 23)).Value = Range(lInputRange.Offset(lInputRow, 0), lInputRange.Offset(lInputRow, 23)).Value
'        lOutputRow = lOutputRow + 1
'        lInputRow = lInputRow + 11
'    Loop
'    Range(lOutputrange.Offset(-2, 0), lOutputrange.Offset(-2, 23)).Value = Range(lInputRange.Offset(-10, 0), lInputRange.Offset(-10, 23)).Value
'    Range(lOutputrange.Offset(-1, 0), lOutputrange.Offset(-1, 23)).Value = Range(lInputRange.Offset(-8, 0), lInputRange.Offset(-8, 23)).Value
'    Range(lOutputrange.Offset(-2, 0), lOutputrange.Offset(lOutputRow, 23)).Columns.AutoFit
'    Range(lOutputrange.Offset(-1, 1), lOutputrange.Offset(lOutputRow, 23)).Style = "Comma"
'    Range(lOutputrange.Offset(-1, 23), lOutputrange.Offset(lOutputRow, 23)).NumberFormat = "0.00%"
'
'    For i = 1 To lOutputRow
'        lOutputrange.Offset(lOutputRow + i + 1, 0).Value = i - 1
'        lOutputrange.Offset(lOutputRow + i + 1, 1).Value = lOutputrange.Offset(i - 2, 4).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 2).Value = lOutputrange.Offset(i - 2, 5).Value + lOutputrange.Offset(i - 2, 6).Value + lOutputrange.Offset(i - 2, 7).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 3).Value = lOutputrange.Offset(i - 2, 8).Value + lOutputrange.Offset(i - 2, 9).Value + lOutputrange.Offset(i - 2, 10).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 4).Value = lOutputrange.Offset(i - 2, 11).Value + lOutputrange.Offset(i - 2, 12).Value + lOutputrange.Offset(i - 2, 13).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 5).Value = lOutputrange.Offset(i - 2, 14).Value + lOutputrange.Offset(i - 2, 15).Value + lOutputrange.Offset(i - 2, 16).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 6).Value = lOutputrange.Offset(i - 2, 17).Value + lOutputrange.Offset(i - 2, 18).Value + lOutputrange.Offset(i - 2, 19).Value
'        lOutputrange.Offset(lOutputRow + i + 1, 7).Value = lOutputrange.Offset(i - 2, 20).Value
'    Next i
'    lOutputrange.Offset(lOutputRow + 1, 0).Value = "Period"
'    lOutputrange.Offset(lOutputRow + 1, 1).Value = "AAA"
'    lOutputrange.Offset(lOutputRow + 1, 2).Value = "AA"
'    lOutputrange.Offset(lOutputRow + 1, 3).Value = "A"
'    lOutputrange.Offset(lOutputRow + 1, 4).Value = "BBB"
'    lOutputrange.Offset(lOutputRow + 1, 5).Value = "BB"
'    lOutputrange.Offset(lOutputRow + 1, 6).Value = "B"
'    lOutputrange.Offset(lOutputRow + 1, 7).Value = "CCC"
'    Range(Range(lOutputrange.Offset(lOutputRow + 1, 1), lOutputrange.Offset(lOutputRow + 1, 7)), Range(lOutputrange.Offset(lOutputRow * 2 + 2, 1), lOutputrange.Offset(lOutputRow * 2 + 2, 7))).Style = "Comma"
'
'
'    Dim lTotalBal As Double
'    For i = 1 To lOutputRow
'        lTotalBal = Application.WorksheetFunction.sum(Range(lOutputrange.Offset(lOutputRow + i + 1, 1), lOutputrange.Offset(lOutputRow + i + 1, 7)))
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 0).Value = i - 1
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 1).Value = lOutputrange.Offset(i - 2, 4).Value / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 2).Value = (lOutputrange.Offset(i - 2, 5).Value + lOutputrange.Offset(i - 2, 6).Value + lOutputrange.Offset(i - 2, 7).Value) / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 3).Value = (lOutputrange.Offset(i - 2, 8).Value + lOutputrange.Offset(i - 2, 9).Value + lOutputrange.Offset(i - 2, 10).Value) / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 4).Value = (lOutputrange.Offset(i - 2, 11).Value + lOutputrange.Offset(i - 2, 12).Value + lOutputrange.Offset(i - 2, 13).Value) / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 5).Value = (lOutputrange.Offset(i - 2, 14).Value + lOutputrange.Offset(i - 2, 15).Value + lOutputrange.Offset(i - 2, 16).Value) / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 6).Value = (lOutputrange.Offset(i - 2, 17).Value + lOutputrange.Offset(i - 2, 18).Value + lOutputrange.Offset(i - 2, 19).Value) / lTotalBal
'        lOutputrange.Offset(lOutputRow * 2 + i + 3, 7).Value = (lOutputrange.Offset(i - 2, 20).Value) / lTotalBal
'    Next i
'    lOutputrange.Offset(lOutputRow * 2 + 3, 0).Value = "Period"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 1).Value = "AAA"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 2).Value = "AA"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 3).Value = "A"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 4).Value = "BBB"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 5).Value = "BB"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 6).Value = "B"
'    lOutputrange.Offset(lOutputRow * 2 + 3, 7).Value = "CCC"
'    Range(Range(lOutputrange.Offset(lOutputRow * 2 + 4, 1), lOutputrange.Offset(lOutputRow * 2 + 4, 7)), Range(lOutputrange.Offset(lOutputRow * 3 + 3, 1), lOutputrange.Offset(lOutputRow * 3 + 3, 7))).NumberFormat = "0.000%"
'
'    lWorksheet.Shapes.AddChart2(227, xlLine).Select
'    lWorksheet.ChartObjects(1).Activate
'    ActiveChart.SetSourceData Range(Range(lOutputrange.Offset(lOutputRow * 2 + 3, 0), lOutputrange.Offset(lOutputRow * 2 + 3, 7)), Range(lOutputrange.Offset(lOutputRow * 3 + 3, 1), lOutputrange.Offset(lOutputRow * 3 + 3, 7)))
'    ActiveChart.Location Where:=xlLocationAsNewSheet
'    ActiveChart.Name = "RM-RatingPercent"
'    ActiveChart.FullSeriesCollection(1).Delete
'    ActiveChart.FullSeriesCollection(1).XValues = Range(lOutputrange.Offset(lOutputRow * 2 + 4, 0), lOutputrange.Offset(lOutputRow * 3 + 3, 0))
'    ActiveChart.Axes(xlValue).TickLabels.NumberFormat = "0.000%"
'    ActiveChart.Tab.Color = 5287936
'
'
'
'
'    lWorksheet.Shapes.AddChart2(227, xlLine).Select
'    lWorksheet.ChartObjects(1).Activate
'    ActiveChart.SetSourceData Range(Range(lOutputrange.Offset(lOutputRow + 1, 0), lOutputrange.Offset(lOutputRow + 1, 7)), Range(lOutputrange.Offset(lOutputRow * 2 + 1, 0), lOutputrange.Offset(lOutputRow * 2 + 1, 7)))
'    ActiveChart.Location Where:=xlLocationAsNewSheet
'    ActiveChart.FullSeriesCollection(1).Delete
'    ActiveChart.FullSeriesCollection(1).XValues = Range(lOutputrange.Offset(lOutputRow * 1 + 2, 0), lOutputrange.Offset(lOutputRow * 2 + 2, 0))
'    ActiveChart.Name = "RM-RatingBal"
'    ActiveChart.Axes(xlValue).TickLabels.NumberFormat = "#,##0.00"
'    ActiveChart.Tab.Color = 5287936
'
'    lWorksheet.Shapes.AddChart2(227, xlLine).Select
'    lWorksheet.ChartObjects(1).Activate
'    ActiveChart.ChartArea.ClearContents
'    ActiveChart.SeriesCollection.NewSeries
'    ActiveChart.FullSeriesCollection(1).Name = lOutputrange.Offset(-2, 23).Value
'    ActiveChart.FullSeriesCollection(1).Values = Range(lOutputrange.Offset(-1, 23), lOutputrange.Offset(lOutputRow - 2, 23))
'    ActiveChart.FullSeriesCollection(1).XValues = Range(lOutputrange.Offset(-1, 0), lOutputrange.Offset(lOutputRow - 2, 0))
'    ActiveChart.Location Where:=xlLocationAsNewSheet
'    ActiveChart.Name = "RM-Period CDR"
'    ActiveChart.Tab.Color = 5287936
'End Sub
'Public Sub Test2()
'    Dim lAdame As LongPtr
'    Debug.Print 1 + 1
'End Sub
'

Public Sub Icecream()
    Dim ladam As Variant
    
    ReDim ladam(3)
    ladam(0) = "Adam"
    ladam(1) = "Chaz"
    ladam(2) = "Freeman"
    ladam(3) = "CFA"
    
    ReDim Preserve ladam(5)
End Sub
