/* Power Query (M) script
   Input: CSV with headers "msgid","msgstr"
   Output: a single text value containing a .po file content that you can copy/save as tr.po
*/
let
    // Update this path to your CSV file location
    Source = Csv.Document(File.Contents("C:\\path\\to\\translations.csv"), [Delimiter=",", Columns=2, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Rows = Table.SelectColumns(Promoted, {"msgid", "msgstr"}),
    Escape = Table.TransformColumns(Rows, {
        {"msgid", each Text.Replace(_, "\"", "\\\""), type text},
        {"msgstr", each Text.Replace(_, "\"", "\\\""), type text}
    }),
    ToPoLine = Table.AddColumn(Escape, "po_line", each "msgid """ & [msgid] & """#" & "n" & "msgstr """ & [msgstr] & """"),
    PoBody = Text.Combine(ToPoLine[po_line], "#(lf)#(lf)"),
    Header = "msgid """"" & "#(lf)" &
             "msgstr ""\""Project-Id-Version: shuttle_management\\n\" & \"POT-Creation-Date: " & Date.ToText(DateTimeZone.UtcNow(), "yyyy-MM-dd HH:mm+00:00") & "\\n\" & \"Language: tr\\n\" & "\" & "#(lf)#(lf)",
    Output = Header & PoBody
in
    Output
