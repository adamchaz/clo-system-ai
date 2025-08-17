VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Fees"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
Private clsFeeName As String
Private clsFeeType As String
Private clsIntonFee As Boolean
Private clsIntSpread As Double
Private clsFeePercentage As Double   'clsfixedamount+clsfeebais*clsfeePercentage
Private clsFixedAmount As Double
Private clsDayCount As DayCount
Private clsUnpaidFee As Double


Private clsPeriod As Long
Private clsBegBasis As Double
Private clsEndBasis As Double

'Data Storage
Private clsFeeBasis() As Double
Private clsBegBalance() As Double
Private clsFeeAccrued() As Double
Private clsFeePaid() As Double
Private clsEndBalance() As Double
Private clsLastperiod As Long
Public Property Get Name() As String
    Name = clsFeeName
End Property
Public Property Get FeeAccrued() As Double
    FeeAccrued = clsFeeAccrued(clsPeriod)
End Property
Public Sub DealSetup(iNumofPayments As Long, iBegBasis As Double)
     ReDim clsFeeBasis(iNumofPayments)
     ReDim clsBegBalance(iNumofPayments)
     ReDim clsFeeAccrued(iNumofPayments)
     ReDim clsFeePaid(iNumofPayments)
     ReDim clsEndBalance(iNumofPayments)
    
    clsBegBasis = iBegBasis
    clsBegBalance(1) = clsUnpaidFee
    clsPeriod = 1
    
End Sub



Public Sub Setup(iFeeName As String, iFeeType As String, iFeePercentage As Double, iFeeFixed As Double, idaycount As DayCount, IInfonFeee As Boolean, iIntSpread As Double, iUnpaidFee As Double)
    clsFeeName = iFeeName
    clsFeeType = iFeeType
    clsFeePercentage = iFeePercentage
    clsFixedAmount = iFeeFixed
    clsDayCount = idaycount
    clsIntonFee = IInfonFeee
    clsIntSpread = iIntSpread
    clsUnpaidFee = iUnpaidFee
End Sub
Public Function Output() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastperiod, 4)
    lOutput(0, 0) = "Fee Basis"
    lOutput(0, 1) = "Beg Balance"
    lOutput(0, 2) = "Fee Accrued"
    lOutput(0, 3) = "Fee Paid"
    lOutput(0, 4) = "End Balance"
    
    For i = 1 To clsLastperiod
        lOutput(i, 0) = clsFeeBasis(i)
        lOutput(i, 1) = clsBegBalance(i)
        lOutput(i, 2) = clsFeeAccrued(i)
        lOutput(i, 3) = clsFeePaid(i)
        lOutput(i, 4) = clsEndBalance(i)
    Next i
    
    Output = lOutput
    
End Function

Public Sub Calc(iBegDate As Date, iEndDate As Date, iEndFeeBasis As Double, iLIBOR As Double)

    If iEndFeeBasis > 0 Then
        clsEndBasis = iEndFeeBasis
        Select Case UCase(clsFeeType)
        
        Case "BEGINNING"
            If clsFeePercentage > 0 Then
                clsFeeBasis(clsPeriod) = clsBegBasis
            End If
            clsFeeAccrued(clsPeriod) = (clsBegBasis * clsFeePercentage + clsFixedAmount) * DateFraction(iBegDate, iEndDate, clsDayCount)
        Case "AVERAGE"
            If clsFeePercentage > 0 Then
                clsFeeBasis(clsPeriod) = ((clsBegBasis + clsEndBasis) / 2)
            End If
             clsFeeAccrued(clsPeriod) = (((clsBegBasis + clsEndBasis) / 2) * clsFeePercentage + clsFixedAmount) * DateFraction(iBegDate, iEndDate, clsDayCount)
        End Select
        If clsIntonFee Then
            clsFeeAccrued(clsPeriod) = clsFeeAccrued(clsPeriod) + clsUnpaidFee * (iLIBOR + clsIntSpread) * DateFraction(iBegDate, iEndDate, clsDayCount)
        End If
        clsLastperiod = clsPeriod
    End If
    
    
End Sub

Public Sub PayFee(ByRef iAmount As Double)
    Dim lTotalAmountDue As Double
    
    lTotalAmountDue = clsBegBalance(clsPeriod) + clsFeeAccrued(clsPeriod) - clsFeePaid(clsPeriod)
    If iAmount > lTotalAmountDue Then
        clsFeePaid(clsPeriod) = clsFeePaid(clsPeriod) + lTotalAmountDue
        iAmount = iAmount - lTotalAmountDue
    Else
        clsFeePaid(clsPeriod) = clsFeePaid(clsPeriod) + iAmount
        iAmount = 0
    End If


End Sub

Public Sub Rollfoward()

   clsEndBalance(clsPeriod) = clsBegBalance(clsPeriod) + clsFeeAccrued(clsPeriod) - clsFeePaid(clsPeriod)
    If clsPeriod + 1 <= UBound(clsFeeBasis) Then
        clsBegBasis = clsEndBasis
        clsBegBalance(clsPeriod + 1) = clsEndBalance(clsPeriod)
    End If
    clsPeriod = clsPeriod + 1
End Sub

Public Function FeePaid() As Double
    Dim lTotal As Double
    Dim i As Long
    For i = LBound(clsFeePaid) To UBound(clsFeePaid)
        lTotal = lTotal + clsFeePaid(i)
    Next i
    FeePaid = lTotal
End Function

