VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} FProgressBarIFace 
   Caption         =   "Professional Excel Development"
   ClientHeight    =   1065
   ClientLeft      =   45
   ClientTop       =   330
   ClientWidth     =   4110
   OleObjectBlob   =   "FProgressBarIFace.frx":0000
   ShowModal       =   0   'False
End
Attribute VB_Name = "FProgressBarIFace"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

'
' Description:  Displays a modeless progress bar on the screen,
'               by implementing the IProgressBar interface
'
' Authors:      Rob Bovey, www.appspro.com
'               Stephen Bullen, www.oaltd.co.uk
'
Option Explicit

' **************************************************************
' Interface Declarations Follow
' **************************************************************

'Implement the interface
Implements IProgressBar


' **************************************************************
' Module-level variables to store the property values
' **************************************************************
Dim mdMin As Double
Dim mdMax As Double
Dim mdProgress As Double
Dim mdLastPerc As Double
Dim mlhWnd As Long
Dim mAppWnd As Long

' **************************************************************
' Module Constant Declarations Follow
' **************************************************************
Private Const GWL_STYLE = (-16)
Private Const WS_SYSMENU = &H80000

' **************************************************************
' Module DLL Declarations Follow
' **************************************************************

'Windows API calls to remove the [x] from the top-right of the form
Private Declare PtrSafe Function FindWindow Lib "user32" Alias "FindWindowA" (ByVal lpClassName As String, ByVal lpWindowName As String) As Long
Private Declare PtrSafe Function GetWindowLong Lib "user32" Alias "GetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long) As Long
Private Declare PtrSafe Function SetWindowLong Lib "user32" Alias "SetWindowLongA" (ByVal hwnd As Long, ByVal nIndex As Long, ByVal dwNewLong As Long) As Long

'Windows API calls to bring the progress bar form to the front of other modeless forms
Private Declare PtrSafe Function GetForegroundWindow Lib "user32" () As Long
Private Declare PtrSafe Function GetWindowThreadProcessId Lib "user32" (ByVal hwnd As Long, ByRef lpdwProcessId As Long) As Long
Private Declare PtrSafe Function SetForegroundWindow Lib "user32" (ByVal hwnd As Long) As Long

Private clsLock As Boolean
Private clsPassword As String
Private clsCancel As Boolean








Private Sub CommandButton1_Click()
    'Call SetCancel
    Dim lResult As VbMsgBoxResult
    
    lResult = MsgBox("Would you like to cancel current simulation", vbYesNo, "Cancel")
    If lResult = vbYes Then
        clsCancel = True
    End If
End Sub

Private Sub fraInside_Click()

End Sub


Private Sub fraOutside_Click()

End Sub

Private Property Get IProgressBar_Cancel() As Boolean
    IProgressBar_Cancel = clsCancel
End Property

' **************************************************************
' Implementation of IProgressBar Follows
' **************************************************************

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Let the calling routine set/get the caption of the form
'
' Arguments:    RHS         The new title
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Property Let IProgressBar_Title(ByVal RHS As String)
    Me.Caption = RHS
    RemoveCloseButton
End Property

Private Property Get IProgressBar_Title() As String
    IProgressBar_Title = Me.Caption
End Property


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Let the calling routine set/get the descriptive text on the form
'
' Arguments:    RHS         The new text
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Property Let IProgressBar_Text(ByVal RHS As String)

    If RHS <> lblMessage.Caption Then
        lblMessage.Caption = RHS

        'Refresh the form if it's being shown
        If Me.Visible Then
            Me.Repaint
            BringToFront
        End If
    End If

End Property

Private Property Get IProgressBar_Text() As String
    IProgressBar_Text = lblMessage.Caption
End Property


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Let the calling routine set/get the Minimum scale for the progress bar
'
' Arguments:    RHS         The new value
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Property Let IProgressBar_Min(ByVal RHS As Double)
    mdMin = RHS
End Property

Private Property Get IProgressBar_Min() As Double
    IProgressBar_Min = mdMin
End Property


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Let the calling routine set the Maximum scale for the progress bar
'
' Arguments:    RHS         The new value
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Property Let IProgressBar_Max(ByVal RHS As Double)
    mdMax = RHS
End Property

Private Property Get IProgressBar_Max() As Double
    IProgressBar_Max = mdMax
End Property


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Set the progress bar's progress
'
' Arguments:    RHS         The new value
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Property Let IProgressBar_Progress(ByVal RHS As Double)

    Dim dPerc As Double

    mdProgress = RHS

    'Calculate the progress percentage
    If mdMax = mdMin Then
        dPerc = 0
    Else
        dPerc = Abs((RHS - mdMin) / (mdMax - mdMin))
    End If

    'Only update the form every 0.5% change
    If Abs(dPerc - mdLastPerc) > 0.005 Then
        mdLastPerc = dPerc

        'Set the width of the inside frame, rounding to the nearest pixel
        fraInside.Width = Int(lblBack.Width * dPerc / 0.75 + 1) * 0.75

        'Set the captions for the blue-on-white and white-on-blue texts.
        lblBack.Caption = Format(dPerc, "0%")
        lblFront.Caption = Format(dPerc, "0%")

        'Refresh the form if it's being shown
        If Me.Visible Then
            Me.Repaint
            BringToFront
        End If

        'Allow Cancel click to be processed at each update
        DoEvents
    End If

End Property

Private Property Get IProgressBar_Progress() As Double
    IProgressBar_Progress = mdProgress
End Property


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Show the progress form
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub IProgressBar_Show()

'Remove the [x] close button on the form
    RemoveCloseButton

    'Show the form modelessly
    Me.Show vbModeless

End Sub


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Hide the form
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub IProgressBar_Hide()
    Me.Hide
End Sub

Private Sub IProgressBar_HideCancelButton()
    CommandButton1.Visible = False
End Sub
Private Sub IProgressBar_ShowCancelButton()
    CommandButton1.Visible = True
End Sub



Private Sub lblBack_Click()

End Sub

Private Sub lblFront_Click()

End Sub

Private Sub lblMessage_Click()

End Sub

' **************************************************************
' Form and Control Event Handlers Follow
' **************************************************************

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Initialise the form to show a blank text and 0% complete
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub UserForm_Initialize()

    On Error Resume Next
    Dim topoffset As Integer
    Dim leftoffset As Integer
    

    'Get the form's window handle, for use in API calls
    Me.Caption = "ProExcelProgressBar"
    mlhWnd = FindWindow(vbNullString, Me.Caption)
    mAppWnd = FindWindow(vbNullString, ThisWorkbook.Name)

    'Assume an initial progress of 0-100
    mdMin = 0
    mdMax = 100

    lblMessage.Caption = ""
    Me.Caption = ""
    RemoveCloseButton
    
    topoffset = (Application.UsableHeight / 2) - Me.Height / 2
    leftoffset = (Application.UsableWidth / 2) - Me.Width / 2
    Me.Top = Application.Top + topoffset
    Me.Left = Application.Left + leftoffset
'

    'Print Me.Top

End Sub


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Ignore clicking the [x] on the dialog (which shouldn't be visible anyway!)
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub UserForm_QueryClose(ByRef Cancel As Integer, ByRef CloseMode As Integer)

    If CloseMode = vbFormControlMenu Then Cancel = True

End Sub


' **************************************************************
' Private Helper Procedures Follow
' **************************************************************

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Routine to remove the [x] from the top-right of the form
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub RemoveCloseButton()

    Dim lStyle As Long

    'Remove the close button on the form
    lStyle = GetWindowLong(mlhWnd, GWL_STYLE)

    If lStyle And WS_SYSMENU > 0 Then
        SetWindowLong mlhWnd, GWL_STYLE, (lStyle And Not WS_SYSMENU)
    End If

End Sub


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' Comments: Routine to bring the form to the front of other modeless forms
'
' Arguments:    None
'
' Date          Developer       Action
' --------------------------------------------------------------
' 08 Jun 08     Stephen Bullen  Created
'
Private Sub BringToFront()

    Dim lFocusThread As Long
    Dim lThisThread As Long

    'Does the window being viewed by the user belong to the same thread as the progress bar?
    '(i.e. are they still looking at this instance of Excel)
    lFocusThread = GetWindowThreadProcessId(GetForegroundWindow(), 0)
    lThisThread = GetWindowThreadProcessId(mlhWnd, 0)

    If lFocusThread = lThisThread Then
        'The threads are the same, so force the progress bar in front of other modeless dialogs
        SetForegroundWindow mlhWnd
    Else
        'Not looking at Excel, so yield control to the app they're using
        '(and allow them to switch back to Excel)
        DoEvents
    End If

End Sub




