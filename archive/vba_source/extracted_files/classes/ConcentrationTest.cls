VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ConcentrationTest"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit

'Inteernal
Private clsAggEUScore() As Double
Private clsDiversityScore() As Double

Private clsPrinProceeds As Double
Private clsAssetsDic As Dictionary
Private clsCollateralPrincipalAmount As Double
Private clsTestInputDict As Dictionary
Private clsTestThresholdDict As Dictionary
Private clsResults() As Results
Private clsObjWeights As Dictionary
Private clsUpdaatedPreviousResult As Boolean

Public Sub Setup(iTestInput As Dictionary, iTestThresholds As Dictionary, Optional iObJWeights As Dictionary)
    Set clsTestInputDict = iTestInput
    Set clsTestThresholdDict = iTestThresholds
    If Not (iObJWeights Is Nothing) Then
        Set clsObjWeights = iObJWeights
    End If
End Sub
Public Function GetSpecificTestResult(iTestNum As TestNum) As Double
    Dim i As Long
    For i = LBound(clsResults) To UBound(clsResults)
        If clsResults(i).TestNumber = iTestNum Then
            GetSpecificTestResult = clsResults(i).Result
            Exit For
        End If
    Next i
End Function
Public Sub UpdatePreviousValues()
    Dim i As Long
    If UBound(clsResults()) > 0 Then
        For i = 0 To UBound(clsResults)
            If clsResults(i).TestNumber > 0 Then
                clsTestThresholdDict(clsResults(i).TestNumber).PreviousValues = clsResults(i).Result
            End If
        Next i
    End If
End Sub
Public Function CalcObjectiveFunction() As Double
    Dim i As Long
    Dim lobjective As Double
    
    For i = LBound(clsResults) To UBound(clsResults)
        With clsResults(i)
            If .PassFail = False And .TestNumber <> 31 And .Numerator > 0 Then
                lobjective = 0
                Exit For
            End If
            
            If clsObjWeights.Exists(.TestNumber) Then
                If clsTestThresholdDict(.TestNumber).MinMax = "MAX" Then
                    If .Result <> 0 Then
                        lobjective = lobjective + .Threshold / .Result * clsObjWeights(.TestNumber)
                    End If
                Else
                    If .Threshold <> 0 Then
                        lobjective = lobjective + .Result / .Threshold * clsObjWeights(.TestNumber)
                    End If
                End If
            End If
        End With
    Next i

    CalcObjectiveFunction = lobjective * 100

End Function
Public Function CalcAssetObject(iAssetDict As Dictionary) As Dictionary
    Dim lOutputDict As Dictionary
    Dim lBLKID As Variant
    Dim lTestNum As Variant
    Dim lAsset As Asset
    Dim lOBJ As Double
    Dim lTestResult As Double
    Dim lResults As Results
    Dim lTestResultDict As Dictionary
    Dim i As Long
    
    
    Set lTestResultDict = New Dictionary
    Set lOutputDict = New Dictionary
    For i = LBound(clsResults) To UBound(clsResults)
        If clsObjWeights.Exists(clsResults(i).TestNumber) Then
            If clsObjWeights(clsResults(i).TestNumber) > 0 Then
                lTestResultDict.Add clsResults(i).TestNumber, clsResults(i).Result
            End If
        End If
    Next i
    For Each lBLKID In iAssetDict.Keys
        Set lAsset = iAssetDict.Item(lBLKID)
        lOBJ = 0
        For Each lTestNum In lTestResultDict.Keys
            Select Case lTestNum
            Case 39
                lTestResult = lAsset.LiborFloor - clsTestInputDict("Current LIBOR")
                If lTestResult < 0 Then lTestResult = 0
                lTestResult = lTestResult + lAsset.CpnSpread
                lTestResult = lTestResult / lTestResultDict(lTestNum)
            Case 36
                lTestResult = lTestResultDict(lTestNum) / ConverRatingToFactor(lAsset.MDYDPRatingWARF)
            Case 38
                If lAsset.MarketValue > 0 Then
                    lTestResult = 100 / lAsset.MarketValue
                Else
                    lTestResult = 0
                End If
            End Select
'            If UCase(iType) <> "BUY" Then
'               lTestResult = lTestResult / 1
'            End If
            lOBJ = lOBJ + lTestResult * clsObjWeights.Item(lTestNum)
        Next lTestNum
        lOutputDict.Add lBLKID, lOBJ
    Next lBLKID
    
    Set CalcAssetObject = lOutputDict
End Function
Public Function CalcAssetObject2(iAssetDict As Dictionary, iTranType As TransactionType) As Dictionary
    Dim lOutputDict As Dictionary
    Dim lBLKID As Variant
    Dim lTestNum As Variant
    Dim lAsset As Asset
    Dim lOBJ As Double
    Dim lTestResult As Double
    Dim lResults As Results
    Dim lTestResultDict As Dictionary
    Dim i As Long
    Dim lTempResult As Resultscls
    
    
    Set lTestResultDict = New Dictionary
    Set lOutputDict = New Dictionary
    For i = LBound(clsResults) To UBound(clsResults)
        If clsObjWeights.Exists(clsResults(i).TestNumber) Then
            If clsObjWeights(clsResults(i).TestNumber) > 0 Then
                Set lTempResult = New Resultscls
                lTempResult.Denominator = clsResults(i).Denominator
                lTempResult.Numerator = clsResults(i).Numerator
                lTempResult.Result = clsResults(i).Result
                lTempResult.Threshold = clsResults(i).Threshold
                lTestResultDict.Add clsResults(i).TestNumber, lTempResult
            End If
        End If
    Next i
    For Each lBLKID In iAssetDict.Keys
        Set lAsset = iAssetDict.Item(lBLKID)
        lOBJ = 0
        For Each lTestNum In lTestResultDict.Keys
            Select Case lTestNum
            Case 35
                lTestResult = lAsset.WAL
                lTestResult = (lTestResult * 1000000 + lTestResultDict(lTestNum).Numerator) / (10000000 + lTestResultDict(lTestNum).Denominator)
                lTestResult = lTestResultDict(lTestNum).Threshold / lTestResult
            Case 7
                If ConverRatingToFactor(lAsset.MDYRating) > 3490 Then
                    If iTranType = Buy Then
                        lTestResult = (100 - lAsset.MarketValue) / 100 * 1000000 * iTranType
                        lTestResult = (1000000 + lTestResultDict(lTestNum).Numerator) / (lTestResult + lTestResultDict(lTestNum).Denominator)
                        lTestResult = lTestResultDict(lTestNum).Threshold / lTestResult
                    Else
                        lTestResult = (100 - lAsset.MarketValue) / 100 * 1000000 * iTranType
                        lTestResult = (lTestResultDict(lTestNum).Numerator - 1000000) / (lTestResult + lTestResultDict(lTestNum).Denominator)
                        lTestResult = lTestResult / lTestResultDict(lTestNum).Threshold
                    End If
                Else
                    lTestResult = 10
                End If
                
            Case 33
                lTestResult = lAsset.MDYRecoveryRate
                lTestResult = (lTestResult * 1000000 + lTestResultDict(lTestNum).Numerator) / (10000000 + lTestResultDict(lTestNum).Denominator)
                lTestResult = lTestResult / lTestResultDict(lTestNum).Threshold
            Case 39, 32
                lTestResult = lAsset.LiborFloor - clsTestInputDict("Current LIBOR")
                If lTestResult < 0 Then lTestResult = 0
                lTestResult = lTestResult + lAsset.CpnSpread
                lTestResult = (lTestResult * 1000000 + lTestResultDict(lTestNum).Numerator) / (10000000 + lTestResultDict(lTestNum).Denominator)
                lTestResult = lTestResult / lTestResultDict(lTestNum).Threshold
            Case 36
                lTestResult = ConverRatingToFactor(lAsset.MDYDPRatingWARF)
                If lTestResult = 10000 Then
                    lTestResult = 10000000000#
                Else
                    lTestResult = 1000000 * lTestResult
                End If
                lTestResult = (lTestResult + lTestResultDict(lTestNum).Numerator) / (10000000 + lTestResultDict(lTestNum).Denominator)
                lTestResult = lTestResultDict(lTestNum).Threshold / lTestResult
            Case 38
                lTestResult = (100 - lAsset.MarketValue) / 100 * 1000000 * iTranType
                lTestResult = lTestResultDict(lTestNum).Numerator + lTestResult
                lTestResult = lTestResult / lTestResultDict(lTestNum).Denominator
                If iTranType = Buy Then
                    lTestResult = lTestResult / lTestResultDict(lTestNum).Threshold
                Else
                    lTestResult = lTestResultDict(lTestNum).Threshold / lTestResult
                End If
'                If lAsset.MarketValue > 0 Then
'                    lTestResult = 100 / lAsset.MarketValue
'                Else
'                    lTestResult = 0
'                End If
                
            End Select

            lOBJ = lOBJ + lTestResult * clsObjWeights.Item(lTestNum)
        Next lTestNum
        lOutputDict.Add lBLKID, lOBJ
    Next lBLKID
    
    Set CalcAssetObject2 = lOutputDict
End Function
Private Sub Class_Initialize()
    ReDim clsAggEUScore(200)
    clsAggEUScore(0) = 0
    clsAggEUScore(1) = 0.05
    clsAggEUScore(2) = 0.15
    clsAggEUScore(3) = 0.25
    clsAggEUScore(4) = 0.35
    clsAggEUScore(5) = 0.45
    clsAggEUScore(6) = 0.55
    clsAggEUScore(7) = 0.65
    clsAggEUScore(8) = 0.75
    clsAggEUScore(9) = 0.85
    clsAggEUScore(10) = 0.95
    clsAggEUScore(11) = 1.05
    clsAggEUScore(12) = 1.15
    clsAggEUScore(13) = 1.25
    clsAggEUScore(14) = 1.35
    clsAggEUScore(15) = 1.45
    clsAggEUScore(16) = 1.55
    clsAggEUScore(17) = 1.65
    clsAggEUScore(18) = 1.75
    clsAggEUScore(19) = 1.85
    clsAggEUScore(20) = 1.95
    clsAggEUScore(21) = 2.05
    clsAggEUScore(22) = 2.15
    clsAggEUScore(23) = 2.25
    clsAggEUScore(24) = 2.35
    clsAggEUScore(25) = 2.45
    clsAggEUScore(26) = 2.55
    clsAggEUScore(27) = 2.65
    clsAggEUScore(28) = 2.75
    clsAggEUScore(29) = 2.85
    clsAggEUScore(30) = 2.95
    clsAggEUScore(31) = 3.05
    clsAggEUScore(32) = 3.15
    clsAggEUScore(33) = 3.25
    clsAggEUScore(34) = 3.35
    clsAggEUScore(35) = 3.45
    clsAggEUScore(36) = 3.55
    clsAggEUScore(37) = 3.65
    clsAggEUScore(38) = 3.75
    clsAggEUScore(39) = 3.85
    clsAggEUScore(40) = 3.95
    clsAggEUScore(41) = 4.05
    clsAggEUScore(42) = 4.15
    clsAggEUScore(43) = 4.25
    clsAggEUScore(44) = 4.35
    clsAggEUScore(45) = 4.45
    clsAggEUScore(46) = 4.55
    clsAggEUScore(47) = 4.65
    clsAggEUScore(48) = 4.75
    clsAggEUScore(49) = 4.85
    clsAggEUScore(50) = 4.95
    clsAggEUScore(51) = 5.05
    clsAggEUScore(52) = 5.15
    clsAggEUScore(53) = 5.25
    clsAggEUScore(54) = 5.35
    clsAggEUScore(55) = 5.45
    clsAggEUScore(56) = 5.55
    clsAggEUScore(57) = 5.65
    clsAggEUScore(58) = 5.75
    clsAggEUScore(59) = 5.85
    clsAggEUScore(60) = 5.95
    clsAggEUScore(61) = 6.05
    clsAggEUScore(62) = 6.15
    clsAggEUScore(63) = 6.25
    clsAggEUScore(64) = 6.35
    clsAggEUScore(65) = 6.45
    clsAggEUScore(66) = 6.55
    clsAggEUScore(67) = 6.65
    clsAggEUScore(68) = 6.75
    clsAggEUScore(69) = 6.85
    clsAggEUScore(70) = 6.95
    clsAggEUScore(71) = 7.05
    clsAggEUScore(72) = 7.15
    clsAggEUScore(73) = 7.25
    clsAggEUScore(74) = 7.35
    clsAggEUScore(75) = 7.45
    clsAggEUScore(76) = 7.55
    clsAggEUScore(77) = 7.65
    clsAggEUScore(78) = 7.75
    clsAggEUScore(79) = 7.85
    clsAggEUScore(80) = 7.95
    clsAggEUScore(81) = 8.05
    clsAggEUScore(82) = 8.15
    clsAggEUScore(83) = 8.25
    clsAggEUScore(84) = 8.35
    clsAggEUScore(85) = 8.45
    clsAggEUScore(86) = 8.55
    clsAggEUScore(87) = 8.65
    clsAggEUScore(88) = 8.75
    clsAggEUScore(89) = 8.85
    clsAggEUScore(90) = 8.95
    clsAggEUScore(91) = 9.05
    clsAggEUScore(92) = 9.15
    clsAggEUScore(93) = 9.25
    clsAggEUScore(94) = 9.35
    clsAggEUScore(95) = 9.45
    clsAggEUScore(96) = 9.55
    clsAggEUScore(97) = 9.65
    clsAggEUScore(98) = 9.75
    clsAggEUScore(99) = 9.85
    clsAggEUScore(100) = 9.95
    clsAggEUScore(101) = 10.05
    clsAggEUScore(102) = 10.15
    clsAggEUScore(103) = 10.25
    clsAggEUScore(104) = 10.35
    clsAggEUScore(105) = 10.45
    clsAggEUScore(106) = 10.55
    clsAggEUScore(107) = 10.65
    clsAggEUScore(108) = 10.75
    clsAggEUScore(109) = 10.85
    clsAggEUScore(110) = 10.95
    clsAggEUScore(111) = 11.05
    clsAggEUScore(112) = 11.15
    clsAggEUScore(113) = 11.25
    clsAggEUScore(114) = 11.35
    clsAggEUScore(115) = 11.45
    clsAggEUScore(116) = 11.55
    clsAggEUScore(117) = 11.65
    clsAggEUScore(118) = 11.75
    clsAggEUScore(119) = 11.85
    clsAggEUScore(120) = 11.95
    clsAggEUScore(121) = 12.05
    clsAggEUScore(122) = 12.15
    clsAggEUScore(123) = 12.25
    clsAggEUScore(124) = 12.35
    clsAggEUScore(125) = 12.45
    clsAggEUScore(126) = 12.55
    clsAggEUScore(127) = 12.65
    clsAggEUScore(128) = 12.75
    clsAggEUScore(129) = 12.85
    clsAggEUScore(130) = 12.95
    clsAggEUScore(131) = 13.05
    clsAggEUScore(132) = 13.15
    clsAggEUScore(133) = 13.25
    clsAggEUScore(134) = 13.35
    clsAggEUScore(135) = 13.45
    clsAggEUScore(136) = 13.55
    clsAggEUScore(137) = 13.65
    clsAggEUScore(138) = 13.75
    clsAggEUScore(139) = 13.85
    clsAggEUScore(140) = 13.95
    clsAggEUScore(141) = 14.05
    clsAggEUScore(142) = 14.15
    clsAggEUScore(143) = 14.25
    clsAggEUScore(144) = 14.35
    clsAggEUScore(145) = 14.45
    clsAggEUScore(146) = 14.55
    clsAggEUScore(147) = 14.65
    clsAggEUScore(148) = 14.75
    clsAggEUScore(149) = 14.85
    clsAggEUScore(150) = 14.95
    clsAggEUScore(151) = 15.05
    clsAggEUScore(152) = 15.15
    clsAggEUScore(153) = 15.25
    clsAggEUScore(154) = 15.35
    clsAggEUScore(155) = 15.45
    clsAggEUScore(156) = 15.55
    clsAggEUScore(157) = 15.65
    clsAggEUScore(158) = 15.75
    clsAggEUScore(159) = 15.85
    clsAggEUScore(160) = 15.95
    clsAggEUScore(161) = 16.05
    clsAggEUScore(162) = 16.15
    clsAggEUScore(163) = 16.25
    clsAggEUScore(164) = 16.35
    clsAggEUScore(165) = 16.45
    clsAggEUScore(166) = 16.55
    clsAggEUScore(167) = 16.65
    clsAggEUScore(168) = 16.75
    clsAggEUScore(169) = 16.85
    clsAggEUScore(170) = 16.95
    clsAggEUScore(171) = 17.05
    clsAggEUScore(172) = 17.15
    clsAggEUScore(173) = 17.25
    clsAggEUScore(174) = 17.35
    clsAggEUScore(175) = 17.45
    clsAggEUScore(176) = 17.55
    clsAggEUScore(177) = 17.65
    clsAggEUScore(178) = 17.75
    clsAggEUScore(179) = 17.85
    clsAggEUScore(180) = 17.95
    clsAggEUScore(181) = 18.05
    clsAggEUScore(182) = 18.15
    clsAggEUScore(183) = 18.25
    clsAggEUScore(184) = 18.35
    clsAggEUScore(185) = 18.45
    clsAggEUScore(186) = 18.55
    clsAggEUScore(187) = 18.65
    clsAggEUScore(188) = 18.75
    clsAggEUScore(189) = 18.85
    clsAggEUScore(190) = 18.95
    clsAggEUScore(191) = 19.05
    clsAggEUScore(192) = 19.15
    clsAggEUScore(193) = 19.25
    clsAggEUScore(194) = 19.35
    clsAggEUScore(195) = 19.45
    clsAggEUScore(196) = 19.55
    clsAggEUScore(197) = 19.65
    clsAggEUScore(198) = 19.75
    clsAggEUScore(199) = 19.85
    clsAggEUScore(200) = 19.95
    ReDim clsDiversityScore(200)
    clsDiversityScore(0) = 0
    clsDiversityScore(1) = 0.1
    clsDiversityScore(2) = 0.2
    clsDiversityScore(3) = 0.3
    clsDiversityScore(4) = 0.4
    clsDiversityScore(5) = 0.5
    clsDiversityScore(6) = 0.6
    clsDiversityScore(7) = 0.7
    clsDiversityScore(8) = 0.8
    clsDiversityScore(9) = 0.9
    clsDiversityScore(10) = 1
    clsDiversityScore(11) = 1.05
    clsDiversityScore(12) = 1.1
    clsDiversityScore(13) = 1.15
    clsDiversityScore(14) = 1.2
    clsDiversityScore(15) = 1.25
    clsDiversityScore(16) = 1.3
    clsDiversityScore(17) = 1.35
    clsDiversityScore(18) = 1.4
    clsDiversityScore(19) = 1.45
    clsDiversityScore(20) = 1.5
    clsDiversityScore(21) = 1.55
    clsDiversityScore(22) = 1.6
    clsDiversityScore(23) = 1.65
    clsDiversityScore(24) = 1.7
    clsDiversityScore(25) = 1.75
    clsDiversityScore(26) = 1.8
    clsDiversityScore(27) = 1.85
    clsDiversityScore(28) = 1.9
    clsDiversityScore(29) = 1.95
    clsDiversityScore(30) = 2
    clsDiversityScore(31) = 2.0333
    clsDiversityScore(32) = 2.0667
    clsDiversityScore(33) = 2.1
    clsDiversityScore(34) = 2.1333
    clsDiversityScore(35) = 2.1667
    clsDiversityScore(36) = 2.2
    clsDiversityScore(37) = 2.2333
    clsDiversityScore(38) = 2.2667
    clsDiversityScore(39) = 2.3
    clsDiversityScore(40) = 2.3333
    clsDiversityScore(41) = 2.3667
    clsDiversityScore(42) = 2.4
    clsDiversityScore(43) = 2.4333
    clsDiversityScore(44) = 2.4667
    clsDiversityScore(45) = 2.5
    clsDiversityScore(46) = 2.5333
    clsDiversityScore(47) = 2.5667
    clsDiversityScore(48) = 2.6
    clsDiversityScore(49) = 2.6333
    clsDiversityScore(50) = 2.6667
    clsDiversityScore(51) = 2.7
    clsDiversityScore(52) = 2.7333
    clsDiversityScore(53) = 2.7667
    clsDiversityScore(54) = 2.8
    clsDiversityScore(55) = 2.8333
    clsDiversityScore(56) = 2.8667
    clsDiversityScore(57) = 2.9
    clsDiversityScore(58) = 2.9333
    clsDiversityScore(59) = 2.9667
    clsDiversityScore(60) = 3
    clsDiversityScore(61) = 3.025
    clsDiversityScore(62) = 3.05
    clsDiversityScore(63) = 3.075
    clsDiversityScore(64) = 3.1
    clsDiversityScore(65) = 3.125
    clsDiversityScore(66) = 3.15
    clsDiversityScore(67) = 3.175
    clsDiversityScore(68) = 3.2
    clsDiversityScore(69) = 3.225
    clsDiversityScore(70) = 3.25
    clsDiversityScore(71) = 3.275
    clsDiversityScore(72) = 3.3
    clsDiversityScore(73) = 3.325
    clsDiversityScore(74) = 3.35
    clsDiversityScore(75) = 3.375
    clsDiversityScore(76) = 3.4
    clsDiversityScore(77) = 3.425
    clsDiversityScore(78) = 3.45
    clsDiversityScore(79) = 3.475
    clsDiversityScore(80) = 3.5
    clsDiversityScore(81) = 3.525
    clsDiversityScore(82) = 3.55
    clsDiversityScore(83) = 3.575
    clsDiversityScore(84) = 3.6
    clsDiversityScore(85) = 3.625
    clsDiversityScore(86) = 3.65
    clsDiversityScore(87) = 3.675
    clsDiversityScore(88) = 3.7
    clsDiversityScore(89) = 3.725
    clsDiversityScore(90) = 3.75
    clsDiversityScore(91) = 3.775
    clsDiversityScore(92) = 3.8
    clsDiversityScore(93) = 3.825
    clsDiversityScore(94) = 3.85
    clsDiversityScore(95) = 3.875
    clsDiversityScore(96) = 3.9
    clsDiversityScore(97) = 3.925
    clsDiversityScore(98) = 3.95
    clsDiversityScore(99) = 3.975
    clsDiversityScore(100) = 4
    clsDiversityScore(101) = 4.01
    clsDiversityScore(102) = 4.02
    clsDiversityScore(103) = 4.03
    clsDiversityScore(104) = 4.04
    clsDiversityScore(105) = 4.05
    clsDiversityScore(106) = 4.06
    clsDiversityScore(107) = 4.07
    clsDiversityScore(108) = 4.08
    clsDiversityScore(109) = 4.09
    clsDiversityScore(110) = 4.1
    clsDiversityScore(111) = 4.11
    clsDiversityScore(112) = 4.12
    clsDiversityScore(113) = 4.13
    clsDiversityScore(114) = 4.14
    clsDiversityScore(115) = 4.15
    clsDiversityScore(116) = 4.16
    clsDiversityScore(117) = 4.17
    clsDiversityScore(118) = 4.18
    clsDiversityScore(119) = 4.19
    clsDiversityScore(120) = 4.2
    clsDiversityScore(121) = 4.21
    clsDiversityScore(122) = 4.22
    clsDiversityScore(123) = 4.23
    clsDiversityScore(124) = 4.24
    clsDiversityScore(125) = 4.25
    clsDiversityScore(126) = 4.26
    clsDiversityScore(127) = 4.27
    clsDiversityScore(128) = 4.28
    clsDiversityScore(129) = 4.29
    clsDiversityScore(130) = 4.3
    clsDiversityScore(131) = 4.31
    clsDiversityScore(132) = 4.32
    clsDiversityScore(133) = 4.33
    clsDiversityScore(134) = 4.34
    clsDiversityScore(135) = 4.35
    clsDiversityScore(136) = 4.36
    clsDiversityScore(137) = 4.37
    clsDiversityScore(138) = 4.38
    clsDiversityScore(139) = 4.39
    clsDiversityScore(140) = 4.4
    clsDiversityScore(141) = 4.41
    clsDiversityScore(142) = 4.42
    clsDiversityScore(143) = 4.43
    clsDiversityScore(144) = 4.44
    clsDiversityScore(145) = 4.45
    clsDiversityScore(146) = 4.46
    clsDiversityScore(147) = 4.47
    clsDiversityScore(148) = 4.48
    clsDiversityScore(149) = 4.49
    clsDiversityScore(150) = 4.5
    clsDiversityScore(151) = 4.51
    clsDiversityScore(152) = 4.52
    clsDiversityScore(153) = 4.53
    clsDiversityScore(154) = 4.54
    clsDiversityScore(155) = 4.55
    clsDiversityScore(156) = 4.56
    clsDiversityScore(157) = 4.57
    clsDiversityScore(158) = 4.58
    clsDiversityScore(159) = 4.59
    clsDiversityScore(160) = 4.6
    clsDiversityScore(161) = 4.61
    clsDiversityScore(162) = 4.62
    clsDiversityScore(163) = 4.63
    clsDiversityScore(164) = 4.64
    clsDiversityScore(165) = 4.65
    clsDiversityScore(166) = 4.66
    clsDiversityScore(167) = 4.67
    clsDiversityScore(168) = 4.68
    clsDiversityScore(169) = 4.69
    clsDiversityScore(170) = 4.7
    clsDiversityScore(171) = 4.71
    clsDiversityScore(172) = 4.72
    clsDiversityScore(173) = 4.73
    clsDiversityScore(174) = 4.74
    clsDiversityScore(175) = 4.75
    clsDiversityScore(176) = 4.76
    clsDiversityScore(177) = 4.77
    clsDiversityScore(178) = 4.78
    clsDiversityScore(179) = 4.79
    clsDiversityScore(180) = 4.8
    clsDiversityScore(181) = 4.81
    clsDiversityScore(182) = 4.82
    clsDiversityScore(183) = 4.83
    clsDiversityScore(184) = 4.84
    clsDiversityScore(185) = 4.85
    clsDiversityScore(186) = 4.86
    clsDiversityScore(187) = 4.87
    clsDiversityScore(188) = 4.88
    clsDiversityScore(189) = 4.89
    clsDiversityScore(190) = 4.9
    clsDiversityScore(191) = 4.91
    clsDiversityScore(192) = 4.92
    clsDiversityScore(193) = 4.93
    clsDiversityScore(194) = 4.94
    clsDiversityScore(195) = 4.95
    clsDiversityScore(196) = 4.96
    clsDiversityScore(197) = 4.97
    clsDiversityScore(198) = 4.98
    clsDiversityScore(199) = 4.99
    clsDiversityScore(200) = 5
End Sub
Private Sub CalcCollateralPrincipalAmount(iPrinProceeds As Double)
    Dim i As Long
    Dim lAsset As Asset
    Dim lNumerator As Double
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    clsCollateralPrincipalAmount = lNumerator + iPrinProceeds
    Set lAsset = Nothing
    clsPrinProceeds = iPrinProceeds

End Sub

Public Sub RunTest(iAssetDict As Dictionary, iPrincipalProceeds As Double)
    ReDim clsResults(0)
    Dim lMoodyRecoveryRate As Double
    Dim lkeys As Variant
    Dim i As Long
    
    Set clsAssetsDic = iAssetDict
    Call CalcCollateralPrincipalAmount(iPrincipalProceeds)
    lkeys = clsTestThresholdDict.Keys
    For i = LBound(lkeys) To UBound(lkeys)
        Select Case lkeys(i)
        Case TestNum.LimitationOnSeniorSecuredLoans
            Call LimitationOnSeniorSecuredLoans
        Case TestNum.LimitationOnAssetNotSeniorSecuredLoans
            Call LimitationOnNonSeniorSecuredLoans
        Case TestNum.LimitationOn6LargestObligor
            Call LimitationOnObligor
        Case TestNum.LimitationOn1LagestObligor
            'Call LimitationOnObligor
        Case TestNum.LimitationOnObligorDIP
             Call LimitationOnDIPObligor
        Case TestNum.LimitationOnObligornotSeniorSecured
            Call LimitationOnNonSeniorSecuredObligor
        Case TestNum.LimitationonCasAssets
            Call LimitationOnCaaLoans
        Case TestNum.LimitationonAssetspaylessFrequentlyQuarterly
            Call LimitationOnAssetPayyLessFrequentlyQuarterly
        Case TestNum.LimitationOnFixedRateAssets
            Call LimitationOnFixedRateObligations
        Case TestNum.LimitationonCurrentPayAssets
            Call LimitationOnCurrentPayObligations
        Case TestNum.LimitationOnDIPAssets
            Call LimitationOnDIPObligations
        Case TestNum.LimmitationOnUnfundedcommitments
            Call LimitationOnUnfundedCommitments
        Case TestNum.LimitationOnParticipationInterest
            Call LimitationOnParticipationInt
        Case TestNum.LimitationOnCountriesNotUS
            Call LimitationOnCountryNotUSA
        Case TestNum.LimitationOnCountriesCanadaandTaxJurisdictions
            Call LimitationOnCountryCanadaTaxJurisdiction
        Case TestNum.LimitationonCountriesNotUSCanadaUK
            Call LimitationonCountriesNotUSCanadaUK
        Case TestNum.LimitationOnGroupCountries
            Call LimitationOnGroupCountries
        Case TestNum.LimitationOnGroupICountries
            Call LimitationOnGroupICountries
        Case TestNum.LimitationOnIndividualGroupICountries
            'Call LimitationOnGroupICountries
        Case TestNum.LimitationOnGroupIICountries
            Call LimitationOnGroupIICountries
        Case TestNum.LimitationonIndividualGroupIICountries
            'Call LimitationOnGroupIICountries
        Case TestNum.LimitationOnGroupIIICountries
            Call LimitationOnGroupIIICountries
        Case TestNum.LimitationonIndividualGroupIIICountries
            'Call LimitationOnGroupIIICountries
        Case TestNum.LimitationOnTaxJurisdictions
            Call LimitationOnTaxJurisdictions
        Case TestNum.LimitationOn4SPIndustryClassification
            Call LimitationOnSPIndustryClassification
        Case TestNum.LimitationOn2SPClassification
            'Call LimitationOnSPIndustryClassification
        Case TestNum.LimitationOn1SPClassification
            'Call LimitationOnSPIndustryClassification
        Case TestNum.LimitationOn1MoodyIndustry
            Call LimitationOnMoodyIndustryClassification
        Case TestNum.LimitationOnBridgeLoans
            Call LimitationOnBridgeLoans
        Case TestNum.LimitationOnCovLite
            Call LimitationOnCovLite
        Case TestNum.LimitationonDeferrableSecuriies
            Call LimitationonDeferrableSecuriies
        Case TestNum.LimitationonFacilitiySize
            Call LimitationonFacilitiySize
        Case TestNum.LimitationonFacilitiySizeMAG08
            Call LimitationonFacilitiySizeMAG8
        Case TestNum.WeightedAverateSpread
            Call WeightedAverageSpread
        Case TestNum.WeightedAverageMoodyRecoveryRate
            Call WeightedAverageRecoveryRate
        Case TestNum.WeightedAverageCoupon
            Call WeightedAverageCoupon
        Case TestNum.WeightedAverageLife
            Call WeightedAverageLife
        Case TestNum.WeightedAverageRatingFactor
            Call WeightedAverageRatingFactor
        Case TestNum.WeightedAverageRatingFactorMAG14
            Call WeightedAverageRatingFactorMAG14
        Case TestNum.MoodysDiversity
            Call CalcDiversityScore
        Case TestNum.JROCTEST
            Call CalcJROCTEST(iPrincipalProceeds)
        Case TestNum.WeightedAverageSpreadMag14
            Call WeightedAverageSpreadMag14
        Case TestNum.LimitationonCCCObligations
            Call LimitationOnCCCLoans
        Case TestNum.LimitationOnCanada
            Call LimitationOnCountryCanada
        Case TestNum.LimitationOnLetterOfCredit
            Call LimitationOnLetterOfCredit
        Case TestNum.LimitationOnLongDated
            Call LimitationOnLongDated
        Case TestNum.LimitationOnUnsecuredLoans
            Call LimitationOnUnsecured
        Case TestNum.LimitationOnSwapNonDiscount
            Call LimitationOnSwapNonDiscount
        Case TestNum.WeightedAverageSpreadMag06
            Call WeightedAverageSpreadMag06
        Case TestNum.LimitationOnNonEmergingMarketObligors
            Call LimitationOnNonEmergingMarket
        Case TestNum.LimitationOnSPCriteria
            Call LimitationOnSPCriteria
        End Select
        'Debug.Print i
    Next i

End Sub
Public Function GetResultOutput() As Variant
    Dim i As Long
    Dim lNumResults As Long
    Dim lOutputVar As Variant
    
    lNumResults = clsTestThresholdDict.Count
    ReDim lOutputVar(0 To lNumResults + 1, 0 To 8)
    lOutputVar(0, 0) = "Test Num"
    lOutputVar(0, 1) = "Test Name"
    lOutputVar(0, 2) = "Denominator"
    lOutputVar(0, 3) = "Numeratior"
    lOutputVar(0, 4) = "comments"
    lOutputVar(0, 5) = "Results"
    lOutputVar(0, 6) = "Threshold"
    lOutputVar(0, 7) = "Pass/Fail"
    lOutputVar(0, 8) = "Comments on Pass/Fail"
    
    For i = 1 To lNumResults
        lOutputVar(i, 0) = clsResults(i - 1).TestNumber
        lOutputVar(i, 1) = clsResults(i - 1).TestName
        lOutputVar(i, 2) = clsResults(i - 1).Denominator
        lOutputVar(i, 3) = clsResults(i - 1).Numerator
        lOutputVar(i, 4) = clsResults(i - 1).Comments
        lOutputVar(i, 5) = clsResults(i - 1).Result
        lOutputVar(i, 6) = clsResults(i - 1).Threshold
        lOutputVar(i, 7) = clsResults(i - 1).PassFail
        lOutputVar(i, 8) = clsResults(i - 1).PassFailComment
        
        Select Case CLng(lOutputVar(i, 0))
        Case 36, 35, 37, 54
            lOutputVar(i, 5) = Format(lOutputVar(i, 5), "0.000")
            lOutputVar(i, 6) = Format(lOutputVar(i, 6), "0.000")
        Case Else
            lOutputVar(i, 5) = Format(lOutputVar(i, 5), "0.0000%")
            lOutputVar(i, 6) = Format(lOutputVar(i, 6), "0.0000%")
        End Select
    Next i
    If Not (clsObjWeights Is Nothing) Then
        lOutputVar(lNumResults + 1, 5) = "Objective Function"
        lOutputVar(lNumResults + 1, 6) = CalcObjectiveFunction()
    End If
    GetResultOutput = lOutputVar
End Function



Public Function GetResults() As Results()
    Dim i As Long
    If Len(clsResults(UBound(clsResults)).TestName) > 0 Then
        GetResults = clsResults
        Exit Function
    End If
    Do While Len(clsResults(i).TestName) > 0
        i = i + 1
    Loop
    If i > 1 Then ReDim Preserve clsResults(i - 1)
    GetResults = clsResults
End Function

Private Sub AddResults(iTestResult As Results)
    Dim lResultsNum As Long
    
    Call CheckResults(iTestResult)
    
    lResultsNum = UBound(clsResults)
    If Len(clsResults(lResultsNum).TestName) <> 0 Then
        ReDim Preserve clsResults(lResultsNum + 10)
    End If
    lResultsNum = LBound(clsResults)
    Do While Len(clsResults(lResultsNum).TestName) <> 0
        lResultsNum = lResultsNum + 1
    Loop
    With clsResults(lResultsNum)
        .TestNumber = iTestResult.TestNumber
        .PassFail = iTestResult.PassFail
        .Result = iTestResult.Result
        .TestName = iTestResult.TestName
        .Threshold = iTestResult.Threshold
        .Comments = iTestResult.Comments
        .Denominator = iTestResult.Denominator
        .Numerator = iTestResult.Numerator
        .PassFailComment = iTestResult.PassFailComment
    End With
    
End Sub

'LimitationOnSeniorSecuredLoans
Private Sub LimitationOnSeniorSecuredLoans()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.BondLoan = "LOAN" Then
                lNumerator = lAsset.ParAmount + lNumerator
            End If
            If lAsset.MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                lNumerator = lNumerator - lAsset.ParAmount
            End If
        End If
    Next i
    lNumerator = lNumerator + clsPrinProceeds
    With lResults
        .TestNumber = TestNum.LimitationOnSeniorSecuredLoans
        .TestName = "Limitation on Senior Secured Loans"
        .Threshold = 0.9
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result > .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
'LimitationOnAssetNotSeniorSecuredLoans
Private Sub LimitationOnNonSeniorSecuredLoans()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        
        If Not (lAsset.Seniority = "SENIOR SECURED" And lAsset.BondLoan = "LOAN") Then
            lNumerator = lAsset.ParAmount + lNumerator
        ElseIf lAsset.SPPriorityCategory = "SENIOR UNSECURED LOAN/SECOND LIEN LOAN" Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnAssetNotSeniorSecuredLoans
        .TestName = "Limitation on non Senior Secured Loans"
        .Threshold = 0.1
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnObligor()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If Not (lAsset.DIP) Then
                If lObligors.Exists(lAsset.IssuerId) Then
                    lObligors.Item(lAsset.IssuerId) = lObligors.Item(lAsset.IssuerId) + lAsset.ParAmount
                Else
                    lObligors.Add lAsset.IssuerId, lAsset.ParAmount
                End If
            End If
        End If
    Next i
    Call SortDictionary(lObligors, False, True)
    lItems = lObligors.Items
    lkeys = lObligors.Keys
    'LimitationOn6LargestObligor
    With lResult
        .TestNumber = LimitationOn6LargestObligor
        .Comments = lkeys(5)
        .TestName = "Limitaton on the 6th largest obligor"
        .Result = lItems(5) / clsCollateralPrincipalAmount
        .Threshold = 0.02
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(5)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    'LimitationOn1LagestObligor
    With lResult
        .TestNumber = LimitationOn1LagestObligor
        .Comments = lkeys(0)
        .TestName = "Limitaton on the 1st largest obligor"
        .Result = lItems(0) / clsCollateralPrincipalAmount
        .Threshold = 0.025
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(0)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub

Private Sub LimitationOnDIPObligor()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.DIP Then
                If lObligors.Exists(lAsset.IssuerId) Then
                    lObligors.Item(lAsset.IssuerId) = lObligors.Item(lAsset.IssuerId) + lAsset.ParAmount
                Else
                    lObligors.Add lAsset.IssuerId, lAsset.ParAmount
                End If
            End If
        End If
    Next i
        
    Call SortDictionary(lObligors, True)
    lItems = lObligors.Items
    lkeys = lObligors.Keys

    'LimitationOnDIPLargestObligor
    With lResult
        .TestNumber = LimitationOnObligorDIP
        .Comments = lkeys(0)
        .TestName = "Limitaton on the 1st largest obligor for DIP"
        .Result = lItems(0) / clsCollateralPrincipalAmount
        .Threshold = 0.02
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(0)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub
'LimitationOnObligornotSeniorSecured
Private Sub LimitationOnNonSeniorSecuredObligor()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.SPPriorityCategory = "SENIOR UNSECURED LOAN/SECOND LIEN LOAN" Then
                If lObligors.Exists(lAsset.IssuerId) Then
                    lObligors.Item(lAsset.IssuerId) = lObligors.Item(lAsset.IssuerId) + lAsset.ParAmount
                Else
                    lObligors.Add lAsset.IssuerId, lAsset.ParAmount
                End If
            End If
        End If
    Next i
            
    If lObligors.Count > 0 Then
        Call SortDictionary(lObligors, False, True)
        lItems = lObligors.Items
        lkeys = lObligors.Keys
        With lResult
            .Comments = lkeys(0)
            .Result = lItems(0) / clsCollateralPrincipalAmount
            
            .Numerator = lItems(0)
        End With
    End If

    With lResult
        .TestNumber = LimitationOnObligornotSeniorSecured
        .TestName = "Limitaton on the 1st largest obligor of non Senior Secured Loans"
        .Threshold = 0.02
        .Denominator = clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub





Private Sub LimitationOnCaaLoans()
    'LimitationonCasAssets
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case UCase(lAsset.MDYRating)
            
            Case "CAA1", "CAA2", "CAA3", "CA", "C"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationonCasAssets
        .TestName = "Limitation on Caa Loans"
        .Threshold = 0.075
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnCCCLoans()
    'LimitationonCasAssets
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case UCase(lAsset.SPRating)
            
            Case "CCC+", "CCC", "CCC-", "CC", "C"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationonCCCObligations
        .TestName = "Limitation on CCC Loans"
        .Threshold = 0.075
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnAssetPayyLessFrequentlyQuarterly()
    'LimitationonAssetspaylessFrequentlyQuarterly
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.PaymentFreq < 4 Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationonAssetspaylessFrequentlyQuarterly
        .TestName = "Limitation on Collateral Obligations that pay interest less frequently than quarterly"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        'If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub




Private Sub LimitationOnFixedRateObligations()
    'LimitationonFixedRateObligations
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        
        If lAsset.CouponType = "FIXED" And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnFixedRateAssets
        .TestName = "Limitation on Fixed Rate Obligations"
        .Threshold = 0.025
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub



Private Sub LimitationOnCurrentPayObligations()
    'LimitationonCurrentPayAssets
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.CurrentPay And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationonCurrentPayAssets
        .TestName = "Limitation on Current Pay Obligations"
        .Threshold = 0.025
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub




Private Sub LimitationOnDIPObligations()
    'LimitationOnDIPAssets
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.DIP And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnDIPAssets
        .TestName = "Limitation on DIP Obligations"
        .Threshold = 0.075
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub

'LimmitationOnUnfundedcommitments
Private Sub LimitationOnUnfundedCommitments()

    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.DefaultAsset = False Then
            lNumerator = lAsset.UnfundedAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimmitationOnUnfundedcommitments
        .TestName = "Limitation on Unfunded Commites"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnParticipationInt()
    'LimitationOnParticipationInterest
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.Participation And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnParticipationInterest
        .TestName = "Limitation on Participation Interest"
        .Threshold = 0.15
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub

Private Sub LimitationOnSPCriteria()

    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.Participation And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnSPCriteria
        .TestName = "Limitation on S&P Criteria"
        .Threshold = 0.15
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
'LimitationOnCountriesNotUS
Private Sub LimitationOnCountryNotUSA()
    'LimitationOnParticipationInterest
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.Country <> "USA" And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnCountriesNotUS
        .TestName = "Limitation on countries other then the United States"
        .Threshold = 0.2
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub

Private Sub LimitationOnCountryCanadaTaxJurisdiction()
    'LimitationOnCountriesCanadaandTaxJurisdictions
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            Case "CANADA", "BAHAMAS", "BERMUDA", "BRITISH VIRGIN ISLANDS", "CAYMEN ISLANDS", "CHANNEL ISLANDS", "NETHERLANDS ANTULLES", "CAYMAN ISLANDS"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnCountriesCanadaandTaxJurisdictions
        .TestName = "Limitation on countries that are Tax Jurisdictions or Canada"
        .Threshold = 0.125
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnCountryCanada()
    'LimitationOnCountriesCanadaandTaxJurisdictions
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            Case "CANADA"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = LimitationOnCanada
        .TestName = "Limitation on Canada"
        .Threshold = 0.125
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnNonEmergingMarket()
    
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            
            Case "Test"
                'I'm unable to test for countries that are domiciled in a country with a foreign currency issuer credit rating below "AA" by S&P
            Case Else
                lNumerator = lNumerator + lAsset.ParAmount
            End Select
        End If
    Next i
    lNumerator = lNumerator + clsPrinProceeds
    With lResults
        .TestNumber = LimitationOnNonEmergingMarketObligors
        .TestName = "Limitation on Non-Emerging Market Obligot"
        .Threshold = 0.125
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationonCountriesNotUSCanadaUK()
    'LimitationonCountriesNotUSCanadaUK
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            Case "CANADA", "UK", "USA", "UNITED KINGDOM"
            
            Case Else
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationonCountriesNotUSCanadaUK
        .TestName = "Limitation on countries other that are not USA, Canada, or UK"
        .Threshold = 0.1
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub



Private Sub LimitationOnGroupCountries()
    'LimitationOnGroupCountries
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            Case "NETHERLANDS", "AUSTRALIA", "NEW ZEALAND", "UNITED KINGDOM", "GERMANY", "SWEDEN", "SWITZERLAND", "AUSTRIA", "BELGIUM", "DENMARK", "FINLAND", "FRANCE", "ICELAND", "LIECHTENSTEIN", "LUXEMBOURG", "NORWAY", "SPAIN"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnGroupCountries
        .TestName = "Limitation on Group Countries"
        .Threshold = 0.15
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnGroupICountries()
'LimitationOnGroupICountries
'LimitationOnIndividualGroupICountries
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    Dim lNumerator As Double
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            
            Case "NETHERLANDS", "AUSTRALIA", "NEW ZEALAND", "UNITED KINGDOM"
                lNumerator = lNumerator + lAsset.ParAmount
                If lObligors.Exists(lAsset.Country) Then
                    lObligors.Item(lAsset.Country) = CDbl(lObligors.Item(lAsset.Country)) + CDbl(lAsset.ParAmount)
                Else
                    lObligors.Add lAsset.Country, CDbl(lAsset.ParAmount)
                End If
            End Select
        End If
    Next i
    With lResult
        .Comments = ""
        .TestNumber = TestNum.LimitationOnGroupICountries
        .TestName = "Limitaton on Group I Countries"
        .Result = lNumerator / clsCollateralPrincipalAmount
        .Threshold = 0.15
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
        
    Call AddResults(lResult)
    
    If lObligors.Count <> 0 Then
    'LimitationOnIndividualGroupICountries
        Call SortDictionary(lObligors, False, False)
        lItems = lObligors.Items
        lkeys = lObligors.Keys
        If lItems(0) < lItems(lObligors.Count - 1) Then
            i = lObligors.Count - 1
        Else
            i = 0
        End If
        With lResult
            .Comments = lkeys(i)
            .Result = lItems(i) / clsCollateralPrincipalAmount
            .Numerator = lItems(i)
        End With
    End If

    With lResult
        .TestNumber = LimitationOnIndividualGroupICountries
        .TestName = "Limitaton on individual Group I Countries"
        .Threshold = 0.05
        If .Result < .Threshold Then .PassFail = True
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnGroupIICountries()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    Dim lNumerator As Double
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            
            Case "GERMANY", "SWEDEN", "SWITZERLAND"
                lNumerator = lNumerator + lAsset.ParAmount
                If lObligors.Exists(lAsset.Country) Then
                    lObligors.Item(lAsset.Country) = lObligors.Item(lAsset.Country) + lAsset.ParAmount
                Else
                    lObligors.Add lAsset.Country, lAsset.ParAmount
                End If
            End Select
        End If
    Next i
    
    
    'LimitationOnGroupIICountries
    With lResult
        .TestNumber = TestNum.LimitationOnGroupIICountries
        .Comments = ""
        .TestName = "Limitaton on Group II Countries"
        .Result = lNumerator / clsCollateralPrincipalAmount
        .Threshold = 0.1
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResult)
        
        
    'LimitationOnIndividualGroupIICountries
    If lObligors.Count <> 0 Then
        Call SortDictionary(lObligors, False)
        lItems = lObligors.Items
        lkeys = lObligors.Keys
        If lItems(0) < lItems(lObligors.Count - 1) Then
            i = lObligors.Count - 1
        Else
            i = 0
        End If
        With lResult
            .Comments = lkeys(i)
            .Result = lItems(i) / clsCollateralPrincipalAmount
            .Numerator = lItems(i)
        End With
    End If

    With lResult
        .TestNumber = TestNum.LimitationonIndividualGroupIICountries
        .TestName = "Limitaton on individual Group II Countries"
        .Threshold = 0.05
        If .Result < .Threshold Then .PassFail = True
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnGroupIIICountries()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    Dim lNumerator As Double
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            
            Case "AUSTRIA", "BELGIUM", "DENMARK", "FINLAND", "FRANCE", "ICELAND", "LIECHTENSTEIN", "LUXEMBOURG", "NORWAY", "SPAIN"
                lNumerator = lNumerator + lAsset.ParAmount
                If lObligors.Exists(lAsset.Country) Then
                    lObligors.Item(lAsset.Country) = lObligors.Item(lAsset.Country) + lAsset.ParAmount
                Else
                    lObligors.Add lAsset.Country, lAsset.ParAmount
                End If
            End Select
        End If
    Next i
    'LimitationOnGroupIIiCountries
    With lResult
        .TestNumber = TestNum.LimitationOnGroupIIICountries
        .Comments = ""
        .TestName = "Limitaton on Group III Countries"
        .Result = lNumerator / clsCollateralPrincipalAmount
        .Threshold = 0.075
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
        
    If lObligors.Count <> 0 Then
    'LimitationOnIndividualGroupIIICountries
        Call SortDictionary(lObligors, False)
        lItems = lObligors.Items
        lkeys = lObligors.Keys
        If lItems(0) < lItems(lObligors.Count - 1) Then
            i = lObligors.Count - 1
        Else
            i = 0
        End If
        With lResult
            .Comments = lkeys(i)
            .Result = lItems(i) / clsCollateralPrincipalAmount
            .Numerator = lItems(i)
        End With
    End If

    With lResult
        .TestNumber = TestNum.LimitationonIndividualGroupIIICountries
        .TestName = "Limitaton on individual Group III Countries"
        .Threshold = 0.05
        If .Result < .Threshold Then .PassFail = True
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnTaxJurisdictions()
    ''LimitationOnTaxJurisdictions
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            Select Case lAsset.Country
            Case "BAHAMAS", "BERMUDA", "BRITISH VIRGIN ISLANDS", "CAYMEN ISLANDS", "CHANNEL ISLANDS", "NETHERLANDS ANTULLES", "CAYMAN ISLANDS"
                lNumerator = lAsset.ParAmount + lNumerator
            End Select
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnTaxJurisdictions
        .TestName = "Limitation on Tax Jurisdictions"
        .Threshold = 0.075
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnSPIndustryClassification()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)

        If lObligors.Exists(lAsset.SPIndustry) Then
            lObligors.Item(lAsset.SPIndustry) = lObligors.Item(lAsset.SPIndustry) + lAsset.ParAmount
        Else
            lObligors.Add lAsset.SPIndustry, lAsset.ParAmount
        End If
      
    Next i
    Call SortDictionary(lObligors, False, True)
    lItems = lObligors.Items
    lkeys = lObligors.Keys
    'LimitationOn4S&PIndustryClassification
    With lResult
        .TestNumber = LimitationOn4SPIndustryClassification
        .Comments = lkeys(3)
        .TestName = "Limitaton on the 4th largest S&P Industry Classification"
        .Result = lItems(3) / clsCollateralPrincipalAmount
        .Threshold = 0.1
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(3)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    'LimitationOn2LagestSPIndustryClassification
    With lResult
        .TestNumber = LimitationOn2SPClassification
        .Comments = lkeys(1)
        .TestName = "Limitaton on the 2nd largest Industry Classification"
        .Result = lItems(1) / clsCollateralPrincipalAmount
        .Threshold = 0.12
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(1)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    'LimitationOn1LagestSPIndustryClassification
    With lResult
        .TestNumber = LimitationOn1SPClassification
        .Comments = lkeys(0)
        .TestName = "Limitaton on the 1st largest S&P Industry Classification"
        .Result = lItems(0) / clsCollateralPrincipalAmount
        .Threshold = 0.15
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(0)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    Set lAsset = Nothing
End Sub

Private Sub LimitationOnBridgeLoans()
    'LimitationOnBridgeLoans
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.BridgeLoan And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnBridgeLoans
        .TestName = "Limitation on Bridge Loan Obligations"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub

Private Sub LimitationOnCovLite()
    'LimitationOnCovLite
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.CovLite Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnCovLite
        .TestName = "Limitation on Cov-Lite Loans"
        .Threshold = 0.6
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub

Private Sub LimitationonDeferrableSecuriies()
    'LimitationonDeferrableSecuriies
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.PikAsset And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationonDeferrableSecuriies
        .TestName = "Limitation on Deferabble Securities"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnLetterOfCredit()
    'LimitationOnLetterOfCredit
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.LOC And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnLetterOfCredit
        .TestName = "Limitation on Letter of Credit"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnLongDated()
    'LimitationOnLetterOfCredit
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lStatedMaturity As Date
    
    lStatedMaturity = clsTestInputDict("Stated Maturity Date")
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.Maturity > lStatedMaturity And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnLongDated
        .TestName = "Limitation on Long Dated"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnUnsecured()
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.Seniority <> "SENIOR SECURED" And lAsset.DefaultAsset = False Then
            lNumerator = lAsset.ParAmount + lNumerator
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnUnsecuredLoans
        .TestName = "Limitation on Unsecured Loans"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationOnSwapNonDiscount()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
    
        If lAsset.DefaultAsset = False Then
            'lNumerator = lAsset.ParAmount + lNumerator
            'No test for now
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationOnSwapNonDiscount
        .TestName = "Limitation on Swap Non Discount"
        .Threshold = 0.05
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub


'LimitationonFacilitiySize
Private Sub LimitationonFacilitiySize()
    'LimitationonDeferrableSecuriies
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.Country = "USA" And lAsset.FacilitySize < 150000000 Then
                lNumerator = lAsset.ParAmount + lNumerator
            ElseIf lAsset.Country <> "USA" And lAsset.FacilitySize < 250000000 Then
                lNumerator = lAsset.ParAmount + lNumerator
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationonFacilitiySize
        .TestName = "Limitation on Facility Size"
        .Threshold = 0.07
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub LimitationonFacilitiySizeMAG8()
    'This one dosen't have different facility sizes for USA and other countries
    
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.FacilitySize < 200000000 Then
                lNumerator = lAsset.ParAmount + lNumerator
                'Debug.Print lAsset.IssueName
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.LimitationonFacilitiySizeMAG08
        .TestName = "Limitation on Facility Size"
        .Threshold = 0.07
        .Result = lNumerator / clsCollateralPrincipalAmount
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lNumerator
        .Denominator = clsCollateralPrincipalAmount
    End With
    
    Call AddResults(lResults)
    
    Set lAsset = Nothing
End Sub
Private Sub WeightedAverageSpread()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lLIBOR As Double
    Dim lCollateralBalance As Double
    Dim lMoodysRecoveryRate As Double
    Dim lMoodysAdjustmentFactor As Double
    Dim lWAS As Double
    Dim lRinvestBal As Double
    Dim lDenominator As Double
    Dim lThreshold As Double
    

    'Set inputs
    lLIBOR = clsTestInputDict("Current LIBOR")
    lRinvestBal = clsTestInputDict("Reinvestment Target Balance")
    lMoodysRecoveryRate = clsTestInputDict("MWARR")
    lWAS = clsTestInputDict("Weighted Average Spread")
    If lWAS >= 0.031 Then
        lMoodysAdjustmentFactor = 0.00065
    Else
        lMoodysAdjustmentFactor = 0.0005
    End If
    
    lThreshold = lWAS - (lMoodysRecoveryRate * 100 - 43) * lMoodysAdjustmentFactor
    clsTestThresholdDict(TestNum.WeightedAverateSpread).Thresholds = lThreshold

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.CouponType = "FLOAT" Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
            If InStr(lAsset.Index, "LIBOR") Then
                If lAsset.LiborFloor > lLIBOR Then
                    lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
                Else
                    lNumerator = lNumerator + lAsset.CpnSpread * lAsset.ParAmount
                End If
            Else
                lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = WeightedAverateSpread
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = lThreshold
        .TestName = "Minimum Floating Spread Test"
        .Result = lNumerator / lCollateralBalance
        If .Result > .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
    
    
End Sub
Private Sub WeightedAverageSpreadMag14()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lLIBOR As Double
    Dim lCollateralBalance As Double
    Dim lMoodysRecoveryRate As Double
    Dim lMoodysAdjustmentFactor As Double
    Dim lWARRThreshhold As Double
    Dim lWAS As Double
    Dim lRinvestBal As Double
    Dim lDenominator As Double
    Dim lThreshold As Double
    

    'Set inputs
    lLIBOR = clsTestInputDict("Current LIBOR")
    lRinvestBal = clsTestInputDict("Reinvestment Target Balance")
    lMoodysRecoveryRate = clsTestInputDict("MWARR")
    lWAS = clsTestInputDict("Weighted Average Spread")
    lMoodysAdjustmentFactor = clsTestInputDict("WAS Factor")
    lWARRThreshhold = clsTestInputDict("WARR Threshold")
    
    lThreshold = lWAS - (lMoodysRecoveryRate - lWARRThreshhold) * 100 * lMoodysAdjustmentFactor
    clsTestThresholdDict(TestNum.WeightedAverageSpreadMag14).Thresholds = lThreshold

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.CouponType = "FLOAT" Then
                lCollateralBalance = lCollateralBalance + lAsset.ParAmount
                If InStr(lAsset.Index, "LIBOR") Then
                    If lAsset.LiborFloor > lLIBOR Then
                        lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
                    Else
                        lNumerator = lNumerator + lAsset.CpnSpread * lAsset.ParAmount
                    End If
                Else
                    lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
                End If
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.WeightedAverageSpreadMag14
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = lThreshold
        .TestName = "Minimum Floating Spread Test"
        .Result = lNumerator / lCollateralBalance
        If .Result > .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
    
    
End Sub
Private Sub WeightedAverageSpreadMag06()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lLIBOR As Double
    Dim lCollateralBalance As Double
    Dim lMoodysRecoveryRate As Double
    Dim lMoodysAdjustmentFactor As Double
    Dim lWARRThreshhold As Double
    Dim lWAS As Double
    Dim lRinvestBal As Double
    Dim lDenominator As Double
    Dim lThreshold As Double
    

    'Set inputs
    lLIBOR = clsTestInputDict("Current LIBOR")
    lRinvestBal = clsTestInputDict("Reinvestment Target Balance")
    lMoodysRecoveryRate = clsTestInputDict("MWARR")

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            If lAsset.CouponType = "FLOAT" Then
                lCollateralBalance = lCollateralBalance + lAsset.ParAmount
                If InStr(lAsset.Index, "LIBOR") Then
                    If lAsset.LiborFloor > lLIBOR Then
                        lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
                    Else
                        lNumerator = lNumerator + lAsset.CpnSpread * lAsset.ParAmount
                    End If
                Else
                    lNumerator = lNumerator + (lAsset.Coupon - lLIBOR) * lAsset.ParAmount
                End If
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.WeightedAverageSpreadMag06
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = lThreshold
        .TestName = "Minimum Floating Spread Test"
        .Result = lNumerator / lCollateralBalance
        If .Result > .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
    
    
End Sub


Private Sub WeightedAverageRecoveryRate()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
            lNumerator = lNumerator + lAsset.MDYRecoveryRate * lAsset.ParAmount
        End If
    Next i
    With lResults
        .TestNumber = WeightedAverageMoodyRecoveryRate
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = 0.47
        .TestName = "Minimum Weighted Average Moody’s Recovery Rate Test"
        .Result = lNumerator / lCollateralBalance
        If .Result > .Threshold Then .PassFail = True
        If clsTestInputDict.Exists("MWARR") Then
            clsTestInputDict("MWARR") = .Result
        Else
            clsTestInputDict.Add "MWARR", .Result
        End If
    End With
    Call AddResults(lResults)
    
End Sub

Private Sub WeightedAverageCoupon()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.CouponType = "FIXED" Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
            lNumerator = lNumerator + lAsset.Coupon * lAsset.ParAmount
        End If
    Next i
    With lResults
        .TestNumber = TestNum.WeightedAverageCoupon
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = 0.07
        .TestName = "Minimum Weighted Average Coupon Test"
        If lCollateralBalance > 0 Then
            .Result = lNumerator / lCollateralBalance
            If .Result >= .Threshold Then .PassFail = True
        Else
            .PassFail = True
        End If
    End With
    Call AddResults(lResults)
    
End Sub

Private Sub WeightedAverageLife()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double

    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
        End If
        lNumerator = lNumerator + lAsset.WAL * lAsset.ParAmount

    Next i
    With lResults
        .TestNumber = TestNum.WeightedAverageLife
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .TestName = "Weighted Average Life Test"
        If lCollateralBalance > 0 Then .Result = Round(lNumerator / lCollateralBalance, 2)
        If .Result < .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
End Sub

Private Sub WeightedAverageRatingFactor()
    Dim lRatingFactors As Dictionary
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double
    Dim lMoodysAdjustmentFactor As Long
    Dim lMoodysRecoveryRate As Double
    Dim lWARFThreshold As Long
    Dim lWARFFactor As Long
    Dim lThreshold As Double
    
    'Set inputs
    lMoodysRecoveryRate = clsTestInputDict("MWARR")
    lWARFThreshold = clsTestInputDict("WARF Threshold")
    lWARFFactor = clsTestInputDict("WARF Factor")
    lThreshold = lWARFThreshold + (lMoodysRecoveryRate * 100 - 43) * lWARFFactor
    clsTestThresholdDict(TestNum.WeightedAverageRatingFactor).Thresholds = lThreshold
    
    Set lRatingFactors = LoadingRatingFactor
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
            If lRatingFactors.Exists(UCase(lAsset.MDYDPRatingWARF)) Then
                lNumerator = lNumerator + lAsset.ParAmount * lRatingFactors.Item(UCase(lAsset.MDYDPRatingWARF))
            Else
                lNumerator = lNumerator + lAsset.ParAmount * 10000
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.WeightedAverageRatingFactor
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = lThreshold
        .TestName = "Maximum Moody's Rating Factor Test"
        If lCollateralBalance > 0 Then .Result = lNumerator / lCollateralBalance
        If .Result < .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
End Sub
Private Sub WeightedAverageRatingFactorMAG14()
    Dim lRatingFactors As Dictionary
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double
    Dim lMoodysAdjustmentFactor As Long
    Dim lMoodysRecoveryRate As Double
    Dim lWARFThreshold As Long
    Dim lWARFFactor As Long
    Dim lThreshold As Double
    Dim lWARRThreshhold As Double
    'Set inputs
    lMoodysRecoveryRate = clsTestInputDict("MWARR")
    lWARFThreshold = clsTestInputDict("WARF Threshold")
    lWARFFactor = clsTestInputDict("WARF Factor")
    lWARRThreshhold = clsTestInputDict("WARR Threshold")
    
    lThreshold = lWARFThreshold + (lMoodysRecoveryRate - lWARRThreshhold) * 100 * lWARFFactor
    
    
    
    clsTestThresholdDict(TestNum.WeightedAverageRatingFactorMAG14).Thresholds = lThreshold
    
    Set lRatingFactors = LoadingRatingFactor
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset = False Then
            lCollateralBalance = lCollateralBalance + lAsset.ParAmount
            If lRatingFactors.Exists(UCase(lAsset.MDYDPRatingWARF)) Then
                lNumerator = lNumerator + lAsset.ParAmount * lRatingFactors.Item(UCase(lAsset.MDYDPRatingWARF))
            Else
                lNumerator = lNumerator + lAsset.ParAmount * 10000
            End If
        End If
    Next i
    
    With lResults
        .TestNumber = TestNum.WeightedAverageRatingFactorMAG14
        .Denominator = lCollateralBalance
        .Numerator = lNumerator
        .Threshold = lThreshold
        .TestName = "Maximum Moody's Rating Factor Test"
        If lCollateralBalance > 0 Then .Result = lNumerator / lCollateralBalance
        If .Result < .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)
    
End Sub
Private Sub CalcJROCTEST(iPrincipalProceeds As Double)
    Dim lNumerator As Double
    Dim lDenomerator As Double
    Dim lAsset As Asset
    Dim lResults As Results
    Dim i As Long
    
    lNumerator = lNumerator + iPrincipalProceeds
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        If lAsset.DefaultAsset Then
            lNumerator = lNumerator + lAsset.ParAmount * lAsset.MarketValue / 100
        ElseIf lAsset.PIKing Then
            lNumerator = lNumerator + lAsset.ParAmount * lAsset.MDYRecoveryRate
        ElseIf lAsset.MDYRating = "AAAAAA" Then
        
        ElseIf lAsset.SPRating = "AAAAAA" Then
        
        Else
             lNumerator = lNumerator + lAsset.ParAmount
        End If
        
    
    Next i
    lDenomerator = clsTestInputDict("JR OC Denominator")
    'lNumerator = clsCollateralPrincipalAmount
    With lResults
        .TestNumber = JROCTEST
        .TestName = "Junior OC Test"
        .Result = lNumerator / lDenomerator
        .Numerator = lNumerator
        .Denominator = lDenomerator
    End With
    
    Call AddResults(lResults)
    
    
End Sub
Private Sub CalcDiversityScore()
    Dim i As Long
    Dim lNumerator As Double
    Dim lResults As Results
    Dim lAsset As Asset
    Dim lCollateralBalance As Double
    Dim lNumofIssuers As Long
    Dim lAverageParAmount As Double
    Dim lIssuerDict As Dictionary
    Dim lIndustryDict As Dictionary
    Dim lIssuer As Variant
    Dim lDiversity As Double
    Dim lIndustry As Variant
    Dim lIssuerIndustry As Dictionary
    
    Set lIssuerDict = New Dictionary
    Set lIndustryDict = New Dictionary
    Set lIssuerIndustry = New Dictionary
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        lCollateralBalance = lCollateralBalance + lAsset.ParAmount
        If lIssuerDict.Exists(lAsset.IssuerId) Then
            lIssuerDict.Item(lAsset.IssuerId) = lIssuerDict.Item(lAsset.IssuerId) + lAsset.ParAmount
        Else
            lIssuerDict.Add lAsset.IssuerId, lAsset.ParAmount
            lIssuerIndustry.Add lAsset.IssuerId, lAsset.MDYIndustry
        End If
        If Not (lIndustryDict.Exists(lAsset.MDYIndustry)) Then
            lIndustryDict.Add lAsset.MDYIndustry, 0
        End If
    Next i
    lNumofIssuers = lIssuerDict.Count
    lAverageParAmount = lCollateralBalance / lNumofIssuers
    For Each lIssuer In lIssuerDict.Keys
        If lIssuerDict(lIssuer) / lAverageParAmount > 1 Then
            lIssuerDict(lIssuer) = 1
        Else
            lIssuerDict(lIssuer) = lIssuerDict(lIssuer) / lAverageParAmount
        End If
        lIndustryDict(lIssuerIndustry(lIssuer)) = lIndustryDict(lIssuerIndustry(lIssuer)) + lIssuerDict(lIssuer)
    Next
    
    For Each lIndustry In lIndustryDict.Keys
        If lIndustryDict(lIndustry) > 19.95 Then
            lDiversity = lDiversity + 5
        ElseIf lIndustryDict(lIndustry) <= 0 Then
        
        Else
'            i = 0
'            Do While clsAggEUScore(i) < lIndustryDict(lIndustry)
'                i = i + 1
'            Loop
'            lDiversity = lDiversity + clsDiversityScore(i - 1)
            i = Round(lIndustryDict(lIndustry), 1) * 10
            lDiversity = lDiversity + clsDiversityScore(i)
        End If
    Next
    With lResults
        .TestNumber = MoodysDiversity
        .TestName = "Moody's Diversity Test"
        .Result = lDiversity
        .Threshold = clsTestThresholdDict(TestNum.MoodysDiversity).Thresholds
        If .Result > .Threshold Then .PassFail = True
    End With
    Call AddResults(lResults)

End Sub



Private Function LoadingRatingFactor() As Dictionary
    Dim lNewDict As Dictionary
    
    Set lNewDict = New Dictionary
    
    lNewDict.Add "AAA", 1
    lNewDict.Add "AA1", 10
    lNewDict.Add "AA2", 20
    lNewDict.Add "AA3", 40
    lNewDict.Add "A1", 70
    lNewDict.Add "A2", 120
    lNewDict.Add "A3", 180
    lNewDict.Add "BAA1", 260
    lNewDict.Add "BAA2", 360
    lNewDict.Add "BAA3", 610
    lNewDict.Add "BA1", 940
    lNewDict.Add "BA2", 1350
    lNewDict.Add "BA3", 1766
    lNewDict.Add "B1", 2220
    lNewDict.Add "B2", 2720
    lNewDict.Add "B3", 3490
    lNewDict.Add "CAA1", 4770
    lNewDict.Add "CAA2", 6500
    lNewDict.Add "CAA3", 8070
    lNewDict.Add "CA", 10000
    
    Set LoadingRatingFactor = lNewDict
End Function
Private Sub CheckResults(ByRef iResults As Results)
    Dim lTestThresholds As TestThresholds
    
    If clsTestThresholdDict.Exists(iResults.TestNumber) Then
        Set lTestThresholds = clsTestThresholdDict(iResults.TestNumber)
        If lTestThresholds.ThresholdOverwrite = 0 Then
            iResults.Threshold = lTestThresholds.Thresholds
        Else
            iResults.Threshold = lTestThresholds.ThresholdOverwrite
        End If
        
        If lTestThresholds.MinMax = "MAX" Then
            If iResults.Result <= iResults.Threshold Then
                iResults.PassFail = True
            ElseIf Round(iResults.Result, 4) <= Round(lTestThresholds.PreviousValues, 4) And lTestThresholds.PreviousValues > 0 Then
                iResults.PassFail = True
                iResults.PassFailComment = "New test results improves or maintains previous results"
            Else
                iResults.PassFail = False
            End If
        Else
            If iResults.Result >= iResults.Threshold Then
                iResults.PassFail = True
            ElseIf Round(iResults.Result, 4) >= Round(lTestThresholds.PreviousValues, 4) And lTestThresholds.PreviousValues > 0 Then
                iResults.PassFail = True
                iResults.PassFailComment = "New test results improves or maintains previous results"
            Else
                iResults.PassFail = False
            End If
        End If
    End If
End Sub

Private Sub Class_Terminate()
    Set clsAssetsDic = Nothing
    Set clsTestThresholdDict = Nothing
    
End Sub
Private Sub LimitationOnMoodyIndustryClassification()
    Dim i As Long
    Dim lAsset As Asset
    Dim lObligors As Dictionary
    Dim lResult As Results
    Dim lItems As Variant
    Dim lkeys As Variant
    
    Set lObligors = New Dictionary
    
    For i = 0 To clsAssetsDic.Count - 1
        Set lAsset = clsAssetsDic.Items()(i)
        
        If lAsset.DefaultAsset = False Then
            If lObligors.Exists(lAsset.MDYIndustry) Then
                lObligors.Item(lAsset.MDYIndustry) = lObligors.Item(lAsset.MDYIndustry) + lAsset.ParAmount
            Else
                lObligors.Add lAsset.MDYIndustry, lAsset.ParAmount
            End If
        End If
    Next i
    Call SortDictionary(lObligors, False, True)
    lItems = lObligors.Items
    lkeys = lObligors.Keys
  
    'LimitationOn1LagestSPIndustryClassification
    With lResult
        .TestNumber = LimitationOn1MoodyIndustry
        .Comments = lkeys(0)
        .TestName = "Limitation on Largest Moody's Industry"
        .Result = lItems(0) / clsCollateralPrincipalAmount
        .Threshold = 0.15
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(0)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)

    'LimitationOn2LagestSPIndustryClassification
    With lResult
        .TestNumber = LimitationOn2MoodyIndustry
        .Comments = lkeys(1)
        .TestName = "Limitation on 2nd Largest Moody's Industry"
        .Result = lItems(1) / clsCollateralPrincipalAmount
        .Threshold = 0.12
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(1)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    
    'LimitationOn3S&PIndustryClassification
    With lResult
        .TestNumber = LimitationOn3MoodyIndustry
        .Comments = lkeys(2)
        .TestName = "Limitation on 3rd Largest Moody's Industry"
        .Result = lItems(2) / clsCollateralPrincipalAmount
        .Threshold = 0.12
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(1)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    
    'LimitationOn4S&PIndustryClassification
    With lResult
        .TestNumber = LimitationOn4MoodyIndustry
        .Comments = lkeys(3)
        .TestName = "Limitation on 4th Largest Moody's Industry"
        .Result = lItems(3) / clsCollateralPrincipalAmount
        .Threshold = 0.1
        If .Result < .Threshold Then .PassFail = True
        .Numerator = lItems(3)
        .Denominator = clsCollateralPrincipalAmount
    End With
    Call AddResults(lResult)
    
    Set lAsset = Nothing
End Sub
Public Function GetObjectiveDict() As Dictionary
    Set GetObjectiveDict = clsObjWeights
End Function
