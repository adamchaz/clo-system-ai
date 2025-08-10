Attribute VB_Name = "MatrixMath"
Option Explicit
Option Private Module
'This code is almost identical to what is written from www.spreadsheetadvice.com. It has been rerwriiten to use datatypes instead of variants.
'In general I hate variants.
'This code fores all matrix to start at 1. This is mainly for consistent with the visualization of an matrix
'This will assume all matrix are square



Public Function ConverToVariant(iMat() As Double) As Variant
    Dim lVarOUt As Variant
    Dim i, j As Long
    ReDim lVarOUt(1 To UBound(iMat, 1), 1 To UBound(iMat, 2))
    For i = 1 To UBound(iMat, 1)
        For j = 1 To UBound(iMat, 2)
            lVarOUt(i, j) = iMat(i, j)
        Next j
    Next i
    ConverToVariant = lVarOUt

End Function
Public Function ConvertToArry(iVar As Variant) As Double()
    Dim i, j, lRows, lcol As Long
    Dim lMatOut() As Double
    ReDim lMatOut(1 To UBound(iVar, 1), 1 To UBound(iVar, 2))
    For i = 1 To UBound(iVar, 1)
        For j = 1 To UBound(iVar, 2)
            lMatOut(i, j) = iVar(i, j)
        Next j
    Next i
    ConvertToArry = lMatOut
End Function
Public Function MatrixID(iOrder As Long) As Double()
 Dim lIdenity() As Double
 ReDim lIdenity(1 To iOrder, 1 To iOrder)
 Dim i, j As Long
 
 For i = LBound(lIdenity) To UBound(lIdenity)
    lIdenity(i, i) = 1
 Next i
 
 MatrixID = lIdenity
End Function

Public Function MatrixMultiply(iMat1() As Double, iMat2() As Double) As Double()
    'Not a complete matrix multiplication program
    'Assumes a mat1 is a square matrix and imat is a square matrix or a 1 dimentional matirx
    Dim lOutMatrix() As Double
    Dim i, j, k As Long
    Dim lNumRows As Long
    Dim lNumColumns As Long
    
    lNumRows = UBound(iMat1, 1)
    lNumColumns = UBound(iMat2, 2)
    ReDim lOutMatrix(1 To lNumRows, 1 To lNumColumns)
    
    For i = 1 To lNumRows
        For j = 1 To lNumColumns
            For k = 1 To lNumRows
               lOutMatrix(i, j) = lOutMatrix(i, j) + iMat1(i, k) * iMat2(k, j)
            Next k
        Next j
    Next i
    
    MatrixMultiply = lOutMatrix

End Function
Public Function MatrixInverse(iMat() As Double) As Double()
    Dim lOutMat() As Double
    Dim lNumRows As Long
    
    lNumRows = UBound(iMat, 1)
    ReDim lOutMat(1 To lNumRows, 1 To lNumRows)
    Call sub_m_inv(iMat, lOutMat)
    
    MatrixInverse = lOutMat
End Function

Sub sub_m_inv(A() As Double, y() As Double)
'************************************************
'* Input: square matrix a()
'* Output: inverse in y()
'************************************************

Dim n As Long, i As Long, j As Long, inx() As Long, k As Long
Dim col() As Double, x() As Double, D As Double, Res() As Double
n = UBound(A(), 1)
ReDim x(1 To n, 1 To n), col(1 To n), Res(1 To n)
ReDim inx(1 To n)
For i = 1 To n
    For j = 1 To n
        x(i, j) = A(i, j)
    Next j
Next i

Call sub_ludcomp(x(), inx(), D)
For j = 1 To n
    For i = 1 To n
        col(i) = 0
    Next i
    col(j) = 1
    Call sub_lubacks(x(), inx(), col())

    For i = 1 To n
        Res(i) = 0
        If i = j Then Res(i) = -1
        For k = 1 To n
            Res(i) = Res(i) + A(i, k) * col(k)
        Next k
    Next i
    Call sub_lubacks(x(), inx(), Res())
    For i = 1 To n
        y(i, j) = col(i) - Res(i)
    Next i
Next j
End Sub

Sub sub_ludcomp(A() As Double, inx() As Long, D As Double)
'***************************************************
'* The matrix A() is replaced by the LU decomposition of a rowwise permutation of itself.
'* inx() is an output vector that records the row permutation performed;
'* d is output as +1 if the number of row interchanges was even, otherwise: d=-1.
'*
'* The algorithm follows fairly closely an algorithm published in the book "Numerical Recipes in C"
'***************************************************

Const tiny = 1E-20
Dim i As Long, imaxim As Long, j As Long, k As Long, n As Long
Dim big As Double, dum As Double, sum As Double, temp As Double
Dim viv() As Double

n = UBound(A(), 1)
ReDim viv(n)
D = 1
For i = 1 To n
    big = 0
    For j = 1 To n
        temp = Abs(A(i, j))
        If temp > big Then big = temp
    Next j
    If big = 0 Then
        Error.Raise 5
        Exit Sub
    End If
    viv(i) = 1 / big
Next i
For j = 1 To n
    For i = 1 To j - 1
        sum = A(i, j)
        For k = 1 To i - 1
            sum = sum - A(i, k) * A(k, j)
        Next k
        A(i, j) = sum
    Next i
    big = 0
    For i = j To n
        sum = A(i, j)
        For k = 1 To j - 1
            sum = sum - A(i, k) * A(k, j)
        Next k
        A(i, j) = sum
        dum = viv(i) * Abs(sum)
        If dum >= big Then
            big = dum
            imaxim = i
        End If
    Next i
    If j <> imaxim Then
        For k = 1 To n
            dum = A(imaxim, k)
            A(imaxim, k) = A(j, k)
            A(j, k) = dum
        Next k
        D = -D
        viv(imaxim) = viv(j)
    End If
    inx(j) = imaxim
    If A(j, j) = 0 Then
        Error.Raise 5
        Exit Sub
    End If
    If j <> n Then
        dum = 1 / A(j, j)
        For i = j + 1 To n
            A(i, j) = dum * A(i, j)
        Next i
    End If
Next j
End Sub
'
Sub sub_lubacks(A() As Double, inx() As Long, b() As Double)
'************************************************************
'* Solves the set of n linear equations C·X = d. Here A() is the LU decomposition of the matrix C,
'* as determined by the procedure ludcomp.
'* inx() is a permutation vector produced by ludcomp.
'* b() is input as the RHS vector d, and returns the solution vector X.
'*
'* The algorithm follows fairly closely an algorithm published in the book "Numerical Recipes in C"
'***************************************************

Dim i As Long, ii As Long, ip As Long, j As Long, n As Long
Dim sum As Double
n = UBound(A(), 1)
ii = 0
For i = 1 To n
    ip = inx(i)
    sum = b(ip)
    b(ip) = b(i)
    If ii > 0 Then
        For j = ii To i - 1
            sum = sum - A(i, j) * b(j)
        Next j
    ElseIf sum > 0 Then
        ii = i
    End If
    b(i) = sum
Next i
For i = n To 1 Step -1
    sum = b(i)
    For j = i + 1 To n
        sum = sum - A(i, j) * b(j)
    Next j
    b(i) = sum / A(i, i)
Next i
End Sub

Public Function MatrixABS(iMat() As Double) As Double
    Dim lOutDBL As Double
    Dim lNumRows As Long
    Dim i, j As Long
    
    lNumRows = UBound(iMat, 1)
    
    For i = 1 To lNumRows
        For j = 1 To lNumRows
           lOutDBL = lOutDBL + iMat(i, j) * iMat(i, j)
        Next j
    Next i
    MatrixABS = Sqr(lOutDBL)

End Function
Public Function MatrixMultiplyScalar(iMat() As Double, iScalar As Double) As Double()
    Dim lOutMat() As Double
    Dim lNumRows As Long
    Dim i, j As Long
    
    lNumRows = UBound(iMat, 1)
    ReDim lOutMat(1 To lNumRows, 1 To lNumRows)
    For i = 1 To lNumRows
        For j = 1 To lNumRows
            lOutMat(i, j) = iMat(i, j) * iScalar
        Next j
    Next i
    MatrixMultiplyScalar = lOutMat
End Function
Public Function MatrixAdd(iMat1() As Double, iMat2() As Double) As Double()
    Dim lOutMat() As Double
    Dim lNumRows As Long
    Dim i, j As Long
    
    lNumRows = UBound(iMat1, 1)
    ReDim lOutMat(1 To lNumRows, 1 To lNumRows)
    For i = 1 To lNumRows
        For j = 1 To lNumRows
            lOutMat(i, j) = iMat1(i, j) + iMat2(i, j)
        Next j
    Next i
    MatrixAdd = lOutMat
End Function
Public Function MatrixSub(iMat1() As Double, iMat2() As Double) As Double()
    Dim lOutMat() As Double
    Dim lNumRows As Long
    Dim i, j As Long
    
    lNumRows = UBound(iMat1, 1)
    ReDim lOutMat(1 To lNumRows, 1 To lNumRows)
    For i = 1 To lNumRows
        For j = 1 To lNumRows
            lOutMat(i, j) = iMat1(i, j) - iMat2(i, j)
        Next j
    Next i
    MatrixSub = lOutMat
End Function

Public Function MatrixSQRT(iMat() As Double) As Double()
    Const lMaxIt As Long = 500
    Const lEpsilon As Double = 1 * 10 ^ -15
    Dim lInvY() As Double
    Dim lInvZ() As Double
    Dim lY() As Double
    Dim lZ() As Double
    Dim lNumRows As Long
    Dim i As Long
    
    lNumRows = UBound(iMat, 1)
    lZ = MatrixID(lNumRows)
    lY = iMat
    
    For i = 1 To lMaxIt
        lInvY = MatrixInverse(lY)
        lInvZ = MatrixInverse(lZ)
        lZ = MatrixMultiplyScalar(MatrixAdd(lZ, lInvY), 0.5)
        lY = MatrixMultiplyScalar(MatrixAdd(lY, lInvZ), 0.5)
        
        If MatrixABS(MatrixSub(MatrixMultiply(lY, lY), iMat)) < lEpsilon * lNumRows Then
            Exit For
            'Value found
        End If
    Next i
    MatrixSQRT = lY
    
End Function
Public Function MatrixQOM(iMat1() As Double) As Double()
    Dim lOutMat() As Double
    Dim lLamaba As Double
    Dim lNumRows As Long
    Dim lContinue As Boolean
    Dim lNumDict As Dictionary
    Dim lSortedRow As Variant
    Dim C As Double
    Dim ltempt As Double
    
    Set lNumDict = New Dictionary
    Dim i As Long
    Dim j As Long
    Dim k As Long
    lOutMat = iMat1
    lNumRows = UBound(iMat1, 1)
    For i = 1 To lNumRows
        lLamaba = 0
        For j = 1 To lNumRows
            lLamaba = lLamaba + iMat1(i, j)
        Next j
        lLamaba = lLamaba - 1
        lLamaba = lLamaba / lNumRows
        For j = 1 To lNumRows
            lOutMat(i, j) = iMat1(i, j) - lLamaba
        Next j
        lContinue = False
        For j = 1 To lNumRows
            If lOutMat(i, j) < 0 Then
                lContinue = True
                Exit For
            End If
        Next j
        If lContinue Then
            lNumDict.RemoveAll
            For j = 1 To lNumRows
                lNumDict.Add lOutMat(i, j), j
            Next j
            Call SortDictionary(lNumDict, True, True)
            lSortedRow = lNumDict.Keys
            For j = 1 To lNumRows
                C = 0
                For k = 1 To j
                    C = C + lSortedRow(k - 1)
                Next k
                C = C - j * lSortedRow(j - 1)
                If C > 1 Then
                    k = j - 1
                    Exit For
                End If
            Next j
            C = 0
            For j = 1 To k
                C = C + lSortedRow(j - 1)
            Next j
            C = (1 - C) / k
            For j = 1 To lNumRows
                If j <= k Then
                    lOutMat(i, lNumDict(lSortedRow(j - 1))) = lSortedRow(j - 1) + C
                Else
                    lOutMat(i, lNumDict(lSortedRow(j - 1))) = 0
                End If
            Next j

        End If
    Next i
    
    MatrixQOM = lOutMat
End Function
Public Function MatrixCholesky(iMat() As Double) As Double()
    Dim lOutMat() As Double
    Dim i As Long
    Dim j As Long
    Dim k As Long
    Dim lNumRows As Long
    Dim lsum As Double
    Dim lSum2 As Double
    
    lNumRows = UBound(iMat)
    ReDim lOutMat(1 To lNumRows, 1 To lNumRows)
    
    lOutMat(1, 1) = Sqr(iMat(1, 1))
    lOutMat(2, 1) = iMat(2, 1) / lOutMat(1, 1)
    lOutMat(2, 2) = Sqr(iMat(2, 2) - lOutMat(2, 1) * lOutMat(2, 1))
    For i = 3 To lNumRows
        lSum2 = 0
        For k = 1 To i - 1
            lsum = 0
            For j = 1 To k
                lsum = lsum + lOutMat(i, j) * lOutMat(k, j)
            Next j
            lOutMat(i, k) = (iMat(i, k) - lsum) / lOutMat(k, k)
             lSum2 = lSum2 + lOutMat(i, k) * lOutMat(i, k)
        Next k
       lOutMat(i, i) = Sqr(iMat(i, i) - lSum2)
    Next i
    
    MatrixCholesky = lOutMat
End Function


