from __future__ import annotations

import json
from pathlib import Path


EXAMPLES = [
    ("Can help check ah? Customer Mei Lin says parcel go to Blk 123 Ang Mo Kio Ave 3, #12-34 Singapore 560123.", [("Mei Lin","PERSON"),("Blk 123 Ang Mo Kio Ave 3, #12-34 Singapore 560123","ADDRESS")]),
    ("Please call Mr Tan at +65 9123 4567, he waiting since morning leh.", [("Mr Tan","PERSON"),("+65 9123 4567","PHONE")]),
    ("Order owner is Aisha Rahman, email aisha.rahman@example.com can?", [("Aisha Rahman","PERSON"),("aisha.rahman@example.com","EMAIL")]),
    ("Customer gave NRIC S1234567D for verification, please don't paste outside.", [("S1234567D","SG_NRIC")]),
    ("Deliver to 8 Shenton Way, #25-01 Singapore 068811, attention Daniel Goh.", [("8 Shenton Way, #25-01 Singapore 068811","ADDRESS"),("Daniel Goh","PERSON")]),
    ("Her mobile 81234567 and backup 6123-4567 both can contact.", [("81234567","PHONE"),("6123-4567","PHONE")]),
    ("Eh the buyer Chloe Ng changed email to chloe.ng+shop@mail.example.sg.", [("Chloe Ng","PERSON"),("chloe.ng+shop@mail.example.sg","EMAIL")]),
    ("Send replacement to Blk 45 Tampines St 42 #03-118, Singapore 529001.", [("Blk 45 Tampines St 42 #03-118, Singapore 529001","ADDRESS")]),
    ("Account holder: Ravi Kumar; contact: 9876 5432; pls expedite.", [("Ravi Kumar","PERSON"),("9876 5432","PHONE")]),
    ("Ticket says F7654321N but customer name omitted.", [("F7654321N","SG_NRIC")]),
    ("Can email invoice to finance.user@sample.co, thanks ah.", [("finance.user@sample.co","EMAIL")]),
    ("Pickup from 1 Jurong West Central 2, #B1-07 Singapore 648886 for Nur Izzati.", [("1 Jurong West Central 2, #B1-07 Singapore 648886","ADDRESS"),("Nur Izzati","PERSON")]),
    ("Customer Lim Wei Jie called from +65-8765-4321 about late delivery.", [("Lim Wei Jie","PERSON"),("+65-8765-4321","PHONE")]),
    ("Use this temporary contact 92345678, recipient is Priya Nair.", [("92345678","PHONE"),("Priya Nair","PERSON")]),
    ("Address typo maybe: Blk 701 Bedok Reservoir Rd #10-220 Singapore 470701.", [("Blk 701 Bedok Reservoir Rd #10-220 Singapore 470701","ADDRESS")]),
    ("G1234567X belongs to the requester, do not include in reply.", [("G1234567X","SG_NRIC")]),
    ("Pls update Jia Hui at jiahui_test@example.org once refund done.", [("Jia Hui","PERSON"),("jiahui_test@example.org","EMAIL")]),
    ("The unit is #118-7, customer wrote it like that; phone 9000 1111.", [("#118-7","UNIT_NUMBER"),("9000 1111","PHONE")]),
    ("Mail to 10 Anson Road #17-05 International Plaza Singapore 079903.", [("10 Anson Road #17-05 International Plaza Singapore 079903","ADDRESS")]),
    ("Name maybe misspelled as Muhd Faizal, number +6591112222.", [("Muhd Faizal","PERSON"),("+6591112222","PHONE")]),
    ("Customer typed s2345678e in lowercase, please mask it also.", [("s2345678e","SG_NRIC")]),
    ("Contact Li Xiu Ying via li.xy@demo.net; she prefers email.", [("Li Xiu Ying","PERSON"),("li.xy@demo.net","EMAIL")]),
    ("Drop at Blk 9 Hougang Ave 3 #01-55 Singapore 530009, can lah.", [("Blk 9 Hougang Ave 3 #01-55 Singapore 530009","ADDRESS")]),
    ("Callback requested by Ahmad Bin Salleh at 8899-0011.", [("Ahmad Bin Salleh","PERSON"),("8899-0011","PHONE")]),
    ("Two contacts: Eunice Koh 83334444 and Marcus Lee 96667777.", [("Eunice Koh","PERSON"),("83334444","PHONE"),("Marcus Lee","PERSON"),("96667777","PHONE")]),
    ("Ship to 77 Robinson Rd, Singapore 068896 for Sean Ong.", [("77 Robinson Rd, Singapore 068896","ADDRESS"),("Sean Ong","PERSON")]),
    ("M7654321K and test.person@company.example appeared in the chat.", [("M7654321K","SG_NRIC"),("test.person@company.example","EMAIL")]),
    ("Wah customer Siti Aminah stays at Blk 321 Clementi Ave 5 #04-88.", [("Siti Aminah","PERSON"),("Blk 321 Clementi Ave 5 #04-88","ADDRESS")]),
    ("Please ring 67778888. Do not mask order number 20240929 as phone.", [("67778888","PHONE")]),
    ("Jenny Teo <jenny.teo@example.com> asked delivery to #06-09.", [("Jenny Teo","PERSON"),("jenny.teo@example.com","EMAIL"),("#06-09","UNIT_NUMBER")]),
]


def main() -> None:
    records = []
    for index, (text, annotations) in enumerate(EXAMPLES, 1):
        spans = []
        cursor = 0
        for value, label in annotations:
            start = text.index(value, cursor)
            spans.append({"start": start, "end": start + len(value), "label": label})
            cursor = start + len(value)
        records.append({"id": f"sg-{index:02d}", "text": text, "spans": spans})
    output = Path(__file__).parents[1] / "data" / "singapore_stress.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {output}")


if __name__ == "__main__":
    main()

