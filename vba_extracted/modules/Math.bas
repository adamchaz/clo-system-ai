Attribute VB_Name = "Math"
Option Private Module
Private mHolidayDates As Dictionary


Public Function DateFraction(iBegDate As Date, iEndDate As Date, idaycount As DayCount) As Double
    DateFraction = Application.WorksheetFunction.YearFrac(iBegDate, iEndDate, idaycount)
End Function
Public Function CheckBusinessDate(ByVal iStartDate As Date, Optional iPmtADjMethod As String) As Date
        'CHECKS AS DATE AND RETURNS THE BUSINESS EQUIVALEN
        If mHolidayDates Is Nothing Then Call LoadHolidays
        If Weekday(iStartDate, vbSunday) = 1 Or Weekday(iStartDate, vbSunday) = 7 Or mHolidayDates.Exists(iStartDate) Then
            If (UCase(iPmtADjMethod) = "MOD FOLLOWING" And Day(iStartDate + 1) = 1) Or UCase(ipmyadjmetheod) = "PREVIOUS" Then
                CheckBusinessDate = GetPreviousBusinessDate(iStartDate, 1)
            Else
                CheckBusinessDate = GetNextBusinessDate(iStartDate, 1)
            End If
        Else
            CheckBusinessDate = iStartDate
        End If
End Function
Public Function Min(iarray() As Long) As Long
    Dim lMin As Long
    Dim i As Long
    lMin = iarray(LBound(iarray))
    For i = LBound(iarray) + 1 To UBound(iarray())
        If iarray(i) < lMin Then lMin = iarray(i)
    Next
    Min = lMin
End Function
Public Function Max(iarray() As Long) As Long
    Dim lMax As Long
    Dim i As Long
    lMax = iarray(LBound(iarray))
    For i = LBound(iarray) + 1 To UBound(iarray())
        If iarray(i) > lMax Then lMax = iarray(i)
    Next
    Max = lMax
End Function
Public Function Average(iarray() As Long) As Double
    Dim lTotal As Long
    Dim i As Long
    For i = LBound(iarray) To UBound(iarray())
        lTotal = lTotal + iarray(i)
    Next
    Average = lTotal / (UBound(iarray) + 1)
    
End Function
Public Function STD(iarray() As Long) As Double
    Dim lTotal As Double
    Dim lAverage As Double
    Dim i As Long
    
    lAverage = Average(iarray)
    For i = LBound(iarray) To UBound(iarray())
        lTotal = lTotal + (iarray(i) - lAverage) ^ 2
    Next
    STD = Sqr(lTotal / (UBound(iarray) + 1))
    
End Function
Public Function Median(iarray() As Long) As Double
    Dim lNumItem As Long
    Call QSortInPlace(iarray, , , True)
    lNumItem = UBound(iarray) + 1
    
    If lNumItem = 1 Then
        Median = iarray(0)
    ElseIf lNumItem = 2 Then
        Median = (iarray(0) + iarray(1)) / 2
    ElseIf lNumItem Mod 2 = 0 Then
        'Even
       ' Debug.Print "Even"
        lNumItem = lNumItem / 2
        Median = (iarray(lNumItem) + iarray(lNumItem - 1)) / 2
    Else
        lNumItem = lNumItem / 2
        Median = iarray(lNumItem)
    End If
End Function
Public Function MinDBL(iarray() As Double) As Double
    Dim lMin As Double
    Dim i As Long
    lMin = iarray(LBound(iarray))
    For i = LBound(iarray) + 1 To UBound(iarray())
        If iarray(i) < lMin Then lMin = iarray(i)
    Next
    MinDBL = lMin
End Function
Public Function MaxDBL(iarray() As Double) As Double
    Dim lMax As Double
    Dim i As Long
    lMax = iarray(LBound(iarray))
    For i = LBound(iarray) + 1 To UBound(iarray())
        If iarray(i) > lMax Then lMax = iarray(i)
    Next
    MaxDBL = lMax
End Function
Public Function AverageDBL(iarray() As Double) As Double
    Dim lTotal As Double
    Dim i As Long
    For i = LBound(iarray) To UBound(iarray())
        lTotal = lTotal + iarray(i)
    Next
    AverageDBL = lTotal / (UBound(iarray) + 1)
    
End Function
Public Function STDDBL(iarray() As Double) As Double
    Dim lTotal As Double
    Dim lAverage As Double
    Dim i As Long
    
    lAverage = AverageDBL(iarray)
    For i = LBound(iarray) To UBound(iarray())
        lTotal = lTotal + (iarray(i) - lAverage) ^ 2
    Next
    STDDBL = Sqr(lTotal / (UBound(iarray) + 1))
    
End Function
Public Function MedianDBL(iarray() As Double) As Double
    Dim lNumItem As Long
    Call QSortInPlace(iarray, , , True)
    lNumItem = UBound(iarray) + 1
    
    If lNumItem = 1 Then
        MedianDBL = iarray(0)
    ElseIf lNumItem = 2 Then
        MedianDBL = (iarray(0) + iarray(1)) / 2
    ElseIf lNumItem Mod 2 = 0 Then
        'Even
       ' Debug.Print "Even"
        lNumItem = lNumItem / 2
        MedianDBL = (iarray(lNumItem) + iarray(lNumItem - 1)) / 2
    Else
        lNumItem = lNumItem / 2
        MedianDBL = iarray(lNumItem)
    End If
End Function
Public Function DateAddBusiness(iInterval As String, iNumber As Long, iDate As Date, Optional iPmtADjMethod As String, Optional iEndOfMOnth As Boolean) As Date
Dim lNextDate As Date
    
    lNextDate = DateAdd(iInterval, iNumber, iDate)
    If iEndOfMOnth Then
        lNextDate = Application.WorksheetFunction.EoMonth(lNextDate, 0)
    End If

    If Day(lNextDate + 1) = 1 And UCase(iPmtADjMethod) = "MOD FOLLOWING" Then
        lNextDate = GetPreviousBusinessDate(lNextDate, 0)
    ElseIf UCase(iPmtADjMethod) = "FOLLOWING" Or UCase(iPmtADjMethod) = "MOD FOLLOWING" Then
        lNextDate = GetNextBusinessDate(lNextDate, 0)
    ElseIf UCase(iPmtADjMethod) = "PREVIOUS" Then
        lNextDate = GetPreviousBusinessDate(lNextDate, 0)
    End If
    
    DateAddBusiness = lNextDate
    
    
    
End Function

Public Sub LoadHolidays()
    Dim i As Long
    Dim lHoliday As Variant
    lHoliday = Range("Holidays").Value
    'Call LoadHolidays(lHoliday)
    
    
    Set mHolidayDates = Nothing
    Set mHolidayDates = New Dictionary
    
    For i = LBound(lHoliday) To UBound(lHoliday)
        mHolidayDates.Add CDate(lHoliday(i, 1)), i
    Next i
    
End Sub

Public Function ConvertAnnualRates(iAnnualRate As Double, iStartDate As Date, iEndDate As Date) As Double
    On Error GoTo ErrorTrack
    Dim ldivisor As Double
    If iStartDate <> iEndDate Then
        ldivisor = 360 / Application.WorksheetFunction.Days360(iStartDate, iEndDate)
        ConvertAnnualRates = 1 - (1 - iAnnualRate) ^ (1 / ldivisor)
    End If
    Exit Function
ErrorTrack:
    ConvertAnnualRates = 0
End Function


Public Function GetPreviousBusinessDate(ByVal lNextDate As Date, ByVal lNumofDays As Long) As Date
    Dim i As Long
        If mHolidayDates Is Nothing Then Call LoadHolidays
        
        If Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate) Then
            Do While Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate)
                lNextDate = lNextDate - 1
            Loop
            lNumofDays = lNumofDays - 1
        End If
        Do While i < lNumofDays
            Do While Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate)
                lNextDate = lNextDate - 1
            Loop
            lNextDate = lNextDate - 1
            i = i + 1
        Loop
        GetPreviousBusinessDate = lNextDate
    
End Function



Public Function GetNextBusinessDate(lNextDate As Date, lNumofDays As Long) As Date
    Dim i As Long
    If mHolidayDates Is Nothing Then Call LoadHolidays
    
    If Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate) Then
        Do While Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate)
            lNextDate = lNextDate + 1
        Loop
        lNumofDays = lNumofDays + 1
    End If
    Do While i < lNumofDays
        Do While Weekday(lNextDate, vbSunday) = 1 Or Weekday(lNextDate, vbSunday) = 7 Or mHolidayDates.Exists(lNextDate)
            lNextDate = lNextDate + 1
        Loop
        i = i + 1
    Loop
    GetNextBusinessDate = lNextDate
    
End Function


Public Function GetDayCountEnum(iDayCountSTR As String) As DayCount
    Select Case UCase(iDayCountSTR)
    Case "30/360"
        GetDayCountEnum = 0
    Case "ACTUAL/ACTUAL"
        GetDayCountEnum = 1
    Case "ACTUAL/365", "ACT365"
        GetDayCountEnum = 3
    Case "ACTUAL/360", "ACT360"
        GetDayCountEnum = 2
    Case "30/360EU"
        GetDayCountEnum = 4
    End Select
End Function
'---------------------------------------------------------------------------------------
' Module    : Math
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   : Public functions use to perform math calculations
'---------------------------------------------------------------------------------------

Public Function WAL(iTotalCF() As Double, iPeriodPerYear As Double) As Double
    Dim i As Long
    Dim lValue As Double
    Dim lValueSum As Double
    For i = 1 To UBound(iTotalCF)
        lValue = lValue + iTotalCF(i) * i
        lValueSum = lValueSum + iTotalCF(i)
    Next i
    lValue = lValue / lValueSum
    WAL = lValue / iPeriodPerYear
End Function
Public Function WalwLosses(iCF As SimpleCashflow, iPeriodPerYear As Double) As Double
'    Dim i As Long
'    Dim lValue As Double
'    Dim lValueSum As Double
'    Dim lLossSum As Double
'
'    For i = 1 To iCF.Count
'        lValueSum = i * (iCF.TotalCF(i) - iCF.Interest(i)) + lValueSum
'        lLossSum = iCF.Loss(i) + lLossSum
'    Next i
'
'    i = i - 1
'    lValueSum = lValueSum + i * lLossSum
'
'    WalwLosses = lValueSum / iCF.BegBal(1) / iPeriodPerYear

End Function

Public Function YearFract(iDate1 As Date, iDate2 As Date, DayCount As DayCount) As Double
'---------------------------------------------------------------------------------------
' Procedure : YearFract
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------
    YearFract = Application.WorksheetFunction.YearFrac(iDate1, iDate2, DayCount)
End Function



Public Function Days(iDate1 As Date, iDate2 As Date, DayCount As DayCount) As Long
'---------------------------------------------------------------------------------------
' Procedure : Days
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------
'
    Select Case DayCount
    Case 0
        Days = Application.WorksheetFunction.Days360(iDate1, iDate2, False)
    Case 1, 2, 3
        Days = iDate2 - iDate1
    Case 4
        Days = Application.WorksheetFunction.Days360(iDate1, iDate2, True)
    Case Else
        Days = Application.WorksheetFunction.Days360(iDate1, iDate2, False)
    End Select
End Function

Public Function CalcPV(iCashflows() As Double, iDates() As Date, iSettlmentDate As Date, iYield As Double, idaycount As DayCount, ipayperyear As Long) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcPV
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------

    Dim lRemTerm As Long
    Dim PV As Double
    Dim i As Long
    Dim lDiscount As Double

    lRemTerm = UBound(iCashflows)
    lDiscount = CalcDiscount(iYield, iSettlmentDate, iDates(1), idaycount, ipayperyear, True)
    PV = lDiscount * iCashflows(1)
    For i = 2 To lRemTerm
        lDiscount = lDiscount * CalcDiscount(iYield, iDates(i - 1), iDates(i), idaycount, ipayperyear, False)
        PV = PV + iCashflows(i) * lDiscount
    Next i
    CalcPV = PV

End Function
Public Function CalcPVwSpread(iCashflows() As Double, iDates() As Date, iRates() As Double, iSettlmentDate As Date, iSpread As Double, idaycount As DayCount, ipayperyear As Long) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcPV
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------

    Dim lRemTerm As Long
    Dim PV As Double
    Dim i As Long
    Dim lDiscount As Double

    lRemTerm = UBound(iCashflows)
    lDiscount = CalcDiscount(iRates(1) + iSpread, iSettlmentDate, iDates(1), idaycount, ipayperyear, True)
    PV = lDiscount * iCashflows(1)
    For i = 2 To lRemTerm
        lDiscount = lDiscount * CalcDiscount(iRates(i) + iSpread, iDates(i - 1), iDates(i), idaycount, ipayperyear, False)
        PV = PV + iCashflows(i) * lDiscount
    Next i
    CalcPVwSpread = PV

End Function
Public Function CalcPVwOAS(iCFHolder As Dictionary, iDates() As Date, iRateHolder As Dictionary, iSettlmentDate As Date, iOAS As Double, idaycount As DayCount, ipayperyear As Long) As Double
    Dim lRates() As Double
    Dim lCF() As Double
    Dim lNumCF As Long
    Dim lPV As Double
    Dim i As Integer
        
    lNumCF = iCFHolder.Count
    For i = 0 To lNumCF - 1
        lCF = iCFHolder(i)
        lRates = iRateHolder(i)
        lPV = lPV + CalcPVwSpread(lCF, iDates, lRates, iDates(0), iOAS, idaycount, ipayperyear)
    Next i
    CalcPVwOAS = lPV / lNumCF
    
End Function



Public Function CalcDiscount(iYield As Double, iDate1 As Date, iDate2 As Date, idaycount As DayCount, ipayperyear As Long, iisSettle As Boolean) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcDiscount
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------
'
'Calculates a discount factor.

    CalcDiscount = 1 / CalcCompound(iYield, iDate1, iDate2, idaycount, ipayperyear, iisSettle)
End Function
Public Function CalcCompound(iYield As Double, iDate1 As Date, iDate2 As Date, idaycount As DayCount, ipayperyear As Long, iisSettle As Boolean) As Double
    Dim lNumPeriods As Double
    Dim lCompounded As Double
    
    lNumPeriods = CompoundingPeriodsBetweenDates(iDate1, iDate2, 12 / ipayperyear, idaycount, iisSettle)
    lCompounded = (1 + iYield / ipayperyear) ^ lNumPeriods
    CalcCompound = lCompounded
End Function
Public Function CalcYield(iPV As Double, iTotal() As Double, iDates() As Date, idaycount As DayCount, ifreq As Long) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcYield
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------
'
    On Error GoTo ErrorTrack
    Dim llo As Double
    Dim lhi As Double

    Dim tempPV As Double
    Dim yield As Double
    Dim Counter As Long
    Dim i As Long

    'Check Total
    Dim totalcheck As Boolean
    totalcheck = True
    For i = 1 To UBound(iTotal)
        If iTotal(i) > 0 Then
            totalcheck = False
            Exit For
        End If
    Next i

    If totalcheck = True Then
Exit Function
    End If

    llo = -1.5
    lhi = 1
    Counter = 0
    'Calculate Yield
    Do
        Counter = Counter + 1
        If Counter > 1000000 Then Exit Do
        If iPV = 0 Then Exit Do
        If Abs(llo - lhi) < 0.0000000000001 Then Exit Do
        If tempPV = 0 Then
            yield = (llo + lhi) / 2
        ElseIf tempPV - iPV < 0 Then
            lhi = yield
            yield = (llo + yield) / 2
        ElseIf tempPV - iPV > 0 Then
            llo = yield
            yield = (lhi + yield) / 2
        End If
        If yield = 0 Then yield = yield + 0.01
        tempPV = 0
        tempPV = CalcPV(iTotal, iDates, iDates(0), yield, idaycount, ifreq)

    Loop Until Abs(tempPV - iPV) < 0.0000000000001

    CalcYield = yield
Exit Function

ErrorTrack:
    yield = -1
    CalcYield = -1

End Function
Public Function CalcZSpread(iPV As Double, iTotal() As Double, iDates() As Date, iRates() As Double, idaycount As DayCount, ifreq As Long) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcSpread
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   :
'---------------------------------------------------------------------------------------
'
    On Error GoTo ErrorTrack
    Dim llo As Double
    Dim lhi As Double

    Dim tempPV As Double
    Dim Spread As Double
    Dim Counter As Long
    Dim i As Long

    'Check Total
    Dim totalcheck As Boolean
    totalcheck = True
    For i = 1 To UBound(iTotal)
        If iTotal(i) > 0 Then
            totalcheck = False
            Exit For
        End If
    Next i

    If totalcheck = True Then
Exit Function
    End If

    llo = -1.5
    lhi = 1
    Counter = 0
    'Calculate Spread
    Do
        Counter = Counter + 1
        If Counter > 1000000 Then
            Exit Do
        End If
        If iPV = 0 Then Exit Do
        If Abs(llo - lhi) < 0.0000000000001 Then Exit Do
        If tempPV = 0 Then
            Spread = (llo + lhi) / 2
        ElseIf tempPV - iPV < 0 Then
            lhi = Spread
            Spread = (llo + Spread) / 2
        ElseIf tempPV - iPV > 0 Then
            llo = Spread
            Spread = (lhi + Spread) / 2
        End If
        If Spread = 0 Then Spread = Spread + 0.01
        tempPV = 0
        tempPV = CalcPVwSpread(iTotal, iDates, iRates(), iDates(0), Spread, idaycount, ifreq)

    Loop Until Abs(tempPV - iPV) < 0.00001

    CalcZSpread = Spread
Exit Function

ErrorTrack:
    Spread = -1
    CalcZSpread = -1

End Function
Public Function CalcOAS(iPV As Double, iCFHolder As Dictionary, iDates() As Date, iRateHolder As Dictionary, idaycount As DayCount, ifreq As Long) As Double
'---------------------------------------------------------------------------------------
' Procedure : CalcSpread
' Author    : Adam C. Freeman
' Date      : 1/8/2015
' Purpose   :
'---------------------------------------------------------------------------------------
'
    On Error GoTo ErrorTrack
    Dim llo As Double
    Dim lhi As Double

    Dim tempPV As Double
    Dim Spread As Double
    Dim Counter As Long
    Dim i As Long
    Dim lNumofCashflows As Long
    Dim lRates() As Double
    Dim lcashflows() As Double
    
    
    lNumofCashflows = iCFHolder.Count
    'Need a check to make sure that the rate holder and cfholder have the same number of rates
    

    llo = -0.5
    lhi = 0.5
    Counter = 0
    'Calculate Spread
    Do
        Counter = Counter + 1
        If Counter > 1000000 Then
            Exit Do
        End If
        If iPV = 0 Then Exit Do
        If Abs(llo - lhi) < 0.0000000000001 Then
            
            Exit Do
        End If
        If tempPV = 0 Then
            Spread = (llo + lhi) / 2
        ElseIf tempPV - iPV < 0 Then
            lhi = Spread
            Spread = (llo + Spread) / 2
        ElseIf tempPV - iPV > 0 Then
            llo = Spread
            Spread = (lhi + Spread) / 2
        End If
        If Spread = 0 Then Spread = Spread + 0.01
        
        tempPV = 0
        For i = 0 To lNumofCashflows - 1
            lcashflows = iCFHolder(i)
            lRates = iRateHolder(i)
            tempPV = tempPV + CalcPVwSpread(lcashflows, iDates, lRates(), iDates(0), Spread, idaycount, ifreq)
''            If counter = 1 Then
''                Debug.Print CalcZSpread(iPV, lcashflows, iDates, lRates, US30_360, 12)
''             End If
        Next i
        tempPV = tempPV / lNumofCashflows

    Loop Until Abs(tempPV - iPV) < 0.0001

    CalcOAS = Spread
    'Debug.Print counter
Exit Function

ErrorTrack:
    Spread = -1
    CalcOAS = -1

End Function


Public Function GetMonths(lString As String) As Long
'---------------------------------------------------------------------------------------
' Procedure : GetMonths
' Author    : Adam C. Freeman
' Date      : 12/12/2011
' Purpose   : Convert
'---------------------------------------------------------------------------------------
    Select Case lString

    Case "Annually"
        GetMonths = 12
    Case "Semi-Annually"
        GetMonths = 6
    Case "Quarterly"
        GetMonths = 3
    Case "Monthly"
        GetMonths = 1
    End Select
End Function
Public Function GetPaymentsPerYear(iString As String) As Long
    Select Case UCase(iString)
    
    Case "ANNUALLY"
        GetPaymentsPerYear = 1
    Case "SEMI-ANNUALLY"
        GetPaymentsPerYear = 2
    Case "QUARTERLY"
        GetPaymentsPerYear = 4
    Case "MONTHLY"
        GetPaymentsPerYear = 12
    End Select
    
    
    
End Function
Public Function Rand() As Double
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'
' Copyright 2010 "Cash CDO Modeling in Excel: A Step by Step Approach" by Darren Smith and Pamela Winchie
' See usage statement
'
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

'this function returns a random no between 0->1
    Dim x As Double
    Do
        x = Rnd
    Loop Until x > 0#       'this check as cannot take log 0!!
    Rand = x
End Function

Public Function CompoundingPeriodsBetweenDates(iStartDate As Date, iEndDate As Date, iMonth As Long, iDayCountEnum As Long, iisSettle As Boolean) As Double
    Dim lTempDate As Date
    Dim ltempdate2 As Date
    Dim lTotalFraction As Double
    Dim lCounter As Long

    If iisSettle Then
        'If we are on a settlment date we want to loop backwards from end Date
        lTempDate = DateAdd("M", -iMonth, iEndDate)
        Do While lTempDate > iStartDate And lCounter < 1000000
            lTotalFraction = lTotalFraction + 1
            lCounter = lCounter + 1
            lTempDate = DateAdd("M", -iMonth, lTempDate)
        Loop
        If lCounter = 1000000 Then
            CompoundingPeriodsBetweenDates = xlErrValue
        Else

            ltempdate2 = DateAdd("M", iMonth, lTempDate)
            lTotalFraction = lTotalFraction + Days(iStartDate, ltempdate2, iDayCountEnum) / Days(lTempDate, ltempdate2, iDayCountEnum)
            CompoundingPeriodsBetweenDates = lTotalFraction
        End If
    Else    'If we are not on start date we want to loop backwards
        lTempDate = DateAdd("M", iMonth, iStartDate)
        Do While lTempDate < iEndDate And lCounter < 1000000
            lTotalFraction = lTotalFraction + 1
            lCounter = lCounter + 1
            lTempDate = DateAdd("M", iMonth, lTempDate)
        Loop
        If lCounter = 1000000 Then
            CompoundingPeriodsBetweenDates = xlErrValue
        Else
            ltempdate2 = DateAdd("M", -iMonth, lTempDate)
            lTotalFraction = lTotalFraction + Days(ltempdate2, iEndDate, iDayCountEnum) / Days(ltempdate2, lTempDate, iDayCountEnum)
            CompoundingPeriodsBetweenDates = lTotalFraction
        End If
    End If

End Function




'Public Function ConvertMTGCtoSimpleCashflow(iSettledate As Date, iFirstPayDate As Date, iPayFreq As Long, iMTG As MTGCashflows) As SimpleCashflow
'    On Error GoTo ErrorTrap
'    Dim lSimpleCF As SimpleCashflow
'    Dim i As Long
'    Dim lPrincipal() As Double
'    Dim lDates() As Date
'    Dim lEndBal() As Double
'    Dim lMTGCF As MTGCashflows
'     lMTGCF = iMTG
'    ReDim lPrincipal(UBound(lMTGCF.BegBalance))
'    ReDim lDates(UBound(lPrincipal))
'    ReDim lEndBal(UBound(lPrincipal))
'    lDates(0) = iSettledate
'    lEndBal(0) = lMTGCF.BegBalance(1)
'    For i = 1 To UBound(lPrincipal)
'        If i = 1 Then
'            lDates(1) = iFirstPayDate
'        Else
'            lDates(i) = DateAdd("M", iPayFreq, lDates(i - 1))
'        End If
'        lEndBal(i) = lMTGCF.EndBalance(i)
'        lPrincipal(i) = lMTGCF.SchPrincipal(i) + lMTGCF.UnSchPrincipal(i)
'    Next i
'    Set lSimpleCF = New SimpleCashflow
'    lSimpleCF.DistDates = lDates
'    lSimpleCF.BegBalances = lMTGCF.BegBalance
'    lSimpleCF.IntPayments = lMTGCF.Interest
'    lSimpleCF.PrinPayments = lPrincipal
'    lSimpleCF.EndBalances = lEndBal
'    Set ConvertMTGCtoSimpleCashflow = lSimpleCF
'
'Exit Function
'ErrorTrap:
'    Err.Raise vbObjectError + 1024, "Math", "Error converting Mtgcashflows"
'
'End Function

