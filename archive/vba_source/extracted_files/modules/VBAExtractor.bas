Attribute VB_Name = "VBAExtractor"
Option Explicit

' VBA Code Extraction Script
' This script automatically exports all VBA modules, classes, and forms
' Run this from within your Excel workbook's VBA editor

Public Sub ExtractAllVBACode()
    Dim wb As Workbook
    Dim vbComp As Object
    Dim exportPath As String
    Dim modulePath As String
    Dim classPath As String
    Dim formPath As String
    Dim sheetPath As String
    Dim fileName As String
    Dim fileExt As String
    Dim fso As Object
    Dim exportCount As Long
    
    ' Initialize file system object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set wb = ThisWorkbook
    
    ' Create base export directory
    exportPath = wb.Path & "\vba_extracted"
    If Not fso.FolderExists(exportPath) Then
        fso.CreateFolder exportPath
    End If
    
    ' Create subdirectories
    modulePath = exportPath & "\modules"
    classPath = exportPath & "\classes"
    formPath = exportPath & "\forms"
    sheetPath = exportPath & "\sheets"
    
    If Not fso.FolderExists(modulePath) Then fso.CreateFolder modulePath
    If Not fso.FolderExists(classPath) Then fso.CreateFolder classPath
    If Not fso.FolderExists(formPath) Then fso.CreateFolder formPath
    If Not fso.FolderExists(sheetPath) Then fso.CreateFolder sheetPath
    
    ' Loop through all VBA components
    For Each vbComp In wb.VBProject.VBComponents
        Select Case vbComp.Type
            Case 1 ' vbext_ct_StdModule - Standard Module
                fileName = vbComp.Name & ".bas"
                vbComp.Export modulePath & "\" & fileName
                exportCount = exportCount + 1
                Debug.Print "Exported Module: " & fileName
                
            Case 2 ' vbext_ct_ClassModule - Class Module
                fileName = vbComp.Name & ".cls"
                vbComp.Export classPath & "\" & fileName
                exportCount = exportCount + 1
                Debug.Print "Exported Class: " & fileName
                
            Case 3 ' vbext_ct_MSForm - UserForm
                fileName = vbComp.Name & ".frm"
                vbComp.Export formPath & "\" & fileName
                exportCount = exportCount + 1
                Debug.Print "Exported Form: " & fileName
                
            Case 100 ' vbext_ct_Document - Worksheet/Workbook
                ' Only export if there's actual code
                If vbComp.CodeModule.CountOfLines > 0 Then
                    fileName = vbComp.Name & ".cls"
                    vbComp.Export sheetPath & "\" & fileName
                    exportCount = exportCount + 1
                    Debug.Print "Exported Sheet Code: " & fileName
                End If
        End Select
    Next vbComp
    
    ' Create extraction summary
    Call CreateExtractionSummary(exportPath, exportCount)
    
    ' Open the export folder
    Shell "explorer.exe """ & exportPath & """", vbNormalFocus
    
    MsgBox "VBA Code Extraction Complete!" & vbNewLine & _
           "Exported " & exportCount & " files to:" & vbNewLine & _
           exportPath, vbInformation, "Extraction Complete"
End Sub

Private Sub CreateExtractionSummary(exportPath As String, exportCount As Long)
    Dim fso As Object
    Dim textFile As Object
    Dim summaryPath As String
    Dim wb As Workbook
    Dim vbComp As Object
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set wb = ThisWorkbook
    summaryPath = exportPath & "\EXTRACTION_SUMMARY.md"
    
    Set textFile = fso.CreateTextFile(summaryPath, True)
    
    ' Write summary header
    textFile.WriteLine "# VBA Code Extraction Summary"
    textFile.WriteLine ""
    textFile.WriteLine "**Workbook:** " & wb.Name
    textFile.WriteLine "**Extraction Date:** " & Format(Now, "yyyy-mm-dd hh:mm:ss")
    textFile.WriteLine "**Total Files Exported:** " & exportCount
    textFile.WriteLine ""
    
    ' Write directory structure
    textFile.WriteLine "## Directory Structure"
    textFile.WriteLine "```"
    textFile.WriteLine "vba_extracted/"
    textFile.WriteLine "+-- modules/     # Standard modules (.bas)"
    textFile.WriteLine "+-- classes/     # Class modules (.cls)"
    textFile.WriteLine "+-- forms/       # UserForms (.frm)"
    textFile.WriteLine "+-- sheets/      # Worksheet/Workbook code (.cls)"
    textFile.WriteLine "+-- EXTRACTION_SUMMARY.md"
    textFile.WriteLine "```"
    textFile.WriteLine ""
    
    ' List all components
    textFile.WriteLine "## Exported Components"
    textFile.WriteLine ""
    
    ' Standard Modules
    textFile.WriteLine "### Standard Modules (.bas)"
    For Each vbComp In wb.VBProject.VBComponents
        If vbComp.Type = 1 Then
            textFile.WriteLine "- " & vbComp.Name & ".bas"
        End If
    Next
    textFile.WriteLine ""
    
    ' Class Modules
    textFile.WriteLine "### Class Modules (.cls)"
    For Each vbComp In wb.VBProject.VBComponents
        If vbComp.Type = 2 Then
            textFile.WriteLine "- " & vbComp.Name & ".cls"
        End If
    Next
    textFile.WriteLine ""
    
    ' UserForms
    textFile.WriteLine "### UserForms (.frm)"
    For Each vbComp In wb.VBProject.VBComponents
        If vbComp.Type = 3 Then
            textFile.WriteLine "- " & vbComp.Name & ".frm"
        End If
    Next
    textFile.WriteLine ""
    
    ' Sheet Code
    textFile.WriteLine "### Sheet/Workbook Code (.cls)"
    For Each vbComp In wb.VBProject.VBComponents
        If vbComp.Type = 100 And vbComp.CodeModule.CountOfLines > 0 Then
            textFile.WriteLine "- " & vbComp.Name & ".cls (" & vbComp.CodeModule.CountOfLines & " lines)"
        End If
    Next
    textFile.WriteLine ""
    
    ' Add conversion notes
    textFile.WriteLine "## Conversion Notes"
    textFile.WriteLine ""
    textFile.WriteLine "### Priority Order for Python Conversion:"
    textFile.WriteLine "1. **Classes first** - Core business logic (Asset.cls, LiabOutput.cls, etc.)"
    textFile.WriteLine "2. **Utility modules** - Helper functions and calculations"
    textFile.WriteLine "3. **Main modules** - User interface and orchestration logic"
    textFile.WriteLine "4. **Sheet code** - Excel-specific functionality"
    textFile.WriteLine ""
    textFile.WriteLine "### Key Dependencies to Consider:"
    textFile.WriteLine "- Excel object model (Workbooks, Worksheets, Ranges)"
    textFile.WriteLine "- VBA Collection and Dictionary objects"
    textFile.WriteLine "- File I/O operations"
    textFile.WriteLine "- Mathematical and financial functions"
    textFile.WriteLine ""
    textFile.WriteLine "### Next Steps:"
    textFile.WriteLine "1. Review extracted code for dependencies"
    textFile.WriteLine "2. Start with class modules for core business logic"
    textFile.WriteLine "3. Create Python equivalents using FastAPI/SQLAlchemy"
    textFile.WriteLine "4. Test each converted module individually"
    
    textFile.Close
    Set textFile = Nothing
    Set fso = Nothing
End Sub

' Helper function to enable macro security if needed
Public Sub CheckMacroSecurity()
    ' This function provides guidance on macro security settings
    ' that may prevent the extraction script from running
    
    Dim msg As String
    msg = "VBA Code Extraction Requirements:" & vbNewLine & vbNewLine
    msg = msg & "1. Macro security must allow VBA execution" & vbNewLine
    msg = msg & "2. Trust access to VBA project object model must be enabled" & vbNewLine & vbNewLine
    msg = msg & "To enable VBA project access:" & vbNewLine
    msg = msg & "File ? Options ? Trust Center ? Trust Center Settings ? " & vbNewLine
    msg = msg & "Macro Settings ? Check 'Trust access to the VBA project object model'" & vbNewLine & vbNewLine
    msg = msg & "Would you like to run the extraction script now?"
    
    If MsgBox(msg, vbYesNo + vbInformation, "VBA Extraction Setup") = vbYes Then
        Call ExtractAllVBACode
    End If
End Sub

