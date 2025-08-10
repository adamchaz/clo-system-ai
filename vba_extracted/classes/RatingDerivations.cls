VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "RatingDerivations"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = True
Option Explicit
Private mDealName As String
Private mRatingsDict As Dictionary

Public Function NotchRating(iRatingRank As Long, iRatingName As RatingAgencies, iNotch As Long) As String
    Dim lRating As Ratings

    If iRatingRank - iNotch < 1 Then
       Set lRating = mRatingsDict(1)
    ElseIf iRatingRank - iNotch > mRatingsDict.Count Then
      Set lRating = mRatingsDict(mRatingsDict.Count)
    Else
       Set lRating = mRatingsDict(iRatingRank - iNotch)
    End If
    
    Select Case iRatingName
    
    Case SandP
        NotchRating = lRating.SandP
    Case Moodys
        NotchRating = lRating.Moodys
    Case Fitch
        NotchRating = lRating.Fitch
    End Select

End Function


Public Function ReturnRatingsRank(iString As String) As Long
    Select Case iString
    
    Case "Aaa", "AAA"
        ReturnRatingsRank = 1
    Case "Aa1", "AA+"
        ReturnRatingsRank = 2
    Case "Aa2", "AA"
        ReturnRatingsRank = 3
    Case "Aa3", "AA-"
        ReturnRatingsRank = 4
    Case "A1", "A+"
        ReturnRatingsRank = 5
    Case "A2", "A"
        ReturnRatingsRank = 6
    Case "A3", "A-"
        ReturnRatingsRank = 7
    Case "Baa1", "BBB+"
        ReturnRatingsRank = 8
    Case "Baa2", "BBB"
        ReturnRatingsRank = 9
    Case "Baa3", "BBB-"
        ReturnRatingsRank = 10
    Case "Ba1", "BB+"
        ReturnRatingsRank = 11
    Case "Ba2", "BB"
        ReturnRatingsRank = 12
    Case "Ba3", "BB-"
        ReturnRatingsRank = 13
    Case "B1", "B+"
        ReturnRatingsRank = 14
    Case "B2", "B"
        ReturnRatingsRank = 15
    Case "B3", "B-"
        ReturnRatingsRank = 16
    Case "Caa1", "CCC+"
        ReturnRatingsRank = 17
    Case "Caa2", "CCC"
        ReturnRatingsRank = 18
    Case "Caa3", "CCC-"
        ReturnRatingsRank = 19
    Case "Ca", "CC"
        ReturnRatingsRank = 20
    Case "C"
        ReturnRatingsRank = 21
    End Select
End Function

Private Sub Class_Initialize()

    Set mRatingsDict = New Dictionary
    Dim lRating As Ratings
    Set lRating = New Ratings
    
    With lRating
        .Rank = 1
        .Fitch = "AAA"
        .Moodys = "Aaa"
        .SandP = "AAA"
    End With
    mRatingsDict.Add 1, lRating
    
    
    Set lRating = New Ratings
    With lRating
        .Rank = 2
        .Fitch = "AA+"
        .Moodys = "Aa1"
        .SandP = "AA+"
    End With
    mRatingsDict.Add 2, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 3
        .Fitch = "AA"
        .Moodys = "Aa2"
        .SandP = "AA"
    End With
    mRatingsDict.Add 3, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 4
        .Fitch = "AA-"
        .Moodys = "Aa3"
        .SandP = "AA-"
    End With
    mRatingsDict.Add 4, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 5
        .Fitch = "A+"
        .Moodys = "A1"
        .SandP = "A+"
    End With
    mRatingsDict.Add 5, lRating

    Set lRating = New Ratings
    With lRating
        .Rank = 6
        .Fitch = "A"
        .Moodys = "A2"
        .SandP = "A"
    End With
    mRatingsDict.Add 6, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 7
        .Fitch = "A-"
        .Moodys = "A3"
        .SandP = "A-"
    End With
    mRatingsDict.Add 7, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 8
        .Fitch = "BBB+"
        .Moodys = "Baa1"
        .SandP = "BBB+"
    End With
    mRatingsDict.Add 8, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 9
        .Fitch = "BBB"
        .Moodys = "Baa2"
        .SandP = "BBB"
    End With
    mRatingsDict.Add 9, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 10
        .Fitch = "BBB-"
        .Moodys = "Baa3"
        .SandP = "BBB-"
    End With
    mRatingsDict.Add 10, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 11
        .Fitch = "BB+"
        .Moodys = "Ba1"
        .SandP = "BB+"
    End With
    mRatingsDict.Add 11, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 12
        .Fitch = "BB"
        .Moodys = "Ba2"
        .SandP = "BB"
    End With
    mRatingsDict.Add 12, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 13
        .Fitch = "BB-"
        .Moodys = "Ba3"
        .SandP = "BB-"
    End With
    mRatingsDict.Add 13, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 14
        .Fitch = "B+"
        .Moodys = "B1"
        .SandP = "B+"
    End With
    mRatingsDict.Add 14, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 15
        .Fitch = "BB"
        .Moodys = "B2"
        .SandP = "BB"
    End With
    mRatingsDict.Add 15, lRating
        
    Set lRating = New Ratings
    With lRating
        .Rank = 16
        .Fitch = "B-"
        .Moodys = "B3"
        .SandP = "B-"
    End With
    mRatingsDict.Add 16, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 17
        .Fitch = "CCC+"
        .Moodys = "Caa1"
        .SandP = "CCC+"
    End With
    mRatingsDict.Add 17, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 18
        .Fitch = "CCC"
        .Moodys = "Caa2"
        .SandP = "CCC"
    End With
    mRatingsDict.Add 18, lRating
        
    Set lRating = New Ratings
    With lRating
        .Rank = 19
        .Fitch = "CCC-"
        .Moodys = "Caa3"
        .SandP = "CCC-"
    End With
    mRatingsDict.Add 19, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 20
        .Fitch = "CC"
        .Moodys = "Ca"
        .SandP = "CC"
    End With
    mRatingsDict.Add 20, lRating
    
    Set lRating = New Ratings
    With lRating
        .Rank = 21
        .Fitch = "C"
        .Moodys = "C"
        .SandP = ""
    End With
    mRatingsDict.Add 21, lRating
    

End Sub
Public Sub GetMoodysDefProbRating(iAsset As Asset)
    Dim lMoodyDefProbRating As String
    With iAsset
        If Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = .MDYIssuerRating
            If .MDYIssuerOutlook = "Downgrade" Or .MDYFacilityOutlook = "Downgrade" Then
                lMoodyDefProbRating = NotchRating(ReturnRatingsRank(lMoodyDefProbRating), Moodys, -1)
            ElseIf .MDYIssuerOutlook = "Upgrade" Or .MDYFacilityOutlook = "Upgrade" Then
                lMoodyDefProbRating = NotchRating(ReturnRatingsRank(lMoodyDefProbRating), Moodys, 1)
            
            End If
        ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = .MDYSNRUnSecRating
        ElseIf Not (Len(.MDYSnrSecRating) = 0 Or .MDYSnrSecRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = NotchRating(ReturnRatingsRank(.MDYSnrSecRating), Moodys, -1)
        ElseIf Not (Len(.MDYCreditEstRating) = 0 Or .MDYCreditEstRating = "NR") And DateDiff("m", .MDYCreditEstDate, Now()) < 15 And .DIP = False Then
            lMoodyDefProbRating = .MDYCreditEstRating
        ElseIf .DIP Then
            lMoodyDefProbRating = NotchRating(ReturnRatingsRank(.MDYFacilityRating), Moodys, -1)
        ElseIf Len(GetDerivedMoodyRatingFromSandP(iAsset)) <> 0 Then
            lMoodyDefProbRating = GetDerivedMoodyRatingFromSandP(iAsset)
        Else
            lMoodyDefProbRating = "Caa3"
        End If
    End With
    
    iAsset.MDYDPRating = lMoodyDefProbRating

    
End Sub
Public Sub GetMoodysDefProbRatingWARF(iAsset As Asset)
    Dim lMoodyDefProbRating As String
    With iAsset
        If Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = .MDYIssuerRating
            If .MDYIssuerOutlook = "Negative" Then
                lMoodyDefProbRating = NotchRating(ReturnRatingsRank(lMoodyDefProbRating), Moodys, -2)
            ElseIf .MDYIssuerOutlook = "Downgrade" Or .MDYFacilityOutlook = "Downgrade" Then
                lMoodyDefProbRating = NotchRating(ReturnRatingsRank(lMoodyDefProbRating), Moodys, -1)
            ElseIf .MDYIssuerOutlook = "Upgrade" Or .MDYFacilityOutlook = "Upgrade" Then
                lMoodyDefProbRating = NotchRating(ReturnRatingsRank(lMoodyDefProbRating), Moodys, 1)
            
            End If
        ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = .MDYSNRUnSecRating
        ElseIf Not (Len(.MDYSnrSecRating) = 0 Or .MDYSnrSecRating = "NR") And .DIP = False Then
            lMoodyDefProbRating = NotchRating(ReturnRatingsRank(.MDYSnrSecRating), Moodys, -1)
        ElseIf Not (Len(.MDYCreditEstRating) = 0 Or .MDYCreditEstRating = "NR") And DateDiff("m", .MDYCreditEstDate, Now()) < 15 And .DIP = False Then
            lMoodyDefProbRating = .MDYCreditEstRating
        ElseIf .DIP Then
            lMoodyDefProbRating = NotchRating(ReturnRatingsRank(.MDYFacilityRating), Moodys, -1)
        ElseIf Len(GetDerivedMoodyRatingFromSandP(iAsset)) <> 0 Then
            lMoodyDefProbRating = GetDerivedMoodyRatingFromSandP(iAsset)
        Else
            lMoodyDefProbRating = "Caa3"
        End If
    End With
    
    iAsset.MDYDPRatingWARF = lMoodyDefProbRating

    
End Sub

Public Sub GetMoodysRating(iAsset As Asset)
    Dim lMoodyRating As String
    Dim lMoodyRatingSource As String
    With iAsset
        If .BondLoan = "LOAN" And .Seniority = "SENIOR SECURED" Then
            If Not (Len(.MDYFacilityRating) = 0 Or .MDYFacilityRating = "NR") Then
                lMoodyRating = .MDYFacilityRating
                lMoodyRatingSource = "Moody"
                If .MDYFacilityOutlook = "Upgrade" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, 1)
                    
                ElseIf .MDYFacilityOutlook = "Downgrade" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, -1)
                ElseIf Len(.MDYFacilityOutlook) <> 0 Then

                End If
                
            ElseIf Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") Then
                lMoodyRating = .MDYIssuerRating
                lMoodyRatingSource = "Moody"
                If .MDYIssuerOutlook = "Downgrade" Or .MDYIssuerOutlook = "Negative" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, -1)
                ElseIf Len(.MDYIssuerOutlook) <> 0 Or .MDYIssuerRating = "Downgrade" Or .MDYIssuerRating = "Negative" Then

                End If
            ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYSNRUnSecRating), Moodys, 2)
                lMoodyRatingSource = "Moody"
            ElseIf Len(GetDerivedMoodyRatingFromSandP(iAsset)) <> 0 Then
                lMoodyRating = GetDerivedMoodyRatingFromSandP(iAsset)
                lMoodyRatingSource = "S&P"
            Else
               lMoodyRating = "Caa3"
               lMoodyRatingSource = "Moody"
            End If
        Else
            If Not (Len(.MDYFacilityRating) = 0 Or .MDYFacilityRating = "NR") Then
                lMoodyRating = .MDYFacilityRating
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") Then
                lMoodyRating = .MDYSNRUnSecRating
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYIssuerRating), Moodys, -1)
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYSubRating) = 0 Or .MDYSubRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYSubRating), Moodys, 1)
                lMoodyRatingSource = "Moody"
            ElseIf Len(GetDerivedMoodyRatingFromSandP(iAsset)) <> 0 Then
                lMoodyRating = GetDerivedMoodyRatingFromSandP(iAsset)
                lMoodyRatingSource = "S&P"
            Else
                lMoodyRating = "Caa3"
                lMoodyRatingSource = "Moody"
            End If
        End If
    End With
    'Debug.Print iAsset.BLKRockID & vbTab & lMoodyRating
    iAsset.MDYRating = lMoodyRating
'    Static lstatic As Long
'    ThisWorkbook.Sheets("Sheet2").Range("A2").Offset(lstatic, 0).Value = iAsset.BLKRockID
'    ThisWorkbook.Sheets("Sheet2").Range("A2").Offset(lstatic, 1).Value = lMoodyRating
'    lstatic = lstatic + 1
End Sub
Public Sub GetSnPRatings(iAsset As Asset)
    Dim lSPRating As String
    Dim lMoodysRating As String
    
    
    With iAsset
        If .DIP Then
            lSPRating = .SandPFacilityRating
        ElseIf .DefaultAsset Then
            lSPRating = "D"
        ElseIf Not (Len(.SandPIssuerRating) = 0 Or .SandPIssuerRating = "NR") Then
            lSPRating = .SandPIssuerRating
        ElseIf Not (Len(.SandPSnrSecRating) = 0 Or .SandPSnrSecRating = "NR") Then
            lSPRating = .SandPSnrSecRating
        ElseIf Not (Len(.SandPSubordinate) = 0 Or .SandPSubordinate = "NR") Then
            If ReturnRatingsRank(.SandPSubordinate) < 11 Then
                lSPRating = NotchRating(ReturnRatingsRank(.SandPSubordinate), SandP, 1)
            Else
                lSPRating = NotchRating(ReturnRatingsRank(.SandPSubordinate), SandP, 2)
            End If
        Else
            lSPRating = GetDerivedSandPRatingFromMoody(iAsset)
        End If
        If Len(lSPRating) = 0 Then
            lSPRating = "CCC-"
        End If
        
        .SPRating = lSPRating
    End With


End Sub

Public Function GetDerivedMoodyRatingFromSandP(iAsset As Asset) As String
    Dim lMoodyDerivedRating As String
    
    With iAsset
        If .StructFinance = False And Not (Len(.SandPFacilityRating) = 0 Or .SandPFacilityRating = "NR") Then
            If .BondLoan <> "LOAN" Then
                If ReturnRatingsRank(.SandPFacilityRating) <= 10 Then
                    lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPFacilityRating), Moodys, -1)
                Else
                    lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPFacilityRating), Moodys, -2)
                End If
            Else
                lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPFacilityRating), Moodys, -2)
            End If
        Else
            If Not (Len(.SandPSnrSecRating) = 0 Or .SandPSnrSecRating = "NR") Then
                If ReturnRatingsRank(.SandPSnrSecRating) <= 15 Then
                    lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPSnrSecRating), Moodys, -1)
                Else
                     lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPSnrSecRating), Moodys, -2)
                End If
            ElseIf Not (Len(.SandPSubordinate) = 0 Or .SandPSubordinate = "NR") Then
                If ReturnRatingsRank(.SandPSubordinate) <= 16 Then
                    lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPSubordinate), Moodys, 1)
                Else
                     lMoodyDerivedRating = NotchRating(ReturnRatingsRank(.SandPSubordinate), Moodys, 0)
                End If
            End If
        End If
    End With
    GetDerivedMoodyRatingFromSandP = lMoodyDerivedRating
End Function

Public Function GetDerivedSandPRatingFromMoody(iAsset As Asset)
    Dim lMoodyRating As String
    Dim lMoodyRatingSource As String
    With iAsset
        If .BondLoan = "LOAN" And .Seniority = "SENIOR SECURED" Then
            If Not (Len(.MDYFacilityRating) = 0 Or .MDYFacilityRating = "NR") Then
                lMoodyRating = .MDYFacilityRating
                lMoodyRatingSource = "Moody"
                If .MDYFacilityOutlook = "Upgrade" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, 1)
                    
                ElseIf .MDYFacilityOutlook = "Downgrade" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, -1)
                ElseIf Len(.MDYFacilityOutlook) <> 0 Then

                End If
                
            ElseIf Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") Then
                lMoodyRating = .MDYIssuerRating
                lMoodyRatingSource = "Moody"
                If .MDYIssuerOutlook = "Downgrade" Or .MDYIssuerOutlook = "Negative" Then
                    lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), Moodys, -1)
                ElseIf Len(.MDYIssuerOutlook) <> 0 Or .MDYIssuerRating = "Downgrade" Or .MDYIssuerRating = "Negative" Then

                End If
            ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYSNRUnSecRating), Moodys, 2)
                lMoodyRatingSource = "Moody"
            End If
        Else
            If Not (Len(.MDYFacilityRating) = 0 Or .MDYFacilityRating = "NR") Then
                lMoodyRating = .MDYFacilityRating
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYSNRUnSecRating) = 0 Or .MDYSNRUnSecRating = "NR") Then
                lMoodyRating = .MDYSNRUnSecRating
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYIssuerRating) = 0 Or .MDYIssuerRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYIssuerRating), Moodys, -1)
                lMoodyRatingSource = "Moody"
            ElseIf Not (Len(.MDYSubRating) = 0 Or .MDYSubRating = "NR") Then
                lMoodyRating = NotchRating(ReturnRatingsRank(.MDYSubRating), Moodys, 1)
                lMoodyRatingSource = "Moody"
            End If
        End If
    End With
    If ReturnRatingsRank(lMoodyRating) <= 10 Then
        lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), SandP, -1)
    Else
        lMoodyRating = NotchRating(ReturnRatingsRank(lMoodyRating), SandP, -2)
    End If
    GetDerivedSandPRatingFromMoody = lMoodyRating
End Function

Public Sub MoodyRecoveryRate(iAsset As Asset)
    Dim lRecoveryRate As Double
    Dim lDifference As Long
    'iAsset.BLKRockID
    With iAsset
        If False Then
            'If moody has assigned a recovery rate
        ElseIf .DIP Then
           lRecoveryRate = 0.5
        Else
            lDifference = ReturnRatingsRank(.MDYDPRating) - ReturnRatingsRank(.MDYRating)
            If lDifference >= 2 Then
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.6
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.55
                Else
                    lRecoveryRate = 0.45
                End If
            ElseIf lDifference = 1 Then
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.5
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.45
                Else
                    lRecoveryRate = 0.35
                End If
            ElseIf lDifference = 0 Then
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.45
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.35
                Else
                    lRecoveryRate = 0.3
                End If
            ElseIf lDifference = -1 Then
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.4
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.25
                Else
                    lRecoveryRate = 0.25
                End If
            ElseIf lDifference = -2 Then
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.3
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.15
                Else
                    lRecoveryRate = 0.15
                End If
            Else
                If .MDYAssetCategory = "MOODY’S SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.2
                ElseIf .MDYAssetCategory = "MOODY’S NON-SENIOR SECURED LOAN" Then
                    lRecoveryRate = 0.5
                Else
                    lRecoveryRate = 0.5
                End If
            End If
        End If
        .MDYRecoveryRate = lRecoveryRate
    End With
'    Static lstatic As Long
'    ThisWorkbook.Sheets("Sheet2").Range("A2").Offset(lstatic, 0).Value = iAsset.BLKRockID
'    ThisWorkbook.Sheets("Sheet2").Range("A2").Offset(lstatic, 1).Value = lRecoveryRate
'    lstatic = lstatic + 1
End Sub

