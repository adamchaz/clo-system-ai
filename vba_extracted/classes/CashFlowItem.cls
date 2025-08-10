VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CashFlowItem"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Private clsPaymentdate As Date
Private clsInt As Double
Private clsSchedPrin As Double
Private ClsUnschedPrin As Double
Private clsRecoveries As Double
Private clsNetLoss As Double
Private clsTotalCash As Double

Public Property Get PaymentDate() As Date
    PaymentDate = clsPaymentdate
End Property
Public Property Let PaymentDate(iDate As Date)
    clsPaymentdate = iDate
End Property

Public Property Get Interest() As Double
    Interest = clsInt
End Property
Public Property Let Interest(iValue As Double)
    clsInt = iValue
End Property

Public Property Get SchedPrincipal() As Double
    SchedPrincipal = clsSchedPrin
End Property
Public Property Let SchedPrincipal(iValue As Double)
    clsSchedPrin = iValue
End Property

Public Property Get UnSchedPrincipal() As Double
    UnSchedPrincipal = ClsUnschedPrin
End Property
Public Property Let UnSchedPrincipal(iValue As Double)
    ClsUnschedPrin = iValue
End Property
Public Property Get Recoveries() As Double
    Recoveries = clsRecoveries
End Property
Public Property Let Recoveries(iValue As Double)
    clsRecoveries = iValue
End Property

Public Property Get Netloss() As Double
    Netloss = clsNetLoss
End Property
Public Property Let Netloss(iValue As Double)
    clsNetLoss = iValue
End Property

Public Property Get Total() As Double
    Total = clsTotalCash
End Property
Public Property Let Total(iValue As Double)
    clsTotalCash = iValue
End Property
