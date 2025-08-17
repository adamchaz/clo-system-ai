Attribute VB_Name = "PerfMon"
Option Explicit

Public Sub AddPerfMOn()
    Dim VBProj As VBIDE.VBProject
    Dim vbComp As VBIDE.VBComponent
    Dim lCodeMod As VBIDE.CodeModule
    Dim lProcKind As VBIDE.vbext_ProcKind
    
    Dim lProcName As String
    Dim lLineNum As Long
    Dim lNumLines As Long
    
    Dim lrng As Range
    Dim i As Long
    Dim j As Long
    
    
    
    
    
    Set VBProj = ThisWorkbook.VBProject
    Set lrng = ThisWorkbook.Sheets("Sheet1").Range("A2")
    For Each vbComp In VBProj.VBComponents
        lrng.Offset(i, 0).Value = vbComp.Name
        lrng.Offset(i, 1).Value = ComponentTypeToString(vbComp.Type)
        Set lCodeMod = vbComp.CodeModule
        With lCodeMod
            lLineNum = .CountOfDeclarationLines + 1
            Do Until lLineNum >= .CountOfLines
                lProcName = .ProcOfLine(lLineNum, lProcKind)
                
                lrng.Offset(i, 0).Value = vbComp.Name
                lrng.Offset(i, 1).Value = ComponentTypeToString(vbComp.Type)
                lrng.Offset(i, 2).Value = lProcName
                lrng.Offset(i, 3).Value = ProcKindString(lProcKind)
                lrng.Offset(i, 4).Value = .ProcBodyLine(lProcName, lProcKind)
                lrng.Offset(i, 5).Value = .ProcCountLines(lProcName, lProcKind)
                lrng.Offset(i, 6).Value = .ProcStartLine(lProcName, lProcKind)
                If lrng.Offset(i, 0).Value <> lrng.Offset(i - 1, 0).Value Then
                    lrng.Offset(i, 7).Value = TotalCodeLinesInVBComponent(vbComp)
                End If
                lLineNum = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
                i = i + 1
            Loop
        End With
        
    Next vbComp
    
End Sub
Public Function ComponentTypeToString(ComponentType As VBIDE.vbext_ComponentType) As String
        Select Case ComponentType
            Case vbext_ct_ActiveXDesigner
                ComponentTypeToString = "ActiveX Designer"
            Case vbext_ct_ClassModule
                ComponentTypeToString = "Class Module"
            Case vbext_ct_Document
                ComponentTypeToString = "Document Module"
            Case vbext_ct_MSForm
                ComponentTypeToString = "UserForm"
            Case vbext_ct_StdModule
                ComponentTypeToString = "Code Module"
            Case Else
                ComponentTypeToString = "Unknown Type: " & CStr(ComponentType)
        End Select
    End Function
Public Function ProcKindString(ProcKind As VBIDE.vbext_ProcKind) As String
        Select Case ProcKind
            Case vbext_pk_Get
                ProcKindString = "Property Get"
            Case vbext_pk_Let
                ProcKindString = "Property Let"
            Case vbext_pk_Set
                ProcKindString = "Property Set"
            Case vbext_pk_Proc
                ProcKindString = "Sub Or Function"
            Case Else
                ProcKindString = "Unknown Type: " & CStr(ProcKind)
        End Select
End Function

    Public Function TotalLinesInProject(Optional VBProj As VBIDE.VBProject = Nothing) As Long
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' This returns the total number of lines in all components of the VBProject
    ' referenced by VBProj. If VBProj is missing, the VBProject of the ActiveWorkbook
    ' is used. Returns -1 if the VBProject is locked.
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
        Dim VBP As VBIDE.VBProject
        Dim vbComp As VBIDE.VBComponent
        Dim LineCount As Long
        
        If VBProj Is Nothing Then
            Set VBP = ActiveWorkbook.VBProject
        Else
            Set VBP = VBProj
        End If
        
        If VBP.Protection = vbext_pp_locked Then
            TotalLinesInProject = -1
            Exit Function
        End If
        
        For Each vbComp In VBP.VBComponents
            LineCount = LineCount + vbComp.CodeModule.CountOfLines
        Next vbComp
        
        TotalLinesInProject = LineCount
    End Function
        Public Function TotalCodeLinesInProject(VBProj As VBIDE.VBProject) As Long
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' This returns the total number of code lines (excluding blank lines and
    ' comment lines) in all VBComponents of VBProj. Returns -1 if VBProj
    ' is locked.
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
        
        Dim vbComp As VBIDE.VBComponent
        Dim LineCount As Long
        If VBProj.Protection = vbext_pp_locked Then
            TotalCodeLinesInProject = -1
            Exit Function
        End If
        For Each vbComp In VBProj.VBComponents
            LineCount = LineCount + TotalCodeLinesInVBComponent(vbComp)
        Next vbComp
        
        TotalCodeLinesInProject = LineCount
    End Function
    Public Sub GetTotalcodelines()
        Debug.Print TotalCodeLinesInProject(ThisWorkbook.VBProject)
    End Sub
    
    Public Function TotalCodeLinesInVBComponent(vbComp As VBIDE.VBComponent) As Long
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' This returns the total number of code lines (excluding blank lines and
    ' comment lines) in the VBComponent referenced by VBComp. Returns -1
    ' if the VBProject is locked.
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
        Dim n As Long
        Dim S As String
        Dim LineCount As Long
        
        If vbComp.Collection.Parent.Protection = vbext_pp_locked Then
            TotalCodeLinesInVBComponent = -1
            Exit Function
        End If
        
        With vbComp.CodeModule
            For n = 1 To .CountOfLines
                S = .Lines(n, 1)
                If Trim(S) = vbNullString Then
                    ' blank line, skip it
                ElseIf Left(Trim(S), 1) = "'" Then
                    ' comment line, skip it
                Else
                    LineCount = LineCount + 1
                End If
            Next n
        End With
        TotalCodeLinesInVBComponent = LineCount

End Function
Public Sub AddPerfCallsProj()
    Dim VBProj As VBIDE.VBProject
    Dim vbComp As VBIDE.VBComponent
    
    Set VBProj = ThisWorkbook.VBProject
    For Each vbComp In VBProj.VBComponents
        If vbComp.Type <> vbext_ct_Document And vbComp.Name <> "PerfMon" Then
            Call AddPrefMonCall(vbComp.Name)
        End If
    Next vbComp
End Sub
Public Sub DeletePerfCallsProj()
    Dim VBProj As VBIDE.VBProject
    Dim vbComp As VBIDE.VBComponent
    
    Set VBProj = ThisWorkbook.VBProject
    For Each vbComp In VBProj.VBComponents
        If vbComp.Type <> vbext_ct_Document And vbComp.Name <> "PerfMon" Then
            Call DeletePrefMonCall(vbComp.Name)
        End If
    Next vbComp
End Sub




Public Sub AddPrefMonCall(iVBComp As String)
    Dim VBProj As VBIDE.VBProject
    Dim vbComp As VBIDE.VBComponent
    Dim lCodeMod As VBIDE.CodeModule
    Dim lProcKind As VBIDE.vbext_ProcKind
    
    Dim lProcName As String
    Dim lStartLine As String
    Dim lStopLine As String
    Dim lLineNum As Long
    Dim lNumLines As Long
    Dim lInsertLine As Long
    Dim lLastLineProc As Long
    
    
    Dim lrng As Range
    Dim i As Long
    Dim j As Long
    Dim lVBCompName As String
    
    lVBCompName = iVBComp
    Set VBProj = ThisWorkbook.VBProject
    Set vbComp = VBProj.VBComponents.Item(lVBCompName)
    Set lCodeMod = vbComp.CodeModule
    With lCodeMod
        lLineNum = .CountOfDeclarationLines + 1
        Do Until lLineNum >= .CountOfLines
            lProcName = .ProcOfLine(lLineNum, lProcKind)
            'If lProcName = "LoadAssets" Then
                lLastLineProc = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
                lStartLine = "PerfMonProcStart " & Chr(34) & "VBAProject." & lVBCompName & "." & lProcName & Chr(34)
                lStopLine = "PerfMonProcEnd " & Chr(34) & "VBAProject." & lVBCompName & "." & lProcName & Chr(34)
                lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                Do While right(.Lines(lInsertLine, 1), 1) = "_"
                    lInsertLine = lInsertLine + 1
                Loop
                lInsertLine = lInsertLine + 1
                .InsertLines lInsertLine, lStartLine
                Select Case lProcKind
                Case vbext_pk_Get, vbext_pk_Let, vbext_pk_Set
                    Do Until .Find("End Property", lInsertLine, 1, lLastLineProc, 255) = False Or lInsertLine > lLastLineProc
                        .InsertLines lInsertLine, lStopLine
                        lInsertLine = lInsertLine + 2
                        If lInsertLine > lLastLineProc Then
                            Exit Do
                        End If
                    Loop
                Case vbext_pk_Proc
                    lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    Do Until .Find("End Sub", lInsertLine, 1, lLastLineProc, 255) = False
                        .InsertLines lInsertLine, lStopLine
                        lInsertLine = lInsertLine + 2
                        If lInsertLine > lLastLineProc Then
                            Exit Do
                        End If
                    Loop
                     
                    lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    Do Until .Find("End Function", lInsertLine, 1, lLastLineProc, 255) = False
                        .InsertLines lInsertLine, lStopLine
                        lInsertLine = lInsertLine + 2
                        If lInsertLine > lLastLineProc Then
                            Exit Do
                        End If
                    Loop
                     lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    Do Until .Find("Exit Sub", lInsertLine, 1, lLastLineProc, 255) = False
                        .InsertLines lInsertLine, lStopLine
                        lInsertLine = lInsertLine + 2
                        lLastLineProc = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
                        If lInsertLine > lLastLineProc Then
                            Exit Do
                        End If
                    Loop
                     lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    Do Until .Find("Exit Function", lInsertLine, 1, lLastLineProc, 255) = False
                        .InsertLines lInsertLine, lStopLine
                        lInsertLine = lInsertLine + 2
                        lLastLineProc = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
                        If lInsertLine > lLastLineProc Then
                            Exit Do
                        End If
                    Loop
                
                End Select
            'End If
            lLineNum = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
        Loop
    End With

End Sub
Public Sub DeletePrefMonCall(iVBComp As String)
    Dim VBProj As VBIDE.VBProject
    Dim vbComp As VBIDE.VBComponent
    Dim lCodeMod As VBIDE.CodeModule
    Dim lProcKind As VBIDE.vbext_ProcKind
    
    Dim lProcName As String
    Dim lStartLine As String
    Dim lStopLine As String
    Dim lLineNum As Long
    Dim lNumLines As Long
    Dim lInsertLine As Long
    Dim lLastLineProc As Long
    
    
    Dim lrng As Range
    Dim i As Long
    Dim j As Long
    Dim lVBCompName As String
    
    lVBCompName = iVBComp
    Set VBProj = ThisWorkbook.VBProject
    Set vbComp = VBProj.VBComponents.Item(lVBCompName)
    Set lCodeMod = vbComp.CodeModule
    With lCodeMod
        lLineNum = .CountOfDeclarationLines + 1
        Do Until lLineNum >= .CountOfLines
            lProcName = .ProcOfLine(lLineNum, lProcKind)
            'If lProcName = "LoadAssets" Then
                lLastLineProc = .CountOfLines
                lStartLine = "PerfMonProcStart " & Chr(34) & "VBAProject." & lVBCompName & "." & lProcName & Chr(34)
                lStopLine = "PerfMonProcEnd " & Chr(34) & "VBAProject." & lVBCompName & "." & lProcName & Chr(34)
                lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                Do Until .Find(lStartLine, lInsertLine, 1, lLastLineProc, 255) = False
                    .DeleteLines lInsertLine, 1
                    lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    lLastLineProc = .CountOfLines
                Loop
                lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                lLastLineProc = .CountOfLines
                Do Until .Find(lStopLine, lInsertLine, 1, lLastLineProc, 255) = False
                    .DeleteLines lInsertLine, 1
                    lInsertLine = .ProcBodyLine(lProcName, lProcKind)
                    lLastLineProc = .CountOfLines
                Loop
            'End If
            lLineNum = .ProcStartLine(lProcName, lProcKind) + .ProcCountLines(lProcName, lProcKind)
        Loop
    End With

End Sub
