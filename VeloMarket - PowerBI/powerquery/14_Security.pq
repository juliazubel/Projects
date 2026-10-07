// Query name: Security      Group: 06 Security
// User -> country mapping used by dynamic Row-Level Security ("ALL" = sees every country).
let
    Source   = Csv.Document(File.Contents(pDataFolder & "security_users.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {{"UserEmail", type text}, {"Country", type text}}),
    Lower    = Table.TransformColumns(Typed, {{"UserEmail", each Text.Lower(Text.Trim(_)), type text}})
in
    Lower
