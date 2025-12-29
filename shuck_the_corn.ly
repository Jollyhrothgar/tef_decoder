\version "2.16.0"
\header {
title="Shuckin' The Corn"
subtitle=""
composer=""
encoder="Mike J Beaumier"
encodingsoftware="TablEdit"
tagline="Created with TablEdit 3.05 b4 https://tabledit.com/"
}
PAVA = { 
\tempo 4 = 160
\time 4/4
\key c \major
 s8 g \3 d4 \4 d8 \4 (e \4) g4 \3 | % 1
 \repeat volta 2 { a16 \3 \glissando ais \3 b8 \2^"(A Part)" g' \5 d' ais16 \3 (a \3) b8 \2 g \3 d' | % 2
 a16 \3 \glissando ais \3 b8 \2 g' \5 d' d16 \4 (e \4) b8 \2 g \3 d' | % 3
 a16 \3 \glissando ais \3 b8 \2 g' \5 d' ais16 \3 (a \3) b8 \2 g \3 d' | % 4
 f4 \4 g'8 \5 g \3 d' g' \5 g \3 d' | % 5
 d8 \4 (e \4) g' \5 c' \2 d' g' \5 c' \2 d' | % 6
 ais8 \3 c' \2 d' g' \5 d' c' \2 ais \3 d' | % 7
 g8 \3 d' g' \5 a16 \3 \glissando ais \3 d'8 g \3 e \4 d' | % 8
 g8 \3 d' g' \5 g \3 d' g \3 e \4 d' | % 9
 d4 \4 cis'16 \2 (d' \2) d'8 g' \5 d' \2 d' g' \5 | % 10
 cis'16 \2 (d' \2) d'8 cis'16 \2 (d' \2) d'8 g' \5 ais16 \3 (a \3) d'8 g' \5 | % 11
 g8 \3 d' g' \5 a16 \3 \glissando ais \3 d'8 g \3 e \4 d' | % 12
 } \alternative { { g4 \3 g'8 \5 d' d16 \4 (e \4) b8 \2 g \3 d' | % 13
 } { g4 \3 <g' \5 d'> b \2 <g' \5 d'> | % 14
 } } \repeat volta 2 { <d' \2 f'>4^"(B Part)" g' \5 <cis' \2 e'> <b \2 d'> | % 15
 <cis' \2 e'>4 <d' \2 f'> g'8 \5 d' \2 f' g' \5 | % 16
 <d' \2 f'>4 g' \5 <cis' \2 e'> <b \2 d'> | % 17
 <cis' \2 e'>4 <d' \2 f'> g'8 \5 d' \2 f' g' \5 | % 18
 ais'4^"C7" e'8 \2 ais' g' \5 e' \2 ais' g' \5 | % 19
 e'8 \2 ais' e' \2 ais' g' \5 e' \2 ais' g' \5 | % 20
 d'4 cis'16 \2 (d' \2) d'8 g' \5 ais16 \3 (a \3) d'8 g' \5 | % 21
 g8 \3 d' g' \5 g \3 d' g \3 e \4 d' | % 22
 d8 \4 d' cis'16 \2 (d' \2) d'8 g' \5 d' \2 d' g' \5 | % 23
 cis'16 \2 (d' \2) d'8 cis'16 \2 (d' \2) d'8 g' \5 ais16 \3 (a \3) d'8 g' \5 | % 24
 g8 \3 d' g' \5 a16 \3 \glissando ais \3 d'8 g \3 e \4 d' | % 25
 g4 \3 <g' \5 d'> b \2 <g' \5 d'> } | % 26
}

\score { <<
\new TabStaff <<
\override TabStaff.Rest #'transparent = ##t
\set TabStaff.stringTunings = #banjo-c-tuning
\new TabVoice { \slurUp \stemDown \PAVA }
>>
>> }
