VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} UserForm1 
   Caption         =   "UserForm1"
   ClientHeight    =   4935
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   4665
   OleObjectBlob   =   "UserForm1.frx":0000
End
Attribute VB_Name = "UserForm1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

Option Explicit
Public mListofDeals As Dictionary
Public mSelectListofDeals As Dictionary
Public mCurrList As Dictionary
Public mCancel As Boolean
Private mIncludeAll As Boolean


Private Sub CommandButton1_Click()
    Dim i As Long
    Dim lNumItem As Long
    Set mSelectListofDeals = New Dictionary
    With ListBox1
        If .Selected(0) Then
            Set mSelectListofDeals = mListofDeals
            'mListofDeals.Remove (" ")
        Else
            Set mSelectListofDeals = New Dictionary
            For i = 1 To .ListCount - 1
                If .Selected(i) And Len(.List(i)) > 0 Then
                    lNumItem = lNumItem + 1
                    mSelectListofDeals.Add .List(i), lNumItem
                End If
            Next i
        End If
    End With
    Me.Hide
End Sub

Private Sub CommandButton2_Click()
    Me.Hide
    mCancel = True
    ListBox1.Value = ""
End Sub

Private Sub ListBox1_Click()

End Sub

Private Sub ListBox1_KeyDown(ByVal KeyCode As MSForms.ReturnInteger, ByVal Shift As Integer)

End Sub

Private Sub TextBox1_Change()

End Sub

Private Sub TextBox1_KeyUp(ByVal KeyCode As MSForms.ReturnInteger, ByVal Shift As Integer)
    Dim ltext As String
    Dim lValues As Variant
    Dim i As Long
    Dim lFilterList As Dictionary
    Set lFilterList = New Dictionary

    ltext = TextBox1.Value
    lValues = mListofDeals.Keys
    For i = 0 To UBound(lValues)
        If InStr(UCase(lValues(i)), UCase(ltext)) > 0 Then
            lFilterList.Add lValues(i), i
        End If
    Next i

    For i = 0 To ListBox1.ListCount - 1
        ListBox1.RemoveItem 0
    Next i
    lValues = lFilterList.Keys
    If mIncludeAll = True Then
        ListBox1.AddItem "ALL"
    End If
    For i = 0 To lFilterList.Count - 1
        ListBox1.AddItem lValues(i)
        If mCurrList.Exists(lValues(i)) Then

            ListBox1.Selected(i + 1) = True
            
        End If
    Next i
    ListBox1.AddItem " "
    
    
    
End Sub

Private Sub UserForm_Activate()
    Call ResizeUserForm
End Sub

Public Sub init()
    
    Dim lNumOfDeals As Long
    Dim lDealNames As Variant
    Dim lMaxDealNameLength As Long
    Dim i As Long
    Set mSelectListofDeals = New Dictionary
    If ListBox1.ListCount > 0 Then
        For i = 0 To ListBox1.ListCount - 1
            ListBox1.RemoveItem 0
        Next i
    End If
    TextBox1.Visible = True
    TextBox1.Value = ""
    ListBox1.Visible = True
    ListBox1.MultiSelect = fmMultiSelectMulti
    UserForm1.Caption = "Select Deal to Run"
    lNumOfDeals = Me.mListofDeals.Count
    lDealNames = mListofDeals.Keys
    ListBox1.AddItem "All"
    For i = 0 To lNumOfDeals - 1
        If Len(lDealNames(i)) > lMaxDealNameLength Then lMaxDealNameLength = Len(lDealNames(i))
        ListBox1.AddItem lDealNames(i)
    Next i
    ListBox1.AddItem " "
    mCancel = False
    mIncludeAll = True
    Set mCurrList = New Dictionary
End Sub

Private Sub ResizeUserForm()
    Dim lNumOfDeals As Long
    Dim lMaxLengthofDealName As Long
    Dim i As Long
    lNumOfDeals = ListBox1.ListCount
    For i = 0 To lNumOfDeals - 1
        If lMaxLengthofDealName <= Len(ListBox1.List(i)) Then lMaxLengthofDealName = Len(ListBox1.List(i))
    Next i
    If lMaxLengthofDealName <= 42 Then lMaxLengthofDealName = 42
    If lNumOfDeals <= 20 Then lNumOfDeals = 20
    If lNumOfDeals >= 40 Then lNumOfDeals = 40
    UserForm1.Width = lMaxLengthofDealName * 5.5
    UserForm1.Height = lNumOfDeals * 10 + 35
    ListBox1.Width = lMaxLengthofDealName * 5.3
    ListBox1.Height = lNumOfDeals * 10 - 80
    TextBox1.Width = lMaxLengthofDealName * 5.3
    CommandButton1.Top = lNumOfDeals * 10 - 35
    CommandButton2.Top = lNumOfDeals * 10 - 35
End Sub
Public Sub initA6()
    Dim lNumOfDeals As Long
    Dim lDealNames As Variant
    Dim lMaxDealNameLength As Long
    Dim i As Long
    Set mSelectListofDeals = New Dictionary
    If ListBox1.ListCount > 0 Then
        For i = 0 To ListBox1.ListCount - 1
            ListBox1.RemoveItem 0
        Next i
    End If
    ListBox1.Visible = True
    ListBox1.MultiSelect = fmMultiSelectSingle
    UserForm1.TextBox1.Visible = False
    UserForm1.Caption = "Select Deal"
    UserForm1.CommandButton1.Caption = "OK"
    lNumOfDeals = Me.mListofDeals.Count
    lDealNames = mListofDeals.Keys
    For i = 0 To lNumOfDeals - 1
        If Len(lDealNames(i)) > lMaxDealNameLength Then lMaxDealNameLength = Len(lDealNames(i))
        ListBox1.AddItem lDealNames(i)
    Next i
    ListBox1.AddItem " "
    Set mCurrList = New Dictionary

End Sub
Private Sub ListBox1_MouseUp(ByVal Button As Integer, ByVal Shift As Integer, ByVal x As Single, ByVal y As Single)
    Dim i As Long
    For i = 0 To ListBox1.ListCount - 1
        If ListBox1.Selected(i) Then
            If Not (mCurrList.Exists(ListBox1.List(i))) Then
                mCurrList.Add ListBox1.List(i), 1
            End If
        Else
            If mCurrList.Exists(ListBox1.List(i)) Then
                mCurrList.Remove ListBox1.List(i)
            End If
        End If
    Next i
End Sub

Private Sub UserForm_Initialize()
    Dim ltopoffset As Long
    Dim lleftoffset As Long

    ltopoffset = (Application.UsableHeight / 2) - Me.Height / 2
    lleftoffset = (Application.UsableWidth / 2) - Me.Width / 2
    Me.Top = Application.Top + ltopoffset
    Me.Left = Application.Left + lleftoffset
End Sub
