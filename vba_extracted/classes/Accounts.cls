VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Accounts"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit

Private clsPrincipal As Double
Private clsInterest As Double

Public Property Get InterestProceeds() As Double
    InterestProceeds = clsInterest
End Property

Public Property Get PrincipalProceeds() As Double
    PrincipalProceeds = clsPrincipal
End Property
Public Property Get TotalProceeds() As Double
    TotalProceeds = clsInterest + clsPrincipal
End Property

Public Sub Add(iCashType As CashType, iAmount As Double)
    If iCashType = Interest Then
        clsInterest = clsInterest + iAmount
    ElseIf iCashType = Principal Then
        clsPrincipal = clsPrincipal + iAmount
    End If
End Sub


