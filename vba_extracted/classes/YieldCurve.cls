VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "YieldCurve"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit
'Inputs
Private clsName As String
Private clsAnalysisDate As Date
Private clsRateDict As Dictionary 'Holds a collection of spot rates( i month, rate)

Private clsLastMonth As Long
Private clsFowardDict As Dictionary 'Holds a collection of sorted foward rates ( 0 to ubound spot rate)
Private clsLastDate As Date
Private clsLastFoward As Double
               
Public Sub Setup(iName As String, ianalysisDate As Date, iRateDict As Dictionary)
    Dim i As Long
    Dim lSpotRate() As Double
    Dim lFowardRate() As Double
    Dim lmonth As Variant
    Dim lCounter As Long
    
    
    Dim lPreviousMonth As Long
    Dim lNextMonth As Long
    clsName = iName
    clsAnalysisDate = ianalysisDate
    Set clsRateDict = iRateDict
    
    lmonth = clsRateDict.Keys
    clsLastMonth = lmonth(UBound(lmonth))
    ReDim lSpotRate(clsLastMonth)
    Call SortDictionary(clsRateDict, True)
    lPreviousMonth = lmonth(0)
    lNextMonth = lmonth(0)
    lCounter = 0
    For i = 1 To clsLastMonth
        If clsRateDict.Exists(i) Then
            lSpotRate(i) = clsRateDict(i)
            lPreviousMonth = lNextMonth
            If lCounter + 1 > UBound(lmonth) Then
                lNextMonth = lmonth(lCounter)
            Else
                lNextMonth = lmonth(lCounter + 1)
            End If
            lCounter = lCounter + 1
        Else
          lSpotRate(i) = (1 - (i - lPreviousMonth) / (lNextMonth - lPreviousMonth)) * iRateDict(lPreviousMonth) + (i - lPreviousMonth) / (lNextMonth - lPreviousMonth) * iRateDict(lNextMonth)
        End If
    Next i
    ReDim lFowardRate(UBound(lSpotRate) - 1)
    
    Set clsFowardDict = New Dictionary
    clsFowardDict.Add CLng(clsAnalysisDate), lSpotRate(1)
    For i = 1 To UBound(lFowardRate)
        lFowardRate(i) = (((1 + lSpotRate(i + 1)) ^ (i + 1)) / ((1 + lSpotRate(i)) ^ (i))) - 1
        clsFowardDict.Add CLng(DateAdd("M", i, clsAnalysisDate)), lFowardRate(i)
    Next i
    clsLastDate = DateAdd("M", i - 1, clsAnalysisDate)
    clsLastFoward = lFowardRate(i - 1)
    
End Sub

Public Function SpotRate(ByVal iDate As Date, iMonth As Long) As Double
    'Returns a rate for certain period.
    'example 3 month rate on 01/25/2017
    
    Dim lPreviousDate As Date
    Dim lNextDate As Date
    Dim lFowardDate As Variant
    Dim i As Long
    Dim j As Long
    Dim lRate As Double
    
    lFowardDate = clsFowardDict.Keys
    lRate = 1
    Do While j < iMonth
        If iDate <= CDate(lFowardDate(0)) Then
            lPreviousDate = lFowardDate(0)
            lNextDate = lFowardDate(0)
            lRate = lRate * (1 + clsFowardDict(lNextDate))
        ElseIf iDate <= CDate(lFowardDate(UBound(lFowardDate))) Then
            For i = LBound(lFowardDate) To UBound(lFowardDate) - 1
                If lFowardDate(i + 1) >= CLng(iDate) And lFowardDate(i) < CLng(iDate) Then
                    lPreviousDate = lFowardDate(i)
                    lNextDate = lFowardDate(i + 1)
                    Exit For
                End If
            Next i
            lRate = lRate * (1 + (clsFowardDict(lPreviousDate) + (clsFowardDict(lNextDate) - clsFowardDict(lPreviousDate)) * (iDate - lPreviousDate) / (lNextDate - lPreviousDate)))
        Else
            lRate = lRate * (1 + clsFowardDict(UBound(lFowardDate)))
        End If
        
        iDate = DateAdd("M", 1, iDate)
        j = j + 1
    Loop
    If iMonth > 0 Then lRate = lRate ^ (1 / iMonth)
    lRate = lRate - 1
    SpotRate = lRate
End Function

Public Function ZeroRate(ByVal iStartDate As Date, ByVal iEndDate As Date) As Double
    Dim lMonths As Long
    Dim lLowDate As Date
    Dim lHighDate As Date
    Dim lLowRate As Double
    Dim lHighRate As Double
        
    lMonths = DateDiff("M", iStartDate, iEndDate)
    lLowDate = DateAdd("M", lMonths, iStartDate)
    
    If iEndDate > lLowDate Then
        lHighDate = DateAdd("M", 1, lLowDate)
        lLowRate = SpotRate(iStartDate, lMonths)
        lHighRate = SpotRate(iStartDate, lMonths + 1)
    Else
        lHighDate = lLowDate
        lLowDate = DateAdd("M", -1, lHighDate)
        lLowRate = SpotRate(iStartDate, lMonths - 1)
        lHighRate = SpotRate(iStartDate, lMonths)
    End If
    
    ZeroRate = lLowRate + (lHighRate - lLowRate) * ((iEndDate - lLowDate) / (lHighDate - lLowDate))
    
End Function
